"""collect_381.py — DART API collection using team3 methodology, resumable, atomic writes."""
import os, re, sys, json, html, time, requests, zipfile, argparse, signal
from pathlib import Path
import pandas as pd

SESSION = requests.Session()
_STATE = {"records": None, "meta_path": None}

def _save_and_exit(signum, frame):
    if _STATE["records"] is not None and _STATE["meta_path"] is not None:
        tmp = str(_STATE["meta_path"]) + ".tmp"
        pd.DataFrame(_STATE["records"]).to_csv(tmp, index=False, encoding="utf-8-sig")
        os.replace(tmp, _STATE["meta_path"])
    sys.exit(0)

def find_business_report_v2(corp_code, fiscal_year, api_key):
    search_year = fiscal_year + 1
    res = SESSION.get("https://opendart.fss.or.kr/api/list.json",
        params={"crtfc_key":api_key,"corp_code":corp_code,"bgn_de":f"{search_year}0101",
                "end_de":f"{search_year}1231","pblntf_detail_ty":"A001","page_count":"100"},
        timeout=20)
    j = res.json()
    if j.get("status") != "000": return None
    cands = [r for r in j.get("list",[]) if "사업보고서" in r.get("report_nm","")
             and not any(k in r.get("report_nm","") for k in ("반기","분기","연장","신고서"))]
    if not cands: return None
    def pri(n): return 2 if "[첨부정정]" in n else (1 if "[기재정정]" in n else 0)
    cands.sort(key=lambda r:(pri(r["report_nm"]), r["rcept_dt"]))
    c = cands[0]
    return {"rcept_no":c["rcept_no"],"rcept_dt":c["rcept_dt"],"report_nm":c["report_nm"]}

def download_document_xml(rcept_no, api_key, zip_dir):
    zip_path = os.path.join(zip_dir, f"{rcept_no}.zip")
    if not os.path.exists(zip_path):
        res = SESSION.get("https://opendart.fss.or.kr/api/document.xml",
            params={"crtfc_key":api_key,"rcept_no":rcept_no}, timeout=60)
        res.raise_for_status()
        if res.content[:2] != b"PK": raise ValueError("not zip")
        with open(zip_path,"wb") as f: f.write(res.content)
    with zipfile.ZipFile(zip_path) as zf:
        xs = [n for n in zf.namelist() if n.endswith(".xml")]
        main = f"{rcept_no}.xml"
        chosen = main if main in xs else ([n for n in xs if "_" not in n][:1] or [max(xs,key=lambda n:zf.getinfo(n).file_size)])[0]
        b = zf.read(chosen)
    for enc in ("utf-8","euc-kr","cp949"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("utf-8", errors="ignore")

def extract_esg_sections(xml_text):
    ROMAN = re.compile(r"^(I{1,3}|IV|VI{0,3}|IX|X{0,3}(?:I{1,3}|IV|VI{0,3})?)[.\s]")
    TARGET = {"II","IV","VI"}
    titles = [(m.start(), m.end(), re.sub(r"<[^>]+>","", m.group(1)).strip())
              for m in re.finditer(r"<TITLE[^>]*>(.*?)</TITLE>", xml_text, re.DOTALL)]
    titles = [(s,e,t) for s,e,t in titles if ROMAN.match(t)]
    out = {}
    for i,(s,e,t) in enumerate(titles):
        k = ROMAN.match(t).group(1)
        if k not in TARGET: continue
        cs, ce = e, titles[i+1][0] if i+1<len(titles) else len(xml_text)
        ch = xml_text[cs:ce]
        ch = re.sub(r"<TABLE[^>]*>.*?</TABLE>"," ", ch, flags=re.DOTALL)
        ps = re.findall(r"<P[^>]*>(.*?)</P>", ch, re.DOTALL)
        txts = [html.unescape(re.sub(r"<[^>]+>","", p)).strip() for p in ps
                if len(html.unescape(re.sub(r"<[^>]+>","", p)).strip()) >= 10]
        if txts: out[k] = "\n".join(txts)
    return out

def collect_one(row, api_key, zip_dir):
    sc, cc, fy = row["stock_code"], row["corp_code"], int(row["fiscal_year"])
    f = find_business_report_v2(cc, fy, api_key)
    if f is None: return {"status":"FAIL","reason":"보고서_미발견","stock_code":sc,"fiscal_year":fy}
    try:
        xml = download_document_xml(f["rcept_no"], api_key, zip_dir)
    except Exception as e:
        return {"status":"FAIL","reason":f"ZIP오류:{e}","stock_code":sc,"fiscal_year":fy, **f}
    sec = extract_esg_sections(xml)
    if not sec: return {"status":"FAIL","reason":"섹션_미추출","stock_code":sc,"fiscal_year":fy, **f}
    txt = "\n\n".join(sec.values())
    return {"status":"SUCCESS","reason":"","stock_code":sc,"fiscal_year":fy,
            "rcept_no":f["rcept_no"],"rcept_dt":f["rcept_dt"],"report_nm":f["report_nm"],
            "viewer_url":f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={f['rcept_no']}",
            "text":txt, "section_chars_II":len(sec.get("II","")),
            "section_chars_IV":len(sec.get("IV","")),"section_chars_VI":len(sec.get("VI","")),
            "total_chars":len(txt)}

def atomic_save(records, path):
    df = pd.DataFrame(records)
    if "text" in df.columns:
        df = df.drop(columns=["text"])
    tmp = str(path) + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True); ap.add_argument("--corp_map", required=True)
    ap.add_argument("--zip_dir", required=True); ap.add_argument("--out_dir", required=True)
    ap.add_argument("--api_key", required=True); ap.add_argument("--sleep", type=float, default=0.0)
    args = ap.parse_args()
    out_dir = Path(args.out_dir); corpus_dir = out_dir/"corpus"; corpus_dir.mkdir(exist_ok=True)
    Path(args.zip_dir).mkdir(parents=True, exist_ok=True)

    cm = pd.read_csv(args.master, dtype={"stock_code":str})
    cm["stock_code"] = cm["stock_code"].str.zfill(6); cm["fiscal_year"] = cm["fiscal_year"].astype(int)
    corp_map = pd.read_csv(args.corp_map, encoding="utf-8-sig", dtype={"stock_code":str,"corp_code":str})
    corp_map["stock_code"] = corp_map["stock_code"].str.zfill(6)
    sc2cc = dict(zip(corp_map["stock_code"], corp_map["corp_code"]))
    cm["corp_code"] = cm["stock_code"].map(sc2cc)
    assert cm["corp_code"].notna().all()

    META_CSV = out_dir/"collection_meta.csv"
    if META_CSV.exists():
        done = pd.read_csv(META_CSV, dtype={"stock_code":str})
        done["stock_code"] = done["stock_code"].str.zfill(6); done["fiscal_year"] = done["fiscal_year"].astype(int)
        success_keys = set(zip(done.loc[done["status"]=="SUCCESS","stock_code"],
                                done.loc[done["status"]=="SUCCESS","fiscal_year"]))
        records = done.to_dict("records")
        print(f"[Checkpoint] {len(done)} rows, SUCCESS={len(success_keys)}")
    else:
        success_keys, records = set(), []

    _STATE["records"] = records
    _STATE["meta_path"] = META_CSV
    signal.signal(signal.SIGTERM, _save_and_exit)
    signal.signal(signal.SIGINT, _save_and_exit)

    n_total = len(cm); n_skip = n_success = n_fail = 0
    for i, row in enumerate(cm.to_dict("records"), 1):
        key = (row["stock_code"], int(row["fiscal_year"]))
        if key in success_keys: n_skip += 1; continue
        out = collect_one(row, args.api_key, args.zip_dir)
        out["corp_code"] = row["corp_code"]; out["company_name"] = row.get("company_name","")
        records.append(out)
        if out["status"] == "SUCCESS":
            n_success += 1; success_keys.add(key)
            cp = corpus_dir/f"{row['stock_code']}_{row['fiscal_year']}.json"
            with open(cp,"w",encoding="utf-8") as f:
                json.dump({k:out[k] for k in ["stock_code","fiscal_year","rcept_no","viewer_url",
                          "text","section_chars_II","section_chars_IV","section_chars_VI","total_chars"]},
                          f, ensure_ascii=False)
        else:
            n_fail += 1
        if i % 5 == 0 or i == n_total:
            atomic_save(records, META_CSV)
            print(f"  [{i}/{n_total}] {out['status']} {row['stock_code']}_{row['fiscal_year']} | "
                  f"S={n_success} F={n_fail} skip={n_skip}", flush=True)
        if args.sleep > 0: time.sleep(args.sleep)

    atomic_save(records, META_CSV)
    print(f"[DONE] SUCCESS={n_success+len(success_keys)} FAIL={n_fail}")

if __name__ == "__main__":
    main()

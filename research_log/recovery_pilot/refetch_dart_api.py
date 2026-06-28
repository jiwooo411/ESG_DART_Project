"""
refetch_dart_api.py — DART API refetch script for FAILED_REFETCH_NEEDED firm-years
======================================================================
Recovers 313 firm-years missing from user's pipeline that fall in the
MemberA 127×3=381 universe. Requires OPENDART_API_KEY in .env.

USAGE
-----
    cp .env.example .env
    # add OPENDART_API_KEY=xxxxx
    python refetch_dart_api.py --universe universe_127x3.csv \\
        --out_dir ./recovered_zips \\
        --skip_existing  # uses local zip_cache to avoid double-fetch

OUTPUT
------
    recovered_zips/{rcept_no}.zip
    recovered_collection_meta.csv
    refetch_failed.csv

Methodology (DECISION BOX)
--------------------------
Alternative   : OpenDART MCP / dart-fss CLI / direct REST API
Choice        : Direct REST API
Justification : reproducibility, no LLM-generated text (per project rules),
                explicit lineage logging
Limitation    : rate-limited (1000 req/day default), requires API key
"""
import os, time, json, argparse, zipfile, requests
from io import BytesIO
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE = "https://opendart.fss.or.kr/api"
SLEEP = 0.5  # rate-limit guard

def get_rcept_no(api_key, corp_code, fiscal_year):
    """fiscal_year+1년 공시 사업보고서 검색. 정정공시 우선순위 [기재정정] > 원본 > [첨부정정]."""
    bgn = f"{fiscal_year+1}0101"; end = f"{fiscal_year+1}1231"
    r = requests.get(f"{BASE}/list.json", params={
        "crtfc_key": api_key, "corp_code": corp_code,
        "bgn_de": bgn, "end_de": end, "pblntf_detail_ty": "A001",
        "page_count": 100,
    }, timeout=30)
    j = r.json()
    if j.get("status") not in ("000","013"): return None, f"list_api_status_{j.get('status')}"
    items = j.get("list", [])
    if not items: return None, "no_business_report"
    # Match fiscal_year by report name
    needle = f"({fiscal_year}.12)"
    candidates = [it for it in items if needle in it.get("report_nm","")]
    if not candidates: candidates = items
    # Preference: 기재정정 > original > 첨부정정 (014)
    candidates.sort(key=lambda x: (
        0 if "기재정정" in x.get("report_nm","") else
        2 if "[첨부정정]" in x.get("report_nm","") else 1,
        x.get("rcept_dt","")
    ))
    return candidates[0]["rcept_no"], None

def download_zip(api_key, rcept_no, out_path):
    r = requests.get(f"{BASE}/document.xml", params={
        "crtfc_key": api_key, "rcept_no": rcept_no
    }, timeout=60)
    if r.status_code != 200 or len(r.content) < 1000:
        return False, f"bad_response_{r.status_code}_size={len(r.content)}"
    try:
        zf = zipfile.ZipFile(BytesIO(r.content))
        zf.namelist()
    except Exception as e:
        return False, f"bad_zip: {e}"
    with open(out_path, "wb") as f:
        f.write(r.content)
    return True, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--lineage", required=True, help="firm_year_lineage.csv")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--skip_existing", action="store_true")
    ap.add_argument("--zip_cache", default=None, help="path to existing zip_cache")
    args = ap.parse_args()

    api_key = os.environ.get("OPENDART_API_KEY") or os.environ.get("DART_API_KEY")
    assert api_key, "OPENDART_API_KEY not set"

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    universe = pd.read_csv(args.universe, encoding='utf-8-sig')
    universe['stock_code'] = universe['stock_code'].astype(str).str.zfill(6)

    lineage = pd.read_csv(args.lineage, encoding='utf-8-sig', dtype={'stock_code':str})
    lineage['stock_code'] = lineage['stock_code'].str.zfill(6)
    targets = lineage[lineage['status']=='FAILED_REFETCH_NEEDED'][['stock_code','fiscal_year']].drop_duplicates()
    print(f"[refetch] {len(targets)} firm-years queued")

    # corp_code from corpCode.xml mapping (assume already mapped in universe)
    # If not, run corpCode mapping first
    sc_to_corp = dict(zip(universe['stock_code'], universe.get('corp_code', pd.Series(dtype=str)).fillna('')))

    results = []
    for i, (_, row) in enumerate(targets.iterrows()):
        sc, fy = row['stock_code'], int(row['fiscal_year'])
        corp = sc_to_corp.get(sc, '')
        rec = {'stock_code':sc,'fiscal_year':fy,'corp_code':corp,'ts': datetime.utcnow().isoformat()}
        if not corp:
            rec.update(status='FAIL', reason='no_corp_code'); results.append(rec); continue
        rcept, err = get_rcept_no(api_key, corp, fy)
        time.sleep(SLEEP)
        if not rcept:
            rec.update(status='FAIL', reason=err); results.append(rec); continue
        rec['rcept_no'] = rcept
        zip_path = out / f"{rcept}.zip"
        if args.skip_existing and args.zip_cache:
            cached = Path(args.zip_cache) / f"{rcept}.zip"
            if cached.exists():
                rec.update(status='CACHED', reason='zip in cache'); results.append(rec); continue
        ok, err = download_zip(api_key, rcept, zip_path)
        time.sleep(SLEEP)
        rec.update(status='SUCCESS' if ok else 'FAIL', reason=err or '')
        results.append(rec)
        if (i+1) % 25 == 0:
            pd.DataFrame(results).to_csv(out/'recovered_collection_meta.csv', index=False, encoding='utf-8-sig')
            print(f"  [{i+1}/{len(targets)}] saved checkpoint")

    df = pd.DataFrame(results)
    df.to_csv(out/'recovered_collection_meta.csv', index=False, encoding='utf-8-sig')
    df[df['status']=='FAIL'].to_csv(out/'refetch_failed.csv', index=False, encoding='utf-8-sig')
    print(f"\n[done] success={ (df['status']=='SUCCESS').sum() } fail={ (df['status']=='FAIL').sum() } cached={(df['status']=='CACHED').sum()}")

if __name__ == '__main__':
    main()

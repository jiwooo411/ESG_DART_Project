# =============================================================================
# 02_extract_sections.py — 섹션 추출 + ESG 패시지 추출 + firm-year document 생성
# =============================================================================
# 실행: python 02_extract_sections.py
#
# 입력:  data/01_raw/collected_reports.csv  (01_collect.py 결과)
#        data/zip_cache/*.zip               (다운로드된 ZIP들)
#
# 출력:  data/02_sections/extracted_sections.csv
#        data/02_sections/section_failed_logs.csv
#        data/03_passages/esg_passages.csv
#        data/03_passages/firm_year_documents.csv
#
# 이 스크립트에서 하는 판단들:
#   - XML → 평문 텍스트 변환 (BeautifulSoup)
#   - 섹션 II / IV / VI 추출 (정규식)
#   - ESG 패시지 필터링 (seed 단어 매칭)
#   - firm-year document 병합

import os
import sys
import logging
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.dart_api import extract_xml_from_zip
from src.section_extractor import xml_to_sections
from src.passage_filter import section_to_passages, build_firm_year_document
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(config.SECTION_DIR, "extract_run.log"), encoding="utf-8"
        ),
    ]
)
logger = logging.getLogger(__name__)


def run_extraction(min_seed_count: int = 1,
                   row_start: int = 0, row_end: int | None = None,
                   append: bool = False):
    """
    min_seed_count : ESG 패시지 필터링 강도 (1=느슨, 2=엄격)
    row_start/end  : collected_reports.csv 중 처리할 행 범위 (배치 실행용)
    append         : True이면 기존 출력 CSV에 이어쓰기 (배치 2차~)
    """
    logger.info("=" * 60)
    label = f"rows {row_start}-{row_end}" if row_end else "all"
    logger.info(f"섹션 추출 시작 (min_seed_count={min_seed_count}, {label}, append={append})")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: 수집 결과 로드
    # ------------------------------------------------------------------
    if not os.path.exists(config.COLLECTED_PATH):
        logger.error("collected_reports.csv 없음. 먼저 01_collect.py를 실행하세요.")
        return

    collected = pd.read_csv(config.COLLECTED_PATH, dtype=str)

    # 이미 처리된 rcept_no skip (resume 지원)
    if append and os.path.exists(config.EXTRACTED_SECTION_PATH):
        done = set(pd.read_csv(config.EXTRACTED_SECTION_PATH, dtype=str)["rcept_no"].tolist())
        before = len(collected)
        collected = collected[~collected["rcept_no"].isin(done)].reset_index(drop=True)
        logger.info(f"Resume: {before}건 중 {len(done)}건 기완료 → {len(collected)}건 처리")

    # 배치 슬라이싱
    if row_end is not None:
        collected = collected.iloc[row_start:row_end].reset_index(drop=True)

    logger.info(f"처리 대상: {len(collected)}건")

    # ------------------------------------------------------------------
    # 결과 저장용 리스트
    # ------------------------------------------------------------------
    section_rows  = []   # extracted_sections.csv 용
    passage_rows  = []   # esg_passages.csv 용
    firm_year_rows = []  # firm_year_documents.csv 용
    failed_rows   = []   # section_failed_logs.csv 용

    # ------------------------------------------------------------------
    # Step 2: ZIP → XML → 섹션 → 패시지
    # ------------------------------------------------------------------
    for idx, row in collected.iterrows():
        stock_code  = row["stock_code"]
        corp_code   = row["corp_code"]
        rcept_no    = row["rcept_no"]
        fiscal_year = row["fiscal_year"]
        esg_year    = row["esg_year"]
        zip_filename = os.path.basename(row["zip_path"])
        zip_path = Path(config.ZIP_CACHE) / zip_filename

        logger.info(f"[{idx+1}/{len(collected)}] {stock_code} FY{fiscal_year}")

        # --- ZIP → XML 텍스트 ---
        xml_text = extract_xml_from_zip(zip_path)
        if xml_text is None:
            failed_rows.append(_fail_row(
                row, step="xml_extract", error="XML 추출 실패"
            ))
            continue

        # --- XML → 섹션 딕셔너리 ---
        try:
            plain_text, sections = xml_to_sections(xml_text)
        except Exception as e:
            failed_rows.append(_fail_row(
                row, step="section_extract", error=str(e)
            ))
            continue

        # 어떤 섹션도 찾지 못한 경우
        found_sections = [k for k, v in sections.items() if v]
        if not found_sections:
            failed_rows.append(_fail_row(
                row, step="section_extract", error="모든 섹션 미발견"
            ))

        # 섹션별 저장
        for section_key in config.TARGET_SECTIONS:
            section_text = sections.get(section_key, "")
            section_rows.append({
                "stock_code":    stock_code,
                "corp_code":     corp_code,
                "rcept_no":      rcept_no,
                "fiscal_year":   fiscal_year,
                "esg_year":      esg_year,
                "section":       section_key,
                "text_length":   len(section_text),
                "text":          section_text[:5000],  # 저장 크기 제한 (미리보기용)
            })

        # --- 섹션 → ESG 패시지 ---
        all_passages = []
        for section_key in config.TARGET_SECTIONS:
            section_text = sections.get(section_key, "")
            if not section_text:
                continue

            # exp_E/F 재실행 시에만 use_sentence_filter=True 로 호출
        passages = section_to_passages(
            section_text,
            seed_words=config.ALL_SEEDS,
            min_seed_count=1,
            section_name=section_key,
            use_sentence_filter=True   # exp_E/F 전용
        )

        for p in passages:
                passage_rows.append({
                    "stock_code":    stock_code,
                    "corp_code":     corp_code,
                    "rcept_no":      rcept_no,
                    "fiscal_year":   fiscal_year,
                    "esg_year":      esg_year,
                    "section":       section_key,
                    "paragraph_id":  p["paragraph_id"],
                    "seed_count":    p["seed_count"],
                    "esg_category":  p["esg_category"],
                    "matched_seeds": str(p["matched_seeds"]),
                    "text":          p["text"],
                })
                all_passages.append(p)

        # --- ESG 패시지 → firm-year document ---
        if all_passages:
            firm_doc = build_firm_year_document(all_passages)
            firm_year_rows.append({
                "stock_code":     stock_code,
                "corp_code":      corp_code,
                "rcept_no":       rcept_no,
                "fiscal_year":    fiscal_year,
                "esg_year":       esg_year,
                "passage_count":  len(all_passages),
                "total_char":     len(firm_doc),
                "document":       firm_doc,
            })
            logger.info(
                f"  → firm-year doc: {len(all_passages)}개 패시지, {len(firm_doc)}자"
            )
        else:
            # 패시지가 0인 경우 — 실패 로그에 기록
            failed_rows.append(_fail_row(
                row, step="passage_filter",
                error=f"ESG 패시지 0개 (min_seed={min_seed_count})"
            ))
            logger.warning(f"  → ESG 패시지 없음: {stock_code} FY{fiscal_year}")

    # ------------------------------------------------------------------
    # Step 3: 저장
    # ------------------------------------------------------------------
    _save_df(section_rows,  config.EXTRACTED_SECTION_PATH, "extracted_sections",  append)
    _save_df(passage_rows,  config.ESG_PASSAGES_PATH,      "esg_passages",        append)
    _save_df(firm_year_rows,config.FIRM_YEAR_DOC_PATH,     "firm_year_documents", append)
    _save_df(failed_rows,   config.SECTION_FAILED_PATH,    "section_failed_logs", append)

    logger.info("=" * 60)
    logger.info(f"완료: firm-year doc {len(firm_year_rows)}건 생성")
    logger.info(f"     ESG 패시지 {len(passage_rows)}건")
    logger.info(f"     실패 {len(failed_rows)}건")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 간단한 품질 체크 — 직접 눈으로 확인하도록 유도
    # ------------------------------------------------------------------
    if firm_year_rows:
        sample = firm_year_rows[0]
        logger.info("\n[샘플 확인 — 첫 번째 firm-year document 미리보기]")
        logger.info(f"  stock_code={sample['stock_code']} FY{sample['fiscal_year']}")
        logger.info(f"  passage_count={sample['passage_count']}")
        logger.info(f"  document (앞 300자):\n{sample['document'][:300]}")
        logger.info("\n※ 반드시 눈으로 읽어볼 것 — ESG 내용이 맞는지 확인!")


# =============================================================================
# 유틸리티 함수
# =============================================================================

def _fail_row(row, step: str, error: str) -> dict:
    return {
        "stock_code":  row["stock_code"],
        "corp_code":   row["corp_code"],
        "rcept_no":    row["rcept_no"],
        "fiscal_year": row["fiscal_year"],
        "step":        step,
        "error_type":  type(error).__name__ if not isinstance(error, str) else "Error",
        "error_msg":   str(error),
        "timestamp":   datetime.now().isoformat(),
    }


def _save_df(rows: list, path: str, name: str, append: bool = False):
    df = pd.DataFrame(rows)
    if append and os.path.exists(path):
        existing = pd.read_csv(path, dtype=str)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"저장: {name} ({len(df)}행 total) → {path}")


# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--min_seed",   type=int,  default=1)
    parser.add_argument("--row_start",  type=int,  default=0)
    parser.add_argument("--row_end",    type=int,  default=None)
    parser.add_argument("--append",     action="store_true")
    args = parser.parse_args()
    run_extraction(
        min_seed_count=args.min_seed,
        row_start=args.row_start,
        row_end=args.row_end,
        append=args.append,
    )

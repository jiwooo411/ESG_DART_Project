# =============================================================================
# 01_collect.py — DART 사업보고서 수집 스크립트
# =============================================================================
# 실행: python 01_collect.py
#
# 이 스크립트가 하는 일:
#   1. corp_code 매핑 테이블 다운로드 (또는 캐시 로드)
#   2. 샘플 기업 목록(sample_firms.csv) 읽기
#   3. 각 firm × fiscal_year에 대해:
#      - rcept_no 조회
#      - ZIP 다운로드
#      - 결과 로깅
#   4. 수집 결과를 collected_reports.csv, failed_logs.csv에 저장
#
# 데이터 lineage:
#   stock_code → corp_code → rcept_no → ZIP 파일
#   이 경로를 절대 건너뛰지 않는다.

import os
import time
import pandas as pd
import logging

# 프로젝트 루트를 경로에 추가
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.dart_api import (
    download_corp_code_map,
    get_corp_code,
    get_report_list,
    pick_latest_report,
    download_report_zip,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(config.RAW_DIR, "collect_run.log"), encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 메인 수집 함수
# =============================================================================

def run_collection():
    logger.info("=" * 60)
    logger.info("DART 수집 시작")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: corp_code 매핑 테이블
    # ------------------------------------------------------------------
    # 캐시가 있으면 재다운로드 없이 로드
    if os.path.exists(config.CORP_CODE_MAP_PATH):
        logger.info("corp_code 매핑 테이블 캐시 로드")
        corp_map = pd.read_csv(config.CORP_CODE_MAP_PATH, dtype=str)
    else:
        logger.info("corp_code 매핑 테이블 다운로드 중...")
        corp_map = download_corp_code_map(config.DART_API_KEY)
        corp_map.to_csv(config.CORP_CODE_MAP_PATH, index=False, encoding="utf-8-sig")
        logger.info(f"저장 완료: {config.CORP_CODE_MAP_PATH}")

    # ------------------------------------------------------------------
    # Step 2: 샘플 기업 목록 로드
    # ------------------------------------------------------------------
    # sample_firms.csv 형식:
    #   stock_code, corp_name, kcgs_grade_2022, kcgs_grade_2023, ...
    #   (KCGS 등급 구간별 층화 추출 결과)
    sample_path = os.path.join(config.BASE_DIR, "sample_firms.csv")
    if not os.path.exists(sample_path):
        logger.error(f"sample_firms.csv 없음: {sample_path}")
        logger.error("sample_firms.csv를 먼저 준비하세요. (가이드 문서 1번 참조)")
        return

    sample_df = pd.read_csv(sample_path, dtype=str)
    logger.info(f"샘플 기업 수: {len(sample_df)}개")

    # ------------------------------------------------------------------
    # Step 3: 수집 루프
    # ------------------------------------------------------------------
    collected_rows = []
    failed_rows    = []

    total = len(sample_df) * len(config.FISCAL_YEARS)
    done  = 0

    for _, firm in sample_df.iterrows():
        stock_code = firm["stock_code"].strip()
        corp_name  = firm.get("corp_name", "")

        # stock_code → corp_code
        corp_code = get_corp_code(stock_code, corp_map)
        if corp_code is None:
            for fy in config.FISCAL_YEARS:
                failed_rows.append({
                    "stock_code":  stock_code,
                    "corp_code":   None,
                    "rcept_no":    None,
                    "fiscal_year": fy,
                    "step":        "corp_code_lookup",
                    "error_type":  "NotFound",
                    "error_msg":   "corp_code 없음",
                })
            continue

        for fiscal_year in config.FISCAL_YEARS:
            done += 1
            esg_year = fiscal_year + 1
            logger.info(f"[{done}/{total}] {corp_name}({stock_code}) FY{fiscal_year}")

            # rcept_no 조회
            report_list = get_report_list(corp_code, fiscal_year, config.DART_API_KEY)
            time.sleep(config.REQUEST_DELAY)

            if not report_list:
                failed_rows.append({
                    "stock_code":  stock_code,
                    "corp_code":   corp_code,
                    "rcept_no":    None,
                    "fiscal_year": fiscal_year,
                    "step":        "report_list",
                    "error_type":  "NoReport",
                    "error_msg":   "사업보고서 없음",
                })
                continue

            # 가장 최근 보고서 선택 (정정 공시 대응)
            report = pick_latest_report(report_list)
            rcept_no   = report["rcept_no"]
            report_dt  = report.get("rcept_dt", "")

            # ZIP 다운로드
            zip_path = download_report_zip(
                rcept_no,
                config.DART_API_KEY,
                save_dir=config.ZIP_CACHE,
                max_retries=config.MAX_RETRIES,
                delay=config.REQUEST_DELAY,
            )
            time.sleep(config.REQUEST_DELAY)

            if zip_path is None:
                failed_rows.append({
                    "stock_code":  stock_code,
                    "corp_code":   corp_code,
                    "rcept_no":    rcept_no,
                    "fiscal_year": fiscal_year,
                    "step":        "zip_download",
                    "error_type":  "DownloadFailed",
                    "error_msg":   "모든 재시도 실패",
                })
                continue

            # 수집 성공
            collected_rows.append({
                "stock_code":  stock_code,
                "corp_code":   corp_code,
                "corp_name":   corp_name,
                "rcept_no":    rcept_no,
                "fiscal_year": fiscal_year,
                "esg_year":    esg_year,
                "report_date": report_dt,
                "zip_path":    zip_path,
                "status":      "success",
            })

    # ------------------------------------------------------------------
    # Step 4: 결과 저장
    # ------------------------------------------------------------------
    collected_df = pd.DataFrame(collected_rows)
    failed_df    = pd.DataFrame(failed_rows)

    collected_df.to_csv(config.COLLECTED_PATH,      index=False, encoding="utf-8-sig")
    failed_df.to_csv(config.FAILED_COLLECT_PATH,    index=False, encoding="utf-8-sig")

    logger.info("=" * 60)
    logger.info(f"수집 완료: {len(collected_rows)}건 성공 / {len(failed_rows)}건 실패")
    logger.info(f"collected_reports.csv → {config.COLLECTED_PATH}")
    logger.info(f"failed_logs.csv       → {config.FAILED_COLLECT_PATH}")
    logger.info("=" * 60)

    # 실패 이유 요약 출력
    if not failed_df.empty:
        logger.info("\n[실패 유형 요약]")
        logger.info(failed_df["error_type"].value_counts().to_string())
        logger.info("\n※ 실패 행은 절대 0으로 채우거나 삭제하지 않는다.")
        logger.info("  이 로그는 나중에 데이터 편향 설명에 사용된다.")


# =============================================================================
if __name__ == "__main__":
    run_collection()

# =============================================================================
# collect_expanded.py — 72개 신규 기업 DART 수집 (기존 10개 제외)
# =============================================================================
# 실행: python collect_expanded.py
#
# 기존 sample_firms.csv(10개)는 이미 zip_cache에 있으므로 제외.
# 신규 71개(005200 KCGS 미수집 제외) firm × 3 years = 최대 213건 수집.

import os, sys, time, logging, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from src.dart_api import (
    get_corp_code, get_report_list, pick_latest_report, download_report_zip
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(config.RAW_DIR, "collect_expanded.log"),
            encoding="utf-8"
        ),
    ]
)
logger = logging.getLogger(__name__)

# 기존 10개 제외
EXISTING = {'005930','000660','207940','005380','000270','005490','028260','000810','086790','105560'}

def run():
    logger.info("=" * 60)
    logger.info("확장 수집 시작 (72개 신규 기업)")
    logger.info("=" * 60)

    corp_map = pd.read_csv(config.CORP_CODE_MAP_PATH, dtype=str)
    corp_map['stock_code'] = corp_map['stock_code'].str.zfill(6)

    expanded = pd.read_csv(
        os.path.join(config.BASE_DIR, "sample_firms_expanded.csv"), dtype=str
    )
    # 신규 기업만
    new_firms = expanded[~expanded['stock_code'].str.zfill(6).isin(EXISTING)].copy()
    new_firms['stock_code'] = new_firms['stock_code'].str.zfill(6)

    logger.info(f"신규 기업 수: {len(new_firms)}")

    # 기존 수집 결과 로드 (중복 방지)
    existing_collected_path = config.COLLECTED_PATH
    if os.path.exists(existing_collected_path):
        existing_df = pd.read_csv(existing_collected_path, dtype=str)
        existing_keys = set(zip(existing_df['stock_code'].str.zfill(6),
                                 existing_df['fiscal_year'].astype(str)))
    else:
        existing_keys = set()

    collected_rows, failed_rows = [], []
    total = len(new_firms) * len(config.FISCAL_YEARS)
    done = 0

    for _, firm in new_firms.iterrows():
        stock_code = firm['stock_code']
        corp_name  = firm.get('corp_name', '')

        corp_code = get_corp_code(stock_code, corp_map)
        if corp_code is None:
            for fy in config.FISCAL_YEARS:
                failed_rows.append({
                    'stock_code': stock_code, 'corp_code': None,
                    'rcept_no': None, 'fiscal_year': fy,
                    'step': 'corp_code_lookup', 'error_type': 'NotFound',
                    'error_msg': 'corp_code 없음',
                })
            continue

        for fiscal_year in config.FISCAL_YEARS:
            done += 1
            key = (stock_code, str(fiscal_year))
            if key in existing_keys:
                logger.info(f"[{done}/{total}] {corp_name}({stock_code}) FY{fiscal_year} — 기수집, SKIP")
                continue

            logger.info(f"[{done}/{total}] {corp_name}({stock_code}) FY{fiscal_year}")
            esg_year = fiscal_year + 1

            report_list = get_report_list(corp_code, fiscal_year, config.DART_API_KEY)
            time.sleep(config.REQUEST_DELAY)

            if not report_list:
                failed_rows.append({
                    'stock_code': stock_code, 'corp_code': corp_code,
                    'rcept_no': None, 'fiscal_year': fiscal_year,
                    'step': 'report_list', 'error_type': 'NoReport',
                    'error_msg': '사업보고서 없음',
                })
                continue

            report   = pick_latest_report(report_list)
            rcept_no = report['rcept_no']
            report_dt= report.get('rcept_dt', '')

            zip_path = download_report_zip(
                rcept_no, config.DART_API_KEY,
                save_dir=config.ZIP_CACHE,
                max_retries=config.MAX_RETRIES,
                delay=config.REQUEST_DELAY,
            )
            time.sleep(config.REQUEST_DELAY)

            if zip_path is None:
                failed_rows.append({
                    'stock_code': stock_code, 'corp_code': corp_code,
                    'rcept_no': rcept_no, 'fiscal_year': fiscal_year,
                    'step': 'zip_download', 'error_type': 'DownloadFailed',
                    'error_msg': '모든 재시도 실패',
                })
                continue

            collected_rows.append({
                'stock_code': stock_code, 'corp_code': corp_code,
                'corp_name': corp_name, 'rcept_no': rcept_no,
                'fiscal_year': fiscal_year, 'esg_year': esg_year,
                'report_date': report_dt, 'zip_path': zip_path,
                'status': 'success',
            })

    # collected_reports.csv에 append
    new_df   = pd.DataFrame(collected_rows)
    fail_df  = pd.DataFrame(failed_rows)

    if os.path.exists(existing_collected_path):
        old_df = pd.read_csv(existing_collected_path, dtype=str)
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(config.COLLECTED_PATH, index=False, encoding='utf-8-sig')

    # 실패 로그 append
    fail_path = config.FAILED_COLLECT_PATH
    if os.path.exists(fail_path) and not fail_df.empty:
        old_fail = pd.read_csv(fail_path, dtype=str)
        fail_df  = pd.concat([old_fail, fail_df], ignore_index=True)
    if not fail_df.empty:
        fail_df.to_csv(fail_path, index=False, encoding='utf-8-sig')

    logger.info("=" * 60)
    logger.info(f"완료: {len(collected_rows)}건 성공 / {len(failed_rows)}건 실패")
    logger.info(f"collected_reports.csv 총 {len(combined)}건")
    logger.info("=" * 60)

if __name__ == "__main__":
    run()

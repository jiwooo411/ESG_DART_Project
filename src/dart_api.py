# =============================================================================
# src/dart_api.py — DART OpenAPI 호출 모듈
# =============================================================================
# 이 모듈이 하는 일:
#   1. 기업코드 전체 목록(corp_code) 다운로드 및 파싱
#   2. corp_code → 사업보고서 rcept_no 목록 조회
#   3. rcept_no → ZIP 파일 다운로드
#
# 데이터 lineage 원칙:
#   stock_code → corp_code → rcept_no → ZIP → XML
#   이 변환 경로를 절대 건너뛰지 않는다.

import io
import os
import time
import zipfile
import logging
import requests
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# 1. 기업코드 매핑 테이블 구축
# =============================================================================

def download_corp_code_map(api_key: str) -> pd.DataFrame:
    """
    DART에서 전체 기업코드 ZIP을 받아 stock_code ↔ corp_code 매핑 DataFrame을 반환.

    왜 이 함수가 필요한가:
        DART API 엔드포인트 대부분이 corp_code를 요구한다.
        stock_code(증권코드)와 corp_code(DART 고유코드)는 다른 식별자다.
        이 매핑을 한 번 다운로드해두면 이후 API 호출 수를 줄일 수 있다.

    Decision — API 매번 호출 vs. 매핑 테이블 선다운로드:
        → 매핑 테이블 선다운로드 선택.
        → 이유: 기업 수가 수천 개이므로, 매번 API 호출하면 rate limit에 걸림.
        → 한계: 분기별 기업 상장/폐지 변동이 반영되지 않을 수 있음.
              (사업보고서 수집 직전에 한 번 갱신하는 것으로 충분)
    """
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    logger.info("기업코드 ZIP 다운로드 중...")

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"기업코드 다운로드 실패: {e}")
        raise

    # ZIP → CORPCODE.xml 파싱
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        xml_data = zf.read("CORPCODE.xml")

    # ---------------------------------------------------------------
    # 버그 포인트: pd.read_xml()은 corp_code를 숫자로 읽는다.
    # corp_code는 "00126380" 같은 앞자리 0이 있는 8자리 문자열.
    # int로 읽히면 126380이 되어 DART API 조회가 실패한다.
    # → 명시적으로 dtype=str 지정 후 zfill(8)로 앞자리 0 복원.
    # ---------------------------------------------------------------
    df = pd.read_xml(io.BytesIO(xml_data), dtype=str)

    # 모든 컬럼을 문자열로 강제 변환 (pandas 버전 호환)
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # corp_code는 8자리 zero-padding 보장
    df["corp_code"] = df["corp_code"].str.zfill(8)

    # stock_code가 있는 상장기업만 남김
    # (비상장 기업은 stock_code가 "nan" 또는 공백으로 남음)
    df = df[df["stock_code"].notna()]
    df = df[~df["stock_code"].isin(["nan", "None", ""])]

    logger.info(f"상장기업 수: {len(df)}개")
    return df[["corp_code", "stock_code", "corp_name"]]


def get_corp_code(stock_code: str, corp_map: pd.DataFrame) -> str | None:
    """
    stock_code → corp_code 변환.
    없으면 None 반환 (오류 raise 아님 — 로그 후 계속 진행).
    """
    row = corp_map[corp_map["stock_code"] == stock_code]
    if row.empty:
        logger.warning(f"corp_code 없음: stock_code={stock_code}")
        return None
    return row.iloc[0]["corp_code"]


# =============================================================================
# 2. 사업보고서 rcept_no 조회
# =============================================================================

def get_report_list(corp_code: str, fiscal_year: int, api_key: str) -> list[dict]:
    """
    해당 기업의 fiscal_year 사업보고서 rcept_no 목록을 반환.

    왜 fiscal_year+1 기간을 탐색하는가:
        fiscal_year=2022 사업보고서는 2023년 3~4월에 제출된다.
        따라서 bgn_de를 fiscal_year+1년 1월로 설정해야 잡힌다.
        지연 제출 기업을 고려해 6월까지 열어둔다.

    반환 예시:
        [{"rcept_no": "20230329001234", "report_nm": "사업보고서", ...}, ...]
    """
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key":        api_key,
        "corp_code":        corp_code,
        "bgn_de":           f"{fiscal_year + 1}0101",
        "end_de":           f"{fiscal_year + 1}0630",
        "pblntf_detail_ty": "A001",   # 사업보고서
        "page_count":       10,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"rcept_no 조회 실패 corp_code={corp_code}: {e}")
        return []

    if data.get("status") != "000":
        logger.warning(f"API 응답 오류 corp_code={corp_code}: {data.get('message')}")
        return []

    return data.get("list", [])


def pick_latest_report(report_list: list[dict]) -> dict | None:
    """
    동일 기업에 같은 연도 사업보고서가 여러 건 있을 경우 (정정 공시 등),
    가장 최근 것(rcept_dt 기준)을 선택.

    왜 최신 것을 선택하는가:
        정정 공시가 제출되면 원본보다 최신 정보가 담긴다.
        분석은 항상 가장 최종 버전의 보고서를 대상으로 해야 한다.
    """
    if not report_list:
        return None
    # rcept_dt 내림차순 정렬
    sorted_list = sorted(report_list, key=lambda x: x.get("rcept_dt", ""), reverse=True)
    return sorted_list[0]


# =============================================================================
# 3. ZIP 파일 다운로드
# =============================================================================

def download_report_zip(rcept_no: str, api_key: str,
                         save_dir: str,
                         max_retries: int = 3,
                         delay: float = 1.0) -> str | None:
    """
    rcept_no에 해당하는 사업보고서 ZIP을 다운로드하고, 파일 경로를 반환.
    이미 다운로드된 파일이면 재다운로드 없이 경로만 반환.

    왜 캐시(save_dir)를 사용하는가:
        동일 rcept_no를 여러 번 처리할 때 API 호출을 줄이기 위해.
        또한 실험 중 파이프라인을 재실행할 때 다운로드를 건너뛸 수 있음.

    Decision — 재시도 방식: 고정 대기 vs. exponential backoff
        → 고정 대기 선택 (단순함).
        → 대규모 수집(수백 건 이상)이면 exponential backoff 권장.
        → 현재 30~50개 샘플 수준에서는 고정으로 충분.
    """
    save_path = os.path.join(save_dir, f"{rcept_no}.zip")

    # 캐시 확인
    if os.path.exists(save_path):
        logger.info(f"캐시 사용: {rcept_no}.zip")
        return save_path

    url = "https://opendart.fss.or.kr/api/document.xml"
    params = {"crtfc_key": api_key, "rcept_no": rcept_no}

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()

            # 정상 응답인데 JSON이면 오류 메시지 (ZIP이 아님)
            if resp.headers.get("Content-Type", "").startswith("application/json"):
                logger.warning(f"ZIP 아님 (오류 응답): rcept_no={rcept_no}")
                return None

            with open(save_path, "wb") as f:
                f.write(resp.content)

            logger.info(f"다운로드 완료: {rcept_no}.zip")
            return save_path

        except requests.RequestException as e:
            logger.warning(f"다운로드 시도 {attempt}/{max_retries} 실패: {e}")
            time.sleep(delay * attempt)

    logger.error(f"모든 재시도 실패: rcept_no={rcept_no}")
    return None


def extract_xml_from_zip(zip_path: str) -> str | None:
    """
    ZIP 파일에서 주 보고서 XML 텍스트를 추출.

    왜 가장 큰 XML을 선택하는가:
        DART ZIP에는 여러 XML 파일이 들어있다.
        (예: 첨부서류, 감사보고서, 주요 보고서)
        주 사업보고서 XML이 일반적으로 가장 큰 파일이므로
        파일 크기 기준으로 선택하는 것이 실용적이다.

    Decision — 파일 크기 기준 vs. 파일명 패턴 기준:
        → 파일 크기 기준 선택.
        → 파일명 규칙이 기업/연도마다 달라 패턴 매칭이 불안정함.
        → 한계: 첨부 자료(예: 사업보고서 별첨)가 더 클 경우 오선택 가능.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
            if not xml_files:
                logger.warning(f"XML 없음: {zip_path}")
                return None

            # 가장 큰 XML 선택
            xml_files.sort(key=lambda f: zf.getinfo(f).file_size, reverse=True)
            main_xml = xml_files[0]
            raw = zf.read(main_xml)

        # 인코딩 감지 (euc-kr 또는 utf-8)
        for enc in ["utf-8", "euc-kr", "cp949"]:
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue

        logger.warning(f"인코딩 감지 실패: {zip_path}")
        return None

    except zipfile.BadZipFile:
        logger.error(f"손상된 ZIP: {zip_path}")
        return None

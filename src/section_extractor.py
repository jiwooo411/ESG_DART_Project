# =============================================================================
# src/section_extractor.py — II / IV / VI 섹션 추출 모듈
# =============================================================================
# 이 모듈이 하는 일:
#   XML 전체 텍스트에서 사업보고서의 특정 섹션(II, IV, VI)을 잘라낸다.
#
# 왜 섹션을 분리하는가:
#   전체 보고서를 분석하면 재무제표, 감사 보고서, 계약 조항 등
#   ESG와 무관한 noise가 압도적으로 많아진다.
#   섹션 필터링은 ESG 언어가 집중되는 구간만 남기는 첫 번째 관문이다.

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 섹션 제목 패턴 정의
# =============================================================================
# Decision — 정규식 vs. XML XPath 구조 파싱:
#   → 정규식 선택.
#   → DART XML 구조가 기업마다, 연도마다 비표준이어서 XPath가 일관성 없음.
#   → 섹션 제목 텍스트를 정규식으로 찾는 것이 더 robust함.
#   → 한계: 제목 표기 방식 변형(예: "Ⅱ", "제2장", "2.사업의 내용")을
#           모두 커버해야 하므로 패턴이 늘어날 수 있음.

# =============================================================================
# exp_G: 섹션 패턴 보강 (2026-05-18)
# 추가 이유: 삼성전자·SK하이닉스·LG화학 등에서 섹션 II/IV가 수백 자만 추출되는
#            문제 발견. 특수 유니코드 로마숫자(Ⅱ=U+2161 등), 제N장 표기,
#            그리고 XML 내 줄바꿈·공백 변형을 커버하기 위해 패턴 확장.
# 검증: 패턴 추가 후 반드시 섹션별 텍스트 길이 분포를 재확인할 것.
# =============================================================================
SECTION_PATTERNS = {
    "II": [
        # ASCII 로마숫자
        r"II[\.\s]*사업의\s*내용",
        # 특수 유니코드 로마숫자 (U+2161)
        r"Ⅱ[\.\s]*사업의\s*내용",
        # 제N장 표기
        r"제\s*2\s*장\s*사업의\s*내용",
        # 숫자+점 표기
        r"(?<!\d)2[\.\s]+사업의\s*내용",
        # 줄 시작 기준 느슨한 매칭
        r"사업의\s*내용에\s*관한\s*사항",
    ],
    "IV": [
        r"IV[\.\s]*이사의\s*경영진단",
        r"Ⅳ[\.\s]*이사의\s*경영진단",    # U+2163
        r"제\s*4\s*장\s*이사의\s*경영진단",
        r"(?<!\d)4[\.\s]+이사의\s*경영진단",
        # 줄임 표기 대응
        r"경영진단\s*및\s*분석의견",
        r"이사의\s*경영진단\s*및\s*분석",
    ],
    "VI": [
        r"VI[\.\s]*이사회\s*등",
        r"Ⅵ[\.\s]*이사회\s*등",           # U+2165
        r"제\s*6\s*장\s*이사회",
        r"(?<!\d)6[\.\s]+이사회\s*등",
        r"이사회\s*등\s*회사의\s*기관",
    ],
}

# 다음 주요 섹션 시작 신호 (현재 섹션의 끝을 찾기 위해 사용)
NEXT_SECTION_SIGNALS = [
    r"^[IVX]{1,4}[\.\s]+",   # 로마자 번호 섹션
    r"^Ⅰ|^Ⅱ|^Ⅲ|^Ⅳ|^Ⅴ|^Ⅵ|^Ⅶ",
    r"^제\s*\d+\s*장",
]

# PATCH: 재무 섹션 hard stop — VI 이후 재무제표 본문 유입 방지
# 이 패턴들 중 하나가 탐지되면 해당 위치를 섹션 끝 경계로 사용

FINANCIAL_STOP_PATTERNS = [
    r"VII[\.\s]*재무에\s*관한\s*사항",
    r"Ⅶ[\.\s]*재무에\s*관한\s*사항",
    r"제\s*7\s*장",
    r"VII[\.\s]",
    r"Ⅷ[\.\s]",
    r"독립된\s*감사의견\s*감사보고서",      # 감사보고서 시작 신호
    r"연결\s*재무제표\s*주석",              # 재무제표 주석 본문 시작
    r"별도\s*재무제표\s*주석",
    r"재무제표\s*작성\s*기준\s*및\s*중요한",  # 회계정책 본문 시작

    # 계정과목 행 패턴 (재무제표 본문 시작 신호)
    # "현금및현금성자산", "매출채권", "유형자산" 등이 행 시작에 나오면 재무제표 본문
    r"(?m)^(현금및현금성자산|매출채권|유형자산|무형자산|선급금|미수금)\s*[\d,]",

    # HTML anchor 기반 섹션 구분
    r'<a\s+[^>]*id=["\']?(VII|8|section_7|financial)["\']?',

    # 감사의견 본문 시작
    r"본\s*감사인은.*재무제표에\s*대하여",
    r"우리는.*재무제표를\s*감사하였습니다",
]

# =============================================================================
# 2. XML → 평문 텍스트 추출
# =============================================================================

def xml_to_plain_text(xml_str: str) -> str:
    """
    DART XML(HTML 포함)에서 태그를 제거하고 평문 텍스트를 반환.

    왜 BeautifulSoup을 사용하는가:
        DART XML은 내부에 HTML 테이블, 스타일 태그 등이 혼합되어 있어
        단순 regex 태그 제거보다 파서가 안정적이다.

    Decision — lxml 파서 vs. html.parser:
        → html.parser 선택 (기본 내장, 설치 불필요).
        → 속도가 중요하다면 lxml 권장.
    """
    try:
        soup = BeautifulSoup(xml_str, "html.parser")
        # script, style 태그 제거
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    except Exception as e:
        logger.warning(f"BeautifulSoup 파싱 실패, regex 폴백: {e}")
        text = re.sub(r"<[^>]+>", " ", xml_str)

    # 연속 공백/빈줄 정리
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l]  # 빈줄 제거
    return "\n".join(lines)


# =============================================================================
# 3. 섹션 위치 탐색
# =============================================================================

def find_section_positions(text: str) -> dict[str, int]:
    """
    텍스트에서 각 섹션(II/IV/VI)의 시작 위치(character index)를 반환.

    반환 예시: {"II": 1500, "IV": 8200, "VI": 15000}
    찾지 못한 섹션은 딕셔너리에 포함되지 않음.
    """
    positions = {}
    for section_key, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                positions[section_key] = match.start()
                break  # 첫 번째 매칭 패턴으로 결정
    return positions


def extract_sections(text: str) -> dict[str, str]:
    positions = find_section_positions(text)
    sections = {k: "" for k in SECTION_PATTERNS}

    if not positions:
        logger.warning("어떤 섹션도 찾지 못했습니다.")
        return sections

    # PATCH: 재무 섹션 hard stop 위치 탐색
    financial_stop = _find_financial_stop(text)
    if financial_stop:
        logger.info(f"  재무 섹션 stop 위치: {financial_stop}자")

    sorted_items = sorted(positions.items(), key=lambda x: x[1])

    for i, (key, start) in enumerate(sorted_items):
        if i + 1 < len(sorted_items):
            end = sorted_items[i + 1][1]
        else:
            end = len(text)

        # PATCH: 재무 stop이 현재 섹션 범위 안에 있으면 상한으로 적용
        if financial_stop and start < financial_stop < end:
            end = financial_stop
            logger.info(f"  섹션 {key}: 재무 stop 적용 → {len(text[start:end])}자")

        sections[key] = text[start:end].strip()

    for k, v in sections.items():
        status = f"{len(v)}자" if v else "미발견"
        logger.info(f"  섹션 {k}: {status}")

    return sections


# =============================================================================
# 4. 편의 함수: XML → 섹션 딕셔너리 (원스텝)
# =============================================================================

def _find_financial_stop(text: str) -> Optional[int]:
    """
    재무제표/감사보고서 시작 위치 중 가장 빠른 것을 반환.
    VI 섹션이 재무 본문을 포함하는 것을 막는 hard stop.
    탐지 실패 시 None 반환 (기존 동작 유지).
    """
    stops = []
    for pattern in FINANCIAL_STOP_PATTERNS:
        m = re.search(pattern, text)
        if m:
            stops.append(m.start())
    return min(stops) if stops else None

def xml_to_sections(xml_str: str) -> tuple[str, dict[str, str]]:
    """
    XML 문자열을 받아 (평문 전체 텍스트, 섹션 딕셔너리)를 반환.
    수집 파이프라인에서 단일 호출로 쓸 수 있도록 래핑.
    """
    plain_text = xml_to_plain_text(xml_str)
    sections = extract_sections(plain_text)
    return plain_text, sections

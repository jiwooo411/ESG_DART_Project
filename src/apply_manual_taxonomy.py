# =============================================================================
# src/apply_manual_taxonomy.py
# AMBIGUOUS 토큰 전문가 자동 보강 스크립트
# =============================================================================
# 작성 원칙:
#   ESG disclosure variation measurement 관점에서 판단.
#   false negative (G-signal 삭제) > false positive (noise 보존).
#   IDF/빈도만으로 G-signal을 GENERIC 처리하지 않는다.
#   진정으로 애매한 것만 AMBIGUOUS 유지.
#
# 실행:
#   python -m src.apply_manual_taxonomy

import os, sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# =============================================================================
# 1. 전문가 분류 사전
# =============================================================================
# 판단 기준:
#   G_SIGNAL:    corporate governance disclosure 메커니즘 핵심 용어
#                이사회 기관, 이사 선임/보수, 주주총회, 공시 투명성 등
#                IDF=0이어도 (전문서 등장) G-signal 유지
#   ESG_SIGNAL:  E/S 도메인 고특이성 용어
#                탄소·에너지·환경·사회·안전 계열
#   BOILERPLATE: 재무제표, 회계, 법률 의무공시 행정 용어
#                ESG/G specificity 없고 disclosure variation 설명력 낮음
#   GENERIC:     사업보고서 일반어 (지시어, 시제, 일반 사업 용어)
#                ESG disclosure와 무관한 business-general 표현
#   AMBIGUOUS:   진정한 경계 토큰만 유지

EXPERT_MAP: dict[str, tuple[str, str]] = {
    # =========================================================================
    # G_SIGNAL — Governance disclosure 핵심
    # 이사회 기관 / 이사 / 위원회 / 주주총회 / 보수 / 공시 / 규정 / 절차
    # =========================================================================
    "주주":     ("G_SIGNAL",   "주주권리·주주총회·이해관계자 거버넌스 핵심. 빈도 높아도 G-domain."),
    "총회":     ("G_SIGNAL",   "주주총회 = G-domain 핵심 의사결정 기구. IDF 낮아도 유지."),
    "위원회":   ("G_SIGNAL",   "감사위원회·ESG위원회·보수위원회 등 거버넌스 기구 핵심."),
    "결의":     ("G_SIGNAL",   "이사회/주주총회 결의 = G-domain 핵심 의사결정 행위."),
    "선임":     ("G_SIGNAL",   "이사/감사위원 선임 = 거버넌스 인적 구성 핵심."),
    "위원":     ("G_SIGNAL",   "이사회 위원, 감사위원 등 거버넌스 기구 구성원."),
    "보수":     ("G_SIGNAL",   "임원 보수 = G-domain 핵심 공시 항목 (KCGS 평가 직결)."),
    "보상":     ("G_SIGNAL",   "임원 보상·성과연동 보상체계 = G-domain 핵심."),
    "정관":     ("G_SIGNAL",   "정관 = 거버넌스 최상위 내부규범. 의무적 G-domain 공시."),
    "승인":     ("G_SIGNAL",   "이사회/주주총회 승인 = G-domain 의사결정 핵심 행위."),
    "규정":     ("G_SIGNAL",   "내부규정·거버넌스 규정 = G-domain 내부통제 체계."),
    "공시":     ("G_SIGNAL",   "정보공시 = 투명성 G-domain 핵심. 빈도 높아도 disclosure 신호."),
    "의결":     ("G_SIGNAL",   "의결권 행사 = 주주·이사회 핵심 G-domain 행위."),
    "사외":     ("G_SIGNAL",   "'사외이사' 복합어 핵심. 이사회 독립성 G-domain."),
    "임원":     ("G_SIGNAL",   "임원 구성·임원 보수·임원 선임 = G-domain 공시 핵심."),
    "내부":     ("G_SIGNAL",   "'내부통제', '내부감사' compound G-domain. 절대 제거 금지."),
    "추천":     ("G_SIGNAL",   "이사후보 추천위원회 = G-domain 이사 선임 절차 핵심."),
    "기관":     ("G_SIGNAL",   "'이사회 등 회사의 기관' (VI섹션 제목). G-domain 직결."),
    "지배":     ("G_SIGNAL",   "'지배구조' compound 핵심. G-domain signal."),
    "감사인":   ("G_SIGNAL",   "외부감사인 = 감사·독립성 G-domain. 재무가 아닌 거버넌스 맥락."),
    "구성":     ("G_SIGNAL",   "이사회 구성, 위원회 구성 = G-domain 핵심."),
    "개정":     ("G_SIGNAL",   "정관 개정, 규정 개정 = G-domain 내부규범 변경."),
    "독립":     ("G_SIGNAL",   "이사회 독립성 = KCGS G 핵심 평가 기준."),
    "행사":     ("G_SIGNAL",   "의결권 행사 = G-domain 핵심. IDF 낮아도 유지."),
    "임기":     ("G_SIGNAL",   "이사 임기 = G-domain 이사 선임/지속성 핵심."),
    "정기":     ("G_SIGNAL",   "정기주주총회, 정기이사회 = G-domain 정기 의사결정 기구."),
    "안건":     ("G_SIGNAL",   "이사회/주주총회 안건 = G-domain 의사결정 내용."),
    "개최":     ("G_SIGNAL",   "이사회/주주총회 개최 = G-domain 기구 운영 행위."),
    "위임":     ("G_SIGNAL",   "의결권 위임(proxy) = G-domain 주주권리 행사."),
    "상법":     ("G_SIGNAL",   "상법 = 거버넌스 법적 근거. 법령준수 G-domain 직결."),
    "법령":     ("G_SIGNAL",   "법령준수 = G-domain 준법경영 핵심."),
    "준수":     ("G_SIGNAL",   "법령·규정 준수 = G-domain 컴플라이언스 핵심."),
    "투명":     ("G_SIGNAL",   "투명성 = G-domain ESG_PRESERVE 항목. 절대 유지."),
    "경영진":   ("G_SIGNAL",   "경영진 = 이사회·경영진 관계, G-domain 책임 구조."),
    "역할":     ("G_SIGNAL",   "이사회 역할, 감사위원회 역할 = G-domain 핵심 공시."),
    "집행":     ("G_SIGNAL",   "이사회 집행, 업무집행 = G-domain 경영 감독 구조."),
    "제도":     ("G_SIGNAL",   "거버넌스 제도·내부통제 제도 = G-domain 체계."),
    "절차":     ("G_SIGNAL",   "의사결정 절차, 감사 절차 = G-domain 내부통제."),
    "설치":     ("G_SIGNAL",   "위원회 설치 = G-domain 기구 설립. VI섹션 핵심 맥락."),
    "전문가":   ("G_SIGNAL",   "이사회 전문가 구성 = G-domain 이사 다양성·전문성 공시."),
    "투자자":   ("G_SIGNAL",   "투자자 관계(IR) = G-domain 이해관계자 커뮤니케이션."),
    "성과":     ("G_SIGNAL",   "ESG/이사회 성과평가 = G-domain 핵심. compound: 성과연동 보수."),
    "평가":     ("G_SIGNAL",   "이사회 평가, ESG 평가 = G-domain 핵심 공시."),
    "가치":     ("G_SIGNAL",   "주주가치, 기업가치 = G-domain 핵심 경영 목표."),
    "동의":     ("G_SIGNAL",   "이사회/주주 동의 = G-domain 의사결정 행위."),
    "보고":     ("G_SIGNAL",   "이사회 보고, 공시 보고 = G-domain reporting 핵심."),
    "권리":     ("G_SIGNAL",   "주주권리 = G-domain 핵심. 의결권, 정보청구권 등."),
    "선도":     ("GENERIC",    "선도(leading) 단독 사용 시 일반어. ESG 선도는 복합어."),
    "사내":     ("G_SIGNAL",   "사내이사 = 이사회 구성 G-domain. 사내 단독도 G compound."),
    "후보":     ("G_SIGNAL",   "이사후보, 감사위원후보 = 선임 절차 G-domain."),
    "의사":     ("G_SIGNAL",   "의사결정, 의사록 = G-domain 이사회 운영."),
    "개최":     ("G_SIGNAL",   "이사회/총회 개최 = G-domain 기구 운영."),

    # =========================================================================
    # ESG_SIGNAL — E/S 도메인 특이성
    # =========================================================================
    "환경":     ("ESG_SIGNAL", "E-domain 핵심. '환경경영', '환경리스크'. IDF 낮아도 E signal."),
    "배출":     ("ESG_SIGNAL", "온실가스 배출 = E-domain 핵심. carbon emission."),
    "배출량":   ("ESG_SIGNAL", "배출량 = 탄소중립 E-domain 핵심 KPI."),
    "에너지":   ("ESG_SIGNAL", "에너지 = E-domain 핵심. 에너지 효율, 재생에너지."),
    "재생":     ("ESG_SIGNAL", "재생에너지 compound 핵심. E-domain."),
    "사회":     ("ESG_SIGNAL", "S-domain 핵심. '사회공헌', '사회적 책임'. ESG S 직결."),
    "지속":     ("ESG_SIGNAL", "'지속가능경영', '지속가능성' compound. ESG 핵심 표현."),
    "녹색":     ("ESG_SIGNAL", "녹색경영, 녹색금융, 탄소중립 E-domain."),
    "위험":     ("ESG_SIGNAL", "ESG 리스크, 기후변화 위험 = ESG risk disclosure 핵심."),
    "물질":     ("ESG_SIGNAL", "유해물질, 화학물질 = E-domain 환경규제 공시."),
    "오염":     ("ESG_SIGNAL", "대기오염, 수질오염 = E-domain 환경 공시."),
    "공급":     ("ESG_SIGNAL", "공급망 = S-domain 공급망 관리, 협력사 ESG."),
    "전력":     ("ESG_SIGNAL", "전력 = 에너지 전환 E-domain. RE100, 재생전력."),
    "효율":     ("ESG_SIGNAL", "에너지효율 = E-domain 핵심. 온실가스 감축 수단."),
    "전환":     ("ESG_SIGNAL", "에너지 전환, 저탄소 전환 = E-domain 핵심 전략."),
    "화학":     ("ESG_SIGNAL", "화학물질 관리 = E-domain 유해물질 공시."),
    "목표":     ("ESG_SIGNAL", "탄소중립 목표, ESG 목표 = E/S domain KPI."),
    "지표":     ("ESG_SIGNAL", "ESG KPI, 비재무 지표 = ESG 성과 측정 핵심."),
    "체계":     ("ESG_SIGNAL", "ESG 관리체계, 안전보건 체계 = E/S domain 관리시스템."),
    "대응":     ("ESG_SIGNAL", "기후변화 대응, 탄소중립 대응 = E-domain 핵심."),
    "달성":     ("ESG_SIGNAL", "ESG 목표 달성 = 비재무 성과 달성 disclosure."),
    "기여":     ("ESG_SIGNAL", "사회 기여, ESG 기여 = S-domain 사회공헌 disclosure."),
    "책임":     ("ESG_SIGNAL", "기업의 사회적 책임(CSR) = S-domain 핵심."),
    "강화":     ("ESG_SIGNAL", "ESG 정책 강화, 안전 강화 = E/S 공시 개선 신호."),
    "이행":     ("ESG_SIGNAL", "ESG 약속 이행, 탄소중립 이행 = E/S commitment."),
    "활동":     ("ESG_SIGNAL", "ESG 활동, 사회공헌 활동, 환경 활동 = E/S disclosure."),
    "발전":     ("ESG_SIGNAL", "지속가능발전 + 발전소(전력). ESG 맥락 우선 유지."),
    "기후":     ("ESG_SIGNAL", "기후변화 = ESG_PRESERVE compound. E-domain 핵심."),
    "지원":     ("ESG_SIGNAL", "사회적 지원, 임직원 지원 = S-domain 사회공헌 disclosure."),
    "교육":     ("ESG_SIGNAL", "임직원 교육훈련 = S-domain 인적자본 ESG 핵심."),
    "참여":     ("ESG_SIGNAL", "이해관계자 참여, 사회참여 = S-domain stakeholder engagement."),
    "제고":     ("ESG_SIGNAL", "주주가치 제고, 지속가능성 제고 = ESG/G disclosure 핵심."),
    "다양":     ("ESG_SIGNAL", "다양성 = S-domain D&I 핵심. 이사회 다양성도 G."),
    "보호":     ("ESG_SIGNAL", "환경보호, 소비자보호, 데이터보호 = E/S/G domain."),
    "관리":     ("ESG_SIGNAL", "ESG 리스크 관리, 환경 관리 = E/S disclosure 핵심."),
    "규제":     ("ESG_SIGNAL", "환경규제, 탄소규제 = E-domain 규제 대응 공시."),
    "구축":     ("ESG_SIGNAL", "ESG 체계 구축, 내부통제 구축 = E/S/G 관리시스템."),
    "개선":     ("ESG_SIGNAL", "환경 개선, ESG 성과 개선 = E/S disclosure."),
    "혁신":     ("ESG_SIGNAL", "지속가능 혁신, 친환경 혁신 = E/S domain."),
    "가스":     ("ESG_SIGNAL", "온실가스 compound 핵심. 탄소 배출 E-domain."),
    "연료":     ("ESG_SIGNAL", "연료 전환, 화석연료 = E-domain 에너지 공시."),
    "추진":     ("ESG_SIGNAL", "ESG 정책 추진, 탄소중립 추진 = E/S/G 실행 신호."),
    "설비":     ("ESG_SIGNAL", "환경설비, 방지시설 = E-domain 환경 투자. IDF 중상위."),
    "처리":     ("ESG_SIGNAL", "폐기물 처리, 오염물질 처리 = E-domain 핵심."),
    "인증":     ("ESG_SIGNAL", "환경인증, ISO 인증, ESG 인증 = E/S/G 검증 disclosure."),
    "노력":     ("ESG_SIGNAL", "ESG 노력, 탄소중립 노력 = E/S disclosure 의지 표현."),
    "추가":     ("GENERIC",    "일반 추가(additional) - ESG 특이성 없음."),
    "수립":     ("ESG_SIGNAL", "ESG 전략 수립, 탄소중립 계획 수립 = E/S/G 전략 disclosure."),
    "조직":     ("G_SIGNAL",   "ESG 위원회 조직, 이사회 조직 = G-domain 구조."),
    "역량":     ("ESG_SIGNAL", "ESG 역량, 안전 역량, 전문 역량 = E/S disclosure."),
    "협력":     ("ESG_SIGNAL", "공급망 협력, 이해관계자 협력 = S-domain 상생."),
    "전략":     ("ESG_SIGNAL", "ESG 전략, 지속가능 전략 = E/S/G 핵심 전략 disclosure."),
    "정책":     ("ESG_SIGNAL", "ESG 정책, 환경 정책, 인권 정책 = E/S/G 핵심 disclosure."),
    "목적":     ("GENERIC",    "일반 목적(purpose) - ESG 특이성 낮음."),

    # =========================================================================
    # BOILERPLATE — 재무/법무 의무공시 (ESG specificity 없음)
    # =========================================================================
    "당기":     ("BOILERPLATE","당기순이익, 당기말 = 재무회계 용어. ESG 무관."),
    "연결":     ("BOILERPLATE","연결재무제표, 연결법인 = 재무보고 핵심 boilerplate."),
    "재무":     ("BOILERPLATE","재무상태표, 재무성과 = 재무제표 boilerplate."),
    "자산":     ("BOILERPLATE","유동자산, 비유동자산 = 재무제표 항목. ESG 무관."),
    "자본":     ("BOILERPLATE","자본잉여금, 자본구조 = 재무 항목."),
    "이익":     ("BOILERPLATE","영업이익, 당기순이익 = 재무성과. ESG 무관."),
    "수익":     ("BOILERPLATE","매출수익, 금융수익 = 재무 항목."),
    "손익":     ("BOILERPLATE","손익계산서, 기타포괄손익 = 재무제표 boilerplate."),
    "지급":     ("BOILERPLATE","배당금 지급, 원리금 지급 = 재무 의무이행."),
    "금액":     ("BOILERPLATE","재무 금액, 장부금액 = 재무제표 boilerplate."),
    "장부":     ("BOILERPLATE","장부금액, 장부가치 = 재무회계 전용 용어."),
    "원가":     ("BOILERPLATE","매출원가, 제조원가 = 재무 항목."),
    "채무":     ("BOILERPLATE","금융채무, 계약채무 = 재무 부채 항목."),
    "채권":     ("BOILERPLATE","매출채권, 금융채권 = 재무 자산 항목."),
    "자금":     ("BOILERPLATE","운전자금, 자금 조달 = 재무 활동."),
    "증권":     ("BOILERPLATE","금융증권, 유가증권 = 재무 투자 항목."),
    "주식":     ("BOILERPLATE","보통주, 우선주 = 재무 자본 항목."),
    "발행":     ("BOILERPLATE","채권 발행, 주식 발행 = 재무 자본 조달. 의무공시."),
    "취득":     ("BOILERPLATE","자산 취득, 지분 취득 = 재무 거래."),
    "보유":     ("BOILERPLATE","유가증권 보유, 지분 보유 = 재무 자산 현황."),
    "처분":     ("BOILERPLATE","자산 처분, 지분 처분 = 재무 거래."),
    "보증":     ("BOILERPLATE","지급보증, 보증채무 = 재무 우발부채."),
    "약정":     ("BOILERPLATE","차입 약정, 이자율 약정 = 재무 계약."),
    "계약":     ("BOILERPLATE","재무계약, 주식매매계약 = 법무·재무 의무."),
    "서류":     ("BOILERPLATE","제출 서류, 공시 서류 = 행정 boilerplate."),
    "기재":     ("BOILERPLATE","공시 기재, 사항 기재 = 행정 boilerplate."),
    "작성":     ("BOILERPLATE","재무제표 작성, 보고서 작성 = 행정 boilerplate."),
    "제출":     ("BOILERPLATE","공시 제출, 보고서 제출 = 행정 boilerplate."),
    "산정":     ("BOILERPLATE","손상차손 산정, 공정가치 산정 = 재무회계."),
    "회계":     ("BOILERPLATE","회계처리, 회계기준 = 재무제표 boilerplate."),
    "법인세":   ("BOILERPLATE","법인세 = 재무 세무 항목. ESG 무관."),
    "통화":     ("BOILERPLATE","기능통화, 외화환산 = 재무회계."),
    "리스":     ("BOILERPLATE","리스부채, 사용권자산 = IFRS16 재무 항목."),
    "스왑":     ("BOILERPLATE","금리스왑, 통화스왑 = 파생금융상품."),
    "신주":     ("BOILERPLATE","신주인수권, 신주발행 = 자본 조달 재무 항목."),
    "증자":     ("BOILERPLATE","유상증자, 무상증자 = 자본 조달 재무 거래."),
    "배당":     ("BOILERPLATE","배당금 = 재무 주주환원. G signal 아님 (ESG 관점에서)."),
    "주식회사": ("BOILERPLATE","'주식회사' 법인격 표기 = 행정 boilerplate."),
    "주석":     ("BOILERPLATE","재무제표 주석 = 재무공시 행정 boilerplate."),
    "표시":     ("BOILERPLATE","재무제표 표시 방법 = 회계 기준 boilerplate."),
    "측정":     ("BOILERPLATE","공정가치 측정, 손상 측정 = 재무회계 boilerplate."),
    "분류":     ("BOILERPLATE","재무항목 분류, 리스 분류 = 재무회계."),
    "추정":     ("BOILERPLATE","회계추정, 잔존가치 추정 = 재무회계."),
    "매수":     ("BOILERPLATE","자기주식 매수, 주식 매수 = 재무 거래."),
    "매도":     ("BOILERPLATE","주식 매도, 자산 매도 = 재무 거래."),
    "종속":     ("BOILERPLATE","종속회사, 종속기업 = 연결재무 보고."),
    "별도":     ("BOILERPLATE","별도재무제표 = 재무 보고 형태."),
    "유동":     ("BOILERPLATE","유동자산, 유동부채 = 재무제표 항목."),
    "보통주":   ("BOILERPLATE","보통주, 보통주 자본금 = 재무 자본 항목."),
    "환율":     ("BOILERPLATE","외환위험, 환율 변동 = 재무 리스크 관리."),
    "신용":     ("BOILERPLATE","신용위험, 신용등급 = 재무 리스크."),
    "소유":     ("BOILERPLATE","지분소유, 소유구조 = 재무 지분 항목."),
    "매출":     ("BOILERPLATE","매출액, 매출원가 = 재무 성과 항목."),
    "영업":     ("BOILERPLATE","영업이익, 영업활동 = 재무 성과 항목."),
    "인수":     ("BOILERPLATE","기업인수, 지분인수 = 재무 M&A 거래."),
    "매각":     ("BOILERPLATE","자산매각, 지분매각 = 재무 거래."),
    "현금":     ("BOILERPLATE","현금흐름, 현금 = 재무제표 항목."),
    "부문":     ("BOILERPLATE","사업부문, 영업부문 = 재무 세그먼트."),
    "분기":     ("BOILERPLATE","분기 보고, 분기 실적 = 재무 보고 주기."),
    "법인":     ("BOILERPLATE","법인, 법인격 = 재무·법무 행정 용어."),
    "비용":     ("BOILERPLATE","운영비용, 인건비 = 재무 항목."),
    "조달":     ("BOILERPLATE","자금조달, 재원조달 = 재무 활동."),
    "중요":     ("BOILERPLATE","중요성(materiality) = 재무회계 판단 기준."),
    "실체":     ("BOILERPLATE","회계실체, 연결실체 = 재무회계 boilerplate."),
    "분할":     ("BOILERPLATE","인적분할, 물적분할 = 재무 구조 변경."),
    "합병":     ("BOILERPLATE","기업합병 = 재무 구조 변경."),
    "납부":     ("BOILERPLATE","세금 납부, 과태료 납부 = 재무 의무."),
    "지분":     ("BOILERPLATE","지분율, 지분가치 = 재무 자본 항목."),
    "이자":     ("BOILERPLATE","이자비용, 이자수익 = 재무 항목."),
    "충당":     ("BOILERPLATE","충당부채, 충당금 = 재무회계 항목."),
    "계량":     ("BOILERPLATE","계량 측정, 계리 추정 = 재무/보험 actuarial."),
    "손익":     ("BOILERPLATE","손익계산 = 재무제표 핵심 boilerplate."),
    "비율":     ("BOILERPLATE","재무비율, 부채비율 = 재무 분석."),
    "출자":     ("BOILERPLATE","출자금, 출자비율 = 재무 자본 항목."),
    "보험":     ("BOILERPLATE","손해보험, 보험료 = 재무 의무비용."),
    "한도":     ("BOILERPLATE","신용한도, 차입한도 = 재무 계약 조건."),
    "이자":     ("BOILERPLATE","이자율, 이자비용 = 재무 항목."),
    "할당":     ("BOILERPLATE","비용 할당, 원가 배분 = 재무회계."),
    "의거":     ("BOILERPLATE","규정에 의거 = 법적 boilerplate 표현."),
    "참조":     ("BOILERPLATE","주석 참조, 공시 참조 = 재무공시 행정."),
    "참고":     ("BOILERPLATE","참고사항 = 재무공시 행정 boilerplate."),
    "유의":     ("BOILERPLATE","유의적 영향 = 재무회계 중요성 boilerplate."),
    "평균":     ("BOILERPLATE","가중평균, 평균환율 = 재무 계산 용어."),
    "정정":     ("BOILERPLATE","공시 정정, 재무 정정 = 행정 boilerplate."),
    "수정":     ("BOILERPLATE","회계 수정, 오류 수정 = 재무회계 boilerplate."),
    "수익":     ("BOILERPLATE","매출수익, 금융수익 = 재무 항목."),
    "옵션":     ("BOILERPLATE","주식매수선택권(스톡옵션), 파생상품 = 재무."),
    "스왑":     ("BOILERPLATE","금리스왑 = 파생금융상품 boilerplate."),
    "보통주":   ("BOILERPLATE","보통주 자본 = 재무 항목."),
    "전년":     ("BOILERPLATE","전년 대비 = 재무 비교 공시 boilerplate."),
    "급여":     ("BOILERPLATE","임직원 급여 = 재무 인건비 항목 (보수 보고서 아님)."),
    "인식":     ("BOILERPLATE","수익인식, 비용인식 = 재무회계 boilerplate."),
    "사유":     ("BOILERPLATE","공시 사유, 변경 사유 = 행정 boilerplate."),
    "조건":     ("BOILERPLATE","계약조건, 차입조건 = 재무 계약."),
    "동일":     ("BOILERPLATE","동일 기준 적용 = 재무회계 일관성 boilerplate."),
    "청구":     ("BOILERPLATE","손해배상 청구, 소송 청구 = 법무 boilerplate."),
    "수정":     ("BOILERPLATE","재무제표 수정 = 재무회계 보고."),
    "선택":     ("BOILERPLATE","회계정책 선택 = 재무회계 boilerplate."),
    "변동":     ("BOILERPLATE","자본변동, 환율변동 = 재무 항목."),
    "장기":     ("BOILERPLATE","장기부채, 장기차입금 = 재무 항목."),
    "분기":     ("BOILERPLATE","분기 재무 보고 = 재무 공시 주기."),
    "투입":     ("BOILERPLATE","원가 투입, 자원 투입 = 재무 원가 항목."),
    "집행":     ("G_SIGNAL",   "업무 집행, 이사회 집행 → 오버라이드: G_SIGNAL 우선."),
    "수행":     ("GENERIC",    "업무 수행 = 일반 행위 동사. ESG 특이성 없음."),
    "발행":     ("BOILERPLATE","채권/주식 발행 = 재무 자본 조달."),
    "계열":     ("BOILERPLATE","계열사, 계열회사 = 연결재무 범위. G보다 재무 boilerplate."),
    "증자":     ("BOILERPLATE","유상/무상 증자 = 자본 변동 재무 항목."),
    "매각":     ("BOILERPLATE","자산/사업 매각 = 재무 거래."),
    "합병":     ("BOILERPLATE","기업합병 = 재무 구조 변경."),
    "전지":     ("GENERIC",    "이차전지, 전고체전지 = 특정 산업 제품. ESG 특이성 낮음."),
    "솔루션":   ("GENERIC",    "제품/서비스 솔루션 = 일반 사업 용어."),
    "플랫폼":   ("GENERIC",    "IT 플랫폼, 서비스 플랫폼 = 일반 사업 용어."),
    "네이버":   ("GENERIC",    "특정 기업명 = 식별자. TF-IDF 피처 제외 대상."),
    "한전":     ("GENERIC",    "특정 기업명(한국전력) = 식별자."),
    "SK이노베이션": ("GENERIC","특정 기업명 = 식별자."),

    # =========================================================================
    # GENERIC — 사업보고서 일반어 (ESG/G specificity 없음)
    # =========================================================================
    "당사":     ("GENERIC",    "당사 = 자기지칭 대명사. ESG 분석 대상 아님."),
    "회사":     ("GENERIC",    "회사 = 자기지칭 대명사. ESG 분석 대상 아님."),
    "사업":     ("GENERIC",    "사업 = 보고서 일반어. ESG 특이성 없음."),
    "기준":     ("GENERIC",    "기준 = 일반 기준어. ESG 특이성 없음."),
    "기업":     ("GENERIC",    "기업 = 일반 지칭. ESG 특이성 없음."),
    "경우":     ("GENERIC",    "경우 = 조건 표현 일반어."),
    "사항":     ("GENERIC",    "사항 = 공시 사항 일반어. 행정 표현."),
    "가능":     ("GENERIC",    "가능 = 일반 가능성 표현."),
    "포함":     ("GENERIC",    "포함 = 일반 포함 표현."),
    "결정":     ("GENERIC",    "결정 = 일반 결정 표현."),
    "기간":     ("GENERIC",    "기간 = 일반 시간 표현."),
    "내용":     ("GENERIC",    "내용 = 일반 내용 표현."),
    "결과":     ("GENERIC",    "결과 = 일반 결과 표현."),
    "상황":     ("GENERIC",    "상황 = 일반 상황 표현."),
    "현황":     ("GENERIC",    "현황 = 사업 현황 일반어."),
    "최대":     ("GENERIC",    "최대 = 일반 수량 표현."),
    "다음":     ("GENERIC",    "다음 = 순서 지시어."),
    "현재":     ("GENERIC",    "현재 = 시제 표현."),
    "이후":     ("GENERIC",    "이후 = 시제 표현."),
    "이상":     ("GENERIC",    "이상 = 수량 비교 표현."),
    "향후":     ("GENERIC",    "향후 = 시제/방향 표현."),
    "국내":     ("GENERIC",    "국내 = 지역 범위 표현."),
    "최근":     ("GENERIC",    "최근 = 시제 표현."),
    "해외":     ("GENERIC",    "해외 = 지역 범위 표현."),
    "주요":     ("GENERIC",    "주요 = 일반 강조 표현."),
    "발생":     ("GENERIC",    "발생 = 일반 발생 표현."),
    "기타":     ("GENERIC",    "기타 = 열거 일반어."),
    "일부":     ("GENERIC",    "일부 = 수량 표현."),
    "가격":     ("GENERIC",    "가격 = 시장/재무 일반 표현."),
    "성장":     ("GENERIC",    "성장 = 사업 일반어. ESG 특이성 없음."),
    "시장":     ("GENERIC",    "시장 = 사업 환경 일반어."),
    "산업":     ("GENERIC",    "산업 = 사업 분류 일반어."),
    "금융":     ("GENERIC",    "금융 = 사업 분야 일반어. ESG 특이성 낮음."),
    "제품":     ("GENERIC",    "제품 = 사업 아이템 일반어."),
    "상품":     ("GENERIC",    "상품 = 사업 아이템 일반어."),
    "수준":     ("GENERIC",    "수준 = 일반 수준 표현."),
    "방법":     ("GENERIC",    "방법 = 일반 방법론 표현."),
    "범위":     ("GENERIC",    "범위 = 일반 범위 표현."),
    "경쟁력":   ("GENERIC",    "경쟁력 = 사업 일반어. ESG 특이성 없음."),
    "기술":     ("GENERIC",    "기술 = 사업/R&D 일반어."),
    "개발":     ("GENERIC",    "개발 = 사업 일반어."),
    "정보":     ("GENERIC",    "정보 = 일반 정보. 비재무정보는 복합어로 확인."),
    "서비스":   ("GENERIC",    "서비스 = 사업 아이템 일반어."),
    "최초":     ("GENERIC",    "최초 = 시제 표현."),
    "글로벌":   ("GENERIC",    "글로벌 = 지역 범위 일반어."),
    "고객":     ("GENERIC",    "고객 = 사업 대상 일반어. (고객 ESG는 compound)"),
    "세계":     ("GENERIC",    "세계 = 지역 범위 표현."),
    "규모":     ("GENERIC",    "규모 = 일반 크기 표현."),
    "시스템":   ("GENERIC",    "시스템 = 일반 IT/운영 용어."),
    "기초":     ("GENERIC",    "기초 = 일반 기준/시작 표현."),
    "수요":     ("GENERIC",    "수요 = 시장/사업 일반어."),
    "진행":     ("GENERIC",    "진행 = 일반 진행 표현."),
    "완료":     ("GENERIC",    "완료 = 일반 완료 표현."),
    "능력":     ("GENERIC",    "능력 = 일반 역량 표현."),
    "분야":     ("GENERIC",    "분야 = 일반 분야 표현."),
    "항목":     ("GENERIC",    "항목 = 일반 목록 표현."),
    "방식":     ("GENERIC",    "방식 = 일반 방법론 표현."),
    "확보":     ("GENERIC",    "확보 = 일반 자원 획득 표현."),
    "확인":     ("GENERIC",    "확인 = 일반 검증 표현."),
    "국가":     ("GENERIC",    "국가 = 지역 범위 표현."),
    "기대":     ("GENERIC",    "기대 = 일반 예측 표현."),
    "중심":     ("GENERIC",    "중심 = 일반 강조 표현."),
    "핵심":     ("GENERIC",    "핵심 = 일반 강조 표현."),
    "도입":     ("GENERIC",    "도입 = 일반 채택 표현."),
    "기본":     ("GENERIC",    "기본 = 일반 기본 표현."),
    "확대":     ("GENERIC",    "확대 = 일반 확장 표현."),
    "제공":     ("GENERIC",    "제공 = 일반 제공 표현."),
    "보유":     ("BOILERPLATE","보유 지분/자산 → 재무 항목 우선."),
    "감소":     ("GENERIC",    "감소 = 일반 수량 변화 표현."),
    "증가":     ("GENERIC",    "증가 = 일반 수량 변화 표현."),
    "관계":     ("GENERIC",    "관계 = 일반 관계 표현."),
    "경기":     ("GENERIC",    "경기 = 거시경제 일반 표현."),
    "최종":     ("GENERIC",    "최종 = 일반 순서 표현."),
    "최소":     ("GENERIC",    "최소 = 일반 수량 표현."),
    "공공":     ("GENERIC",    "공공 = 일반 공공 표현."),
    "향상":     ("GENERIC",    "향상 = 일반 개선 표현."),
    "창출":     ("GENERIC",    "창출 = 일반 가치창출 표현."),
    "수량":     ("GENERIC",    "수량 = 일반 수량 표현."),
    "안건":     ("G_SIGNAL",   "이미 G_SIGNAL 처리됨."),
    "분석":     ("GENERIC",    "분석 = 일반 분석 표현."),
    "경쟁":     ("GENERIC",    "경쟁 = 사업 환경 일반어."),
    "특수":     ("GENERIC",    "특수 = 일반 특성 표현."),
    "조치":     ("GENERIC",    "조치 = 일반 대응 조치 표현."),
    "이용":     ("GENERIC",    "이용 = 일반 사용 표현."),
    "수상":     ("GENERIC",    "수상(award) = 일반 성과 표현."),
    "사업장":   ("GENERIC",    "사업장 = 사업 운영 장소. ESG 특이성 낮음."),
    "자원":     ("GENERIC",    "자원 = 일반 자원 표현. (천연자원은 compound로 확인)"),
    "특성":     ("GENERIC",    "특성 = 일반 특성 표현."),
    "전문":     ("GENERIC",    "전문 = 일반 전문성 표현."),
    "반도체":   ("GENERIC",    "반도체 = 특정 산업 제품."),
    "배터리":   ("GENERIC",    "배터리 = 특정 산업 제품. (EV 전환은 E-signal 복합어)"),
    "자동차":   ("GENERIC",    "자동차 = 특정 산업 제품/기업."),
    "공정":     ("GENERIC",    "공정(process/fair) - 맥락에 따라 다르나 일반적으로 GENERIC."),
    "연도":     ("GENERIC",    "연도 = 시제 표현."),
    "실적":     ("GENERIC",    "실적 = 재무/사업 성과 일반어."),
    "실시":     ("GENERIC",    "실시 = 일반 실행 표현."),
    "기간":     ("GENERIC",    "기간 = 시간 범위 일반어."),
    "상기":     ("GENERIC",    "상기 = 지시 대명사 일반어."),
    "이용자":   ("GENERIC",    "이용자 = 서비스 이용 대상 일반어."),
    "소재":     ("GENERIC",    "소재지, 소재 = 위치/재료 일반어."),
    "미국":     ("GENERIC",    "미국 = 국가명. 특이성 없음."),
    "한국":     ("GENERIC",    "한국 = 국가명. 특이성 없음."),
    "국내외":   ("GENERIC",    "국내외 = 지역 범위 일반어."),
    "대비":     ("GENERIC",    "대비 = 비교 표현."),
    "부과":     ("BOILERPLATE","과태료 부과 = 법무 행정 boilerplate."),
    "과태료":   ("BOILERPLATE","과태료 = 법무 행정 boilerplate."),
    "소송":     ("BOILERPLATE","소송 = 법무 우발부채 boilerplate."),
    "소비자":   ("GENERIC",    "소비자 = 일반 사업 대상. (소비자 보호는 compound)"),
    "미래":     ("GENERIC",    "미래 = 시제 표현."),
    "단계":     ("GENERIC",    "단계 = 일반 단계 표현."),
    "등급":     ("GENERIC",    "등급 = 신용등급, ESG등급 - 맥락 불명확. GENERIC."),
    "상장":     ("GENERIC",    "주식 상장 = 재무 거래. ESG 특이성 없음."),
    "조사":     ("GENERIC",    "조사 = 일반 조사 표현."),
    "이외":     ("GENERIC",    "이외 = 열거 표현."),
    "재고":     ("BOILERPLATE","재고자산 = 재무 항목."),
    "원가":     ("BOILERPLATE","제조원가 = 재무 항목."),
    "국제":     ("GENERIC",    "국제 = 일반 국제 표현."),
    "건설":     ("GENERIC",    "건설 = 특정 산업. ESG 특이성 낮음."),
    "공동":     ("GENERIC",    "공동 = 일반 공동 표현."),
    "정부":     ("GENERIC",    "정부 = 외부 이해관계자 일반어."),
    "생산":     ("GENERIC",    "생산 = 사업 운영 일반어."),
    "판매":     ("GENERIC",    "판매 = 사업 운영 일반어."),
    "도출":     ("GENERIC",    "도출 = 일반 결론 표현."),
    "최적":     ("GENERIC",    "최적 = 일반 최적 표현."),
    "대한민국": ("GENERIC",    "국가명 = 일반 지칭."),
    "사장":     ("G_SIGNAL",   "사장(CEO) = G-domain 경영진 공시. 대표이사 맥락."),
    "특별":     ("GENERIC",    "특별 = 일반 강조 표현."),
    "수행":     ("GENERIC",    "수행 = 일반 실행 표현."),
    "종합":     ("GENERIC",    "종합 = 일반 종합 표현."),
    "기능":     ("GENERIC",    "기능 = 일반 기능 표현."),
    "의무":     ("G_SIGNAL",   "법적 의무, 공시 의무 = G-domain 컴플라이언스."),
    "시작":     ("GENERIC",    "시작 = 일반 시제 표현."),
    "최고":     ("G_SIGNAL",   "최고경영자(CEO), 최고재무책임자(CFO) = G-domain 경영진."),
    "기후":     ("ESG_SIGNAL", "기후변화 = E-domain 핵심. 이미 처리."),
    "석유":     ("GENERIC",    "석유 = 특정 에너지원. (탄소중립 맥락은 compound)"),
    "업체":     ("GENERIC",    "업체 = 사업 주체 일반어."),
    "의안":     ("G_SIGNAL",   "주주총회 의안 = G-domain 핵심 의사결정."),
    "우선주":   ("BOILERPLATE","우선주 = 재무 자본 항목."),
    "상환":     ("BOILERPLATE","차입금 상환 = 재무 채무 이행."),
    "처우":     ("ESG_SIGNAL", "임직원 처우 = S-domain 인적자본 공시."),
    "조치":     ("GENERIC",    "시정조치 = 일반 대응. ESG 특이성 낮음."),
    "유상":     ("BOILERPLATE","유상증자 = 재무 자본 조달."),
    "할인":     ("BOILERPLATE","현재가치 할인 = 재무회계."),
    "합리":     ("GENERIC",    "합리적 = 일반 기준 표현."),
    "대기":     ("ESG_SIGNAL", "대기오염, 대기질 관리 = E-domain 공시."),
    "효과":     ("GENERIC",    "효과 = 일반 효과 표현."),
    "산출":     ("BOILERPLATE","비용 산출, 공정가치 산출 = 재무회계."),
    "결제":     ("BOILERPLATE","결제 = 재무 결제 거래."),
    "발전소":   ("ESG_SIGNAL", "발전소 = 에너지 인프라. E-domain 공시 맥락."),
    "차이":     ("GENERIC",    "차이 = 일반 비교 표현."),
    "양도":     ("BOILERPLATE","자산 양도 = 재무 거래."),
    "가정":     ("BOILERPLATE","회계 가정, 추정 가정 = 재무회계."),
    "충족":     ("GENERIC",    "조건 충족 = 일반 표현."),
    "이전":     ("GENERIC",    "이전 = 시제 표현."),
    "우수":     ("GENERIC",    "우수 = 일반 평가 표현."),
    "공장":     ("GENERIC",    "공장 = 사업 운영 일반어."),
    "적극":     ("GENERIC",    "적극 = 일반 강조 표현."),
    "선정":     ("GENERIC",    "선정 = 일반 선발 표현."),
    "개인":     ("GENERIC",    "개인 = 일반 주체 표현."),
    "총액":     ("BOILERPLATE","총액 = 재무 금액 표현."),
    "법규":     ("G_SIGNAL",   "법규 준수 = G-domain 컴플라이언스."),
    "여부":     ("GENERIC",    "여부 = 일반 판단 표현."),
    "전반":     ("GENERIC",    "전반 = 일반 전체 표현."),
    "기존":     ("GENERIC",    "기존 = 일반 기존 표현."),
    "전망":     ("GENERIC",    "전망 = 일반 미래 표현."),
    "연간":     ("GENERIC",    "연간 = 시간 범위 표현."),
    "표명":     ("G_SIGNAL",   "ESG 의지 표명, 공약 표명 = G-domain disclosure 신호."),
    "경기":     ("GENERIC",    "경기 = 거시경제 일반어."),
    "이외":     ("GENERIC",    "이외 = 열거 일반어."),
    "세부":     ("GENERIC",    "세부 = 일반 세부 표현."),
    "자기":     ("G_SIGNAL",   "자기주식 취득/소각 = G-domain 주주가치 관련."),
    "회사채":   ("BOILERPLATE","회사채 = 재무 채권 발행."),
    "통제":     ("G_SIGNAL",   "내부통제, 위험 통제 = G-domain ESG_PRESERVE 항목."),
    "감독":     ("G_SIGNAL",   "이사회 감독, 경영 감독 = G-domain 핵심."),
    "준비금":   ("BOILERPLATE","법정 준비금, 이익 준비금 = 재무 자본 항목."),
    "감축":     ("ESG_SIGNAL", "온실가스 감축, 탄소 감축 = E-domain 핵심."),
    "저감":     ("ESG_SIGNAL", "오염물질 저감, 탄소 저감 = E-domain."),
    "심의":     ("G_SIGNAL",   "이사회 심의, 위원회 심의 = G-domain 의사결정."),
    "점검":     ("ESG_SIGNAL", "안전 점검, ESG 점검 = E/S 리스크 관리."),
    "검증":     ("ESG_SIGNAL", "ESG 검증, 탄소 검증 = 비재무 assurance."),
    "연구":     ("GENERIC",    "R&D 연구 = 사업 일반어."),
    "플랫폼":   ("GENERIC",    "디지털 플랫폼 = 사업 모델 일반어."),
    "복합":     ("GENERIC",    "복합 = 일반 복합 표현."),
    "위원장":   ("G_SIGNAL",   "위원장 = 거버넌스 기구 대표. G-domain 핵심."),
    "절감":     ("ESG_SIGNAL", "에너지 절감, 비용 절감 = E-domain 효율 공시."),
    "손상":     ("BOILERPLATE","자산손상, 손상차손 = 재무회계 항목."),
    "등기":     ("G_SIGNAL",   "등기이사 = G-domain 이사 등록 공시."),
    "우선":     ("GENERIC",    "우선순위 = 일반 표현."),
    "대출":     ("BOILERPLATE","대출금 = 재무 채무 항목."),
    "무상":     ("BOILERPLATE","무상증자, 무상주 = 재무 자본 항목."),
    "장치":     ("GENERIC",    "장치 = 일반 설비 용어."),
    "명부":     ("G_SIGNAL",   "주주명부 = G-domain 주주 관리."),
    "인센티브": ("G_SIGNAL",   "임원 인센티브 = G-domain 보수 체계."),
    "파생":     ("BOILERPLATE","파생상품 = 재무 hedging 도구."),
    "기후":     ("ESG_SIGNAL", "기후 = E-domain 핵심."),
    "차량":     ("GENERIC",    "차량 = 사업 자산 일반어."),
    "업체":     ("GENERIC",    "업체 = 사업 주체."),
    "연료":     ("ESG_SIGNAL", "연료 전환 = E-domain."),
    "의안":     ("G_SIGNAL",   "주주총회 의안 = G-domain."),
    "상환":     ("BOILERPLATE","상환 = 재무 채무 이행."),
    "대기":     ("ESG_SIGNAL", "대기오염 = E-domain."),
    "발전소":   ("ESG_SIGNAL", "발전소 = 에너지 E-domain."),
    "담당":     ("GENERIC",    "담당 = 일반 역할 표현."),
    "시행":     ("GENERIC",    "시행 = 일반 실행 표현."),
    "확정":     ("GENERIC",    "확정 = 일반 확정 표현."),
    "신설":     ("G_SIGNAL",   "위원회 신설, 부서 신설 = G-domain 기관 설립."),
    "재고":     ("BOILERPLATE","재고자산 = 재무 항목."),
    "관측":     ("GENERIC",    "시장 관측, 환경 관측 = 일반어."),
}


# =============================================================================
# 2. 보강 실행 함수
# =============================================================================

def apply_expert_taxonomy(exp_id: str = "exp_A"):
    """
    ambiguous_review CSV에 manual_class / keep_note 컬럼을 자동 보강한다.
    기존 manual_class가 있는 행은 덮어쓰지 않는다.
    """
    review_path = os.path.join(
        config.PREPROC_DIR, f"ambiguous_review_{exp_id}.csv"
    )
    if not os.path.exists(review_path):
        print(f"파일 없음: {review_path}")
        return

    df = pd.read_csv(review_path, dtype=str)
    df["token"] = df["token"].fillna("").astype(str)

    # manual_class / keep_note 컬럼이 없으면 추가
    if "manual_class" not in df.columns:
        df["manual_class"] = ""
    if "keep_note" not in df.columns:
        df["keep_note"] = ""

    df["manual_class"] = df["manual_class"].fillna("")
    df["keep_note"]    = df["keep_note"].fillna("")

    overridden = []
    kept_ambiguous = []
    skipped = []

    for idx, row in df.iterrows():
        token = str(row["token"])

        # 이미 사람이 분류한 경우 스킵
        if str(row["manual_class"]).strip():
            skipped.append(token)
            continue

        if token in EXPERT_MAP:
            cls, note = EXPERT_MAP[token]
            df.at[idx, "manual_class"] = cls
            df.at[idx, "keep_note"]    = note
            overridden.append((token, cls))
        else:
            # 사전에 없으면 AMBIGUOUS 유지
            kept_ambiguous.append(token)

    # 저장
    df.to_csv(review_path, index=False, encoding="utf-8-sig")
    print(f"\n[보강 완료] {review_path}")
    print(f"  분류 완료: {len(overridden)}개")
    print(f"  AMBIGUOUS 유지: {len(kept_ambiguous)}개")
    print(f"  기존 분류 유지: {len(skipped)}개")

    # 분류 결과 요약
    final = pd.read_csv(review_path, dtype=str)
    final["manual_class"] = final["manual_class"].fillna("AMBIGUOUS")
    counts = final["manual_class"].value_counts()
    print("\n[최종 분류 분포]")
    for cls in ["G_SIGNAL", "ESG_SIGNAL", "BOILERPLATE", "GENERIC", "AMBIGUOUS", ""]:
        n = counts.get(cls, 0)
        if n > 0:
            pct = n / len(final) * 100
            print(f"  {cls:<15} {n:>4}개  {pct:.1f}%")

    # AMBIGUOUS 유지 토큰 출력
    if kept_ambiguous:
        print(f"\n[AMBIGUOUS 유지 — 수동 검토 필요] ({len(kept_ambiguous)}개)")
        print("  " + ", ".join(kept_ambiguous[:50]))
        if len(kept_ambiguous) > 50:
            print(f"  ... 외 {len(kept_ambiguous)-50}개")

    # 의사결정 로그 추가
    _append_log(overridden, kept_ambiguous, exp_id)
    return df


def _append_log(overridden, kept_ambiguous, exp_id):
    log_path = os.path.join(config.PREPROC_DIR, "PREPROCESSING_DECISIONS.md")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 범주별 집계
    by_class = {}
    for token, cls in overridden:
        by_class.setdefault(cls, []).append(token)

    lines = [
        "",
        "---",
        "",
        f"## 전문가 자동 보강 실행 기록 — {exp_id}",
        f"**실행 시각:** {ts}  ",
        f"**분류 완료:** {len(overridden)}개 | **AMBIGUOUS 유지:** {len(kept_ambiguous)}개  ",
        "",
        "### 보강 원칙",
        "",
        "- false negative (G-signal 삭제) > false positive (noise 보존)",
        "- IDF/빈도만으로 G-signal을 GENERIC 처리하지 않음",
        "- Corporate governance disclosure 메커니즘 용어는 전문서 등장해도 G_SIGNAL",
        "- 진정한 경계 토큰만 AMBIGUOUS 유지",
        "",
        "### G_SIGNAL 보강 결과",
        "",
        f"총 {len(by_class.get('G_SIGNAL', []))}개:",
        "```",
        ", ".join(by_class.get("G_SIGNAL", [])),
        "```",
        "",
        "### ESG_SIGNAL 보강 결과",
        "",
        f"총 {len(by_class.get('ESG_SIGNAL', []))}개:",
        "```",
        ", ".join(by_class.get("ESG_SIGNAL", [])),
        "```",
        "",
        "### BOILERPLATE 제거 대상 추가",
        "",
        f"총 {len(by_class.get('BOILERPLATE', []))}개:",
        "```",
        ", ".join(by_class.get("BOILERPLATE", [])),
        "```",
        "",
        "### GENERIC 처리",
        "",
        f"총 {len(by_class.get('GENERIC', []))}개:",
        "```",
        ", ".join(by_class.get("GENERIC", [])),
        "```",
        "",
        "### AMBIGUOUS 유지 (수동 검토 필요)",
        "",
        f"총 {len(kept_ambiguous)}개 — 사전 미등록 토큰:",
        "```",
        ", ".join(kept_ambiguous),
        "```",
        "",
        f"*이 기록은 {ts}에 자동 생성되었습니다.*",
        "",
    ]

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n의사결정 로그 추가: {log_path}")


# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", default="exp_A")
    args = parser.parse_args()
    apply_expert_taxonomy(args.exp)

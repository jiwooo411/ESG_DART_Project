# results/tables/ — 현재 비어 있음

이 폴더에는 회귀 비교표(`regression_comparison.csv`), VIF, Cook's distance, 전처리 실험별 robustness 표가 들어갈 예정이다.

이전에 이 폴더에 있던 4개 CSV는 **N=209 pilot 표본**(2021 회계연도 포함, 최종 127사×2022–2024 표본과 다름) 기준 산출물이었고, 그 결과는 README의 핵심 발견 2("통제 후 G만 남는다")와 충돌한다(N=209 산출물에서는 G 계수가 음수·비유의). 최종 N=381 표본과 섞여 혼동을 줄 수 있어 공개 저장소에서는 제외했다.

최종 노트북(`notebook/3조_분석노트북.ipynb`)은 N=381 표본으로 회귀를 실행하지만, 현재 VIF/Cook's distance/robustness 표를 CSV로 별도 export하는 셀은 포함하지 않는다. 해당 셀을 추가해 N=381 기준으로 재생성하기 전까지는 이 폴더를 비워 둔다 — 없는 것이 틀린 것보다 낫다는 원칙(데이터 계보·재현성 우선)에 따른 결정이다.

`results/validation/`의 Spearman·Mann-Whitney·분량직교성 검증 3개 CSV는 N=381 기준으로 확인되었으므로 정상적으로 포함되어 있다.

# CONTRIBUTING

4인 팀 저장소 기준 협업 규칙. 사람과 AI 에이전트(Claude · Codex 등) 모두 동일하게 따른다.

## 브랜치 흐름

`main` pull → 작업 브랜치 생성 → commit → push → PR → 리뷰 → merge.

작업 시작 전 항상 `main`을 pull 한다. 워크트리 기반 도구는 지시만으로 로컬 `main`에 반영되지 않을 수 있으므로 반영 여부를 확인한다.

## 브랜치 네이밍

`<type>/<short-topic>` 형식. 예: `docs/readme-polish`, `feat/token-classifier`, `fix/merge-key`.

`claude/*`·`codex/*` 같은 임의 브랜치는 만들지 않는다.

## 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org) 사용.

| type | 용도 |
|---|---|
| `feat` | 기능·분석 단계 추가 |
| `fix` | 버그·오류 수정 |
| `docs` | 문서·README 변경 |
| `refactor` | 동작 변화 없는 구조 개선 |
| `chore` | 설정·의존성·정리 |

## Pull Request

무엇을·왜·리뷰 포인트만 간단히 기술한다. 분석 수치나 연구 결과를 바꾸는 변경은 PR 설명에 근거를 남긴다.

merge는 임의로 하지 않고 팀 확인 후 수행한다.

## 연구 산출물 원칙

- 수치·실험 결과는 임의로 변경하지 않는다.
- 표본·정의가 다른 산출물(예: N=209 pilot)은 최종(N=381)과 섞지 않는다.
- 재현 불가능한 표는 추가하지 않는다 — 없는 것이 틀린 것보다 낫다.

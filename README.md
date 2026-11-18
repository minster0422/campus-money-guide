# Campus Money Guide

대학생이 교내 장학금, 근로, 생활관 활동, 공모전 등 **돈을 마련할 기회**를 한눈에 탐색하고, 선택적으로 목표 금액을 설정해 적금과 관심 자산 정보까지 이어서 살펴보는 Streamlit 웹앱입니다.

## 바로 실행하기

**공개 데모:** [https://campus-money-guide.streamlit.app](https://campus-money-guide.streamlit.app)

별도의 설치 없이 위 링크를 열면 웹브라우저에서 바로 기능을 확인할 수 있습니다.

> 현재 포함된 공고·적금·이색자산 데이터는 화면과 추천 흐름을 검증하기 위한 데모 데이터입니다. 실제 서비스 단계에서는 학교 공식 공고와 출처가 확인된 상품 데이터로 교체해야 합니다.

## 핵심 기능

- 학년·거주 형태·활동 가능 시간 기반 경제기회 추천
- 장학금·근로·공모전·생활관 활동 통합 탐색
- 관심 기회 저장
- 선택형 목표 금액 시뮬레이션
- 목표 기간에 맞춘 데모 적금 안내
- 레고·TCG 등 수집형 자산의 변동성과 위험 정보 제공

## 로컬 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

macOS/Linux에서는 가상환경 활성화 명령으로 `source .venv/bin/activate`를 사용합니다.

## 테스트

```bash
python -m unittest discover -s tests
```

## Streamlit Community Cloud 배포

1. 이 프로젝트를 GitHub 공동 저장소에 푸시합니다.
2. `share.streamlit.io`에 GitHub 계정으로 로그인합니다.
3. 저장소와 `streamlit_app.py`를 선택합니다.
4. Deploy를 눌러 생성된 URL을 공유합니다.

## 권장 협업 영역

| 영역 | 주요 작업 |
|---|---|
| 통합·배포 | 공통 구조, PR 병합, Streamlit 배포 |
| 교내 데이터 | 실제 공고 조사, 크롤러, 데이터 정규화 |
| 추천·계산 | 조건 매칭, 목표 금액 계산, 적금 추천 |
| 화면·검수 | 카드 UI, 필터, 데이터 원문 검수 |
| QA·문서 | 관심 목록, 테스트, README, 발표자료 |

## 데이터 교체

- `data/opportunities.csv`: 교내 경제기회
- `data/savings.csv`: 적금 상품
- `data/alternative_assets.csv`: 이색 자산 시세

실제 데이터를 사용할 때는 출처 URL, 수집 시각, 금액 기준을 함께 기록해야 합니다. 공모전 상금처럼 확정되지 않은 금액은 기본 목표 계산에 포함하지 않습니다.


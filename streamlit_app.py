from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from services.calculator import calculate_goal_plan, format_money
from services.recommendation import rank_opportunities, recommend_savings


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="Campus Money Guide",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .stApp { background: #f7f8fc; }
    [data-testid="stSidebar"] { background: #171b2b; }
    [data-testid="stSidebar"] * { color: #f7f8ff; }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="select"] input,
    [data-testid="stSidebar"] [data-baseweb="tag"] * {
        color: #1e2430 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #ffffff !important;
    }
    [data-testid="stSidebar"] input[role="combobox"] {
        color: #1e2430 !important;
        -webkit-text-fill-color: #1e2430 !important;
    }
    [data-testid="stSidebar"] input[role="combobox"]::placeholder {
        color: #6f7688 !important;
        -webkit-text-fill-color: #6f7688 !important;
        opacity: 1;
    }
    .hero {
        padding: 2.2rem 2.4rem;
        border-radius: 26px;
        background: linear-gradient(135deg, #5d4df4 0%, #8879ff 55%, #45c6ba 100%);
        color: white;
        box-shadow: 0 18px 45px rgba(78, 65, 210, .18);
        margin-bottom: 1.25rem;
    }
    .hero .eyebrow { font-size: .84rem; letter-spacing: .12em; opacity: .82; font-weight: 700; }
    .hero h1 { margin: .35rem 0 .4rem; font-size: 2.35rem; line-height: 1.15; }
    .hero p { max-width: 760px; margin: 0; font-size: 1.04rem; opacity: .92; }
    .notice {
        background: #fff8dc; color: #725500; border: 1px solid #f3df8e;
        padding: .72rem 1rem; border-radius: 12px; margin: .3rem 0 1rem;
    }
    .opportunity-card {
        background: white; border: 1px solid #e8eaf2; border-radius: 18px;
        padding: 1.05rem 1.1rem; min-height: 224px;
        box-shadow: 0 8px 24px rgba(27, 31, 48, .055);
    }
    .tag {
        display: inline-block; padding: .25rem .55rem; border-radius: 999px;
        background: #efedff; color: #5545d9; font-size: .76rem; font-weight: 700;
        margin-right: .3rem;
    }
    .score { float: right; color: #3a2bc8; font-weight: 800; }
    .opportunity-card h3 { font-size: 1.05rem; margin: .8rem 0 .35rem; color: #1f2533; }
    .opportunity-card .meta { color: #697084; font-size: .86rem; margin-bottom: .7rem; }
    .opportunity-card .money { color: #15806f; font-size: 1rem; font-weight: 800; }
    .opportunity-card .reason { color: #555d70; font-size: .82rem; margin-top: .7rem; }
    .asset-card {
        background: white; border: 1px solid #e8eaf2; border-radius: 16px;
        padding: .9rem 1rem; height: 100%;
    }
    .positive { color: #0b8c73; font-weight: 800; }
    .negative { color: #d14b61; font-weight: 800; }
    .section-kicker { color: #6656e8; font-size: .8rem; font-weight: 800; letter-spacing: .08em; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e7e9f1; padding: .85rem 1rem;
        border-radius: 16px;
    }
    .footer-note { color: #777f92; font-size: .82rem; margin-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    opportunities = pd.read_csv(DATA_DIR / "opportunities.csv")
    savings = pd.read_csv(DATA_DIR / "savings.csv")
    alternatives = pd.read_csv(DATA_DIR / "alternative_assets.csv")
    opportunities["deadline"] = pd.to_datetime(opportunities["deadline"])
    return opportunities, savings, alternatives


opportunities, savings, alternatives = load_data()
if "favorites" not in st.session_state:
    st.session_state.favorites = set()


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">CAMPUS MONEY GUIDE · DEMO</div>
          <h1>돈을 넣기 전에, 마련할 기회부터.</h1>
          <p>대학생에게 흩어진 장학·근로·공모전 기회를 모아 보여주고,
          현재 상황에 맞는 저축과 관심 자산 탐색까지 연결합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice">현재 화면의 공고와 금융상품은 기능 시연용 데모 데이터입니다. 실제 공고로 교체할 때는 원문과 최신 조건을 반드시 확인해야 합니다.</div>',
        unsafe_allow_html=True,
    )


def opportunity_amount(row: pd.Series) -> str:
    minimum = int(row["amount_min"])
    maximum = int(row["amount_max"])
    if minimum == maximum:
        return format_money(minimum)
    return f"{format_money(minimum)} ~ {format_money(maximum)}"


def render_opportunity(row: pd.Series, *, prefix: str) -> None:
    deadline = pd.Timestamp(row["deadline"]).strftime("%m월 %d일")
    st.markdown(
        f"""
        <div class="opportunity-card">
          <span class="tag">{row['category']}</span>
          <span class="tag">{row['competition']}</span>
          <span class="score">{int(row.get('match_score', 0))}%</span>
          <h3>{row['title']}</h3>
          <div class="meta">{row['organization']} · 마감 {deadline} · {row['duration']}</div>
          <div class="money">{row['benefit_type']} · {opportunity_amount(row)}</div>
          <div class="reason">{row.get('match_reason', row['summary'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    opportunity_id = str(row["id"])
    is_favorite = opportunity_id in st.session_state.favorites
    source_url = row.get("source_url")
    has_source = isinstance(source_url, str) and source_url.startswith("http")
    action_columns = st.columns([1, 0.72]) if has_source else [st.container()]
    with action_columns[0]:
        if st.button(
            "★ 관심 목록에서 제거" if is_favorite else "☆ 관심 기회로 저장",
            key=f"{prefix}-{opportunity_id}",
            use_container_width=True,
        ):
            if is_favorite:
                st.session_state.favorites.remove(opportunity_id)
            else:
                st.session_state.favorites.add(opportunity_id)
            st.rerun()
    if has_source:
        with action_columns[1]:
            st.link_button("원문 보기", source_url, use_container_width=True)


with st.sidebar:
    st.markdown("## 🌱 나의 기본 조건")
    grade = st.selectbox("학년", [1, 2, 3, 4], index=0)
    residence = st.selectbox("거주 형태", ["전체", "기숙사", "자취"], index=0)
    available_hours = st.slider("주당 활동 가능한 시간", 0, 20, 6)
    categories = sorted(opportunities["category"].unique().tolist())
    interests = st.multiselect("관심 있는 기회", categories)
    st.markdown("---")
    st.caption("입력한 조건은 추천 순서를 정하는 데만 사용되며 서버에 저장하지 않습니다.")


ranked = rank_opportunities(
    opportunities,
    grade=grade,
    residence=residence,
    available_hours=available_hours,
    interests=interests,
)

render_hero()

nav = st.radio(
    "화면 이동",
    ["맞춤 추천", "목표 시뮬레이션", "관심 목록", "프로젝트 소개"],
    horizontal=True,
    label_visibility="collapsed",
)

if nav == "맞춤 추천":
    st.markdown('<div class="section-kicker">PERSONALIZED OPPORTUNITIES</div>', unsafe_allow_html=True)
    st.subheader(f"{grade}학년에게 먼저 보여드릴 기회")
    eligible_count = int(ranked["eligible"].sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("조건에 맞는 기회", f"{eligible_count}개")
    m2.metric("가장 가까운 마감", ranked.iloc[0]["deadline"].strftime("%m월 %d일"))
    m3.metric("저장한 관심 기회", f"{len(st.session_state.favorites)}개")

    show_only_eligible = st.toggle("조건에 맞는 기회만 보기", value=True)
    view = ranked[ranked["eligible"]] if show_only_eligible else ranked
    if view.empty:
        st.info("현재 조건과 정확히 일치하는 기회가 없습니다. 활동 가능 시간을 늘리거나 필터를 완화해보세요.")
    else:
        for start in range(0, min(len(view), 9), 3):
            columns = st.columns(3)
            for column, (_, row) in zip(columns, view.iloc[start : start + 3].iterrows()):
                with column:
                    render_opportunity(row, prefix="rec")

    st.divider()
    st.markdown('<div class="section-kicker">NEXT STEP</div>', unsafe_allow_html=True)
    st.subheader("여유자금이 생겼다면, 다음 선택지를 비교하세요")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### 안전하게 모으기")
        top_savings = savings.sort_values("max_rate", ascending=False).head(3)
        for _, product in top_savings.iterrows():
            st.markdown(
                f"**{product['name']}** · {int(product['term_months'])}개월  \n"
                f"기본 {product['base_rate']:.1f}% / 최고 {product['max_rate']:.1f}% · {product['conditions']}"
            )
            st.caption(product["description"])
    with right:
        st.markdown("#### 관심 자산 탐색")
        st.caption("구매 추천이 아닌 가격·변동성 정보입니다.")
        for _, asset in alternatives.head(3).iterrows():
            trend_class = "positive" if asset["change_6m"] >= 0 else "negative"
            sign = "+" if asset["change_6m"] >= 0 else ""
            st.markdown(
                f"""
                <div class="asset-card">
                  <b>{asset['item']}</b> <span class="tag">{asset['category']}</span><br>
                  {format_money(asset['current_price'])} ·
                  <span class="{trend_class}">6개월 {sign}{asset['change_6m']:.1f}%</span><br>
                  <small>위험 {asset['risk']} · 환금성 {asset['liquidity']}</small>
                </div><br>
                """,
                unsafe_allow_html=True,
            )

elif nav == "목표 시뮬레이션":
    st.markdown('<div class="section-kicker">OPTIONAL GOAL PLANNER</div>', unsafe_allow_html=True)
    st.subheader("목표가 있다면, 선택한 기회가 얼마나 도움이 되는지 확인하세요")
    st.caption("목표 금액 입력은 선택 기능입니다. 경쟁형 공모전 상금은 기본 계획과 분리합니다.")

    c1, c2, c3 = st.columns(3)
    with c1:
        target_amount = st.number_input("목표 금액", min_value=100_000, value=2_000_000, step=100_000)
    with c2:
        current_amount = st.number_input("현재 보유 금액", min_value=0, value=300_000, step=50_000)
    with c3:
        remaining_months = st.number_input("남은 기간(개월)", min_value=1, max_value=60, value=8)

    options = {
        f"{row['title']} · {opportunity_amount(row)}": row["id"]
        for _, row in ranked[ranked["eligible"]].iterrows()
    }
    selected_labels = st.multiselect("계획에 넣어볼 경제기회", list(options.keys()))
    selected_ids = [options[label] for label in selected_labels]
    selected = opportunities[opportunities["id"].isin(selected_ids)]

    plan = calculate_goal_plan(
        selected,
        target_amount=int(target_amount),
        current_amount=int(current_amount),
        remaining_months=int(remaining_months),
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("추가 필요 금액", format_money(max(plan.target_amount - plan.current_amount, 0)))
    m2.metric("선택 기회 예상", f"{format_money(plan.expected_min)} ~ {format_money(plan.expected_max)}")
    m3.metric("월 필요 금액", format_money(plan.monthly_required))
    m4.metric("도전 가능 상금", format_money(plan.challenge_max))

    base_progress = min((plan.current_amount + plan.expected_min) / plan.target_amount, 1.0)
    st.progress(base_progress, text=f"현재 금액과 비경쟁형 기회를 반영한 목표 기여도 {base_progress * 100:.0f}%")

    if plan.challenge_max:
        st.info(
            f"경쟁형 공모전까지 모두 성과가 난 낙관 시나리오의 부족 금액은 "
            f"{format_money(plan.optimistic_gap)}입니다. 상금은 기본 계획에는 포함하지 않았습니다."
        )

    st.divider()
    st.subheader("목표 기간과 월 금액에 가까운 데모 적금")
    recommended_savings = recommend_savings(
        savings,
        remaining_months=int(remaining_months),
        monthly_budget=int(plan.monthly_required),
    ).head(3)
    for _, product in recommended_savings.iterrows():
        with st.container(border=True):
            st.markdown(f"### {product['name']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("기간", f"{int(product['term_months'])}개월")
            c2.metric("최고금리(데모)", f"{product['max_rate']:.1f}%")
            c3.metric("최소 월납입", format_money(product["min_monthly"]))
            st.write(product["description"])
            st.caption(f"조건: {product['conditions']}")

elif nav == "관심 목록":
    st.markdown('<div class="section-kicker">SAVED OPPORTUNITIES</div>', unsafe_allow_html=True)
    st.subheader("나중에 다시 확인할 기회")
    favorites = ranked[ranked["id"].isin(st.session_state.favorites)]
    if favorites.empty:
        st.info("아직 저장한 기회가 없습니다. 맞춤 추천에서 별표 버튼을 눌러보세요.")
    else:
        for start in range(0, len(favorites), 3):
            columns = st.columns(3)
            for column, (_, row) in zip(columns, favorites.iloc[start : start + 3].iterrows()):
                with column:
                    render_opportunity(row, prefix="fav")

elif nav == "프로젝트 소개":
    st.markdown('<div class="section-kicker">ABOUT THE PROJECT</div>', unsafe_allow_html=True)
    st.subheader("대학생의 첫 경제적 기회를 한곳에")
    st.write(
        "기존 자산관리 서비스가 이미 가진 돈을 어디에 넣을지 안내한다면, "
        "이 프로젝트는 대학생이 장학·근로·공모전 등으로 돈을 마련하는 단계부터 시작합니다."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### ① 기회 탐색")
        st.write("학교 여러 게시판에 흩어진 경제기회를 공통 형식으로 모읍니다.")
    with c2:
        st.markdown("### ② 조건 추천")
        st.write("학년·거주·활동시간을 기준으로 설명 가능한 규칙형 추천을 제공합니다.")
    with c3:
        st.markdown("### ③ 다음 선택")
        st.write("선택적인 목표 계산 뒤 적금과 수집형 자산 정보를 이어서 보여줍니다.")

    st.divider()
    st.markdown("#### 이번 MVP에서 의도적으로 제외한 기능")
    st.write("실제 계좌 연동 · 회원가입 · 실시간 크롤링 · 투자수익 예측 · 메인 챗봇")
    st.markdown("#### 다음 개발 단계")
    st.write("실제 교내 공고 크롤러 연결 → 출처 검수 → 추천 규칙 보완 → 배포 및 발표 시나리오 테스트")

st.markdown(
    f'<div class="footer-note">데모 기준일 {date.today().isoformat()} · 모든 금액과 상품 정보는 기능 검증용 예시입니다.</div>',
    unsafe_allow_html=True,
)

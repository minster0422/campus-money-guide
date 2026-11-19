from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from services.calculator import calculate_goal_plan, format_money
from services.market import build_market_index, build_price_history
from services.recommendation import filter_opportunities, rank_opportunities, recommend_savings


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
NAV_ITEMS = ["홈", "경제기회", "목표계획", "대체자산", "관심목록"]

st.set_page_config(
    page_title="Campus Money Guide",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #191f28;
        --sub: #6b7684;
        --blue: #3182f6;
        --blue-soft: #eaf3ff;
        --surface: #f2f4f6;
        --line: #e5e8eb;
        --green: #00a77b;
        --red: #f04452;
    }
    .stApp { background: #ffffff; color: var(--ink); }
    .block-container { max-width: 1120px; padding: 1.35rem 1.5rem 4.5rem; }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }
    .stAppViewContainer > .main { padding-top: 0 !important; }
    h1 a, h2 a, h3 a, [data-testid="stHeaderActionElements"] { display: none !important; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -.035em; }
    h1 { font-size: 2.35rem !important; line-height: 1.2 !important; }
    h2 { font-size: 1.55rem !important; }
    h3 { font-size: 1.08rem !important; }
    p { color: var(--ink); }
    .brand { display: flex; align-items: center; gap: .7rem; min-height: 42px; }
    .brand-mark {
        width: 34px; height: 34px; border-radius: 11px; display: grid; place-items: center;
        background: var(--blue); color: #fff; font-weight: 800; font-size: .9rem;
    }
    .brand-name { color: var(--ink); font-size: .98rem; font-weight: 800; letter-spacing: -.03em; line-height: 1.2; }
    .brand-sub { color: var(--sub); font-size: .72rem; line-height: 1.35; margin-top: .12rem; }
    div[role="radiogroup"] { gap: .25rem; justify-content: flex-end; }
    div[role="radiogroup"] label {
        background: transparent; padding: .5rem .68rem; border-radius: 10px;
        transition: background .15s ease;
    }
    div[role="radiogroup"] label:hover { background: var(--surface); }
    div[role="radiogroup"] label:has(input:checked) { background: var(--ink); color: #fff; }
    div[role="radiogroup"] label:has(input:checked) p { color: #fff !important; }
    div[role="radiogroup"] [data-testid="stMarkdownContainer"] p { font-size: .9rem; font-weight: 700; }
    [data-testid="stRadioOption"] > div > div:first-child { display: none !important; }
    .top-divider { height: 1px; background: var(--line); margin: .6rem 0 2.8rem; }
    .hero { max-width: 880px; margin-bottom: 1.1rem; }
    .hero h1 { font-size: 2.65rem; line-height: 1.24; margin: .75rem 0 .85rem; letter-spacing: -.055em; }
    .hero h1 span { color: var(--ink); }
    .eyebrow { color: var(--blue); font-size: .78rem; font-weight: 800; letter-spacing: .08em; }
    .lead { color: var(--sub); font-size: 1.02rem; line-height: 1.65; max-width: 760px; margin-top: -.2rem; }
    .demo-note {
        display: inline-flex; align-items: center; gap: .45rem; color: var(--sub);
        background: var(--surface); border-radius: 999px; padding: .42rem .72rem;
        font-size: .76rem; margin: .3rem 0 1.1rem;
    }
    .home-summary {
        background: linear-gradient(135deg, #edf5ff 0%, #f5f8ff 55%, #f3fbf8 100%);
        border-radius: 26px; padding: 1.85rem 2rem; margin: 1.5rem 0 1.7rem;
    }
    .home-summary h2 { font-size: 1.65rem !important; margin: .35rem 0 1.4rem; }
    .summary-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: .7rem; }
    .summary-stat { background: rgba(255,255,255,.82); border-radius: 16px; padding: 1rem; }
    .summary-stat span { color: var(--sub); font-size: .76rem; display: block; margin-bottom: .3rem; }
    .summary-stat b { font-size: 1.18rem; letter-spacing: -.03em; }
    .section-head { margin-top: 2.65rem; margin-bottom: .8rem; }
    .section-head h2 { margin: .25rem 0 .2rem; }
    .section-head p { color: var(--sub); margin: 0; font-size: .9rem; }
    .op-row { padding: 1.1rem .15rem; }
    .op-tags { display: flex; flex-wrap: wrap; gap: .35rem; margin-bottom: .55rem; }
    .pill {
        display: inline-block; padding: .28rem .55rem; border-radius: 999px;
        background: var(--surface); color: var(--sub); font-size: .72rem; font-weight: 700;
    }
    .pill.blue { background: var(--blue-soft); color: var(--blue); }
    .pill.green { background: #e8f8f3; color: #008f69; }
    .pill.amber { background: #fff3df; color: #b85c00; }
    .op-title { font-size: 1.06rem; font-weight: 800; letter-spacing: -.025em; margin-bottom: .35rem; }
    .op-meta { color: var(--sub); font-size: .82rem; line-height: 1.55; }
    .op-money { font-size: .88rem; font-weight: 800; color: var(--ink); margin-top: .45rem; }
    .row-divider { height: 1px; background: var(--line); }
    .soft-card { background: var(--surface); border-radius: 20px; padding: 1.4rem; min-height: 100%; }
    .soft-card .label { color: var(--sub); font-size: .78rem; }
    .soft-card .big { font-size: 1.45rem; font-weight: 800; letter-spacing: -.04em; margin: .35rem 0; }
    .soft-card .desc { color: var(--sub); font-size: .82rem; line-height: 1.5; }
    .progress-track { height: 10px; background: #dfe4ea; border-radius: 999px; overflow: hidden; margin: .9rem 0 .45rem; }
    .progress-fill { height: 100%; background: var(--blue); border-radius: inherit; }
    .progress-meta { display: flex; justify-content: space-between; color: var(--sub); font-size: .75rem; }
    .detail-hero { padding: .5rem 0 1rem; }
    .detail-hero h1 { margin: .55rem 0 .4rem; }
    .detail-amount { font-size: 1.35rem; font-weight: 800; margin-top: 1.05rem; }
    .fact-list { display: grid; gap: 0; }
    .fact-row { display: flex; justify-content: space-between; gap: 1rem; padding: .9rem 0; border-bottom: 1px solid var(--line); }
    .fact-row:last-child { border-bottom: 0; }
    .fact-row span { color: var(--sub); font-size: .85rem; }
    .fact-row b { font-size: .86rem; text-align: right; }
    .reason-box { background: var(--blue-soft); border-radius: 18px; padding: 1.1rem; }
    .reason-box b { display: block; color: var(--blue); margin-bottom: .4rem; }
    .reason-box p { margin: 0; font-size: .86rem; line-height: 1.55; }
    .goal-total { font-size: 2.1rem; font-weight: 800; letter-spacing: -.05em; }
    .goal-sub { color: var(--sub); font-size: .85rem; }
    .impact-card { background: #eef8f5; border-radius: 18px; padding: 1.05rem; margin-top: .8rem; }
    .impact-card b { font-size: 1.05rem; }
    .impact-card p { color: var(--sub); font-size: .82rem; margin: .35rem 0 0; }
    .market-number { font-size: 2rem; font-weight: 800; letter-spacing: -.045em; }
    .positive { color: var(--green) !important; font-weight: 800; }
    .negative { color: var(--red) !important; font-weight: 800; }
    .asset-row { padding: .8rem 0; }
    .asset-name { font-size: 1rem; font-weight: 800; }
    .asset-meta { color: var(--sub); font-size: .78rem; margin-top: .3rem; }
    .asset-price { font-size: .95rem; font-weight: 800; text-align: right; }
    .asset-delta { font-size: .76rem; text-align: right; margin-top: .25rem; }
    .warning-box { background: #fff7e8; color: #8b5e00; border-radius: 16px; padding: .9rem 1rem; font-size: .82rem; line-height: 1.5; }
    .empty-state { text-align: center; padding: 3rem 1rem; color: var(--sub); background: var(--surface); border-radius: 22px; }
    .footer-note { color: var(--sub); font-size: .76rem; margin-top: 3rem; text-align: center; }
    .stButton > button, .stLinkButton > a {
        border: 0 !important; border-radius: 12px !important; min-height: 42px;
        font-weight: 800 !important; box-shadow: none !important;
    }
    .stButton > button { background: var(--surface); color: var(--ink); }
    .stButton > button:hover { background: #e8ebee; color: var(--ink); }
    .stButton > button[kind="primary"] { background: var(--blue); color: #fff; }
    .stButton > button[kind="primary"]:hover { background: #1b64da; color: #fff; }
    .stLinkButton > a { background: var(--surface) !important; color: var(--ink) !important; }
    [data-testid="stExpander"] { border: 0 !important; border-radius: 16px !important; background: var(--surface); }
    [data-testid="stExpander"] summary { min-height: 48px; }
    [data-testid="stNumberInput"], [data-baseweb="select"] { border-radius: 12px; }
    [data-testid="stVegaLiteChart"] { margin-top: -.4rem; }
    @media (max-width: 760px) {
        .block-container { padding: .9rem 1rem 3.5rem; }
        h1 { font-size: 1.85rem !important; }
        .brand { margin-bottom: .35rem; }
        .brand-sub { display: none; }
        .top-divider { margin: .65rem 0 1.8rem; }
        .hero { margin-bottom: .8rem; }
        .hero h1 { font-size: 2rem; line-height: 1.28; margin: .65rem 0 .75rem; }
        .lead { font-size: .94rem; line-height: 1.6; }
        .summary-grid { grid-template-columns: 1fr; }
        .home-summary { padding: 1.3rem; border-radius: 20px; margin-top: 1.2rem; }
        .home-summary h2 { font-size: 1.35rem !important; margin-bottom: 1rem; }
        .section-head { margin-top: 2.1rem; }
        .op-row { padding: .9rem 0 .65rem; }
        div[role="radiogroup"] { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; }
        div[role="radiogroup"] label { white-space: nowrap; padding: .45rem .58rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    opportunities = pd.read_csv(DATA_DIR / "opportunities.csv")
    savings = pd.read_csv(DATA_DIR / "savings.csv")
    alternatives = pd.read_csv(DATA_DIR / "alternative_assets.csv")
    opportunities["deadline"] = pd.to_datetime(opportunities["deadline"], errors="coerce")
    return opportunities, savings, alternatives


@st.cache_data
def load_opportunity_meta() -> dict[str, object]:
    path = DATA_DIR / "opportunities_meta.json"
    if not path.exists():
        return {"source_type": "demo", "count": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"source_type": "demo", "count": 0}


def opportunity_data_note() -> str:
    meta = load_opportunity_meta()
    if meta.get("source_type") == "official_school_notices":
        fetched_at = str(meta.get("fetched_at", "")).replace("T", " ")[:16]
        return (
            f"● {meta.get('school', '학교')} 공식 공고 {int(meta.get('count', 0))}건"
            f" · 마지막 수집 {fetched_at}"
        )
    return "● 교내 공고와 이색자산 시세는 화면 검증용 데모 데이터입니다"


def init_state(opportunities: pd.DataFrame, alternatives: pd.DataFrame) -> None:
    defaults = {
        "main_nav": "홈",
        "favorites": set(),
        "favorite_assets": set(),
        "goal_opportunities": set(),
        "selected_opportunity": str(opportunities.iloc[0]["id"]),
        "opportunity_detail": False,
        "selected_asset": str(alternatives.iloc[0]["id"]),
        "asset_detail": False,
        "profile_grade": 1,
        "profile_residence": "전체",
        "profile_region": "",
        "profile_hours": 6,
        "profile_interests": [],
        "target_amount": 1_500_000,
        "current_amount": 300_000,
        "remaining_months": 6,
        "asset_period": "6개월",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clean_title(value: object) -> str:
    return str(value).replace("[데모] ", "").strip()


def opportunity_amount(row: pd.Series) -> str:
    amount_note = row.get("amount_note", "")
    if isinstance(amount_note, str) and amount_note.strip():
        return amount_note.strip()
    minimum = int(row.get("amount_min", 0) or 0)
    maximum = int(row.get("amount_max", 0) or 0)
    if minimum <= 0 and maximum <= 0:
        return "원문에서 확인"
    if minimum == maximum:
        return format_money(minimum)
    return f"{format_money(minimum)} ~ {format_money(maximum)}"


def deadline_label(value: object) -> str:
    if pd.isna(value):
        return "마감일 원문 확인"
    deadline = pd.Timestamp(value).date()
    days = (deadline - date.today()).days
    if days == 0:
        return "오늘 마감"
    if days > 0:
        return f"D-{days}"
    return "마감"


def region_requirement_label(row: pd.Series) -> str:
    value = row.get("region_requirement", "제한 없음")
    if pd.isna(value) or not str(value).strip():
        return "제한 없음"
    return str(value).replace("|", "·")


def category_icon(category: str) -> str:
    return {
        "레고": "🧱",
        "TCG": "🃏",
        "시계": "⌚",
        "스니커즈": "👟",
        "와인": "🍷",
    }.get(category, "◇")


def go_to(page: str) -> None:
    st.session_state.main_nav = page
    if page == "경제기회":
        st.session_state.opportunity_detail = False
    if page == "대체자산":
        st.session_state.asset_detail = False


def handle_navigation() -> None:
    if st.session_state.main_nav == "경제기회":
        st.session_state.opportunity_detail = False
    if st.session_state.main_nav == "대체자산":
        st.session_state.asset_detail = False


def open_opportunity(opportunity_id: str) -> None:
    st.session_state.selected_opportunity = opportunity_id
    st.session_state.opportunity_detail = True
    st.session_state.main_nav = "경제기회"
    st.session_state.opportunity_scroll_top = True
    st.session_state.opportunity_scroll_nonce = (
        int(st.session_state.get("opportunity_scroll_nonce", 0)) + 1
    )


def close_opportunity() -> None:
    st.session_state.opportunity_detail = False


def toggle_opportunity(opportunity_id: str) -> None:
    favorites = st.session_state.favorites
    if opportunity_id in favorites:
        favorites.remove(opportunity_id)
    else:
        favorites.add(opportunity_id)


def add_to_goal(opportunity_id: str) -> None:
    st.session_state.goal_opportunities.add(opportunity_id)
    st.session_state[f"goal-check-{opportunity_id}"] = True
    st.session_state.main_nav = "목표계획"


def open_asset(asset_id: str) -> None:
    st.session_state.selected_asset = asset_id
    st.session_state.asset_detail = True
    st.session_state.main_nav = "대체자산"


def close_asset() -> None:
    st.session_state.asset_detail = False


def toggle_asset(asset_id: str) -> None:
    favorites = st.session_state.favorite_assets
    if asset_id in favorites:
        favorites.remove(asset_id)
    else:
        favorites.add(asset_id)


def sync_goal_check(opportunity_id: str, key: str) -> None:
    if st.session_state[key]:
        st.session_state.goal_opportunities.add(opportunity_id)
    else:
        st.session_state.goal_opportunities.discard(opportunity_id)


def render_section_head(kicker: str, title: str, description: str = "") -> None:
    desc = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        f'<div class="section-head"><div class="eyebrow">{escape(kicker)}</div>'
        f'<h2>{escape(title)}</h2>{desc}</div>',
        unsafe_allow_html=True,
    )


def render_price_chart(history: pd.DataFrame, *, height: int = 260, compact: bool = False) -> None:
    color = "#00a77b" if history.iloc[-1]["price"] >= history.iloc[0]["price"] else "#f04452"
    chart = {
        "height": height,
        "layer": [
            {
                "mark": {"type": "area", "line": False, "color": color, "opacity": 0.08},
                "encoding": {
                    "x": {"field": "date", "type": "temporal", "axis": None if compact else {"title": None, "format": "%m월", "labelColor": "#8b95a1", "grid": False}},
                    "y": {"field": "price", "type": "quantitative", "axis": None if compact else {"title": None, "labelColor": "#8b95a1", "gridColor": "#f2f4f6", "format": ",.0f", "tickCount": 4}, "scale": {"zero": False}},
                },
            },
            {
                "mark": {"type": "line", "color": color, "strokeWidth": 2.5},
                "encoding": {
                    "x": {"field": "date", "type": "temporal", "axis": None},
                    "y": {"field": "price", "type": "quantitative", "axis": None, "scale": {"zero": False}},
                    "tooltip": [
                        {"field": "date", "type": "temporal", "title": "기준일", "format": "%Y-%m-%d"},
                        {"field": "price", "type": "quantitative", "title": "가격", "format": ",.0f"},
                    ],
                },
            },
        ],
        "config": {"view": {"stroke": None}},
    }
    st.vega_lite_chart(history, chart, width="stretch")


def render_opportunity_row(row: pd.Series, *, prefix: str, show_actions: bool = True) -> None:
    opportunity_id = str(row["id"])
    title = escape(clean_title(row["title"]))
    amount = escape(opportunity_amount(row))
    reason = escape(str(row.get("match_reason", row["summary"])))
    region_label = region_requirement_label(row)
    region_pill = (
        f'<span class="pill amber">{escape(region_label)} 지역 조건</span>'
        if region_label != "제한 없음"
        else ""
    )
    left, right = st.columns([4.2, 1.15], vertical_alignment="center")
    with left:
        st.markdown(
            f"""
            <div class="op-row">
              <div class="op-tags">
                <span class="pill blue">{escape(str(row['category']))}</span>
                <span class="pill">{escape(deadline_label(row['deadline']))}</span>
                <span class="pill green">{int(row.get('match_score', 0))}% 일치</span>
                {region_pill}
              </div>
              <div class="op-title">{title}</div>
              <div class="op-meta">{escape(str(row['organization']))} · {reason}</div>
              <div class="op-money">{escape(str(row['benefit_type']))} · {amount}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if show_actions:
        with right:
            st.button(
                "자세히 보기",
                key=f"{prefix}-open-{opportunity_id}",
                width="stretch",
                on_click=open_opportunity,
                args=(opportunity_id,),
            )
            favorite = opportunity_id in st.session_state.favorites
            st.button(
                "저장됨 ✓" if favorite else "관심 저장",
                key=f"{prefix}-fav-{opportunity_id}",
                width="stretch",
                on_click=toggle_opportunity,
                args=(opportunity_id,),
            )
    st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)


def render_header() -> str:
    brand, navigation = st.columns([.42, 1.58], vertical_alignment="center")
    with brand:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-mark">CM</div>
              <div><div class="brand-name">Campus Money</div><div class="brand-sub">대학생 경제기회 가이드</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with navigation:
        page = st.radio(
            "주요 화면",
            NAV_ITEMS,
            horizontal=True,
            label_visibility="collapsed",
            key="main_nav",
            on_change=handle_navigation,
        )
    st.markdown('<div class="top-divider"></div>', unsafe_allow_html=True)
    return page


def render_profile_controls(opportunities: pd.DataFrame) -> None:
    with st.expander("내 조건 수정 · 추천 기준 보기"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.selectbox("학년", [1, 2, 3, 4], key="profile_grade")
        with c2:
            st.selectbox("거주 형태", ["전체", "기숙사", "자취"], key="profile_residence")
        with c3:
            st.slider("주당 활동 가능 시간", 0, 20, key="profile_hours")
        with c4:
            st.text_input(
                "거주·연고 지역",
                key="profile_region",
                placeholder="예: 통영시, 아산시",
            )
        categories = sorted(opportunities["category"].unique().tolist())
        st.multiselect("관심 있는 기회", categories, key="profile_interests")
        st.caption(
            "지역을 비워두면 특정 시·군·구 거주 또는 출신 조건이 있는 공고는 추천 가능 목록에서 제외됩니다. "
            "입력한 조건은 별도로 저장하지 않습니다."
        )


def render_home(ranked: pd.DataFrame, alternatives: pd.DataFrame) -> None:
    eligible = ranked[ranked["eligible"]]
    nearest = eligible.iloc[0] if not eligible.empty else ranked.iloc[0]
    noncompetitive = eligible[eligible["competition"] != "경쟁형"]
    max_benefit = int(noncompetitive["amount_max"].max()) if not noncompetitive.empty else 0
    max_benefit_text = format_money(max_benefit) if max_benefit > 0 else "공고 원문 확인"
    st.markdown(
        '<div class="hero"><div class="eyebrow">FOR YOUR CAMPUS LIFE</div>'
        '<h1>돈을 모으기 전에,<br><span>받을 수 있는 기회부터 찾아보세요</span></h1>'
        '<div class="lead">장학·근로·공모전처럼 흩어진 경제기회를 내 조건에 맞춰 보고, '
        '목표금액과 저축·관심 자산 탐색까지 한 흐름으로 연결합니다.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="demo-note">{escape(opportunity_data_note())}</div>',
        unsafe_allow_html=True,
    )
    render_profile_controls(ranked)

    st.markdown(
        f"""
        <div class="home-summary">
          <div class="eyebrow">오늘의 경제기회 요약</div>
          <h2>{int(st.session_state.profile_grade)}학년 조건에서 확인할 기회가 {int(eligible.shape[0])}개 있어요</h2>
          <div class="summary-grid">
            <div class="summary-stat"><span>가장 가까운 마감</span><b>{escape(clean_title(nearest['title']))} · {escape(deadline_label(nearest['deadline']))}</b></div>
            <div class="summary-stat"><span>가장 큰 비경쟁형 혜택</span><b>{escape(max_benefit_text)}</b></div>
            <div class="summary-stat"><span>관심 목록</span><b>{len(st.session_state.favorites) + len(st.session_state.favorite_assets)}개 저장됨</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_head("RECOMMENDED", "지금 확인할 경제기회", "내 조건과 마감일을 함께 반영한 추천입니다.")
    for _, row in eligible.head(3).iterrows():
        render_opportunity_row(row, prefix="home")
    st.button("경제기회 전체 보기", width="stretch", on_click=go_to, args=("경제기회",))

    render_section_head("NEXT STEP", "모은 돈의 다음 경로", "목표가 있다면 계획하고, 관심이 있다면 시장을 탐색하세요.")
    goal_col, market_col = st.columns(2, gap="large")
    target = int(st.session_state.target_amount)
    current = int(st.session_state.current_amount)
    progress = min(current / target, 1.0) if target else 0
    with goal_col:
        st.markdown(
            f"""
            <div class="soft-card">
              <div class="label">나의 선택형 목표</div>
              <div class="big">목표까지 {format_money(max(target-current, 0))}</div>
              <div class="desc">기회를 목표에 담으면 매달 필요한 저축액이 어떻게 달라지는지 보여드려요.</div>
              <div class="progress-track"><div class="progress-fill" style="width:{progress*100:.0f}%"></div></div>
              <div class="progress-meta"><span>{format_money(current)}</span><span>{format_money(target)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("목표계획 열기", key="home-goal", type="primary", width="stretch", on_click=go_to, args=("목표계획",))
    with market_col:
        market = build_market_index(alternatives)
        change = (market.iloc[-1]["price"] / market.iloc[0]["price"] - 1) * 100
        st.markdown(
            f"""
            <div class="soft-card">
              <div class="label">대체자산 시장지수 · 6개월</div>
              <div class="big">{market.iloc[-1]['price']:,.1f} <span class="{'positive' if change >= 0 else 'negative'}" style="font-size:.88rem">{change:+.1f}%</span></div>
              <div class="desc">레고·TCG·시계·스니커즈·와인 시세의 흐름을 같은 기준으로 비교합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("대체자산 둘러보기", key="home-market", width="stretch", on_click=go_to, args=("대체자산",))


def render_opportunity_list(ranked: pd.DataFrame) -> None:
    st.markdown(
        '<div class="hero"><div class="eyebrow">OPPORTUNITY FINDER</div>'
        '<h1>내 조건에 맞는<br><span>경제기회를 모아봤어요</span></h1>'
        '<div class="lead">장학금·근로·공모전·교내 활동을 마감일과 예상 혜택 기준으로 비교하세요.</div></div>',
        unsafe_allow_html=True,
    )
    render_profile_controls(ranked)
    search_col, category_col, sort_col = st.columns([1.8, 1, 1])
    with search_col:
        query = st.text_input(
            "경제기회 검색",
            placeholder="공고명, 담당 부서, 지역 조건 검색",
            key="opportunity_search",
        )
    with category_col:
        selected_categories = st.multiselect(
            "카테고리",
            sorted(ranked["category"].dropna().unique().tolist()),
            key="opportunity_category_filter",
            placeholder="전체 카테고리",
        )
    with sort_col:
        sort_by = st.selectbox(
            "정렬",
            ["추천순", "마감 임박순", "혜택 큰 순"],
            key="opportunity_sort",
        )

    filtered = filter_opportunities(
        ranked,
        query=query,
        categories=selected_categories,
        sort_by=sort_by,
    )
    eligible = filtered[filtered["eligible"]]
    condition_check = filtered[~filtered["eligible"]]
    st.caption(f"현재 조건과 필터에서 총 {len(filtered)}개의 경제기회를 확인할 수 있습니다.")
    render_section_head("MATCHED", f"지원 가능한 기회 {len(eligible)}개", "추천 점수와 마감일을 함께 반영했습니다.")
    if eligible.empty:
        st.markdown('<div class="empty-state">현재 조건에 맞는 기회가 없습니다.<br>상단에서 조건을 넓혀보세요.</div>', unsafe_allow_html=True)
    else:
        for _, row in eligible.iterrows():
            render_opportunity_row(row, prefix="opportunity-list")
    if not condition_check.empty:
        render_section_head(
            "CHECK CONDITIONS",
            f"추가 조건을 확인할 기회 {len(condition_check)}개",
            "학년·지역·활동시간 조건이 맞지 않거나 확인이 필요한 공고입니다.",
        )
        for _, row in condition_check.iterrows():
            render_opportunity_row(row, prefix="condition-check")


def render_opportunity_detail(ranked: pd.DataFrame) -> None:
    st.markdown('<div id="opportunity-detail-top"></div>', unsafe_allow_html=True)
    if st.session_state.pop("opportunity_scroll_top", False):
        scroll_nonce = int(st.session_state.get("opportunity_scroll_nonce", 0))
        scroll_html = f"<!-- scroll-request:{scroll_nonce} -->" + """
            <script>
              const scrollTop = () => {
                const doc = window.parent.document;
                const detailTop = doc.querySelector('#opportunity-detail-top');
                const main = doc.querySelector('[data-testid="stMain"]');
                const appView = doc.querySelector('[data-testid="stAppViewContainer"]');
                const block = doc.querySelector('[data-testid="stMainBlockContainer"]');
                [main, appView, doc.scrollingElement, doc.documentElement, doc.body]
                  .filter(Boolean)
                  .forEach((element) => {
                    element.scrollTop = 0;
                    if (element.scrollTo) {
                      element.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                    }
                  });
                (block || detailTop)?.scrollIntoView({ block: 'start', behavior: 'auto' });
                window.parent.scrollTo({ top: 0, left: 0, behavior: 'auto' });
              };
              [0, 80, 200, 450].forEach((delay) =>
                window.parent.setTimeout(scrollTop, delay)
              );
            </script>
        """
        components.html(
            scroll_html,
            height=0,
        )

    selected_id = st.session_state.selected_opportunity
    matches = ranked[ranked["id"].astype(str) == selected_id]
    row = matches.iloc[0] if not matches.empty else ranked.iloc[0]
    opportunity_id = str(row["id"])
    deadline = (
        "공고 원문 확인"
        if pd.isna(row["deadline"])
        else pd.Timestamp(row["deadline"]).strftime("%Y년 %m월 %d일")
    )
    weekly_hours = "해당 없음" if int(row["weekly_hours"]) == 0 else f"{int(row['weekly_hours'])}시간"
    region_requirement = region_requirement_label(row)

    st.button("← 경제기회 목록", key="opportunity-back", on_click=close_opportunity)
    st.markdown('<div class="eyebrow" style="margin-top:1.35rem">OPPORTUNITY DETAIL</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="detail-hero">
          <div class="op-tags"><span class="pill blue">{escape(str(row['category']))}</span><span class="pill">{escape(deadline_label(row['deadline']))}</span><span class="pill green">{int(row['match_score'])}% 일치</span></div>
          <h1>{escape(clean_title(row['title']))}</h1>
          <div class="lead">{escape(str(row['organization']))} · {escape(str(row['summary']))}</div>
          <div class="detail-amount">{escape(str(row['benefit_type']))} · {escape(opportunity_amount(row))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info, action = st.columns([1.65, 1], gap="large")
    with info:
        st.markdown(
            f"""
            <div class="fact-list">
              <div class="fact-row"><span>신청 대상</span><b>{escape(str(row['eligible_grades']).replace('|', '·'))}학년</b></div>
              <div class="fact-row"><span>지역 조건</span><b>{escape(region_requirement)}</b></div>
              <div class="fact-row"><span>마감일</span><b>{deadline}</b></div>
              <div class="fact-row"><span>활동 기간</span><b>{escape(str(row['duration']))}</b></div>
              <div class="fact-row"><span>주당 활동시간</span><b>{weekly_hours}</b></div>
              <div class="fact-row"><span>선발 방식</span><b>{escape(str(row['competition']))}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with action:
        st.markdown(
            f'<div class="reason-box"><b>나에게 추천된 이유</b><p>{escape(str(row["match_reason"]))}</p></div>',
            unsafe_allow_html=True,
        )
        st.button(
            "목표계획에 담기",
            key=f"detail-goal-{opportunity_id}",
            type="primary",
            width="stretch",
            on_click=add_to_goal,
            args=(opportunity_id,),
        )
        favorite = opportunity_id in st.session_state.favorites
        st.button(
            "관심 목록에서 제거" if favorite else "관심 기회로 저장",
            key=f"detail-fav-{opportunity_id}",
            width="stretch",
            on_click=toggle_opportunity,
            args=(opportunity_id,),
        )
        source_url = row.get("source_url")
        if isinstance(source_url, str) and source_url.startswith("http"):
            st.link_button("공식 공고 확인", source_url, width="stretch")
        else:
            st.caption("실데이터 교체 시 공식 공고 링크가 표시됩니다.")

    render_section_head("MORE FOR YOU", "다른 추천 기회")
    for _, other in ranked[ranked["id"] != row["id"]].head(4).iterrows():
        render_opportunity_row(other, prefix="detail-list")


def render_goal_plan(ranked: pd.DataFrame, opportunities: pd.DataFrame, savings: pd.DataFrame) -> None:
    st.markdown('<div class="eyebrow">GOAL PLAN</div>', unsafe_allow_html=True)
    st.title("기회를 목표금액으로 연결해보세요")
    st.markdown('<div class="lead">목표는 선택사항입니다. 경쟁형 상금은 확정 수입과 분리해서 계산합니다.</div>', unsafe_allow_html=True)

    with st.expander("목표 금액과 기간 수정", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("목표 금액", min_value=100_000, step=100_000, key="target_amount")
        with c2:
            st.number_input("현재 보유 금액", min_value=0, step=50_000, key="current_amount")
        with c3:
            st.number_input("남은 기간(개월)", min_value=1, max_value=60, key="remaining_months")

    render_section_head("INCOME PATH", "목표에 반영할 경제기회", "확정 가능성이 있는 기회와 경쟁형 기회를 구분합니다.")
    eligible = ranked[ranked["eligible"]].head(6)
    checkbox_cols = st.columns(2)
    for index, (_, row) in enumerate(eligible.iterrows()):
        opportunity_id = str(row["id"])
        key = f"goal-check-{opportunity_id}"
        if key not in st.session_state:
            st.session_state[key] = opportunity_id in st.session_state.goal_opportunities
        with checkbox_cols[index % 2]:
            st.checkbox(
                f"{clean_title(row['title'])} · {opportunity_amount(row)}",
                key=key,
                on_change=sync_goal_check,
                args=(opportunity_id, key),
            )

    selected = opportunities[opportunities["id"].astype(str).isin(st.session_state.goal_opportunities)]
    plan = calculate_goal_plan(
        selected,
        target_amount=int(st.session_state.target_amount),
        current_amount=int(st.session_state.current_amount),
        remaining_months=int(st.session_state.remaining_months),
    )
    contribution = plan.current_amount + plan.expected_min
    progress = min(contribution / plan.target_amount, 1.0) if plan.target_amount else 0

    render_section_head("PLAN RESULT", "현재 계획으로 가능한 경로")
    result, impact = st.columns([1.4, 1], gap="large")
    with result:
        st.markdown(
            f"""
            <div class="soft-card">
              <div class="label">목표까지 남은 금액</div>
              <div class="goal-total">{format_money(plan.base_gap)}</div>
              <div class="goal-sub">현재 금액과 비경쟁형 기회의 최소 금액을 반영했습니다.</div>
              <div class="progress-track"><div class="progress-fill" style="width:{progress*100:.0f}%"></div></div>
              <div class="progress-meta"><span>{progress*100:.0f}% 마련 가능</span><span>{format_money(plan.target_amount)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with impact:
        st.markdown(
            f"""
            <div class="soft-card">
              <div class="label">매달 필요한 저축액</div>
              <div class="goal-total">{format_money(plan.monthly_required)}</div>
              <div class="impact-card"><b>경제기회 예상 {format_money(plan.expected_min)} ~ {format_money(plan.expected_max)}</b><p>도전 가능한 경쟁형 상금은 최대 {format_money(plan.challenge_max)}이며 기본 계획에는 포함하지 않았어요.</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_section_head(
        "SAVINGS",
        "내 계획에 가까운 실제 적금",
        "목표 기간·월 납입 가능 여부·기본금리를 먼저 보고, 우대금리는 조건을 따로 확인합니다.",
    )
    st.caption("은행 공식 페이지에서 확인한 세전 금리 스냅샷입니다. 가입 전 기준일과 최신 상품설명서를 반드시 다시 확인하세요.")
    recommendations = recommend_savings(
        savings,
        remaining_months=int(st.session_state.remaining_months),
        monthly_budget=int(plan.monthly_required),
    ).head(4)
    for _, product in recommendations.iterrows():
        term_min = int(product["min_term_months"])
        term_max = int(product["max_term_months"])
        term_label = f"{term_min}개월" if term_min == term_max else f"{term_min}~{term_max}개월"
        monthly_label = (
            f"월 {format_money(product['min_monthly'])}부터"
            if int(product["min_monthly"]) > 0
            else f"월 최대 {format_money(product['max_monthly'])}"
        )
        fit_notes = [f"목표 {int(product['matched_term_months'])}개월에 맞춤"]
        if not bool(product["within_monthly_limit"]):
            fit_notes.append("월 한도 초과분은 다른 수단과 분산 필요")
        if int(product["condition_level"]) >= 3:
            fit_notes.append("우대조건 확인 중요")

        name, rate, condition, action = st.columns([2.1, 1, 1.8, 0.8], vertical_alignment="center")
        with name:
            st.markdown(
                f"**{escape(clean_title(product['name']))}**  \n"
                f"<span style='color:#6b7684;font-size:.8rem'>{escape(str(product['provider']))} · {term_label} · {monthly_label}</span>  \n"
                f"<span style='color:#3182f6;font-size:.76rem'>{escape(' · '.join(fit_notes))}</span>",
                unsafe_allow_html=True,
            )
        with rate:
            st.markdown(
                f"<div style='text-align:right'><b>기본 {product['base_rate']:.2f}%</b><br>"
                f"<span style='color:#6b7684;font-size:.75rem'>최고 {product['max_rate']:.2f}% · {int(product['rate_term_months'])}개월 기준</span><br>"
                f"<span style='color:#8b95a1;font-size:.72rem'>{escape(str(product['rate_as_of']))}</span></div>",
                unsafe_allow_html=True,
            )
        with condition:
            st.markdown(
                f"<div style='color:#6b7684;font-size:.78rem'><b>우대조건</b><br>{escape(str(product['conditions']))}</div>",
                unsafe_allow_html=True,
            )
        with action:
            st.link_button("공식 확인", str(product["source_url"]), width="stretch")
        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)


def render_asset_list(alternatives: pd.DataFrame) -> None:
    st.markdown('<div class="eyebrow">ALTERNATIVE MARKET</div>', unsafe_allow_html=True)
    st.title("낯선 자산도, 가격 흐름부터 편하게")
    st.markdown('<div class="lead">구매 추천이 아니라 여러 수집형 자산의 시세·변동성·환금성을 같은 형식으로 비교합니다.</div>', unsafe_allow_html=True)
    st.markdown('<div class="demo-note">● 모든 가격은 UI 검증을 위한 예시이며 실제 투자 판단에 사용할 수 없습니다</div>', unsafe_allow_html=True)

    categories = ["전체"] + alternatives["category"].drop_duplicates().tolist()
    category = st.radio("자산 종류", categories, horizontal=True, label_visibility="collapsed", key="asset_category")
    view = alternatives if category == "전체" else alternatives[alternatives["category"] == category]
    market = build_market_index(view)
    change = (market.iloc[-1]["price"] / market.iloc[0]["price"] - 1) * 100
    change_class = "positive" if change >= 0 else "negative"
    st.markdown(
        f'<div class="section-head"><div class="eyebrow">MARKET INDEX · 6 MONTHS</div><div class="market-number">{market.iloc[-1]["price"]:,.1f} '
        f'<span class="{change_class}" style="font-size:1rem">{change:+.1f}%</span></div><p>{escape(category)} 자산을 100에서 시작한 지수로 환산한 데모입니다.</p></div>',
        unsafe_allow_html=True,
    )
    render_price_chart(market, height=230)

    render_section_head("ASSETS", "시세를 확인할 품목")
    for _, asset in view.iterrows():
        asset_id = str(asset["id"])
        history = build_price_history(asset["current_price"], asset["change_6m"], seed_key=asset_id)
        info, spark, price, action = st.columns([2.2, 1.45, 1.05, .95], vertical_alignment="center")
        with info:
            st.markdown(
                f'<div class="asset-row"><div class="asset-name">{category_icon(str(asset["category"]))} {escape(clean_title(asset["item"]))}</div>'
                f'<div class="asset-meta">{escape(str(asset["category"]))} · 위험 {escape(str(asset["risk"]))} · 환금성 {escape(str(asset["liquidity"]))}</div></div>',
                unsafe_allow_html=True,
            )
        with spark:
            render_price_chart(history, height=64, compact=True)
        with price:
            trend_class = "positive" if asset["change_6m"] >= 0 else "negative"
            st.markdown(
                f'<div class="asset-price">{format_money(asset["current_price"])}</div><div class="asset-delta {trend_class}">6개월 {asset["change_6m"]:+.1f}%</div>',
                unsafe_allow_html=True,
            )
        with action:
            st.button("시세 보기", key=f"asset-open-{asset_id}", width="stretch", on_click=open_asset, args=(asset_id,))
        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)


def render_asset_detail(alternatives: pd.DataFrame) -> None:
    matches = alternatives[alternatives["id"].astype(str) == st.session_state.selected_asset]
    asset = matches.iloc[0] if not matches.empty else alternatives.iloc[0]
    asset_id = str(asset["id"])
    history = build_price_history(asset["current_price"], asset["change_6m"], seed_key=asset_id)
    trend_class = "positive" if asset["change_6m"] >= 0 else "negative"

    st.button("← 시장으로 돌아가기", key="asset-back", on_click=close_asset)
    st.markdown(
        f"""
        <div class="detail-hero">
          <div class="op-tags"><span class="pill blue">{escape(str(asset['category']))}</span><span class="pill">6개월 시세</span></div>
          <h1>{category_icon(str(asset['category']))} {escape(clean_title(asset['item']))}</h1>
          <div class="lead">{escape(str(asset['summary']))}</div>
          <div class="detail-amount">{format_money(asset['current_price'])} <span class="{trend_class}" style="font-size:1rem">6개월 {asset['change_6m']:+.1f}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    periods = {"1개월": 5, "3개월": 13, "6개월": 26}
    period = st.radio("조회 기간", list(periods), horizontal=True, label_visibility="collapsed", key="asset_period")
    chart_data = history.tail(periods[period]).reset_index(drop=True)
    render_price_chart(chart_data, height=330)

    low = int(chart_data["price"].min())
    high = int(chart_data["price"].max())
    c1, c2, c3, c4 = st.columns(4)
    facts = [
        ("기간 내 최저", format_money(low)),
        ("기간 내 최고", format_money(high)),
        ("환금성", str(asset["liquidity"])),
        ("위험도", str(asset["risk"])),
    ]
    for column, (label, value) in zip([c1, c2, c3, c4], facts):
        with column:
            st.markdown(f'<div class="soft-card"><div class="label">{escape(label)}</div><div class="big" style="font-size:1.05rem">{escape(value)}</div></div>', unsafe_allow_html=True)

    favorite = asset_id in st.session_state.favorite_assets
    st.button(
        "관심 자산에서 제거" if favorite else "관심 자산에 추가",
        key=f"asset-fav-{asset_id}",
        type="primary",
        width="stretch",
        on_click=toggle_asset,
        args=(asset_id,),
    )
    st.markdown('<div class="warning-box">대체자산은 거래량이 적고 상태·진품 여부·보관 비용에 따라 실제 가격 차이가 큽니다. 이 화면은 가격 탐색 방식을 보여주는 데모이며 매수 추천이 아닙니다.</div>', unsafe_allow_html=True)


def render_favorites(ranked: pd.DataFrame, alternatives: pd.DataFrame) -> None:
    st.markdown('<div class="eyebrow">SAVED</div>', unsafe_allow_html=True)
    st.title("다시 보고 싶은 기회와 자산")
    opportunity_tab, asset_tab = st.tabs(["경제기회", "대체자산"])
    with opportunity_tab:
        favorites = ranked[ranked["id"].astype(str).isin(st.session_state.favorites)]
        if favorites.empty:
            st.markdown('<div class="empty-state">저장한 경제기회가 없습니다.<br>추천 목록에서 관심 기회를 저장해보세요.</div>', unsafe_allow_html=True)
        else:
            for _, row in favorites.iterrows():
                render_opportunity_row(row, prefix="saved")
    with asset_tab:
        favorite_assets = alternatives[alternatives["id"].astype(str).isin(st.session_state.favorite_assets)]
        if favorite_assets.empty:
            st.markdown('<div class="empty-state">저장한 대체자산이 없습니다.<br>시세 상세에서 관심 자산을 추가해보세요.</div>', unsafe_allow_html=True)
        else:
            for _, asset in favorite_assets.iterrows():
                info, action = st.columns([4, 1], vertical_alignment="center")
                with info:
                    st.markdown(f"**{category_icon(str(asset['category']))} {escape(clean_title(asset['item']))}**  \n{format_money(asset['current_price'])} · 6개월 {asset['change_6m']:+.1f}%")
                with action:
                    st.button("시세 보기", key=f"saved-asset-{asset['id']}", width="stretch", on_click=open_asset, args=(str(asset["id"]),))
                st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)


opportunities, savings, alternatives = load_data()
init_state(opportunities, alternatives)

ranked = rank_opportunities(
    opportunities,
    grade=int(st.session_state.profile_grade),
    residence=str(st.session_state.profile_residence),
    available_hours=int(st.session_state.profile_hours),
    region=str(st.session_state.profile_region),
    interests=list(st.session_state.profile_interests),
)

page = render_header()
if page == "홈":
    render_home(ranked, alternatives)
elif page == "경제기회":
    if st.session_state.opportunity_detail:
        render_opportunity_detail(ranked)
    else:
        render_opportunity_list(ranked)
elif page == "목표계획":
    render_goal_plan(ranked, opportunities, savings)
elif page == "대체자산":
    if st.session_state.asset_detail:
        render_asset_detail(alternatives)
    else:
        render_asset_list(alternatives)
elif page == "관심목록":
    render_favorites(ranked, alternatives)

with st.expander("프로젝트 소개와 데이터 안내"):
    st.write(
        "기존 자산관리 서비스가 이미 가진 돈을 어디에 넣을지 안내한다면, "
        "Campus Money Guide는 대학생이 장학·근로·공모전으로 돈을 마련하는 단계부터 시작합니다."
    )
    st.caption("현재 MVP에서는 회원가입, 계좌 연동, 자동 매수, 투자수익 예측을 제공하지 않습니다.")

footer_meta = load_opportunity_meta()
footer_source = (
    f"{footer_meta.get('school', '학교')} 공식 공고 기반"
    if footer_meta.get("source_type") == "official_school_notices"
    else f"데모 기준일 {date.today().isoformat()}"
)
st.markdown(
    f'<div class="footer-note">Campus Money Guide · {escape(footer_source)} · 원문과 최신 조건을 반드시 확인하세요.</div>',
    unsafe_allow_html=True,
)

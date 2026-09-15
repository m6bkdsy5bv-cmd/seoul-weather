import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ────────────────────────────────
# 기본 설정
# ────────────────────────────────
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="centered",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


@st.cache_data
def get_yearly_avg(df: pd.DataFrame) -> pd.DataFrame:
    # 관측 일수가 300일 이상인 '온전한 연도'만 사용 (첫해·마지막해는 자료가 일부만 있을 수 있음)
    counts = df.groupby("연도")["평균기온"].count()
    full_years = counts[counts >= 300].index
    yearly = (
        df[df["연도"].isin(full_years)]
        .groupby("연도")["평균기온"]
        .mean()
        .reset_index()
        .rename(columns={"평균기온": "연평균기온"})
    )
    return yearly


# ────────────────────────────────
# 화면 구성
# ────────────────────────────────
st.title("🌡️ 서울, 100년의 기온 변화")
st.markdown(
    "서울의 **일별 기온 관측 데이터**를 이용해서, "
    "지난 100여 년간 **연평균 기온**이 어떻게 달라졌는지 살펴봐요."
)

with st.spinner("데이터를 불러오는 중이에요..."):
    raw_df = load_data(DATA_URL)
    yearly_df = get_yearly_avg(raw_df)

first_year = int(yearly_df["연도"].min())
last_year = int(yearly_df["연도"].max())

st.caption(f"📅 분석 기간: {first_year}년 ~ {last_year}년 (총 {last_year - first_year + 1}년)")

# ────────────────────────────────
# 핵심 지표 카드
# ────────────────────────────────
recent_n = 10
early_avg = yearly_df.head(recent_n)["연평균기온"].mean()
recent_avg = yearly_df.tail(recent_n)["연평균기온"].mean()
diff = recent_avg - early_avg

col1, col2, col3 = st.columns(3)
col1.metric(f"초기 {recent_n}년 평균", f"{early_avg:.1f} ℃")
col2.metric(f"최근 {recent_n}년 평균", f"{recent_avg:.1f} ℃")
col3.metric("변화량", f"{diff:+.1f} ℃")

st.markdown("---")

# ────────────────────────────────
# 그래프: 연평균 기온 + 추세선 + 10년 이동평균
# ────────────────────────────────
x = yearly_df["연도"].values
y = yearly_df["연평균기온"].values

# 선형 추세선
coef = np.polyfit(x, y, 1)
trend = np.poly1d(coef)(x)

# 10년 이동평균 (부드러운 변화 확인용)
yearly_df["10년 이동평균"] = yearly_df["연평균기온"].rolling(window=10, center=True, min_periods=1).mean()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x, y=y,
    mode="lines+markers",
    name="연평균 기온",
    line=dict(color="#F6C453", width=1.5),
    marker=dict(size=4),
    opacity=0.7,
))

fig.add_trace(go.Scatter(
    x=x, y=yearly_df["10년 이동평균"],
    mode="lines",
    name="10년 이동평균",
    line=dict(color="#E07B39", width=3),
))

fig.add_trace(go.Scatter(
    x=x, y=trend,
    mode="lines",
    name="전체 추세선",
    line=dict(color="#A15C1E", width=2, dash="dash"),
))

fig.update_layout(
    title=f"서울 연평균 기온 변화 ({first_year}~{last_year})",
    xaxis_title="연도",
    yaxis_title="연평균 기온 (℃)",
    template="plotly_white",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────
# 해설
# ────────────────────────────────
per_decade = coef[0] * 10
st.info(
    f"📈 **추세선 분석**: 1년마다 평균적으로 약 **{coef[0]:.3f}℃**씩 올랐고, "
    f"10년으로 환산하면 약 **{per_decade:.2f}℃** 상승한 셈이에요."
)

with st.expander("📋 연도별 데이터 표로 보기"):
    st.dataframe(
        yearly_df[["연도", "연평균기온"]].sort_values("연도", ascending=False).round(2),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("ℹ️ 데이터 안내"):
    st.markdown(
        "- 데이터 출처: [greatsong/modudata](https://github.com/greatsong/modudata) 서울 기온 관측 데이터\n"
        "- 열 구성: 날짜, 지점, 평균기온, 최저기온, 최고기온\n"
        "- 관측 일수가 300일 미만인 연도(자료가 일부만 있는 첫해·마지막해 등)는 "
        "평균 계산에서 제외했어요."
    )

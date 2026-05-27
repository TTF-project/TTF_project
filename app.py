import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# =========================================
# 페이지 설정
# =========================================

st.set_page_config(
    page_title="TTF Crypto",
    layout="wide"
)

# =========================================
# CSS (모바일 + 가독성 강화)
# =========================================

st.markdown("""
<style>

/* 전체 배경 */
html, body, [class*="css"] {
    background-color: #0F172A;
    color: #FFFFFF !important;
}

/* 메인 컨테이너 */
.block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    padding-bottom: 2rem;
}

/* 전체 글씨 */
p, span, div, label {
    color: #FFFFFF !important;
}

/* 제목 */
.main-title {
    font-size: 34px;
    font-weight: bold;
    text-align: center;
    color: #00F5B4 !important;
    margin-bottom: 25px;
}

/* 카드 */
.card {
    background-color: #1E293B;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
    border: 1px solid #334155;
}

/* 카드 제목 */
.card-title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 15px;
    color: #FFFFFF !important;
}

/* LONG */
.long {
    color: #00FF99 !important;
    font-size: 34px;
    font-weight: bold;
    margin-bottom: 15px;
}

/* SHORT */
.short {
    color: #FF5C5C !important;
    font-size: 34px;
    font-weight: bold;
    margin-bottom: 15px;
}

/* NEUTRAL */
.neutral {
    color: #FFD54A !important;
    font-size: 34px;
    font-weight: bold;
    margin-bottom: 15px;
}

/* 정보 */
.info {
    font-size: 19px;
    font-weight: 600;
    color: #FFFFFF !important;
    margin-top: 10px;
}

/* 박스 */
.div-box {
    background-color: #334155;
    border-radius: 14px;
    padding: 14px;
    margin-top: 10px;
    font-size: 17px;
    font-weight: bold;
    color: #FFFFFF !important;
}

/* 라디오 버튼 전체 */
div[role="radiogroup"] label {

    background-color: #1E293B !important;

    color: #FFFFFF !important;

    padding: 10px 18px !important;

    border-radius: 12px !important;

    border: 1px solid #475569 !important;

    margin-right: 10px !important;

    font-size: 18px !important;

    font-weight: bold !important;

}

/* 선택된 버튼 */
div[role="radiogroup"] label[data-baseweb="radio"] input:checked + div {

    color: #00FF99 !important;

}

/* 모바일 */
@media (max-width: 768px) {

    .main-title {
        font-size: 26px;
    }

    .card-title {
        font-size: 18px;
    }

    .info {
        font-size: 16px;
    }

    .long, .short, .neutral {
        font-size: 28px;
    }

    .div-box {
        font-size: 15px;
    }

}

</style>
""", unsafe_allow_html=True)

# =========================================
# 제목
# =========================================

st.markdown(
    '<div class="main-title">📈 TTF CRYPTO INTELLIGENCE</div>',
    unsafe_allow_html=True
)

# =========================================
# 거래소
# =========================================

exchange = ccxt.binanceus()

# =========================================
# 코인 선택
# =========================================

symbol = st.radio(
    "코인 선택",
    ["BTC/USDT", "ETH/USDT", "XRP/USDT"],
    horizontal=True
)

# =========================================
# 데이터 가져오기
# =========================================

def get_data(timeframe):

    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=300
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms"
    )

    return df

# =========================================
# 지표 계산
# =========================================

def calculate(df):

    ema20 = EMAIndicator(
        close=df["close"],
        window=20
    )

    ema50 = EMAIndicator(
        close=df["close"],
        window=50
    )

    rsi = RSIIndicator(
        close=df["close"],
        window=14
    )

    df["ema20"] = ema20.ema_indicator()
    df["ema50"] = ema50.ema_indicator()
    df["rsi"] = rsi.rsi()

    return df

# =========================================
# 추세 분석
# =========================================

def get_trend(df):

    price = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]

    if price > ema20 > ema50:
        return "LONG"

    elif price < ema20 < ema50:
        return "SHORT"

    else:
        return "NEUTRAL"

# =========================================
# 다이버전스 감지
# =========================================

def detect_divergence(df):

    recent_price = df["close"].iloc[-5:]
    recent_rsi = df["rsi"].iloc[-5:]

    if (
        recent_price.iloc[-1] < recent_price.iloc[0]
        and
        recent_rsi.iloc[-1] > recent_rsi.iloc[0]
    ):

        return "🟢 Bullish Divergence"

    elif (
        recent_price.iloc[-1] > recent_price.iloc[0]
        and
        recent_rsi.iloc[-1] < recent_rsi.iloc[0]
    ):

        return "🔴 Bearish Divergence"

    else:

        return "⚪ 없음"

# =========================================
# 데이터 로드
# =========================================

df_15m = calculate(get_data("15m"))
df_1h = calculate(get_data("1h"))
df_4h = calculate(get_data("4h"))
df_1d = calculate(get_data("1d"))

# =========================================
# 추세 계산
# =========================================

trend_15m = get_trend(df_15m)
trend_1h = get_trend(df_1h)
trend_4h = get_trend(df_4h)

# =========================================
# 최종 시그널
# =========================================

if trend_4h == trend_1h:

    final_signal = trend_4h

else:

    final_signal = "NEUTRAL"

# =========================================
# 현재가
# =========================================

current_price = round(
    df_15m["close"].iloc[-1],
    2
)

# =========================================
# 진입 / 손절 / 익절
# =========================================

if final_signal == "LONG":

    entry = current_price
    stop = round(entry * 0.98, 2)
    target = round(entry * 1.04, 2)

    rr = round(
        (target - entry)
        /
        (entry - stop),
        2
    )

    probability = "높음"

elif final_signal == "SHORT":

    entry = current_price
    stop = round(entry * 1.02, 2)
    target = round(entry * 0.96, 2)

    rr = round(
        (entry - target)
        /
        (stop - entry),
        2
    )

    probability = "높음"

else:

    entry = "-"
    stop = "-"
    target = "-"
    rr = "-"
    probability = "낮음"

# =========================================
# 시그널 색상
# =========================================

if final_signal == "LONG":
    signal_class = "long"

elif final_signal == "SHORT":
    signal_class = "short"

else:
    signal_class = "neutral"

# =========================================
# 메인 카드
# =========================================

st.markdown(f"""
<div class="card">

<div class="{signal_class}">
{final_signal}
</div>

<div class="info">
💰 현재가 : {current_price}
</div>

<div class="info">
🎯 진입가 : {entry}
</div>

<div class="info">
🛑 손절가 : {stop}
</div>

<div class="info">
🚀 목표가 : {target}
</div>

<div class="info">
⚖ 손익비 : {rr}
</div>

<div class="info">
📊 전략 신뢰도 : {probability}
</div>

</div>
""", unsafe_allow_html=True)

# =========================================
# 멀티 타임프레임
# =========================================

st.markdown("""
<div class="card">

<div class="card-title">
📡 멀티 타임프레임 분석
</div>

""", unsafe_allow_html=True)

st.markdown(f"""
<div class="div-box">
📍 15분봉 :
<span style="color:#FFFFFF;font-weight:bold;">
{trend_15m}
</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="div-box">
📍 1시간봉 :
<span style="color:#FFFFFF;font-weight:bold;">
{trend_1h}
</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="div-box">
📍 4시간봉 :
<span style="color:#FFFFFF;font-weight:bold;">
{trend_4h}
</span>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================
# 다이버전스
# =========================================

st.markdown("""
<div class="card">

<div class="card-title">
⚠ RSI 다이버전스
</div>

""", unsafe_allow_html=True)

st.markdown(
    f'<div class="div-box">15분봉 : {detect_divergence(df_15m)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">1시간봉 : {detect_divergence(df_1h)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">4시간봉 : {detect_divergence(df_4h)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">일봉 : {detect_divergence(df_1d)}</div>',
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================
# 차트 생성
# =========================================

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.6, 0.2, 0.2]
)

# =========================================
# 캔들 차트
# =========================================

fig.add_trace(
    go.Candlestick(
        x=df_15m["timestamp"],
        open=df_15m["open"],
        high=df_15m["high"],
        low=df_15m["low"],
        close=df_15m["close"],
        name="Price"
    ),
    row=1,
    col=1
)

# =========================================
# EMA20
# =========================================

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["ema20"],
        name="EMA20",
        line=dict(color="#00E5FF", width=2)
    ),
    row=1,
    col=1
)

# =========================================
# EMA50
# =========================================

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["ema50"],
        name="EMA50",
        line=dict(color="#FFD54A", width=2)
    ),
    row=1,
    col=1
)

# =========================================
# 거래량
# =========================================

fig.add_trace(
    go.Bar(
        x=df_15m["timestamp"],
        y=df_15m["volume"],
        name="Volume",
        marker_color="#00E5FF"
    ),
    row=2,
    col=1
)

# =========================================
# RSI
# =========================================

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["rsi"],
        name="RSI",
        line=dict(color="#00FF99", width=2)
    ),
    row=3,
    col=1
)

# =========================================
# 차트 레이아웃
# =========================================

fig.update_layout(
    template="plotly_dark",
    height=750,
    xaxis_rangeslider_visible=False,

    paper_bgcolor="#0F172A",
    plot_bgcolor="#111827",

    font=dict(
        size=15,
        color="white"
    ),

    legend=dict(
        font=dict(
            color="white"
        )
    )
)

# 격자

fig.update_xaxes(
    gridcolor="#374151"
)

fig.update_yaxes(
    gridcolor="#374151"
)

# =========================================
# 차트 출력
# =========================================

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================
# 마지막 업데이트
# =========================================

st.caption(
    f"마지막 업데이트 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
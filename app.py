import streamlit as st
import pandas as pd
import numpy as np
import ccxt

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from datetime import datetime

# ======================================================
# 페이지 설정
# ======================================================

st.set_page_config(
    page_title="TTF V6 PRO FINAL",
    layout="wide"
)

# ======================================================
# CSS
# ======================================================

st.markdown("""
<style>

html, body, [class*="css"] {

    background-color: #0F172A;
    color: white !important;

}

/* 제목 */

.main-title {

    font-size: 34px;
    font-weight: bold;
    text-align: center;
    color: #00FFB2;
    margin-bottom: 20px;

}

/* 카드 */

.card {

    background: #1E293B;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #334155;

}

/* 카드 제목 */

.card-title {

    font-size: 22px;
    font-weight: bold;
    margin-bottom: 15px;

}

/* 신호 */

.long {

    color: #00FF99;
    font-size: 34px;
    font-weight: bold;

}

.short {

    color: #FF5C5C;
    font-size: 34px;
    font-weight: bold;

}

.neutral {

    color: #FFD54A;
    font-size: 34px;
    font-weight: bold;

}

/* 정보 */

.info {

    font-size: 18px;
    margin-top: 8px;
    font-weight: 600;

}

/* 박스 */

.box {

    background: #334155;
    padding: 14px;
    border-radius: 14px;
    margin-top: 10px;
    font-size: 16px;
    font-weight: bold;

}

/* 라디오 버튼 */

div[role="radiogroup"] label {

    background-color: #1E293B !important;
    color: white !important;

    padding: 10px 18px !important;

    border-radius: 12px !important;

    border: 1px solid #475569 !important;

    margin-right: 10px !important;

    font-size: 18px !important;

    font-weight: bold !important;

}

/* 모바일 */

@media (max-width:768px){

    .main-title{
        font-size:26px;
    }

    .card-title{
        font-size:18px;
    }

    .info{
        font-size:15px;
    }

    .box{
        font-size:14px;
    }

}

</style>
""", unsafe_allow_html=True)

# ======================================================
# 제목
# ======================================================

st.markdown(
    '<div class="main-title">🚀 TTF V6 PRO FINAL</div>',
    unsafe_allow_html=True
)

# ======================================================
# 거래소
# ======================================================

exchange = ccxt.binanceus()

# ======================================================
# 코인 선택
# ======================================================

symbol = st.radio(
    "코인 선택",
    ["BTC/USDT", "ETH/USDT", "XRP/USDT"],
    horizontal=True
)

# ======================================================
# 데이터 가져오기
# ======================================================

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

# ======================================================
# 지표 계산
# ======================================================

def calculate(df):

    df["ema20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    df["rsi"] = RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["atr"] = atr.average_true_range()

    return df

# ======================================================
# 추세 판단
# ======================================================

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

# ======================================================
# 횡보 필터
# ======================================================

def is_sideways(df):

    ema_gap = abs(
        df["ema20"].iloc[-1]
        -
        df["ema50"].iloc[-1]
    )

    price = df["close"].iloc[-1]

    gap_percent = ema_gap / price * 100

    if gap_percent < 0.3:

        return True

    return False

# ======================================================
# 거래량 강도
# ======================================================

def volume_strength(df):

    current = df["volume"].iloc[-1]

    avg = df["volume"].rolling(20).mean().iloc[-1]

    if current > avg:

        return "STRONG"

    return "WEAK"

# ======================================================
# 추세 강도 점수
# ======================================================

def trend_score(df):

    score = 0

    price = df["close"].iloc[-1]

    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]

    rsi = df["rsi"].iloc[-1]

    if price > ema20:
        score += 30

    if ema20 > ema50:
        score += 30

    if rsi > 55:
        score += 20

    if volume_strength(df) == "STRONG":
        score += 20

    return score

# ======================================================
# RSI 다이버전스 감지
# ======================================================

def detect_divergence(df):

    closes = df["close"]
    rsi = df["rsi"]

    p1 = closes.iloc[-5]
    p2 = closes.iloc[-1]

    r1 = rsi.iloc[-5]
    r2 = rsi.iloc[-1]

    # Bullish Divergence

    if p2 < p1 and r2 > r1:

        return "BULLISH"

    # Bearish Divergence

    elif p2 > p1 and r2 < r1:

        return "BEARISH"

    else:

        return "NONE"

# ======================================================
# 데이터 로드
# ======================================================

df_15m = calculate(get_data("15m"))
df_1h = calculate(get_data("1h"))
df_4h = calculate(get_data("4h"))

# ======================================================
# 다이버전스
# ======================================================

div_15m = detect_divergence(df_15m)
div_1h = detect_divergence(df_1h)
div_4h = detect_divergence(df_4h)

# ======================================================
# 추세
# ======================================================

trend_15m = get_trend(df_15m)
trend_1h = get_trend(df_1h)
trend_4h = get_trend(df_4h)

# ======================================================
# 횡보 여부
# ======================================================

sideways = is_sideways(df_4h)

# ======================================================
# 최종 신호
# ======================================================

if sideways:

    final_signal = "NEUTRAL"

elif trend_4h == "LONG" and trend_1h == "LONG":

    final_signal = "LONG"

elif trend_4h == "SHORT" and trend_1h == "SHORT":

    final_signal = "SHORT"

else:

    final_signal = "NEUTRAL"

# ======================================================
# 현재가
# ======================================================

current_price = round(
    df_15m["close"].iloc[-1],
    2
)

# ======================================================
# ATR
# ======================================================

atr = df_4h["atr"].iloc[-1]

# ======================================================
# 진입 / 손절 / 익절
# ======================================================

if final_signal == "LONG":

    entry = current_price

    stop = round(
        entry - (atr * 1.5),
        2
    )

    target = round(
        entry + (atr * 3),
        2
    )

    strategy = "공격적 LONG 전략"

elif final_signal == "SHORT":

    entry = current_price

    stop = round(
        entry + (atr * 1.5),
        2
    )

    target = round(
        entry - (atr * 3),
        2
    )

    strategy = "공격적 SHORT 전략"

else:

    entry = "-"
    stop = "-"
    target = "-"
    strategy = "관망 추천"

# ======================================================
# 추세 강도
# ======================================================

score = trend_score(df_4h)

# ======================================================
# 시장 상태
# ======================================================

market_status = "횡보장"

if score >= 70:

    market_status = "강한 추세장"

elif score >= 40:

    market_status = "중립 시장"

# ======================================================
# 신호 색상
# ======================================================

if final_signal == "LONG":

    signal_class = "long"

elif final_signal == "SHORT":

    signal_class = "short"

else:

    signal_class = "neutral"

# ======================================================
# 메인 카드
# ======================================================

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
📈 추세 강도 : {score}/100
</div>

<div class="info">
🧠 전략 : {strategy}
</div>

</div>

""", unsafe_allow_html=True)

# ======================================================
# 시장 상태 카드
# ======================================================

st.markdown(f"""

<div class="card">

<div class="card-title">
📊 시장 상태
</div>

<div class="box">
시장 상태 : {market_status}
</div>

<div class="box">
거래량 : {volume_strength(df_4h)}
</div>

<div class="box">
4시간 추세 : {trend_4h}
</div>

<div class="box">
1시간 추세 : {trend_1h}
</div>

<div class="box">
15분 추세 : {trend_15m}
</div>

<div class="box">
15분 다이버전스 : {div_15m}
</div>

<div class="box">
1시간 다이버전스 : {div_1h}
</div>

<div class="box">
4시간 다이버전스 : {div_4h}
</div>

</div>

""", unsafe_allow_html=True)

# ======================================================
# 차트
# ======================================================

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.6,0.2,0.2],
    vertical_spacing=0.03
)

# 캔들

fig.add_trace(
    go.Candlestick(
        x=df_15m["timestamp"],
        open=df_15m["open"],
        high=df_15m["high"],
        low=df_15m["low"],
        close=df_15m["close"],
        name="PRICE"
    ),
    row=1,
    col=1
)

# EMA20

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["ema20"],
        line=dict(
            color="#00E5FF",
            width=2
        ),
        name="EMA20"
    ),
    row=1,
    col=1
)

# EMA50

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["ema50"],
        line=dict(
            color="#FFD54A",
            width=2
        ),
        name="EMA50"
    ),
    row=1,
    col=1
)

# 거래량

fig.add_trace(
    go.Bar(
        x=df_15m["timestamp"],
        y=df_15m["volume"],
        marker_color="#00E5FF",
        name="Volume"
    ),
    row=2,
    col=1
)

# RSI

fig.add_trace(
    go.Scatter(
        x=df_15m["timestamp"],
        y=df_15m["rsi"],
        line=dict(
            color="#00FF99",
            width=2
        ),
        name="RSI"
    ),
    row=3,
    col=1
)

# RSI 기준선

fig.add_hline(
    y=70,
    line_dash="dash",
    line_color="red",
    row=3,
    col=1
)

fig.add_hline(
    y=30,
    line_dash="dash",
    line_color="green",
    row=3,
    col=1
)

# 레이아웃

fig.update_layout(

    template="plotly_dark",

    height=850,

    xaxis_rangeslider_visible=False,

    paper_bgcolor="#0F172A",

    plot_bgcolor="#111827",

    font=dict(
        color="white",
        size=14
    )
)

fig.update_xaxes(
    gridcolor="#374151"
)

fig.update_yaxes(
    gridcolor="#374151"
)

# ======================================================
# 출력
# ======================================================

st.plotly_chart(
    fig,
    use_container_width=True
)

# ======================================================
# 시간
# ======================================================

st.caption(
    f"업데이트 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
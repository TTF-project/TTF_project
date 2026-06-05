import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import requests

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from datetime import datetime

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="TTF V7 SCALPING",
    layout="wide"
)

# ==================================================
# CSS
# ==================================================

st.markdown("""
<style>

html, body, [class*="css"] {

    background-color:#0F172A;
    color:white !important;

}

.main-title {

    font-size:34px;
    font-weight:bold;
    text-align:center;

    color:#00FFB2;

    margin-bottom:20px;

}

.card {

    background:#1E293B;

    padding:20px;

    border-radius:20px;

    margin-bottom:20px;

    border:1px solid #334155;

}

.card-title {

    font-size:22px;

    font-weight:bold;

    margin-bottom:10px;

}

.long {

    color:#00FF99;

    font-size:34px;

    font-weight:bold;

}

.short {

    color:#FF5C5C;

    font-size:34px;

    font-weight:bold;

}

.neutral {

    color:#FFD54A;

    font-size:34px;

    font-weight:bold;

}

.info {

    font-size:18px;

    font-weight:600;

    margin-top:8px;

}

.box {

    background:#334155;

    padding:12px;

    border-radius:12px;

    margin-top:10px;

    font-size:16px;

    font-weight:bold;

}

@media (max-width:768px){

    .main-title{
        font-size:24px;
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

# ==================================================
# TITLE
# ==================================================

st.markdown(
    '<div class="main-title">⚡ TTF V7 SCALPING</div>',
    unsafe_allow_html=True
)

# ==================================================
# TELEGRAM
# ==================================================

def send_telegram(message):

    try:

        token = st.secrets["BOT_TOKEN"]
        chat_id = st.secrets["CHAT_ID"]

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message
            },
            timeout=10
        )

    except Exception:
        pass


if "last_signal" not in st.session_state:

    st.session_state.last_signal = ""

# ==================================================
# EXCHANGE
# ==================================================

exchange = ccxt.binanceus()

# ==================================================
# SYMBOL
# ==================================================

symbol = st.radio(
    "코인 선택",
    [
        "BTC/USDT",
        "ETH/USDT",
        "XRP/USDT"
    ],
    horizontal=True
)

# ==================================================
# DATA
# ==================================================

@st.cache_data(ttl=30)
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

# ==================================================
# INDICATORS
# ==================================================

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

# ==================================================
# TREND
# ==================================================

def get_trend(df):

    price = df["close"].iloc[-1]

    ema20 = df["ema20"].iloc[-1]

    ema50 = df["ema50"].iloc[-1]

    if price > ema20 > ema50:

        return "LONG"

    elif price < ema20 < ema50:

        return "SHORT"

    return "NEUTRAL"

# ==================================================
# VOLUME
# ==================================================

def volume_strength(df):

    current = df["volume"].iloc[-1]

    avg = df["volume"].rolling(20).mean().iloc[-1]

    if current > avg:

        return "STRONG"

    return "WEAK"

# ==================================================
# DIVERGENCE
# ==================================================

def detect_divergence(df):

    closes = df["close"]

    rsi = df["rsi"]

    p1 = closes.iloc[-5]
    p2 = closes.iloc[-1]

    r1 = rsi.iloc[-5]
    r2 = rsi.iloc[-1]

    if p2 < p1 and r2 > r1:

        return "BULLISH"

    elif p2 > p1 and r2 < r1:

        return "BEARISH"

    return "NONE"

# ==================================================
# LOAD DATA
# ==================================================

df_3m = calculate(get_data("3m"))

df_5m = calculate(get_data("5m"))

df_15m = calculate(get_data("15m"))

df_1h = calculate(get_data("1h"))

df_4h = calculate(get_data("4h"))

# ==================================================
# TRENDS
# ==================================================

trend_4h = get_trend(df_4h)

trend_1h = get_trend(df_1h)

trend_15m = get_trend(df_15m)

# ==================================================
# DIVERGENCE
# ==================================================

div_15m = detect_divergence(df_15m)

div_1h = detect_divergence(df_1h)

div_4h = detect_divergence(df_4h)

# ==================================================
# SCALPING ENGINE
# ==================================================

rsi_3m = df_3m["rsi"].iloc[-1]
rsi_5m = df_5m["rsi"].iloc[-1]

volume_state = volume_strength(df_15m)

scalp_signal = "WAIT"

confidence = 50

# LONG

if (
    trend_4h == "LONG"
    and trend_1h == "LONG"
    and trend_15m == "LONG"
):

    confidence += 20

    if rsi_5m > 50:

        confidence += 10

    if volume_state == "STRONG":

        confidence += 10

    if div_15m == "BULLISH":

        confidence += 10

    if (
        rsi_3m > 50
        and df_3m["close"].iloc[-1]
        > df_3m["ema20"].iloc[-1]
    ):

        scalp_signal = "LONG"

# SHORT

elif (
    trend_4h == "SHORT"
    and trend_1h == "SHORT"
    and trend_15m == "SHORT"
):

    confidence += 20

    if rsi_5m < 50:

        confidence += 10

    if volume_state == "STRONG":

        confidence += 10

    if div_15m == "BEARISH":

        confidence += 10

    if (
        rsi_3m < 50
        and df_3m["close"].iloc[-1]
        < df_3m["ema20"].iloc[-1]
    ):

        scalp_signal = "SHORT"

# ==================================================
# PRICE
# ==================================================

current_price = round(
    df_3m["close"].iloc[-1],
    4
)

# ==================================================
# TP / SL
# ==================================================

if scalp_signal == "LONG":

    entry = current_price

    stop = round(entry * 0.993, 4)

    tp1 = round(entry * 1.01, 4)
    tp2 = round(entry * 1.015, 4)
    tp3 = round(entry * 1.02, 4)


elif scalp_signal == "SHORT":

    recent_low = df_15m["low"].tail(50).min()

    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_low, 4)

    ai_tp2 = round(
        recent_low - atr_value,
        4
    )

    ai_tp3 = round(
        recent_low - atr_value * 2,
        4
    )

    base_prob = min(
        round(confidence * 0.9),
        95
    )

    ai_prob1 = max(base_prob, 40)

    ai_prob2 = max(base_prob - 15, 25)

    ai_prob3 = max(base_prob - 30, 10)


else:

    entry = "-"
    stop = "-"
    tp1 = "-"
    tp2 = "-"
    tp3 = "-"

# ==================================================
# AI TARGET (STRUCTURE + ATR)
# ==================================================

if scalp_signal == "LONG":

    recent_high = df_15m["high"].tail(50).max()
    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_high, 4)
    ai_tp2 = round(recent_high + atr_value, 4)
    ai_tp3 = round(recent_high + atr_value * 2, 4)

    base_prob = min(round(confidence * 0.9), 95)

    ai_prob1 = max(base_prob, 40)
    ai_prob2 = max(base_prob - 15, 25)
    ai_prob3 = max(base_prob - 30, 10)


elif scalp_signal == "SHORT":

    recent_low = df_15m["low"].tail(50).min()
    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_low, 4)
    ai_tp2 = round(recent_low - atr_value, 4)
    ai_tp3 = round(recent_low - atr_value * 2, 4)

    base_prob = min(round(confidence * 0.9), 95)

    ai_prob1 = max(base_prob, 40)
    ai_prob2 = max(base_prob - 15, 25)
    ai_prob3 = max(base_prob - 30, 10)


else:

    ai_tp1 = "-"
    ai_tp2 = "-"
    ai_tp3 = "-"

    ai_prob1 = "-"
    ai_prob2 = "-"
    ai_prob3 = "-"

# ==================================================
# TELEGRAM ALERT
# ==================================================

if scalp_signal == "LONG":

    signal_key = f"{symbol}_LONG"

    if st.session_state.last_signal != signal_key:

        send_telegram(
            f"""
🚀 LONG SIGNAL

종목 : {symbol}

진입가 : {entry}

손절가 : {stop}

TP1 : {tp1}

TP2 : {tp2}

TP3 : {tp3}

신뢰도 : {confidence}/100
"""
        )

        st.session_state.last_signal = signal_key

elif scalp_signal == "SHORT":

    signal_key = f"{symbol}_SHORT"

    if st.session_state.last_signal != signal_key:

        send_telegram(
            f"""
🔻 SHORT SIGNAL

종목 : {symbol}

진입가 : {entry}

손절가 : {stop}

TP1 : {tp1}

TP2 : {tp2}

TP3 : {tp3}

신뢰도 : {confidence}/100
"""
        )

        st.session_state.last_signal = signal_key

else:

    st.session_state.last_signal = ""

# ==================================================
# AI TARGET
# ==================================================

if scalp_signal == "LONG":

    recent_high = df_15m["high"].tail(50).max()

    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_high, 4)

    ai_tp2 = round(
        recent_high + atr_value,
        4
    )

    ai_tp3 = round(
        recent_high + atr_value * 2,
        4
    )

    base_prob = min(
        round(confidence * 0.9),
        95
    )

    ai_prob1 = max(base_prob, 40)

    ai_prob2 = max(base_prob - 15, 25)

    ai_prob3 = max(base_prob - 30, 10)

elif scalp_signal == "SHORT":

    recent_low = df_15m["low"].tail(50).min()

    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_low, 4)

    ai_tp2 = round(
        recent_low - atr_value,
        4
    )

    ai_tp3 = round(
        recent_low - atr_value * 2,
        4
    )

    ai_probability = min(
        round(confidence * 0.8),
        95
    )

else:

    ai_tp1 = "-"
    ai_tp2 = "-"
    ai_tp3 = "-"
    ai_probability = "-"

# ==================================================
# SIGNAL COLOR
# ==================================================

if scalp_signal == "LONG":

    recent_high = df_15m["high"].tail(50).max()

    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_high, 4)

    ai_tp2 = round(
        recent_high + atr_value,
        4
    )

    ai_tp3 = round(
        recent_high + atr_value * 2,
        4
    )

    base_prob = min(
        round(confidence * 0.9),
        95
    )

    ai_prob1 = max(base_prob, 40)

    ai_prob2 = max(base_prob - 15, 25)

    ai_prob3 = max(base_prob - 30, 10)

elif scalp_signal == "SHORT":

    recent_low = df_15m["low"].tail(50).min()

    atr_value = df_15m["atr"].iloc[-1]

    ai_tp1 = round(recent_low, 4)

    ai_tp2 = round(
        recent_low - atr_value,
        4
    )

    ai_tp3 = round(
        recent_low - atr_value * 2,
        4
    )

    base_prob = min(
        round(confidence * 0.9),
        95
    )

    ai_prob1 = max(base_prob, 40)

    ai_prob2 = max(base_prob - 15, 25)

    ai_prob3 = max(base_prob - 30, 10)

else:

    ai_tp1 = "-"
    ai_tp2 = "-"
    ai_tp3 = "-"

    ai_prob1 = "-"
    ai_prob2 = "-"
    ai_prob3 = "-"

# ==================================================
# SIGNAL CARD
# ==================================================

st.markdown(f"""

<div class="card">

<div class="{signal_class}">
{scalp_signal}
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
🚀 TP1 (+1%) : {tp1}
</div>

<div class="info">
🚀 TP2 (+1.5%) : {tp2}
</div>

<div class="info">
🚀 TP3 (+2%) : {tp3}
</div>

<div class="info">
🤖 AI TP1 : {ai_tp1}
</div>

<div class="info">
🤖 AI TP2 : {ai_tp2}
</div>

<div class="info">
🤖 AI TP3 : {ai_tp3}
</div>

<div class="info">
🎯 AI 도달확률 : {ai_probability}%
</div>

<div class="info">
📈 신뢰도 : {confidence}/100
</div>

</div>

""", unsafe_allow_html=True)

# ==================================================
# MARKET STATUS
# ==================================================

st.markdown(f"""

<div class="card">

<div class="card-title">
📊 멀티 타임프레임 분석
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
거래량 : {volume_state}
</div>

</div>

""", unsafe_allow_html=True)

# ==================================================
# DIVERGENCE CARD
# ==================================================

st.markdown(f"""

<div class="card">

<div class="card-title">
⚡ RSI 다이버전스
</div>

<div class="box">
15분 : {div_15m}
</div>

<div class="box">
1시간 : {div_1h}
</div>

<div class="box">
4시간 : {div_4h}
</div>

</div>

""", unsafe_allow_html=True)

# ==================================================
# AI TARGET CARD
# ==================================================

st.markdown(f"""

<div class="card">

<div class="card-title">
🤖 AI 목표가 분석 (구조 + ATR)
</div>

<div class="box">
AI TP1 : {ai_tp1} <br>
도달확률 : {ai_prob1}%
</div>

<div class="box">
AI TP2 : {ai_tp2} <br>
도달확률 : {ai_prob2}%
</div>

<div class="box">
AI TP3 : {ai_tp3} <br>
도달확률 : {ai_prob3}%
</div>

</div>

""", unsafe_allow_html=True)

# ==================================================
# SCALPING STATUS
# ==================================================

st.markdown(f"""

<div class="card">

<div class="card-title">
⚡ 스캘핑 상태
</div>

<div class="box">
3분 RSI : {round(rsi_3m,2)}
</div>

<div class="box">
5분 RSI : {round(rsi_5m,2)}
</div>

<div class="box">
진입 상태 : {scalp_signal}
</div>

</div>

""", unsafe_allow_html=True)

# ==================================================
# CHART
# ==================================================

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.6,0.2,0.2]
)

# CANDLE

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
        name="EMA50"
    ),
    row=1,
    col=1
)

# VOLUME

fig.add_trace(
    go.Bar(
        x=df_15m["timestamp"],
        y=df_15m["volume"],
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
        name="RSI"
    ),
    row=3,
    col=1
)

fig.add_hline(
    y=70,
    row=3,
    col=1
)

fig.add_hline(
    y=30,
    row=3,
    col=1
)

fig.update_layout(

    template="plotly_dark",

    height=900,

    paper_bgcolor="#0F172A",

    plot_bgcolor="#0F172A",

    font=dict(
        color="white",
        size=14
    ),

    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# UPDATE TIME
# ==================================================

st.caption(
    f"업데이트 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
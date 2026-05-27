import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# =========================
# 페이지 설정
# =========================

st.set_page_config(
    page_title="TTF Crypto",
    layout="wide"
)

# =========================
# 모바일 UI CSS
# =========================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0E1117;
    color: white;
    font-family: sans-serif;
}

.block-container {
    padding-top: 1rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    padding-bottom: 1rem;
}

.title {
    text-align: center;
    font-size: 30px;
    font-weight: bold;
    color: #00FFAA;
    margin-bottom: 20px;
}

.card {
    background-color: #1B1F2A;
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 15px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.4);
}

.section {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 10px;
}

.long {
    color: #00FF88;
    font-size: 24px;
    font-weight: bold;
}

.short {
    color: #FF4B4B;
    font-size: 24px;
    font-weight: bold;
}

.neutral {
    color: #AAAAAA;
    font-size: 24px;
    font-weight: bold;
}

.info {
    font-size: 16px;
    margin-top: 5px;
}

@media (max-width: 768px) {

    .title {
        font-size: 22px;
    }

    .section {
        font-size: 18px;
    }

    .info {
        font-size: 14px;
    }

}

</style>
""", unsafe_allow_html=True)

# =========================
# 제목
# =========================

st.markdown(
    '<div class="title">📈 TTF Crypto Intelligence</div>',
    unsafe_allow_html=True
)

# =========================
# 거래소
# =========================

exchange = ccxt.binanceus()

# =========================
# 코인 선택
# =========================

symbol = st.radio(
    "코인 선택",
    ["BTC/USDT", "ETH/USDT", "XRP/USDT"],
    horizontal=True
)

# =========================
# 데이터 가져오기
# =========================

def get_data(timeframe):

    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=300
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume'
        ]
    )

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df

# =========================
# 지표 계산
# =========================

def calculate(df):

    ema20 = EMAIndicator(close=df['close'], window=20)
    ema50 = EMAIndicator(close=df['close'], window=50)

    rsi = RSIIndicator(close=df['close'], window=14)

    df['ema20'] = ema20.ema_indicator()
    df['ema50'] = ema50.ema_indicator()

    df['rsi'] = rsi.rsi()

    return df

# =========================
# 추세 판단
# =========================

def get_trend(df):

    price = df['close'].iloc[-1]
    ema20 = df['ema20'].iloc[-1]
    ema50 = df['ema50'].iloc[-1]

    if price > ema20 > ema50:
        return "LONG"

    elif price < ema20 < ema50:
        return "SHORT"

    else:
        return "NEUTRAL"

# =========================
# 다이버전스
# =========================

def detect_divergence(df):

    recent_price = df['close'].iloc[-5:]
    recent_rsi = df['rsi'].iloc[-5:]

    if recent_price.iloc[-1] < recent_price.iloc[0] and recent_rsi.iloc[-1] > recent_rsi.iloc[0]:
        return "Bullish Divergence"

    elif recent_price.iloc[-1] > recent_price.iloc[0] and recent_rsi.iloc[-1] < recent_rsi.iloc[0]:
        return "Bearish Divergence"

    else:
        return "No Divergence"

# =========================
# 데이터 로드
# =========================

df_15m = calculate(get_data("15m"))
df_1h = calculate(get_data("1h"))
df_4h = calculate(get_data("4h"))
df_1d = calculate(get_data("1d"))

# =========================
# 추세 분석
# =========================

trend_15m = get_trend(df_15m)
trend_1h = get_trend(df_1h)
trend_4h = get_trend(df_4h)

# =========================
# 메인 방향성
# =========================

if trend_4h == trend_1h:
    final_signal = trend_4h
else:
    final_signal = "NEUTRAL"

# =========================
# 진입 손절 익절
# =========================

current_price = round(df_15m['close'].iloc[-1], 2)

if final_signal == "LONG":

    entry = current_price
    stop = round(entry * 0.98, 2)
    target = round(entry * 1.04, 2)

    rr = round(
        (target - entry) / (entry - stop),
        2
    )

    probability = "HIGH"

elif final_signal == "SHORT":

    entry = current_price
    stop = round(entry * 1.02, 2)
    target = round(entry * 0.96, 2)

    rr = round(
        (entry - target) / (stop - entry),
        2
    )

    probability = "HIGH"

else:

    entry = "-"
    stop = "-"
    target = "-"
    rr = "-"
    probability = "LOW"

# =========================
# 다이버전스
# =========================

div_15m = detect_divergence(df_15m)
div_1h = detect_divergence(df_1h)
div_4h = detect_divergence(df_4h)
div_1d = detect_divergence(df_1d)

# =========================
# 시그널 색상
# =========================

if final_signal == "LONG":
    signal_class = "long"

elif final_signal == "SHORT":
    signal_class = "short"

else:
    signal_class = "neutral"

# =========================
# 메인 카드
# =========================

st.markdown(f"""
<div class="card">

<div class="{signal_class}">
{final_signal}
</div>

<div class="info">
💰 현재가: {current_price}
</div>

<div class="info">
🎯 진입가: {entry}
</div>

<div class="info">
🛑 손절가: {stop}
</div>

<div class="info">
🚀 목표가: {target}
</div>

<div class="info">
⚖ 손익비: {rr}
</div>

<div class="info">
📊 확률: {probability}
</div>

</div>
""", unsafe_allow_html=True)

# =========================
# 타임프레임 분석
# =========================

st.markdown("""
<div class="card">
<div class="section">
📡 멀티 타임프레임 분석
</div>
""", unsafe_allow_html=True)

st.write(f"15분봉: {trend_15m}")
st.write(f"1시간봉: {trend_1h}")
st.write(f"4시간봉: {trend_4h}")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 다이버전스 카드
# =========================

st.markdown("""
<div class="card">
<div class="section">
⚠ RSI 다이버전스
</div>
""", unsafe_allow_html=True)

st.write(f"15분봉: {div_15m}")
st.write(f"1시간봉: {div_1h}")
st.write(f"4시간봉: {div_4h}")
st.write(f"일봉: {div_1d}")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 차트
# =========================

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.6, 0.2, 0.2]
)

# 캔들

fig.add_trace(
    go.Candlestick(
        x=df_15m['timestamp'],
        open=df_15m['open'],
        high=df_15m['high'],
        low=df_15m['low'],
        close=df_15m['close'],
        name='Price'
    ),
    row=1,
    col=1
)

# EMA20

fig.add_trace(
    go.Scatter(
        x=df_15m['timestamp'],
        y=df_15m['ema20'],
        name='EMA20'
    ),
    row=1,
    col=1
)

# EMA50

fig.add_trace(
    go.Scatter(
        x=df_15m['timestamp'],
        y=df_15m['ema50'],
        name='EMA50'
    ),
    row=1,
    col=1
)

# 거래량

fig.add_trace(
    go.Bar(
        x=df_15m['timestamp'],
        y=df_15m['volume'],
        name='Volume'
    ),
    row=2,
    col=1
)

# RSI

fig.add_trace(
    go.Scatter(
        x=df_15m['timestamp'],
        y=df_15m['rsi'],
        name='RSI'
    ),
    row=3,
    col=1
)

fig.update_layout(
    template="plotly_dark",
    height=700,
    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================
# 마지막 업데이트
# =========================

st.caption(
    f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
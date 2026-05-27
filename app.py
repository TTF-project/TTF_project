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
# 모바일 최적화 CSS
# =========================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0E1117;
    color: #FFFFFF;
    font-family: sans-serif;
}

/* 전체 여백 */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
}

/* 제목 */
.main-title {
    font-size: 34px;
    font-weight: bold;
    text-align: center;
    color: #00FFAA;
    margin-bottom: 20px;
}

/* 카드 */
.card {
    background-color: #1B1F2A;
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 15px;
    border: 1px solid #2A2F3A;
}

/* 섹션 */
.section-title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 12px;
    color: white;
}

/* LONG */
.long {
    color: #00FF88;
    font-size: 30px;
    font-weight: bold;
}

/* SHORT */
.short {
    color: #FF4B4B;
    font-size: 30px;
    font-weight: bold;
}

/* NEUTRAL */
.neutral {
    color: #AAAAAA;
    font-size: 30px;
    font-weight: bold;
}

/* 정보 텍스트 */
.info {
    font-size: 18px;
    color: #FFFFFF;
    margin-top: 10px;
    font-weight: 500;
}

/* 다이버전스 */
.div-box {
    background-color: #252A36;
    padding: 12px;
    border-radius: 12px;
    margin-top: 8px;
    font-size: 16px;
}

/* 모바일 */
@media (max-width: 768px) {

    .main-title {
        font-size: 24px;
    }

    .section-title {
        font-size: 18px;
    }

    .info {
        font-size: 16px;
    }

    .long, .short, .neutral {
        font-size: 24px;
    }

}

</style>
""", unsafe_allow_html=True)

# =========================
# 제목
# =========================

st.markdown(
    '<div class="main-title">📈 TTF Crypto Intelligence</div>',
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

    ema20 = EMAIndicator(
        close=df['close'],
        window=20
    )

    ema50 = EMAIndicator(
        close=df['close'],
        window=50
    )

    rsi = RSIIndicator(
        close=df['close'],
        window=14
    )

    df['ema20'] = ema20.ema_indicator()
    df['ema50'] = ema50.ema_indicator()

    df['rsi'] = rsi.rsi()

    return df

# =========================
# 추세 분석
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

# =========================
# 데이터 로드
# =========================

df_15m = calculate(get_data("15m"))
df_1h = calculate(get_data("1h"))
df_4h = calculate(get_data("4h"))
df_1d = calculate(get_data("1d"))

# =========================
# 추세
# =========================

trend_15m = get_trend(df_15m)
trend_1h = get_trend(df_1h)
trend_4h = get_trend(df_4h)

# =========================
# 최종 시그널
# =========================

if trend_4h == trend_1h:

    final_signal = trend_4h

else:

    final_signal = "NEUTRAL"

# =========================
# 현재가
# =========================

current_price = round(
    df_15m['close'].iloc[-1],
    2
)

# =========================
# 진입 / 손절 / 목표
# =========================

if final_signal == "LONG":

    entry = current_price
    stop = round(entry * 0.98, 2)
    target = round(entry * 1.04, 2)

    rr = round(
        (target - entry) /
        (entry - stop),
        2
    )

    probability = "높음"

elif final_signal == "SHORT":

    entry = current_price
    stop = round(entry * 1.02, 2)
    target = round(entry * 0.96, 2)

    rr = round(
        (entry - target) /
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

# =========================
# 색상 클래스
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
📊 전략 신뢰도: {probability}
</div>

</div>
""", unsafe_allow_html=True)

# =========================
# 멀티 타임프레임
# =========================

st.markdown("""
<div class="card">

<div class="section-title">
📡 멀티 타임프레임
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="info">15분봉: {trend_15m}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="info">1시간봉: {trend_1h}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="info">4시간봉: {trend_4h}</div>',
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 다이버전스
# =========================

st.markdown("""
<div class="card">

<div class="section-title">
⚠ RSI 다이버전스
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="div-box">15분봉: {detect_divergence(df_15m)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">1시간봉: {detect_divergence(df_1h)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">4시간봉: {detect_divergence(df_4h)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="div-box">일봉: {detect_divergence(df_1d)}</div>',
    unsafe_allow_html=True
)

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
    height=750,
    xaxis_rangeslider_visible=False,
    font=dict(
        size=15,
        color="white"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================
# 마지막 업데이트
# =========================

st.caption(
    f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
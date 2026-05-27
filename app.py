import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go

# ==================================================
# 기본 설정
# ==================================================
st.set_page_config(
    page_title="TTF Crypto Intelligence",
    layout="wide"
)

# ==================================================
# 스타일
# ==================================================
st.markdown("""
<style>

.stApp {
    background-color: #f4f7fb;
}

h1,h2,h3,h4 {
    color: #111827;
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.08);
}

.green {
    color: #16a34a;
    font-weight: bold;
}

.red {
    color: #dc2626;
    font-weight: bold;
}

.yellow {
    color: #ca8a04;
    font-weight: bold;
}

.signal-long {
    background-color: #dcfce7;
    color: #166534;
    padding: 15px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

.signal-short {
    background-color: #fee2e2;
    color: #991b1b;
    padding: 15px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

.signal-wait {
    background-color: #fef9c3;
    color: #854d0e;
    padding: 15px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# 제목
# ==================================================
st.title("TTF 암호화폐 분석 시스템")

# ==================================================
# 거래소
# ==================================================
exchange = ccxt.binance()

symbols = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "XRP": "XRP/USDT"
}

coin = st.selectbox(
    "코인 선택",
    list(symbols.keys())
)

symbol = symbols[coin]

# ==================================================
# 데이터 가져오기 함수
# ==================================================
def get_data(timeframe):

    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=300
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()

    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()

    rs = gain / loss

    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# ==================================================
# 추세 분석
# ==================================================
def trend_analysis(df):

    latest = df.iloc[-1]

    ema20 = latest["ema20"]
    ema50 = latest["ema50"]
    rsi = latest["rsi"]

    score = 0

    if ema20 > ema50:
        score += 1
    else:
        score -= 1

    if rsi > 55:
        score += 1
    elif rsi < 45:
        score -= 1

    if score >= 2:
        return "상승", "green"

    elif score <= -2:
        return "하락", "red"

    else:
        return "횡보", "yellow"

# ==================================================
# 다이버전스 감지
# ==================================================
def detect_divergence(df):

    recent_price = df["close"].iloc[-5:]
    recent_rsi = df["rsi"].iloc[-5:]

    price_high = recent_price.iloc[-1] > recent_price.max()

    rsi_lower = recent_rsi.iloc[-1] < recent_rsi.max()

    price_low = recent_price.iloc[-1] < recent_price.min()

    rsi_higher = recent_rsi.iloc[-1] > recent_rsi.min()

    if price_high and rsi_lower:
        return "Bearish Divergence"

    elif price_low and rsi_higher:
        return "Bullish Divergence"

    else:
        return "없음"

# ==================================================
# 데이터
# ==================================================
df_15m = get_data("15m")
df_1h = get_data("1h")
df_4h = get_data("4h")
df_1d = get_data("1d")

# ==================================================
# 추세
# ==================================================
trend_15m, color_15m = trend_analysis(df_15m)
trend_1h, color_1h = trend_analysis(df_1h)
trend_4h, color_4h = trend_analysis(df_4h)

# ==================================================
# 다이버전스
# ==================================================
div_15m = detect_divergence(df_15m)
div_1h = detect_divergence(df_1h)
div_4h = detect_divergence(df_4h)
div_1d = detect_divergence(df_1d)

# ==================================================
# 현재 가격
# ==================================================
price = df_15m["close"].iloc[-1]

# ==================================================
# 전략 판단
# ==================================================
if trend_4h == "상승" and trend_1h == "상승":

    signal = "LONG"

    signal_class = "signal-long"

    entry = price
    stop = price * 0.97
    target = price * 1.06

elif trend_4h == "하락" and trend_1h == "하락":

    signal = "SHORT"

    signal_class = "signal-short"

    entry = price
    stop = price * 1.03
    target = price * 0.94

else:

    signal = "WAIT"

    signal_class = "signal-wait"

    entry = price
    stop = price * 0.98
    target = price * 1.02

# ==================================================
# 손익비
# ==================================================
rr = abs(target - entry) / abs(entry - stop)

# ==================================================
# 상단 카드
# ==================================================
col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(f"""
    <div class='card'>
    <h3>현재 가격</h3>
    <h2>{price:.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:

    st.markdown(f"""
    <div class='card'>
    <h3>4H 방향</h3>
    <h2 class='{color_4h}'>{trend_4h}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:

    st.markdown(f"""
    <div class='card'>
    <h3>1H 상태</h3>
    <h2 class='{color_1h}'>{trend_1h}</h2>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# 시그널
# ==================================================
st.markdown(f"""
<div class='{signal_class}'>
{signal} SIGNAL
</div>
""", unsafe_allow_html=True)

# ==================================================
# 차트
# ==================================================
st.subheader("15분봉 캔들차트")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df_15m.index,
    open=df_15m["open"],
    high=df_15m["high"],
    low=df_15m["low"],
    close=df_15m["close"],
    name="Price"
))

fig.add_trace(go.Scatter(
    x=df_15m.index,
    y=df_15m["ema20"],
    name="EMA20"
))

fig.add_trace(go.Scatter(
    x=df_15m.index,
    y=df_15m["ema50"],
    name="EMA50"
))

fig.update_layout(
    template="plotly_white",
    height=600,
    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# 다이버전스
# ==================================================
st.subheader("다이버전스 현황")

st.write("Daily :", div_1d)
st.write("4H :", div_4h)
st.write("1H :", div_1h)
st.write("15M :", div_15m)

# ==================================================
# 전략
# ==================================================
st.subheader("매매 전략")

col4, col5 = st.columns(2)

with col4:

    st.markdown(f"""
    <div class='card'>
    <h3>진입가</h3>
    <p>{entry:.2f}</p>

    <h3>손절가</h3>
    <p>{stop:.2f}</p>

    <h3>익절가</h3>
    <p>{target:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

with col5:

    st.markdown(f"""
    <div class='card'>
    <h3>손익비</h3>
    <p>{rr:.2f}</p>

    <h3>15M 추세</h3>
    <p>{trend_15m}</p>

    <h3>1H 추세</h3>
    <p>{trend_1h}</p>

    <h3>4H 추세</h3>
    <p>{trend_4h}</p>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# RSI
# ==================================================
st.subheader("RSI")

st.line_chart(
    df_15m["rsi"]
)

# ==================================================
# 거래량
# ==================================================
st.subheader("거래량")

st.bar_chart(
    df_15m["volume"]
)

# ==================================================
# AI 코멘트
# ==================================================
st.subheader("AI 시장 코멘트")

comments = []

if trend_4h == "상승":
    comments.append(
        "4시간봉 기준 상승 우세입니다."
    )

if trend_4h == "하락":
    comments.append(
        "4시간봉 기준 하락 우세입니다."
    )

if div_1h != "없음":
    comments.append(
        f"1시간봉에서 {div_1h} 감지."
    )

if div_15m != "없음":
    comments.append(
        f"15분봉에서 {div_15m} 감지."
    )

for c in comments:
    st.write("-", c)

st.caption(
    "TTF Crypto Intelligence V6"
)
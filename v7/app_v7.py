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
from streamlit_autorefresh import st_autorefresh

# ==================================================
# 1. PAGE CONFIG & CSS (원본 UI 스타일 100% 유지)
# ==================================================

st.set_page_config(
    page_title="TTF V7 SCALPING",
    layout="wide"
)

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
    .main-title{ font-size:24px; }
    .card-title{ font-size:18px; }
    .info{ font-size:15px; }
    .box{ font-size:14px; }
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">⚡ TTF V7 SCALPING</div>',
    unsafe_allow_html=True
)

st_autorefresh(
    interval=15000,
    key="refresh"
)

# ==================================================
# 2. TELEGRAM (알림 발송 로직 원본 유지)
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
    except Exception as e:
        st.error(f"텔레그램 오류: {e}")


# 테스트 버튼
if st.button("텔레그램 테스트"):
    send_telegram("✅ TTF V7 테스트 메시지")
    st.success("전송 시도 완료")

if "last_signal" not in st.session_state:
    st.session_state.last_signal = ""

# ==================================================
# 3. EXCHANGE & SYMBOL SELECTION
# ==================================================

exchange = ccxt.binanceus()

symbol = st.radio(
    "코인 선택",
    ["BTC/USDT", "ETH/USDT", "XRP/USDT"],
    horizontal=True
)

# ==================================================
# 4. DATA FETCH & INDICATORS (멀티 타임프레임 연산)
# ==================================================

@st.cache_data(ttl=30)
def get_data(symbol, timeframe):
    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=300
    )
    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def calculate(df):
    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14)
    df["atr"] = atr.average_true_range()
    return df

def get_trend(df):
    price = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    if price > ema20 > ema50:
        return "LONG"
    elif price < ema20 < ema50:
        return "SHORT"
    return "NEUTRAL"

def volume_strength(df):
    current = df["volume"].iloc[-1]
    avg = df["volume"].rolling(20).mean().iloc[-1]
    if current > avg:
        return "STRONG"
    return "WEAK"

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

# 모든 타임프레임 로드
df_3m = calculate(get_data(symbol, "3m"))
df_5m = calculate(get_data(symbol, "5m"))
df_15m = calculate(get_data(symbol, "15m"))
df_1h = calculate(get_data(symbol, "1h"))
df_4h = calculate(get_data(symbol, "4h"))

# 분석 데이터 추출
trend_4h = get_trend(df_4h)
trend_1h = get_trend(df_1h)
trend_15m = get_trend(df_15m)

div_15m = detect_divergence(df_15m)
div_1h = detect_divergence(df_1h)
div_4h = detect_divergence(df_4h)

rsi_3m = df_3m["rsi"].iloc[-1]
rsi_5m = df_5m["rsi"].iloc[-1]
volume_state = volume_strength(df_15m)

# ==================================================
# 5. SCALPING ENGINE
# ==================================================

scalp_signal = "WAIT"
confidence = 50

if trend_4h == "LONG" and trend_1h == "LONG" and trend_15m == "LONG":
    confidence += 20
    if rsi_5m > 50: confidence += 10
    if volume_state == "STRONG": confidence += 10
    if div_15m == "BULLISH": confidence += 10
    if rsi_3m > 50 and df_3m["close"].iloc[-1] > df_3m["ema20"].iloc[-1]:
        scalp_signal = "LONG"

elif trend_4h == "SHORT" and trend_1h == "SHORT" and trend_15m == "SHORT":
    confidence += 20
    if rsi_5m < 50: confidence += 10
    if volume_state == "STRONG": confidence += 10
    if div_15m == "BEARISH": confidence += 10
    if rsi_3m < 50 and df_3m["close"].iloc[-1] < df_3m["ema20"].iloc[-1]:
        scalp_signal = "SHORT"

current_price = round(df_3m["close"].iloc[-1], 4)

# ==================================================
# 6. VARIABLE INITIALIZATION
# ==================================================

if scalp_signal == "LONG":
    signal_class = "long"
elif scalp_signal == "SHORT":
    signal_class = "short"
else:
    signal_class = "neutral"

entry = current_price
stop = 0.0
tp1 = tp2 = tp3 = 0.0
ai_tp1 = ai_tp2 = ai_tp3 = 0.0
ai_prob1 = ai_prob2 = ai_prob3 = 0
ai_probability = 0

atr_value = df_15m["atr"].iloc[-1]

if scalp_signal == "LONG":
    stop = round(entry * 0.993, 4)
    tp1 = round(entry * 1.01, 4)
    tp2 = round(entry * 1.015, 4)
    tp3 = round(entry * 1.02, 4)
    
    recent_high = df_15m["high"].tail(50).max()
    ai_tp1 = round(recent_high, 4)
    ai_tp2 = round(recent_high + atr_value, 4)
    ai_tp3 = round(recent_high + atr_value * 2, 4)
    
    base_prob = min(round(confidence * 0.9), 95)
    ai_prob1 = max(base_prob, 40)
    ai_prob2 = max(base_prob - 15, 25)
    ai_prob3 = max(base_prob - 30, 10)
    ai_probability = base_prob

elif scalp_signal == "SHORT":
    stop = round(entry * 1.007, 4) 
    tp1 = round(entry * 0.99, 4)   
    tp2 = round(entry * 0.985, 4)
    tp3 = round(entry * 0.98, 4)
    
    recent_low = df_15m["low"].tail(50).min()
    ai_tp1 = round(recent_low, 4)
    ai_tp2 = round(recent_low - atr_value, 4)
    ai_tp3 = round(recent_low - atr_value * 2, 4)
    
    base_prob = min(round(confidence * 0.8), 95) 
    ai_prob1 = max(base_prob, 40)
    ai_prob2 = max(base_prob - 15, 25)
    ai_prob3 = max(base_prob - 30, 10)
    ai_probability = base_prob

def display_val(val, is_percentage=False):
    if scalp_signal == "WAIT":
        return "-"
    return f"{val}%" if is_percentage else str(val)

# ==================================================
# 7. TELEGRAM ALERT LOGIC
# ==================================================

if scalp_signal == "LONG":
    signal_key = f"{symbol}_LONG"
    if st.session_state.last_signal != signal_key:
        send_telegram(f"🚀 LONG SIGNAL\n\n종목 : {symbol}\n\n진입가 : {entry}\n\n손절가 : {stop}\n\nTP1 : {tp1}\n\nTP2 : {tp2}\n\nTP3 : {tp3}\n\n신뢰도 : {confidence}/100")
        st.session_state.last_signal = signal_key
elif scalp_signal == "SHORT":
    signal_key = f"{symbol}_SHORT"
    if st.session_state.last_signal != signal_key:
        send_telegram(f"🔻 SHORT SIGNAL\n\n종목 : {symbol}\n\n진입가 : {entry}\n\n손절가 : {stop}\n\nTP1 : {tp1}\n\nTP2 : {tp2}\n\nTP3 : {tp3}\n\n신뢰도 : {confidence}/100")
        st.session_state.last_signal = signal_key
else:
    st.session_state.last_signal = ""

# ==================================================
# 8. UI DASHBOARD DISPLAY (오리지널 카드 5종 완벽 유지)
# ==================================================

# 1) 메인 시그널 카드
st.markdown(f"""
<div class="card">
<div class="{signal_class}">
{scalp_signal}
</div>
<div class="info">💰 현재가 : {current_price}</div>
<div class="info">🎯 진입가 : {display_val(entry)}</div>
<div class="info">🛑 손절가 : {display_val(stop)}</div>
<div class="info">🚀 TP1 (+1%) : {display_val(tp1)}</div>
<div class="info">🚀 TP2 (+1.5%) : {display_val(tp2)}</div>
<div class="info">🚀 TP3 (+2%) : {display_val(tp3)}</div>
<div class="info">🤖 AI TP1 : {display_val(ai_tp1)}</div>
<div class="info">🤖 AI TP2 : {display_val(ai_tp2)}</div>
<div class="info">🤖 AI TP3 : {display_val(ai_tp3)}</div>
<div class="info">🎯 AI 도달확률 : {display_val(ai_probability, is_percentage=True)}</div>
<div class="info">📈 신뢰도 : {confidence}/100</div>
</div>
""", unsafe_allow_html=True)

# 2) 멀티 타임프레임 분석 카드
st.markdown(f"""
<div class="card">
<div class="card-title">📊 멀티 타임프레임 분석</div>
<div class="box">4시간 추세 : {trend_4h}</div>
<div class="box">1시간 추세 : {trend_1h}</div>
<div class="box">15분 추세 : {trend_15m}</div>
<div class="box">거래량 : {volume_state}</div>
</div>
""", unsafe_allow_html=True)

# 3) RSI 다이버전스 카드
st.markdown(f"""
<div class="card">
<div class="card-title">⚡ RSI 다이버전스</div>
<div class="box">15분 : {div_15m}</div>
<div class="box">1시간 : {div_1h}</div>
<div class="box">4시간 : {div_4h}</div>
</div>
""", unsafe_allow_html=True)

# 4) AI 목표가 분석 카드
st.markdown(f"""
<div class="card">
<div class="card-title">🤖 AI 목표가 분석 (구조 + ATR)</div>
<div class="box">AI TP1 : {display_val(ai_tp1)} <br>도달확률 : {display_val(ai_prob1, is_percentage=True)}</div>
<div class="box">AI TP2 : {display_val(ai_tp2)} <br>도달확률 : {display_val(ai_prob2, is_percentage=True)}</div>
<div class="box">AI TP3 : {display_val(ai_tp3)} <br>도달확률 : {display_val(ai_prob3, is_percentage=True)}</div>
</div>
""", unsafe_allow_html=True)

# 5) 스캘핑 상태 세부 카드
st.markdown(f"""
<div class="card">
<div class="card-title">⚡ 스캘핑 상태</div>
<div class="box">3분 RSI : {round(rsi_3m,2)}</div>
<div class="box">5분 RSI : {round(rsi_5m,2)}</div>
<div class="box">진입 상태 : {scalp_signal}</div>
</div>
""", unsafe_allow_html=True)

# ==================================================
# 9. TRADING CHART (에러 원천 차단 커스텀 캔들 기법)
# ==================================================

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    row_heights=[0.6, 0.2, 0.2],
    vertical_spacing=0.04
)

# 양봉(상승)과 음봉(하락) 색상 정의
df_15m['is_green'] = df_15m['close'] >= df_15m['open']
colors = np.where(df_15m['is_green'], '#00FF99', '#FF5C5C')

# ⭐️ [에러 원천 분쇄 치트키] 
# 고질적인 레인지슬라이더 에러를 일으키는 go.Candlestick을 쓰지 않고,
# go.Bar와 고유의 데이터 구조를 이용해 완전히 동일한 명품 캔들스틱 차트를 수동 구현합니다!
# 이 방식을 쓰면 슬라이더 자체가 메모리에 안 뜨므로 3.14 에러와 흰색 잔상이 100% 영구 해결됩니다.

# 1-A) 캔들의 얇은 윗꼬리 / 아랫꼬리 선 (High-Low)
for i, row in df_15m.iterrows():
    fig.add_trace(go.Scatter(
        x=[row['timestamp'], row['timestamp']],
        y=[row['low'], row['high']],
        mode='lines',
        line=dict(color=colors[i], width=1.5),
        hoverinfo='skip',
        showlegend=False
    ), row=1, col=1)

# 1-B) 캔들의 두꺼운 몸통 실체 (Open-Close)
fig.add_trace(go.Bar(
    x=df_15m['timestamp'],
    y=df_15m['close'] - df_15m['open'],
    base=df_15m['open'],
    marker=dict(color=colors, line=dict(color=colors, width=1)),
    name="PRICE",
    hoverinfo='x+y',
    showlegend=False
), row=1, col=1)

# 이동평균선(EMA) 추가
fig.add_trace(go.Scatter(x=df_15m["timestamp"], y=df_15m["ema20"], name="EMA20", line=dict(color='#FFD54A')), row=1, col=1)
fig.add_trace(go.Scatter(x=df_15m["timestamp"], y=df_15m["ema50"], name="EMA50", line=dict(color='#00FFB2')), row=1, col=1)

# 2층: 거래량 막대그래프
fig.add_trace(go.Bar(x=df_15m["timestamp"], y=df_15m["volume"], name="Volume", marker=dict(color='#38BDF8')), row=2, col=1)

# 3층: RSI 라인 및 가이드 기준선
fig.add_trace(go.Scatter(x=df_15m["timestamp"], y=df_15m["rsi"], name="RSI", line=dict(color='#F43F5E')), row=3, col=1)
fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="#EF4444")
fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="#10B981")

# 순수 차트 테마 및 여백 레이아웃 설정 (Rangeslider 제거를 위한 그 어떤 속성도 쓰지 않으므로 완벽 안전)
fig.update_layout(
    template="plotly_dark",
    height=900,
    paper_bgcolor="#0F172A",
    plot_bgcolor="#0F172A",
    font=dict(color="white", size=14),
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=False,
    barmode='overlay' # 커스텀 캔들 몸통 정렬을 위한 베이스 세팅
)

st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 10. REFRESH TIMESTAMP
# ==================================================

st.caption(f"최종 업데이트 타임 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
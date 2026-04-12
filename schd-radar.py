import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="SCHD Investing RADAR", layout="wide")

# 2. 프리미엄 CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }

/* 텍스트 가시성 보장 */
h1, h2, h3, h4, p, span, label { color: inherit !important; }

.main-card {
    padding: 40px; border-radius: 35px; text-align: center;
    background: linear-gradient(145deg, rgba(120, 120, 120, 0.1), rgba(0, 0, 0, 0.05));
    border: 1px solid rgba(128, 128, 128, 0.2); box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    margin-bottom: 35px;
}
.score-value { font-size: 5.5rem; font-weight: 800; color: var(--score-color); line-height: 1; }
.status-badge {
    font-size: 1.3rem; font-weight: 700; color: var(--score-color);
    background: rgba(128, 128, 128, 0.1); padding: 10px 25px; border-radius: 50px;
    display: inline-block; margin-top: 15px; border: 1.5px solid var(--score-color);
}
.section-header {
    font-size: 1.6rem; font-weight: 800; margin: 55px 0 25px 0;
    padding-left: 15px; border-left: 6px solid #1DB954;
}
.guide-box { padding: 30px; border-radius: 25px; background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.1); }
.logic-card { background: rgba(29, 185, 84, 0.1); padding: 20px; border-radius: 15px; margin-top: 20px; border-left: 5px solid #1DB954; }
.meta-info { font-size: 0.85rem; opacity: 0.6; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 엔진
@st.cache_data(ttl=3600)
def load_pro_data(ticker_symbol):
    tk = yf.Ticker(ticker_symbol)
    hist = tk.history(period="max")
    try:
        live_price = tk.basic_info['lastPrice']
        if live_price:
            hist.iloc[-1, hist.columns.get_loc('Close')] = live_price
    except:
        pass
    divs = tk.dividends.to_frame(name='div_amt')
    divs['ttm_sum'] = divs['div_amt'].rolling(window=4).sum()
    df = pd.merge_asof(hist.sort_index(), divs[['ttm_sum']].sort_index(), 
                       left_index=True, right_index=True, direction='backward')
    df['yield'] = (df['ttm_sum'] / df['Close']) * 100
    return df[df.index >= (df.index[0] + pd.DateOffset(years=1))].dropna().copy()

# 사이드바 제거 및 종목 하드코딩
selected_ticker = "SCHD"
df = load_pro_data(selected_ticker)

# 4. 통계 로직 산출
curr_y = df['yield'].iloc[-1]
curr_p = df['Close'].iloc[-1]
today_str = datetime.now().strftime('%Y-%m-%d')
ref_date = df.index[-1].strftime('%Y-%m-%d')

cheaper_days_pct = (df['yield'] > curr_y).mean() * 100
buy_score = 100 - cheaper_days_pct

if buy_score >= 90: status, color, emoji = "전설의 꿀통 매수", "#B8860B", "🍯"
elif buy_score >= 70: status, color, emoji = "맛도리 적립 구간", "#00C853", "😋"
elif buy_score >= 40: status, color, emoji = "합리적 정가 매수", "#F9A825", "⚖️"
else: status, color, emoji = "고평가 주의 / 관망", "#D50000", "🚨"

# --- 구간별 동적 판독 텍스트 생성 ---
if buy_score >= 70:
    guide_title = "📉 압도적 가격 매력 구간 (할인 상태)"
    guide_text = f"상장 이후 지금까지 과거의 모든 영업일과 비교했을 때, <b>역사상 단 {cheaper_days_pct:.1f}%의 날들만이 오늘보다 배당수익률이 더 높았습니다.</b><br>즉, 현재 가격은 과거 데이터 기준 <b>상위 {cheaper_days_pct:.1f}% 수준의 압도적인 가격 매력</b>을 가지고 있음을 통계가 증명합니다."
    logic_color = "#1DB954"
elif buy_score >= 40:
    guide_title = "⚖️ 적정 가치 구간 (평균 수준)"
    guide_text = f"현재 배당수익률은 역사적 평균에 수렴하는 <b>적정 수준</b>입니다.<br>상장 이후 지금까지 <b>오늘보다 배당수익률이 더 높았던(더 저렴했던) 날들은 {cheaper_days_pct:.1f}%</b> 였습니다. 무리한 비중 확대보다는 분할 매수로 접근하기 좋은 구간입니다."
    logic_color = "#F9A825"
else:
    guide_title = "🚨 배당 매력 저하 구간 (고평가 주의)"
    guide_text = f"현재 가격은 배당수익률 관점에서 <b>매력이 떨어지는 고평가 구간</b>입니다.<br>과거 데이터를 보면, <b>오늘보다 배당수익률이 더 높았던(더 저렴했던) 날들이 무려 {cheaper_days_pct:.1f}% 나 있었습니다.</b> 추가 매수보다는 관망하며 더 나은 기회를 기다리는 것을 권장합니다."
    logic_color = "#D50000"

# --- 화면 렌더링 ---
st.markdown("<h1>📊 SCHD 배당수익률 RADAR</h1>", unsafe_allow_html=True)
st.markdown("<p style='opacity:0.7; margin-bottom:40px;'>SCHD-investing.besmelt.com | SCHD 역대 배당수익률 데이터 제련으로 포착한 매수의 꿀타임 찾기 사이트</p>", unsafe_allow_html=True)

# [Main Summary Card]
st.markdown(f"""
<div class="main-card" style="--score-color: {color};">
    <p style="letter-spacing: 2px; font-weight: 600; font-size: 0.9rem; opacity: 0.8;">{selected_ticker} 매수 매력 점수</p>
    <div class="score-value">{int(buy_score)}<span style="font-size:1.5rem; opacity:0.5;"> / 100</span></div>
    <div class="status-badge">{emoji} {status}</div>
    <div style="display: flex; justify-content: space-around; margin-top: 40px; background: rgba(128,128,128,0.08); padding: 25px; border-radius: 25px;">
        <div><p style="margin:0; opacity:0.6; font-size:0.85rem;">현재가</p><b style="font-size:1.7rem;">${curr_p:.2f}</b></div>
        <div><p style="margin:0; opacity:0.6; font-size:0.85rem;">배당률</p><b style="font-size:1.7rem;">{curr_y:.2f}%</b></div>
    </div>
    <div class="meta-info">
        조회일: {today_str} | 데이터 기준: {ref_date} | 갱신 간격: 1시간
    </div>
</div>
""", unsafe_allow_html=True)

# [AI 판독 가이드]
st.markdown("<div class='section-header'>💡 배당수익률 점수 판독 가이드</div>", unsafe_allow_html=True)

guide_html = f"""
<div class="guide-box">
<p style="font-size: 1.1rem; font-weight: 700; margin-bottom: 15px;">"왜 배당수익률로 지금이 싼지 비싼지 아는 건가요?"</p>
<p style="font-size: 0.95rem; opacity: 0.8; line-height: 1.8;">
배당금은 기업이 우리에게 나누어주는 '확실한 현금'입니다. SCHD처럼 매년 배당금을 꾸준히 올려주는 우량 ETF는, 주가가 떨어질 때마다 내가 챙길 수 있는 <b>'배당수익률(배당금 ÷ 주가)'</b>이 반대로 껑충 뜁니다.<br>
즉, 현재 배당수익률이 과거 평균보다 유독 높다면? 지금이 바로 우량 자산이 바겐세일 중인 '저렴한 구간'이라는 뜻이죠.
</p>
<div class="logic-card" style="background: {logic_color}15; border-left: 5px solid {logic_color};">
<p style="font-size: 1.1rem; font-weight: 800; color: {logic_color} !important; margin-bottom: 10px;">{guide_title}</p>
<p style="font-size: 1rem; opacity: 0.9; line-height: 1.7;">
{guide_text}
</p>
</div>
<div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin: 30px 0 5px 0;">
<div style="width: 40%; background: #D50000;"></div>
<div style="width: 30%; background: #F9A825;"></div>
<div style="width: 20%; background: #00C853;"></div>
<div style="width: 10%; background: #B8860B;"></div>
</div>
<div style="display: flex; text-align: center; font-size: 0.75rem; color: #888; font-weight: 600;">
<div style="width: 40%;">주의(0-40)</div>
<div style="width: 30%;">정가(40-70)</div>
<div style="width: 20%;">맛도리(70-90)</div>
<div style="width: 10%; white-space: nowrap;">꿀통(90-100)</div>
</div>
</div>
"""
st.markdown(guide_html, unsafe_allow_html=True)

# [Histogram Chart]
st.markdown("<div class='section-header'>📊 역사상 총 배당수익률 히스토그램</div>", unsafe_allow_html=True)
fig_hist = px.histogram(df, x="yield")
fig_hist.update_traces(xbins=dict(size=0.01), marker_line_width=0.5)

fig_hist.update_layout(
    xaxis_title="<b>배당수익률 (%)</b>",
    yaxis_title="<b>과거 거래일 수 (Days)</b>",
    height=420, 
    margin=dict(l=0, r=0, t=70, b=0)
)
fig_hist.update_xaxes(dtick=0.1, tickformat=".1f")
fig_hist.add_vline(x=curr_y, line_width=3, line_dash="dash", line_color="#D50000")

# 마커 추가
fig_hist.add_annotation(
    x=curr_y,
    y=1.0,
    yref="paper",
    text="<b>📍 현재 위치<br><span style='font-size:11px;'>(We are here!)</span></b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#D50000",
    ax=0,
    ay=-45,
    font=dict(size=14, color="white"),
    bgcolor="#D50000",
    borderpad=6,
    bordercolor="white",
    borderwidth=2,
    opacity=0.95
)
st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

# [Timeline Chart]
st.markdown("<div class='section-header'>📈 배당수익률 및 주가 시계열 그래프</div>", unsafe_allow_html=True)
fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
fig_dual.add_trace(go.Scatter(x=df.index, y=df['yield'], name="배당수익률", line=dict(color="#00C853", width=2.5)), secondary_y=False)
fig_dual.add_trace(go.Scatter(x=df.index, y=df['Close'], name="주가 ($)", line=dict(color="#FF69B4", width=1.5, dash='dot'), opacity=0.4), secondary_y=True)
fig_dual.update_layout(height=450, hovermode="x unified", margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.1, x=1))
fig_dual.update_yaxes(secondary_y=True, showgrid=False)
st.plotly_chart(fig_dual, use_container_width=True, config={'displayModeBar': False})

# [Legal Disclaimer]
st.markdown("<div class='section-header'>⚠️ 면책 조항</div>", unsafe_allow_html=True)
st.markdown("""
<div style="padding: 20px; border-radius: 15px; background: rgba(213, 0, 0, 0.05); border: 1px solid rgba(213, 0, 0, 0.1); font-size: 0.8rem; opacity: 0.8;">
본 서비스는 통계 참고용이며 투자 권유가 아닙니다. 모든 투자의 결과는 투자자 본인에게 책임이 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br><p style='text-align:center; color:gray; font-size:0.75rem; padding-bottom:50px;'>© Besmelt | SCHD investing Radar </p>", unsafe_allow_html=True)
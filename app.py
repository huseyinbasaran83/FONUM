import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Reel Portföy", layout="wide")

# --- 1. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), 
                           end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

def get_inflation_factor(start_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    months_diff = (datetime.now().year - start_date.year) * 12 + (datetime.now().month - start_date.month)
    monthly_rate = 0.042 
    return (1 + monthly_rate) ** max(0, months_diff)

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("💾 Veri Yönetimi")
    if st.session_state.portfolio:
        json_save = []
        for item in st.session_state.portfolio:
            temp = item.copy()
            if hasattr(temp['tarih'], 'strftime'): temp['tarih'] = temp['tarih'].strftime('%Y-%m-%d')
            json_save.append(temp)
        st.download_button("📥 Portföyü Yedekle (JSON)", data=json.dumps(json_save),
                           file_name=f"portfoy_{datetime.now().strftime('%d%m%Y')}.json", use_container_width=True)

    uploaded_json = st.file_uploader("📂 Yedek Yükle", type=['json'])
    if uploaded_json:
        data = json.load(uploaded_json)
        for item in data: item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
        st.session_state.portfolio = data
        st.rerun()

    st.divider()
    st.header("➕ Fon Ekle")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=180))
    f_qty = st.number_input("Adet", min_value=0.0, format="%.4f")
    f_cost = st.number_input("Birim Alış Fiyatı (TL)", min_value=0.0, format="%.4f")
    f_now = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.0, value=f_cost, format="%.4f")
    
    if st.button("➕ Ekle", use_container_width=True):
        if f_code and f_qty > 0:
            u_old = get_kur_data("USDTRY=X", f_date)
            g_old = get_kur_data("GBPTRY=X", f_date)
            gold_old = (get_kur_data("GC=F", f_date) / 31.10) * (u_old if u_old else 1)
            st.session_state.portfolio.append({
                "kod": f_code, "tarih": f_date, "adet": f_qty, 
                "maliyet": f_cost, "guncel": f_now,
                "usd_old": u_old, "gbp_old": g_old, "gold_old": gold_old
            })
            st.rerun()

# --- 4. ANA EKRAN ---
st.title("⚖️ Reel Portföy ve Maliyet Analizi")

if st.session_state.portfolio:
    with st.expander("⚙️ Portföyü Düzenle / Sil", expanded=True):
        to_delete = None
        for idx, item in enumerate(st.session_state.portfolio):
            c = st.columns([1, 1, 1, 1, 1, 0.5])
            with c[0]: st.write(f"**{item['kod']}**")
            with c[1]: st.write(item['tarih'].strftime('%d.%m.%Y') if hasattr(item['tarih'], 'strftime') else item['tarih'])
            with c[2]: st.session_state.portfolio[idx]['adet'] = c[2].number_input("Adet", value=float(item['adet']), key=f"q_{idx}", label_visibility="collapsed")
            with c[3]: st.session_state.portfolio[idx]['maliyet'] = c[3].number_input("Mal.", value=float(item['maliyet']), key=f"m_{idx}", label_visibility="collapsed")
            with c[4]: st.session_state.portfolio[idx]['guncel'] = c[4].number_input("Gün.", value=float(item['guncel']), key=f"g_{idx}", label_visibility="collapsed")
            with c[5]: 
                if c[5].button("🗑️", key=f"del_{idx}"): to_delete = idx
        if to_delete is not None:
            st.session_state.portfolio.pop(to_delete); st.rerun()

    # HESAPLAMALAR
    u_now = get_live_price("USDTRY=X")
    g_now = get_live_price("GBPTRY=X")
    gold_now = (get_live_price("GC=F") / 31.10) * u_now
    
    rows = []
    for item in st.session_state.portfolio:
        tm = item['adet'] * item['maliyet']
        tg = item['adet'] * item['guncel']
        inf = get_inflation_factor(item['tarih'])
        rows.append({
            "Fon": item['kod'],
            "Toplam Alış Tutarı": tm,
            "Güncel Değer": tg,
            "Enflasyon Farkı (₺)": tg - (tm * inf),
            "Dolar Farkı ($)": (tg / u_now) - (tm / item['usd_old']),
            "Sterlin Farkı (£)": (tg / g_now) - (tm / item['gbp_old']),
            "Altın Farkı (gr)": (tg / gold_now) - (tm / item['gold_old'])
        })
    
    df = pd.DataFrame(rows)

    # TABLO
    st.subheader("📋 Detaylı Performans Tablosu")
    st.dataframe(df.style.format({
        "Toplam Alış Tutarı": "{:,.2f} ₺", "Güncel Değer": "{:,.2f} ₺",
        "Enflasyon Farkı (₺)": "{:+.2f} ₺", "Dolar Farkı ($)": "{:+.2f} $",
        "Sterlin Farkı (£)": "{:+.2f} £", "Altın Farkı (gr)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B4B', 
                subset=df.columns[3:]), use_container_width=True)

    # ÖZET METRİKLER
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    total_m = df["Toplam Alış Tutarı"].sum()
    total_g = df["Güncel Değer"].sum()
    
    c1.metric("Toplam Sermaye", f"{total_m:,.2f} ₺")
    c2.metric("Güncel Portföy", f"{total_g:,.2f} ₺", delta=f"{total_g - total_m:,.2f} ₺")
    c3.metric("Reel Enf. Farkı", f"{df['Enflasyon Farkı (₺)'].sum():+,.2f} ₺")
    c4.metric("Reel Dolar Farkı", f"{df['Dolar Farkı ($)'].sum():+,.2f} $")
    c5.metric("Reel Altın Farkı", f"{df['Altın Farkı (gr)'].sum():+,.2f} gr")

else:
    st.info("💡 Sol taraftan fon ekleyerek başlayın.")

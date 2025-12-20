import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# 1. AYARLAR
st.set_page_config(page_title="Zenith Pro: Stabil Sürüm", layout="wide")

# 2. VERİ MOTORU
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        data = yf.download(ticker, start=d.strftime('%Y-%m-%d'), end=(d + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else 1.0
    except: return 1.0

@st.cache_data(ttl=300)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

def get_inflation_factor(start_date):
    if isinstance(start_date, str): start_date = datetime.strptime(start_date, '%Y-%m-%d')
    months_diff = (datetime.now().year - start_date.year) * 12 + (datetime.now().month - start_date.month)
    return (1 + 0.042) ** max(0, months_diff)

# 3. BELLEK YÖNETİMİ
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# 4. SOL MENÜ (DOSYA İŞLEMLERİ)
with st.sidebar:
    st.header("💾 Dosya İşlemleri")
    up_file = st.file_uploader("Yedek Yükle", type=['json'])
    if up_file:
        try:
            data = json.load(up_file)
            for item in data:
                if isinstance(item['tarih'], str): item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
            st.session_state.portfolio = data
            st.success("Yüklendi!")
        except: st.error("Dosya hatası!")
    
    if st.session_state.portfolio:
        save_data = []
        for i in st.session_state.portfolio:
            temp = i.copy()
            if hasattr(temp['tarih'], 'strftime'): temp['tarih'] = temp['tarih'].strftime('%Y-%m-%d')
            save_data.append(temp)
        st.download_button("📥 Portföyü İndir", json.dumps(save_data), "portfoy.json", use_container_width=True)

# 5. ANA EKRAN: YENİ FON EKLEME (EN BASİT HALİ)
st.title("🛡️ Zenith Pro: Kesintisiz Analiz")
st.subheader("➕ Yeni Fon Ekle")

# Sütunları zorla oluşturuyoruz
c1, c2, c3, c4, c5 = st.columns(5)
with c1: f_kod = st.text_input("Fon Kodu", key="new_kod").upper().strip()
with c2: f_tar = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30), key="new_tar")
with c3: f_adet = st.number_input("Adet", min_value=0.0, format="%.4f", key="new_adet")
with c4: f_alis = st.number_input("Alış Fiyatı (₺)", min_value=0.0, format="%.4f", key="new_alis")
with c5: f_gun = st.number_input("Güncel Fiyat (₺)", min_value=0.0, format="%.4f", key="new_gun")

if st.button("🚀 Listeye Ekle", use_container_width=True):
    if f_kod and f_adet > 0:
        d_s = f_tar.strftime('%Y-%m-%d')
        u_o = get_kur_data("USDTRY=X", d_s)
        g_o = get_kur_data("GBPTRY=X", d_s)
        gold_o = (get_kur_data("GC=F", d_s) / 31.10) * u_o
        
        st.session_state.portfolio.append({
            "kod": f_kod, "tarih": f_tar, "adet": f_adet, 
            "maliyet": f_alis, "guncel": f_gun if f_gun > 0 else f_alis,
            "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
        })
        st.rerun()
    else:
        st.warning("Eksik bilgi girdiniz!")

st.divider()

# 6. TABLO VE ANALİZ
if st.session_state.portfolio:
    # LİSTE DÜZENLEME
    with st.expander("⚙️ Portföyü Düzenle", expanded=True):
        to_del = None
        for i, item in enumerate(st.session_state.portfolio):
            cols = st.columns([1, 1, 1, 1, 1, 0.5])
            cols[0].write(f"**{item['kod']}**")
            cols[1].write(item['tarih'].strftime('%d.%m.%Y'))
            st.session_state.portfolio[i]['adet'] = cols[2].number_input("Adet", value=float(item['adet']), key=f"e_a_{i}", label_visibility="collapsed")
            st.session_state.portfolio[i]['maliyet'] = cols[3].number_input("Alış", value=float(item['maliyet']), key=f"e_m_{i}", label_visibility="collapsed")
            st.session_state.portfolio[i]['guncel'] = cols[4].number_input("Güncel", value=float(item['guncel']), key=f"e_g_{i}", label_visibility="collapsed")
            if cols[5].button("🗑️", key=f"btn_d_{i}"): to_del = i
        if to_del is not None:
            st.session_state.portfolio.pop(to_del)
            st.rerun()

    # HESAPLAMALAR
    u_n = get_live_price("USDTRY=X")
    g_n = get_live_price("GBPTRY=X")
    gold_n = (get_live_price("GC=F") / 31.10) * u_n
    
    rows = []
    for item in st.session_state.portfolio:
        t_m = item['adet'] * item['maliyet']
        t_g = item['adet'] * item['guncel']
        inf = get_inflation_factor(item['tarih'])
        rows.append({
            "Fon": item['kod'], "Sermaye": t_m, "Değer": t_g,
            "Enflasyon (₺)": t_g - (t_m * inf),
            "Dolar ($)": (t_g / u_n) - (t_m / item['usd_old']),
            "Altın (gr)": (t_g / gold_n) - (t_m / item['gold_old'])
        })
    
    st.dataframe(pd.DataFrame(rows).style.format("{:,.2f}"), use_container_width=True)

    # ÖZET
    df = pd.DataFrame(rows)
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Sermaye", f"{df['Sermaye'].sum():,.2f} ₺")
    m2.metric("Portföy Değeri", f"{df['Değer'].sum():,.2f} ₺")
    m3.metric("Reel Dolar Farkı", f"{df['Dolar ($)'].sum():+,.2f} $")

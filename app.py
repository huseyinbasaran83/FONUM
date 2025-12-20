import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Kesintisiz Analiz", layout="wide")

# --- 1. VERİ MOTORU (GİZLİ HESAPLAMALAR) ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), 
                           end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else 1.0
    except: return 1.0

@st.cache_data(ttl=300)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

def get_inflation_factor(start_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    today = datetime.now()
    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return (1 + 0.042) ** max(0, months_diff)

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR (SADECE DOSYA İŞLEMLERİ) ---
with st.sidebar:
    st.header("💾 Dosya Yönetimi")
    uploaded_json = st.file_uploader("📂 Yedek Dosyanı Buraya At", type=['json'])
    if uploaded_json:
        raw_data = json.load(uploaded_json)
        for item in raw_data:
            if isinstance(item['tarih'], str):
                item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
        st.session_state.portfolio = raw_data
        st.success("Yedek Yüklendi!")

    if st.session_state.portfolio:
        export_data = []
        for item in st.session_state.portfolio:
            new_item = item.copy()
            if hasattr(new_item['tarih'], 'strftime'):
                new_item['tarih'] = new_item['tarih'].strftime('%Y-%m-%d')
            export_data.append(new_item)
        st.download_button("📥 Mevcut Portföyü İndir", data=json.dumps(export_data), file_name="portfoy.json", use_container_width=True)

# --- 4. ANA EKRAN (YENİ FON EKLEME - GENİŞ ALAN) ---
st.title("🛡️ Zenith Pro: Portföy Yönetimi")

st.subheader("➕ Yeni Fon Ekle")
with st.container():
    # Tüm girişleri yan yana sütunlara ayırdık (Görünmeme ihtimalini yok ettik)
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.5, 1, 1, 1])
    
    with col1: f_code = st.text_input("Fon Kodu", placeholder="Örn: TCD").upper().strip()
    with col2: f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30))
    with col3: f_qty = st.number_input("Adet", min_value=0.0, format="%.4f", step=0.0001)
    with col4: f_cost = st.number_input("Birim Alış (₺)", min_value=0.0, format="%.4f", step=0.0001)
    with col5: f_now = st.number_input("Birim Güncel (₺)", min_value=0.0, format="%.4f", step=0.0001)

    if st.button("🚀 Portföye Kaydet ve Hesapla", use_container_width=True):
        if f_code and f_qty > 0 and f_cost > 0:
            with st.spinner("Piyasa verileri işleniyor..."):
                d_str = f_date.strftime('%Y-%m-%d')
                u_o = get_kur_data("USDTRY=X", d_str)
                g_o = get_kur_data("GBPTRY=X", d_str)
                gold_o = (get_kur_data("GC=F", d_str) / 31.10) * u_o
                
                st.session_state.portfolio.append({
                    "kod": f_code, "tarih": f_date, "adet": f_qty, 
                    "maliyet": f_cost, "guncel": f_now if f_now > 0 else f_cost,
                    "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
                })
                st.rerun()
        else:
            st.warning("Lütfen Fon Kodu, Adet ve Alış Fiyatını doldurun!")

st.divider()

# --- 5. ANALİZ VE TABLOLAR ---
if st.session_state.portfolio:
    # MEVCUT LİSTE (DÜZENLEME)
    with st.expander("⚙️ Portföy Listesi (Adet ve Fiyatları Buradan Güncelleyebilirsiniz)", expanded=True):
        to_del = None
        for i, item in enumerate(st.session_state.portfolio):
            c = st.columns([1, 1.2, 1, 1, 1, 0.5])
            with c[0]: st.info(f"**{item['kod']}**")
            with c[1]: st.write(item['tarih'].strftime('%d.%m.%Y'))
            with c[2]: st.session_state.portfolio[i]['adet'] = c[2].number_input("Adet", value=float(item['adet']), key=f"edit_q_{i}", label_visibility="collapsed")
            with c[3]: st.session_state.portfolio[i]['maliyet'] = c[3].number_input("Alış", value=float(item['maliyet']), key=f"edit_m_{i}", label_visibility="collapsed")
            with c[4]: st.session_state.portfolio[i]['guncel'] = c[4].number_input("Güncel", value=float(item['guncel']), key=f"edit_g_{i}", label_visibility="collapsed")
            with c[5]: 
                if c[5].button("🗑️", key=f"del_{i}"): to_del = i
        
        if to_del is not None:
            st.session_state.portfolio.pop(to_del)
            st.rerun()

    # HESAPLAMALAR
    u_n = get_live_price("USDTRY=X") or 1.0
    g_n = get_live_price("GBPTRY=X") or 1.0
    gold_n = ((get_live_price("GC=F") or 2500) / 31.10) * u_n
    
    final_rows = []
    for item in st.session_state.portfolio:
        t_mal = item['adet'] * item['maliyet']
        t_gun = item['adet'] * item['guncel']
        inf = get_inflation_factor(item['tarih'])
        
        final_rows.append({
            "Fon": item['kod'],
            "Toplam Alış": t_mal,
            "Güncel Değer": t_gun,
            "Enflasyon Farkı (₺)": t_gun - (t_mal * inf),
            "Dolar Farkı ($)": (t_gun / u_n) - (t_mal / item['usd_old']),
            "Sterlin Farkı (£)": (t_gun / g_n) - (t_mal / item['gbp_old']),
            "Altın Farkı (gr)": (t_gun / gold_n) - (t_mal / item['gold_old'])
        })
    
    df = pd.DataFrame(final_rows)

    # TABLO
    st.subheader("📋 Reel Kazanç/Kayıp Analizi")
    st.dataframe(df.style.format({
        "Toplam Alış": "{:,.2f} ₺", "Güncel Değer": "{:,.2f} ₺",
        "Enflasyon Farkı (₺)": "{:+.2f} ₺", "Dolar Farkı ($)": "{:+.2f} $",
        "Sterlin Farkı (£)": "{:+.2f} £", "Altın Farkı (gr)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B

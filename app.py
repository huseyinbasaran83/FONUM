import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Kesintisiz Analiz", layout="wide")

# --- 1. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), 
                           end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        if not data.empty:
            return float(data['Close'].iloc[0])
        return 1.0
    except:
        return 1.0

@st.cache_data(ttl=300)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except:
        return 1.0

def get_inflation_factor(start_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    today = datetime.now()
    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return (1 + 0.042) ** max(0, months_diff)

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("💾 Veri Yönetimi")
    
    # Yükleme Alanı
    uploaded_json = st.file_uploader("📂 Yedek Dosyasını Yükle", type=['json'])
    if uploaded_json:
        try:
            raw_data = json.load(uploaded_json)
            cleaned_data = []
            for item in raw_data:
                if 'tarih' in item and isinstance(item['tarih'], str):
                    item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
                cleaned_data.append(item)
            st.session_state.portfolio = cleaned_data
            st.success("Yükleme Başarılı!")
        except Exception as e:
            st.error(f"Hata: {e}")

    # İndirme Alanı
    if st.session_state.portfolio:
        export_data = []
        for item in st.session_state.portfolio:
            new_item = item.copy()
            if hasattr(new_item['tarih'], 'strftime'):
                new_item['tarih'] = new_item['tarih'].strftime('%Y-%m-%d')
            export_data.append(new_item)
        
        st.download_button("📥 Portföyü Yedekle (JSON)", 
                           data=json.dumps(export_data),
                           file_name=f"portfoy_yedek.json",
                           use_container_width=True)

    st.divider()
    
    # Yeni Fon Ekleme Alanı (Form içinde daha güvenli çalışır)
    st.header("➕ Yeni Fon Ekle")
    with st.form("add_fund_form", clear_on_submit=True):
        f_code = st.text_input("Fon Kodu").upper().strip()
        f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
        f_qty = st.number_input("Adet", min_value=0.0, step=0.0001, format="%.4f")
        f_cost = st.number_input("Birim Alış Fiyatı (TL)", min_value=0.0, step=0.000001, format="%.6f")
        f_now = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.0, step=0.000001, format="%.6f")
        
        submitted = st.form_submit_button("Listeye Ekle", use_container_width=True)
        
        if submitted:
            if f_code and f_qty > 0:
                d_str = f_date.strftime('%Y-%m-%d')
                with st.spinner("Piyasa verileri alınıyor..."):
                    u_o = get_kur_data("USDTRY=X", d_str)
                    g_o = get_kur_data("GBPTRY=X", d_str)
                    gold_o = (get_kur_data("GC=F", d_str) / 31.10) * u_o
                    
                    st.session_state.portfolio.append({
                        "kod": f_code, "tarih": f_date, "adet": f_qty, 
                        "maliyet": f_cost, "guncel": f_now,
                        "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
                    })
                    st.rerun()

# --- 4. ANA EKRAN ---
st.title("⚖️ Zenith Pro: Reel Portföy")

if st.session_state.portfolio:
    with st.expander("⚙️ Portföy Listesi ve Düzenleme", expanded=True):
        to_del = None
        for i, item in enumerate(st.session_state.portfolio):
            c = st.columns([1, 1.2, 1, 1, 1, 0.5])
            with c[0]: st.info(f"**{item['kod']}**")
            with c[1]: 
                d_val = item['tarih']
                st.write(d_val.strftime('%d.%m.%Y') if hasattr(d_val, 'strftime') else str(d_val))
            with c[2]: st.session_state.portfolio[i]['adet'] = c[2].number_input("Adet", value=float(item['adet']), key=f"q_{i}", format="%.4f", label_visibility="collapsed")
            with c[3]: st.session_state.portfolio[i]['maliyet'] = c[3].number_input("Alış", value=float(item['maliyet']), key=f"m_{i}", format="%.6f", label_visibility="collapsed")
            with c[4]: st.session_state.portfolio[i]['guncel'] = c[4].number_input("Güncel", value=float(item['guncel']), key=f"g_{i}", format="%.6f", label_visibility="collapsed")
            with c[5]: 
                if c[5].button("🗑️", key=f"d_{i}"): to_del = i
        if to_del is not None:
            st.session_state.portfolio.pop(to_del)
            st.rerun()

    with st.spinner("Hesaplanıyor..."):
        u_n = get_live_price("USDTRY=X")
        g_n = get_live_price("GBPTRY=X")
        gold_n = (get_live_price("GC=F") / 31.10) * u_n
        
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
                "Dolar Farkı ($)": (t_gun / u_n) - (t_mal / (item['usd_old'] if item['usd_old'] else 1)),
                "Sterlin Farkı (£)": (t_gun / g_n) - (t_mal / (item['gbp_old'] if item['gbp_old'] else 1)),
                "Altın Farkı (gr)": (t_gun / gold_n) - (t_mal / (item['gold_old'] if item['gold_old'] else 1))
            })
        
        df = pd.DataFrame(final_rows)

    st.subheader("📋 Reel Performans Tablosu")
    st.dataframe(df.style.format({
        "Toplam Alış": "{:,.2f} ₺", "Güncel Değer": "{:,.2f} ₺",
        "Enflasyon Farkı (₺)": "{:+.2f} ₺", "Dolar Farkı ($)": "{:+.2f} $",
        "Sterlin Farkı (£)": "{:+.2f} £", "Altın Farkı (gr)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B4B', 
                subset=df.columns[3:]), use_container_width=True)

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Sermaye", f"{df['Toplam Alış'].sum():,.2f} ₺")
    m2.metric("Portföy Değeri", f"{df['Güncel Değer'].sum():,.2f} ₺", delta=f"{df['Güncel Değer'].sum() - df['Toplam Alış'].sum():,.2f} ₺")
    m3.metric("Reel Dolar Farkı", f"{df['Dolar Farkı ($)'].sum():+,.2f} $")
    m4.metric("Reel Altın Farkı", f"{df['Altın Farkı (gr)'].sum():+,.2f} gr")

else:
    st.info("💡 Lütfen yedek dosyanızı yükleyin veya yeni fon ekleyin.")

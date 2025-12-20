import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Hızlı Portföy", layout="wide")

# --- 1. HIZLANDIRILMIŞ VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    """Tarihi string alarak cache mekanizmasını stabilize ediyoruz"""
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
    # Tarih farkını ay bazında hesapla
    today = datetime.now()
    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return (1 + 0.042) ** max(0, months_diff)

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR: YÜKLEME VE GİRİŞ ---
with st.sidebar:
    st.header("💾 Veri Yönetimi")
    
    uploaded_json = st.file_uploader("📂 Yedek Dosyasını Seç", type=['json'])
    if uploaded_json:
        try:
            raw_data = json.load(uploaded_json)
            # Kritik düzeltme: Yüklenen veriyi temizle ve date objesine çevir
            cleaned_data = []
            for item in raw_data:
                if 'tarih' in item and isinstance(item['tarih'], str):
                    item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
                cleaned_data.append(item)
            st.session_state.portfolio = cleaned_data
            st.success("Yükleme tamamlandı!")
        except Exception as e:
            st.error(f"Yükleme hatası: {e}")

    if st.session_state.portfolio:
        # JSON İndirme Hazırlığı
        export_data = []
        for item in st.session_state.portfolio:
            new_item = item.copy()
            if hasattr(new_item['tarih'], 'strftime'):
                new_item['tarih'] = new_item['tarih'].strftime('%Y-%m-%d')
            export_data.append(new_item)
        
        st.download_button("📥 Mevcut Portföyü İndir", 
                           data=json.dumps(export_data),
                           file_name=f"portfoy_yedek.json",
                           use_container_width=True)

    st.divider()
    st.header("➕ Fon Ekle")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=180))
    f_qty = st.number_input("Adet", min_value=0.0, format="%.4f")
    f_cost = st.number_input("Birim Alış (TL)", min_value=0.0, format="%.4f")
    
    if st.button("➕ Listeye Ekle", use_container_width=True):
        if f_code and f_qty > 0:
            d_str = f_date.strftime('%Y-%m-%d')
            with st.spinner("Kurlar çekiliyor..."):
                u_o = get_kur_data("USDTRY=X", d_str)
                g_o = get_kur_data("GBPTRY=X", d_str)
                gold_o = (get_kur_data("GC=F", d_str) / 31.10) * u_o
                
                st.session_state.portfolio.append({
                    "kod": f_code, "tarih": f_date, "adet": f_qty, 
                    "maliyet": f_cost, "guncel": f_cost,
                    "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
                })
                st.rerun()

# --- 4. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Kesintisiz Analiz")

if st.session_state.portfolio:
    # 1. DÜZENLEME PANELİ
    with st.expander("⚙️ Portföy Listesi ve Düzenleme", expanded=True):
        to_del = None
        for i, item in enumerate(st.session_state.portfolio):
            c = st.columns([1, 1.2, 1, 1, 1, 0.5])
            with c[0]: st.info(f"**{item['kod']}**")
            with c[1]: 
                # Tarih gösterimi hatasını engelle
                d_val = item['tarih']
                st.write(d_val.strftime('%d.%m.%Y') if hasattr(d_val, 'strftime') else str(d_val))
            with c[2]: st.session_state.portfolio[i]['adet'] = c[2].number_input("Adet", value=float(item['adet']), key=f"q_{i}", label_visibility="collapsed")
            with c[3]: st.session_state.portfolio[i]['maliyet'] = c[3].number_input("Mal", value=float(item['maliyet']), key=f"m_{i}", label_visibility="collapsed")
            with c[4]: st.session_state.portfolio[i]['guncel'] = c[4].number_input("Gün", value=float(item['guncel']), key=f"g_{i}", label_visibility="collapsed")
            with c[5]: 
                if c[5].button("🗑️", key=f"d_{i}"): to_del = i
        if to_del is not None:
            st.session_state.portfolio.pop(to_del)
            st.rerun()

    # 2. HESAPLAMALAR
    with st.spinner("Piyasa verileri güncelleniyor..."):
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
                "Alış Tutarı": t_mal,
                "Güncel Değer": t_gun,
                "Enflasyon Farkı (₺)": t_gun - (t_mal * inf),
                "Dolar Farkı ($)": (t_gun / u_n) - (t_mal / item['usd_old']),
                "Sterlin Farkı (£)": (t_gun / g_n) - (tm / item['gbp_old']) if 'tm' not in locals() else (t_gun / g_n) - (t_mal / item['gbp_old']),
                "Altın Farkı (gr)": (t_gun / gold_n) - (t_mal / item['gold_old'])
            })
        
        df = pd.DataFrame(final_rows)

    # 3. GÖRÜNÜM
    st.subheader("📋 Reel Performans Tablosu")
    st.dataframe(df.style.format({
        "Alış Tutarı": "{:,.2f} ₺", "Güncel Değer": "{:,.2f} ₺",
        "Enflasyon Farkı (₺)": "{:+.2f} ₺", "Dolar Farkı ($)": "{:+.2f} $",
        "Sterlin Farkı (£)": "{:+.2f} £", "Altın Farkı (gr)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B4B', 
                subset=df.columns[3:]), use_container_width=True)

    # 4. ÖZET
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ana Sermaye", f"{df['Alış Tutarı'].sum():,.2f} ₺")
    m2.metric("Portföy Değeri", f"{df['Güncel Değer'].sum():,.2f} ₺", delta=f"{df['Güncel Değer'].sum() - df['Alış Tutarı'].sum():,.2f} ₺")
    m3.metric("Reel Dolar Farkı", f"{df['Dolar Farkı ($)'].sum():+,.2f} $")
    m4.metric("Reel Altın Farkı", f"{df['Altın Farkı (gr)'].sum():+,.2f} gr")

else:
    st.info("💡 Lütfen yedek dosyanızı yükleyin veya yeni fon ekleyin.")

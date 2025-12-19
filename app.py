import streamlit as st
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Agent", layout="wide")

# --- CSS ile Finansal Arayüz Özelleştirme ---
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- Sabit Veriler (Agent Veri Modeli) ---
rates = {"USD_TRY": 32.50, "GRAM_GOLD_TRY": 2650}

# --- Sidebar: Fon Girişi ---
with st.sidebar:
    st.header("📥 Fon Portföyü")
    fund_code = st.text_input("Fon Kodu", placeholder="Örn: AFT")
    fund_qty = st.number_input("Adet", min_value=0, value=100)
    fund_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=12.5)
    
    if st.button("Portföye Ekle"):
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = []
        st.session_state.portfolio.append({"kod": fund_code, "adet": fund_qty, "fiyat": fund_price})
        st.success(f"{fund_code} eklendi!")

# --- Ana Panel ---
st.title("🛡️ Zenith Portföy Analiz Agent")

if 'portfolio' in st.session_state and len(st.session_state.portfolio) > 0:
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    # Üst Metrikler
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Büyüklük (TL)", f"{total_tl:,.0f} ₺")
    col2.metric("USD Karşılığı", f"${total_tl/rates['USD_TRY']:,.2f}")
    col3.metric("Altın Karşılığı", f"{total_tl/rates['GRAM_GOLD_TRY']:,.2f} gr")
    col4.metric("Sağlık Skoru", "78/100")

    # Senaryo Analizi
    st.divider()
    st.subheader("🧪 Senaryo Simülatörü")
    s_col1, s_col2 = st.columns([2, 1])
    
    with s_col1:
        usd_change = st.slider("USD / TL Değişimi (%)", -20, 50, 0)
        gold_change = st.slider("Gram Altın Değişimi (%)", -20, 50, 0)
    
    with s_col2:
        # Agent Hesaplama Mantığı (Basitleştirilmiş)
        # Varsayalım ki portföyün %60'ı USD hassasiyetli
        new_val = total_tl * (1 + (usd_change/100 * 0.6) + (gold_change/100 * 0.1))
        st.write("### Senaryo Sonucu")
        st.write(f"Yeni Değer: **{new_val:,.0f} ₺**")
        st.write(f"Fark: **{new_val - total_tl:,.0f} ₺**")

    # Agent Yorumu
    st.info(f"**Agent Analizi:** Portföyünüz kura duyarlı varlıklar içeriyor. USD'deki %{usd_change} artış, toplam değerinizi yaklaşık %{usd_change*0.6:.1f} oranında etkileyecektir.")

    # Portföy Tablosu
    st.subheader("📊 Mevcut Varlıklar")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("Henüz fon eklenmedi. Lütfen sol taraftaki panelden fon girişlerini yapın.")
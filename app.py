import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy: Kar/Zarar Analizi", layout="wide")

# --- GÜNCEL FİYAT VERİTABANI (Simüle Edilmiş Canlı Fiyatlar) ---
# Gerçek dünyada bu veriler her gün TEFAS veya API'den çekilir.
live_prices = {
    "AFT": 185.40,
    "TCD": 12.80,
    "MAC": 245.15,
    "GUM": 0.45,
    "TI3": 4.12,
    "ZRE": 115.30
}

# --- FON İÇERİĞİ (Röntgen Verisi) ---
fund_composition = {
    "AFT": {"detay": {"NVIDIA": 0.18, "APPLE": 0.15, "MICROSOFT": 0.12, "ALPHABET": 0.10, "NAKİT": 0.45}},
    "TCD": {"detay": {"TÜPRAŞ": 0.15, "KOÇ HOLDİNG": 0.12, "ASELSAN": 0.10, "THY": 0.08, "ALTIN": 0.15, "NAKİT": 0.40}},
    "MAC": {"detay": {"THY": 0.18, "BİMAS": 0.14, "EREĞLİ": 0.12, "SAHOL": 0.10, "MGROS": 0.08, "DİĞER": 0.38}},
    "GUM": {"detay": {"GÜMÜŞ": 0.95, "NAKİT": 0.05}}
}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar: Alış Verisi Girişi ---
with st.sidebar:
    st.header("🛒 Alış İşlemi Gir")
    f_code = st.text_input("Fon Kodu", placeholder="Örn: AFT").upper()
    f_qty = st.number_input("Adet", min_value=1.0, value=100.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.0, value=150.0)
    
    if st.button("➕ İşlemi Kaydet", use_container_width=True):
        if f_code:
            st.session_state.portfolio.append({
                "kod": f_code, 
                "adet": f_qty, 
                "maliyet": f_cost
            })
            st.rerun()

    st.divider()
    if st.session_state.portfolio and st.checkbox("⚠️ Temizleme Onayı"):
        if st.button("🗑️ TÜMÜNÜ SİL"):
            st.session_state.portfolio = []
            st.rerun()

# --- Ana Ekran ---
st.title("📈 Zenith Performans & Kar-Zarar Agent")

if st.session_state.portfolio:
    # Verileri Hazırlama
    df = pd.DataFrame(st.session_state.portfolio)
    
    # Güncel fiyatları ekle (Veritabanında yoksa maliyeti fiyat kabul et)
    df['Güncel Fiyat'] = df['kod'].apply(lambda x: live_prices.get(x, 0))
    # Eğer canlı fiyat listede yoksa kullanıcıya manuel fiyat girmesi için maliyeti kullanırız
    df.loc[df['Güncel Fiyat'] == 0, 'Güncel Fiyat'] = df['maliyet'] 
    
    df['Toplam Maliyet'] = df['adet'] * df['maliyet']
    df['Güncel Değer'] = df['adet'] * df['Güncel Fiyat']
    df['Kar/Zarar (TL)'] = df['Güncel Değer'] - df['Toplam Maliyet']
    df['Getiri (%)'] = (df['Kar/Zarar (TL)'] / df['Toplam Maliyet']) * 100

    # Özet Metrikler
    total_cost = df['Toplam Maliyet'].sum()
    current_value = df['Güncel Değer'].sum()
    total_profit = current_value - total_cost
    profit_pct = (total_profit / total_cost) * 100 if total_cost != 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Maliyet", f"{total_cost:,.2f} ₺")
    m2.metric("Güncel Değer", f"{current_value:,.2f} ₺")
    m3.metric("Net Kar/Zarar", f"{total_profit:,.2f} ₺", f"{profit_pct:.2f}%")
    m4.metric("Fon Sayısı", len(df))

    st.divider()

    # --- PERFORMANS TABLOSU ---
    st.subheader("📊 Fon Bazlı Performans")
    
    # Kar-Zarar Renklendirme Fonksiyonu
    def color_profit(val):
        color = '#2ecc71' if val > 0 else '#e74c3c'
        return f'color: {color}; font-weight: bold'

    st.dataframe(df.style.format({
        'maliyet': '{:.4f} ₺',
        'Güncel Fiyat': '{:.4f} ₺',
        'Toplam Maliyet': '{:,.2f} ₺',
        'Güncel Değer': '{:,.2f} ₺',
        'Kar/Zarar (TL)': '{:,.2f} ₺',
        'Getiri (%)': '% {:.2f}'
    }).applymap(color_profit, subset=['Kar/Zarar (TL)', 'Getiri (%)']), use_container_width=True)

    # --- GÖRSEL ANALİZ ---
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💰 Fonların Kar/Zarar Dağılımı (TL)")
        fig_profit = px.bar(df, x='kod', y='Kar/Zarar (TL)', color='Kar/Zarar (TL)',
                            color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_profit, use_container_width=True)

    with c2:
        # Gerçek Varlık Röntgeni (Yine aktif)
        asset_breakdown = {}
        for _, row in df.iterrows():
            fund_info = fund_composition.get(row['kod'], {"detay": {"DİĞER": 1.0}})
            for asset, ratio in fund_info['detay'].items():
                asset_breakdown[asset] = asset_breakdown.get(asset, 0) + (row['Güncel Değer'] * ratio)
        
        breakdown_df = pd.DataFrame(list(asset_breakdown.items()), columns=['Varlık', 'Değer']).sort_values(by='Değer', ascending=False)
        
        st.subheader("💎 Güncel Varlık Röntgeni")
        st.plotly_chart(px.pie(breakdown_df.head(10), values='Değer', names='Varlık', hole=0.3), use_container_width=True)

    # Düzenleme Alanı
    with st.expander("✏️ Portföyü Düzenle (Adet/Maliyet Değiştir)"):
        for idx, item in enumerate(st.session_state.portfolio):
            col_k, col_a, col_m, col_s = st.columns([1,2,2,1])
            col_k.write(f"**{item['kod']}**")
            st.session_state.portfolio[idx]['adet'] = col_a.number_input("Yeni Adet", value=float(item['adet']), key=f"q_{idx}")
            st.session_state.portfolio[idx]['maliyet'] = col_m.number_input("Yeni Maliyet", value=float(item['maliyet']), key=f"m_{idx}")
            if col_s.button("Sil", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

else:
    st.info("İşlem verilerinizi girerek performans analizini başlatın. (Örn: AFT maliyet 150, güncel fiyat 185)")

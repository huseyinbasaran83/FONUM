import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# 1. AYARLAR
st.set_page_config(page_title="Zenith Pro: Final", layout="wide")

# 2. VERİ MOTORU
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        data = yf.download(ticker, start=d.strftime('%Y-%m-%d'), end=(d + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else 1.0
    except: return 1.0

# 3. BELLEK
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# 4. SIDEBAR (DOSYA)
with st.sidebar:
    st.header("💾 Dosya İşlemleri")
    up_file = st.file_uploader("JSON Yedeği Yükle", type=['json'])
    if up_file is not None:
        try:
            data = json.load(up_file)
            for item in data:
                if isinstance(item['tarih'], str): 
                    item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
            st.session_state.portfolio = data
            st.success("Yedek Yüklendi!")
        except: st.error("Yükleme başarısız.")

    if st.session_state.portfolio:
        save_list = []
        for i in st.session_state.portfolio:
            t = i.copy()
            if hasattr(t['tarih'], 'strftime'): t['tarih'] = t['tarih'].strftime('%Y-%m-%d')
            save_list.append(t)
        st.download_button("📥 Portföyü İndir", json.dumps(save_list), "portfoy_yedek.json", use_container_width=True)

# 5. ANA EKRAN (ALT ALTA GİRİŞ - GARANTİ YÖNTEM)
st.title("🛡️ Zenith Pro: Kesin Çözüm")
st.markdown("### ➕ Yeni Fon Ekle")

# Sütunları bıraktık, alt alta en güvenli girişleri yapıyoruz
f_kod = st.text_input("1. Fon Kodu", key="f_kod").upper().strip()
f_tar = st.date_input("2. Alış Tarihi", value=datetime.now() - timedelta(days=30), key="f_tar")
f_adet = st.number_input("3. Adet", min_value=0.0, format="%.4f", step=0.0001, key="f_adet")
f_alis = st.number_input("4. Birim Alış Fiyatı (₺)", min_value=0.0, format="%.4f", step=0.0001, key="f_alis")
f_gun = st.number_input("5. Birim Güncel Fiyat (₺)", min_value=0.0, format="%.4f", step=0.0001, key="f_gun")

if st.button("✅ LİSTEYE KAYDET", use_container_width=True):
    if f_kod and f_adet > 0:
        with st.spinner("Kurlar hesaplanıyor..."):
            d_s = f_tar.strftime('%Y-%m-%d')
            u_o = get_kur_data("USDTRY=X", d_s)
            g_o = get_kur_data("GBPTRY=X", d_s)
            gold_o = (get_kur_data("GC=F", d_s) / 31.10) * u_o
            
            # Veriyi session_state'e ekle
            new_entry = {
                "kod": f_code if 'f_code' in locals() else f_kod, 
                "tarih": f_tar, 
                "adet": f_adet, 
                "maliyet": f_alis, 
                "guncel": f_gun if f_gun > 0 else f_alis,
                "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
            }
            st.session_state.portfolio.append(new_entry)
            st.success(f"{f_kod} başarıyla eklendi!")
            st.rerun()
    else:
        st.error("Lütfen Fon Kodu ve Adet alanlarını doldurun!")

st.divider()

# 6. TABLO VE ANALİZ
if st.session_state.portfolio:
    st.subheader("📋 Mevcut Portföy ve Düzenleme")
    
    # Düzenleme Alanı
    for i, item in enumerate(st.session_state.portfolio):
        with st.expander(f"📌 {item['kod']} - {item['tarih']}", expanded=False):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
            st.session_state.portfolio[i]['adet'] = c1.number_input(f"Adet ({item['kod']})", value=float(item['adet']), key=f"ed_a_{i}")
            st.session_state.portfolio[i]['maliyet'] = c2.number_input(f"Alış ({item['kod']})", value=float(item['maliyet']), key=f"ed_m_{i}")
            st.session_state.portfolio[i]['guncel'] = c3.number_input(f"Güncel ({item['kod']})", value=float(item['guncel']), key=f"ed_g_{i}")
            if c4.button("🗑️ Sil", key=f"del_{i}"):
                st.session_state.portfolio.pop(i)
                st.rerun()

    # Özet Tablo
    u_n = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    gold_n = (yf.download("GC=F", period="1d", progress=False)['Close'].iloc[-1] / 31.10) * u_n
    
    res = []
    for item in st.session_state.portfolio:
        t_m = item['adet'] * item['maliyet']
        t_g = item['adet'] * item['guncel']
        res.append({
            "Fon": item['kod'],
            "Maliyet (₺)": t_m,
            "Güncel (₺)": t_g,
            "Kar/Zarar (₺)": t_g - t_m,
            "Dolar ($) Farkı": (t_g / u_n) - (t_m / item['usd_old']),
            "Altın (gr) Farkı": (t_g / gold_n) - (t_m / item['gold_old'])
        })
    
    df = pd.DataFrame(res)
    st.dataframe(df.style.format("{:,.2f}"), use_container_width=True)
    
    # Metrikler
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Sermaye", f"{df['Maliyet (₺)'].sum():,.2f} ₺")
    m2.metric("Portföy Değeri", f"{df['Güncel (₺)'].sum():,.2f} ₺")
    m3.metric("Reel Dolar Kazancı", f"{df['Dolar ($) Farkı'].sum():+,.2f} $")

else:
    st.info("Henüz fon eklenmemiş.")

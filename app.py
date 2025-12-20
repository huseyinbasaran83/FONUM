import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# --- 1. AYARLAR ---
st.set_page_config(page_title="Zenith Kesin Cozum", layout="wide")

# Belleği sıfırdan başlat
if 'DATA' not in st.session_state:
    st.session_state['DATA'] = []

# --- 2. DOSYA YUKLEME ---
with st.sidebar:
    st.header("1. ADIM: YEDEK YUKLE")
    f = st.file_uploader("JSON Dosyası", type=['json'], key="uploader_final")
    if f:
        try:
            raw = json.load(f)
            processed = []
            for r in raw:
                if isinstance(r.get('tarih'), str):
                    r['tarih'] = datetime.strptime(r['tarih'], '%Y-%m-%d').date()
                processed.append(r)
            if st.button("YEDEGI LISTEYE AKTAR"):
                st.session_state['DATA'] = processed
                st.rerun()
        except: st.error("Dosya okunamadı.")

# --- 3. MANUEL FON EKLEME (METIN KUTUSU YONTEMI) ---
st.title("🛡️ Zenith Portfoy Takip (Stabil Surum)")
st.info("Ekleme yapamıyorsanız veya kutular eksikse lütfen reklam engelleyicinizi (AdBlock) kapatın.")

st.subheader("2. ADIM: YENI FON EKLE")

# Sayı girişlerini metin kutusuna çevirdik (Engellenmemesi için)
in_kod = st.text_input("FON KODU (Orn: TCD)", key="in1").upper().strip()
in_tar = st.date_input("ALIS TARIHI", key="in2")
in_adet = st.text_input("ADET (Miktar girin)", value="0.0", key="in3")
in_alis = st.text_input("BIRIM ALIS FIYATI (₺)", value="0.0", key="in4")
# En kritik kutu:
in_guncel = st.text_input("GUNCEL BIRIM FIYAT (₺) - MUTLAKA DOLDURUN", value="0.0", key="in5")

if st.button("🚀 PORTFOYE EKLE"):
    if in_kod:
        try:
            # Metinleri sayıya çevir
            a = float(in_adet.replace(',', '.'))
            m = float(in_alis.replace(',', '.'))
            g = float(in_guncel.replace(',', '.'))
            
            if a > 0:
                with st.spinner("Kurlar cekiliyor..."):
                    # Gecmis kur
                    d_s = in_tar.strftime('%Y-%m-%d')
                    u = yf.download("USDTRY=X", start=d_s, end=(in_tar + timedelta(days=5)).strftime('%Y-%m-%d'), progress=False)
                    u_old = float(u['Close'].iloc[0]) if not u.empty else 1.0
                    
                    # Kaydet
                    yeni = {
                        "kod": in_kod, "tarih": in_tar, "adet": a, 
                        "maliyet": m, "guncel": g, "usd_old": u_old
                    }
                    st.session_state['DATA'].append(yeni)
                    st.success("Eklendi!")
                    st.rerun()
            else: st.error("Adet 0'dan buyuk olmalı.")
        except: st.error("Lutfen sayı kutularına sadece rakam girin (Orn: 10.5)")
    else: st.error("Fon kodu bos olamaz.")

st.divider()

# --- 4. TABLO ---
if st.session_state['DATA']:
    st.subheader("3. ADIM: MEVCUT DURUM")
    
    # Guncel Dolar
    try: u_n = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    except: u_n = 1.0
    
    final_list = []
    for i, item in enumerate(st.session_state['DATA']):
        top_m = item['adet'] * item['maliyet']
        top_g = item['adet'] * item['guncel']
        
        final_list.append({
            "KOD": item['kod'],
            "ADET": item['adet'],
            "TOPLAM MALIYET": f"{top_m:,.2f} TL",
            "GUNCEL DEGER": f"{top_g:,.2f} TL",
            "DOLAR FARKI ($)": f"{((top_g/u_n) - (top_m/item['usd_old'])):,.2f} $"
        })
        
        if st.button(f"SİL: {item['kod']} ({i})", key=f"btn_{i}"):
            st.session_state['DATA'].pop(i)
            st.rerun()

    st.table(final_list)
else:
    st.info("Liste bos. Yukaridan ekleme yapin.")

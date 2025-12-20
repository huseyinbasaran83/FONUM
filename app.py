import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# 1. TEMEL AYARLAR
st.set_page_config(page_title="Zenith Pro: Final", layout="wide")

# Portföyü session_state içinde başlat
if 'portfoy' not in st.session_state:
    st.session_state['portfoy'] = []

# 2. YEDEK YÜKLEME (SIDEBAR)
with st.sidebar:
    st.header("📂 VERİ YÖNETİMİ")
    yuklenen_dosya = st.file_uploader("JSON Yedeğini Seç", type=['json'])
    
    if yuklenen_dosya is not None:
        try:
            # Dosyayı oku ve içeriği listeye ekle
            dosya_icerik = json.load(yuklenen_dosya)
            yeni_liste = []
            for satir in dosya_icerik:
                if isinstance(satir.get('tarih'), str):
                    satir['tarih'] = datetime.strptime(satir['tarih'], '%Y-%m-%d').date()
                yeni_liste.append(satir)
            
            # Belleği güncelle (Üzerine yazmak yerine mevcutla birleştirme opsiyonu açık)
            if st.button("📥 Yedeği Listeye Aktar"):
                st.session_state['portfoy'] = yeni_liste
                st.success("Yükleme Başarılı!")
                st.rerun()
        except:
            st.error("JSON dosyası okunamadı!")

    st.divider()
    if st.session_state['portfoy']:
        # İndirme hazırlığı
        indirme_hazirlik = []
        for p in st.session_state['portfoy']:
            k = p.copy()
            if hasattr(k['tarih'], 'strftime'): k['tarih'] = k['tarih'].strftime('%Y-%m-%d')
            indirme_hazirlik.append(k)
        st.download_button("📥 Portföyü Bilgisayara İndir", json.dumps(indirme_hazirlik), "yedek_portfoy.json")

# 3. ANA EKRAN: VERİ GİRİŞİ (HER ŞEY ALT ALTA - HİÇBİR ŞEY GİZLENEMEZ)
st.title("⚖️ Zenith Portföy Takip")
st.subheader("➕ Yeni Fon Girişi")

# Her kutu için benzersiz bir ID ve etiket
f_kod = st.text_input("1. FON KODU", key="in_kod").upper().strip()
f_tar = st.date_input("2. SATIN ALMA TARİHİ", key="in_tar")
f_adet = st.number_input("3. ADET (MİKTAR)", min_value=0.0, format="%.4f", key="in_adet")
f_alis = st.number_input("4. BİRİM ALIŞ FİYATI (TL)", min_value=0.0, format="%.4f", key="in_alis")
# Bu hücrenin kaybolma ihtimalini ortadan kaldırmak için ismini değiştirdik:
f_guncel = st.number_input("5. BUGÜNKÜ GÜNCEL BİRİM FİYAT (TL)", min_value=0.0, format="%.4f", key="in_guncel_deger")

if st.button("🚀 FONU LİSTEYE EKLE", use_container_width=True):
    if f_kod and f_adet > 0:
        # Geçmiş kuru çek
        t_str = f_tar.strftime('%Y-%m-%d')
        u_data = yf.download("USDTRY=X", start=t_str, end=(f_tar + timedelta(days=5)).strftime('%Y-%m-%d'), progress=False)
        u_eski = float(u_data['Close'].iloc[0]) if not u_data.empty else 1.0
        
        # Yeni veriyi paketle
        yeni_fon = {
            "kod": f_kod,
            "tarih": f_tar,
            "adet": f_adet,
            "maliyet": f_alis,
            "guncel": f_guncel if f_guncel > 0 else f_alis,
            "usd_old": u_eski
        }
        
        # Listeye ekle ve zorla yenile
        st.session_state['portfoy'].append(yeni_fon)
        st.success(f"{f_kod} Portföye Eklendi!")
        st.rerun()
    else:
        st.warning("Lütfen Fon Kodu ve Adet kısımlarını doldurunuz!")

st.divider()

# 4. TABLO VE HESAPLAR
if st.session_state['portfoy']:
    st.subheader("📋 Mevcut Fonlarınız")
    
    # Anlık kuru çek
    try:
        u_anlik = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    except:
        u_anlik = 1.0
    
    tablo_data = []
    for i, item in enumerate(st.session_state['portfoy']):
        m_toplam = item['adet'] * item['maliyet']
        g_toplam = item['adet'] * item['guncel']
        
        tablo_data.append({
            "FON": item['kod'],
            "TARİH": item['tarih'],
            "ADET": item['adet'],
            "TOPLAM MALİYET": f"{m_toplam:,.2f} TL",
            "GÜNCEL DEĞER": f"{g_toplam:,.2f} TL",
            "DOLAR FARKI ($)": f"{((g_toplam / u_anlik) - (m_toplam / item['usd_old'])):,.2f} $"
        })
        
        # SİLME BUTONU
        if st.button(f"🗑️ {item['kod']} Kaydını Sil", key=f"sil_{i}"):
            st.session_state['portfoy'].pop(i)
            st.rerun()

    # BASİT TABLO GÖSTERİMİ
    st.table(tablo_data)

else:
    st.info("Portföy listesi boş. Lütfen yukarıdaki kutuları doldurarak ekleme yapın.")

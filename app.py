import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Radar Conflitti", layout="wide")
st.title("🌍 Radar OSINT: Crimini di Guerra")

# INSERISCI QUI IL TUO LINK CSV
SHEET_CSV_URL = "INSERISCI_IL_LINK_CSV_QUI"

@st.cache_data(ttl=60)
def carica_dati():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        
        if len(df.columns) >= 5:
            df = df.iloc[:, :5] 
            df.columns = ["Bersaglio", "Vittime", "Latitudine", "Longitudine", "Paese"]
            
            # --- LA NOSTRA PULIZIA SALVAVITA ---
            # 1. Forza la conversione in numeri (se c'è testo o virgole, lo trasforma in NaN/Vuoto)
            df['Latitudine'] = pd.to_numeric(df['Latitudine'], errors='coerce')
            df['Longitudine'] = pd.to_numeric(df['Longitudine'], errors='coerce')
            
            # 2. Cancella tutte le righe che non hanno coordinate valide
            df = df.dropna(subset=['Latitudine', 'Longitudine'])
            
            return df
        else:
            st.error(f"Errore: il file ha solo {len(df.columns)} colonne.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return pd.DataFrame()

df = carica_dati()

if not df.empty:
    st.subheader("Mappa Topografica degli Attacchi")
    mappa = folium.Map(location=[30.0, 35.0], zoom_start=3, tiles='OpenTopoMap')
    
    for _, row in df.iterrows():
        popup_html = f"<b>{row['Paese']}</b><br>Bersaglio: {row['Bersaglio']}<br>Vittime: {row['Vittime']}"
        folium.CircleMarker(
            location=[row['Latitudine'], row['Longitudine']],
            radius=5 + (row['Vittime'] * 0.5),
            popup=folium.Popup(popup_html, max_width=200),
            color="red", fill=True, fill_opacity=0.7
        ).add_to(mappa)
        
    st_folium(mappa, width=1000, height=500)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("In attesa di dati validi. La mappa si aggiornerà a breve.")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configurazione pagina
st.set_page_config(page_title="Radar Conflitti", layout="wide")
st.title("🌍 Radar OSINT: Monitoraggio Conflitti Armati")
st.markdown("Dashboard in tempo reale per il monitoraggio di violazioni in zone di conflitto.")

# INSERISCI QUI IL TUO LINK CSV PUBBLICATO
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTIPelNU3xgAcJyfEs4FeqXofRMfECbIcncm6S9prheQzezaP-R2uRHQUHQ4OGKj-vPrGC2Ss0XWS8I/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def carica_dati():
    try:
        # Carica i dati
        df = pd.read_csv(SHEET_CSV_URL)
        
        # Verifica colonne minime
        if len(df.columns) >= 5:
            df = df.iloc[:, :5] 
            df.columns = ["Bersaglio", "Vittime", "Latitudine", "Longitudine", "Paese"]
            
            # PULIZIA DATI (virgola -> punto)
            for col in ['Latitudine', 'Longitudine']:
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Rimuoviamo righe senza coordinate valide
            df = df.dropna(subset=['Latitudine', 'Longitudine'])
            
            return df
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# Caricamento
df = carica_dati()

# Visualizzazione
if not df.empty:
    st.subheader("Mappa Topografica degli Attacchi")
    
    # Creazione mappa satellitare ad alta risoluzione (Esri World Imagery)
    mappa = folium.Map(
        location=[20.0, 30.0], 
        zoom_start=3, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )
    
    
    for _, row in df.iterrows():
        popup_html = f"""
        <div style="font-family: sans-serif;">
            <b>{row['Paese']}</b><br>
            Bersaglio: {row['Bersaglio']}<br>
            Vittime: <b style="color:red;">{row['Vittime']}</b>
        </div>
        """
        folium.CircleMarker(
            location=[row['Latitudine'], row['Longitudine']],
            radius=8 + (row['Vittime'] * 0.5),
            popup=folium.Popup(popup_html, max_width=200),
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.7
        ).add_to(mappa)
    
    st_folium(mappa, width=1000, height=500)
    
    # Tabella riassuntiva
    st.subheader("Elenco Eventi")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("In attesa di dati validi dal database. Verifica che lo script su GitHub sia attivo.")

import streamlit as st
import pandas as pd
import pydeck as pdk
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURAZIONE DELLA PAGINA ---
st.set_page_config(page_title="Radar Conflitti Globale", layout="wide")
st.title("🌍 Radar Conflitti OSINT (Centro Operativo Satellitare)")

# Recuperiamo la tua chiave segreta Mapbox dai Secrets di Streamlit
MAPBOX_KEY = st.secrets["MAPBOX_API_KEY"]

# --- FUNZIONE DI CARICAMENTO DATI ---
# Usiamo la cache per velocizzare il sito e non bloccare le API
@st.cache_data(ttl=60)
def carica_dati():
    # Connessione a Google Sheets usando i segreti di Streamlit
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    
    # INSERISCI QUI IL TUO ID ALFANUMERICO TRA LE VIRGOLETTE
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
    sheet = client.open_by_key(ID_FOGLIO).sheet1
    
    # Leggiamo tutto il foglio
    dati = sheet.get_all_values()
    
    # Controlliamo che ci siano dati oltre alla riga di intestazione
    if len(dati) > 1:
        # Creiamo il dataframe saltando la prima riga (i titoli delle colonne)
        df = pd.DataFrame(dati[1:], columns=["titolo", "vittime", "lat", "lon", "paese"])
        
        # Trasformiamo i dati in numeri veri e propri per permettere il 3D
        df['vittime'] = pd.to_numeric(df['vittime'], errors='coerce').fillna(2)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        
        # Puliamo eventuali righe danneggiate senza coordinate
        df = df.dropna(subset=['lat', 'lon'])
        return df
    else:
        # Ritorna una tabella vuota se non ci sono ancora eventi
        return pd.DataFrame()

# --- ESECUZIONE E VISTA 3D ---
df = carica_dati()

# Se il foglio è vuoto, avvisiamo l'utente
if df.empty:
    st.info("Nessun evento confermato al momento. Il sistema OSINT è in ascolto...")
else:
    st.write(f"Monitoraggio attivo: **{len(df)}** eventi critici confermati dalle agenzie internazionali. Generazione globo spaziale in corso...")

    # Impostiamo la telecamera del satellite (inclinata a 45 gradi per vedere il 3D)
    view_state = pdk.ViewState(
        latitude=20.0,
        longitude=30.0,
        zoom=2,
        pitch=45,
        bearing=0
    )

    # Creiamo i pilastri rossi tridimensionali
    layer_colonne = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation="vittime",
        elevation_scale=100000, # Regola l'altezza dei pilastri
        radius=50000,           # Regola lo spessore alla base
        get_fill_color=[255, 50, 50, 200], # Colore rosso radar trasparente
        pickable=True,
        auto_highlight=True,
    )

    # Uniamo il satellite Mapbox con i nostri dati e creiamo i popup al passaggio del mouse
    deck = pdk.Deck(
        layers=[layer_colonne],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/satellite-streets-v12", # Vista satellitare + nomi città
        api_keys={"mapbox": MAPBOX_KEY},
        tooltip={"text": "📍 {paese}\n\nEvento: {titolo}\n⚠️ Vittime stimate: {vittime}"}
    )

    # Proiettiamo tutto sulla dashboard
    st.pydeck_chart(deck)

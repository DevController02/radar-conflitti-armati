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

        # Creiamo i classici pallini rossi piatti al posto delle colonne
    layer_pallini = pdk.Layer(
        "ScatterplotLayer", # Il comando magico per i cerchi piatti
        data=df,
        get_position=["lon", "lat"],
        get_radius=50000, # Il raggio base del cerchio in metri
        radius_min_pixels=5, # Grandezza minima sullo schermo
        radius_max_pixels=30, # Grandezza massima quando fai zoom
        get_fill_color=[255, 50, 50, 200], # Colore rosso radar trasparente
        get_line_color=[255, 0, 0, 255], # Bordo rosso acceso
        line_width_min_pixels=1,
        stroked=True,
        pickable=True,
        auto_highlight=True,
    )

    # Assicurati di aggiornare anche la variabile dentro il Deck!
    deck = pdk.Deck(
        layers=[layer_pallini], # <-- Modifica qui inserendo layer_pallini
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/satellite-streets-v12", 
        api_keys={"mapbox": MAPBOX_KEY},
        tooltip={"text": "📍 {paese}\n\nEvento: {titolo}\n⚠️ Vittime stimate: {vittime}"}
    )
    
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

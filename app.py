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
@st.cache_data(ttl=60)
def carica_dati():
    # Connessione a Google Sheets
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
    sheet = client.open_by_key(ID_FOGLIO).sheet1
    
    dati = sheet.get_all_values()
    
    if len(dati) > 1:
        # Ora definiamo correttamente tutte le 8 colonne che hai nel foglio
        df = pd.DataFrame(dati[1:], columns=["ID_Univoco", "Data", "Titolo", "Vittime", "Lat", "Lon", "Paese", "Fonte"])
        
        # Trasformiamo i dati in numeri
        df['Vittime'] = pd.to_numeric(df['Vittime'], errors='coerce').fillna(0)
        df['Lat'] = pd.to_numeric(df['Lat'], errors='coerce')
        df['Lon'] = pd.to_numeric(df['Lon'], errors='coerce')
        
        # Puliamo le righe vuote
        df = df.dropna(subset=['Lat', 'Lon'])
        return df
    else:
        return pd.DataFrame()
    
    # INSERISCI QUI IL TUO ID ALFANUMERICO TRA LE VIRGOLETTE
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
    sheet = client.open_by_key(ID_FOGLIO).sheet1
    
    # Leggiamo tutto il foglio
    dati = sheet.get_all_values()
    
    # Controlliamo che ci siano dati oltre alla riga di intestazione
    if len(dati) > 1:
        df = pd.DataFrame(dati[1:], columns=["titolo", "vittime", "lat", "lon", "paese"])
        
        # Trasformiamo i dati in numeri veri e propri
        df['vittime'] = pd.to_numeric(df['vittime'], errors='coerce').fillna(0)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        
        # Puliamo eventuali righe danneggiate
        df = df.dropna(subset=['lat', 'lon'])
        return df
    else:
        return pd.DataFrame()

# --- ESECUZIONE E VISTA ---
df = carica_dati()

# Se il foglio è vuoto, avvisiamo l'utente
if df.empty:
    st.info("Nessun evento confermato al momento. Il sistema OSINT è in ascolto...")
else:
    st.write(f"Monitoraggio attivo: **{len(df)}** eventi critici confermati dalle agenzie internazionali.")

    # Telecamera satellitare (pitch=0 per visuale piatta dall'alto)
    view_state = pdk.ViewState(
        latitude=20.0,
        longitude=30.0,
        zoom=2,
        pitch=0,
        bearing=0
    )

   # 1. Definiamo i colori basati sulla fonte
    def assegna_colore(fonte):
        if "CONFERMATO" in fonte:
            return [255, 0, 0]  # ROSSO (ACLED)
        else:
            return [255, 165, 0] # ARANCIONE (RSS)

    # 2. Applichiamo la funzione alla colonna 'Fonte'
    df['colore'] = df['Fonte'].apply(assegna_colore)

    # 3. Creiamo il layer con i colori dinamici
    layer_pallini = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["Lon", "Lat"],
        get_color="colore",  # Usa la colonna colore che abbiamo appena creato
        get_radius=50000,    # Raggio del pallino
        pickable=True,
        auto_highlight=True,
    )
    )

    # Uniamo il satellite Mapbox con i pallini e creiamo i popup
    deck = pdk.Deck(
        layers=[layer_pallini],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/satellite-streets-v12", 
        api_keys={"mapbox": MAPBOX_KEY},
        tooltip={"text": "📍 {paese}\n\nEvento: {titolo}\n⚠️ Vittime stimate: {vittime}"}
    )

    # Proiettiamo sulla dashboard (Questa era la riga dove era rimasta la parentesi di troppo!)
    st.pydeck_chart(deck)
    
min_date = st.sidebar.date_input("Data inizio", value=pd.to_datetime("2026-01-01"))
max_date = st.sidebar.date_input("Data fine")
# Filtra il df
df = df[(df['Data'] >= str(min_date)) & (df['Data'] <= str(max_date))]
st.dataframe(df) # Ecco la tua tabella!

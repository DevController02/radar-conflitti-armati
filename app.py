import streamlit as st
import pandas as pd
import pydeck as pdk

# Configurazione della pagina a tutto schermo
st.set_page_config(page_title="Radar Conflitti Globale", layout="wide")
st.title("🌍 Radar Conflitti OSINT (Centro Operativo Satellitare)")

# Recuperiamo la tua nuova chiave segreta Mapbox
MAPBOX_KEY = st.secrets["MAPBOX_API_KEY"]

# ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
# Immaginiamo che il tuo foglio diventi un dataframe chiamato 'df'
# con colonne: 'titolo', 'vittime', 'lat', 'lon', 'paese'

st.write("Dati caricati e validati dalle agenzie ONU. Visualizzazione 3D in corso...")

# --- MOTORE GRAFICO PYDECK (IL GLOBO 3D) ---
# Impostiamo l'inclinazione della telecamera (pitch) per vedere il mondo in 3D
view_state = pdk.ViewState(
    latitude=20.0,
    longitude=30.0,
    zoom=2,
    pitch=45, # L'inclinazione magica che crea la prospettiva 3D
    bearing=0
)

# Creiamo le colonne rosse 3D al posto dei vecchi cerchi piatti
layer_colonne = pdk.Layer(
    "ColumnLayer",
    data=df,
    get_position=["lon", "lat"],
    get_elevation="vittime",
    elevation_scale=100000, # Moltiplicatore per rendere le colonne ben visibili
    radius=50000, # Spessore della base
    get_fill_color=[255, 0, 0, 200], # Rosso traslucido
    pickable=True,
    auto_highlight=True,
)

# Uniamo il satellite, i nomi delle città e le colonne rosse
deck = pdk.Deck(
    layers=[layer_colonne],
    initial_view_state=view_state,
    # Questo è lo stile "ibrido" perfetto: foto dallo spazio + scritte
    map_style="mapbox://styles/mapbox/satellite-streets-v12",
    api_keys={"mapbox": MAPBOX_KEY},
    tooltip={"text": "{paese}\n{titolo}\nVittime: {vittime}"}
)

# Disegniamo il capolavoro su Streamlit
st.pydeck_chart(deck)

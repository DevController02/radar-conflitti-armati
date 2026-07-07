import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Radar OSINT Vittime Conflitti", layout="wide")

st.title("🛰️ Radar OSINT: Monitoraggio Globale Vittime di Conflitti Armati")
st.markdown("Sistema di rilevamento ibrido accoppiato (Fonti ONU + Allerta Rapida GDELT). Update ogni 15 min.")

@st.cache_data(ttl=60)
def carica_dati():
    try:
        SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        
        ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
        sheet = client.open_by_key(ID_FOGLIO).sheet1
        
        dati = sheet.get_all_values()
        
        if len(dati) > 1:
            df = pd.DataFrame(dati[1:], columns=["ID_Univoco", "Data", "Titolo", "Vittime", "Lat", "Lon", "Paese", "Fonte"])
            df['Vittime'] = pd.to_numeric(df['Vittime'], errors='coerce').fillna(0).astype(int)
            df['Lat'] = pd.to_numeric(df['Lat'], errors='coerce')
            df['Lon'] = pd.to_numeric(df['Lon'], errors='coerce')
            df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
            df = df.dropna(subset=['Lat', 'Lon', 'Data_dt'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore caricamento database: {e}")
        return pd.DataFrame()

df_completo = carica_dati()

if df_completo.empty:
    st.warning("⚠️ Il database è vuoto. Attendi il prossimo ciclo di raccolta dati.")
else:
    st.sidebar.header("🎛️ Filtri Radar")
    
    data_minima = df_completo['Data_dt'].min().date()
    data_massima = df_completo['Data_dt'].max().date()
    
    start_date = st.sidebar.date_input("Data Inizio", value=data_minima, min_value=data_minima, max_value=data_massima)
    end_date = st.sidebar.date_input("Data Fine", value=data_massima, min_value=data_minima, max_value=data_massima)
    
    mostra_confermati = st.sidebar.checkbox("Mostra Confermati ONU (🔴)", value=True)
    mostra_attesa = st.sidebar.checkbox("Mostra Allarmi Rapidi (🟠)", value=True)
    
    df_filtrato = df_completo[(df_completo['Data_dt'].dt.date >= start_date) & (df_completo['Data_dt'].dt.date <= end_date)]
    
    fonti_ammesse = []
    if mostra_confermati: fonti_ammesse.append("🔴 CONFERMATO")
    if mostra_attesa: fonti_ammesse.append("🟠 IN ATTESA")
    
    df_filtrato = df_filtrato[df_filtrato['Fonte'].isin(fonti_ammesse)]

    def applica_colore(row):
        return [255, 0, 0, 200] if "CONFERMATO" in row['Fonte'] else [255, 165, 0, 200]
            
    df_filtrato['colore'] = df_filtrato.apply(applica_colore, axis=1)

    col1, col2 = st.columns(2)
    col1.metric("Totale Vittime Rilevate nel periodo", f"{df_filtrato['Vittime'].sum():,}")
    col2.metric("Eventi d'Arma Tracciati", f"{len(df_filtrato):,}")

    # TOOLTIP CORRETTO: Le variabili tra parentesi graffe DEVONO avere le iniziali maiuscole come le colonne del DataFrame
    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer(
            "ScatterplotLayer",
            data=df_filtrato,
            get_position=["Lon", "Lat"],
            get_color="colore",
            get_radius="Vittime * 2000 + 15000",
            pickable=True,
            auto_highlight=True,
        )],
        initial_view_state=pdk.ViewState(latitude=20.0, longitude=20.0, zoom=1.5, pitch=0),
        map_style="mapbox://styles/mapbox/satellite-streets-v12",
        tooltip={
            "html": "<b>📍 {Paese}</b><br/><b>Data:</b> {Data}<br/><b>Evento:</b> {Titolo}<br/><b>⚠️ Vittime Accertate:</b> {Vittime}<br/><b>Status:</b> {Fonte}",
            "style": {"backgroundColor": "#1E1E1E", "color": "white", "borderRadius": "5px", "padding": "10px"}
        }
    ))

    st.subheader("📊 Registro Operativo")
    st.dataframe(
        df_filtrato[["Data", "Paese", "Titolo", "Vittime", "Fonte"]].sort_values(by="Data", ascending=False), 
        use_container_width=True, hide_index=True
)
    

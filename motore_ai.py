import os
import json
import requests
import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

print("--- Avvio Motore Intelligence Ibrido (ACLED + RSS) ---")

# --- 1. CONFIGURAZIONE E AUTH ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(creds)
ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
sheet = client.open_by_key(ID_FOGLIO).sheet1

# Sessione per ACLED
session = requests.Session()
login_url = "https://acleddata.com/login" # Assicurati che sia l'URL corretto del loro login
payload = {
    'username': os.environ.get("ACLED_USERNAME"),
    'password': os.environ.get("ACLED_PASSWORD")
}
session.post(login_url, data=payload)

# --- 2. LOGICA ID UNIVOCO ---
def genera_id(data, lat, lon):
    # Crea una chiave univoca: es "2026-07-06_15.5_32.5"
    return f"{data}_{round(float(lat), 2)}_{round(float(lon), 2)}"

# Carichiamo gli ID esistenti per evitare doppioni
ids_esistenti = sheet.col_values(1) 
nuove_righe = []

# --- 3. FETCH DATI ACLED ---
print("Scaricamento dati ACLED...")
try:
    # Limitato a 50 eventi per evitare crash
    acled_url = "https://acleddata.com/api/acled/read?limit=50" 
    response = session.get(acled_url)
    if response.status_code == 200:
        dati_acled = response.json().get('data', [])
        for evento in dati_acled:
            data = evento.get('event_date')
            lat = evento.get('latitude')
            lon = evento.get('longitude')
            titolo = evento.get('event_type') + " - " + evento.get('location')
            vittime = evento.get('fatalities', 0)
            paese = evento.get('country')
            
            uid = genera_id(data, lat, lon)
            
            if uid not in ids_esistenti:
                nuove_righe.append([uid, data, titolo, vittime, lat, lon, paese, "ACLED"])
                ids_esistenti.append(uid)
except Exception as e:
    print(f"Errore ACLED: {e}")

# --- 4. FETCH DATI RSS (Fonti Umanitarie) ---
FONTI_RSS = ["https://reliefweb.int/updates/rss.xml", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"]
print("Scansione RSS...")

for url in FONTI_RSS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:10]:
        data = datetime.now().strftime("%Y-%m-%d") # RSS spesso non hanno data precisa, usiamo oggi
        lat, lon = 0.0, 0.0 # Qui dovresti aggiungere logica per estrarre lat/lon dal titolo se vuoi precisione
        titolo = entry.title
        vittime = 0 
        paese = "Global/Vario"
        
        uid = genera_id(data, lat, lon)
        
        if uid not in ids_esistenti:
            nuove_righe.append([uid, data, titolo, vittime, lat, lon, paese, "RSS"])
            ids_esistenti.append(uid)

# --- 5. SCRITTURA BATCH ---
if nuove_righe:
    sheet.append_rows(nuove_righe)
    print(f"✅ Aggiunti {len(nuove_righe)} nuovi eventi.")
else:
    print("Nessun nuovo evento da aggiungere.")

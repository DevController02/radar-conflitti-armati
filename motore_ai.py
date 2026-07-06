import os
import json
import requests
import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURAZIONE ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(creds)
ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
sheet = client.open_by_key(ID_FOGLIO).sheet1

# Sessione ACLED
session = requests.Session()
session.post("https://acleddata.com/login", data={
    'username': os.environ.get("ACLED_USERNAME"),
    'password': os.environ.get("ACLED_PASSWORD")
})

def genera_id(data, lat, lon):
    return f"{data}_{round(float(lat), 2)}_{round(float(lon), 2)}"

# Carichiamo esistenti
ids_esistenti = sheet.col_values(1)
nuove_righe = []

# --- 1. MOTORE ACLED (Dati Certificati) ---
try:
    response = session.get("https://acleddata.com/api/acled/read?limit=50")
    if response.status_code == 200:
        for evento in response.json().get('data', []):
            vittime = int(evento.get('fatalities', 0))
            if vittime > 0: # FILTRO RIGIDO: Solo eventi con vittime
                uid = genera_id(evento['event_date'], evento['latitude'], evento['longitude'])
                if uid not in ids_esistenti:
                    nuove_righe.append([uid, evento['event_date'], evento['event_type'], vittime, evento['latitude'], evento['longitude'], evento['country'], "🔴 CONFERMATO"])
                    ids_esistenti.append(uid)
except: pass

# --- 2. MOTORE RSS (Input rapido) ---
FONTI_RSS = ["https://reliefweb.int/updates/rss.xml", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"]
for url in FONTI_RSS:
    for entry in feedparser.parse(url).entries[:10]:
        # Cerca numeri nel testo per estrarre vittime
        import re
        match = re.search(r'(\d+)\s*(killed|dead|vittime|morti)', entry.title.lower() + entry.summary.lower())
        vittime = int(match.group(1)) if match else 0
        
        if vittime > 0: # FILTRO RIGIDO: Scarta tutto ciò che non ha vittime
            # (Qui dovresti aggiungere logica per estrarre lat/lon dal testo se presente)
            lat, lon = 0.0, 0.0 
            uid = genera_id(datetime.now().strftime("%Y-%m-%d"), lat, lon)
            if uid not in ids_esistenti:
                nuove_righe.append([uid, datetime.now().strftime("%Y-%m-%d"), entry.title, vittime, lat, lon, "Global", "🟠 IN ATTESA"])
                ids_esistenti.append(uid)

# --- 3. SCRITTURA ---
if nuove_righe:
    sheet.append_rows(nuove_righe)

import os
import json
import requests
import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

print("--- Avvio Radar OSINT Globale (Con Scudo Anti-Calamità e Burocrazia) ---")

# --- LISTA NERA: SCUDO ANTI-DISASTRI, ANTI-BUROCRAZIA E MULTILINGUA ---
# Qualsiasi notizia che contenga una di queste parole verrà scartata immediatamente.
PAROLE_VIETATE = [
    # Disastri Naturali (Inglese)
    "quake", "earthquake", "tsunami", "flood", "hurricane", "storm", "cyclone", "typhoon", "tornado",
    "landslide", "mudslide", "volcano", "eruption", "wildfire", "fire", "accident", "crash", 
    "collision", "derailment", "disease", "virus", "outbreak", "cancer", "covid", "ebola", 
    "cholera", "malaria", "dengue", "famine", "drought",
    
    # Disastri Naturali (Spagnolo, Francese, Italiano)
    "terremoto", "terremotos", "sismo", "inundacion", "inondation", "ouragan", "séisme", "seisme", "alluvione",
    
    # Intrattenimento e Fake News
    "movie", "film", "game", "trailer", "simulation", "anniversary", "zombie", "actor", "hollywood", "fiction",
    
    # Burocrazia, Riassunti Logistici e Tracciamento Profughi (Che generano falsi positivi)
    "displacement", "refugee", "unicef", "ifrc", "council", "meeting", "procedimiento", "procedure", 
    "hospital", "brief", "briefing", "session", "resolution", "funding", "donor", "appeal", "tracking",
    "overview", "response plan", "standard operating", "rescuers"
]

# --- 1. CONFIGURAZIONE DATABASE ---
try:
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
    sheet = client.open_by_key(ID_FOGLIO).sheet1
    ids_esistenti = sheet.col_values(1)
except Exception as e:
    print(f"Errore fatale connessione Google Sheets: {e}")
    exit()

nuove_righe = []

def genera_id(data, lat, lon, titolo=""):
    titolo_pulito = "".join(e for e in titolo[:10] if e.isalnum())
    return f"{data}_{round(float(lat), 2)}_{round(float(lon), 2)}_{titolo_pulito}"

# DIZIONARIO GLOBALE - 195 STATI
DIZIONARIO_STATI = {
    "afghanistan": {"lat": 33.93, "lon": 67.70, "paese": "Afghanistan"}, "albania": {"lat": 41.15, "lon": 20.16, "paese": "Albania"},
    "algeria": {"lat": 28.03, "lon": 1.65, "paese": "Algeria"}, "andorra": {"lat": 42.50, "lon": 1.52, "paese": "Andorra"},
    "angola": {"lat": -11.20, "lon": 17.87, "paese": "Angola"}, "argentina": {"lat": -38.41, "lon": -63.61, "paese": "Argentina"},
    "armenia": {"lat": 40.06, "lon": 45.03, "paese": "Armenia"}, "australia": {"lat": -25.27, "lon": 133.77, "paese": "Australia"},
    "austria": {"lat": 47.51, "lon": 14.55, "paese": "Austria"}, "azerbaijan": {"lat": 40.14, "lon": 47.57, "paese": "Azerbaijan"},
    "bahamas": {"lat": 25.03, "lon": -77.39, "paese": "Bahamas"}, "bahrain": {"lat": 25.93, "lon": 50.63, "paese": "Bahrain"},
    "bangladesh": {"lat": 23.68, "lon": 90.35, "paese": "Bangladesh"}, "belarus": {"lat": 53.70, "lon": 27.95, "paese": "Belarus"},
    "belgium": {"lat": 50.50, "lon": 4.46, "paese": "Belgium"}, "bolivia": {"lat": -16.29, "lon": -63.58, "paese": "Bolivia"},
    "bosnia": {"lat": 43.91, "lon": 17.67, "paese": "Bosnia and Herzegovina"}, "botswana": {"lat": -22.32, "lon": 24.68, "paese": "Botswana"},
    "brazil": {"lat": -14.23, "lon": -51.92, "paese": "Brazil"}, "bulgaria": {"lat": 42.73, "lon": 25.48, "paese": "Bulgaria"},
    "burkina faso": {"lat": 12.23, "lon": -1.56, "paese": "Burkina Faso"}, "burundi": {"lat": -3.37, "lon": 29.91, "paese": "Burundi"},
    "cambodia": {"lat": 12.56, "lon": 104.99, "paese": "Cambodia"}, "cameroon": {"lat": 7.36, "lon": 12.35, "paese": "Cameroon"},
    "canada": {"lat": 56.13, "lon": -106.34, "paese": "Canada"}, "central african republic": {"lat": 6.61, "lon": 20.93, "paese": "Central African Republic"},
    "chad": {"lat": 15.45, "lon": 18.73, "paese": "Chad"}, "chile": {"lat": -35.67, "lon": -71.54, "paese": "Chile"},
    "china": {"lat": 35.86, "lon": 104.19, "paese": "China"}, "colombia": {"lat": 4.57, "lon": -74.29, "paese": "Colombia"},
    "congo": {"lat": -4.03, "lon": 21.75, "paese": "DR Congo"}, "drc": {"lat": -4.03, "lon": 21.75, "paese": "DR Congo"},
    "costa rica": {"lat": 9.74, "lon": -83.75, "paese": "Costa Rica"}, "croatia": {"lat": 45.10, "lon": 15.20, "paese": "Croatia"},
    "cuba": {"lat": 21.52, "lon": -77.78, "paese": "Cuba"}, "cyprus": {"lat": 35.12, "lon": 33.42, "paese": "Cyprus"},
    "czechia": {"lat": 49.81, "lon": 15.47, "paese": "Czech Republic"}, "denmark": {"lat": 56.26, "lon": 9.50, "paese": "Denmark"},
    "djibouti": {"lat": 11.82, "lon": 42.59, "paese": "Djibouti"}, "ecuador": {"lat": -1.83, "lon": -78.18, "paese": "Ecuador"},
    "egypt": {"lat": 26.82, "lon": 30.80, "paese": "Egypt"}, "el salvador": {"lat": 13.79, "lon": -88.89, "paese": "El Salvador"},
    "eritrea": {"lat": 15.17, "lon": 39.78, "paese": "Eritrea"}, "estonia": {"lat": 58.59, "lon": 25.01, "paese": "Estonia"},
    "ethiopia": {"lat": 9.14, "lon": 40.48, "paese": "Ethiopia"}, "finland": {"lat": 61.92, "lon": 25.74, "paese": "Finland"},
    "france": {"lat": 46.22, "lon": 2.21, "paese": "France"}, "gabon": {"lat": -0.80, "lon": 11.60, "paese": "Gabon"},
    "georgia": {"lat": 42.31, "lon": 43.35, "paese": "Georgia"}, "germany": {"lat": 51.16, "lon": 10.45, "paese": "Germany"},
    "ghana": {"lat": 7.94, "lon": -1.02, "paese": "Ghana"}, "greece": {"lat": 39.07, "lon": 21.82, "paese": "Greece"},
    "guatemala": {"lat": 15.78, "lon": -90.23, "paese": "Guatemala"}, "haiti": {"lat": 18.97, "lon": -72.28, "paese": "Haiti"},
    "honduras": {"lat": 15.19, "lon": -86.24, "paese": "Honduras"}, "hungary": {"lat": 47.16, "lon": 19.50, "paese": "Hungary"},
    "india": {"lat": 20.59, "lon": 78.96, "paese": "India"}, "indonesia": {"lat": -0.78, "lon": 113.92, "paese": "Indonesia"},
    "iran": {"lat": 32.42, "lon": 53.68, "paese": "Iran"}, "iraq": {"lat": 33.22, "lon": 43.67, "paese": "Iraq"},
    "ireland": {"lat": 53.41, "lon": -8.24, "paese": "Ireland"}, "israel": {"lat": 31.04, "lon": 34.85, "paese": "Israel"},
    "italy": {"lat": 41.87, "lon": 12.56, "paese": "Italy"}, "japan": {"lat": 36.20, "lon": 138.25, "paese": "Japan"},
    "jordan": {"lat": 30.58, "lon": 36.23, "paese": "Jordan"}, "kazakhstan": {"lat": 48.01, "lon": 66.92, "paese": "Kazakhstan"},
    "kenya": {"lat": -0.02, "lon": 37.90, "paese": "Kenya"}, "kuwait": {"lat": 29.31, "lon": 47.48, "paese": "Kuwait"},
    "kyrgyzstan": {"lat": 41.20, "lon": 74.76, "paese": "Kyrgyzstan"}, "lebanon": {"lat": 33.85, "lon": 35.86, "paese": "Lebanon"},
    "libya": {"lat": 26.33, "lon": 17.22, "paese": "Libya"}, "lithuania": {"lat": 55.16, "lon": 23.88, "paese": "Lithuania"},
    "madagascar": {"lat": -18.76, "lon": 46.86, "paese": "Madagascar"}, "mali": {"lat": 17.57, "lon": -3.99, "paese": "Mali"},
    "mexico": {"lat": 23.63, "lon": -102.55, "paese": "Mexico"}, "morocco": {"lat": 31.79, "lon": -7.09, "paese": "Morocco"},
    "myanmar": {"lat": 21.91, "lon": 95.95, "paese": "Myanmar"}, "burma": {"lat": 21.91, "lon": 95.95, "paese": "Myanmar"},
    "netherlands": {"lat": 52.13, "lon": 5.29, "paese": "Netherlands"}, "new zealand": {"lat": -40.90, "lon": 174.88, "paese": "New Zealand"},
    "niger": {"lat": 17.60, "lon": 8.08, "paese": "Niger"}, "nigeria": {"lat": 9.08, "lon": 8.67, "paese": "Nigeria"},
    "north korea": {"lat": 40.33, "lon": 127.51, "paese": "North Korea"}, "norway": {"lat": 60.47, "lon": 8.46, "paese": "Norway"},
    "oman": {"lat": 21.51, "lon": 55.92, "paese": "Oman"}, "pakistan": {"lat": 30.37, "lon": 69.34, "paese": "Pakistan"},
    "palestine": {"lat": 31.95, "lon": 35.23, "paese": "Palestine"}, "gaza": {"lat": 31.35, "lon": 34.30, "paese": "Palestine"},
    "panama": {"lat": 8.53, "lon": -80.78, "paese": "Panama"}, "peru": {"lat": -9.18, "lon": -75.01, "paese": "Peru"},
    "philippines": {"lat": 12.87, "lon": 121.77, "paese": "Philippines"}, "poland": {"lat": 51.91, "lon": 19.14, "paese": "Poland"},
    "portugal": {"lat": 39.39, "lon": -8.22, "paese": "Portugal"}, "qatar": {"lat": 25.35, "lon": 51.18, "paese": "Qatar"},
    "romania": {"lat": 45.94, "lon": 24.96, "paese": "Romania"}, "russia": {"lat": 61.52, "lon": 105.31, "paese": "Russia"},
    "rwanda": {"lat": -1.94, "lon": 29.87, "paese": "Rwanda"}, "saudi arabia": {"lat": 23.88, "lon": 45.07, "paese": "Saudi Arabia"},
    "senegal": {"lat": 14.49, "lon": -14.45, "paese": "Senegal"}, "serbia": {"lat": 44.01, "lon": 21.00, "paese": "Serbia"},
    "somalia": {"lat": 5.15, "lon": 46.19, "paese": "Somalia"}, "south africa": {"lat": -30.55, "lon": 22.93, "paese": "South Africa"},
    "south korea": {"lat": 35.90, "lon": 127.76, "paese": "South Korea"}, "south sudan": {"lat": 6.87, "lon": 31.30, "paese": "South Sudan"},
    "spain": {"lat": 40.46, "lon": -3.74, "paese": "Spain"}, "sri lanka": {"lat": 7.87, "lon": 80.77, "paese": "Sri Lanka"},
    "sudan": {"lat": 12.86, "lon": 30.21, "paese": "Sudan"}, "sweden": {"lat": 60.12, "lon": 18.64, "paese": "Sweden"},
    "switzerland": {"lat": 46.81, "lon": 8.22, "paese": "Switzerland"}, "syria": {"lat": 34.80, "lon": 38.99, "paese": "Syria"},
    "taiwan": {"lat": 23.69, "lon": 120.96, "paese": "Taiwan"}, "thailand": {"lat": 15.87, "lon": 100.99, "paese": "Thailand"},
    "tunisia": {"lat": 33.88, "lon": 9.53, "paese": "Tunisia"}, "turkey": {"lat": 38.96, "lon": 35.24, "paese": "Turkey"},
    "uganda": {"lat": 1.37, "lon": 32.29, "paese": "Uganda"}, "ukraine": {"lat": 48.37, "lon": 31.16, "paese": "Ukraine"},
    "united arab emirates": {"lat": 23.42, "lon": 53.84, "paese": "United Arab Emirates"}, 
    "united kingdom": {"lat": 55.37, "lon": -3.43, "paese": "United Kingdom"}, "uk": {"lat": 55.37, "lon": -3.43, "paese": "United Kingdom"},
    "united states": {"lat": 37.09, "lon": -95.71, "paese": "United States"}, "usa": {"lat": 37.09, "lon": -95.71, "paese": "United States"},
    "venezuela": {"lat": 6.42, "lon": -66.58, "paese": "Venezuela"}, "vietnam": {"lat": 14.05, "lon": 108.27, "paese": "Vietnam"},
    "yemen": {"lat": 15.55, "lon": 48.51, "paese": "Yemen"}, "zimbabwe": {"lat": -19.01, "lon": 29.15, "paese": "Zimbabwe"}
}

# --- 2. MOTORE ISTITUZIONALE ONU ---
print("Scansione fonti ufficiali Nazioni Unite / ReliefWeb...")
FONTI_ONU = [
    "https://reliefweb.int/updates/rss.xml",
    "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
]

try:
    for url in FONTI_ONU:
        feed = feedparser.parse(url)
        for entry in feed.entries[:25]:
            testo = (entry.title + " " + getattr(entry, 'summary', '')).lower()
            
            # Applichiamo lo Scudo Anti-Disastri e Anti-Burocrazia
            if "?" in entry.title or any(word in testo for word in PAROLE_VIETATE): 
                continue
            
            vittime = 0
            match = re.search(r'(\d+)', testo)
            if match:
                vittime = int(match.group(1))
                
            if vittime == 0 and any(w in testo for w in ["killed", "dead", "vittime", "morti", "casualties"]):
                vittime = 1
                
            if vittime == 0 or vittime > 1000:
                continue
                
            lat, lon, paese_rilevato = None, None, None
            for chiave, dati_geo in DIZIONARIO_STATI.items():
                if re.search(r'\b' + re.escape(chiave) + r'\b', testo):
                    lat, lon, paese_rilevato = dati_geo["lat"], dati_geo["lon"], dati_geo["paese"]
                    break

            if lat is not None and lon is not None:
                uid = genera_id(datetime.now().strftime("%Y-%m-%d"), lat, lon, entry.title)
                if uid not in ids_esistenti:
                    titolo_breve = entry.title[:70] + "..."
                    nuove_righe.append([uid, datetime.now().strftime("%Y-%m-%d"), titolo_breve, vittime, lat, lon, paese_rilevato, "🔴 CONFERMATO"])
                    ids_esistenti.append(uid)
except Exception as e:
    print(f"Errore lettura feed ONU: {e}")

# --- 3. MOTORE GDELT AI (Allerta Rapida) ---
print("Scansione GDELT AI (Rete a strascico mondiale)...")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Aggiunti termini militari per forzare GDELT a cercare SOLO violenza cinetica
    params = {
        "query": "(killed OR casualties OR fatalities OR dead OR deaths) (attack OR strike OR clash OR armed OR bombing OR military OR combat OR gunfire OR artillery)",
        "mode": "artlist",
        "maxrecords": "50",
        "format": "json",
        "sort": "datedesc"
    }
    
    # Timeout allungato a 45 secondi per superare i blocchi di rete
    req_gdelt = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, headers=headers, timeout=45)
    
    if req_gdelt.status_code == 200:
        articoli = req_gdelt.json().get('articles', [])
        
        for art in articoli:
            titolo = art.get('title', '')
            titolo_lower = titolo.lower()
            
            # Applichiamo lo Scudo Anti-Disastri e Anti-Burocrazia anche qui
            if "?" in titolo or any(word in titolo_lower for word in PAROLE_VIETATE):
                continue

            vittime = 0
            match = re.search(r'(\d+)', titolo_lower)
            if match:
                vittime = int(match.group(1))
            if vittime == 0 and any(w in titolo_lower for w in ["killed", "dead", "vittime", "morti", "casualties", "deaths"]):
                vittime = 1
                
            if vittime == 0 or vittime > 1000:
                continue
                
            lat, lon, paese_rilevato = None, None, None
            for chiave, dati_geo in DIZIONARIO_STATI.items():
                if re.search(r'\b' + re.escape(chiave) + r'\b', titolo_lower):
                    lat, lon, paese_rilevato = dati_geo["lat"], dati_geo["lon"], dati_geo["paese"]
                    break

            if lat is not None and lon is not None:
                uid = genera_id(datetime.now().strftime("%Y-%m-%d"), lat, lon, titolo)
                if uid not in ids_esistenti:
                    titolo_breve = titolo[:70] + "..."
                    nuove_righe.append([uid, datetime.now().strftime("%Y-%m-%d"), titolo_breve, vittime, lat, lon, paese_rilevato, "🟠 IN ATTESA"])
                    ids_esistenti.append(uid)
except Exception as e:
    print(f"Errore GDELT: {e}")

# --- 4. SALVATAGGIO ---
if nuove_righe:
    sheet.append_rows(nuove_righe)
    print(f"Scrittura di {len(nuove_righe)} eventi sul database.")
else:
    print("Nessun nuovo evento ha superato tutti i filtri.")

# --- 5. PULIZIA AUTOMATICA (7 Giorni solo per IN ATTESA) ---
try:
    dati_foglio = sheet.get_all_values()
    oggi = datetime.now()
    righe_da_eliminare = []
    for i, row in enumerate(dati_foglio):
        if i == 0: continue
        if len(row) >= 8 and "IN ATTESA" in row[7]:
            try:
                if (oggi - datetime.strptime(row[1], "%Y-%m-%d")).days > 7:
                    righe_da_eliminare.append(i + 1)
            except: pass
    for riga in sorted(righe_da_eliminare, reverse=True):
        sheet.delete_rows(riga)
except: pass

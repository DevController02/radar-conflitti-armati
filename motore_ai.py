import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

print("--- Avvio Radar OSINT Globale (195 Stati) ---")

# --- 1. CONFIGURAZIONE DATABASE ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(creds)
ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
sheet = client.open_by_key(ID_FOGLIO).sheet1

# Login ACLED
session = requests.Session()
session.post("https://acleddata.com/login", data={
    'username': os.environ.get("ACLED_USERNAME"),
    'password': os.environ.get("ACLED_PASSWORD")
})

# DIZIONARIO GLOBALE - 195 STATI + Varianti Geopolitiche
DIZIONARIO_STATI = {
    "afghanistan": {"lat": 33.93, "lon": 67.70, "paese": "Afghanistan"},
    "albania": {"lat": 41.15, "lon": 20.16, "paese": "Albania"},
    "algeria": {"lat": 28.03, "lon": 1.65, "paese": "Algeria"},
    "andorra": {"lat": 42.50, "lon": 1.52, "paese": "Andorra"},
    "angola": {"lat": -11.20, "lon": 17.87, "paese": "Angola"},
    "antigua and barbuda": {"lat": 17.06, "lon": -61.79, "paese": "Antigua and Barbuda"},
    "argentina": {"lat": -38.41, "lon": -63.61, "paese": "Argentina"},
    "armenia": {"lat": 40.06, "lon": 45.03, "paese": "Armenia"},
    "australia": {"lat": -25.27, "lon": 133.77, "paese": "Australia"},
    "austria": {"lat": 47.51, "lon": 14.55, "paese": "Austria"},
    "azerbaijan": {"lat": 40.14, "lon": 47.57, "paese": "Azerbaijan"},
    "bahamas": {"lat": 25.03, "lon": -77.39, "paese": "Bahamas"},
    "bahrain": {"lat": 25.93, "lon": 50.63, "paese": "Bahrain"},
    "bangladesh": {"lat": 23.68, "lon": 90.35, "paese": "Bangladesh"},
    "barbados": {"lat": 13.19, "lon": -59.54, "paese": "Barbados"},
    "belarus": {"lat": 53.70, "lon": 27.95, "paese": "Belarus"},
    "belgium": {"lat": 50.50, "lon": 4.46, "paese": "Belgium"},
    "belize": {"lat": 17.18, "lon": -88.49, "paese": "Belize"},
    "benin": {"lat": 9.30, "lon": 2.31, "paese": "Benin"},
    "bhutan": {"lat": 27.51, "lon": 90.43, "paese": "Bhutan"},
    "bolivia": {"lat": -16.29, "lon": -63.58, "paese": "Bolivia"},
    "bosnia": {"lat": 43.91, "lon": 17.67, "paese": "Bosnia and Herzegovina"},
    "botswana": {"lat": -22.32, "lon": 24.68, "paese": "Botswana"},
    "brazil": {"lat": -14.23, "lon": -51.92, "paese": "Brazil"},
    "brunei": {"lat": 4.53, "lon": 114.72, "paese": "Brunei"},
    "bulgaria": {"lat": 42.73, "lon": 25.48, "paese": "Bulgaria"},
    "burkina faso": {"lat": 12.23, "lon": -1.56, "paese": "Burkina Faso"},
    "burundi": {"lat": -3.37, "lon": 29.91, "paese": "Burundi"},
    "côte d'ivoire": {"lat": 7.53, "lon": -5.54, "paese": "Ivory Coast"},
    "ivory coast": {"lat": 7.53, "lon": -5.54, "paese": "Ivory Coast"},
    "cabo verde": {"lat": 16.00, "lon": -24.01, "paese": "Cabo Verde"},
    "cambodia": {"lat": 12.56, "lon": 104.99, "paese": "Cambodia"},
    "cameroon": {"lat": 7.36, "lon": 12.35, "paese": "Cameroon"},
    "canada": {"lat": 56.13, "lon": -106.34, "paese": "Canada"},
    "central african republic": {"lat": 6.61, "lon": 20.93, "paese": "Central African Republic"},
    "chad": {"lat": 15.45, "lon": 18.73, "paese": "Chad"},
    "chile": {"lat": -35.67, "lon": -71.54, "paese": "Chile"},
    "china": {"lat": 35.86, "lon": 104.19, "paese": "China"},
    "colombia": {"lat": 4.57, "lon": -74.29, "paese": "Colombia"},
    "comoros": {"lat": -11.64, "lon": 43.33, "paese": "Comoros"},
    "congo": {"lat": -4.03, "lon": 21.75, "paese": "DR Congo"},
    "drc": {"lat": -4.03, "lon": 21.75, "paese": "DR Congo"},
    "costa rica": {"lat": 9.74, "lon": -83.75, "paese": "Costa Rica"},
    "croatia": {"lat": 45.10, "lon": 15.20, "paese": "Croatia"},
    "cuba": {"lat": 21.52, "lon": -77.78, "paese": "Cuba"},
    "cyprus": {"lat": 35.12, "lon": 33.42, "paese": "Cyprus"},
    "czechia": {"lat": 49.81, "lon": 15.47, "paese": "Czech Republic"},
    "denmark": {"lat": 56.26, "lon": 9.50, "paese": "Denmark"},
    "djibouti": {"lat": 11.82, "lon": 42.59, "paese": "Djibouti"},
    "dominica": {"lat": 15.41, "lon": -61.37, "paese": "Dominica"},
    "dominican republic": {"lat": 18.73, "lon": -70.16, "paese": "Dominican Republic"},
    "ecuador": {"lat": -1.83, "lon": -78.18, "paese": "Ecuador"},
    "egypt": {"lat": 26.82, "lon": 30.80, "paese": "Egypt"},
    "el salvador": {"lat": 13.79, "lon": -88.89, "paese": "El Salvador"},
    "equatorial guinea": {"lat": 1.65, "lon": 10.26, "paese": "Equatorial Guinea"},
    "eritrea": {"lat": 15.17, "lon": 39.78, "paese": "Eritrea"},
    "estonia": {"lat": 58.59, "lon": 25.01, "paese": "Estonia"},
    "eswatini": {"lat": -26.52, "lon": 31.46, "paese": "Eswatini"},
    "ethiopia": {"lat": 9.14, "lon": 40.48, "paese": "Ethiopia"},
    "fiji": {"lat": -17.71, "lon": 178.06, "paese": "Fiji"},
    "finland": {"lat": 61.92, "lon": 25.74, "paese": "Finland"},
    "france": {"lat": 46.22, "lon": 2.21, "paese": "France"},
    "gabon": {"lat": -0.80, "lon": 11.60, "paese": "Gabon"},
    "gambia": {"lat": 13.44, "lon": -15.31, "paese": "Gambia"},
    "georgia": {"lat": 42.31, "lon": 43.35, "paese": "Georgia"},
    "germany": {"lat": 51.16, "lon": 10.45, "paese": "Germany"},
    "ghana": {"lat": 7.94, "lon": -1.02, "paese": "Ghana"},
    "greece": {"lat": 39.07, "lon": 21.82, "paese": "Greece"},
    "grenada": {"lat": 12.11, "lon": -61.67, "paese": "Grenada"},
    "guatemala": {"lat": 15.78, "lon": -90.23, "paese": "Guatemala"},
    "guinea": {"lat": 9.94, "lon": -9.69, "paese": "Guinea"},
    "guinea-bissau": {"lat": 11.80, "lon": -15.18, "paese": "Guinea-Bissau"},
    "guyana": {"lat": 4.86, "lon": -58.93, "paese": "Guyana"},
    "haiti": {"lat": 18.97, "lon": -72.28, "paese": "Haiti"},
    "honduras": {"lat": 15.19, "lon": -86.24, "paese": "Honduras"},
    "hungary": {"lat": 47.16, "lon": 19.50, "paese": "Hungary"},
    "iceland": {"lat": 64.96, "lon": -19.02, "paese": "Iceland"},
    "india": {"lat": 20.59, "lon": 78.96, "paese": "India"},
    "indonesia": {"lat": -0.78, "lon": 113.92, "paese": "Indonesia"},
    "iran": {"lat": 32.42, "lon": 53.68, "paese": "Iran"},
    "iraq": {"lat": 33.22, "lon": 43.67, "paese": "Iraq"},
    "ireland": {"lat": 53.41, "lon": -8.24, "paese": "Ireland"},
    "israel": {"lat": 31.04, "lon": 34.85, "paese": "Israel"},
    "italy": {"lat": 41.87, "lon": 12.56, "paese": "Italy"},
    "jamaica": {"lat": 18.10, "lon": -77.29, "paese": "Jamaica"},
    "japan": {"lat": 36.20, "lon": 138.25, "paese": "Japan"},
    "jordan": {"lat": 30.58, "lon": 36.23, "paese": "Jordan"},
    "kazakhstan": {"lat": 48.01, "lon": 66.92, "paese": "Kazakhstan"},
    "kenya": {"lat": -0.02, "lon": 37.90, "paese": "Kenya"},
    "kiribati": {"lat": -3.37, "lon": -168.73, "paese": "Kiribati"},
    "kuwait": {"lat": 29.31, "lon": 47.48, "paese": "Kuwait"},
    "kyrgyzstan": {"lat": 41.20, "lon": 74.76, "paese": "Kyrgyzstan"},
    "laos": {"lat": 19.85, "lon": 102.49, "paese": "Laos"},
    "latvia": {"lat": 56.87, "lon": 24.60, "paese": "Latvia"},
    "lebanon": {"lat": 33.85, "lon": 35.86, "paese": "Lebanon"},
    "lesotho": {"lat": -29.60, "lon": 28.23, "paese": "Lesotho"},
    "liberia": {"lat": 6.42, "lon": -9.42, "paese": "Liberia"},
    "libya": {"lat": 26.33, "lon": 17.22, "paese": "Libya"},
    "liechtenstein": {"lat": 47.16, "lon": 9.55, "paese": "Liechtenstein"},
    "lithuania": {"lat": 55.16, "lon": 23.88, "paese": "Lithuania"},
    "luxembourg": {"lat": 49.81, "lon": 6.12, "paese": "Luxembourg"},
    "madagascar": {"lat": -18.76, "lon": 46.86, "paese": "Madagascar"},
    "malawi": {"lat": -13.25, "lon": 34.30, "paese": "Malawi"},
    "malaysia": {"lat": 4.21, "lon": 101.97, "paese": "Malaysia"},
    "maldives": {"lat": 3.20, "lon": 73.22, "paese": "Maldives"},
    "mali": {"lat": 17.57, "lon": -3.99, "paese": "Mali"},
    "malta": {"lat": 35.93, "lon": 14.37, "paese": "Malta"},
    "marshall islands": {"lat": 7.13, "lon": 171.18, "paese": "Marshall Islands"},
    "mauritania": {"lat": 21.00, "lon": -10.94, "paese": "Mauritania"},
    "mauritius": {"lat": -20.34, "lon": 57.55, "paese": "Mauritius"},
    "mexico": {"lat": 23.63, "lon": -102.55, "paese": "Mexico"},
    "micronesia": {"lat": 7.42, "lon": 150.55, "paese": "Micronesia"},
    "moldova": {"lat": 47.41, "lon": 28.36, "paese": "Moldova"},
    "monaco": {"lat": 43.73, "lon": 7.42, "paese": "Monaco"},
    "mongolia": {"lat": 46.86, "lon": 103.84, "paese": "Mongolia"},
    "montenegro": {"lat": 42.70, "lon": 19.37, "paese": "Montenegro"},
    "morocco": {"lat": 31.79, "lon": -7.09, "paese": "Morocco"},
    "mozambique": {"lat": -18.66, "lon": 35.52, "paese": "Mozambique"},
    "myanmar": {"lat": 21.91, "lon": 95.95, "paese": "Myanmar"},
    "burma": {"lat": 21.91, "lon": 95.95, "paese": "Myanmar"},
    "namibia": {"lat": -22.95, "lon": 18.49, "paese": "Namibia"},
    "nauru": {"lat": -0.52, "lon": 166.93, "paese": "Nauru"},
    "nepal": {"lat": 28.39, "lon": 84.12, "paese": "Nepal"},
    "netherlands": {"lat": 52.13, "lon": 5.29, "paese": "Netherlands"},
    "new zealand": {"lat": -40.90, "lon": 174.88, "paese": "New Zealand"},
    "nicaragua": {"lat": 12.86, "lon": -85.20, "paese": "Nicaragua"},
    "niger": {"lat": 17.60, "lon": 8.08, "paese": "Niger"},
    "nigeria": {"lat": 9.08, "lon": 8.67, "paese": "Nigeria"},
    "north korea": {"lat": 40.33, "lon": 127.51, "paese": "North Korea"},
    "macedonia": {"lat": 41.60, "lon": 21.74, "paese": "North Macedonia"},
    "norway": {"lat": 60.47, "lon": 8.46, "paese": "Norway"},
    "oman": {"lat": 21.51, "lon": 55.92, "paese": "Oman"},
    "pakistan": {"lat": 30.37, "lon": 69.34, "paese": "Pakistan"},
    "palau": {"lat": 7.51, "lon": 134.58, "paese": "Palau"},
    "palestine": {"lat": 31.95, "lon": 35.23, "paese": "Palestine"},
    "gaza": {"lat": 31.35, "lon": 34.30, "paese": "Palestine"},
    "panama": {"lat": 8.53, "lon": -80.78, "paese": "Panama"},
    "papua new guinea": {"lat": -6.31, "lon": 143.95, "paese": "Papua New Guinea"},
    "paraguay": {"lat": -23.44, "lon": -58.44, "paese": "Paraguay"},
    "peru": {"lat": -9.18, "lon": -75.01, "paese": "Peru"},
    "philippines": {"lat": 12.87, "lon": 121.77, "paese": "Philippines"},
    "poland": {"lat": 51.91, "lon": 19.14, "paese": "Poland"},
    "portugal": {"lat": 39.39, "lon": -8.22, "paese": "Portugal"},
    "qatar": {"lat": 25.35, "lon": 51.18, "paese": "Qatar"},
    "romania": {"lat": 45.94, "lon": 24.96, "paese": "Romania"},
    "russia": {"lat": 61.52, "lon": 105.31, "paese": "Russia"},
    "rwanda": {"lat": -1.94, "lon": 29.87, "paese": "Rwanda"},
    "saint kitts and nevis": {"lat": 17.35, "lon": -62.78, "paese": "Saint Kitts and Nevis"},
    "saint lucia": {"lat": 13.90, "lon": -60.97, "paese": "Saint Lucia"},
    "saint vincent": {"lat": 13.25, "lon": -61.22, "paese": "Saint Vincent"},
    "samoa": {"lat": -13.75, "lon": -172.10, "paese": "Samoa"},
    "san marino": {"lat": 43.94, "lon": 12.45, "paese": "San Marino"},
    "sao tome and principe": {"lat": 0.18, "lon": 6.61, "paese": "Sao Tome and Principe"},
    "saudi arabia": {"lat": 23.88, "lon": 45.07, "paese": "Saudi Arabia"},
    "senegal": {"lat": 14.49, "lon": -14.45, "paese": "Senegal"},
    "serbia": {"lat": 44.01, "lon": 21.00, "paese": "Serbia"},
    "seychelles": {"lat": -4.67, "lon": 55.49, "paese": "Seychelles"},
    "sierra leone": {"lat": 8.46, "lon": -11.77, "paese": "Sierra Leone"},
    "singapore": {"lat": 1.35, "lon": 103.81, "paese": "Singapore"},
    "slovakia": {"lat": 48.66, "lon": 19.69, "paese": "Slovakia"},
    "slovenia": {"lat": 46.15, "lon": 14.99, "paese": "Slovenia"},
    "solomon islands": {"lat": -9.64, "lon": 160.15, "paese": "Solomon Islands"},
    "somalia": {"lat": 5.15, "lon": 46.19, "paese": "Somalia"},
    "south africa": {"lat": -30.55, "lon": 22.93, "paese": "South Africa"},
    "south korea": {"lat": 35.90, "lon": 127.76, "paese": "South Korea"},
    "south sudan": {"lat": 6.87, "lon": 31.30, "paese": "South Sudan"},
    "spain": {"lat": 40.46, "lon": -3.74, "paese": "Spain"},
    "sri lanka": {"lat": 7.87, "lon": 80.77, "paese": "Sri Lanka"},
    "sudan": {"lat": 12.86, "lon": 30.21, "paese": "Sudan"},
    "suriname": {"lat": 3.91, "lon": -56.02, "paese": "Suriname"},
    "sweden": {"lat": 60.12, "lon": 18.64, "paese": "Sweden"},
    "switzerland": {"lat": 46.81, "lon": 8.22, "paese": "Switzerland"},
    "syria": {"lat": 34.80, "lon": 38.99, "paese": "Syria"},
    "taiwan": {"lat": 23.69, "lon": 120.96, "paese": "Taiwan"},
    "tajikistan": {"lat": 38.86, "lon": 71.27, "paese": "Tajikistan"},
    "tanzania": {"lat": -6.36, "lon": 34.88, "paese": "Tanzania"},
    "thailand": {"lat": 15.87, "lon": 100.99, "paese": "Thailand"},
    "timor-leste": {"lat": -8.87, "lon": 125.72, "paese": "Timor-Leste"},
    "togo": {"lat": 8.61, "lon": 0.82, "paese": "Togo"},
    "tonga": {"lat": -21.17, "lon": -175.19, "paese": "Tonga"},
    "trinidad and tobago": {"lat": 10.69, "lon": -61.22, "paese": "Trinidad and Tobago"},
    "tunisia": {"lat": 33.88, "lon": 9.53, "paese": "Tunisia"},
    "turkey": {"lat": 38.96, "lon": 35.24, "paese": "Turkey"},
    "turkmenistan": {"lat": 38.96, "lon": 59.55, "paese": "Turkmenistan"},
    "tuvalu": {"lat": -7.10, "lon": 177.64, "paese": "Tuvalu"},
    "uganda": {"lat": 1.37, "lon": 32.29, "paese": "Uganda"},
    "ukraine": {"lat": 48.37, "lon": 31.16, "paese": "Ukraine"},
    "united arab emirates": {"lat": 23.42, "lon": 53.84, "paese": "United Arab Emirates"},
    "united kingdom": {"lat": 55.37, "lon": -3.43, "paese": "United Kingdom"},
    "uk": {"lat": 55.37, "lon": -3.43, "paese": "United Kingdom"},
    "united states": {"lat": 37.09, "lon": -95.71, "paese": "United States"},
    "usa": {"lat": 37.09, "lon": -95.71, "paese": "United States"},
    "uruguay": {"lat": -32.52, "lon": -55.76, "paese": "Uruguay"},
    "uzbekistan": {"lat": 41.37, "lon": 64.58, "paese": "Uzbekistan"},
    "vanuatu": {"lat": -15.37, "lon": 166.95, "paese": "Vanuatu"},
    "vatican city": {"lat": 41.90, "lon": 12.45, "paese": "Vatican City"},
    "venezuela": {"lat": 6.42, "lon": -66.58, "paese": "Venezuela"},
    "vietnam": {"lat": 14.05, "lon": 108.27, "paese": "Vietnam"},
    "yemen": {"lat": 15.55, "lon": 48.51, "paese": "Yemen"},
    "zambia": {"lat": -13.13, "lon": 27.84, "paese": "Zambia"},
    "zimbabwe": {"lat": -19.01, "lon": 29.15, "paese": "Zimbabwe"}
}

def genera_id(data, lat, lon, titolo=""):
    titolo_pulito = "".join(e for e in titolo[:10] if e.isalnum())
    return f"{data}_{round(float(lat), 2)}_{round(float(lon), 2)}_{titolo_pulito}"

ids_esistenti = sheet.col_values(1)
nuove_righe = []

# --- 2. MOTORE ACLED (Globale Certificato: 🔴 CONFERMATO) ---
try:
    print("Scansione ACLED in corso...")
    response = session.get("https://acleddata.com/api/acled/read?limit=50")
    if response.status_code == 200:
        for evento in response.json().get('data', []):
            vittime = int(evento.get('fatalities', 0))
            if vittime > 0:
                uid = genera_id(evento['event_date'], evento['latitude'], evento['longitude'], evento['event_type'])
                if uid not in ids_esistenti:
                    nuove_righe.append([uid, evento['event_date'], evento['event_type'], vittime, evento['latitude'], evento['longitude'], evento['country'], "🔴 CONFERMATO"])
                    ids_esistenti.append(uid)
except Exception as e:
    print(f"ACLED Standby: {e}")

# --- 3. MOTORE GDELT AI GLOBALE (Radar 15 minuti: 🟠 IN ATTESA) ---
print("Scansione GDELT AI globale con dizionario fisso 195 Stati...")
gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc?query=(killed OR casualties OR fatalities OR dead OR deaths OR morts OR vittime) (attack OR strike OR clash OR armed OR bombing OR military) -movie -cinema -film -game -fiction -metaphor&mode=artlist&maxrecords=50&format=json&sort=datedesc"

try:
    req_gdelt = requests.get(gdelt_url)
    if req_gdelt.status_code == 200:
        articoli = req_gdelt.json().get('articles', [])
        
        for art in articoli:
            titolo = art.get('title', '')
            titolo_lower = titolo.lower()
            
            # SCUDI ANTI-FAKE NEWS
            if "?" in titolo or any(word in titolo_lower for word in ["trailer", "actor", "zombie", "alien", "simulation", "anniversary"]):
                continue

            # ESTRATTORE VITTIME ELASTICO
            vittime = 0
            match = re.search(r'(\d+)', titolo_lower)
            if match:
                vittime = int(match.group(1))
            
            if vittime == 0 and any(w in titolo_lower for w in ["killed", "dead", "vittime", "morti", "casualties", "deaths"]):
                vittime = 1
                
            if vittime > 1000:
                continue
                
            # VERIFICA GEOGRAFICA SUI 195 STATI
            lat, lon, paese_rilevato = None, None, None
            for chiave, dati_geo in DIZIONARIO_STATI.items():
                # Cerchiamo la parola esatta per evitare che "Oman" venga trovato dentro "R(oman)ia"
                if re.search(r'\b' + re.escape(chiave) + r'\b', titolo_lower):
                    lat = dati_geo["lat"]
                    lon = dati_geo["lon"]
                    paese_rilevato = dati_geo["paese"]
                    break

            if lat is not None and lon is not None:
                uid = genera_id(datetime.now().strftime("%Y-%m-%d"), lat, lon, titolo)
                if uid not in ids_esistenti:
                    titolo_breve = titolo[:70] + "..."
                    nuove_righe.append([uid, datetime.now().strftime("%Y-%m-%d"), titolo_breve, vittime, lat, lon, paese_rilevato, "🟠 IN ATTESA"])
                    ids_esistenti.append(uid)
except Exception as e:
    print(f"Errore GDELT: {e}")

# --- 4. SCRITTURA BATCH SU GOOGLE SHEETS ---
if nuove_righe:
    sheet.append_rows(nuove_righe)
    print(f"Sincronizzazione riuscita: aggiunti {len(nuove_righe)} eventi al radar.")
else:
    print("Nessun nuovo evento ha superato i filtri in questo ciclo.")

# --- 5. PROTOCOLLO DI AUTO-PULIZIA (7 GIORNI) ---
try:
    dati_foglio = sheet.get_all_values()
    oggi = datetime.now()
    righe_da_eliminare = []

    for i, row in enumerate(dati_foglio):
        if i == 0: continue
        if len(row) >= 8:
            data_evento_str = row[1]
            fonte = row[7]
            if "IN ATTESA" in fonte:
                try:
                    data_evento = datetime.strptime(data_evento_str, "%Y-%m-%d")
                    if (oggi - data_evento).days > 7:
                        righe_da_eliminare.append(i + 1)
                except: pass

    for riga in sorted(righe_da_eliminare, reverse=True):
        sheet.delete_rows(riga)
except Exception as e:
    print(f"Errore pulizia: {e}")

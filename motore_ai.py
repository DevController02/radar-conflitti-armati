import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

print("--- Avvio Radar OSINT Globale Totale (ACLED + GDELT AI) ---")

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

# Inizializzazione Geolocalizzatore Globale (OpenStreetMap)
geolocator = Nominatim(user_agent="radar_conflitti_osint_bot")

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
print("Scansione GDELT AI globale ed estrazione geografica...")
gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc?query=(killed OR casualties OR fatalities) (attack OR strike OR clash OR armed) -movie -cinema -film -game -fiction -metaphor&mode=artlist&maxrecords=50&format=json&sort=datedesc"

try:
    req_gdelt = requests.get(gdelt_url)
    if req_gdelt.status_code == 200:
        articoli = req_gdelt.json().get('articles', [])
        
        for art in articoli:
            titolo = art.get('title', '')
            titolo_lower = titolo.lower()
            
            # FILTRI ANTI-FAKE NEWS
            if "?" in titolo or any(word in titolo_lower for word in ["trailer", "actor", "zombie", "alien", "simulation"]):
                continue

            # Estrazione vittime
            vittime = 0
            match = re.search(r'(\d+)\s*(killed|dead|morti|uccisi|casualties)', titolo_lower)
            if match:
                vittime = int(match.group(1))
                
            if vittime == 0 or vittime > 1000:
                continue
                
            # GEOLOCALIZZAZIONE GLOBALE AUTOMATICA
            luoghi_candidati = re.findall(r'\b[A-Z][a-z]+\b', titolo)
            lat, lon, paese_rilevato = None, None, "Sconosciuto"
            
            for potenziale_luogo in luoghi_candidati:
                if potenziale_luogo.lower() in ["the", "attack", "killed", "strike", "armed", "clash", "bombing"]:
                    continue 
                
                try:
                    location = geolocator.geocode(potenziale_luogo, timeout=3, language="en")
                    if location:
                        lat = location.latitude
                        lon = location.longitude
                        paese_rilevato = location.address.split(",")[-1].strip()
                        break 
                except (GeocoderTimedOut, Exception):
                    continue 

            if lat is not None and lon is not None:
                uid = genera_id(datetime.now().strftime("%Y-%m-%d"), lat, lon, titolo)
                if uid not in ids_esistenti:
                    titolo_breve = titolo[:70] + "..."
                    nuove_righe.append([uid, datetime.now().strftime("%Y-%m-%d"), titolo_breve, vittime, lat, lon, paese_rilevato, "🟠 IN ATTESA"])
                    ids_esistenti.append(uid)
except Exception as e:
    print(f"Errore GDELT Globale: {e}")

# --- 4. SCRITTURA BATCH SU GOOGLE SHEETS ---
if nuove_righe:
    sheet.append_rows(nuove_righe)
    print(f"Aggiornamento globale completato: {len(nuove_righe)} eventi inseriti.")
else:
    print("Nessun nuovo evento globale inserito in questo ciclo.")

# --- 5. PROTOCOLLO DI AUTO-PULIZIA (7 GIORNI) ---
print("Avvio protocollo di auto-pulizia del database...")
try:
    dati_foglio = sheet.get_all_values()
    oggi = datetime.now()
    righe_da_eliminare = []

    # Analizziamo le righe partendo dalla seconda (evitiamo l'intestazione)
    for i, row in enumerate(dati_foglio):
        if i == 0: continue
        
        # Ci assicuriamo che la riga abbia tutte le colonne prima di leggerla
        if len(row) >= 8:
            data_evento_str = row[1] # Colonna Data
            fonte = row[7] # Colonna Fonte
            
            if "IN ATTESA" in fonte:
                try:
                    # Trasformiamo il testo della data in un oggetto temporale
                    data_evento = datetime.strptime(data_evento_str, "%Y-%m-%d")
                    differenza_giorni = (oggi - data_evento).days
                    
                    # Se il pallino arancione ha più di 7 giorni, lo mettiamo in lista per l'eliminazione
                    if differenza_giorni > 7:
                        righe_da_eliminare.append(i + 1) # +1 perché Google Sheets inizia a contare da 1
                except Exception as e:
                    pass

    # Eliminiamo le righe partendo dal basso verso l'alto per non sballare gli indici numerici
    for riga in sorted(righe_da_eliminare, reverse=True):
        sheet.delete_rows(riga)
        
    if righe_da_eliminare:
        print(f"Pulizia completata: eliminate {len(righe_da_eliminare)} allerte scadute.")
    else:
        print("Il database è già pulito e ottimizzato.")

except Exception as e:
    print(f"Errore durante l'auto-pulizia: {e}")
          

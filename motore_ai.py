import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import re
import time
from datetime import datetime

# --- 1. CONFIGURAZIONE GOOGLE SHEETS ---
print("Avvio connessione a Google Sheets...")
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(creds)

# ATTENZIONE: Inserisci qui il nome esatto del tuo file Google Sheets
NOME_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
sheet = client.open(NOME_FOGLIO).sheet1

# --- 2. FONTI OSINT UMANITARIE ---
FONTI_RSS = {
    "ReliefWeb (ONU)": "https://reliefweb.int/updates/rss.xml",
    "Amnesty International": "https://www.amnesty.org/en/rss/",
    "Human Rights Watch": "https://www.hrw.org/rss/news",
    "UN News": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
}

# --- 3. DATABASE GEOGRAFICO DI BASE ---
COORDINATE = {
    "Syria": [34.8, 38.9], "Siria": [34.8, 38.9],
    "Sudan": [12.8, 30.2],
    "Ukraine": [48.3, 31.1], "Ucraina": [48.3, 31.1],
    "Gaza": [31.5, 34.4], "Palestine": [31.5, 34.4],
    "Yemen": [15.5, 48.5],
    "Myanmar": [21.9, 95.9],
    "Congo": [-4.0, 21.7],
    "Somalia": [5.1, 46.1],
    "Lebanon": [33.8, 35.5], "Libano": [33.8, 35.5]
}

# --- 4. FUNZIONE DI ESTRAZIONE DATI ---
def estrai_dati_notizia(titolo, sommario):
    testo_completo = (titolo + " " + sommario).lower()
    
    paese_trovato = None
    lat, lon = None, None
    for paese, coords in COORDINATE.items():
        if paese.lower() in testo_completo:
            paese_trovato = paese
            lat, lon = coords
            break
            
    if not paese_trovato:
        return None
        
    parole_conflitto = ['killed', 'dead', 'casualties', 'attack', 'strike', 'vittime', 'morti', 'uccisi', 'conflict']
    if not any(parola in testo_completo for parola in parole_conflitto):
        return None
        
    match_vittime = re.search(r'(\d+)\s*(people|civilians|killed|dead|vittime|morti)', testo_completo)
    vittime = int(match_vittime.group(1)) if match_vittime else 2 
    
    return {
        "titolo": titolo[:50] + "...", 
        "vittime": vittime, 
        "lat": lat, 
        "lon": lon, 
        "paese": paese_trovato
    }

# --- 5. IL MOTORE CON CROSS-REFERENCING ---
print("Inizio scansione delle fonti umanitarie e Cross-Referencing...")

# Buffer di attesa: raggruppa le notizie per Paese
# Struttura: { "Sudan": {"fonti": set(), "dati_migliori": {...}} }
buffer_eventi = {}

# FASE A: Raccolta Dati (Popoliamo il Buffer)
for nome_fonte, url_feed in FONTI_RSS.items():
    print(f"Lettura da: {nome_fonte}")
    feed = feedparser.parse(url_feed)
    
    for entry in feed.entries[:10]:
        titolo = getattr(entry, 'title', '')
        sommario = getattr(entry, 'summary', '')
        
        dati = estrai_dati_notizia(titolo, sommario)
        
        if dati:
            paese = dati["paese"]
            if paese not in buffer_eventi:
                buffer_eventi[paese] = {
                    "fonti_confermanti": set(),
                    "titolo_principale": dati["titolo"],
                    "vittime_max": dati["vittime"],
                    "lat": dati["lat"],
                    "lon": dati["lon"]
                }
            
            # Aggiungiamo la fonte all'elenco di chi ha segnalato l'evento
            buffer_eventi[paese]["fonti_confermanti"].add(nome_fonte)
            
            # Teniamo il numero di vittime più alto segnalato tra le fonti
            if dati["vittime"] > buffer_eventi[paese]["vittime_max"]:
                buffer_eventi[paese]["vittime_max"] = dati["vittime"]

# FASE B: Validazione (Cross-Referencing) e Inserimento
titoli_esistenti = sheet.col_values(1)
nuovi_inserimenti = 0

print("\n--- Analisi Incrociata dei Dati ---")
for paese, info in buffer_eventi.items():
    numero_fonti = len(info["fonti_confermanti"])
    nomi_fonti = ", ".join(info["fonti_confermanti"])
    
    # REGOLA D'ORO OSINT: Almeno 2 fonti diverse per confermare!
    if numero_fonti >= 2:
        print(f"✅ EVENTO CONFERMATO in {paese} da {numero_fonti} fonti ({nomi_fonti})")
        
        # Prepariamo la riga per Google Sheets
        nuova_riga = [
            info["titolo_principale"],
            info["vittime_max"],
            info["lat"],
            info["lon"],
            paese
        ]
        
        # Controllo Anti-Duplicati Storici
        if info["titolo_principale"] not in titoli_esistenti:
            try:
                sheet.append_row(nuova_riga)
                titoli_esistenti.append(info["titolo_principale"])
                nuovi_inserimenti += 1
                print(f"   -> Salvato nel database.")
                time.sleep(2) # Evita il blocco per le API di Google
            except Exception as e:
                print(f"   -> Errore di salvataggio: {e}")
        else:
            print(f"   -> Già presente nel database storico, ignorato.")
    else:
        print(f"❌ Evento SCARTATO in {paese}. Segnalato solo da 1 fonte ({nomi_fonti}). Attendibilità insufficiente.")

print(f"\nScansione completata. Aggiunti {nuovi_inserimenti} nuovi eventi validati.")
    

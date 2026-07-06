import os
import json
import feedparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import time

print("Avvio del Motore AI OSINT Avanzato...")

# --- 1. CONFIGURAZIONE GOOGLE SHEETS ---
try:
    print("Autenticazione con Google Cloud...")
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if not creds_json:
        raise ValueError("Variabile d'ambiente GOOGLE_CREDENTIALS non trovata. Controlla i Secrets di GitHub!")

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)

    # Il tuo ID foglio originale blindato
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4"
    sheet = client.open_by_key(ID_FOGLIO).sheet1
    print("Connessione al database avvenuta con successo!")

except Exception as e:
    print(f"Errore critico di connessione: {e}")
    exit(1)


# --- 2. FONTI RSS UMANITARIE ---
FONTI_RSS = {
    "ReliefWeb (ONU)": "https://reliefweb.int/updates/rss.xml",
    "Amnesty International": "https://www.amnesty.org/en/rss/",
    "Human Rights Watch": "https://www.hrw.org/rss/news",
    "UN News": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
}

# --- 3. FILTRO CINETICO (Solo eventi armati/bellici) ---
PAROLE_CHIAVE_CONFLITTO = [
    "attack", "killed", "strike", "bombing", "clash", "gunfire", 
    "offensive", "casualties", "dead", "armed", "drone", "missile", 
    "explosion", "ambush", "raid", "terrorist", "assassination",
    "vittime", "morti", "uccisi", "conflict"
]

# --- 4. DATABASE GEOGRAFICO DI BASE ---
COORDINATE = {
    "syria": {"lat": 34.8, "lon": 38.9, "paese": "Syria"},
    "siria": {"lat": 34.8, "lon": 38.9, "paese": "Syria"},
    "sudan": {"lat": 12.8, "lon": 30.2, "paese": "Sudan"},
    "ukraine": {"lat": 48.3, "lon": 31.1, "paese": "Ukraine"},
    "ucraina": {"lat": 48.3, "lon": 31.1, "paese": "Ukraine"},
    "gaza": {"lat": 31.5, "lon": 34.4, "paese": "Palestine"},
    "palestine": {"lat": 31.5, "lon": 34.4, "paese": "Palestine"},
    "yemen": {"lat": 15.5, "lon": 48.5, "paese": "Yemen"},
    "myanmar": {"lat": 21.9, "lon": 95.9, "paese": "Myanmar"},
    "congo": {"lat": -4.0, "lon": 21.7, "paese": "Congo"},
    "somalia": {"lat": 5.1, "lon": 46.1, "paese": "Somalia"},
    "lebanon": {"lat": 33.8, "lon": 35.5, "paese": "Lebanon"},
    "libano": {"lat": 33.8, "lon": 35.5, "paese": "Lebanon"}
}


# --- 5. FUNZIONE DI FILTRAGGIO ED ESTRAZIONE DATI ---
def analizza_notizia(titolo, sommario):
    testo_completo = (titolo + " " + sommario).lower()
    
    # A. RICERCA PAESE E COORDINATE
    lat, lon, paese_trovato = None, None, None
    for chiave_paese, dati_geo in COORDINATE.items():
        if chiave_paese in testo_completo:
            lat = dati_geo["lat"]
            lon = dati_geo["lon"]
            paese_trovato = dati_geo["paese"]
            break
            
    if not paese_trovato:
        return None # Nessun paese conosciuto rilevato
        
    # B. FILTRO CINETICO (Riduzione drastica del rumore diplomatico)
    if not any(parola in testo_completo for parola in PAROLE_CHIAVE_CONFLITTO):
        return None # È solo diplomazia o una conferenza, ignoriamo
        
    # C. ESTRAZIONE VITTIME REALE (Se non trova numeri, mette 0, addio al trucco del "2")
    vittime = 0
    match_vittime = re.search(r'(\d+)\s*(people|civilians|killed|dead|vittime|morti|casualties|fatalities)', testo_completo)
    if match_vittime:
        vittime = int(match_vittime.group(1))
    
    return {
        "titolo": titolo[:70] + "..." if len(titolo) > 70 else titolo, 
        "vittime": vittime, 
        "lat": lat, 
        "lon": lon, 
        "paese": paese_trovato
    }


# --- 6. APPLICAZIONE LOGICA CROSS-REFERENCING ---
print("Inizio scansione delle fonti con verifica incrociata...")

# Raggruppiamo gli eventi rilevati per Paese in questo ciclo
buffer_eventi = {}

# FASE 1: Lettura dei feed e popolamento del buffer
for nome_fonte, url_feed in FONTI_RSS.items():
    print(f"Scansione in corso su: {nome_fonte}")
    feed = feedparser.parse(url_feed)
    
    for entry in feed.entries[:15]:  # Analizziamo gli ultimi 15 articoli per fonte
        titolo = getattr(entry, 'title', '')
        sommario = getattr(entry, 'summary', '')
        
        dati = analizza_notizia(titolo, sommario)
        
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
            
            # Registriamo quale agenzia ha segnalato o confermato questo fronte
            buffer_eventi[paese]["fonti_confermanti"].add(nome_fonte)
            
            # Aggiorniamo il bilancio delle vittime se un'altra fonte riporta un dato più accurato/alto
            if dati["vittime"] > buffer_eventi[paese]["vittime_max"]:
                buffer_eventi[paese]["vittime_max"] = dati["vittime"]

# FASE 2: Validazione incrociata e scrittura su Google Sheets
titoli_esistenti = sheet.col_values(1)  # Carica lo storico per evitare doppioni
nuove_righe = []

print("\n--- Fase Analisi Incrociata e Intelligence ---")
for paese, info in buffer_eventi.items():
    numero_fonti = len(info["fonti_confermanti"])
    nomi_fonti = ", ".join(info["fonti_confermanti"])
    
    # REGOLA D'ORO: Conferma valida sul radar solo con almeno 2 fonti indipendenti!
    if numero_fonti >= 2:
        print(f"✅ EVENTO CINETICO CONFERMATO in [{paese}] da {numero_fonti} fonti: ({nomi_fonti})")
        
        # Struttura colonne Excel standard: titolo, vittime, lat, lon, paese
        nuova_riga = [
            info["titolo_principale"],
            info["vittime_max"],
            info["lat"],
            info["lon"],
            paese
        ]
        
        # Controllo anti-duplicato storico
        if info["titolo_principale"] not in titoli_esistenti:
            nuove_righe.append(nuova_riga)
            titoli_esistenti.append(info["titolo_principale"])
            print(f"   -> Approvato e preparato per l'inserimento sul radar.")
        else:
            print(f"   -> Ignorato: Evento identico già registrato nel database storico.")
    else:
        print(f"❌ Evento SCARTATO in [{paese}]. Attendibilità insufficiente: registrato solo da '{nomi_fonti}'.")

# FASE 3: Aggiornamento massivo del database
if nuove_righe:
    try:
        print(f"\nScrittura in corso di {len(nuove_righe)} righe filtrate nel database Google Sheets...")
        sheet.append_rows(nuove_righe)
        print("Database aggiornato con successo!")
    except Exception as e:
        print(f"Errore durante la scrittura su Google Sheets: {e}")
else:
    print("\nNessun nuovo evento cinetico ha superato il controllo incrociato in questo ciclo.")

print("\nOperazione completata. Il motore OSINT torna in modalità ascolto.")

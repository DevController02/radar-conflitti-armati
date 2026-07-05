import gspread
import json
import os
import datetime
import random
import re

# 1. Connessione sicura tramite GitHub Secrets
try:
    # Legge il file JSON segreto dalle variabili di ambiente di GitHub
    creds_dict = json.loads(os.environ["GCP_CREDENTIALS"])
    client = gspread.service_account_from_dict(creds_dict)
    
    # INSERISCI QUI L'ID DEL TUO FOGLIO GOOGLE
    ID_FOGLIO = "1UDCmPyNqsWRSIBTmo6UYNBkqMg3FiJ4sdgmdY1e22G4" 
    foglio = client.open_by_key(ID_FOGLIO).sheet1
    print("✅ Connessione al database avvenuta con successo.")
except Exception as e:
    print(f"❌ Errore di connessione: {e}")
    exit(1)

# 2. Sistema di Analisi
def analizza_conflitto(testo):
    testo_low = testo.lower()
    risultato = {"violazione": False, "bersaglio": "nessuno", "vittime": 0}
    
    armi = ["bombardament", "raid", "missil", "artiglieria", "attacco aereo", "drone"]
    bersagli = {"civil": "Civili", "ospedal": "Ospedale", "scuol": "Scuola", "rifugi": "Rifugio", "clinica": "Clinica"}

    if any(arma in testo_low for arma in armi):
        for chiave, nome_bersaglio in bersagli.items():
            if chiave in testo_low:
                risultato["violazione"] = True
                risultato["bersaglio"] = nome_bersaglio
                break
                
    if risultato["violazione"]:
        numeri = re.findall(r'\d+', testo)
        if numeri: risultato["vittime"] = int(numeri[0])

    return risultato

# 3. Raccolta Dati (Simulata per ora)
print(f"[{datetime.datetime.now()}] Avvio scansione web...")
paesi = [("Ucraina", 48.37, 31.16), ("Sudan", 12.86, 30.21), ("Siria", 34.80, 38.99)]
paese = random.choice(paesi)

scenari = [
    f"Missile colpisce un ospedale nella periferia. Segnalati {random.randint(2, 15)} morti.",
    "Scontro militare al confine, truppe avanzano."
]
notizia = random.choice(scenari)
analisi = analizza_conflitto(notizia)

if analisi["violazione"]:
    nuova_riga = [analisi["bersaglio"], analisi["vittime"], paese[1], paese[2], paese[0]]
    foglio.append_row(nuova_riga)
    print(f"⚠️ REGISTRATA: Attacco a {analisi['bersaglio']} in {paese[0]}")
else:
    print("✅ Nessuna nuova violazione.")

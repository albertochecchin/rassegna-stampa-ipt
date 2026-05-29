#!/usr/bin/env python3
"""
Rassegna stampa automatica IPT noleggio auto.
Versione con deduplicazione: legge lo storico delle ultime rassegne
e chiede a Claude di NON ripetere temi gia' coperti.
"""

import os
import smtplib
import datetime
import pathlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
import anthropic

# --- CONFIG ---
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
MITTENTE_EMAIL = "alberto.checchin@gmail.com"
MITTENTE_NOME = "Rassegna Stampa IPT"
DESTINATARI = ["alberto.checchin@gmail.com", "luca.checchin98@gmail.com"]
GIORNI_STORICO = 7

# --- DATE ---
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
           "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
oggi_date = datetime.date.today()
OGGI = oggi_date.strftime("%d/%m/%Y")
OGGI_ESTESA = f"{oggi_date.day} {MESI_IT[oggi_date.month - 1]} {oggi_date.year}"

# --- STORICO ---
STORICO_DIR = pathlib.Path("rassegne")
STORICO_DIR.mkdir(exist_ok=True)


def carica_storico():
    """Carica le rassegne degli ultimi N giorni."""
    storico = []
    for i in range(1, GIORNI_STORICO + 1):
        data = oggi_date - datetime.timedelta(days=i)
        fname = STORICO_DIR / f"{data.isoformat()}.md"
        if fname.exists():
            contenuto = fname.read_text(encoding="utf-8")
            storico.append(f"=== RASSEGNA DEL {data.strftime('%d/%m/%Y')} ===\n{contenuto}")
    if storico:
        return "\n\n".join(storico)
    return "Nessuna rassegna precedente disponibile."


# --- PROMPT ---
PROMPT = f"""Sei un analista che prepara una rassegna stampa GIORNALIERA per una societa' di domiciliazione a Bolzano.

DATA DI OGGI: {OGGI_ESTESA}

REGOLA FONDAMENTALE - SOLO NOVITA' DEL GIORNO:
Qui sotto trovi le rassegne degli ultimi giorni. Devi includere SOLO notizie genuinamente NUOVE rispetto a quanto gia' coperto.

- NON ripetere notizie, temi o analisi gia' presenti nelle rassegne precedenti.
- Se l'unica novita' di oggi e' un aggiornamento minore su un tema gia' coperto, segnalalo come AGGIORNAMENTO in una riga e cita la data in cui il tema e' apparso la prima volta.
- Se OGGI non ci sono notizie nuove, scrivilo esplicitamente.
- Meglio una rassegna corta e onesta che una piena di ripetizioni.

--- STORICO RASSEGNE PRECEDENTI ---
{carica_storico()}
--- FINE STORICO ---

TEMI DA MONITORARE:
1. Norma IPT noleggio auto - "gestione ordinaria in via principale" (Decreto Fiscale 2026 / Legge 88/2026)
2. Agenzia Entrate - circolari e istruzioni su IPT noleggio
3. ANIASA - ricorsi, comunicati, strategie legali sull'IPT
4. Province autonome Bolzano e Trento - reazioni, ricorsi, lobbying sull'IPT
5. TAR e Corte Costituzionale - ricorsi su IPT noleggio
6. Societa' di noleggio auto - trasferimenti sedi, strategie fiscali, sentenze

ISTRUZIONI OPERATIVE:
- Usa la ricerca web. Cerca notizie pubblicate il {OGGI_ESTESA} o nelle ultime 24 ore.
- Per ogni notizia inclusa: titolo, fonte con link, data di pubblicazione verificata, 2-3 righe di sintesi, impatto per una domiciliazione a Bolzano.
- Scrivi in italiano, tono diretto. NIENTE preamboli tipo "Procedo con la redazione", "Ora cerco le notizie", ecc. Vai dritto al report.

STRUTTURA DEL REPORT (in questo ordine esatto):

RASSEGNA STAMPA IPT NOLEGGIO AUTO - {OGGI}

NOVITA' DEL GIORNO
(solo notizie genuinamente nuove di oggi; se non ce ne sono, scrivi "Nessuna novita' rilevante in data odierna")

AGGIORNAMENTI SU TEMI GIA' COPERTI
(una riga per ogni aggiornamento, con link; se nessuno, scrivi "Nessun aggiornamento")

RIEPILOGO
1-2 frasi su cosa di nuovo e' emerso oggi. Se nulla, dillo esplicitamente."""


def genera_rassegna():
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT}],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10
        }]
    )
    testo = ""
    for block in response.content:
        if block.type == "text":
            testo += block.text + "\n"
    return testo.strip()


def salva_rassegna(testo):
    fname = STORICO_DIR / f"{oggi_date.isoformat()}.md"
    fname.write_text(testo, encoding="utf-8")
    print(f"Rassegna salvata in: {fname}")


def invia_email(corpo):
    msg = MIMEMultipart()
    msg["From"] = formataddr((MITTENTE_NOME, MITTENTE_EMAIL))
    msg["To"] = ", ".join(DESTINATARI)
    msg["Reply-To"] = MITTENTE_EMAIL
    msg["Subject"] = f"Rassegna Stampa IPT Noleggio - {OGGI}"
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg.attach(MIMEText(corpo, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MITTENTE_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(MITTENTE_EMAIL, DESTINATARI, msg.as_string())
    print(f"Email inviata a: {', '.join(DESTINATARI)}")


if __name__ == "__main__":
    print(f"Generazione rassegna stampa del {OGGI}...")
    rassegna = genera_rassegna()
    print("Salvataggio nello storico...")
    salva_rassegna(rassegna)
    print("Invio email...")
    invia_email(rassegna)
    print("Completato.")

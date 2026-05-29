#!/usr/bin/env python3
"""
Rassegna stampa automatica IPT noleggio auto.
Usa Claude API con web search per cercare notizie, poi invia il report via email.
"""

import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
import anthropic

# --- CONFIGURAZIONE ---
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

MITTENTE_EMAIL = "alberto.checchin@gmail.com"
MITTENTE_NOME = "Rassegna Stampa IPT"
DESTINATARI = ["alberto.checchin@gmail.com", "luca.checchin98@gmail.com"]

# --- DATE ---
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
           "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
oggi_date = datetime.date.today()
ieri_date = oggi_date - datetime.timedelta(days=1)
sette_giorni_fa = oggi_date - datetime.timedelta(days=7)

OGGI = oggi_date.strftime("%d/%m/%Y")
OGGI_ESTESA = f"{oggi_date.day} {MESI_IT[oggi_date.month - 1]} {oggi_date.year}"
IERI_ESTESA = f"{ieri_date.day} {MESI_IT[ieri_date.month - 1]} {ieri_date.year}"
LIMITE_ESTESA = f"{sette_giorni_fa.day} {MESI_IT[sette_giorni_fa.month - 1]} {sette_giorni_fa.year}"

# --- PROMPT ---
PROMPT = f"""Sei un analista che prepara una rassegna stampa per una societa' di domiciliazione a Bolzano.

DATA DI OGGI: {OGGI_ESTESA}

REGOLA FONDAMENTALE SULLE DATE:
- Includi SOLO notizie pubblicate il {OGGI_ESTESA} oppure il {IERI_ESTESA} (ultime 24-48 ore).
- NON includere notizie piu' vecchie di {LIMITE_ESTESA}.
- Verifica la data di pubblicazione di ogni articolo prima di includerlo.
- Se una notizia non riporta una data esplicita, prova a verificarla; in caso di dubbio NON includerla.
- Se NON ci sono notizie nuove del giorno su un tema, scrivi esplicitamente "Nessuna nuova notizia in data {OGGI}".
- NON ripiegare su notizie vecchie: meglio dire che non c'e' nulla di nuovo.

TEMI DA MONITORARE (in ordine di priorita'):
1. Norma IPT noleggio auto - "gestione ordinaria in via principale" (Decreto Fiscale 2026)
2. Agenzia Entrate - circolari e istruzioni su IPT noleggio
3. ANIASA - ricorsi, comunicati, strategie legali sull'IPT
4. Province autonome Bolzano e Trento - reazioni, ricorsi, lobbying sull'IPT
5. TAR e Corte Costituzionale - ricorsi su IPT noleggio
6. Societa' di noleggio auto - trasferimenti sedi, strategie fiscali

ISTRUZIONI:
- Usa attivamente la ricerca web per ogni tema, includendo nella query "{oggi_date.year}" e termini come "oggi", "ieri" o la data esplicita.
- Per ogni notizia inclusa, riporta: titolo, fonte con link, data di pubblicazione, breve sintesi (2-3 righe), perche' e' importante per una domiciliazione a Bolzano.
- Scrivi in italiano, tono professionale.

STRUTTURA DEL REPORT:

RASSEGNA STAMPA IPT NOLEGGIO AUTO - {OGGI}

1. NOTIZIE CRITICHE DI OGGI
2. NOVITA' NORMATIVE / CIRCOLARI AGENZIA ENTRATE
3. COMUNICATI ANIASA
4. AGGIORNAMENTI PROVINCE BOLZANO / TRENTO
5. RICORSI E CONTENZIOSO

RIEPILOGO DEL GIORNO
2-3 frasi sulle notizie effettivamente nuove di oggi. Se non c'e' nulla di nuovo, dillo esplicitamente.

AZIONI CONSIGLIATE
Solo se ci sono notizie del giorno che richiedono azione."""


def genera_rassegna():
    """Chiama Claude API con web search e genera la rassegna."""
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


def invia_email(corpo):
    """Invia la rassegna via email a tutti i destinatari."""
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
    print("Rassegna generata. Invio email...")
    invia_email(rassegna)
    print("Completato.")

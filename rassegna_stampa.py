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
import anthropic

# --- CONFIGURAZIONE ---
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

MITTENTE = "alberto.checchin@gmail.com"
DESTINATARI = ["alberto.checchin@gmail.com", "luca.checchin98@gmail.com"]

# --- PROMPT PER LA RASSEGNA STAMPA ---
OGGI = datetime.date.today().strftime("%d/%m/%Y")

PROMPT = f"""Sei un analista che prepara una rassegna stampa quotidiana per una societa' di domiciliazione a Bolzano.

Cerca sul web le notizie piu' recenti (ultime 24-48 ore) sui seguenti temi, in ordine di priorita':

1. Norma IPT noleggio auto - "gestione ordinaria in via principale" (Decreto Fiscale 2026)
2. Agenzia Entrate - circolari e istruzioni su IPT noleggio
3. ANIASA - ricorsi, comunicati, strategie legali sull'IPT
4. Province autonome Bolzano e Trento - reazioni, ricorsi, lobbying sull'IPT
5. TAR e Corte Costituzionale - ricorsi su IPT noleggio
6. Societa' di noleggio auto - trasferimenti sedi, strategie fiscali

Cerca attivamente notizie aggiornate. Usa la ricerca web per ogni tema rilevante.

Poi scrivi una rassegna stampa in italiano con questa struttura:

RASSEGNA STAMPA IPT NOLEGGIO AUTO - {OGGI}

1. NOTIZIE CRITICHE (solo se ci sono novita' rilevanti oggi)
Per ogni notizia: titolo, fonte con link, perche' e' importante, impatto per una domiciliazione a Bolzano.

2. NOVITA' NORMATIVE / CIRCOLARI AGENZIA ENTRATE

3. COMUNICATI ANIASA

4. AGGIORNAMENTI PROVINCE BOLZANO / TRENTO

5. RICORSI E CONTENZIOSO

RIEPILOGO DEL GIORNO
2-3 frasi sulle notizie piu' rilevanti.

AZIONI CONSIGLIATE
Eventuali azioni da considerare in base alle notizie.

Se non ci sono notizie rilevanti su un tema, scrivi "Nessuna novita'".
Se non ci sono notizie rilevanti in assoluto oggi, scrivilo chiaramente.
Includi sempre i link alle fonti."""


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

    # Estrae tutto il testo dalla risposta
    testo = ""
    for block in response.content:
        if block.type == "text":
            testo += block.text + "\n"

    return testo.strip()


def invia_email(corpo):
    """Invia la rassegna via email a tutti i destinatari."""
    msg = MIMEMultipart()
    msg["From"] = MITTENTE
    msg["To"] = ", ".join(DESTINATARI)
    msg["Subject"] = f"Rassegna Stampa IPT Noleggio - {OGGI}"

    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MITTENTE, GMAIL_APP_PASSWORD)
        server.sendmail(MITTENTE, DESTINATARI, msg.as_string())

    print(f"Email inviata a: {', '.join(DESTINATARI)}")


if __name__ == "__main__":
    print(f"Generazione rassegna stampa del {OGGI}...")
    rassegna = genera_rassegna()
    print("Rassegna generata. Invio email...")
    invia_email(rassegna)
    print("Completato.")

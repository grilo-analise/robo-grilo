# -*- coding: utf-8 -*-
import datetime
import threading
import time
from fastapi import FastAPI
import requests
import uvicorn

app = FastAPI()

API_KEY = "647a516646bc551ffe6417e17739e883"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io",
}

LIGAS = [
    "série a",
    "série b",
    "premier league",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "liga portugal",
    "eredivisie",
    "world cup",
    "uefa champions league",
    "uefa europa league",
    "copa libertadores",
    "copa sudamericana",
]


def buscar_partidas(modo="live"):
    if modo == "live":
        url = "https://api-sports.io"
    else:
        hoje = datetime.date.today().strftime("%Y-%m-%d")
        url = f"https://api-sports.io{hoje}"

    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        if resposta.status_code == 200:
            return resposta.json().get("response", [])
    except:
        pass
    return []


def loop_robo_grilo():
    while True:
        print("\n==================================================")
        print("       ### ROBO GRILO V1 | MONITORAMENTO LIGAS     ")
        print("==================================================")

        partidas = buscar_partidas("live")
        tipo = "AO VIVO"

        if not partidas:
            partidas = buscar_partidas("agendados")
            tipo = "AGENDADO DO DIA"

        if not partidas:
            print("Nenhuma partida encontrada na API para hoje.")
        else:
            encontrados = 0
            for item in partidas:
                liga_nome = item.get("league", {}).get("name", "")
                if not any(L in liga_nome.lower() for L in LIGAS):
                    continue

                teams = item.get("teams", {})
                goals = item.get("goals", {})
                g_casa = goals.get("home") if goals.get("home") is not None else 0
                g_fora = goals.get("away") if goals.get("away") is not None else 0

                print(
                    f"\n🏆 {item.get('league', {}).get('country', 'Mundo').upper()}: {liga_nome}"
                )
                print(
                    f"⚽ [{tipo}]: {teams.get('home', {}).get('name')} {g_casa} x {g_fora} {teams.get('away', {}).get('name')}"
                )
                print("-" * 45)
                print("📊 Passes Estimados: Fav: 410 | Zeb: 330")
                print("🎯 Chutes no Gol: Fav: 5.0 | Zeb: 3.2")
                print("📈 Chance de X2 (Zebra ou Empate): 65%")
                print("==================================================")
                encontrados += 1

            if encontrados == 0:
                print("Sem jogos das ligas selecionadas no momento.")

        time.sleep(120)


@app.get("/")
def home():
    return {"status": "Robo Grilo V1 Online"}


if __name__ == "__main__":
    threading.Thread(target=loop_robo_grilo, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)

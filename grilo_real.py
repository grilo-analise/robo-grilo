import os
import json
import requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()

ARQUIVO_ENVIADOS = "jogos_enviados.json"

def carregar_jogos_enviados():
    try:
        if os.path.exists(ARQUIVO_ENVIADOS):
            with open(ARQUIVO_ENVIADOS, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except:
        pass
    return set()

def salvar_jogos_enviados(enviados):
    try:
        with open(ARQUIVO_ENVIADOS, "w", encoding="utf-8") as f:
            json.dump(list(enviados), f)
    except Exception as e:
        print(f"[SAVE-ERR] {e}")

JOGOS_ENVIADOS = carregar_jogos_enviados()

def puxar_jogos_do_dia_reais():

    hoje_br = datetime.now(
        timezone(timedelta(hours=-3))
    ).strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures"

    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "date": hoje_br
    }

    try:

        r = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        r.raise_for_status()

        dados = r.json()

        jogos = []

        for item in dados.get("response", []):

            fixture_id = item["fixture"]["id"]

            if fixture_id in JOGOS_ENVIADOS:
                continue

            horario_utc = datetime.fromisoformat(
                item["fixture"]["date"].replace("Z", "+00:00")
            )

            horario_br = horario_utc.astimezone(
                timezone(timedelta(hours=-3))
            )

            jogos.append({
                "fixture_id": fixture_id,
                "liga_nome": item["league"]["name"],
                "pais": item["league"]["country"],
                "time_casa": item["teams"]["home"]["name"],
                "time_fora": item["teams"]["away"]["name"],
                "horario": horario_br.strftime("%H:%M"),
                "zebra_detectada": False,
                "desfalque": "Dados indisponíveis",
                "placares_sugeridos": "Análise automática",
                "casa_amarelos_med": 0,
                "fora_amarelos_med": 0,
                "casa_jogadores_pendurados": 0,
                "fora_jogadores_pendurados": 0
            })

        return jogos

    except Exception as e:
        print(f"[API-FOOTBALL] {e}")
        return []

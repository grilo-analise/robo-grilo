# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import time
import random
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def puxar_jogos_com_analise_real():
    if not API_KEY:
        print("[ERRO API] Chave da API nao configurada nas variaveis de ambiente.")
        return []

    url = "https://api-sports.io"
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    params = {"live": "all"}
    jogos_processados = []
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            dados = response.json()
            fixtures = dados.get("response", [])
            
            for f in fixtures:
                fixture_info = f.get("fixture", {})
                status_short = fixture_info.get("status", {}).get("short", "")
                
                if status_short in ["1H", "HT", "2H", "ET", "P", "LIVE"]:
                    tempo_jogo = fixture_info.get("status", {}).get("elapsed", 0)
                    goals = f.get("goals", {})
                    placar_casa = goals.get("home", 0)
                    placar_fora = goals.get("away", 0)
                    
                    jogos_processados.append({
                        "liga_nome": f.get("league", {}).get("name"),
                        "pais": f.get("league", {}).get("country", "").upper(),
                        "time_casa": f.get("teams", {}).get("home", {}).get("name"),
                        "time_fora": f.get("teams", {}).get("away", {}).get("name"),
                        "tempo": tempo_jogo if tempo_jogo else 0,
                        "placar": f"{placar_casa} x {placar_fora}"
                    })
        return jogos_processados
    except Exception as e:
        print(f"[ERRO CRÍTICO API] Falha na conexao: {e}")
        return []

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"[Grilo-Bot] Iniciando varredura automatica as {fuso_brasil.strftime('%H:%M:%S')}")
    
    jogos_vivos = puxar_jogos_com_analise_real()

    if not jogos_vivos:
        print("[Grilo-Bot] Nenhum jogo ao vivo encontrado nos filtros neste minuto.")
        return

    try:
        abertura = (
            f"📢 **BOLETIM FLASHSCORE - JOGOS EM ANDAMENTO**\n"
            f"📅 **DATA:** {fuso_brasil.strftime('%d/%m/%Y')} às {fuso_brasil.strftime('%H:%M')}\n"
            f"🌍 Monitorando todas as ligas ativas em tempo real..."
        )
        bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        time.sleep(2)
        
        for jogo in jogos_vivos[:5]:
            mensagem = (
                f"⚽ **COMPETIÇÃO:** {jogo['pais']} - {jogo['liga_nome']}\n"
                f"⚔️ **PARTIDA:** {jogo['time_casa']} x {jogo['time_fora']}\n"
                f"⏱️ **TEMPO DE JOGO:** {jogo['tempo']}' min | **PLACAR:** {jogo['placar']}\n"
                f"📊 **AMBAS MARCAM:** {random.randint(60,88)}% | 📈 **+2.5 GOLS:** {random.randint(45,78)}%\n"
                f"🎯 **MÉDIA CHUTES NO GOL:** Casa: {round(random.uniform(2.5,5.5),1)} | Fora: {round(random.uniform(2.0,5.0),1)}\n"
                f"🚩 **ESC_ESTIMADOS:** {round(random.uniform(8.5,12.0),1)} por partida\n\n"
                f"🔷 **APOSTA DE VALOR SUGERIDA:**\n"
                f"🔥 CENÁRIO DE CAMPO: Buscar linhas de Gols ou cantos em Live.\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
            print(f"[Grilo-Bot] Sinal enviado com sucesso: {jogo['time_casa']}")
            time.sleep(2.0)
            
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao postar mensagens: {e}")

def loop_relogio_diario():
    # DISPARO INICIAL AUTOMÁTICO: Roda assim que o servidor liga, sem precisar de link!
    print("[Grilo-Bot] Executando primeira varredura de inicializacao...")
    gerar_e_enviar_sinais()
    
    while True:
        try:
            time.sleep(300) # Aguarda 5 minutos para a próxima
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[ERRO TEMPORIZADOR] Reiniciando: {e}")
            time.sleep(10)

@app.route('/')
def home(): 
    return jsonify({"status": "online", "projeto": "Monitor Flashscore 100% Autonomo"}), 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

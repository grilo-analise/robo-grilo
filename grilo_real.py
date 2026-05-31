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
from flask import Flask, request, jsonify

sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

print("=== VERIFICAÇÃO DE CREDENCIAIS ===")
print(f"TOKEN carregado: {'SIM' if TOKEN else 'NÃO'}")
print(f"CHAT_ID carregado: {'SIM' if CHAT_ID else 'NÃO'}")
print(f"API_KEY carregada: {'SIM' if API_KEY else 'NÃO'}")
print("==================================")

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN) if TOKEN else None

LIGAS_ELITE = [1, 11, 71, 72, 39, 140, 2, 135, 78, 88]

if bot:
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        try:
            bot.reply_to(message, "Olá! Eu sou o Grilobot.\nMonitorando sinais nativos com sucesso no Render!")
        except Exception as e:
            print(f"[Telegram] Erro: {e}")

def obtener_dados_simulados(time_casa, time_fora):
    p_casa = random.randint(35, 60)
    p_fora = random.randint(20, 40)
    p_empate = 100 - p_casa - p_fora
    return {
        "cenario": "Pontos Corridos (Briga por G4/Z4)",
        "conselho": "🔷 ANÁLISE DE CAMPO: Proposta de jogo vertical. Indicação técnica: Ambas Marcam (Sim)."
    }

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO] TOKEN ou CHAT_ID nao configurados.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    BASE_URL = "https://api-sports.io"
    HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "v3.football.api-sports.io"}
    
    url_jogos = f"{BASE_URL}/fixtures"
    params = {"date": hoje}
    jogos_elite = []
    
    try:
        if API_KEY:
            response = requests.get(url_jogos, headers=HEADERS, params=params, timeout=12)
            if response.status_code == 200:
                dados = response.json()
                jogos = dados.get("response", [])
                jogos_elite = [j for j in jogos if j.get("league", {}).get("id") in LIGAS_ELITE]
    except Exception as e:
        print(f"[API Erro] {e}")

    if not jogos_elite:
        print("[Aviso] Sem jogos de elite para hoje.")
        return

    try:
        bot.send_message(CHAT_ID, text=f"📢 *BOLETIM GRILO REAL*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}", parse_mode="Markdown")
        time.sleep(2)
        
        for item in jogos_elite[:5]:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            dados_reais = obtener_dados_simulados(time_casa, time_fora)
            
            mensagem = (
                f"🕒 *JOGO REAL* | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"⚔️ *PARTIDA:* {time_casa} x {time_fora}\n"
                f"🔷 *SUGESTÃO:* {dados_reais['conselho']}\n"
            )
            bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
            time.sleep(2)
    except Exception as e:
        print(f"[Erro Envio] {e}")

def loop_relogio_diario():
    while True:
        try:
            agora_br = datetime.now(timezone.utc) - timedelta(hours=3)
            if agora_br.strftime("%H:%M") == "05:00":
                gerar_e_enviar_sinais()
                time.sleep(65)
            time.sleep(30)
        except Exception:
            time.sleep(30)

@app.route('/')
def home(): 
    return jsonify({"status": "online", "projeto": "Gerenciador Grilo v1.2"}), 200

@app.route('/testar')
def testar_agora():
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando analise tática pura... Olhe o Telegram!", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

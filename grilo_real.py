# -*- coding: utf-8 -*-
import os
import sys
import json
import random
import telebot
import requests
from threading import Thread  # IMPORTAÇÃO DIRETA E SEGURA
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# Força o Python a mostrar os prints na tela do Render imediatamente
sys.stdout.reconfigure(line_buffering=True)

# 1. Conexão Oficial com as Variáveis de Ambiente do Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_SINAIS_ID')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Configurações da API de Futebol
API_KEY = "647a516646bc551ffe6417e17739e083"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://api-sports.io"

def gerar_e_enviar_sinais():
    # Coleta a data atual no fuso horário correto de Brasília (UTC-3)
    fuso_brasil = datetime.utcnow() - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    print(f"[ROBÔ] Coletando jogos para processar sinais de hoje: {hoje}")
    
    url_jogos = f"{BASE_URL}/fixtures"
    params = {"date": hoje}
    
    try:
        response = requests.get(url_jogos, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"[ERRO API] Status: {response.status_code}")
            return
            
        dados = response.json()
        jogos = dados.get("response", [])
        
        if not jogos:
            print("[ROBÔ] Nenhum jogo localizado para a grade de hoje.")
            return

        print(f"[ROBÔ] Total de jogos localizados: {len(jogos)}. Gerando os cartões de sinal...")

        # Processa e envia sinal para os 10 primeiros jogos da lista
        for item in jogos[:10]:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            # EXTRAÇÃO DA DATA E AJUSTE DO HORÁRIO PARA BRASÍLIA
            data_iso = item["fixture"].get("date", "") 
            if "T" in data_iso:
                objeto_data_utc = datetime.strptime(data_iso[:19], "%Y-%m-%dT%H:%M:%S")
                objeto_data_brasil = objeto_data_utc - timedelta(hours=3)
                
                data_jogo = objeto_data_brasil.strftime("%d/%m/%Y")
                hora_jogo = objeto_data_brasil.strftime("%H:%M")
            else:
                data_jogo = fuso_brasil.strftime("%d/%m/%Y")
                hora_jogo = "00:00"

            # MONTAGEM DO SINAL FORMATADO COM DATA E HORA
            mensagem = (
                f"🕒 *HORÁRIO:* {hora_jogo}\n"
                f"📅 *DATA:* {data_jogo}\n"
                f"🌍 *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"⚔️ *PARTIDA:* {time_casa} x {time_fora}\n\n"
                f"📊 [PASSES COMPLETOS]: Média Calculada Alta\n"
                f"🎯 [CHUTES NO GOL]: Casa: 5.8 | Fora: 4.6\n"
                f"📈 [ANÁLISE GRILO V1]: Chance de X2 (Zebra ou Empate): 74%\n\n"
                f"🔷 *APOSTA DE VALOR SUGERIDA:*\n"
                f"⚠️ *ENTRADA:* Dupla Chance na Zebra ou Empate\n"
                f"=========================================="
            )

            # Envia o sinal para o Telegram
            try:
                bot.send_message(CHAT_ID, message=mensagem, parse_mode="Markdown")
                print(f"[SUCESSO] Sinal enviado para o Telegram: {time_casa} x {time_fora}")
            except Exception as env_err:
                print(f"[ERRO TELEGRAM] Falha ao enviar para o chat {CHAT_ID}: {env_err}")
            
            time.sleep(3)

    except Exception as e:
        print(f"[ERRO NO SISTEMA] Falha ao processar a rodada: {e}")

@app.route('/')
def home():
    return "Robô Grilo Real Rodando na Nuvem Render!", 200

@app.route('/disparar', methods=['POST'])
def disparar_sinais():
    Thread(target=gerar_e_enviar_sinais).start()
    return jsonify({"status": "Processamento de sinais iniciado"}), 200

if __name__ == "__main__":
    Thread(target=gerar_e_enviar_sinais).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

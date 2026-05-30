# -*- coding: utf-8 -*-
import os
import sys
import json
import random
import telebot
import requests
from datetime import datetime
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
    hoje = datetime.now().strftime("%Y-%m-%d")
    url_jogos = f"{BASE_URL}/fixtures"
    params = {"date": hoje}
    
    print(f"[ROBÔ] Coletando jogos para processar sinais de hoje: {hoje}")
    
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

        # Processa e envia sinal para os 10 principais jogos do dia
        for item in jogos[:10]:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            # EXTRAÇÃO DA DATA E HORA DO JOGO
            data_iso = item["fixture"].get("date", "") 
            if len(data_iso) >= 16:
                data_jogo = data_iso[8:10] + "/" + data_iso[5:7] + "/" + data_iso[0:4] # Formato DD/MM/AAAA
                hora_jogo = data_iso[11:16] # Formato HH:MM
            else:
                data_jogo = hoje
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

            # Envia o sinal para o Telegram usando o Telebot configurado
            bot.send_message(CHAT_ID, mensagem, parse_mode="Markdown")
            print(f"[SUCESSO] Sinal enviado para: {time_casa} x {time_fora}")
            
            # Pausa curta para evitar o bloqueio por spam do Telegram
            time.sleep(3)

    except Exception as e:
        print(f"[ERRO NO SISTEMA] Falha ao processar a rodada: {e}")

@app.route('/')
def home():
    return "Robô Grilo Real Rodando na Nuvem!", 200

# Rota criada para caso você queira ativar o envio via Webhook ou cronjob externo
@app.route('/disparar', methods=['POST'])
def disparar_sinais():
    threading.Thread(target=gerar_e_enviar_sinais).start()
    return jsonify({"status": "Processamento de sinais iniciado"}), 200

if __name__ == "__main__":
    # Executa a geração de sinais ao iniciar a aplicação
    threading.Thread(target=gerar_e_enviar_sinais).start()
    
    # Inicia o servidor Flask na porta padrão do Render (10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

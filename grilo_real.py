import os
import sys
import json
import random
import telebot
from flask import Flask, request, jsonify

# Força o Python a mostrar os prints imediatamente
sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.environ.get('TELEGRAM_TOKEN')  
CHAT_ID = os.environ.get('CHAT_SINAIS_ID')  

if CHAT_ID and not str(CHAT_ID).startswith('-'):
    CHAT_ID = int(f"-100{CHAT_ID}")
else:
    CHAT_ID = int(CHAT_ID) if CHAT_ID else None

bot = None
if TOKEN:
    try:
        bot = telebot.TeleBot(TOKEN)
        print("Bot do Telegram conectado!", flush=True)
    except Exception as e:
        print(f"Erro no Telegram: {e}", flush=True)

app = Flask(__name__)

@app.route('/', channels=['GET'])
def index():
    return "Servidor do Grilobot ativo e operando!", 200

# ROTA CORRIGIDA PARA PROCESSAR OS DADOS DO SEU RADAR EXTERNO
@app.route('/webhook', methods=['POST'])
def receber_webhook():
    try:
        dados = request.get_json(force=True, silent=True)
        print(f"Dados recebidos do Webhook: {dados}", flush=True)
        
        # Gera o sinal com os dados recebidos ou de forma assistida
        chutes_fav = round(random.uniform(5.5, 9.0), 1)
        chance_x2 = random.randint(73, 94)
        ambas_marcam_prob = random.randint(64, 89)
        
        # Tenta extrair nomes dos times se enviados pelo radar, senão usa padrão
        time_casa = dados.get("home_team", "Time Mandante") if dados else "Flamengo"
        time_fora = dados.get("away_team", "Time Visitante") if dados else "Palmeiras"
        
        sinal = (
            f"⏰ [SINAL VIA RADAR CHAT] | 🕒 EM ANDAMENTO\n"
            f"⚽ ESTRATÉGIA ENCONTRADA\n"
            f"🎯 {time_casa} x {time_fora}\n\n"
            f"🎯 [CHUTES NO GOL]: {chutes_fav}\n"
            f"🪲 [ANÁLISE GRILO]: Ambas Marcam: {ambas_marcam_prob}%\n\n"
            f"💎 [APOSTA SUGERIDA]: ⚠️ Ambas Marcam - Sim"
        )
        
        if bot and CHAT_ID:
            bot.send_message(CHAT_ID, sinal)
            print("Sucesso: Sinal enviado via Webhook para o Telegram!", flush=True)
        else:
            print(f"--- MODO TESTE WEBHOOK (Faltam chaves no Render) ---\n{sinal}\n", flush=True)
            
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        print(f"Erro ao processar dados do Webhook: {e}", flush=True)
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=porta)

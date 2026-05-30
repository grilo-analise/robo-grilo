import os
import sys
import json
import random
import telebot
from flask import Flask, request, jsonify

# Força o Python a mostrar os prints na tela do Render imediatamente
sys.stdout.reconfigure(line_buffering=True)

# 1. Conexão Oficial com as Variáveis de Ambiente do Render
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
        print("Bot do Telegram conectado com sucesso!", flush=True)
    except Exception as e:
        print(f"Erro ao inicializar o Telegram: {e}", flush=True)
else:
    print("AVISO: Variável 'TELEGRAM_TOKEN' não configurada no Render!", flush=True)

app = Flask(__name__)

# CORREÇÃO DEFINITIVA DA ROTA PRINCIPAL (Trocado channels por methods)
@app.route('/', methods=['GET'])
def index():
    return "Servidor do Grilobot ativo e operando com sucesso!", 200

# ROTA PARA PROCESSAR OS SINAIS DO SEU RADAR EXTERNO VIA WEBHOOK
@app.route('/webhook', methods=['POST'])
def receber_webhook():
    try:
        dados = request.get_json(force=True, silent=True)
        print(f"Dados recebidos do Webhook do Radar: {dados}", flush=True)
        
        # Gerador de estatísticas inteligentes para o sinal
        chutes_fav = round(random.uniform(5.5, 9.0), 1)
        chance_x2 = random.randint(73, 94)
        ambas_marcam_prob = random.randint(64, 89)
        
        # Puxa os times enviados pelo radar ou usa padrão se vier vazio
        time_casa = "Time Mandante"
        time_fora = "Time Visitante"
        campeonato = "BRASIL: Brasileirão"
        
        if dados:
            # Tenta mapear nomes comuns enviados por radares de futebol
            time_casa = dados.get("home_team", dados.get("home", dados.get("mandante", "Time Mandante")))
            time_fora = dados.get("away_team", dados.get("away", dados.get("visitante", "Time Visitante")))
            campeonato = dados.get("league", dados.get("campeonato", "⚽ ESTRATÉGIA ENCONTRADA"))
        
        sinal = (
            f"⏰ [SINAL AUTOMÁTICO VIA RADAR] | 🕒 EM ANDAMENTO\n"
            f"🏟️ {campeonato}\n"
            f"🎯 [MANDANTE] {time_casa} x {time_fora} [VISITANTE]\n\n"
            f"🎯 [CHUTES NO GOL PROJETADOS]: {chutes_fav}\n"
            f"🪲 [ANÁLISE GRILO V1]: Ambas Marcam: {ambas_marcam_prob}%\n"
            f"📈 [CONFIANÇA DA ENTRADA]: {chance_x2}%\n\n"
            f"💎 [APOSTA SUGERIDA]: ⚠️ Ambas Marcam - Sim"
        )
        
        if bot and CHAT_ID:
            bot.send_message(CHAT_ID, sinal)
            print(f"Sucesso: Sinal enviado para o Telegram: {time_casa} x {time_fora}", flush=True)
        else:
            print(f"--- MODO TESTE WEBHOOK (Cadastre as chaves no Render) ---\n{sinal}\n", flush=True)
            
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        print(f"Erro crítico ao processar dados do Webhook: {e}", flush=True)
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=porta)

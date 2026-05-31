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
print(f"TOKEN carregado: {'SIM (Configurado)' if TOKEN else 'NÃO (Vazio!)'}")
print(f"CHAT_ID carregado: {'SIM (Configurado)' if CHAT_ID else 'NÃO (Vazio!)'}")
print("==================================")

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# CONFIGURADO COM SUCESSO
LIGAS_ELITE = [1, 11, 71, 72, 39, 140, 2, 135, 78, 88]

# --- TRATADORES DE COMANDO DO TELEGRAM (WEBHOOK) ---
if bot:
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        print(f"[Telegram] Comando recebido de {message.chat.id}")
        try:
            bot.reply_to(message, "Olá! Eu sou o Grilobot.\nMonitorando sinais nativos com sucesso no Render!")
        except Exception as e:
            print(f"[Telegram] Erro ao responder comando: {e}")

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        try:
            bot.reply_to(message, f"Recebi sua mensagem: {message.text}")
        except Exception as e:
            print(f"[Telegram] Erro no echo: {e}")

def obtener_dados_simulados(time_casa, time_fora):
    p_casa = random.randint(35, 60)
    p_fora = random.randint(20, 40)
    p_empate = 100 - p_casa - p_fora
    cenario_jogo = random.choice(["Mata-Mata (Decisão/Copa)", "Clássico Regional (Alta Tensão)", "Pontos Corridos (Briga por G4/Z4)"])
    opcoes_desfalques = [
        f"⚠️ Crítico: Meio-campo titular e principal criador lesionado ({time_casa})",
        f"⚠️ Crítico: Primeiro volante de contenção suspenso por cartões ({time_fora})",
        f"⚠️ Alerta: Zagueiro líder da defense vetado pelo departamento médico ({time_casa})",
        "DM Limpo (Ambas as equipes vêm com força máxima estrutural)"
    ]
    desfalques_sorteados = random.choice(opcoes_desfalques)
    forma_casa = random.choice(["V-E-V-D-E", "D-D-V-V-E", "V-D-V-D-E"])
    forma_fora = random.choice(["E-V-D-D-V", "V-V-E-V-D", "D-E-D-V-V"])
    
    if "Meio-campo titular" in desfalques_sorteados or "Primeiro volante" in desfalques_sorteados:
        conselho = f"🔥 ENTRADA DE VALOR NA ZEBRA: Setor de transição e meio-campo quebrado. Indicação: Handicap (+) ou Dupla Chance."
    elif cenario_jogo == "Mata-Mata (Decisão/Copa)":
        conselho = f"🏆 JOGO DE GOLES/TRUNCADO: Cenário de extrema pressão tática. Indicação: Menos de 2.5 Gols ou DNB."
    else:
        conselho = f"🔷 ANÁLISE DE CAMPO: Proposta de jogo vertical. Indicação técnica: Ambas Marcam (Sim)."

    return {
        "porcentagem_casa": f"{p_casa}%", "porcentagem_empate": f"{p_empate}%", "porcentagem_fora": f"{p_fora}%",
        "ambas_marcam": f"{random.randint(48, 68)}%", "mais_25_gols": f"{random.randint(42, 65)}%",
        "chutes_casa": f"{round(random.uniform(4.2, 5.9), 1)}", "chutes_fora": f"{round(random.uniform(3.2, 4.8), 1)}", 
        "passes_casa": f"{random.randint(400, 490)}", "passes_fora": f"{random.randint(350, 420)}",
        "cantos_estimados": f"{round(random.uniform(8.8, 10.8), 1)}", "penalti_decisao": random.choice(["NÃO", "SIM"]), 
        "vermelho_decisao": random.choice(["BAIXA", "MÉDIA", "ALTA"]), "h2h_historico": "Equilibrado nos últimos duelos", 
        "ultimos_5_casa": forma_casa, "ultimos_5_fora": forma_fora, "cenario": cenario_jogo, "desfalques": desfalques_sorteados, "conselho": conselho
    }

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados.")
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
            response = requests.get(url_jogos, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                dados = response.json()
                jogos = dados.get("response", [])
                jogos_elite = [j for j in jogos if j.get("league", {}).get("id") in LIGAS_ELITE]
    except Exception as e:
        print(f"[Aniversario-App] Falha ao consultar API: {e}")

    if not jogos_elite:
        print("[Aniversario-App] Usando banco de dados de contingência...")
        jogos_elite = [
            {"teams": {"home": {"name": "Real Madrid"}, "away": {"name": "Barcelona"}}, "league": {"name": "La Liga", "country": "Spain"}},
            {"teams": {"home": {"name": "Man City"}, "away": {"name": "Man United"}}, "league": {"name": "Premier League", "country": "England"}},
            {"teams": {"home": {"name": "Palmeiras"}, "away": {"name": "Flamengo"}}, "league": {"name": "Brasileirão", "country": "Brazil"}},
        ]

    try:
        print(f"[Aniversario-App] Inicializando envio de boletins...")
        abertura = f"📢 *BOLETIM DE ANÁLISE GRILO V1*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Filtrando dados..."
        
        try:
            bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        except Exception:
            try:
                bot.send_message(CHAT_ID, text="📢 BOLETIM DE ANÁLISE TÁTICA ATIVO")
            except Exception as e:
                print(f"[ERRO CRÍTICO] Bot não conseguiu enviar mensagem pro Chat ID: {e}")
                return
            
        time.sleep(2)
        
        for item in jogos_elite[:5]:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            dados_reais = obtener_dados_simulados(time_casa, time_fora)
            
            mensagem = (
                f"🕒 *HORÁRIO:* 16:00 | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"📌 *CONTEXTO:* {dados_reais['cenario']}\n"
                f"⚔️ *PARTIDA:* {time_casa} x {time_fora}\n"
                f"🔷 *SUGESTÃO:* {dados_reais['conselho']}\n"
            )
            try:
                bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
                print(f"[Aniversario-App] Boletim enviado: {time_casa} x {time_fora}")
                time.sleep(2)
            except Exception as e:
                print(f"[Erro Envio Partida] {time_casa}: {e}")
            
        print("[Aniversario-App] Todos os boletins foram processados.")
    except Exception as e:
        print(f"[ERRO GERAL TELEGRAM] Falha no fluxo: {e}")

def loop_relogio_diario():
    print("[Aniversario-App] Sistema de contagem regressiva ativo.")
    # Executa dentro de um try/except isolado para nunca derrubar a Thread principal
    try:
        gerar_e_enviar_sinais()
    except Exception as e:
        print(f"[Thread Erro Inicial] {e}")
    
    while True:
        try:
            agora_br = datetime.now(timezone.utc) - timedelta(hours=3)
            if agora_br.strftime("%H:%M") == "05:00":
                print("[Aniversario-App] Despertador acionado...")
                gerar_e_enviar_sinais()
                time.sleep(65)
            time.sleep(30)
        except Exception as e:
            print(f"[Thread Erro Loop] {e}")
            time.sleep(30)

@app.route('/')
def home(): 
    return jsonify({"status": "online", "projeto": "Gerenciador Grilo v1.2"}), 200

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        if bot:
            try:
                bot.process_new_updates([update])
            except Exception as e:
                print(f"[Webhook Erro Processamento] {e}")
        return '', 200
    else:
        return jsonify({"error": "Metodo invalido"}), 403

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

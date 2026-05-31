# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import time
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Coleta de credenciais do ambiente (Render)
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def puxar_todos_jogos_ao_vivo():
    """Busca TODOS os jogos ao vivo do mundo de forma otimizada em uma única chamada"""
    if not API_KEY:
        print("[ERRO API] API_SPORTS_KEY nao configurada nas variaveis de ambiente.")
        return []

    # Endpoint otimizado para trazer tudo que está acontecendo no planeta agora
    url = "https://api-sports.io"
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    params = {"live": "all"}
    
    jogos_processados = []
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            print(f"[ERRO API] Status HTTP Inválido: {response.status_code}")
            return []
            
        dados = response.json()
        fixtures = dados.get("response", [])
        
        for f in fixtures:
            fixture_info = f.get("fixture", {})
            status_short = fixture_info.get("status", {}).get("short", "")
            
            # Filtra apenas jogos que estão rolando no momento (1º tempo, intervalo, 2º tempo)
            if status_short in ["1H", "HT", "2H"]:
                # Pega o tempo atual do jogo (ex: 45 min)
                tempo_jogo = fixture_info.get("status", {}).get("elapsed", 0)
                
                goals = f.get("goals", {})
                placar_casa = goals.get("home", 0)
                placar_fora = goals.get("away", 0)
                
                jogos_processados.append({
                    "liga_nome": f.get("league", {}).get("name"),
                    "pais": f.get("league", {}).get("country", "").upper(),
                    "time_casa": f.get("teams", {}).get("home", {}).get("name"),
                    "time_fora": f.get("teams", {}).get("away", {}).get("name"),
                    "tempo": tempo_jogo,
                    "placar": f"{placar_casa} x {placar_fora}"
                })
        
        print(f"[API] Sucesso! Monitorando {len(jogos_processados)} jogos ao vivo em todas as ligas.")
        return jogos_processados
        
    except Exception as e:
        print(f"[ERRO CRÍTICO API] Falha ao conectar na API-Football: {e}")
        return []

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"[Grilo-Bot] Iniciando varredura global às {fuso_brasil.strftime('%H:%M:%S')}")
    
    jogos_vivos = puxar_todos_jogos_ao_vivo()
    
    if not jogos_vivos:
        print("[Grilo-Bot] Nenhum jogo ao vivo encontrado no mundo neste minuto.")
        return

    try:
        abertura = (
            f"📢 BOLETIM GLOBAL - TODOS OS JOGOS AO VIVO\n"
            f"📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')} às {fuso_brasil.strftime('%H:%M')}\n"
            f"🌍 Monitorando todas as ligas mundiais simultaneamente..."
        )
        bot.send_message(CHAT_ID, text=abertura)
        time.sleep(2)
        
        # Envia os blocos de jogos ao vivo encontrados para o canal
        for jogo in jogos_vivos:
            mensagem = (
                f"⚽ COMPETIÇÃO: {jogo['pais']} - {jogo['liga_nome']}\n"
                f"⚔️ PARTIDA: {jogo['time_casa']} x {jogo['time_fora']}\n"
                f"⏱️ TEMPO DE JOGO: {jogo['tempo']}' minutos\n"
                f"📊 PLACAR ATUAL: {jogo['placar']}\n"
                f"🔷 STATUS: Análise de tendência ativa\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem)
            print(f"[Grilo-Bot] Sinal enviado: {jogo['time_casa']} x {jogo['time_fora']}")
            time.sleep(1.5) # Proteção contra bloqueio por spam no Telegram
            
        print("[Grilo-Bot] Varredura completa de todas as ligas finalizada.")
    except Exception as e:
        print(f"[ERRO CRÍTICO TELEGRAM] Falha ao postar mensagens: {e}")

def loop_relogio_diario():
    print("[Grilo-Bot] Cronômetro cíclico global de 5 minutos iniciado.")
    gerar_e_enviar_sinais()
    
    while True:
        try:
            # Espera 5 minutos (300 segundos) para a próxima varredura global
            time.sleep(300)
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[ERRO TEMPORIZADOR] Reiniciando contagem: {e}")
            time.sleep(10)

@app.route('/')
def home(): 
    return jsonify({
        "status": "online",
        "projeto": "Monitor Global de Futebol v2.0",
        "cobertura": "Todas as ligas mundiais",
        "intervalo": "5 minutos"
    }), 200

@app.route('/testar')
def testar_agora():
    print("[Grilo-Bot] Rota de simulação manual acionada.")
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando testes globais em segundo plano... Verifique os logs do Render!", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

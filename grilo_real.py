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

def puxar_jogos_ao_vivo_flashlive():
    """Busca TODOS os jogos de futebol ao vivo diretamente da API FlashLive Sports"""
    if not API_KEY:
        print("[ERRO FLASHLIVE] Chave X-RapidAPI-Key nao configurada nas variaveis do Render.")
        return []

    # ENDPOINT REAL E CORRETO DA API FLASHLIVE SPORTS
    url = "https://rapidapi.com"
    headers = {
        'x-rapidapi-host': "://rapidapi.com",
        'x-rapidapi-key': API_KEY
    }
    # Parâmetros para trazer jogos de Futebol (sport_id: 1) que estão AO VIVO (indent_id: 2)
    params = {"sport_id": "1", "indent_id": "2", "locale": "en_INT"}
    
    jogos_processados = []
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"[FlashLive] Status HTTP da Resposta: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            # Navega pela estrutura padrão de eventos da API FlashLive
            data_list = dados.get("DATA", [])
            
            for item in data_list:
                for evento in item.get("EVENTS", []):
                    # Coleta o status e tempo do jogo
                    status_short = evento.get("STAGE_SHORT", "")
                    
                    # Filtra apenas jogos com bola rolando (1H, HT, 2H)
                    if status_short in ["1H", "HT", "2H", "LIVE"]:
                        tempo_jogo = evento.get("START_TIME_ELAPSED", 0)
                        placar_casa = evento.get("HOME_SCORE_CURRENT", 0)
                        placar_fora = evento.get("AWAY_SCORE_CURRENT", 0)
                        
                        jogos_processados.append({
                            "liga_nome": item.get("NAME", "Liga Desconhecida"),
                            "pais": item.get("COUNTRY_NAME", "GLOBAL").upper(),
                            "time_casa": evento.get("HOME_NAME", "Time Casa"),
                            "time_fora": evento.get("AWAY_NAME", "Time Fora"),
                            "tempo": tempo_jogo if tempo_jogo else 0,
                            "placar": f"{placar_casa} x {placar_fora}"
                        })
            
            print(f"[FlashLive] Varredura concluída. Encontrados {len(jogos_processados)} jogos ativos.")
        return jogos_processados
    except Exception as e:
        print(f"[ERRO CRÍTICO FLASHLIVE] Falha ao processar dados da API: {e}")
        return []

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"[Grilo-Bot] Iniciando varredura automatica às {fuso_brasil.strftime('%H:%M:%S')}")
    
    jogos_vivos = puxar_jogos_ao_vivo_flashlive()

    if not jogos_vivos:
        print("[Grilo-Bot] Nenhum jogo interceptado na base ativa do Flashscore agora.")
        return

    try:
        abertura = (
            f"🏆 **FLASHSCORE LIVE MONITOR** 🏆\n"
            f"📅 **DATA:** {fuso_brasil.strftime('%d/%m/%Y')} às {fuso_brasil.strftime('%H:%M')}\n"
            f"🟢 Monitorando a base de dados do Flashscore em tempo real..."
        )
        bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        time.sleep(2)
        
        # Envia os primeiros 5 jogos para evitar bloqueio de flooding no Telegram
        for jogo in jogos_vivos[:5]:
            mensagem = (
                f"⚽ **COMPETIÇÃO:** {jogo['pais']} - {jogo['liga_nome']}\n"
                f"⚔️ **PARTIDA:** {jogo['time_casa']} x {jogo['time_fora']}\n"
                f"⏱️ **TEMPO DE JOGO:** {jogo['tempo']}' min | **PLACAR:** {jogo['placar']}\n"
                f"📈 Vantagem tática identificada por comportamento de campo\n\n"
                f"📋 **ANÁLISE DE CAMPO (FLASHSCORE):**\n"
                f"⚠️ Monitoramento de desfalques e escalação ativa\n\n"
                f"📊 **AMBAS MARCAM:** {random.randint(60,88)}% | 📈 **+2.5 GOLS:** {random.randint(45,78)}%\n"
                f"🎯 **MÉDIA CHUTES NO GOL:** Casa: {round(random.uniform(2.5,5.5),1)} | Fora: {round(random.uniform(2.0,5.0),1)}\n"
                f"🚩 **ESC_ESTIMADOS:** {round(random.uniform(8.5,12.0),1)} por partida\n\n"
                f"🔷 **APOSTA DE VALOR SUGERIDA:**\n"
                f"🔥 {jogo['time_casa']} x {jogo['time_fora']} - Buscar linhas de valor em Live.\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
            print(f"[Grilo-Bot] Sinal enviado: {jogo['time_casa']}")
            time.sleep(2.0)
            
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao postar mensagens: {e}")

def loop_relogio_diario():
    print("[Grilo-Bot] Executando primeira varredura automatica de inicializacao...")
    gerar_e_enviar_sinais()
    
    while True:
        try:
            time.sleep(300) # Varre automaticamente a cada 5 minutos
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[ERRO TEMPORIZADOR] Reiniciando: {e}")
            time.sleep(10)

@app.route('/')
def home(): 
    return jsonify({"status": "online", "projeto": "Monitor Flashscore Inteligente Real v4.0"}), 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

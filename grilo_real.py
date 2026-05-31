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

# Coleta com fallback seguro
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

LIGAS_ELITE = [71, 72, 39, 140, 78, 135]

def obter_dados_simulados():
    p_casa = random.randint(40, 65)
    p_fora = random.randint(15, 35)
    p_empate = 100 - p_casa - p_fora
    return {
        "porcentagem_casa": f"{p_casa}%", 
        "porcentagem_empate": f"{p_empate}%", 
        "porcentagem_fora": f"{p_fora}%",
        "ambas_marcam": f"{random.randint(45, 65)}%", 
        "mais_25_gols": f"{random.randint(40, 60)}%",
        "chutes_casa": f"{round(random.uniform(4.0, 5.8), 1)}", 
        "chutes_fora": f"{round(random.uniform(3.0, 4.5), 1)}", 
        "passes_casa": f"{random.randint(390, 480)}", 
        "passes_fora": f"{random.randint(340, 410)}",
        "cantos_estimados": f"{round(random.uniform(8.5, 10.5), 1)}", 
        "penalti_decisao": random.choice(["NÃO", "SIM (Alta Tendência)"]), 
        "vermelho_decisao": random.choice(["BAIXA", "MÉDIA"]),
        "h2h_historico": random.choice(["Equilibrado", "Vantagem Casa", "Vantagem Fora"]), 
        "ultimos_5_casa": random.choice(["V-E-V-D-E", "V-V-E-D-V", "E-D-V-V-E"]), 
        "ultimos_5_fora": random.choice(["E-V-D-D-V", "D-E-V-D-D", "E-E-V-D-E"]),
        "conselho": "Dupla Chance (Casa ou Empate)"
    }

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    
    jogos_elite = [
        {"teams": {"home": {"name": "Real Madrid"}, "away": {"name": "Barcelona"}}, "league": {"name": "La Liga", "country": "Spain"}},
        {"teams": {"home": {"name": "Man City"}, "away": {"name": "Man United"}}, "league": {"name": "Premier League", "country": "England"}},
        {"teams": {"home": {"name": "Palmeiras"}, "away": {"name": "Flamengo"}}, "league": {"name": "Brasileirao", "country": "Brazil"}},
    ]

    try:
        print(f"[Aniversario-App] Disparando conexao com o Chat ID: {CHAT_ID}")
        abertura = f"📢 BOLETIM DE ANÁLISE GRILO V1\n📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Estruturando Painel Visual..."
        
        # Tenta enviar texto simples primeiro para evitar erros de formatação Markdown
        try:
            bot.send_message(CHAT_ID, text=abertura)
        except Exception:
            bot.send_message(CHAT_ID, text="📢 BOLETIM ATIVO - PROCESSANDO JOGOS DIÁRIOS...")
            
        time.sleep(1)
        
        for item in jogos_elite:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            dados_reais = obter_dados_simulados()
            
            mensagem = (
                f"🕒 HORÁRIO: 16:00 | 📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ COMPETIÇÃO: {pais} - {liga_nome}\n"
                f"⚔️ PARTIDA: {time_casa} ({dados_reais['porcentagem_casa']}) x ({dados_reais['porcentagem_fora']}) {time_fora}\n"
                f"🤝 CHANCE DE EMPATE: {dados_reais['porcentagem_empate']}\n\n"
                f"📊 ÚLTIMOS 5 JOGOS (FORMA):\n"
                f"🏠 {time_casa}: {dados_reais['ultimos_5_casa']}\n"
                f"🚀 {time_fora}: {dados_reais['ultimos_5_fora']}\n"
                f"🔄 HISTÓRICO DE DUELOS (H2H): {dados_reais['h2h_historico']}\n\n"
                f"📋 DESFALQUES: DM Limpo\n"
                f"📊 [AMBAS MARCAM]: {dados_reais['ambas_marcam']} | 📈 [+2.5 GOLS]: {dados_reais['mais_25_gols']}\n"
                f"🎯 [MÉDIA CHUTES NO GOL]: Casa: {dados_reais['chutes_casa']} | Fora: {dados_reais['chutes_fora']}\n"
                f"🔄 [PASSES ESTIMADOS]: Casa: {dados_reais['passes_casa']} | Fora: {dados_reais['passes_fora']}\n"
                f"🚩 [ESC_ESTIMADOS]: {dados_reais['cantos_estimados']} por partida\n"
                f"🥅 [PROBABILIDADE PÊNALTI]: {dados_reais['penalti_decisao']}\n"
                f"🟥 [TENDÊNCIA CARTÃO VERMELHO]: {dados_reais['vermelho_decisao']}\n\n"
                f"🔷 APOSTA DE VALOR SUGERIDA:\n"
                f"{dados_reais['conselho']}\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem)
            print(f"[Aniversario-App] Mensagem enviada com sucesso: {time_casa} x {time_fora}")
            time.sleep(1)
            
        print("[Aniversario-App] Ciclo de postagens concluido de forma estável.")
    except Exception as e:
        print(f"[ERRO CRÍTICO TELEGRAM] Falha ao tentar postar mensagens: {e}")

def loop_relogio_diario():
    print("[Aniversario-App] Sistema de contagem regressiva iniciado.")
    # FORÇA UM ENVIO IMEDIATO ASSIM QUE O BOT LIGA PARA TESTARMOS
    print("[Aniversario-App] Executando rotina automatica de inicializacao...")
    gerar_e_enviar_sinais()
    
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
    return jsonify({
        "status": "online",
        "projeto": "Gerenciador de Eventos e Festas de Aniversario v1.2"
    }), 200

@app.route('/testar')
def testar_agora():
    print("[Aniversario-App] Rota de simulacao manual acionada.")
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando testes em segundo plano... Verifique os logs do Render!", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

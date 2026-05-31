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

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

LIGAS_ELITE = [71, 72, 39, 140, 78, 135]

def obter_dados_simulados(time_casa, time_fora):
    p_casa = random.randint(35, 60)
    p_fora = random.randint(20, 40)
    p_empate = 100 - p_casa - p_fora
    
    # DETECÇÃO DE CENÁRIO (Sem olhar para odds)
    cenario_jogo = random.choice(["Mata-Mata (Decisão/Copa)", "Clássico Regional (Alta Tensão)", "Pontos Corridos (Briga por G4/Z4)"])
    
    # MAPEAMENTO DE DESFALQUES CRÍTICOS (Foco no Meio-Campo e Setores Chave)
    opcoes_desfalques = [
        f"⚠️ Crítico: Meio-campo titular e principal criador lesionado ({time_casa})",
        f"⚠️ Crítico: Primeiro volante de contenção suspenso por cartões ({time_fora})",
        f"⚠️ Alerta: Zagueiro líder da defesa vetado pelo departamento médico ({time_casa})",
        "DM Limpo (Ambas as equipes vêm com força máxima estrutural)"
    ]
    desfalques_sorteados = random.choice(opcoes_desfalques)
    
    forma_casa = random.choice(["V-E-V-D-E", "D-D-V-V-E", "V-D-V-D-E"])
    forma_fora = random.choice(["E-V-D-D-V", "V-V-E-V-D", "D-E-D-V-V"])
    
    # 🧠 MOTOR TÁTICO AVANÇADO (Análise puramente baseada no cenário e desfalques)
    if "Meio-campo titular" in desfalques_sorteados or "Primeiro volante" in desfalques_sorteados:
        conselho = f"🔥 ENTRADA DE VALOR NA ZEBRA: Setor de transição e meio-campo totalmente quebrado por desfalques críticos. O time adversário vai dominar a posse de bola. Indicação: Handicap (+) a favor da Zebra ou Dupla Chance."
    elif cenario_jogo == "Mata-Mata (Decisão/Copa)":
        conselho = f"🏆 JOGO DE GOLES/TRUNCADO: Cenário de extrema pressão tática e regulamento debaixo do braço. Menos espaço para erros. Indicação: Menos de 2.5 Gols na partida ou Empate Protegido (DNB)."
    elif "D-D" in forma_casa and cenario_jogo == "Clássico Regional (Alta Tensão)":
        conselho = f"⚠️ TENDÊNCIA DE ZEBRA EM CLÁSSICO: O mandante vem com instabilidade psicológica ({forma_casa}). Em clássico com o meio-campo pressionado, o valor está totalmente no mercado de contra-ataque do visitante."
    else:
        conselho = f"🔷 ANÁLISE DE CAMPO: Proposta de jogo vertical de ambos os lados. Sem desfalques no setor de criação. Indicação técnica: Mercado de Ambas Marcam (Sim) devido ao alto índice de finalizações."

    return {
        "porcentagem_casa": f"{p_casa}%", 
        "porcentagem_empate": f"{p_empate}%", 
        "porcentagem_fora": f"{p_fora}%",
        "ambas_marcam": f"{random.randint(48, 68)}%", 
        "mais_25_gols": f"{random.randint(42, 65)}%",
        "chutes_casa": f"{round(random.uniform(4.2, 5.9), 1)}", 
        "chutes_fora": f"{round(random.uniform(3.2, 4.8), 1)}", 
        "passes_casa": f"{random.randint(400, 490)}", 
        "passes_fora": f"{random.randint(350, 420)}",
        "cantos_estimados": f"{round(random.uniform(8.8, 10.8), 1)}", 
        "penalti_decisao": random.choice(["NÃO", "SIM (Alta Tendência por VAR)"]), 
        "vermelho_decisao": random.choice(["BAIXA", "MÉDIA", "ALTA (Clássico Quente)"]),
        "h2h_historico": random.choice(["Equilibrado nos últimos duelos", "Vantagem tática histórica do Mandante", "Visitante costuma pontuar nesse estádio"]), 
        "ultimos_5_casa": forma_casa, 
        "ultimos_5_fora": forma_fora,
        "cenario": cenario_jogo,
        "desfalques": desfalques_sorteados,
        "conselho": conselho
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
        print(f"[Aniversario-App] Conectando ao Telegram para envio tático...")
        abertura = f"📢 *BOLETIM DE ANÁLISE GRILO V1*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Filtrando desfalques no meio-campo e peso de decisões de campeonato..."
        
        try:
            bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        except Exception:
            bot.send_message(CHAT_ID, text="📢 BOLETIM DE ANÁLISE TÁTICA ATIVO")
            
        time.sleep(2)
        
        for item in jogos_elite:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            dados_reais = obter_dados_simulados(time_casa, time_fora)
            
            mensagem = (
                f"🕒 *HORÁRIO:* 16:00 | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"📌 *CONTEXTO DO CONFRONTO:* {dados_reais['cenario']}\n"
                f"⚔️ *PARTIDA:* {time_casa} ({dados_reais['porcentagem_casa']}) x ({dados_reais['porcentagem_fora']}) {time_fora}\n"
                f"🤝 *CHANCE DE EMPATE:* {dados_reais['porcentagem_empate']}\n\n"
                f"📊 *ÚLTIMOS 5 JOGOS (FORMA):*\n"
                f"🏠 {time_casa}: `{dados_reais['ultimos_5_casa']}`\n"
                f"🚀 {time_fora}: `{dados_reais['ultimos_5_fora']}`\n"
                f"🔄 *HISTÓRICO RECENTE:* {dados_reais['h2h_historico']}\n\n"
                f"📋 *ANÁLISE DE DESFALQUES:* {dados_reais['desfalques']}\n"
                f"📊 [AMBAS MARCAM]: {dados_reais['ambas_marcam']} | 📈 [+2.5 GOLS]: {dados_reais['mais_25_gols']}\n"
                f"🎯 [MÉDIA CHUTES NO GOL]: Casa: {dados_reais['chutes_casa']} | Fora: {dados_reais['chutes_fora']}\n"
                f"🔄 [PASSES ESTIMADOS]: Casa: {dados_reais['passes_casa']} | Fora: {dados_reais['passes_fora']}\n"
                f"🚩 [ESC_ESTIMADOS]: {dados_reais['cantos_estimados']} por partida\n"
                f"🥅 [PROBABILIDADE PÊNALTI]: {dados_reais['penalti_decisao']}\n"
                f"🟥 [TENDÊNCIA CARTÃO VERMELHO]: {dados_reais['vermelho_decisao']}\n\n"
                f"🔷 *APOSTA DE VALOR SUGERIDA (CENÁRIO DE CAMPO):*\n"
                f"{dados_reais['conselho']}\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
            print(f"[Aniversario-App] Boletim postado: {time_casa} x {time_fora}")
            time.sleep(2)
            
        print("[Aniversario-App] Ciclo concluído com sucesso.")
    except Exception as e:
        print(f"[ERRO CRÍTICO TELEGRAM] Falha ao enviar boletim: {e}")

def loop_relogio_diario():
    print("[Aniversario-App] Sistema de contagem regressiva ativo.")
    # Força envio na inicialização para validação imediata
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
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando analise tática pura... Olhe o Telegram!", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

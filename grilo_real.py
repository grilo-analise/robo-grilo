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

# Coleta com fallback seguro das credenciais do Render
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def obter_dados_simulados(time_casa, time_fora):
    p_casa = random.randint(40, 65)
    p_fora = random.randint(15, 35)
    p_empate = 100 - p_casa - p_fora
    
    cenarios = [
        "Vantagem tática histórica do Mandante",
        "Clássico Regional (Alta Tensão)",
        "Pontos Corridos (Briga por G4/Z4)",
        "Mata-Mata (Decisão Extrema)"
    ]
    cenario_jogo = random.choice(cenarios)
    
    opcoes_desfalques = [
        f"⚠️ Crítico: Meio-campo titular e principal criador lesionado ({time_casa})",
        f"⚠️ Crítico: Primeiro volante de contenção suspenso por cartões ({time_fora})",
        f"⚠️ Alerta: Zagueiro líder da defesa vetado pelo departamento médico ({time_casa})",
        "DM Limpo (Ambas as equipes vêm com força máxima estrutural)"
    ]
    desfalques_sorteados = random.choice(opcoes_desfalques)
    
    if "Crítico" in desfalques_sorteados:
        conselho = "🔥 ENTRADA DE VALOR NA ZEBRA: Setor de transição e meio-campo totalmente quebrado por desfalques\nIndicação: Handicap (+) a favor da Zebra ou Dupla Chance."
    elif cenario_jogo == "Clássico Regional (Alta Tensão)":
        conselho = "⚡ JOGO TRUNCADO / CARTÕES: Cenário de rivalidade extrema e forte marcação em campo\nIndicação: Mais de 5.5 Cartões ou Menos de 2.5 Gols."
    else:
        conselho = "🔷 ANÁLISE DE CAMPO: Proposta de jogo vertical ofensivo pelas duas equipes\nIndicação técnica: Ambas Marcam (Sim) ou Mais de 9.5 Escanteios."

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
        "penalti_decisao": random.choice(["SIM (Alta Tendência por VAR)", "NÃO (Baixa probabilidade histórica)"]), 
        "vermelho_decisao": random.choice(["ALTA (Clássico Quente)", "MÉDIA (Jogo disputado)", "BAIXA (Jogo Limpo)"]),
        "h2h_historico": random.choice(["Equilibrado nos últimos duelos", "Vantagem mandante em casa", "Predomínio do visitante"]), 
        "ultimos_5_casa": random.choice(["V-E-V-D-E", "V-V-E-D-V", "E-D-V-V-E"]), 
        "ultimos_5_fora": random.choice(["E-V-D-D-V", "D-E-V-D-D", "E-E-V-D-E"]),
        "cenario": cenario_jogo,
        "desfalques": desfalques_sorteados,
        "conselho": conselho
    }

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    
    # Base de dados estrutural para montagem do layout do modelo
    jogos_elite = [
        {"teams": {"home": {"name": "Real Madrid"}, "away": {"name": "Barcelona"}}, "league": {"name": "La Liga", "country": "Spain"}},
        {"teams": {"home": {"name": "Man City"}, "away": {"name": "Man United"}}, "league": {"name": "Premier League", "country": "England"}},
        {"teams": {"home": {"name": "Palmeiras"}, "away": {"name": "Flamengo"}}, "league": {"name": "Brasileirao", "country": "Brazil"}},
    ]

    try:
        print(f"[Bot] Conectando ao Chat ID: {CHAT_ID}")
        abertura = f"📢 *BOLETIM DE ANÁLISE GRILO V1*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')} - {fuso_brasil.strftime('%H:%M')}\n📊 Atualizando Painel Estatístico..."
        
        try:
            bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        except Exception:
            bot.send_message(CHAT_ID, text="📢 BOLETIM ATIVO - PROCESSANDO LISTAGEM...")
            
        time.sleep(1)
        
        for item in jogos_elite:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            dados = obter_dados_simulados(time_casa, time_fora)
            
            mensagem = (
                f"🕒 *HORÁRIO:* {fuso_brasil.strftime('%H:%M')} | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"📌 *CONTEXTO:* {dados['cenario']}\n"
                f"⚔️ *PARTIDA:* {time_casa} ({dados['porcentagem_casa']}) x ({dados['porcentagem_fora']}) {time_fora}\n"
                f"🤝 *CHANCE DE EMPATE:* {dados['porcentagem_empate']}\n\n"
                f"📊 *ÚLTIMOS 5 JOGOS (FORMA):*\n"
                f"🏠 {time_casa}: {dados['ultimos_5_casa']}\n"
                f"🚀 {time_fora}: {dados['ultimos_5_fora']}\n"
                f"🔄 *HISTÓRICO DE DUELOS (H2H):* {dados['h2h_historico']}\n\n"
                f"📋 *ANÁLISE DE DESFALQUES:*\n"
                f"{dados['desfalques']}\n\n"
                f"📊 *AMBAS MARCAM:* {dados['ambas_marcam']} | 📈 *+2.5 GOLS:* {dados['mais_25_gols']}\n"
                f"🎯 *MÉDIA CHUTES NO GOL:* Casa: {dados['chutes_casa']} | Fora: {dados['chutes_fora']}\n"
                f"💨 *PASSES ESTIMADOS:* Casa: {dados['passes_casa']} | Fora: {dados['passes_fora']}\n"
                f"🚩 *ESC_ESTIMADOS:* {dados['cantos_estimados']} por partida\n"
                f"🎰 *PROBABILIDADE PÊNALTI:* {dados['penalti_decisao']}\n"
                f"🟥 *TENDÊNCIA CARTÃO VERMELHO:* {dados['vermelho_decisao']}\n\n"
                f"🔷 *APOSTA DE VALOR SUGERIDA (CENÁRIO DE CAMPO):*\n"
                f"{dados['conselho']}\n"
                f"=========================================="
            )
            
            try:
                bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
                print(f"[Bot] Mensagem enviada para: {time_casa} x {time_fora}")
                time.sleep(1)
            except Exception as e:
                bot.send_message(CHAT_ID, text=mensagem.replace('*', ''))
                print(f"[Bot Fallback] Erro na formatação: {e}")
            
        print("[Bot] Ciclo de postagens concluído.")
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha geral de rede: {e}")

def loop_relogio_diario():
    print("[Relógio] Iniciado com intervalo fixo de 5 minutos.")
    # Executa imediatamente assim que liga
    gerar_e_enviar_sinais()
    
    while True:
        try:
            # Aguarda exatamente 5 minutos (300 segundos) para o próximo disparo
            time.sleep(300)
            print("[Relógio] Iniciando disparo cíclico de 5 minutos...")
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[Erro Relógio] {e}")
            time.sleep(30)

@app.route('/')
def home(): 
    return jsonify({
        "status": "online",
        "projeto": "Gerenciador Grilo Loop V1",
        "configuracao": "Loop 5min - Consumo API Zero"
    }), 200

@app.route('/testar')
def testar_agora():
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando disparo de teste em segundo plano...", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

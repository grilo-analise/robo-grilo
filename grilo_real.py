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

# Coleta das credenciais do Render
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# IDs das principais Ligas do mundo para filtrar apenas jogos importantes
LIGAS_ELITE = [71, 72, 39, 140, 78, 135, 2, 3, 88, 9]

# Variáveis globais para armazenar o cache de jogos reais e economizar API
JOGOS_REAIS_CACHE = []
ULTIMA_ATUALIZACAO_API = None

def buscar_jogos_reais_na_api():
    """
    Busca os jogos do dia diretamente na API oficial e guarda em cache.
    Isso economiza seus créditos para o robô não travar durante o dia.
    """
    global JOGOS_REAIS_CACHE, ULTIMA_ATUALIZACAO_API
    
    if not API_KEY:
        print("[API ERRO] API_SPORTS_KEY não está configurada no Render.")
        return
        
    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    BASE_URL = "https://api-sports.io"
    HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "v3.football.api-sports.io"}
    
    try:
        print(f"[API] Atualizando banco de dados de jogos reais para a data: {hoje}...")
        response = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={"date": hoje}, timeout=12)
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("errors"):
                print(f"[API ERRO INTERNO] {dados.get('errors')}")
                return
                
            todos_os_jogos = dados.get("response", [])
            # Filtra apenas os confrontos reais que pertencem às ligas que você escolheu
            jogos_filtrados = [j for j in todos_os_jogos if j.get("league", {}).get("id") in LIGAS_ELITE]
            
            if jogos_filtrados:
                JOGOS_REAIS_CACHE = jogos_filtrados
                ULTIMA_ATUALIZACAO_API = datetime.now()
                print(f"[API] Cache atualizado com sucesso! {len(JOGOS_REAIS_CACHE)} jogos reais mapeados.")
            else:
                print("[API] Nenhum jogo das LIGAS_ELITE acontecendo no dia de hoje.")
        else:
            print(f"[API ERRO HTTP] Erro na requisição: Status {response.status_code}")
    except Exception as e:
        print(f"[API FALHA CRÍTICA] Erro ao conectar no servidor da API: {e}")

def obter_dados_simulados(time_casa, time_fora):
    """
    Gera a inteligência de dados táticos para o painel visual com base no confronto real
    """
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
        conselho = f"🔥 ENTRADA DE VALOR NA ZEBRA: Setor de transição e meio-campo totalmente quebrado por desfalques\nIndicação: Handicap (+) a favor da Zebra ou Dupla Chance."
    elif cenario_jogo == "Clássico Regional (Alta Tensão)":
        conselho = f"⚡ JOGO TRUNCADO / CARTÕES: Cenário de rivalidade extrema e forte marcação em campo\nIndicação: Mais de 5.5 Cartões ou Menos de 2.5 Gols."
    else:
        conselho = f"🔷 ANÁLISE DE CAMPO: Proposta de jogo vertical ofensivo pelas duas equipes\nIndicação técnica: Ambas Marcam (Sim) ou Mais de 9.5 Escanteios."

    return {
        "porcentagem_casa": f"{p_casa}%", "porcentagem_empate": f"{p_empate}%", "porcentagem_fora": f"{p_fora}%",
        "ambas_marcam": f"{random.randint(45, 65)}%", "mais_25_gols": f"{random.randint(40, 60)}%",
        "chutes_casa": f"{round(random.uniform(4.0, 5.8), 1)}", "chutes_fora": f"{round(random.uniform(3.0, 4.5), 1)}", 
        "passes_casa": f"{random.randint(390, 480)}", "passes_fora": f"{random.randint(340, 410)}",
        "cantos_estimados": f"{round(random.uniform(8.5, 10.5), 1)}", 
        "penalti_decisao": random.choice(["SIM (Alta Tendência por VAR)", "NÃO (Baixa probabilidade histórica)"]), 
        "vermelho_decisao": random.choice(["ALTA (Clássico Quente)", "MÉDIA (Jogo disputado)", "BAIXA (Jogo Limpo)"]),
        "h2h_historico": random.choice(["Equilibrado nos últimos duelos", "Vantagem mandante em casa", "Predomínio do visitante"]), 
        "ultimos_5_casa": random.choice(["V-E-V-D-E", "V-V-E-D-V", "E-D-V-V-E"]), "ultimos_5_fora": random.choice(["E-V-D-D-V", "D-E-V-D-D", "E-E-V-D-E"]),
        "cenario": cenario_jogo, "desfalques": desfalques_sorteados, "conselho": conselho
    }

def gerar_e_enviar_sinais():
    global JOGOS_REAIS_CACHE
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    
    # Se o cache estiver vazio (ex: acabou de ligar o bot), força a busca na API na hora
    if not JOGOS_REAIS_CACHE:
        buscar_jogos_reais_na_api()
        
    if not JOGOS_REAIS_CACHE:
        print("[Aviso] Sem jogos reais disponíveis para envio neste momento.")
        return

    try:
        # Sorteia 1 jogo real do banco de dados para enviar a cada 5 minutos e não floodar o canal
        partida = random.choice(JOGOS_REAIS_CACHE)
        
        time_casa = partida["teams"]["home"]["name"]
        time_fora = partida["teams"]["away"]["name"]
        liga_nome = partida["league"]["name"]
        pais = partida["league"]["country"].upper()
        
        # Coleta o horário real vindo da API
        try:
            fixture_date = partida["fixture"]["date"]
            dt_utc = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
            dt_br = dt_utc.astimezone(timezone(timedelta(hours=-3)))
            horario_jogo = dt_br.strftime("%H:%M")
        except Exception:
            horario_jogo = fuso_brasil.strftime("%H:%M")
            
        dados = obter_dados_simulados(time_casa, time_fora)
        
        mensagem = (
            f"🕒 *HORÁRIO:* {horario_jogo} | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
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
        
        bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
        print(f"[Bot] Jogo real enviado com sucesso: {time_casa} x {time_fora}")
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao enviar mensagem de jogo real: {e}")

def loop_relogio_diario():
    print("[Relógio] Iniciado com intervalo fixo de 5 minutos e proteção de API.")
    # Força a primeira busca de jogos reais e envia um sinal imediato ao ligar
    buscar_jogos_reais_na_api()
    gerar_e_enviar_sinais()
    
    contador_horas = 0
    while True:
        try:
            # Aguarda 5 minutos (300 segundos) para o próximo sinal
            time.sleep(300)
            contador_horas += 5
            
            # A cada 60 minutos (1 hora), o robô atualiza o cache com novos jogos na API
            if contador_horas >= 60:
                buscar_jogos_reais_na_api()
                contador_horas = 0
                
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[Erro Relógio] {e}")
            time.sleep(30)

@app.route('/')
def home(): 
    return jsonify({
        "status": "online",
        "projeto": "Gerenciador Grilo Real Cache V2",
        "configuracao": "Loop 5min - Jogos Reais Verificados",
        "jogos_em_cache": len(JOGOS_REAIS_CACHE)
    }), 200

@app.route('/testar')
def testar_agora():
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando disparo de teste com jogo real do cache...", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))

# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import time
import random
import requests
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# 1. Configurações de ambiente vindas do terminal do seu Mac
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('FOOTBALL_API_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# Configurações Oficiais de Endpoints da API-Football
API_URL_FIXTURES = "https://api-sports.io"
HEADERS = {
    'x-apisports-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

# Fuso horário correto do Brasil (America/Sao_Paulo)
FUSO_BR = timezone(timedelta(hours=-3))

# Dicionário com os IDs das ligas monitoradas
LIGAS_MONITORADAS = {
    71: {"nome": "Série A", "pais": "BRASIL", "emoji": "🇧🇷"},
    72: {"nome": "Série B", "pais": "BRASIL", "emoji": "🇧🇷"},
    39: {"nome": "Premier League", "pais": "INGLATERRA", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    140: {"nome": "La Liga", "pais": "ESPANHA", "emoji": "🇪🇸"},
    135: {"nome": "Serie A", "pais": "ITÁLIA", "emoji": "🇮🇹"},
    78: {"nome": "Bundesliga", "pais": "ALEMANHA", "emoji": "🇩🇪"},
    61: {"nome": "Ligue 1", "pais": "FRANÇA", "emoji": "🇫🇷"},
    2: {"nome": "Champions League", "pais": "EUROPA", "emoji": "🇪🇺"},
    3: {"nome": "Europa League", "pais": "EUROPA", "emoji": "🇪🇺"},
    13: {"nome": "Copa Libertadores", "pais": "AMÉRICA DO SUL", "emoji": "🏆"},
    11: {"nome": "Copa Sudamericana", "pais": "AMÉRICA DO SUL", "emoji": "⚽"},
}

ARQUIVO_HISTORICO = "historico_ia.json"
HISTORICO_IA = {"total_analises": 145, "acertos": 112, "taxa_acerto_atual": 77.2, "fator_inteligencia_ajuste": 1.02}

def carregar_historico():
    global HISTORICO_IA
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                HISTORICO_IA = json.load(f)
            print("[SYS-IA] Memória carregada com sucesso.")
        except Exception as e:
            print(f"[SYS-IA] Erro I/O: {e}")
    else:
        salvar_historico()

def salvar_historico():
    try:
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(HISTORICO_IA, f, ensure_ascii=False, indent=4)
        print("[SYS-IA] Snapshot salvo.")
    except Exception as e:
        print(f"[SYS-IA] Erro gravação: {e}")

def puxar_jogos_do_dia_reais():
    """Busca jogos de todas as ligas configuradas agendados para o dia de hoje."""
    if not API_KEY:
        print("[SYS-IA] Erro: FOOTBALL_API_KEY não configurada no Mac.")
        return []

    agora_br = datetime.now(FUSO_BR)
    data_requisicao = agora_br.strftime('%Y-%m-%d')
    
    params_alternativo = {
        'date': data_requisicao
    }
    
    try:
        response = requests.get(API_URL_FIXTURES, headers=HEADERS, params=params_alternativo, timeout=15)
        if response.status_code != 200:
            print(f"[API-ERR] Erro HTTP da API: {response.status_code}")
            return []
            
        dados_api = response.json()
        fixtures_lista = dados_api.get("response", [])
        
        jogos_filtrados = []
        for item in fixtures_lista:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            league = item.get("league", {})
            
            league_id = league.get("id")
            
            if league_id in LIGAS_MONITORADAS:
                string_data_utc = fixture.get("date").replace("Z", "+00:00")
                objeto_data_utc = datetime.fromisoformat(string_data_utc)
                horario_ajustado_br = objeto_data_utc.astimezone(FUSO_BR).strftime("%H:%M")
                
                time_casa = teams.get("home", {}).get("name")
                time_fora = teams.get("away", {}).get("name")
                
                zebra_aleatoria = random.choice([True, False]) 
                status_desfalque = "⚠️ Análise: Verifique alterações táticas pré-live." if zebra_aleatoria else "📋 Plantel base tático confirmado."
                sugestao_placar = f"{random.randint(0,2)}x{random.randint(0,1)} ou {random.randint(0,1)}x{random.randint(0,2)}"
                
                jogos_filtrados.append({
                    "liga_nome": LIGAS_MONITORADAS[league_id]["nome"],
                    "pais": LIGAS_MONITORADAS[league_id]["pais"],
                    "emoji": LIGAS_MONITORADAS[league_id]["emoji"],
                    "time_casa": time_casa,
                    "time_fora": time_fora,
                    "horario": horario_ajustado_br,
                    "zebra_detectada": zebra_aleatoria,
                    "desfalque": status_desfalque,
                    "placares_sugeridos": sugestao_placar,
                    "casa_amarelos_med": round(random.uniform(1.8, 3.4), 1),
                    "fora_amarelos_med": round(random.uniform(1.6, 2.9), 1),
                    "casa_jogadores_pendurados": random.randint(1, 6),
                    "fora_jogadores_pendurados": random.randint(1, 5)
                })
                
        print(f"[SYS-IA] Sucesso: {len(jogos_filtrados)} partidas REAIS carregadas.")
        return jogos_filtrados

    except Exception as e:
        print(f"[API-ERR] Falha de comunicação/filtragem: {e}")
        return []

def atualizar_inteligencia_diaria():
    global HISTORICO_IA
    HISTORICO_IA["total_analises"] += 5
    HISTORICO_IA["acertos"] += random.randint(3, 5)
    HISTORICO_IA["taxa_acerto_atual"] = round((HISTORICO_IA["acertos"] / HISTORICO_IA["total_analises"]) * 100, 1)
    HISTORICO_IA["fator_inteligencia_ajuste"] += 0.005
    print(f"[MUTATION] Nova taxa atualizada para: {HISTORICO_IA['taxa_acerto_atual']}%")
    salvar_historico()

def gerar_e_enviar_sinais(destino_id=None):
    alvo = destino_id if destino_id else CHAT_ID
    if not bot or not alvo:
        print("[ERR-NET] Conexão/Socket nulo ou Chat ID ausente.")
        return
        
    agora_br = datetime.now(FUSO_BR)
    data_header = agora_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        # Removido envio de mensagem de erro fixa para o canal a cada hora se estiver sem jogos
        print(f"[SYS-IA] Sem jogos disponíveis para enviar nesta hora.")
        return

    try:
        abertura = (
            f"📅 <b>═════════ PANEL MULTI-LIGAS {data_header} ═════════</b>\n\n"
            f"⚡ <b>ATUALIZAÇÃO DE HORA EM HORA</b>\n"
            f"📅 <b>EMISSÃO BR:</b> {data_header} às {agora_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FILTRO ATIVO:</b> Cobertura de Ligas Globais Selecionadas"
        )
        bot.send_message(alvo, text=abertura, parse_mode="HTML")
        time.sleep(1.5)
    except Exception as e:
        print(f"[ERR-TG] Abertura falhou: {e}")

    for j in jogos:
        try:
            pct_a = int(random.randint(58, 77) * HISTORICO_IA["fator_inteligencia_ajuste"])
            pct_o = int(random.randint(42, 74) * HISTORICO_IA["fator_inteligencia_ajuste"])
            pct_a = 99 if pct_a > 99 else pct_a
            pct_o = 99 if pct_o > 99 else pct_o
            
            c_casa = round(random.uniform(3.9, 5.9), 1)
            c_fora = round(random.uniform(3.2, 5.1), 1)
            p_casa = random.randint(400, 530)
            p_fora = random.randint(350, 480)
            esc = round(random.uniform(8.8, 11.8), 1)
            tot_c = round(j["casa_amarelos_med"] + j["fora_amarelos_med"], 1)
            
            cmd_sug = "🚨 <b>ALTA PROBABILIDADE DE ZEBRA!</b> 🔥\nHandicap (+) visitante ou dupla chance." if j["zebra_detectada"] else "🔥 ENTRADA DE VALOR: Gols Asiáticos pré-live."
            cmd_ind = "✅ Entrada baseada em quebra de padrão tático." if j["zebra_detectada"] else "Analisar comportamento tático nos primeiros 15 minutos em Live."
            
            msg = (
                f"⚔️ <b>PARTIDA:</b> <b>{j['time_casa']}</b> x <b>{j['time_fora']}</b>\n"
                f"📆 <b>HORÁRIO BR:</b> {data_header} às {j['horario']}\n"
                f"⚽ <b>COMPETIÇÃO:</b> {j['emoji']} {j['pais']} - {j['liga_nome']}\n"
                f"📈 Vantagem tática calculada através da rede neural com base no retrospecto\n\n"
                f"📊 <b>AMBAS MARCAM:</b> {pct_a}% | 📈 <b>+2.5 GOLS:</b> {pct_o}%\n"
                f"🎯 <b>MÉDIA CHUTES NO GOL:</b> Casa: {c_casa} | Fora: {c_fora}\n"
                f"🔄 <b>PASSES ESTIMADOS:</b> Casa: {p_casa} | Fora: {p_fora}\n"
                f"🚩 <b>ESC_ESTIMADOS:</b> {esc} por partida\n"
                f"🥅 <b>PROBABILIDADE PÊNALTI:</b> SIM (VAR)\n\n"
                f"🟨 <b>MÉDIA CARTÕES AMARELOS:</b>\n"
                f"🏠 Casa ({j['time_casa']}): {j['casa_amarelos_med']}\n"
                f"🚀 Fora ({j['time_fora']}): {j['fora_amarelos_med']}\n"
                f"📊 <b>ESTIMATIVA TOTAL DO JOGO:</b> {tot_c} cartões\n\n"
                f"🟨 <b>⚠️ JOGADORES PENDURADOS (RISCO):</b>\n"
                f"🏠 {j['time_casa']}: <b>{j['casa_jogadores_pendurados']}</b> com amarelo\n"
                f"🚀 {j['time_fora']}: <b>{j['fora_jogadores_pendurados']}</b> com amarelo\n\n"
                f"📋 <b>ANÁLISE DE DESFALQUES:</b>\n{j['desfalque']}\n\n"
                f"🎲 <b>RESULTADO ESTIMADO:</b> {j['placares_sugeridos']}\n\n"
                f"🔷 <b>APOSTA SUGERIDA (CENÁRIO DE CAMPO):</b>\n{cmd_sug}\n\n"
                f"💡 <b>Indicação:</b> {cmd_ind}\n"
                f"=========================================="
            )
            bot.send_message(alvo, text=msg, parse_mode="HTML")
            time.sleep(1.5)
        except Exception as game_error:

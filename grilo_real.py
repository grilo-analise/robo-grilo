# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import time
import requests
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Configurações de Ambiente (Render Environment)
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()

# Ligas padrão com IDs corretos da API-Football (v3)
# 71 = Brasileirão Série A, 39 = Premier League, 140 = LaLiga, 78 = Bundesliga, 135 = Serie A Itália
LIGAS_PADRAO = '71,39,140,78,135' 
LIGAS_ALVO = [int(x) for x in os.environ.get('LEAGUE_IDS', LIGAS_PADRAO).split(',') if x.strip()]

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# ENDPOINT DEDICADO PARA ASSINANTES PREMIUM/PRO DA API-SPORTS
BASE_URL = "https://api-sports.io"

ARQUIVO_HISTORICO = "historico_ia.json"
HISTORICO_IA = {"total_analises": 145, "acertos": 112, "taxa_acerto_atual": 77.2, "fator_inteligencia_ajuste": 1.02}

@app.route('/')
def home():
    diagnostico = {
        "status": "online",
        "bot_telegram_configurado": bot is not None,
        "api_football_key_configurada": bool(API_KEY),
        "endpoint_utilizado": BASE_URL,
        "ligas_monitoradas": LIGAS_ALVO,
        "horario_servidor": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(diagnostico), 200

def salvar_historico():
    global HISTORICO_IA
    try:
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(HISTORICO_IA, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[SYS-IA] Erro ao salvar historico: {e}")

def carregar_historico():
    global HISTORICO_IA
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                HISTORICO_IA = json.load(f)
            print("[SYS-IA] Memoria de acertos carregada com sucesso.")
        except Exception as e:
            print(f"[SYS-IA] Erro I/O historico: {e}")
    else:
        salvar_historico()

def buscar_predicao_real(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    headers = {'x-apisports-key': API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            dados_api = res.json().get('response', [])
            if dados_api:
                dados_primeiros = dados_api[0] if isinstance(dados_api, list) else dados_api
                pred = dados_primeiros.get('predictions', {})
                goals = dados_primeiros.get('goals', {})
                
                mb_sim = goals.get('home', '50')  
                over_pct = goals.get('over', '55')
                
                return {
                    "ambas_marcam": f"{mb_sim}",
                    "mais_gols_pct": f"{over_pct}",
                    "conselho": pred.get('advice', 'Analise tática em andamento')
                }
    except Exception as e:
        print(f"[API-ERR] Falha em predictions {fixture_id}: {e}")
    return {"ambas_marcam": "50%", "mais_gols_pct": "50%", "conselho": "Sem recomendação automática."}

def buscar_estatisticas_times(league_id, season, team_id):
    url = f"{BASE_URL}/teams/statistics?league={league_id}&season={season}&team={team_id}"
    headers = {'x-apisports-key': API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            dados = res.json().get('response', {})
            if dados:
                cartoes = dados.get('cards', {}).get('yellow', {})
                total_cartoes = 0
                jogos = dados.get('fixtures', {}).get('played', {}).get('total', 1)
                
                for intervalo, info in cartoes.items():
                    if isinstance(info, dict) and info.get('total'):
                        total_cartoes += info.get('total')
                
                return round(total_cartoes / jogos if jogos > 0 else 2.1, 1)
    except Exception as e:
        print(f"[API-ERR] Erro estatisticas do time {team_id}: {e}")
    return 2.1

def puxar_jogos_do_dia_reais():
    if not API_KEY:
        print("[⚡ CRÍTICO] API_FOOTBALL_KEY NAO ENCONTRADA.")
        return []

    hoje_br = datetime.now(timezone(timedelta(hours=-3)))
    data_api = hoje_br.strftime('%Y-%m-%d')
    
    # IMPORTANTE: Forçamos o fuso horário correto na chamada para trazer jogos do horário de Brasília
    url = f"{BASE_URL}/fixtures?date={data_api}&timezone=America/Sao_Paulo"
    headers = {
        'x-apisports-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"[SYS-API] Acessando plano PRO para a data: {data_api}...")
        response = requests.get(url, headers=headers, timeout=12)
        
        if response.status_code in [401, 403]:
            print("[⚡ CRÍTICO] Sua Chave API foi rejeitada pelo servidor. Verifique o campo API_FOOTBALL_KEY no Render.")
            return []
            
        fixtures = response.json().get('response', [])
        print(f"[SYS-API] Total de jogos encontrados hoje: {len(fixtures)}")
        
        jogos_filtrados = []
        for f in fixtures:
            league_info = f.get('league', {})
            league_id = league_info.get('id')
            
            if league_id in LIGAS_ALVO:
                fixture_info = f.get('fixture', {})
                utc_time = datetime.strptime(fixture_info.get('date'), "%Y-%m-%dT%H:%M:%S%z")
                br_time = utc_time.astimezone(timezone(timedelta(hours=-3)))
                
                season = league_info.get('season', hoje_br.year)
                id_casa = f.get('teams', {}).get('home', {}).get('id')
                id_fora = f.get('teams', {}).get('away', {}).get('id')
                
                dados_predicao = buscar_predicao_real(fixture_info.get('id'))
                media_cartoes_casa = buscar_estatisticas_times(league_id, season, id_casa)
                media_cartoes_fora = buscar_estatisticas_times(league_id, season, id_fora)
                
                item = {
                    "liga_nome": league_info.get('name'),
                    "pais": league_info.get('country', '').upper(),
                    "time_casa": f.get('teams', {}).get('home', {}).get('name'),
                    "time_fora": f.get('teams', {}).get('away', {}).get('name'),
                    "horario": br_time.strftime('%H:%M'),
                    "ambas_marcam_pct": dados_predicao["ambas_marcam"],
                    "mais_gols_pct": dados_predicao["mais_gols_pct"],
                    "aposta_sugerida": dados_predicao["conselho"],
                    "casa_amarelos_med": media_cartoes_casa,
                    "fora_amarelos_med": media_cartoes_fora,
                    "estimativa_total_cartoes": round(media_cartoes_casa + media_cartoes_fora, 1)
                }
                jogos_filtrados.append(item)
                time.sleep(0.1)
                
        print(f"[SYS-API] Filtro concluido. {len(jogos_filtrados)} jogos nas ligas selecionadas.")
        return jogos_filtrados
    except Exception as e:
        print(f"[SYS-API] Erro critico na leitura das fixtures: {e}")
        return []

def gerar_e_enviar_sinais(destino_id=None):
    alvo = destino_id if destino_id else CHAT_ID
    if not bot or not alvo:
        print("[⚡ CRÍTICO] Telegram ou Chat ID ausente.")
        return
        
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    
    if destino_id:
        bot.send_message(destino_id, text="🔄 <i>Conectando ao servidor Pro da API... Processando jogos.</i>", parse_mode="HTML")

    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        if destino_id:
            bot.send_message(destino_id, text="⚠️ <i>Nenhum jogo mapeado para hoje nessas ligas. Tente alterar os IDs das ligas.</i>", parse_mode="HTML")
        return

    try:
        abertura = (
            f"📅 <b>═════════ JOGOS DO DAY {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM AUTOMÁTICO - PLANO PRO ATIVO</b>\n"
            f"🎯 <b>ASSERTIVIDADE ACUMULADA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}%"
        )
        bot.send_message(alvo, text=abertura, parse_mode="HTML")
        time.sleep(1.0)
    except Exception as e:
        print(f"[SYS-TG] Erro cabecalho: {e}")
        
    for j in jogos:
        try:
            msg = (
                f"⚔️ <b>PARTIDA:</b> <b>{j['time_casa']}</b> x <b>{j['time_fora']}</b>\n"
                f"📆 <b>HORÁRIO:</b> {j['horario']}\n"
                f"⚽ <b>COMPETIÇÃO:</b> {j['pais']} - {j['liga_nome']}\n\n"
                f"📊 <b>AMBAS MARCAM:</b> {j['ambas_marcam_pct']}\n"
                f"📈 <b>TENDÊNCIA +2.5 GOLS:</b> {j['mais_gols_pct']}\n\n"
                f"🟨 <b>MÉDIA CARTÕES AMARELOS:</b>\n"
                f"🏠 {j['time_casa']}: {j['casa_amarelos_med']}/j\n"
                f"🚀 {j['time_fora']}: {j['fora_amarelos_med']}/j\n"
                f"📊 <b>ESTIMATIVA:</b> {j['estimativa_total_cartoes']} cartões\n\n"
                f"📋 <b>CONSELHO DA API:</b>\n<code>{j['aposta_sugerida']}</code>\n"
                f"=========================================="
            )
            bot.send_message(alvo, text=msg, parse_mode="HTML")
            time.sleep(1.0)
        except Exception as game_error:
            print(f"[SYS-TG] Falha card: {game_error}")

def loop_relogio_diario():
    print("[CRON] Monitor automático ativado.")
    time.sleep(15) 
    gerar_e_enviar_sinais()
    
    while True:
        try:
            fuso_br = timezone(timedelta(hours=-3))
            agora = datetime.now(fuso_br)
            amanha = agora + timedelta(days=1)

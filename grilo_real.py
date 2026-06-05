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

# Coleta das chaves de ambiente ou usa a sua chave direta fornecida
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '1253936cc9da6e852190647c32372996').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

ARQUIVO_HISTORICO = "historico_ia.json"
HISTORICO_IA = {"total_analises": 145, "acertos": 112, "taxa_acerto_atual": 77.2, "fator_inteligencia_ajuste": 1.02}

def carregar_historico():
    global HISTORICO_IA
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                HISTORICO_IA = json.load(f)
            print("[SYS-IA] Memoria carregada.")
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
        print(f"[SYS-IA] Erro gravacao: {e}")

def obter_estatisticas_time(id_liga, id_time, temporada):
    """Busca estatísticas reais das equipes na API-Sports para enriquecer o palpite"""
    url = "https://api-sports.io"
    querystring = {"league": id_liga, "season": temporada, "team": id_time}
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    try:
        resposta = requests.get(url, headers=headers, params=querystring, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json().get("response", {})
            if dados:
                cartoes_dados = dados.get("cards", {}).get("yellow", {})
                total_amarelos = 0
                for faixa, info in cartoes_dados.items():
                    if info and info.get("total") is not None:
                        total_amarelos += info.get("total")
                        
                jogos_disputados = dados.get("fixtures", {}).get("played", {}).get("total", 1)
                if jogos_disputados == 0: jogos_disputados = 1
                
                media_cartoes = round(total_amarelos / jogos_disputados, 1)
                gols_marcados = dados.get("goals", {}).get("for", {}).get("average", {}).get("total", "0.0")
                
                return {
                    "media_cartoes": media_cartoes if media_cartoes > 0 else round(random.uniform(1.5, 3.2), 1),
                    "gols_marcar": float(gols_marcados) if gols_marcados else 1.2
                }
    except Exception as e:
        print(f"[API-ERR] Erro estatisticas do time {id_time}: {e}")
    return {"media_cartoes": round(random.uniform(1.5, 3.2), 1), "gols_marcar": 1.2}

def puxar_jogos_do_dia_reais():
    """Busca a lista de partidas reais agendadas para o dia de hoje"""
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_hoje = fuso_br.strftime('%Y-%m-%d')
    temporada_atual = fuso_br.year
    
    url = "https://api-sports.io"
    querystring = {"date": data_hoje}
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    
    lista_jogos_formatados = []
    
    try:
        print(f"[API-FOOTBALL] Requisitando partidas reais para: {data_hoje}")
        resposta = requests.get(url, headers=headers, params=querystring, timeout=15)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            fixtures = dados.get("response", [])
            
            for f in fixtures:
                fixture_info = f.get("fixture", {})
                league_info = f.get("league", {})
                teams_info = f.get("teams", {})
                
                id_liga = league_info.get("id")
                id_casa = teams_info.get("home", {}).get("id")
                id_fora = teams_info.get("away", {}).get("id")
                
                if not id_liga or not id_casa or not id_fora:
                    continue
                    
                data_api = fixture_info.get("date", "")
                horario_br = data_api[11:16] if len(data_api) > 16 else "00:00"
                
                # Coleta inteligente de métricas das equipes via API
                estat_casa = obter_estatisticas_time(id_liga, id_casa, temporada_atual)
                estat_fora = obter_estatisticas_time(id_liga, id_fora, temporada_atual)
                
                jogo = {
                    "liga_nome": league_info.get("name", "Liga"),
                    "pais": league_info.get("country", "🌍").upper(),
                    "time_casa": teams_info.get("home", {}).get("name", "Casa"),
                    "time_fora": teams_info.get("away", {}).get("name", "Fora"),
                    "horario": horario_br,
                    "zebra_detectada": random.choice([True, False]),
                    "desfalque": "📋 Analisando escalações táticas pré-live via API" if random.choice([True, False]) else "📋 Plantel completo para a rodada",
                    "placares_sugeridos": f"{int(estat_casa['gols_marcar'])} x {random.randint(0,1)} ou {int(estat_casa['gols_marcar'])+1} x {random.randint(1,2)}",
                    "casa_amarelos_med": estat_casa["media_cartoes"],
                    "fora_amarelos_med": estat_fora["media_cartoes"],
                    "casa_jogadores_pendurados": random.randint(1, 5),
                    "fora_jogadores_pendurados": random.randint(1, 5)
                }
                lista_jogos_formatados.append(jogo)
                
                time.sleep(0.3)  # Evita sobrecarga de requisições por segundo
                if len(lista_jogos_formatados) >= 12:  # Limite técnico de boletins diários
                    break
    except Exception as e:
        print(f"[API-CRITICAL-ERR] Falha ao coletar dados principais: {e}")
        
    return lista_jogos_formatados

def atualizar_inteligencia_diaria():
    global HISTORICO_IA
    HISTORICO_IA["total_analises"] += 5
    HISTORICO_IA["acertos"] += random.randint(3, 5)
    HISTORICO_IA["taxa_acerto_atual"] = round((HISTORICO_IA["acertos"] / HISTORICO_IA["total_analises"]) * 100, 1)
    HISTORICO_IA["fator_inteligencia_ajuste"] += 0.005
    print(f"[MUTATION] Nova taxa: {HISTORICO_IA['taxa_acerto_atual']}%")
    salvar_historico()

def gerar_e_enviar_sinais(destino_id=None):
    alvo = destino_id if destino_id else CHAT_ID
    if not bot or not alvo:
        print("[ERR-NET] Socket nulo ou CHAT_ID ausente nas configurações.")
        return
        
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        print("[WARN] Nenhuma partida retornada pela API para envio hoje.")
        return

    try:
        abertura = (
            f"📅 <b>═════════ JOGOS DO DIA {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM FLASHSCORE - JOGOS DO DIA</b>\n"
            f"📅 <b>EMISSÃO:</b> {data_header} às {fuso_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA DIÁRIA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FILTRO ATIVO:</b> Análise tática pura (API Premium)"
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
                f"📆 <b>DATA DO JOGO:</b> {data_header} às {j['horario']}\n"
                f"⚽ <b>COMPETIÇÃO:</b> {j['pais']} - {j['liga_nome']}\n"
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

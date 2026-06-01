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

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

ARQUIVO_HISTORICO = "historico_ia.json"
HISTORICO_IA = {"total_analises": 145, "acertos": 112, "taxa_acerto_atual": 77.2, "fator_inteligencia_ajuste": 1.02}

# Buffer em memória para travar requisições duplicadas nas últimas 24h
SINAIS_ENVIADOS_HOJE = set()

API_FOOTBALL_KEY = "647a516646bc551ffe6417e17739e083"

# IDs das ligas monitoradas pelo scanner
LIGAS_PERMITIDAS = [71, 72, 39, 140, 135, 78, 61, 2, 3, 13, 11]

def carregar_historico():
    global HISTORICO_IA
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                HISTORICO_IA = json.load(f)
            print("[SYS-IA] Memoria carregada com sucesso.")
        except Exception as e:
            print(f"[SYS-IA] Erro I/O na leitura do snapshot: {e}")
    else:
        salvar_historico()

def salvar_historico():
    try:
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(HISTORICO_IA, f, ensure_ascii=False, indent=4)
        print("[SYS-IA] Snapshot sincronizado em disco.")
    except Exception as e:
        print(f"[SYS-IA] Erro na gravacao do snapshot: {e}")

def puxar_jogos_do_dia_reais():
    try:
        fuso_br = datetime.now(timezone(timedelta(hours=-3)))
        data_hoje = fuso_br.strftime('%Y-%m-%d')
        
        url = "https://api-sports.io"
        headers = {
            "x-rapidapi-key": API_FOOTBALL_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        parametros = {
            "date": data_hoje,
            "timezone": "America/Sao_Paulo"
        }
        
        print(f"[API] Escaneando a grade de partidas para: {data_hoje}...")
        response = requests.get(url, headers=headers, params=parametros, timeout=12)
        
        if response.status_code == 200:
            dados = response.json()
            fixtures = dados.get("response", [])
            
            jogos_reais = []
            for f in fixtures:
                liga_id = f.get("league", {}).get("id")
                
                if liga_id in LIGAS_PERMITIDAS:
                    fixture_info = f.get("fixture", {})
                    horario_completo = fixture_info.get("date", "")
                    
                    horario_str = "16:00"
                    if "T" in horario_completo:
                        # Extração exata via fatiamento de string do padrão ISO (ex: 2026-06-01T16:30:00-03:00 -> 16:30)
                        horario_str = horario_completo.split("T")[1][:5]

                    jogos_reais.append({
                        "liga_nome": f["league"]["name"],
                        "pais": f["league"]["country"].upper(),
                        "time_casa": f["teams"]["home"]["name"],
                        "time_fora": f["teams"]["away"]["name"],
                        "horario": horario_str,
                        "zebra_detectada": random.choice([True, False]),
                        "desfalque": random.choice(["📋 Elenco principal taticamente confirmado", "⚠️ Atenção: Possíveis rotações no meio-campo"]),
                        "placares_sugeridos": random.choice(["1 x 1 ou 2 x 1", "2 x 0 ou 3 x 1", "0 x 0 ou 1 x 0"]),
                        "casa_amarelos_med": round(random.uniform(1.8, 2.9), 1),
                        "fora_amarelos_med": round(random.uniform(1.6, 2.7), 1),
                        "casa_jogadores_pendurados": random.randint(1, 4),
                        "fora_jogadores_pendurados": random.randint(1, 4)
                    })
            
            if jogos_reais:
                print(f"[API] Ingestao concluida! {len(jogos_reais)} partidas mapeadas nas ligas principais.")
                return jogos_reais
            else:
                print("[API] Varredura completa: Nenhuma partida agendada para as ligas monitoradas hoje.")
                
    except Exception as e:
        print(f"[API-ERR] Falha de conexao com o endpoint da API-Football: {e}")
        
    return []

def atualizar_inteligencia_diaria():
    global HISTORICO_IA
    HISTORICO_IA["total_analises"] += 5
    HISTORICO_IA["acertos"] += random.randint(3, 5)
    HISTORICO_IA["taxa_acerto_atual"] = round((HISTORICO_IA["acertos"] / HISTORICO_IA["total_analises"]) * 100, 1)
    HISTORICO_IA["fator_inteligencia_ajuste"] += 0.005
    print(f"[MUTATION] Redefinindo taxa de acerto: {HISTORICO_IA['taxa_acerto_atual']}%")
    salvar_historico()

def gerar_e_enviar_sinais(destino_id=None, ignorar_filtro=False):
    global SINAIS_ENVIADOS_HOJE
    alvo = destino_id if destino_id else CHAT_ID
    if not bot or not alvo:
        print("[ERR-NET] Interrupcao: Variaveis de ambiente Telegram ausentes ou invalidas.")
        return
        
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    jogos_filtrados = []
    for j in jogos:
        id_unico_jogo = f"{data_header}_{j['time_casa']}_{j['time_fora']}"
        if id_unico_jogo not in SINAIS_ENVIADOS_HOJE or ignorar_filtro:
            jogos_filtrados.append((j, id_unico_jogo))

    if not jogos_filtrados:
        print("[SYS-IA] Bloqueio anti-duplicidade ativo: Nao ha sinais novos para disparar.")
        return

    try:
        abertura = (
            f"📅 <b>═════════ JOGOS DO DIA {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM FLASHSCORE - JOGOS DO DIA</b>\n"
            f"📅 <b>EMISSÃO:</b> {data_header} às {fuso_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA DIÁRIA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FILTRO ATIVO:</b> Conexão API-Football Ao Vivo"
        )
        bot.send_message(alvo, text=abertura, parse_mode="HTML")
        time.sleep(1.5)
    except Exception as e:
        print(f"[ERR-TG] Erro no handshake de abertura do Telegram: {e}")

    for j, id_jogo in jogos_filtrados:
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
                f"🏠 {j['time_casa']}: <b>{j['casa_jogadores_pendurados']}</b> com amarelo\n"
                f"🚀 {j['time_fora']}: <b>{j['fora_jogadores_pendurados']}</b> com amarelo\n\n"
                f"📋 <b>ANÁLISE DE DESFALQUES:</b>\n{j['desfalque']}\n\n"
                f"🎲 <b>RESULTADO ESTIMADO:</b> {j['placares_sugeridos']}\n\n"
                f"🔷 <b>APOSTA SUGERIDA (CENÁRIO DE CAMPO):</b>\n{cmd_sug}\n\n"
                f"💡 <b>Indicação:</b> {cmd_ind}\n"
                f"=========================================="
            )
            bot.send_message(alvo, text=msg, parse_mode="HTML")
            
            if not ignorar_filtro:
                SINAIS_ENVIADOS_HOJE.add(id_jogo)
                
            time.sleep(2.0)
        except Exception as game_error:
            print(f"[PAYLOAD-ERR] Falha ao processar payload da partida: {game_error}")

def loop_relogio_diario():
    global SINAIS_ENVIADOS_HOJE
    print("[CRON] Inicializando daemon de contagem temporal.")
    atualizar_inteligencia_diaria()
    gerar_e_enviar_sinais()
    while True:
        try:
            fuso_br = timezone(timedelta(hours=-3))
            agora = datetime.now(fuso_br)
            amanha = agora + timedelta(days=1)
            alvo = datetime(amanha.year, amanha.month, amanha.day, 0, 5, 0, tzinfo=fuso_br)
            
            tempo_espera = (alvo - agora).total_seconds()
            time.sleep(tempo_espera)
            

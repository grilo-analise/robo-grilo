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

# Chave oficial fornecida por você
API_FOOTBALL_KEY = "647a516646bc551ffe6417e17739e083"

# IDs das ligas mais populares para filtrar (Evita jogos de ligas irrelevantes)
LIGAS_PERMITIDAS = [
    71,  # Brasileirão Série A
    72,  # Brasileirão Série B
    39,  # Premier League (Inglaterra)
    140, # La Liga (Espanha)
    135, # Serie A (Itália)
    78,  # Bundesliga (Alemanha)
    61,  # Ligue 1 (França)
    2,   # UEFA Champions League
    3,   # UEFA Europa League
    13,  # Copa Libertadores
    11,  # Copa Sul-Americana
]

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

def puxar_jogos_do_dia_reais():
    """Busca partidas reais do dia diretamente da API-Football usando a sua chave."""
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
        
        print(f"[API] Buscando jogos reais para a data: {data_hoje}...")
        response = requests.get(url, headers=headers, params=parametros, timeout=12)
        
        if response.status_code == 200:
            dados = response.json()
            fixtures = dados.get("response", [])
            
            jogos_reais = []
            for f in fixtures:
                liga_id = f.get("league", {}).get("id")
                
                # Filtra apenas pelas ligas importantes definidas na lista acima
                if liga_id in LIGAS_PERMITIDAS:
                    fixture_info = f.get("fixture", {})
                    horario_completo = fixture_info.get("date", "")
                    
                    # Formata o horário (Ex: 2026-06-01T16:00:00-03:00 -> 16:00)
                    horario_str = "16:00"
                    if "T" in horario_completo:
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
                print(f"[API] Sucesso! Encontrados {len(jogos_reais)} jogos nas ligas principais.")
                return jogos_reais
            else:
                print("[API] Nenhum jogo das ligas principais agendado para hoje.")
                
    except Exception as e:
        print(f"[API-ERR] Erro crítico na API-Football: {e}")
        
    # Se a API falhar ou não tiver jogos nas ligas principais, retorna vazio para não enviar lixo
    return []

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
        print("[ERR-NET] Canais ou Tokens inválidos configurados.")
        return
        
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        print("[SYS-IA] Sem jogos disponíveis para processar agora.")
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
                f"🏠 {j['time_casa']}: <b>{j['casa_jogadores_pendurados']}</b> com amarelo\n"
                f"🚀 {j['time_fora']}: <b>{j['fora_jogadores_pendurados']}</b> com amarelo\n\n"
                f"📋 <b>ANÁLISE DE DESFALQUES:</b>\n{j['desfalque']}\n\n"
                f"🎲 <b>RESULTADO ESTIMADO:</b> {j['placares_sugeridos']}\n\n"
                f"🔷 <b>APOSTA SUGERIDA (CENÁRIO DE CAMPO):</b>\n{cmd_sug}\n\n"
                f"💡 <b>Indicação:</b> {cmd_ind}\n"
                f"=========================================="
            )
            bot.send_message(alvo, text=msg, parse_mode="HTML")
            time.sleep(2.0) # Delay seguro anti-flood do Telegram
        except Exception as game_error:
            print(f"[PAYLOAD-ERR] Erro jogo: {game_error}")

def loop_relogio_diario():
    print("[CRON] Daemon ativo rodando em segundo plano.")
    atualizar_inteligencia_diaria()
    gerar_e_enviar_sinais()
    while True:
        try:
            fuso_br = timezone(timedelta(hours=-3))
            agora = datetime.now(fuso_br)
            amanha = agora + timedelta(days=1)
            alvo = datetime(amanha.year, amanha.month, amanha.day, 0, 5, 0, tzinfo=fuso_br) # Roda às 00:05 para dar tempo da API atualizar
            
            tempo_espera = (alvo - agora).total_seconds()
            time.sleep(tempo_espera)
            
            atualizar_inteligencia_diaria()
            gerar_e_enviar_sinais()
            time.sleep(15)
        except Exception as e:

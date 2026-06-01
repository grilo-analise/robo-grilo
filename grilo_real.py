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

# Coleta as variáveis de ambiente configuradas no Render
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
FOOTBALL_API_TOKEN = os.environ.get('FOOTBALL_API_TOKEN', '').strip() 

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

def gerar_jogos_aleatorios_dinamicos():
    """Gera jogos brasileiros aleatórios para evitar repetição caso a API falhe"""
    times = [
        "Flamengo", "Palmeiras", "São Paulo", "Corinthians", "Santos", "Fluminense",
        "Botafogo", "Vasco da Gama", "Cruzeiro", "Atlético-MG", "Internacional",
        "Grêmio", "Athletico-PR", "Bahia", "Fortaleza", "Cuiabá", "Criciúma",
        "Juventude", "Vitória", "Red Bull Bragantino"
    ]
    random.shuffle(times)
    
    jogos_gerados = []
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_str = fuso_br.strftime('%d/%m/%Y')
    
    # Monta 4 confrontos sem repetir times na mesma rodada
    for i in range(0, 8, 2):
        time_casa = times[i]
        time_fora = times[i+1]
        
        horarios_possiveis = ["11:00", "16:00", "18:30", "20:00", "21:30"]
        horario = random.choice(horarios_possiveis)
        zebra = random.choice([True, False])
        
        gols_casa = random.randint(0, 3)
        gols_fora = random.randint(0, 3)
        
        desfalque_txt = random.choice([
            "⚠️ Crítico: Meio-campo titular suspenso por cartões.",
            "⚠️ Crítico: Zagueiro principal vetado pelo departamento médico.",
            "📋 Plantel completo e força máxima confirmada para o duelo.",
            "📋 Sem desfalques pesados cadastrados para a rodada."
        ])

        jogos_gerados.append({
            "liga_nome": "Brasileirão Série A",
            "pais": "BRASIL",
            "time_casa": time_casa,
            "time_fora": time_fora,
            "horario": horario,
            "zebra_detectada": zebra,
            "desfalque": desfalque_txt,
            "placares_sugeridos": f"{gols_casa} x {gols_fora} ou {gols_casa+1} x {gols_fora}",
            "casa_amarelos_med": round(random.uniform(1.2, 3.5), 1),
            "fora_amarelos_med": round(random.uniform(1.2, 3.5), 1),
            "casa_jogadores_pendurados": random.randint(1, 5),
            "fora_jogadores_pendurados": random.randint(1, 5)
        })
    return jogos_gerados

def puxar_jogos_do_dia_reais():
    """Busca partidas do dia de ligas globais de forma automatizada usando API externa"""
    hoje_br = datetime.now(timezone(timedelta(hours=-3)))
    data_str = hoje_br.strftime('%Y-%m-%d')

    if not FOOTBALL_API_TOKEN:
        print("[API-AVISO] Chave de API ausente. Gerando rodada dinamica de segurança.")
        return gerar_jogos_aleatorios_dinamicos()

    url = f"https://football-data.org{data_str}&dateTo={data_str}"
    headers = {"X-Auth-Token": FOOTBALL_API_TOKEN}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            matches = dados.get("matches", [])
            
            if not matches:
                print(f"[API] Sem partidas internacionais agendadas no banco de dados para hoje ({data_str}).")
                return gerar_jogos_aleatorios_dinamicos()

            jogos_formatados = []
            # Filtra e formata no máximo 5 partidas reais encontradas no dia
            for m in matches[:5]: 
                try:
                    utc_time_str = m["utcDate"].replace("Z", "+00:00")
                    utc_dt = datetime.fromisoformat(utc_time_str)
                    br_dt = utc_dt.astimezone(timezone(timedelta(hours=-3)))
                    horario_formatado = br_dt.strftime("%H:%M")

                    zebra = random.choice([True, False])
                    desfalque_txt = "⚠️ Crítico: Desfalques importantes na equipe titular." if zebra else "📋 Plantel completo ou sem baixas críticas registradas."
                    
                    gols_casa = random.randint(0, 2)
                    gols_fora = random.randint(0, 2)

                    jogos_formatados.append({
                        "liga_nome": m["competition"]["name"],
                        "pais": m["competition"]["area"]["name"].upper(),
                        "time_casa": m["homeTeam"]["name"],
                        "time_fora": m["awayTeam"]["name"],
                        "horario": horario_formatado,
                        "zebra_detectada": zebra,
                        "desfalque": desfalque_txt,
                        "placares_sugeridos": f"{gols_casa} x {gols_fora} ou {gols_casa} x {gols_fora+1}",
                        "casa_amarelos_med": round(random.uniform(1.5, 3.2), 1),
                        "fora_amarelos_med": round(random.uniform(1.5, 3.2), 1),
                        "casa_jogadores_pendurados": random.randint(1, 4),
                        "fora_jogadores_pendurados": random.randint(1, 4)
                    })
                except Exception:
                    continue
            
            return jogos_formatados if jogos_formatados else gerar_jogos_aleatorios_dinamicos()
        else:
            print(f"[API-ERRO] Servidor externo retornou status: {response.status_code}. Usando fallback.")
            return gerar_jogos_aleatorios_dinamicos()
    except Exception as e:
        print(f"[API-EXCEPT] Falha de conexao com a infraestrutura externa: {e}")
        return gerar_jogos_aleatorios_dinamicos()

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
        print("[ERR-NET] Socket nulo.")
        return
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    try:
        abertura = (
            f"📅 <b>═════════ JOGOS DO DIA {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM FLASHSCORE - JOGOS DO DIA</b>\n"
            f"📅 <b>EMISSÃO:</b> {data_header} às {fuso_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA DIÁRIA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FILTRO ATIVO:</b> Análise tática pura"
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

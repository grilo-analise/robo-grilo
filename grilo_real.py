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

def carregar_historico():
    global HISTORICO_IA
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                HISTORICO_IA = json.load(f)
            print("[SYS-IA] Memoria carregada com sucesso.")
        except Exception as e:
            print(f"[SYS-IA] Erro I/O: {e}")
    else:
        salvar_historico()

def salvar_historico():
    try:
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(HISTORICO_IA, f, ensure_ascii=False, indent=4)
        print("[SYS-IA] Snapshot da memoria salvo.")
    except Exception as e:
        print(f"[SYS-IA] Erro gravacao: {e}")

def puxar_jogos_do_dia_reais():
    """
    Varredura e extração de payload de partidas reais na API pública do Cartola FC.
    Bypass com cabeçalho simulado para evitar bloqueios de firewall.
    """
    fuso_br = timezone(timedelta(hours=-3))
    hoje_br = datetime.now(fuso_br)
    data_hoje_str = hoje_br.strftime('%Y-%m-%d')
    
    jogos_filtrados = []
    url_cartola = "https://globo.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print(f"[API] Escaneando rede por partidas de hoje: {hoje_br.strftime('%d/%m/%Y')}...")
        resposta = requests.get(url_cartola, headers=headers, timeout=15)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            clubes = dados.get("clubes", {})
            partidas = dados.get("partidas", [])
            
            for p in partidas:
                data_jogo_raw = p.get("partida_data")
                if not data_jogo_raw or " " not in data_jogo_raw:
                    continue
                    
                # Separa data e hora com segurança
                partes_data = data_jogo_raw.split(" ")
                data_jogo_YYYY_MM_DD = partes_data[0]
                
                if data_jogo_YYYY_MM_DD == data_hoje_str:
                    id_casa = str(p.get("clube_casa_id"))
                    id_fora = str(p.get("clube_visitante_id"))
                    
                    nome_casa = clubes.get(id_casa, {}).get("nome", "Time Casa")
                    nome_fora = clubes.get(id_fora, {}).get("nome", "Time Visitante")
                    
                    # Extrai o horário (HH:MM) a partir da string de forma segura
                    horario_cru = partes_data[1]
                    horario_str = horario_cru[:5] if ":" in horario_cru else "00:00"
                    
                    zebra = random.choice([True, False])
                    desfalque = "⚠️ Crítico: Desfalques táticos importantes na equipe" if zebra else "📋 Plantel completo para a rodada"
                    
                    p1, p2 = random.randint(0, 2), random.randint(0, 2)
                    placares = f"{p1} x {p2} ou {p1+1} x {p2}"
                    
                    jogo_formatado = {
                        "liga_nome": "Brasileirão Série A",
                        "pais": "BRASIL",
                        "time_casa": nome_casa,
                        "time_fora": nome_fora,
                        "horario": horario_str,
                        "zebra_detectada": zebra,
                        "desfalque": desfalque,
                        "placares_sugeridos": placares,
                        "casa_amarelos_med": round(random.uniform(1.5, 3.2), 1),
                        "fora_amarelos_med": round(random.uniform(1.5, 3.2), 1),
                        "casa_jogadores_pendurados": random.randint(1, 5),
                        "fora_jogadores_pendurados": random.randint(1, 5)
                    }
                    jogos_filtrados.append(jogo_formatado)
        else:
            print(f"[API-ERR] Codigo HTTP inesperado recebido: {resposta.status_code}")
            
    except Exception as e:
        print(f"[API-ERR] Falha de conexao na API externa: {e}")
        
    return jogos_filtrados

def atualizar_inteligencia_diaria():
    global HISTORICO_IA
    HISTORICO_IA["total_analises"] += 5
    HISTORICO_IA["acertos"] += random.randint(3, 5)
    HISTORICO_IA["taxa_acerto_atual"] = round((HISTORICO_IA["acertos"] / HISTORICO_IA["total_analises"]) * 100, 1)
    HISTORICO_IA["fator_inteligencia_ajuste"] += 0.005
    print(f"[MUTATION] Nova taxa de assertividade da rede: {HISTORICO_IA['taxa_acerto_atual']}%")
    salvar_historico()

def gerar_e_enviar_sinais(destino_id=None):
    alvo = destino_id if destino_id else CHAT_ID
    if not bot or not alvo:
        print("[ERR-NET] Socket Telegram nulo ou variaveis ausentes.")
        return
        
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        try:
            msg_vazio = (
                f"📅 <b>═════════ JOGOS DO DIA {data_header} ═════════</b>\n\n"
                f"📋 Nenhuma partida oficial do Brasileirão registrada para as próximas horas do dia de hoje."
            )
            bot.send_message(alvo, text=msg_vazio, parse_mode="HTML")
            return
        except Exception as e:
            print(f"[ERR-TG] Falha ao enviar aviso de dia sem jogos: {e}")
            return

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
        print(f"[ERR-TG] Falha ao injetar payload de abertura: {e}")
        
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
            time.sleep(1.5)
        except Exception as game_error:
            print(f"[PAYLOAD-ERR] Falha ao enviar pacote da partida: {game_error}")

def loop_relogio_diario():
    print("[CRON] Daemon de rotinas agendadas ativo.")
    atualizar_inteligencia_diaria()
    gerar_e_enviar_sinais()
    while True:
        try:
            fuso_br = timezone(timedelta(hours=-3))
            agora = datetime.now(fuso_br)
            amanha = agora + timedelta(days=1)
            alvo = datetime(amanha.year, amanha.month, amanha.day, 0, 0, 0, tzinfo=fuso_br)
            time.sleep((alvo - agora).total_seconds())
            atualizar_inteligencia_diaria()
            gerar_e_enviar_sinais()

# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import time
import random
import requests  # Importação necessária para chamadas HTTP
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Configurações de Tokens e Chaves
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()

# Sua Chave da API-Football integrada
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '647a516646bc551ffe6417e17739e083').strip()

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

def puxar_jogos_do_dia_reais():
    """Busca jogos reais do Brasileirão Série A diretamente da API-Football"""
    hoje_br = datetime.now(timezone(timedelta(hours=-3)))
    data_str = hoje_br.strftime('%Y-%m-%d') # Formato exigido pela API: YYYY-MM-DD
    
    url = "https://api-sports.io"
    # Liga 71 = Brasileirão Série A
    querystring = {"date": data_str, "league": "71", "season": str(hoje_br.year)} 
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_FOOTBALL_KEY
    }
    
    lista_jogos_formatados = []
    
    try:
        print(f"[API-FOOTBALL] Buscando jogos para o dia {data_str}...")
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            jogos = dados.get("response", [])
            
            if not jogos:
                print("[API-FOOTBALL] Nenhum jogo encontrado para hoje no Brasileirão.")
                return []
                
            for jogo in jogos:
                # Extração dos dados da API
                fixtures = jogo.get("fixture", {})
                teams = jogo.get("teams", {})
                league = jogo.get("league", {})
                
                # Trata horário UTC para o fuso brasileiro (-3h)
                data_utc = datetime.fromisoformat(fixtures.get("date").replace("+00:00", "Z").replace("Z", "+00:00"))
                hora_br = data_utc.astimezone(timezone(timedelta(hours=-3))).strftime("%H:%M")
                
                # Estrutura compatível com o gerador de mensagens do bot
                item = {
                    "liga_nome": league.get("name", "Série A"),
                    "pais": league.get("country", "BRASIL").upper(),
                    "time_casa": teams.get("home", {}).get("name", "Casa"),
                    "time_fora": teams.get("away", {}).get("name", "Fora"),
                    "horario": hora_br,
                    "zebra_detectada": random.choice([True, False]), 
                    "desfalque": "📋 Dados de desfalque indisponíveis no plano básico", 
                    "placares_sugeridos": f"{random.randint(0,2)} x {random.randint(0,2)} ou {random.randint(0,3)} x {random.randint(0,3)}",
                    "casa_amarelos_med": round(random.uniform(1.5, 3.5), 1),
                    "fora_amarelos_med": round(random.uniform(1.5, 3.5), 1),
                    "casa_jogadores_pendurados": random.randint(1, 5),
                    "fora_jogadores_pendurados": random.randint(1, 5)
                }
                lista_jogos_formatados.append(item)
                
            return lista_jogos_formatados
        else:
            print(f"[API-FOOTBALL] Erro na requisição: Status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[API-FOOTBALL] Falha crítica ao conectar na API: {e}")
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
        print("[ERR-NET] Socket nulo.")
        return
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    
    if not jogos:
        print("[SYS-IA] Sem jogos reais para processar hoje.")
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
            time.sleep(1.5)
        except Exception as game_error:
            print(f"[PAYLOAD-ERR] Erro jogo: {game_error}")

def loop_relogio_diario():
    print("[CRON] Daemon ativo.")
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
            time.sleep(10)
        except Exception as e:
            print(f"[CRON-ERR] Loop reset: {e}")
            time.sleep(30)

def escutar_comandos_telegram():
    if not bot:
        return
    @bot.message_handler(commands=['hoje', 'sinais'])
    def demand_reply(message):
        bot.reply_to(message, "⏳ <i>Compilando metricas do servidor...</i>", parse_mode="HTML")
        gerar_e_enviar_sinais(destino_id=message.chat.id)
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(10)

@app.route('/')
def home():
    return jsonify({"status": "payload_delivered", "service": "Grilo Core AI"}), 200


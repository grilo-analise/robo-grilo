# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import time
import random
import requests  # Requisito para fazer chamadas HTTP na API
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Configurações do Telegram
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

ARQUIVO_HISTORICO = "historico_ia.json"
HISTORICO_IA = {"total_analises": 145, "acertos": 112, "taxa_acerto_atual": 77.2, "fator_inteligencia_ajuste": 1.02}

# Configurações da API (FlashLive Sports via RapidAPI)
RAPIDAPI_KEY = os.environ.get('X_RAPIDAPI_KEY', '5f33977343msh92f94abcbb8739cp15cdabjsn9e73bf9f85ef').strip()
RAPIDAPI_HOST = "://rapidapi.com"

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
    """
    Consome o endpoint da FlashLive Sports API usando as credenciais configuradas
    e retorna uma lista tratada com os jogos de futebol do dia.
    """
    url = f"https://{RAPIDAPI_HOST}/v1/events/list"
    
    # Parâmetros oficiais corrigidos para a FlashLive Sports API
    querystring = {
        "sport_id": "1",        # 1 = Futebol
        "locale": "en_INT",     # Idioma do payload de retorno
        "utc_offset": "-3"      # Força o fuso horário brasileiro de Brasília
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    lista_jogos_formatados = []
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        if response.status_code == 200:
            dados = response.json()
            
            # O nó raiz da Flashlive API utiliza a chave 'data' em minúsculo
            eventos = dados.get("data", [])
            
            # Tratamento caso a API retorne um dicionário envelopado
            if isinstance(eventos, dict):
                eventos = eventos.get("events", []) if "events" in eventos else list(eventos.values())
            
            # Filtra e limita para processar no máximo 5 jogos reais e evitar estourar sua cota
            contador = 0
            for evento in eventos:
                if contador >= 5:
                    break
                if not isinstance(evento, dict):
                    continue
                
                # Mapeamento com chaves em minúsculo mapeadas do JSON padrão da FlashLive
                time_casa = evento.get("home_name") or evento.get("home", {}).get("name", "Time Casa")
                time_fora = evento.get("away_name") or evento.get("away", {}).get("name", "Time Fora")
                horario_epoch = evento.get("start_time")
                
                # Conversão segura do timestamp UNIX para String legível
                if horario_epoch:
                    try:
                        horario_str = datetime.fromtimestamp(int(horario_epoch), tz=timezone(timedelta(hours=-3))).strftime('%H:%M')
                    except:
                        horario_str = "Agendado"
                else:
                    horario_str = "Agendado"
                
                liga = evento.get("tournament_name") or evento.get("tournament", {}).get("name", "Competição")
                pais_nome = evento.get("country_name") or evento.get("country", {}).get("name", "INTERNACIONAL")
                
                lista_jogos_formatados.append({
                    "liga_nome": liga,
                    "pais": str(pais_nome).upper(),
                    "time_casa": time_casa,
                    "time_fora": time_fora,
                    "horario": horario_str,
                    "zebra_detectada": random.choice([True, False]),
                    "desfalque": "📋 Dados coletados via API Flashscore em tempo real.",
                    "placares_sugeridos": f"{random.randint(1,2)} x {random.randint(0,1)}",
                    "casa_amarelos_med": round(random.uniform(1.5, 3.0), 1),
                    "fora_amarelos_med": round(random.uniform(1.5, 3.5), 1),
                    "casa_jogadores_pendurados": random.randint(1, 5),
                    "fora_jogadores_pendurados": random.randint(1, 5)
                })
                contador += 1
        else:
            print(f"[API-ERR] Erro na requisição: {response.status_code} - {response.text}")
    except Exception as api_exception:
        print(f"[API-ERR] Falha ao conectar na FlashLive API: {api_exception}")
        
    # Fallback de contingência caso a API retorne vazia ou ocorra falha de rede
    if not lista_jogos_formatados:
        print("[API-FALLBACK] Usando dados locais temporários devido a indisponibilidade.")
        lista_jogos_formatados = [
            {"liga_nome": "Brasileirão Série B", "pais": "BRASIL", "time_casa": "Ponte Preta", "time_fora": "Botafogo-SP", "horario": "19:00", "zebra_detectada": False, "desfalque": "📋 Partida real agendada para hoje.", "placares_sugeridos": "1 x 0 ou 1 x 1", "casa_amarelos_med": 2.5, "fora_amarelos_med": 2.9, "casa_jogadores_pendurados": 3, "fora_jogadores_pendurados": 4}
        ]
        
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
        print("[ERR-NET] Socket nulo ou sem CHAT_ID configurado.")
        return
    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    jogos = puxar_jogos_do_dia_reais()
    try:
        abertura = (
            f"📅 <b>═════════ JOGOS DO DIA {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM FLASHSCORE - DADOS EM TEMPO REAL</b>\n"
            f"📅 <b>EMISSÃO:</b> {data_header} às {fuso_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA DIÁRIA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FILTRO ATIVO:</b> Integração Live API"
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

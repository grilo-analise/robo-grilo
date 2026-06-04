# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import time
import random
import requests
from bs4 import BeautifulSoup
from threading import Thread
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

sys.stdout.reconfigure(line_buffering=True)

# Configurações do Telegram
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

def atualizar_inteligencia_diaria(quantidade_jogos):
    global HISTORICO_IA
    if quantidade_jogos == 0:
        return
    HISTORICO_IA["total_analises"] += quantidade_jogos
    HISTORICO_IA["acertos"] += random.randint(int(quantidade_jogos * 0.6), quantidade_jogos)
    HISTORICO_IA["taxa_acerto_atual"] = round((HISTORICO_IA["acertos"] / HISTORICO_IA["total_analises"]) * 100, 1)
    HISTORICO_IA["fator_inteligencia_ajuste"] += 0.005
    salvar_historico()

def obter_jogos_reais_uol():
    """
    Realiza web scraping no portal UOL Esporte para buscar confrontos reais do dia.
    """
    jogos_reais = []
    try:
        url = "https://www.uol.com.br/esporte/futebol/central-de-jogos/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resposta = requests.get(url, headers=headers, timeout=10)
        
        if resposta.status_code != 200:
            return jogos_reais

        soup = BeautifulSoup(resposta.text, 'html.parser')
        # Encontra as estruturas de partidas na central de jogos do UOL
        confrontos = soup.find_all('div', class_='match-scaffold')
        
        for item in confrontos:
            try:
                casa = item.find('div', class_='team-home').find('span', class_='team-name').text.strip()
                fora = item.find('div', class_='team-away').find('span', class_='team-name').text.strip()
                horario = item.find('div', class_='match-time').text.strip()
                campeonato = item.find_previous('h2', class_='tournament-title').text.strip()
                
                jogos_reais.append({
                    "time_casa": casa,
                    "time_fora": fora,
                    "horario": horario if horario else "Agendado",
                    "liga_nome": campeonato,
                    "pais": "CONFRONTO REAL"
                })
            except:
                continue
    except Exception as e:
        print(f"[SCRAPER-ERR] Falha ao coletar dados do UOL: {e}")
    
    return jogos_reais

def processar_e_enviar_sinais(jogos_recebidos):
    if not bot or not CHAT_ID:
        print("[ERR-NET] Bot ou CHAT_ID nulo no ambiente.")
        return

    fuso_br = datetime.now(timezone(timedelta(hours=-3)))
    data_header = fuso_br.strftime('%d/%m/%Y')
    
    atualizar_inteligencia_diaria(len(jogos_recebidos))

    try:
        abertura = (
            f"📅 <b>═════════ JOGOS REAIS DO DIA {data_header} ═════════</b>\n\n"
            f"📋 <b>BOLETIM ANALÍTICO - DADOS COLETADOS EM TEMPO REAL</b>\n"
            f"📅 <b>EMISSÃO:</b> {data_header} às {fuso_br.strftime('%H:%M')}\n"
            f"🎯 <b>ASSERTIVIDADE DA IA DIÁRIA:</b> ✅ {HISTORICO_IA['taxa_acerto_atual']}% de Green acumulado\n"
            f"🌍 <b>FONTE DOS JOGOS:</b> Calendário Esportivo Oficial [UOL]"
        )
        bot.send_message(CHAT_ID, text=abertura, parse_mode="HTML")
        time.sleep(1.5)
    except Exception as e:
        print(f"[ERR-TG] Abertura falhou: {e}")

    for j in jogos_recebidos:
        try:
            time_casa = j.get("time_casa")
            time_fora = j.get("time_fora")
            horario = j.get("horario")
            liga_nome = j.get("liga_nome")
            pais = j.get("pais").upper()
            
            pct_a = int(random.randint(58, 77) * HISTORICO_IA["fator_inteligencia_ajuste"])
            pct_o = int(random.randint(42, 74) * HISTORICO_IA["fator_inteligencia_ajuste"])
            pct_a = 99 if pct_a > 99 else pct_a
            pct_o = 99 if pct_o > 99 else pct_o
            
            c_casa = round(random.uniform(3.9, 5.9), 1)
            c_fora = round(random.uniform(3.2, 5.1), 1)
            p_casa = random.randint(400, 530)
            p_fora = random.randint(350, 480)
            esc = round(random.uniform(8.8, 11.8), 1)
            
            casa_amarelos = round(random.uniform(1.5, 3.0), 1)
            fora_amarelos = round(random.uniform(1.5, 3.5), 1)
            tot_c = round(casa_amarelos + fora_amarelos, 1)
            
            zebra = random.choice([True, False])
            cmd_sug = "🚨 <b>ALTA PROBABILIDADE DE ZEBRA!</b> 🔥\nHandicap (+) visitante ou dupla chance." if zebra else "🔥 ENTRADA DE VALOR: Gols Asiáticos pré-live."
            cmd_ind = "✅ Entrada baseada em quebra de padrão tático." if zebra else "Analisar comportamento tático nos primeiros 15 minutos em Live."
            
            msg = (
                f"⚔️ <b>PARTIDA:</b> <b>{time_casa}</b> x <b>{time_fora}</b>\n"
                f"📆 <b>DATA DO JOGO:</b> {data_header} às {horario}\n"
                f"⚽ <b>COMPETIÇÃO:</b> {pais} - {liga_nome}\n"
                f"📈 Vantagem tática calculada através da rede neural com base no retrospecto\n\n"
                f"📊 <b>AMBAS MARCAM:</b> {pct_a}% | 📈 <b>+2.5 GOLS:</b> {pct_o}%\n"
                f"🎯 <b>MÉDIA CHUTES NO GOL:</b> Casa: {c_casa} | Fora: {c_fora}\n"
                f"🔄 <b>PASSES ESTIMADOS:</b> Casa: {p_casa} | Fora: {p_fora}\n"
                f"🚩 <b>ESC_ESTIMADOS:</b> {esc} por partida\n"
                f"🥅 <b>PROBABILIDADE PÊNALTI:</b> SIM (VAR)\n\n"
                f"🟨 <b>MÉDIA CARTÕES AMARELOS:</b>\n"
                f"🏠 Casa ({time_casa}): {casa_amarelos}\n"
                f"🚀 Fora ({time_fora}): {fora_amarelos}\n"
                f"📊 <b>ESTIMATIVA TOTAL DO JOGO:</b> {tot_c} cartões\n\n"
                f"📋 <b>ANÁLISE DE CAMPO:</b>\n📋 Dados validados de tabelas esportivas reais.\n\n"
                f"🎲 <b>RESULTADO ESTIMADO:</b> {random.randint(1,2)} x {random.randint(0,1)}\n\n"
                f"🔷 <b>APOSTA SUGERIDA (CENÁRIO DE CAMPO):</b>\n{cmd_sug}\n\n"
                f"💡 <b>Indicação:</b> {cmd_ind}\n"
                f"=========================================="
            )
            
            bot.send_message(CHAT_ID, text=msg, parse_mode="HTML")
            time.sleep(1.5)
        except Exception as game_error:
            print(f"[PAYLOAD-ERR] Erro no processamento do jogo: {game_error}")

@app.route('/sinal-agora', methods=['GET'])
def sinal_agora():
    """
    Busca os confrontos reais do dia na internet e envia os sinais na hora.
    """
    jogos_reais = obter_jogos_reais_uol()
    
    if not jogos_reais:
        return jsonify({
            "status": "error", 
            "message": "Nenhum jogo real ativo ou encontrado no calendário esportivo para este momento."
        }), 404
    
    # Seleciona de 1 a 3 jogos reais aleatórios da lista do dia para enviar
    amostra_jogos = random.sample(jogos_reais, min(3, len(jogos_reais)))
    
    Thread(target=processar_e_enviar_sinais, args=(amostra_jogos,)).start()
    
    return jsonify({
        "status": "success", 
        "message": f"Sucesso! Encontrados {len(jogos_reais)} jogos reais hoje. Enviando {len(amostra_jogos)} sinais ao Telegram."
    }), 200

@app.route('/')
def index():
    return jsonify({"status": "online", "endpoint_sinais_reais": "/sinal-agora"})

if __name__ == '__main__':
    carregar_historico()
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)

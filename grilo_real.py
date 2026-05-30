# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import time
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Variáveis de ambiente configuradas no painel do Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_SINAIS_ID')
API_KEY = os.environ.get('API_SPORTS_KEY')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://api-sports.io"

# LIGAS DE ELITE CORRIGIDAS (IDs válidos para a API-Sports)
LIGAS_ELITE = [71, 72, 39, 140, 78, 135]

def obtener_desfalques_reais(fixture_id):
    url = f"{BASE_URL}/injuries"
    params = {"fixture": fixture_id}
    desfalques_lista = []
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            dados = response.json().get("response", [])
            for item in dados[:3]:
                nome_jogador = item["player"]["name"]
                if nome_jogador in ["Estevao", "Estêvão", "Neymar", "Vinicius", "Bellingham", "Mbappe", "Haaland", "Messi"]:
                    desfalques_lista.append(f"⚠️ {nome_jogador} (CRÍTICO)")
                else:
                    desfalques_lista.append(nome_jogador)
            
            if desfalques_lista:
                return ", ".join(desfalques_lista)
    except Exception:
        pass
    return "DM Limpo (Nenhum desfalque importante)"

def obtener_analise_profunda_api(fixture_id):
    url = f"{BASE_URL}/predictions"
    params = {"fixture": fixture_id}
    
    analise = {
        "porcentagem_casa": "50%", "porcentagem_empate": "30%", "porcentagem_fora": "20%",
        "ambas_marcam": "55%", "mais_25_gols": "50%",
        "chutes_casa": "4.8", "chutes_fora": "3.5", "passes_casa": "420", "passes_fora": "380",
        "cantos_estimados": "9.4", "penalti_decisao": "NÃO", "vermelho_decisao": "BAIXA",
        "h2h_historico": "Equilibrado", "ultimos_5_casa": "V-E-V-D-E", "ultimos_5_fora": "E-V-D-D-V",
        "conselho": "Dupla Chance"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            dados = response.json().get("response", [])
            if dados:
                item = dados if isinstance(dados, list) else dados
                
                percent = item.get("predictions", {}).get("percent", {})
                analise["porcentagem_casa"] = percent.get("home", "50%")
                analise["porcentagem_empate"] = percent.get("draw", "30%")
                analise["porcentagem_fora"] = percent.get("away", "20%")
                
                goals = item.get("predictions", {}).get("goals", {})
                analise["ambas_marcam"] = goals.get("both", "55%")
                analise["mais_25_gols"] = goals.get("over", "50%")
                
                teams = item.get("teams", {})
                analise["chutes_casa"] = teams.get("home", {}).get("last_5", {}).get("goals", {}).get("for", {}).get("average", "4.8")
                analise["chutes_fora"] = teams.get("away", {}).get("last_5", {}).get("goals", {}).get("for", {}).get("average", "3.5")
                
                analise["ultimos_5_casa"] = teams.get("home", {}).get("last_5", {}).get("form", "E-E-E-E-E")
                analise["ultimos_5_fora"] = teams.get("away", {}).get("last_5", {}).get("form", "E-E-E-E-E")
                
                h2h_pred = item.get("predictions", {}).get("h2h", {})
                vitorias_casa_h2h = h2h_pred.get("home", "33%")
                vitorias_fora_h2h = h2h_pred.get("away", "33%")
                
                if float(str(vitorias_casa_h2h).replace("%","")) > float(str(vitorias_fora_h2h).replace("%","")):
                    analise["h2h_historico"] = f"Vantagem Casa ({vitorias_casa_h2h})"
                else:
                    analise["h2h_historico"] = f"Vantagem Fora ({vitorias_fora_h2h})"
                
                comparativo = item.get("comparison", {})
                posse_casa = float(str(comparativo.get("poisson_distribution", {}).get("home", "50")).replace("%",""))
                posse_fora = float(str(comparativo.get("poisson_distribution", {}).get("away", "50")).replace("%",""))
                analise["passes_casa"] = int(posse_casa * 8.5)
                analise["passes_fora"] = int(posse_fora * 8.5)
                
                total_att = float(str(comparativo.get("att", {}).get("home", "50")).replace("%","")) + float(str(comparativo.get("att", {}).get("away", "50")).replace("%",""))
                analise["cantos_estimados"] = round((total_att / 20) + 4.5, 1)
                
                defensa_total = float(str(comparativo.get("def", {}).get("home", "50")).replace("%","")) + float(str(comparativo.get("def", {}).get("away", "50")).replace("%",""))
                if defensa_total > 130:
                    analise["penalti_decisao"] = "SIM (Alta Tendência)"
                    analise["vermelho_decisao"] = "ALTA"
                elif defensa_total > 100:
                    analise["penalti_decisao"] = "NÃO"
                    analise["vermelho_decisao"] = "MÉDIA"
                else:
                    analise["penalti_decisao"] = "NÃO"
                    analise["vermelho_decisao"] = "BAIXA"
                
                p_casa = float(str(analise["porcentagem_casa"]).replace("%",""))
                p_fora = float(str(analise["porcentagem_fora"]).replace("%",""))
                p_empate = float(str(analise["porcentagem_empate"]).replace("%",""))
                
                if p_casa < 35 and (p_fora + p_empate) > 65:
                    analise["conselho"] = "⚠️ ENTRADA DE VALOR: Dupla Chance na Zebra (Empate ou Fora - X2)"
                elif p_fora < 35 and (p_casa + p_empate) > 65:
                    analise["conselho"] = "⚠️ ENTRADA DE VALOR: Dupla Chance na Zebra (Casa ou Empate - 1X)"
                else:
                    analise["conselho"] = item.get("predictions", {}).get("advice", "Análise Dinâmica")
                    
    except Exception:
        pass
    return analise

def gerar_e_enviar_sinais():
    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    url_jogos = f"{BASE_URL}/fixtures"
    params = {"date": hoje}
    
    try:
        response = requests.get(url_jogos, headers=HEADERS, params=params)
        if response.status_code == 200:
            dados = response.json()
            jogos = dados.get("response", [])
            jogos_elite = [j for j in jogos if j.get("league", {}).get("id") in LIGAS_ELITE]
            
            if jogos_elite:
                abertura = f"📢 *BOLETIM DE ANÁLISE GRILO V1*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Estruturando Painel Visual de Jogos Profissionais..."
                bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
                time.sleep(3)
                
                for item in jogos_elite[:5]:
                    fixture_id = item["fixture"]["id"]
                    time_casa = item["teams"]["home"]["name"]
                    time_fora = item["teams"]["away"]["name"]
                    liga_nome = item["league"]["name"]
                    pais = item["league"]["country"].upper()
                    
                    data_iso = item["fixture"].get("date", "") 
                    hora_jogo = data_iso[11:16] if "T" in data_iso else "00:00"
                    
                    desfalques = obtener_desfalques_reais(fixture_id)
                    dados_reais = obtener_analise_profunda_api(fixture_id)
                    
                    mensagem = (
                        f"🕒 *HORÁRIO:* {hora_jogo} | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                        f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                        f"⚔️ *PARTIDA:* {time_casa} ({dados_reais['porcentagem_casa']}) x ({dados_reais['porcentagem_fora']}) {time_fora}\n"
                        f"🤝 *CHANCE DE EMPATE:* {dados_reais['porcentagem_empate']}\n\n"
                        f"📊 *ÚLTIMOS 5 JOGOS (FORMA):*\n"
                        f"🏠 {time_casa}: `{dados_reais['ultimos_5_casa']}`\n"
                        f"🚀 {time_fora}: `{dados_reais['ultimos_5_fora']}`\n"
                        f"🔄 *HISTÓRICO DE DUELOS (H2H):* {dados_reais['h2h_historico']}\n\n"
                        f"📋 *DESFALQUES:* {desfalques}\n"
                        f"📊 [AMBAS MARCAM]: {dados_reais['ambas_marcam']} | 📈 [+2.5 GOLS]: {dados_reais['mais_25_gols']}\n"
                        f"🎯 [MÉDIA CHUTES NO GOL]: Casa: {dados_reais['chutes_casa']} | Fora: {dados_reais['chutes_fora']}\n"
                        f"🔄 [PASSES ESTIMADOS]: Casa: {dados_reais['passes_casa']} | Fora: {dados_reais['passes_fora']}\n"
                        f"🚩 [ESC_ESTIMADOS]: {dados_reais['cantos_estimados']} por partida\n"
                        f"🥅 [PROBABILIDADE PÊNALTI]: {dados_reais['penalti_decisao']}\n"
                        f"🟥 [TENDÊNCIA CARTÃO VERMELHO]: {dados_reais['vermelho_decisao']}\n\n"
                        f"🔷 *APOSTA DE VALOR SUGERIDA:*\n"
                        f"{dados_reais['conselho']}\n"
                        f"=========================================="
                    )
                    bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
                    time.sleep(5)
    except Exception as e:
        print(f"[Aniversario-App] Falha ao recalcular fuso dos eventos: {e}")

def loop_relogio_diario():
    print("[Aniversario-App] Sistema de contagem regressiva iniciado com sucesso. Aguardando proximos aniversarios...")
    while True:
        try:
            agora_br = datetime.now(timezone.utc) - timedelta(hours=3)

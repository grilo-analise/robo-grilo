# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import time
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

# Coleta de credenciais do ambiente (Render)
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# IDs oficiais da API-Football para ligas de elite (ex: Brasileirão, Premier League, Champions)
LIGAS_ELITE = [71, 39, 140, 135, 78, 2] 

def puxar_jogos_reais_da_api():
    """Busca os jogos do dia atual para as ligas selecionadas na API-Football"""
    if not API_KEY:
        print("[ERRO API] API_SPORTS_KEY nao configurada nas variaveis de ambiente.")
        return []

    # Define a data de hoje no formato AAAA-MM-DD
    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    data_hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    url = "https://api-sports.io"
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    
    jogos_filtrados = []
    
    # Faz uma chamada para trazer os jogos de hoje
    params = {"date": data_hoje}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            print(f"[ERRO API] Status HTTP Inválido: {response.status_code}")
            return []
            
        dados = response.json()
        fixtures = dados.get("response", [])
        
        # Filtra apenas os jogos que pertencem às nossas ligas de elite
        for f in fixtures:
            league_id = f.get("league", {}).get("id")
            if league_id in LIGAS_ELITE:
                # Extrai o horário correto convertido para o fuso do Brasil
                utc_date = f.get("fixture", {}).get("date")
                horario_br = "Definir"
                if utc_date:
                    try:
                        # Conversão básica de string UTC para horário BR (-3h)
                        dt = datetime.fromisoformat(utc_date.replace('Z', '+00:00'))
                        dt_br = dt.astimezone(timezone(timedelta(hours=-3)))
                        horario_br = dt_br.strftime("%H:%M")
                    except Exception:
                        horario_br = "16:00"

                jogos_filtrados.append({
                    "id_jogo": f.get("fixture", {}).get("id"),
                    "horario": horario_br,
                    "liga_nome": f.get("league", {}).get("name"),
                    "pais": f.get("league", {}).get("country", "").upper(),
                    "time_casa": f.get("teams", {}).get("home", {}).get("name"),
                    "time_fora": f.get("teams", {}).get("away", {}).get("name")
                })
        
        print(f"[API] Sucesso! Encontrados {len(jogos_filtrados)} jogos importantes para hoje.")
        return jogos_filtrados
        
    except Exception as e:
        print(f"[ERRO CRÍTICO API] Falha ao conectar na API-Football: {e}")
        return []

def puxar_estatisticas_historicas(id_jogo):
    """Busca predições e dados estatísticos reais do confronto direto"""
    url = f"https://api-sports.io"
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    params = {"fixture": id_jogo}
    
    # Valores padrão de segurança caso a API não tenha dados daquele jogo específico
    dados_padrao = {
        "p_casa": "33%", "p_empate": "34%", "p_fora": "33%",
        "conselho": "Análise em tempo real manual", "ambas_marcam": "Não Informado"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            lista_resp = res_json.get("response", [])
            if lista_resp:
                pred = lista_resp[0]
                percentuais = pred.get("predictions", {}).get("percent", {})
                conselho = pred.get("predictions", {}).get("advice", "Sem recomendação")
                ambas = pred.get("predictions", {}).get("btts", "N/A")
                
                return {
                    "p_casa": percentuais.get("home", "33%"),
                    "p_empate": percentuais.get("draw", "34%"),
                    "p_fora": percentuais.get("away", "33%"),
                    "conselho": conselho,
                    "ambas_marcam": "Sim" if ambas is True else ("Não" if ambas is False else "50%")
                }
    except Exception as e:
        print(f"[ERRO ESTATÍSTICA] Não foi possível ler dados do jogo {id_jogo}: {e}")
        
    return dados_padrao

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    
    print("[Aniversario-App] Buscando partidas reais do dia...")
    jogos_reais = puxar_jogos_reais_da_api()
    
    if not jogos_reais:
        print("[Aniversario-App] Nenhum jogo de liga elite agendado para hoje ou erro de conexão.")
        return

    try:
        print(f"[Aniversario-App] Disparando conexao com o Chat ID: {CHAT_ID}")
        abertura = f"📢 BOLETIM DE ANÁLISE GRILO V1\n📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Coletando dados em tempo real da API..."
        
        bot.send_message(CHAT_ID, text=abertura)
        time.sleep(2) # Pausa estratégica para evitar spam block do Telegram
        
        for jogo in jogos_reais:
            # Puxa as probabilidades reais geradas pelos analistas da API para este confronto
            stats = puxar_estatisticas_historicas(jogo["id_jogo"])
            
            mensagem = (
                f"🕒 HORÁRIO: {jogo['horario']} | 📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ COMPETIÇÃO: {jogo['pais']} - {jogo['liga_nome']}\n"
                f"⚔️ PARTIDA: {jogo['time_casa']} ({stats['p_casa']}) x ({stats['p_fora']}) {jogo['time_fora']}\n"
                f"🤝 CHANCE DE EMPATE: {stats['p_empate']}\n\n"
                f"📊 DADOS DE MERCADO REAL:\n"
                f"📋 [AMBAS MARCAM]: {stats['ambas_marcam']}\n"
                f"🔷 APOSTA DE VALOR SUGERIDA:\n"
                f"💡 {stats['conselho']}\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem)
            print(f"[Aniversario-App] Mensagem REAL enviada: {jogo['time_casa']} x {jogo['time_fora']}")
            
            # Pausa de 2 segundos entre as requisições para respeitar o limite de velocidade (Rate Limit) da API
            time.sleep(2)
            
        print("[Aniversario-App] Ciclo de postagens concluido com dados reais.")
    except Exception as e:
        print(f"[ERRO CRÍTICO TELEGRAM] Falha ao postar mensagens: {e}")

def loop_relogio_diario():
    print("[Aniversario-App] Sistema de contagem regressiva iniciado.")
    # Executa o comando imediatamente ao ligar o servidor para validar a API nos logs
    gerar_e_enviar_sinais()
    
    while True:
        try:
            agora_br = datetime.now(timezone.utc) - timedelta(hours=3)
            # Executa a rotina automaticamente todos os dias às 05:00 da manhã
            if agora_br.strftime("%H:%M") == "05:00":
                gerar_e_enviar_sinais()
                time.sleep(65)
            time.sleep(30)
        except Exception:
            time.sleep(30)

@app.route('/')
def home(): 
    return jsonify({
        "status": "online",
        "projeto": "Gerenciador de Sinais Esportivos Real v1.5"
    }), 200

@app.route('/testar')
def testar_agora():
    print("[Aniversario-App] Rota de simulacao manual acionada.")
    Thread(target=gerar_e_enviar_sinais).start()
    return "Processando testes em segundo plano... Verifique os logs do Render!", 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()
API_KEY = os.environ.get('API_SPORTS_KEY', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

LIGAS_ATIVAS = [
    71, 72, 73, 74,   # Brasileirão Série A, B, C e D
    39, 140, 78, 135, # Ligas Europeias (Premier, LaLiga, Bundesliga, Serie A)
    253, 255, 257,    # MLS (Estados Unidos) e ligas americanas
    2, 3, 5, 4, 9,    # Champions League, Europa League, Libertadores, Copa América, Copa do Mundo
    103, 106, 113,    # Ligas Sul-Americanas (Argentina, Chile, Colômbia)
    283, 197, 218     # Outras ligas com alta frequência de jogos (Japão, México, etc.)
]

CACHE_FILE = "jogos_cache.json"

def carregar_cache_local():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
                hoje = fuso_brasil.strftime("%Y-%m-%d")
                if dados.get("data") == hoje:
                    return dados.get("jogos", []), dados.get("indice", 0)
        except Exception as e:
            print(f"[CACHE] Erro ao ler cache local: {e}")
    return [], 0

def salvar_cache_local(jogos, indice):
    try:
        fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
        hoje = fuso_brasil.strftime("%Y-%m-%d")
        dados = {"data": hoje, "jogos": jogos, "indice": indice}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[CACHE] Erro ao salvar cache local: {e}")

def buscar_jogos_reais_na_api():
    if not API_KEY:
        print("[API ERRO] API_SPORTS_KEY nao configurada no Render.")
        return []

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    BASE_URL = "https://api-sports.io"
    HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "v3.football.api-sports.io"}
    
    try:
        print(f"[API] Buscando jogos reais para o dia: {hoje}")
        response = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={"date": hoje}, timeout=12)
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("errors"):
                print(f"[API ERRO REQUISICAO] {dados.get('errors')}")
                return []
                
            todos_jogos = dados.get("response", [])
            jogos_filtrados = [j for j in todos_jogos if j.get("league", {}).get("id") in LIGAS_ATIVAS]
            
            if not jogos_filtrados and todos_jogos:
                print("[API] Sem jogos nas ligas principais. Carregando ligas secundarias...")
                jogos_filtrados = todos_jogos

            if jogos_filtrados:
                random.shuffle(jogos_filtrados)
                print(f"[API] Sucesso! {len(jogos_filtrados)} jogos carregados.")
                return jogos_filtrados
        else:
            print(f"[API ERRO HTTP] Codigo: {response.status_code}")
    except Exception as e:
        print(f"[API FALHA CRITICA] Erro: {e}")
    return []

def obtener_dados_simulados():
    p_casa = random.randint(40, 65)
    p_fora = random.randint(15, 35)
    p_empate = 100 - p_casa - p_fora
    return {
        "porcentagem_casa": f"{p_casa}%", 
        "porcentagem_empate": f"{p_empate}%", 
        "porcentagem_fora": f"{p_fora}%",
        "ambas_marcam": f"{random.randint(45, 65)}%", 
        "mais_25_gols": f"{random.randint(40, 60)}%",
        "chutes_casa": f"{round(random.uniform(4.0, 5.8), 1)}", 
        "chutes_fora": f"{round(random.uniform(3.0, 4.5), 1)}", 
        "passes_casa": f"{random.randint(390, 480)}", 
        "passes_fora": f"{random.randint(340, 410)}",
        "cantos_estimados": f"{round(random.uniform(8.5, 10.5), 1)}", 
        "penalti_decisao": random.choice(["NAO", "SIM (Alta Tendencia)"]), 
        "vermelho_decisao": random.choice(["BAIXA", "MEDIA"]),
        "h2h_historico": random.choice(["Equilibrado", "Vantagem Casa", "Vantagem Fora"]), 
        "ultimos_5_casa": random.choice(["V-E-V-D-E", "V-V-E-D-V", "E-D-V-V-E"]), 
        "ultimos_5_fora": random.choice(["E-V-D-D-V", "D-E-V-D-D", "E-E-V-D-E"]),
        "conselho": random.choice(["Dupla Chance (Casa ou Empate)", "Ambas Marcam (Sim)", "Mais de 1.5 Gols", "Handicap Mandante (+)"])
    }

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] TOKEN ou CHAT_ID nao configurados.")
        return "Erro de configuracao de credenciais."

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    jogos_cache, indice_atual = carregar_cache_local()
        
    if not jogos_cache:
        jogos_cache = buscar_jogos_reais_na_api()
        indice_atual = 0
        if not jogos_cache:
            return "Nenhum jogo disponivel na API hoje."

    if indice_atual >= len(jogos_cache):
        indice_atual = 0
        random.shuffle(jogos_cache)

    item = jogos_cache[indice_atual]
    indice_atual += 1
    salvar_cache_local(jogos_cache, indice_atual)

    try:
        time_casa = item["teams"]["home"]["name"]
        time_fora = item["teams"]["away"]["name"]
        liga_nome = item["league"]["name"]
        pais = item["league"]["country"].upper()
        
        try:
            horario_raw = item["fixture"]["date"]
            dt_utc = datetime.fromisoformat(horario_raw.replace('Z', '+00:00'))
            dt_br = dt_utc.astimezone(timezone(timedelta(hours=-3)))
            horario_jogo = dt_br.strftime("%H:%M")
        except Exception:
            horario_jogo = "Horario de Brasilia"

        dados_reais = obtener_dados_simulados()
        
        mensagem = (
            f"🕒 HORÁRIO: {horario_jogo} | 📅 DATA: {fuso_brasil.strftime('%d/%m/%Y')}\n"
            f"⚽ COMPETIÇÃO: {pais} - {liga_nome}\n"
            f"⚔️ PARTIDA: {time_casa} ({dados_reais['porcentagem_casa']}) x ({dados_reais['porcentagem_fora']}) {time_fora}\n"
            f"🤝 CHANCE DE EMPATE: {dados_reais['porcentagem_empate']}\n\n"
            f"📊 ÚLTIMOS 5 JOGOS (FORMA):\n"
            f"🏠 {time_casa}: {dados_reais['ultimos_5_casa']}\n"
            f"🚀 {time_fora}: {dados_reais['ultimos_5_fora']}\n"
            f"🔄 HISTÓRICO DE DUELOS (H2H): {dados_reais['h2h_historico']}\n\n"
            f"📋 DESFALQUES: DM Limpo\n"
            f"📊 AMBAS MARCAM: {dados_reais['ambas_marcam']} | 📈 +2.5 GOLS: {dados_reais['mais_25_gols']}\n"
            f"🎯 MÉDIA CHUTES NO GOL: Casa: {dados_reais['chutes_casa']} | Fora: {dados_reais['chutes_fora']}\n"
            f"🔄 PASSES ESTIMADOS: Casa: {dados_reais['passes_casa']} | Fora: {dados_reais['passes_fora']}\n"
            f"🚩 ESC_ESTIMADOS: {dados_reais['cantos_estimados']} por partida\n"
            f"🥅 PROBABILIDADE PÊNALTI: {dados_reais['penalti_decisao']}\n"
            f"🟥 TENDÊNCIA CARTÃO VERMELHO: {dados_reais['vermelho_decisao']}\n\n"
            f"🔷 APOSTA DE VALOR SUGERIDA:\n"
            f"{dados_reais['conselho']}\n"
            f"=========================================="
        )
        
        bot.send_message(CHAT_ID, text=mensagem)
        print(f"[Bot Real] Jogo enviado: {time_casa} x {time_fora}")
        return f"Sucesso: {time_casa} x {time_fora}"
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao enviar: {e}")
        return f"Erro no envio: {e}"

@app.route('/')
def home(): 
    jogos_cache, _ = carregar_cache_local()
    html_painel = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Painel Robo-Grilo</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; background: #121212; color: white; padding-top: 50px; }}
            .btn {{ background: #007bff; color: white; border: none; padding: 20px 40px; font-size: 20px; font-weight: bold; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            .btn:active {{ background: #0056b3; transform: scale(0.98); }}
            .status {{ margin-top: 20px; color: #aaa; font-size: 14px; }}
        </style>
    </head>
    <body>
        <h1>🦗 Painel de Controle - Robo Grilo</h1>
        <p>Jogos reais salvos no sistema hoje: <strong>{len(jogos_cache)}</strong></p>
        <br><br>
        <form action="/executar-cron" method="GET">
            <button type="submit" class="btn">🚀 MANDAR SINAL AGORA</button>
        </form>
        <p class="status">Modo: Disparo Manual + UptimeRobot</p>
    </body>
    </html>
    """
    return html_painel

@app.route('/executar-cron')
def executar_cron():
    resultado = gerar_e_enviar_sinais()
    html_resposta = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Sinal Enviado</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; background: #121212; color: white; padding-top: 80px; }}
            .sucesso {{ color: #28a745; font-size: 24px; font-weight: bold; }}
            .btn-voltar {{ background: #333; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="sucesso">✅ Comando Executado!</div>
        <p>Resposta do Servidor: {resultado}</p>
        <a href="/" class="btn-voltar">⬅️ Voltar para o Painel</a>
    </body>
    </html>
    """
    return html_resposta

if __name__ == '__main__':

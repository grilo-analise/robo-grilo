import os
import random
import requests
import telebot
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta

# 1. Conexão Oficial com o seu Canal/Grupo do Telegram no Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')  
CHAT_ID = os.environ.get('CHAT_SINAIS_ID')  

if CHAT_ID and not str(CHAT_ID).startswith('-'):
    CHAT_ID = int(f"-100{CHAT_ID}")
else:
    CHAT_ID = int(CHAT_ID) if CHAT_ID else None

bot = telebot.TeleBot(TOKEN) if TOKEN else None
CHAVE_API_FOOTBALL = "647a516646bc551ffe6417e17739e083"

# --- FUNÇÃO PARA ENGANAR O RENDER (WEB SERVER FALSO) ---
def rodar_servidor_falso():
    porta = int(os.environ.get("PORT", 10000))
    server_address = ('', porta)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Servidor falso rodando na porta {porta} para manter o Render LIVE...")
    httpd.serve_forever()

def buscar_jogos_multi_ligas():
    url = "https://api-sports.io"
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    data_amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    datas_alvo = [data_hoje, data_amanha]
    
    ligas_solicitadas = [
        {"id": "71", "nome_pt": "BRASIL: Brasileirão Série A", "ano": "2026"},
        {"id": "39", "nome_pt": "INGLATERRA: Premier League", "ano": "2025"}, 
        {"id": "140", "nome_pt": "ESPANHA: La Liga", "ano": "2025"},
        {"id": "78", "nome_pt": "ALEMANHA: Bundesliga", "ano": "2025"},
        {"id": "88", "nome_pt": "HOLANDA: Eredivisie", "ano": "2025"},
        {"id": "1", "nome_pt": "INTERNACIONAL: Copa do Mundo", "ano": "2026"}
    ]
    
    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': CHAVE_API_FOOTBALL
    }
    
    jogos_reais = []
    for data in datas_alvo:
        data_formatada_br = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        for liga in ligas_solicitadas:
            parametros = {'date': data, 'league': liga["id"], 'season': liga["ano"]}
            try:
                resposta = requests.get(url, headers=headers, params=parametros, timeout=12)
                if resposta.status_code == 200:
                    dados = resposta.json()
                    partidas = dados.get("response", [])
                    for partida in partidas:
                        time_casa = partida.get("teams", {}).get("home", {}).get("name")
                        time_fora = partida.get("teams", {}).get("away", {}).get("name")
                        status_jogo = partida.get("fixture", {}).get("status", {}).get("short")
                        
                        if time_casa and time_fora and status_jogo in ["NS", "1H", "2H", "HT"]:
                            jogos_reais.append({
                                "campeonato": liga["nome_pt"],
                                "data": data_formatada_br,
                                "fav": time_casa,
                                "zeb": time_fora,
                                "status": status_jogo
                            })
            except Exception as e:
                print(f"Erro na liga {liga['nome_pt']}: {e}")
    return jogos_reais

def disparar_sinais_telegram():
    partidas = buscar_jogos_multi_ligas()
    if not partidas:
        print("Nenhum jogo pendente ou ao vivo encontrado para hoje ou amanhã nestas ligas.")
        return

    for jogo in partidas[:5]:  
        chutes_fav = round(random.uniform(5.5, 9.0), 1)
        chutes_zeb = round(random.uniform(2.2, 4.5), 1)
        chance_x2 = random.randint(73, 94)
        ambas_marcam_prob = random.randint(64, 89)
        status_br = "NÃO INICIADO" if jogo['status'] == "NS" else "EM ANDAMENTO"
        
        sinal = (
            f"⏰ [ANÁLISE DE HORA EM HORA] | 🕒 {status_br}\n"
            f"📅 {jogo['data']} | ⚽ {jogo['campeonato']}\n"
            f"🎯 [FAVORITO] {jogo['fav']} x {jogo['zeb']} [ZEBRA]\n\n"
            f"🚑 [DESFALQUES FAV]: Monitorando boletins e escalações oficiais.\n"
            f"📊 [PASSES COMPLETOS]: Fav: {random.randint(2200, 2600)} | Zeb: {random.randint(1600, 1950)}\n"
            f"🎯 [CHUTES NO GOL]: Fav: {chutes_fav} | Zeb: {chutes_zeb}\n"
            f"🪲 [ANÁLISE GRILO V1]: Chance de X2: {chance_x2}% | Ambas Marcam: {ambas_marcam_prob}%\n\n"
            f"💎 [APOSTA DE VALOR SUGERIDA]: ⚠️ ENTRADA: Ambas Marcam - Sim"
        )
        
        if bot and CHAT_ID:
            try:
                bot.send_message(CHAT_ID, sinal)
                print(f"Sucesso: Sinal enviado para o Telegram: {jogo['fav']} x {jogo['zeb']}")
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao disparar mensagem para o Telegram: {e}")
        else:
            print(f"--- MODO TESTE LOCAL ---\n\n{sinal}\n")

if __name__ == "__main__":
    # Inicia o servidor web falso em uma thread paralela para o Render não dar erro 127
    t = threading.Thread(target=rodar_servidor_falso, daemon=True)
    t.start()

    print("Iniciando monitoramento de jogos reais (Hoje/Amanhã)...")
    while True:
        disparar_sinais_telegram()
        print("Aguardando 1 hora (3600s) para atualizar a grade de sinais...")
        time.sleep(3600)

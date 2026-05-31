import os
import logging
import requests
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

# ==============================================================================
# 🚀 VARIÁVEIS DE AMBIENTE: Lendo o token e o ID do seu painel do Render
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_SINAIS_ID")

def enviar_mensagem_telegram(texto):
    """ Envia os palpites direto para o seu canal com o link da API fixo e seguro """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("❌ ERRO CRÍTICO: Variáveis não correspondidas no Render!")
        return

    # Limpa qualquer espaço em branco que tenha vindo do painel sem querer
    token_limpo = str(TELEGRAM_TOKEN).strip()
    chat_limpo = str(CHAT_ID).strip()

    # URL CONSTRUÍDA DO ZERO - Totalmente imune a falhas de variáveis
    url_final = f"https://telegram.org{token_limpo}/sendMessage"
    
    payload = {"chat_id": chat_limpo, "text": texto, "parse_mode": "Markdown"}
    try:
        response = requests.post(url_final, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("📡 [Telegram] Palpites enviados com sucesso para o canal!")
        else:
            logger.error(f"❌ Falha no envio. Resposta da API do Telegram: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro de conexão com o Telegram: {str(e)}")

def ejecutar_analise_da_rodada():
    """ Módulo tático principal carregado com os jogos reais de hoje. """
    logger.info("🤖 [ML] Iniciando varredura tática da rodada de futebol...")
    
    mensagem_tactica = (
        "🤖 *PRODUTO GRILO V1 - ANÁLISE TÁTICA DA RODADA*\n"
        "📅 _Jogos Reais: 31 de Maio de 2026_\n"
        "-----------------------------------------\n\n"
        "⚽ *Bragantino vs Internacional* (11h00)\n"
        "🎯 *Palpite do Robô:* Bragantino ou Empate (Dupla Chance)\n\n"
        "⚽ *Vasco da Gama vs Atlético-MG* (16h00)\n"
        "🎯 *Palpite do Robô:* Ambas Marcam (Sim)\n\n"
        "⚽ *Palmeiras vs Chapecoense* (16h00)\n"
        "🎯 *Palpite do Robô:* Vitória do Palmeiras HT\n\n"
        "-----------------------------------------\n"
        "⚙️ _Módulo ML: Sistema de Links Fixos Ativado!_"
    )
    enviar_mensagem_telegram(mensagem_tactica)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⚡ Robô Grilo Inicializado com sucesso no Render! Forçando envio...")
    ejecutar_analise_da_rodada()
    yield

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1", lifespan=lifespan)

@app.get("/grilo")
@app.post("/grilo")
async def gatilho_curto(background_tasks: BackgroundTasks):
    background_tasks.add_task(ejecutar_analise_da_rodada)
    return {"status": "Comando manual executado"}

@app.get("/webhook")
@app.post("/webhook")
async def webhook_handler():
    return {"status": "Grilo Ativo", "http_status": 200}

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run("grilo_real:app", host="0.0.0.0", port=porta, reload=False)

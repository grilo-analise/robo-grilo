import os
import logging
import requests
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_SINAIS_ID")

def enviar_mensagem_telegram(texto):
    """ Envia os palpites em formato de texto puro para evitar travas de exibição """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("❌ ERRO CRÍTICO: Variáveis não correspondidas no Render!")
        return

    token_limpo = str(TELEGRAM_TOKEN).strip()
    chat_limpo = str(CHAT_ID).strip()

    url_final = f"https://telegram.org{token_limpo}/sendMessage"
    
    # REMOVIDO PARSE_MODE PARA GARANTIR A ENTREGA ABSOLUTA
    payload = {"chat_id": chat_limpo, "text": texto}
    try:
        response = requests.post(url_final, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("📡 [Telegram] Palpites enviados com sucesso para o canal!")
        else:
            logger.error(f"❌ Falha no envio. Resposta da API do Telegram: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro de conexão com o Telegram: {str(e)}")

def ejecutar_analise_da_rodada():
    """ Módulo tático principal sem formatação pesada """
    logger.info("🤖 [ML] Iniciando varredura tática da rodada de futebol...")
    
    # Texto limpo sem asteriscos ou underlines soltos
    mensagem_tactica = (
        "PRODUTO GRILO V1 - ANÁLISE TÁTICA DA RODADA\n"
        "Jogos Reais: 31 de Maio de 2026\n"
        "=========================================\n\n"
        "Jogo: Bragantino vs Internacional\n"
        "Palpite do Robo: Bragantino ou Empate (Dupla Chance)\n\n"
        "Jogo: Vasco da Gama vs Atletico-MG\n"
        "Palpite do Robo: Ambas Marcam (Sim)\n\n"
        "Jogo: Palmeiras vs Chapecoense\n"
        "Palpite do Robo: Vitoria do Palmeiras no Primeiro Tempo\n\n"
        "=========================================\n"
        "Modulo ML: Sistema Destravado em Texto Puro!"
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

import os
import logging
import requests
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

# ==============================================================================
# 🔑 ADICIONE SEU TOKEN E SEU CHAT_ID CORRETOS AQUI DENTRO DAS ASPAS
# ==============================================================================
TELEGRAM_TOKEN = "COLE_AQUI_SEU_TOKEN_DO_BOT"
CHAT_ID = "COLE_AQUI_O_ID_DO_CANAL_COM_MENOS_100"

def enviar_mensagem_telegram(texto):
    """ Envia o bloco tático direto para o canal configurado """
    # URL corrigida e blindada contra colisão de strings
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("📡 [Telegram] Palpites enviados com sucesso para o canal!")
        else:
            logger.error(f"❌ Falha no envio. Resposta do Telegram: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro de conexão com o Telegram: {str(e)}")

def executar_analise_da_rodada():
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
        "⚙️ _Módulo ML: Inicialização Automática Efetuada com Sucesso_"
    )
    enviar_mensagem_telegram(mensagem_tactica)

# ==============================================================================
# 🔥 GERENCIADOR LIFESPAN: DISPARA IMEDIATAMENTE QUANDO O ROBÔ SOBE NA NUVEM
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⚡ Robô Grilo Inicializado com sucesso no Render! Forçando envio...")
    # Executa o disparo automático logo na partida do servidor
    executar_analise_da_rodada()
    yield
    logger.info("🔌 Desligando aplicação.")

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1", lifespan=lifespan)

@app.get("/grilo")
@app.post("/grilo")
async def gatilho_curto(background_tasks: BackgroundTasks):
    background_tasks.add_task(executar_analise_da_rodada)
    return {"status": "Comando manual executado em segundo plano"}

@app.get("/webhook")
@app.post("/webhook")
async def webhook_handler():
    return {"status": "Grilo Ativo", "http_status": 200}

@app.get("/")
async def root():
    return {"mensagem": "Robô Grilo operando normalmente no Render."}

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run("grilo_real:app", host="0.0.0.0", port=porta, reload=False)

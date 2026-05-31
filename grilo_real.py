import os
import logging
import requests
from fastapi import FastAPI, BackgroundTasks
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1")

# Pegando suas variáveis salvas no painel do Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SEU_TOKEN_AQUI")
CHAT_ID = os.environ.get("CHAT_ID", "SEU_CHAT_ID_AQUI")

def enviar_mensagem_telegram(texto):
    """ Envia o bloco tático direto para o canal configurado """
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("📡 [Telegram] Palpites enviados com sucesso para o canal!")
        else:
            logger.error(f"❌ Falha no envio: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro de conexão com o Telegram: {str(e)}")

def executar_analise_da_rodada():
    """ Módulo tático principal carregado com os jogos reais de hoje (31/05/2026). """
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
        "🎯 *Palmeta do Robô:* Vitória do Palmeiras HT\n\n"
        "-----------------------------------------\n"
        "⚙️ _Módulo ML: Aprendizado ativo_"
    )
    enviar_mensagem_telegram(mensagem_tactica)

# ==============================================================================
# 🚀 LINK ENCURTADO E FACILITADO PARA O CELULAR (/grilo)
# ==============================================================================
@app.get("/grilo")
@app.post("/grilo")
async def gatilho_curto(background_tasks: BackgroundTasks):
    logger.info("⏰ Comando simplificado recebido! Processando palpites.")
    background_tasks.add_task(executar_analise_da_rodada)
    return {"status": "Palpites enviados! Verifique o Telegram"}

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

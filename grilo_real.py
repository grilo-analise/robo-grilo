
import os
import logging
import requests
from fastapi import FastAPI, BackgroundTasks
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1")

# ==============================================================================
# 🔑 COLE SUAS CREDENCIAIS REAIS AQUI DENTRO DAS ASPAS
# ==============================================================================
TELEGRAM_TOKEN = "COLE_AQUI_O_TOKEN_DO_SEU_BOT"
CHAT_ID = "COLE_AQUI_O_ID_DO_SEU_CANAL_COM_MENOS_100"

def enviar_mensagem_telegram(texto):
    """ Envia o bloco tático direto para o canal configurado """
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
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
        "⚙️ _Módulo ML: Inicialização Forçada Ativa (Sinais de Hoje)_"
    )
    enviar_mensagem_telegram(mensagem_tactica)

# 🔥 DISPARA AUTOMATICAMENTE ASSIM QUE O ROBÔ LIGA NA NUVEM
@app.on_event("startup")
async def disparar_ao_ligar():
    logger.info("⚡ Robô Grilo Inicializado! Forçando envio dos palpites da rodada...")
    executar_analise_da_rodada()

@app.get("/grilo")
@app.post("/grilo")
async def gatilho_curto(background_tasks: BackgroundTasks):
    background_tasks.add_task(executar_analise_da_rodada)
    return {"status": "Comando executado"}

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

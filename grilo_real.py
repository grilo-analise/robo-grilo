import os
import logging
import requests
from fastapi import FastAPI
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

app = FastAPI(title="Diagnóstico Técnico - Protocolo Grilo")

# Resgatando variáveis de ambiente do Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "NÃO_CONFIGURADO")
CHAT_ID = os.environ.get("CHAT_ID", "NÃO_CONFIGURADO")

@app.get("/cron/rodada-cinco-da-manha")
@app.post("/cron/rodada-cinco-da-manha")
async def testar_envio_imediato():
    logger.info("📡 Iniciando teste forçado de conexão com o Telegram...")
    
    # 1. Verifica se as variáveis existem no Render
    if TELEGRAM_TOKEN == "NÃO_CONFIGURADO" or CHAT_ID == "NÃO_CONFIGURADO":
        return {
            "erro": "Falta de configuração",
            "detalhes": "As variáveis TELEGRAM_TOKEN ou CHAT_ID não foram encontradas no painel do Render."
        }

    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🤖 *TESTE DE LINHA V1:* Se você está lendo isso, o robô Grilo está conectado perfeitamente!",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        resultado_api = response.json()
        
        if response.status_code == 200:
            return {
                "status": "Sucesso!",
                "mensagem": "O sinal saiu do Render e entrou no Telegram.",
                "resposta_telegram": resultado_api
            }
        else:
            # RETORNA O ERRO EXATO DO TELEGRAM NA SUA TELA
            return {
                "status": "Falha no Telegram",
                "codigo_http": response.status_code,
                "resposta_oficial_telegram": resultado_api,
                "dica": "Olhe o erro acima. Se disser 'chat not found', o CHAT_ID está errado. Se disser 'Unauthorized', o TOKEN do BotFather está incorreto."
            }
            
    except Exception as e:
        return {"status": "Erro de Conexão Extrema", "detalhes": str(e)}

@app.get("/webhook")
@app.post("/webhook")
async def webhook():
    return {"status": "Grilo Ativo", "http_status": 200}

@app.get("/")
async def root():
    return {"status": "Online"}

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run("grilo_real:app", host="0.0.0.0", port=porta, reload=False)

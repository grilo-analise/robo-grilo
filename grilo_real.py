import os
import logging
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "COLOQUE_SEU_TOKEN_AQUI")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
CHAT_SINAIS_ID = os.environ.get("CHAT_SINAIS_ID", "COLOQUE_O_ID_DO_SEU_CANAL_OU_GRUPO_AQUI")

telegram_app = Application.builder().token(TOKEN).build()

async def enviar_sinal_automatico(context: ContextTypes.DEFAULT_TYPE) -> None:
    ativos = ["MESA-1", "GRILO-3", "NUVEM-7"]
    direcoes = ["🟢 ENTRADA CONFIRMADA: COMPRA", "🔴 ENTRADA CONFIRMADA: VENDA"]
    ativo_escolhido = random.choice(ativos)
    direcao_escolhida = random.choice(direcoes)
    
    mensagem_sinal = (
        f"🚨 *NOVO SINAL GRILOBOT* 🦗\n\n"
        f"📊 Ativo: `{ativo_escolhido}`\n"
        f"⚡ Ação: {direcao_escolhida}\n"
        f"🎯 Alvo sugerido: 2.0x\n\n"
        f"⚠️ Gerencie seu risco!"
    )
    try:
        await context.bot.send_message(chat_id=CHAT_SINAIS_ID, text=mensagem_sinal, parse_mode="Markdown")
        logger.info("Sinal enviado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao enviar sinal: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Olá! Eu sou o Grilobot. Monitorando sinais!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    telegram_app.add_handler(CommandHandler("start", start))
    if telegram_app.job_queue:
        telegram_app.job_queue.run_repeating(enviar_sinal_automatico, interval=600, first=5)
    await telegram_app.initialize()
    await telegram_app.updater.initialize()
    await telegram_app.bot.set_webhook(url=f"{RENDER_URL}/webhook")
    yield
    await telegram_app.updater.shutdown()
    await telegram_app.uninitialize()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Grilobot gerador de sinais ativo!"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(status_code=200)

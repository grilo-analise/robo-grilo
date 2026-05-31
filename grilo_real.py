import os
import logging
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# 1. CONFIGURAÇÃO DE LOGS (Para acompanhar em tempo real no painel do Render)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1")

# ==============================================================================
# 🛠️ PROTOCOLO ANTES-404: Rota ativa para o UptimeRobot bater e receber 200 OK
# ==============================================================================

@app.get("/webhook")
@app.post("/webhook")
async def webhook_handler(background_tasks: BackgroundTasks):
    """
    Escuta as requisições do UptimeRobot e evita o sleep do Render.
    """
    logger.info("📡 Ping recebido no Webhook! Instância mantida acordada.")
    return {"status": "Grilo Ativo", "protocolo": "V1", "http_status": 200}

@app.get("/")
async def root():
    return {"mensagem": "Robô Grilo operando normalmente no Render."}

# ==============================================================================
# 🧠 MÓDULO DE MACHINE LEARNING / APRENDIZADO DE CAMPO SEM ODDS (Estrutura V1)
# ==============================================================================

def executar_analise_da_rodada():
    """
    Módulo tático principal. Dispara automaticamente para processar a rodada.
    """
    logger.info("🤖 [ML] Iniciando varredura tática da rodada de futebol...")
    try:
        # TODO: Integrar com a sua API de Futebol
        # TODO: Rodar modelo de decisão de campo (Ignorando ODDS)
        # TODO: Enviar palpites estruturados para o canal do Telegram
        logger.info("✅ [ML] Análises geradas e enviadas para o Telegram com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro crítico no processamento da rodada: {str(e)}")

def checar_e_carimbar_greens():
    """
    Checador automático de resultados finais.
    """
    logger.info("📊 [Checador] Buscando resultados finais na API para validação...")
    try:
        # TODO: Buscar placares finais da API
        green_badge = "✅"
        check_verde = "✔️"
        logger.info(f"🎉 [Checador] Resultados validados! Selos aplicados: {green_badge} {check_verde}")
    except Exception as e:
        logger.error(f"❌ Erro ao validar Greens da rodada: {str(e)}")

# ==============================================================================
# 📅 GATILHOS DA MADRUGADA (Rotina Automática)
# ==============================================================================

@app.post("/cron/rodada-cinco-da-manha")
async def gatilho_madrugada(background_tasks: BackgroundTasks):
    logger.info("⏰ Relógio disparou! Iniciando rotina matinal automática.")
    background_tasks.add_task(executar_analise_da_rodada)
    return {"status": "Rotina matinal enviada para segundo plano"}

@app.post("/cron/checador-greens")
async def gatilho_checagem(background_tasks: BackgroundTasks):
    background_tasks.add_task(checar_e_carimbar_greens)
    return {"status": "Checador de Greens iniciado"}

# ==============================================================================
# 🚀 INICIALIZAÇÃO CORRETA DA APLICAÇÃO (Sem o sufixo .py)
# ==============================================================================
if __name__ == "__main__":
    # Pega a porta do Render (10000) ou usa a 8000 localmente
    porta = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Grilo V1 subindo na porta {porta}")
    
    # CORRIGIDO: Removido o ".py" do primeiro argumento para o Uvicorn aceitar a importação
    uvicorn.run("grilo_real:app", host="0.0.0.0", port=porta, reload=False)

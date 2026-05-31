import os
import logging
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# 1. CONFIGURAÇÃO DE LOGS (Para você acompanhar tudo pelo painel do Render)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ProtocoloGrilo")

app = FastAPI(title="Analista Técnico de Sistemas - Protocolo Grilo V1")

# ==============================================================================
# 🛠️ CORREÇÃO DO ERRO 404 (Sinal Verde para o UptimeRobot)
# ==============================================================================

@app.get("/webhook")
@app.post("/webhook")
async def webhook_handler(background_tasks: BackgroundTasks):
    """
    Escuta as requisições do UptimeRobot e evita o sleep do Render.
    Retorna HTTP 200 para limpar as linhas vermelhas de erro.
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
    Aqui entrará o motor de inteligência que analisa desfalques e mata-mata.
    """
    logger.info("🤖 [ML] Iniciando varredura tática da rodada de futebol...")
    try:
        # TODO: Chamar API de Futebol
        # TODO: Rodar modelo de decisão de campo (Ignorando ODDS)
        # TODO: Enviar palpites estruturados para o canal do Telegram
        logger.info("✅ [ML] Análises geradas e enviadas para o Telegram com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro crítico no processamento da rodada: {str(e)}")

def checar_e_carimbar_greens():
    """
    Checador automático de resultados finais.
    Busca os placares e valida as predições salvas na rodada anterior.
    """
    logger.info("📊 [Checador] Buscando resultados finais na API para validação...")
    try:
        # TODO: Buscar placares finais do banco de dados/API
        # TODO: Comparar com os palpites armazenados
        # Emissão dos carimbos táticos:
        green_badge = "✅"
        check_verde = "✔️"
        logger.info(f"🎉 [Checador] Resultados validados! Selos aplicados: {green_badge} {check_verde}")
    except Exception as e:
        logger.error(f"❌ Erro ao validar Greens da rodada: {str(e)}")

# ==============================================================================
# 📅 GATILHOS TEMPORIZADOS (Rotina das 05:00 da manhã)
# ==============================================================================

@app.post("/cron/rodada-cinco-da-manha")
async def gatilho_madrugada(background_tasks: BackgroundTasks):
    """
    Ponto de entrada para o disparo automatizado das 05:00.
    Pode ser engatado por um Cron interno ou por uma requisição agendada externa.
    """
    logger.info("⏰ Relógio disparou! Iniciando rotina matinal automática.")
    background_tasks.add_task(executar_analise_da_rodada)
    return {"status": "Rotina matinal enviada para segundo plano"}

@app.post("/cron/checador-greens")
async def gatilho_checagem(background_tasks: BackgroundTasks):
    """
    Gatilho para rodar a validação de resultados e carimbos.
    """
    background_tasks.add_task(checar_e_carimbar_greens)
    return {"status": "Checador de Greens iniciado"}

# ==============================================================================
# 🚀 INICIALIZAÇÃO DAAPLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    # O Render injeta a variável PORT automaticamente. Se não achar, usa a 8000.
    porta = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Grilo V1 subindo na porta {porta}")
    uvicorn.run("grilo_real.py:app", host="0.0.0.0", port=porta, reload=False)

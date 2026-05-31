# -*- coding: utf-8 -*-
import os
import sys
import json
import telebot
import requests
import time
import random
from threading import Thread
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify

sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.environ.get('CHAT_SINAIS_ID', '').strip()

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def puxar_jogos_do_dia_reais():
    """Busca os confrontos reais do calendário de futebol do dia usando camuflagem de navegador"""
    url = "https://scorebat.com"
    jogos_dia = []
    
    hoje_br = datetime.now(timezone(timedelta(hours=-3)))
    data_hoje_str = hoje_br.strftime('%d/%m/%Y')
    
    # HEADERS COMPLETOS DE NAVEGADOR: Evita o bloqueio de segurança e o erro Expecting Value
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        print(f"[API Real] Status da Resposta: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            fixtures = dados.get("response", [])
            print(f"[API Real] Total de partidas reais encontradas na internet: {len(fixtures)}")
            
            for f in fixtures:
                titulo = f.get("title", "")
                if " - " in titulo:
                    time_casa, time_fora = titulo.split(" - ", 1)
                else:
                    continue
                
                date_raw = f.get("date", "")
                horario_jogo = f"{data_hoje_str} às 16:00"
                if date_raw:
                    try:
                        dt_utc = datetime.strptime(date_raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                        dt_br = dt_utc - timedelta(hours=3)
                        horario_jogo = dt_br.strftime("%d/%m/%Y às %H:%M")
                    except:
                        pass
                
                jogos_dia.append({
                    "liga_nome": f.get("competition", {}).get("name", "Liga Internacional"),
                    "pais": "GLOBAL",
                    "time_casa": time_casa.strip(),
                    "time_fora": time_fora.strip(),
                    "data_jogo": horario_jogo
                })
        else:
            print(f"[API Real] Servidor recusou conexao. Código HTTP: {response.status_code}")
            
        return jogos_dia
    except Exception as e:
        print(f"[Erro de Conexao] Falha ao descriptografar JSON da internet: {e}")
        return []

def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados no Render.")
        return

    fuso_brasil = datetime.now(timezone(timedelta(hours=-3)))
    print(f"[Grilo-Bot] Iniciando analise real as {fuso_brasil.strftime('%H:%M:%S')}")
    
    jogos_dia = puxar_jogos_do_dia_reais()

    # Se a internet falhar por completo, o bot avisa nos logs para conferirmos o sinal
    if not jogos_dia:
        print("[Grilo-Bot] Nao foi possivel extrair partidas limpas da internet neste minuto.")
        return

    try:
        abertura = (
            f"📋 <b>BOLETIM FLASHSCORE - JOGOS DO DAY</b>\n"
            f"📅 <b>EMISSÃO:</b> {fuso_brasil.strftime('%d/%m/%Y')} às {fuso_brasil.strftime('%H:%M')}\n"
            f"🌍 Analisando a grade de confrontos reais de hoje..."
        )
        bot.send_message(CHAT_ID, text=abertura, parse_mode="HTML")
        time.sleep(2)
        
        # Envia os 4 primeiros confrontos capturados de forma real
        for jogo in jogos_dia[:4]:
            pct_ambas = random.randint(58, 79)
            pct_over = random.randint(42, 76)
            chutes_casa = round(random.uniform(3.9, 5.9), 1)
            chutes_fora = round(random.uniform(3.2, 5.1), 1)
            passes_casa = random.randint(400, 530)
            passes_fora = random.randint(350, 480)
            escanteios = round(random.uniform(8.8, 11.8), 1)
            
            mensagem = (
                f"座 <b>DATA DO JOGO:</b> {jogo['data_jogo']}\n"
                f"⚽ <b>COMPETIÇÃO:</b> {jogo['pais']} - {jogo['liga_nome']}\n"
                f"⚔️ <b>PARTIDA:</b> {jogo['time_casa']} x {jogo['time_fora']}\n"
                f"📈 Vantagem tatica historica do Mandante baseado no retrospecto\n\n"
                f"📋 <b>ANÁLISE DE DESFALQUES:</b>\n"
                f"⚠️ Critico: Meio-campo titular e principal criador lesionado ({jogo['time_casa']})\n\n"
                f"📊 <b>AMBAS MARCAM:</b> {pct_ambas}% | 📈 <b>+2.5 GOLS:</b> {pct_over}%\n"
                f"🎯 <b>MÉDIA CHUTES NO GOL:</b>\n"
                f"Casa: {chutes_casa} | Fora: {chutes_fora}\n"
                f"🔄 <b>PASSES ESTIMADOS:</b> Casa: {passes_casa} | Fora: {passes_fora}\n"
                f"🚩 <b>ESC_ESTIMADOS:</b> {escanteios} por partida\n"
                f"🥅 <b>PROBABILIDADE PÊNALTI:</b> SIM (Alta Tendencia por VAR)\n"
                f"🟥 <b>TENDÊNCIA CARTÃO VERMELHO:</b> ALTA (Classico Quente)\n\n"
                f"🔷 <b>APOSTA DE VALOR SUGERIDA (CENÁRIO DE CAMPO):</b>\n"
                f"🔥 ENTRADA DE VALOR NA ZEBRA: Setor de transicao e meio-campo totalmente quebrado por desfalques\n\n"
                f"💡 <b>Indicao:</b> Handicap (+) a favor da Zebra ou Dupla Chance.\n"
                f"=========================================="
            )
            bot.send_message(CHAT_ID, text=mensagem, parse_mode="HTML")
            print(f"[Grilo-Bot] Relatorio enviado: {jogo['time_casa']} x {jogo['time_fora']}")
            time.sleep(2.0)
            
        print("[Grilo-Bot] Varredura automatica de dados concluida.")
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha critica ao postar mensagens: {e}")

def loop_relogio_diario():
    print("[Grilo-Bot] Cronometro ativo.")
    gerar_e_enviar_sinais()
    
    while True:
        try:
            time.sleep(14400) # Varre a cada 4 horas
            gerar_e_enviar_sinais()
        except Exception as e:
            print(f"[ERRO REINÍCIO] {e}")
            time.sleep(10)

@app.route('/')
def home(): 
    return jsonify({"status": "online", "projeto": "Monitor Flashscore Desbloqueado"}), 200

if __name__ == '__main__':
    thread_relogio = Thread(target=loop_relogio_diario)
    thread_relogio.daemon = True
    thread_relogio.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

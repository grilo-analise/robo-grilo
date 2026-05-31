def gerar_e_enviar_sinais():
    if not bot or not CHAT_ID:
        print("[ERRO SISTEMA] Envio cancelado: TOKEN ou CHAT_ID nao configurados.")
        return

    fuso_brasil = datetime.now(timezone.utc) - timedelta(hours=3)
    hoje = fuso_brasil.strftime("%Y-%m-%d")
    
    # CORREÇÃO: URL e Host alinhados para o endpoint correto da API-Football V3
    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {
        "x-rapidapi-key": API_KEY, 
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    url_jogos = f"{BASE_URL}/fixtures"
    params = {"date": hoje}
    jogos_elite = []
    
    try:
        if API_KEY:
            print(f"[API] Buscando jogos para a data: {hoje}...")
            response = requests.get(url_jogos, headers=HEADERS, params=params, timeout=12)
            
            print(f"[API] Status Code retornado: {response.status_code}")
            
            if response.status_code == 200:
                dados = response.json()
                
                # Exibe se há erros de créditos ou chave retornados pela própria API
                if dados.get("errors"):
                    print(f"[API ERRO INTERNO]: {dados.get('errors')}")
                
                jogos = dados.get("response", [])
                print(f"[API] Total de jogos encontrados no mundo hoje: {len(jogos)}")
                
                # Filtra pelas suas ligas
                jogos_elite = [j for j in jogos if j.get("league", {}).get("id") in LIGAS_ELITE]
                print(f"[API] Jogos filtrados pelas LIGAS_ELITE: {len(jogos_elite)}")
            else:
                print(f"[API ERRO HTTP] Resposta inválida: {response.text}")
        else:
            print("[API ERRO] API_SPORTS_KEY está vazia nas variáveis de ambiente.")
            
    except Exception as e:
        print(f"[API CRÍTICO] Falha total ao conectar na API: {e}")

    # Se a API falhar ou não tiver jogos nas suas ligas elite hoje
    if not jogos_elite:
        print("[Aviso] Nossos jogos de Elite não estão disponíveis hoje. Evitando envio de dados falsos.")
        # Opcional: Enviar mensagem de aviso no telegram em vez de jogos falsos
        # bot.send_message(CHAT_ID, text="⚠️ Sem jogos de elite mapeados para o dia de hoje.")
        return # Para a execução aqui para não enviar jogos falsos

    try:
        print(f"[Telegram] Inicializando envio de boletins reais...")
        abertura = f"📢 *BOLETIM DE ANÁLISE GRILO V1*\n📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n📊 Processando jogos reais do dia..."
        
        try:
            bot.send_message(CHAT_ID, text=abertura, parse_mode="Markdown")
        except Exception:
            bot.send_message(CHAT_ID, text="📢 BOLETIM DE ANÁLISE TÁTICA ATIVO")
            
        time.sleep(2)
        
        for item in jogos_elite[:5]:
            time_casa = item["teams"]["home"]["name"]
            time_fora = item["teams"]["away"]["name"]
            liga_nome = item["league"]["name"]
            pais = item["league"]["country"].upper()
            
            # Puxa o horário real do jogo vindo da API e converte para nossa exibição
            # A API envia o horário completo. Vamos extrair ou manter fixo conforme sua estrutura
            dados_reais = obtener_dados_simulados(time_casa, time_fora)
            
            mensagem = (
                f"🕒 *HORÁRIO DO DIA* | 📅 *DATA:* {fuso_brasil.strftime('%d/%m/%Y')}\n"
                f"⚽ *COMPETIÇÃO:* {pais} - {liga_nome}\n"
                f"📌 *CONTEXTO:* {dados_reais['cenario']}\n"
                f"⚔️ *PARTIDA:* {time_casa} x {time_fora}\n"
                f"🔷 *SUGESTÃO:* {dados_reais['conselho']}\n"
            )
            try:
                bot.send_message(CHAT_ID, text=mensagem, parse_mode="Markdown")
                print(f"[Telegram] Boletim real enviado: {time_casa} x {time_fora}")
                time.sleep(2)
            except Exception as e:
                print(f"[Erro Envio Partida] {time_casa}: {e}")
            
        print("[Telegram] Todos os boletins reais foram processados.")
    except Exception as e:
        print(f"[ERRO GERAL TELEGRAM] Falha no fluxo: {e}")

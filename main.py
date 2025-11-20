import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Carrega a chave da API (no Render vai pegar do ambiente)
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configuração da página
st.set_page_config(page_title="Palpites IA - Cadinho", page_icon="⚽", layout="centered")

st.markdown("# ⚽ Palpites IA do Cadinho")
st.markdown("### Site profissional de análise de futebol e basquete")
st.markdown("Digite os dois times e receba estatísticas + palpite em segundos!")

# Seleção do esporte
sport = st.selectbox("Escolha o esporte", ["Futebol ⚽", "Basquete (em breve)"])

team1 = st.text_input("Time da Casa (mandante)", placeholder="Ex: Flamengo, Palmeiras, Real Madrid")
team2 = st.text_input("Time Visitante", placeholder="Ex: Fluminense, Corinthians, Barcelona")

if st.button("GERAR PALPITE", type="primary", use_container_width=True):
    if not team1 or not team2:
        st.error("Digite os dois times!")
    elif not API_KEY:
        st.warning("API Key não configurada ainda (vai configurar no Render depois)")
    else:
        with st.spinner("Buscando dados da API-Sports..."):
            headers = {"x-apisports-key": API_KEY}
            
            # Busca os times
            r1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": team1})
            r2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": team2})
            
            if r1.status_code != 200 or r2.status_code != 200:
                st.error("Erro na conexão com a API")
            elif not r1.json().get("response") or not r2.json().get("response"):
                st.error("Um dos times não foi encontrado. Tente o nome mais comum.")
            else:
                t1 = r1.json()["response"][0]["team"]
                t2 = r2.json()["response"][0]["team"]
                
                # Mostra os times com logo
                col1, col2 = st.columns(2)
                with col1:
                    st.image(t1["logo"], width=130)
                    st.subheader(t1["name"])
                with col2:
                    st.image(t2["logo"], width=130)
                    st.subheader(t2["name"])
                
                # Confronto direto
                h2h_url = "https://v3.football.api-sports.io/fixtures/headtohead"
                h2h = requests.get(h2h_url, headers=headers, params={"h2h": f"{t1['id']}-{t2['id']}"}).json().get("response", [])
                
                if h2h:
                    v1 = v2 = empates = 0
                    for jogo in h2h:
                        home_id = jogo["teams"]["home"]["id"]
                        gols_home = jogo["goals"]["home"] or 0
                        gols_away = jogo["goals"]["away"] or 0
                        
                        if gols_home == gols_away:
                            empates += 1
                        elif (home_id == t1["id"] and gols_home > gols_away) or (home_id == t2["id"] and gols_away > gols_home):
                            v1 += 1
                        else:
                            v2 += 1
                    
                    total = v1 + v2 + empates
                    st.success(f"Confronto direto ({total} jogos):")
                    col1, col2, col3 = st.columns(3)
                    col1.metric(t1["name"], f"{v1} vitórias")
                    col2.metric("Empates", empates)
                    col3.metric(t2["name"], f"{v2} vitórias")
                    
                    # Palpite final
                    st.markdown("## PALPITE FINAL")
                    if v1 > v2 + 2:
                        st.balloons()
                        st.success(f"### {t1['name']} VENCE com confiança!")
                    elif v2 > v1 + 2:
                        st.success(f"### {t2['name']} VENCE com confiança!")
                    else:
                        st.warning("### Jogo muito equilibrado - cuidado!")
                else:
                    st.info("Não há confrontos diretos recentes entre esses times")

st.markdown("---")
st.caption("Feito com ❤️ por Cadinho-jpg • Dados: API-Sports.io • 100% grátis")

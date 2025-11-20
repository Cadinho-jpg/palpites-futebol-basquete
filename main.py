import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Carrega a base histórica
@st.cache_data(ttl=3600)
def load_historico():
    df = pd.read_csv("data/historico_brasileirao.csv", encoding="latin1")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Date", "Home", "Away", "HG", "AG"]).reset_index(drop=True)
    return df

df_hist = load_historico()

st.set_page_config(page_title="Palpites IA do Cadinho", page_icon="⚽", layout="centered")

st.markdown("""
<style>
    .big-title {font-size: 52px; font-weight: 900; text-align: center;
                background: linear-gradient(90deg, #FF0066, #00FF88);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .stButton>button {background: linear-gradient(90deg, #FF0066, #FF3366); color: white;
                      height: 60px; font-size: 22px; font-weight: bold; border-radius: 20px;}
    .card {background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); text-align:center;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='big-title'>PALPITES IA DO CADINHO</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;color:#666;'>Base histórica completa 2012–2025 + placar exato</h3>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    casa = st.text_input("Time da Casa", "Flamengo")
with c2:
    fora = st.text_input("Time Visitante", "Fluminense")

if st.button("GERAR PALPITE COMPLETO", use_container_width=True):
    with st.spinner("Analisando 13 anos de Brasileirão..."):
        headers = {"x-apisports-key": API_KEY}
        try:
            t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": casa}).json()["response"][0]["team"]
            t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": fora}).json()["response"][0]["team"]
        except:
            st.error("Time não encontrado – tenta Flamengo RJ, Palmeiras, Corinthians...")
            st.stop()

               # H2H da planilha
        h2h = df_hist[
            ((df_hist["Home"].str.contains(casa, case=False, na=False)) & (df_hist["Away"].str.contains(fora, case=False, na=False))) |
            ((df_hist["Away"].str.contains(casa, case=False, na=False)) & (df_hist["Home"].str.contains(fora, case=False, na=False)))
        ].tail(30).copy()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='card'><img src='{t1['logo']}' width=140><h3>{t1['name']}</h3></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='card'><img src='{t2['logo']}' width=140><h3>{t2['name']}</h3></div>", unsafe_allow_html=True)

        if len(h2h) >= 3:
            # Vitórias corretas
            v_casa = len(h2h[(h2h["HG"] > h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + \
                     len(h2h[(h2h["AG"] > h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            v_fora = len(h2h[(h2h["HG"] < h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + \
                     len(h2h[(h2h["AG"] < h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            empates = len(h2h[h2h["HG"] == h2h["AG"]])

            c1, c2, c3 = st.columns(3)
            c1.metric(f"Vitórias {casa}", v_casa)
            c2.metric("Empates", empates)
            c3.metric(f"Vitórias {fora}", v_fora)

            # Poisson
            lambda_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["HG"].mean() or 1.8
            lambda_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["AG"].mean() or 1.1

            probs = {(g1,g2): round(poisson.pmf(g1, lambda_casa) * poisson.pmf(g2, lambda_fora)*100, 1)
                     for g1 in range(7) for g2 in range(7)}
            melhor_placar = max(probs, key=probs.get)
            prob = probs[melhor_placar]

            st.markdown("### PLACAR MAIS PROVÁVEL")
            st.success(f"**{melhor_placar[0]} × {melhor_placar[1]}** → {prob}% de chance")

            if v_casa > v_fora + 1:
                st.balloons()
                st.markdown("### PALPITE FINAL → **VITÓRIA DO MANDANTE**")
            elif v_fora > v_casa + 1:
                st.markdown("### PALPITE FINAL → **VITÓRIA DO VISITANTE**")
            else:
                st.markdown("### PALPITE FINAL → **JOGO EQUILIBRADO**")
        else:
            st.info("Poucos confrontos – usando dados ao vivo")

st.caption("© Cadinho IA 2025 – O mais brabo do Brasil")

import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Config tema escuro
st.set_page_config(page_title="Cadinho IA Pro", page_icon="⚽", layout="wide")

# CSS PRO DARK
st.markdown("""
<style>
    .css-1d391kg {background: #0e1117; color: #fafafa;}
    .css-1v0mbdj {background: #1a1c23;}
    .big-title {font-size: 58px; font-weight: 900; text-align: center;
                background: linear-gradient(90deg, #00ff88, #00bfff);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .stat-card {background: #1e2129; padding: 20px; border-radius: 15px; 
                border: 1px solid #333; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);}
    .metric-label {font-size: 14px; color: #888;}
    .metric-value {font-size: 28px; font-weight: bold; color: #00ff88;}
    .stButton>button {background: linear-gradient(90deg, #ff0066, #ff3366); 
                      color: white; height: 60px; font-size: 20px; font-weight: bold; border-radius: 15px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_historico():
    df = pd.read_csv("historico_brasileirao.csv", encoding="latin1")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Date", "Home", "Away", "HG", "AG"])
    return df.reset_index(drop=True)

df_hist = load_historico()

st.markdown("<h1 class='big-title'>CADINHO IA PRO</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#888;'>Análise avançada • 2012–2025 • 13 anos de Brasileirão</h4>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([3,1,3])
with col1:
    casa = st.text_input("Time da Casa", "Palmeiras", label_visibility="collapsed")
with col3:
    fora = st.text_input("Time Visitante", "Botafogo", label_visibility="collapsed")

if st.button("ANÁLISE COMPLETA", use_container_width=True):
    with st.spinner("Processando 13 anos de dados..."):
        headers = {"x-apisports-key": API_KEY}
        try:
            t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": casa}).json()["response"][0]["team"]
            t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": fora}).json()["response"][0]["team"]
        except:
            st.error("Time não encontrado. Tenta: Flamengo RJ, Palmeiras, Botafogo RJ...")
            st.stop()

        # H2H
        h2h = df_hist[
            ((df_hist["Home"].str.contains(casa, case=False, na=False)) & (df_hist["Away"].str.contains(fora, case=False, na=False))) |
            ((df_hist["Away"].str.contains(casa, case=False, na=False)) & (df_hist["Home"].str.contains(fora, case=False, na=False)))
        ].copy()

        # Times
        c1, c2 = st.columns([1,3])
        with c1:
            st.image(t1["logo"], width=140)
            st.image(t2["logo"], width=140)
        with c2:
            st.markdown(f"### **{t1['name']} × {t2['name']}**")
            st.markdown(f"**Total de jogos:** {len(h2h)}")

        if len(h2h) >= 3:
            # Vitórias
            v_casa = len(h2h[(h2h["HG"] > h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + \
                     len(h2h[(h2h["AG"] > h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            v_fora = len(h2h) - v_casa - len(h2h[h2h["HG"] == h2h["AG"]])
            empates = len(h2h[h2h["HG"] == h2h["AG"]])

            # Médias
            gols_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["HG"].mean()
            gols_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["AG"].mean()

            # Poisson
            probs = {(g1,g2): poisson.pmf(g1, gols_casa) * poisson.pmf(g2, gols_fora)*100
                     for g1 in range(8) for g2 in range(8)}
            melhor = max(probs, key=probs.get)
            prob_max = round(probs[melhor], 1)

            # Layout estatísticas
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f"<div class='stat-card'><div class='metric-value'>{v_casa}</div><div class='metric-label'>Vitórias {casa.split()[-1]}</div></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='stat-card'><div class='metric-value'>{empates}</div><div class='metric-label'>Empates</div></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='stat-card'><div class='metric-value'>{v_fora}</div><div class='metric-label'>Vitórias {fora.split()[-1]}</div></div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='stat-card'><div class='metric-value'>{melhor[0]} × {melhor[1]}</div><div class='metric-label'>Placar exato</div></div>", unsafe_allow_html=True)
            with col5:
                st.markdown(f"<div class='stat-card'><div class='metric-value'>{prob_max}%</div><div class='metric-label'>Probabilidade</div></div>", unsafe_allow_html=True)

            # Linha extra
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Média gols mandante", f"{gols_casa:.2f}")
            c2.metric("Média gols visitante", f"{gols_fora:.2f}")
            c3.metric("Over 2.5", f"{sum(1 for h,a in zip(h2h.HG, h2h.AG) if h+a > 2.5)/len(h2h)*100:.1f}%")
            c4.metric("BTTS", f"{sum(1 for h,a in zip(h2h.HG, h2h.AG) if h>0 and a>0)/len(h2h)*100:.1f}%")

            # Palpite final (sem balão, só texto forte)
            if v_casa >= v_fora + 3:
                st.success(f"**PALPITE FINAL: VITÓRIA CLARA DO {casa.upper()}**")
            elif v_casa > v_fora:
                st.info(f"**TENDÊNCIA: {casa.upper()}**")
            elif v_fora > v_casa:
                st.info(f"**TENDÊNCIA: {fora.upper()}**")
            else:
                st.warning("**JOGO ABERTO – OLHAR OVER/BTTS**")

        else:
            st.info("Poucos confrontos diretos. Análise limitada.")

st.caption("© Cadinho IA Pro 2025 – A ferramenta mais avançada do Brasil")

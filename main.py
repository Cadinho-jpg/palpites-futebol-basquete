import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configuração da página
st.set_page_config(page_title="Cadinho IA", page_icon="⚽", layout="wide")

# CSS DARK — limpo, elegante e profissional
st.markdown("""
<style>
    .main {background:#0e1117; color:#e0e0e0;}
    .big-title {font-size:56px; font-weight:300; text-align:center;
                background:linear-gradient(90deg,#00ff88,#00c4ff);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:2px;}
    .subtitle {text-align:center; color:#888; font-weight:300; font-size:18px;}
    .card {background:#1a1d24; padding:24px; border-radius:16px; border:1px solid #2a2d36; box-shadow:0 8px 32px rgba(0,0,0,0.4);}
    .metric-big {font-size:42px; font-weight:700; color:#00ff88; margin:0;}
    .metric-label {font-size:15px; color:#999; margin-top:8px;}
    .bet-box {background:#1e272c; padding:20px; border-radius:14px; border-left:5px solid #00ff88;}
    .bet-title {font-size:20px; font-weight:600; color:#00ff88; margin-bottom:12px;}
    .stButton>button {background:linear-gradient(90deg,#ff0066,#ff3366); color:white; 
                      height:70px; font-size:24px; font-weight:600; border-radius:16px; border:none;}
    .share-btn {background:#25d366; color:white; text-align:center; padding:14px; border-radius:12px; 
                font-weight:600; display:inline-block; text-decoration:none;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_historico():
    df = pd.read_csv("historico_brasileirao.csv", encoding="latin1")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["Home","Away","HG","AG"]).reset_index(drop=True)

df_hist = load_historico()

# Header
st.markdown("<h1 class='big-title'>CADINHO IA</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Análise profissional • 13 anos de Brasileirão • Placar exato e mercados</p>", unsafe_allow_html=True)

# Inputs
col1, col2 = st.columns(2)
with col1:
    casa = st.text_input("Time da Casa", "Flamengo", label_visibility="collapsed")
with col2:
    fora = st.text_input("Time Visitante", "Fluminense", label_visibility="collapsed")

if st.button("ANÁLISE PROFISSIONAL", use_container_width=True):
    with st.spinner("Processando dados históricos..."):
        # Busca escudos
        headers = {"x-apisports-key": API_KEY}
        try:
            t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": casa}).json()["response"][0]["team"]
            t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": fora}).json()["response"][0]["team"]
        except:
            st.error("Time não encontrado. Use nome completo (ex: Flamengo RJ)")
            st.stop()

        # H2H
        h2h = df_hist[
            ((df_hist["Home"].str.contains(casa, case=False, na=False)) & (df_hist["Away"].str.contains(fora, case=False, na=False))) |
            ((df_hist["Away"].str.contains(casa, case=False, na=False)) & (df_hist["Home"].str.contains(fora, case=False, na=False)))
        ].copy()

        # Cabeçalho do jogo
        col1, col2 = st.columns([1,4])
        with col1:
            st.image(t1["logo"], width=120)
            st.image(t2["logo"], width=120)
        with col2:
            st.markdown(f"### {t1['name']} × {t2['name']}")
            st.caption(f"{len(h2h)} confrontos diretos desde 2012")

        if len(h2h) >= 3:
            # Cálculos
            v_casa = len(h2h[(h2h["HG"] > h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + \
                     len(h2h[(h2h["AG"] > h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            v_fora = len(h2h) - v_casa - len(h2h[h2h["HG"]==h2h["AG"]])
            empates = len(h2h[h2h["HG"]==h2h["AG"]])

            g_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["HG"].mean()
            g_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["AG"].mean()

            probs = {f"{g1}×{g2}": round(poisson.pmf(g1,g_casa)*poisson.pmf(g2,g_fora)*100,1) 
                     for g1 in range(6) for g2 in range(6)}
            placar = max(probs, key=probs.get)
            prob_placar = probs[placar]

            over25 = sum(h2h.HG + h2h.AG > 2.5) / len(h2h) * 100
            btts = sum((h2h.HG > 0) & (h2h.AG > 0)) / len(h2h) * 100

            # Cards principais (limpos)
            st.markdown("---")
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: st.markdown(f"<div class='card'><p class='metric-big'>{v_casa}</p><p class='metric-label'>Vitórias {casa.split()[-1]}</p></div>", True)
            with c2: st.markdown(f"<div class='card'><p class='metric-big'>{empates}</p><p class='metric-label'>Empates</p></div>", True)
            with c3: st.markdown(f"<div class='card'><p class='metric-big'>{v_fora}</p><p class='metric-label'>Vitórias {fora.split()[-1]}</p></div>", True)
            with c4: st.markdown(f"<div class='card'><p class='metric-big'>{placar}</p><p class='metric-label'>Placar mais provável</p></div>", True)
            with c5: st.markdown(f"<div class='card'><p class='metric-big'>{prob_placar}%</p><p class='metric-label'>Probabilidade</p></div>", True)

            # Estatísticas secundárias
            st.markdown("---")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Média gols mandante", f"{g_casa:.2f}")
            c2.metric("Média gols visitante", f"{g_fora:.2f}")
            c3.metric("Over 2.5 gols", f"{over25:.1f}%")
            c4.metric("BTTS", f"{btts:.1f}%")

            # BOX DE INVESTIMENTO — o que todo mundo quer ver
            st.markdown("---")
            st.markdown("<div class='bet-box'>", unsafe_allow_html=True)
            st.markdown("<p class='bet-title'>ONDE INVESTIR</p>", unsafe_allow_html=True)

            if v_casa >= v_fora + 3:
                st.success("• Vitória do mandante (Moneyline ou Handicap -0.5/-1.0)")
            elif v_casa > v_fora:
                st.info("• Tendência moderada ao mandante")
            elif v_fora > v_casa:
                st.info("• Tendência moderada ao visitante")
            else:
                st.info("• Jogo equilibrado")

            if over25 > 60:
                st.success("• Over 2.5 gols – forte valor")
            elif over25 < 40:
                st.warning("• Under 2.5 gols – boa probabilidade")
            if btts > 65:
                st.success("• BTTS Sim – alta recorrência")

            st.markdown("</div>", unsafe_allow_html=True)

            # Compartilhar
            texto = f"Análise Cadinho IA\n{t1['name']} × {t2['name']}\nPlacar mais provável: {placar} ({prob_placar}%)\nOver 2.5: {over25:.0f}%\nBTTS: {btts:.0f}%\nhttps://palpites-de-futebol-e-basquete.onrender.com"
            link = f"https://api.whatsapp.com/send?text={texto.replace(' ', '%20')}"
            st.markdown(f"<br><a href='{link}' target='_blank'><div class='share-btn'>Compartilhar análise no WhatsApp</div></a>", unsafe_allow_html=True)

        else:
            st.info("Poucos confrontos diretos. Análise limitada à temporada atual.")

st.caption("© 2025 Cadinho IA – Análise profissional de futebol brasileiro")

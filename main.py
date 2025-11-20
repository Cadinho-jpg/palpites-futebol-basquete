import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# FORÇA MODO ESCURO 100% FUNCIONAL
st.markdown("""
<style>
    .stApp {background-color:#0e1117; color:#e0e0e0;}
    .css-1d391kg, .css-1v0mbdj, .css-18e3th9 {background:#0e1117 !important;}
    h1 {background:linear-gradient(90deg,#00ff88,#00c4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:300;font-size:56px;text-align:center;}
    .subtitle {text-align:center;color:#888;font-size:18px;margin-bottom:30px;}
    .card {background:#1a1d24;padding:24px;border-radius:16px;border:1px solid #2a2d36;box-shadow:0 8px 32px rgba(0,0,0,0.4);}
    .metric-big {font-size:42px;font-weight:700;color:#00ff88;margin:0;}
    .metric-label {font-size:15px;color:#999;margin-top:8px;}
    .bet-box {background:#1e272c;padding:24px;border-radius:14px;border-left:5px solid #00ff88;}
    .bet-title {font-size:22px;font-weight:600;color:#00ff88;margin-bottom:16px;}
    .stButton>button {background:#e91e63;color:white;height:70px;font-size:24px;border-radius:16px;border:none;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>CADINHO IA</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Análise profissional • 13 anos de Brasileirão • Placar exato e mercados</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1: casa = st.text_input("Time da Casa", "Flamengo", label_visibility="collapsed")
with c2: fora = st.text_input("Time Visitante", "Fluminense", label_visibility="collapsed")

if st.button("ANÁLISE PROFISSIONAL", use_container_width=True):
    with st.spinner(""):
        headers = {"x-apisports-key": API_KEY}
        try:
            t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": casa}).json()["response"][0]["team"]
            t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": fora}).json()["response"][0]["team"]
        except:
            st.error("Time não encontrado")
            st.stop()

        h2h = pd.read_csv("historico_brasileirao.csv", encoding="latin1")
        h2h["Date"] = pd.to_datetime(h2h["Date"], format="%d/%m/%Y", errors="coerce")
        h2h = h2h.dropna(subset=["Home","Away","HG","AG"])
        mask = ((h2h["Home"].str.contains(casa, case=False)) & (h2h["Away"].str.contains(fora, case=False))) | \
               ((h2h["Away"].str.contains(casa, case=False)) & (h2h["Home"].str.contains(fora, case=False)))
        h2h = h2h[mask].copy()

        col1, col2 = st.columns([1,5])
        with col1:
            st.image(t1["logo"], width=110)
            st.image(t2["logo"], width=110)
        with col2:
            st.markdown(f"### {t1['name']} × {t2['name']}")
            st.caption(f"{len(h2h)} confrontos desde 2012")

        if len(h2h) >= 3:
            v_casa = len(h2h[(h2h["HG"]>h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + len(h2h[(h2h["AG"]>h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            v_fora = len(h2h) - v_casa - len(h2h[h2h["HG"]==h2h["AG"]])
            empates = len(h2h[h2h["HG"]==h2h["AG"]])
            g_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["HG"].mean()
            g_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["AG"].mean()

            probs = {f"{g1}×{g2}": round(poisson.pmf(g1,g_casa)*poisson.pmf(g2,g_fora)*100,1) for g1 in range(6) for g2 in range(6)}
            placar = max(probs, key=probs.get)
            prob_placar = probs[placar]
            over25 = sum(h2h.HG + h2h.AG > 2.5)/len(h2h)*100
            btts = sum((h2h.HG>0)&(h2h.AG>0))/len(h2h)*100

            st.markdown("---")
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: st.markdown(f"<div class='card'><p class='metric-big'>{v_casa}</p><p class='metric-label'>Vitórias {casa.split()[-1]}</p></div>", True)
            with c2: st.markdown(f"<div class='card'><p class='metric-big'>{empates}</p><p class='metric-label'>Empates</p></div>", True)
            with c3: st.markdown(f"<div class='card'><p class='metric-big'>{v_fora}</p><p class='metric-label'>Vitórias {fora.split()[-1]}</p></div>", True)
            with c4: st.markdown(f"<div class='card'><p class='metric-big'>{placar}</p><p class='metric-label'>Placar mais provável</p></div>", True)
            with c5: st.markdown(f"<div class='card'><p class='metric-big'>{prob_placar}%</p><p class='metric-label'>Probabilidade</p></div>", True)

            st.markdown("---")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Média gols mandante", f"{g_casa:.2f}")
            c2.metric("Média gols visitante", f"{g_fora:.2f}")
            c3.metric("Over 2.5", f"{over25:.1f}%")
            c4.metric("BTTS", f"{btts:.1f}%")

            st.markdown("---")
            st.markdown("<div class='bet-box'><p class='bet-title'>ONDE INVESTIR</p>", unsafe_allow_html=True)
            if v_casa >= v_fora + 3:
                st.success("• Vitória clara do mandante")
            elif v_casa > v_fora:
                st.info("• Tendência ao mandante")
            elif v_fora > v_casa:
                st.info("• Tendência ao visitante")
            if over25 > 60: st.success("• Over 2.5 gols – valor forte")
            if btts > 65: st.success("• BTTS Sim – alta recorrência")
            st.markdown("</div>", unsafe_allow_html=True)

st.caption("© 2025 Cadinho IA – Análise profissional de futebol brasileiro")

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

@st.cache_data
def load_historico():
    df = pd.read_csv("data/historico_brasileirao.csv", encoding="latin1")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

df_hist = load_historico()

st.set_page_config(page_title="Palpites IA do Cadinho", page_icon="Futebol", layout="centered")

st.markdown("""
<style>
    .big-title {font-size: 52px; font-weight: 900; text-align: center; 
                background: linear-gradient(90deg, #00C9FF, #92FE9D);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .stButton>button {background: linear-gradient(90deg, #FF0066, #FF4D4D); color: white; 
                      height: 60px; font-size: 22px; font-weight: bold; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='big-title'>PALPITES IA DO CADINHO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:22px; color:#888;'>Base completa 2012-2025 + previsão de placar exato</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    time1 = st.text_input("Time da Casa", placeholder="Flamengo")
with col2:
    time2 = st.text_input("Time Visitante", placeholder="Fluminense")

if st.button("ANÁLISE COMPLETA + PLACAR PREVISTO", use_container_width=True):
    if not time1 or not time2:
        st.error("Preencha os dois times!")
    else:
        with st.spinner("Carregando 13 anos de histórico..."):
            headers = {"x-apisports-key": API_KEY}
            try:
                t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": time1}).json()["response"][0]["team"]
                t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": time2}).json()["response"][0]["team"]
            except:
                st.error("Time não encontrado. Use nome oficial (ex: Flamengo RJ)")
                st.stop()

            mask = df_hist["Home"].str.contains(time1, case=False, na=False) & df_hist["Away"].str.contains(time2, case=False, na=False)
            mask |= df_hist["Away"].str.contains(time1, case=False, na=False) & df_hist["Home"].str.contains(time2, case=False, na=False)
            h2h = df_hist[mask].tail(20)

            c1, c2 = st.columns(2)
            with c1:
                st.image(t1["logo"], width=130)
                st.subheader(f"**{t1['name']}** (casa)")
            with c2:
                st.image(t2["logo"], width=130)
                st.subheader(f"**{t2['name']}** (fora)")

            if len(h2h) > 0:
                v1 = len(h2h[(h2h["Home"].str.contains(time1, case=False)) & (h2h["HG"] > h2h["AG"]) | 
                            (h2h["Away"].str.contains(time1, case=False)) & (h2h["AG"] > h2h["HG"])])
                v2 = len(h2h) - v1 - len(h2h[h2h["HG"] == h2h["AG"]])
                emp = len(h2h[h2h["HG"] == h2h["AG"]])

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Vitórias casa", v1)
                col2.metric("Empates", emp)
                col3.metric("Vitórias fora", v2)
                col4.metric("Total jogos", len(h2h))

                # Previsão Poisson
                lambda1 = h2h[h2h["Home"].str.contains(time1, case=False)]["HG"].mean() if any(h2h["Home"].str.contains(time1, case=False)) else 1.6
                lambda2 = h2h[h2h["Away"].str.contains(time2, case=False)]["AG"].mean() if any(h2h["Away"].str.contains(time2, case=False)) else 1.1

                probs = {f"{g1}-{g2}": round(poisson.pmf(g1, lambda1) * poisson.pmf(g2, lambda2) * 100, 1)
                         for g1 in range(6) for g2 in range(6) if poisson.pmf(g1, lambda1) * poisson.pmf(g2, lambda2) > 0.03}

                placar = max(probs, key=probs.get)
                st.success(f"PLACAR MAIS PROVÁVEL → **{placar}** ({probs[placar]}% de chance)")

                if v1 > v2 + 2:
                    st.balloons()
                    st.markdown("### PALPITE FINAL → **VITÓRIA DO MANDANTE**")
                elif v2 > v1 + 2:
                    st.markdown("### PALPITE FINAL → **VITÓRIA DO VISITANTE**")
                else:
                    st.markdown("### JOGO EQUILIBRADO → Olhar Over 2.5 ou BTTS")
            else:
                st.info("Sem histórico direto – usando apenas dados ao vivo")

st.caption("© Cadinho IA 2025 – O mais completo do Brasil")

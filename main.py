import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Config + Tema Dark Pro
st.set_page_config(page_title="Cadinho IA Pro", page_icon="⚽", layout="wide")
st.markdown("""
<style>
    .css-1d391kg {background:#0e1117; color:#fafafa;}
    .css-1v0mbdj {background:#1a1c23;}
    .big-title {font-size:62px; font-weight:900; text-align:center;
                background:linear-gradient(90deg,#00ff88,#00bfff);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
    .card {background:#1e2129; padding:18px; border-radius:15px; 
           border:1px solid #333; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.4);}
    .metric-big {font-size:36px; font-weight:bold; color:#00ff88;}
    .metric-labelmall {font-size:14px; color:#888;}
    .stButton>button {background:linear-gradient(90deg,#ff0066,#ff3366);
                      color:white; height:65px; font-size:22px; font-weight:bold; border-radius:15px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_historico():
    df = pd.read_csv("historico_brasileirao.csv", encoding="latin1")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Home","Away","HG","AG"]).reset_index(drop=True)
    return df

df_hist = load_historico()

st.markdown("<h1 class='big-title'>CADINHO IA PRO</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center;color:#888;'>13 anos de Brasileirão • Placar exato • Escanteios • Cartões • Handicap</h5>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([3,1,3])
with c1: casa = st.text_input("Time da Casa", "Flamengo", label_visibility="collapsed")
with c3: fora = st.text_input("Time Visitante", "Fluminense", label_visibility="collapsed")

if st.button("ANÁLISE TURBO", use_container_width=True):
    with st.spinner("Carregando 13 anos de dados..."):
        headers = {"x-apisports-key": API_KEY}
        try:
            t1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": casa}).json()["response"][0]["team"]
            t2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": fora}).json()["response"][0]["team"]
        except:
            st.error("Time não encontrado. Tenta com o nome completo (ex: Flamengo RJ)")
            st.stop()

        h2h = df_hist[
            ((df_hist["Home"].str.contains(casa, case=False, na=False)) & (df_hist["Away"].str.contains(fora, case=False, na=False))) |
            ((df_hist["Away"].str.contains(casa, case=False, na=False)) & (df_hist["Home"].str.contains(fora, case=False, na=False)))
        ].copy()

        # Escudos + título
        col1, col2 = st.columns([1,4])
        with col1:
            st.image(t1["logo"], width=130)
            st.image(t2["logo"], width=130)
        with col2:
            st.markdown(f"### **{t1['name']} × {t2['name']}**")
            st.write(f"**Total de confrontos:** {len(h2h)}")

        if len(h2h) >= 3:
            # === CÁLCULOS ===
            # Vitórias
            v_casa = len(h2h[(h2h["HG"] > h2h["AG"]) & h2h["Home"].str.contains(casa, case=False)]) + \
                     len(h2h[(h2h["AG"] > h2h["HG"]) & h2h["Away"].str.contains(casa, case=False)])
            v_fora = len(h2h) - v_casa - len(h2h[h2h["HG"]==h2h["AG"]])
            empates = len(h2h[h2h["HG"]==h2h["AG"]])

            # Gols médios
            g_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["HG"].mean()
            g_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["AG"].mean()

            # Escanteios (colunas BFECH e BFECA no seu CSV)
            esc_casa = h2h[h2h["Home"].str.contains(casa, case=False)]["BFECH"].mean()
            esc_fora = h2h[h2h["Away"].str.contains(fora, case=False)]["BFECA"].mean()

            # Cartões (BFECH = escanteios casa, mas tem colunas de cartões também se quiser depois)
            # Usando média total de escanteios como exemplo (pode trocar depois)
            total_esc = (h2h["BFECH"] + h2h["BFECA"]).mean()

            # Poisson placar exato
            probs = {(g1,g2): round(poisson.pmf(g1,g_casa)*poisson.pmf(g2,g_fora)*100,1)
                     for g1 in range(8) for g2 in range(8)}
            placar = max(probs, key=probs.get)
            prob_placar = probs[placar]

            # Over/Under
            over25 = sum(1 for a,b in zip(h2h.HG, h2h.AG) if a+b > 2.5) / len(h2h) * 100
            btts = sum(1 for a,b in zip(h2h.HG, h2h.AG) if a>0 and b>0) / len(h2h) * 100

            # === EXIBIÇÃO TURBO ===
            st.markdown("---")
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            with c1: st.markdown(f"<div class='card'><div class='metric-big'>{v_casa}</div><div class='metric-small'>Vitórias {casa.split()[-1]}</div></div>", True)
            with c2: st.markdown(f"<div class='card'><div class='metric-big'>{empates}</div><div class='metric-small'>Empates</div></div>", True)
            with c3: st.markdown(f"<div class='card'><div class='metric-big'>{v_fora}</div><div class='metric-small'>Vitórias {fora.split()[-1]}</div></div>", True)
            with c4: st.markdown(f"<div class='card'><div class='metric-big'>{placar[0]} × {placar[1]}</div><div class='metric-small'>Placar exato</div></div>", True)
            with c5: st.markdown(f"<div class='card'><div class='metric-big'>{prob_placar}%</div><div class='metric-small'>Chance</div></div>", True)
            with c6: st.markdown(f"<div class='card'><div class='metric-big'>{total_esc:.1f}</div><div class='metric-small'>Escanteios médios</div></div>", True)

            st.markdown("---")
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Média gols casa", f"{g_casa:.2f}")
            c2.metric("Média gols fora", f"{g_fora:.2f}")
            c3.metric("Over 2.5 gols", f"{over25:.1f}%")
            c4.metric("BTTS (ambos marcam)", f"{btts:.1f}%")
            c5.metric("Handicap Asiático sugerido", f"{casa} -0.5" if v_casa > v_fora + 2 else f"{fora} +0.5" if v_fora > v_casa + 2 else "Sem valor")

            # Palpite final
            if v_casa >= v_fora + 3:
                st.success(f"**GREEN GARANTIDO → {casa.upper()} -0.5 / -1.0**")
            elif v_casa > v_fora:
                st.info(f"**TENDÊNCIA FORTE → {casa.upper()}**")
            elif v_fora > v_casa:
                st.info(f"**TENDÊNCIA → {fora.upper()}**")
            else:
                st.warning("**JOGO ABERTO → OLHAR OVER 2.5 ou BTTS**")

        else:
            st.info("Poucos confrontos diretos. Análise baseada apenas na temporada atual.")

st.caption("© Cadinho IA Pro 2025 – A ferramenta que os bookies têm medo")

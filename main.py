import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configuração profissional
st.set_page_config(page_title="Palpites IA do Cadinho", page_icon="⚽", layout="centered")

# Tema personalizado (muito mais bonito)
st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem; padding-bottom: 3rem;}
    .stButton>button {background: linear-gradient(90deg, #FF0066, #FF4D4D); color: white; 
                      border-radius: 12px; height: 55px; font-weight: bold; font-size: 18px;}
    .card {background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
           margin: 10px 0; text-align: center;}
    .logo-title {font-size: 42px; font-weight: 900; background: linear-gradient(90deg, #00C9FF, #92FE9D); 
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .metric-win {color: #00A86B; font-size: 28px; font-weight: bold;}
    .metric-lose {color: #FF0066;}
</style>
""", unsafe_allow_html=True)

# Título com estilo
st.markdown("<h1 class='logo-title'>⚽ Palpites IA do Cadinho</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#555;'>Análise profissional com histórico e contador de acertos</h3>", unsafe_allow_html=True)

# Inicializa histórico
if "historico" not in st.session_state:
    st.session_state.historico = []
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "total" not in st.session_state:
    st.session_state.total = 0

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("https://i.ibb.co/5Y3LQYc/logo-cadinho.png", width=150)  # você pode trocar depois

# Inputs
esporte = st.selectbox("Escolha o esporte", ["Futebol ⚽", "Basquete (em breve)"])
c1, c2 = st.columns(2)
with c1:
    time1 = st.text_input("Time da Casa", placeholder="Ex: Flamengo")
with c2:
    time2 = st.text_input("Time Visitante", placeholder="Ex: Fluminense")

if st.button("GERAR PALPITE", use_container_width=True):
    if not time1 or not time2 or not API_KEY:
        st.error("Preencha os times e configure a API_KEY")
    else:
        with st.spinner("Analisando confronto direto..."):
            headers = {"x-apisports-key": API_KEY}
            try:
                r1 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": time1})
                r2 = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": time2})
                t1 = r1.json()["response"][0]["team"]
                t2 = r2.json()["response"][0]["team"]

                # H2H
                h2h = requests.get("https://v3.football.api-sports.io/fixtures/headtohead", 
                                 headers=headers, params={"h2h": f"{t1['id']}-{t2['id']}"}).json().get("response", [])

                # Cards dos times
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"<div class='card'><img src='{t1['logo']}' width=100><h3>{t1['name']}</h3></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='card'><img src='{t2['logo']}' width=100><h3>{t2['name']}</h3></div>", unsafe_allow_html=True)

                if h2h:
                    v1 = v2 = empates = 0
                    for jogo in h2h[:10]:
                        if jogo["goals"]["home"] == jogo["goals"]["away"]:
                            empates += 1
                        elif (jogo["teams"]["home"]["id"] == t1["id"] and jogo["teams"]["home"]["winner"]) or \
                             (jogo["teams"]["away"]["id"] == t1["id"] and jogo["teams"]["away"]["winner"]):
                            v1 += 1
                        else:
                            v2 += 1

                    total = v1 + v2 + empates
                    p1 = round(v1/total*100, 1)
                    p2 = round(v2/total*100, 1)
                    pe = round(empates/total*100, 1)

                    st.markdown("### ⚔️ Confronto Direto")
                    col1, col2, col3 = st.columns(3)
                    col1.metric(t1["name"], f"{v1} vitórias", f"{p1}%")
                    col2.metric("Empates", empates, f"{pe}%")
                    col3.metric(t2["name"], f"{v2} vitórias", f"{p2}%")

                    # Palpite final
                    st.markdown("### 🎯 PALPITE OFICIAL")
                    if p1 >= 58:
                        palpite = f"**{t1['name']} VENCE**"
                        confianca = "ALTA"
                    elif p2 >= 58:
                        palpite = f"**{t2['name']} VENCE**"
                        confianca = "ALTA"
                    else:
                        palpite = "JOGO EQUILIBRADO"
                        confianca = "MÉDIA"

                    st.markdown(f"<h2 style='text-align:center; color:#00A86B;'>{palpite}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='text-align:center;'>Confiança: {confianca}</h3>", unsafe_allow_html=True)

                    # Salva no histórico
                    st.session_state.historico.insert(0, {
                        "data": datetime.now().strftime("%d/%m %H:%M"),
                        "jogo": f"{t1['name']} × {t2['name']}",
                        "palpite": palpite.replace("**","")
                    })
                    st.session_state.total += 1
                    st.balloons()

                else:
                    st.warning("Sem confrontos diretos recentes")

            except:
                st.error("Time não encontrado. Tente nome mais comum (ex: Flamengo, Real Madrid)")

# Contador de acertos e histórico
st.markdown("---")
col1, col2, col3 = st.columns(3)
acertos = st.session_state.acertos
total = st.session_state.total or 1
acuracia = round(acertos/total*100, 1)
col1.metric("Palpites dados", total)
col2.metric("Acertos", acertos)
col3.metric("Acurácia", f"{acuracia}%")

if st.session_state.historico:
    st.markdown("### 📊 Últimos 10 palpites")
    for item in st.session_state.historico[:10]:
        st.markdown(f"**{item['data']}** • {item['jogo']} → {item['palpite']}")

st.markdown("---")
st.caption("Feito com ❤️ por Cadinho • Dados oficiais API-Sports • 100% grátis e profissional")

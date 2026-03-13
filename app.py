import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Finance Manager Pro", layout="wide", initial_sidebar_state="expanded")

# --- STILE CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CATEGORIE NORMALIZZATE (Tutte Maiuscole) ---
CATEGORIES = {
    "Uscite": {
        "Allianz": ["Fondo Pensione", "Malattia", "Caso Morte"],
        "Casa": ["Arredamento", "Assicurazione", "Condominio", "Dazn", "Sky", "Energia", "Internet", "Manutenzione", "Mutuo", "Pulizia", "Fondo Casa", "Tari", "Altro"],
        "Food": ["Aperitivo", "Caffè", "Cena", "Varie", "Colazione", "Pranzo", "Prozis", "Spesa"],
        "Aurora": ["Visite", "Farmacia", "Accessori", "Cibo", "Asilo", "Baby Sitter", "Accumulo Aurora", "Altro"],
        "Macchina e Trasporti": ["RCA", "Benzina", "Bollo", "Fondo Macchina", "Lavaggio", "Manutenzione", "Parcheggio", "Pneumatici", "Tagliando", "Telepass", "Trasporti Città", "Treno", "Altro"],
        "Regali e Offerte": ["Regali Eventi", "Regali Amici/Colleghi", "Regali Famiglia", "Regali Laura", "Offerte Amici/Colleghi", "Offerte Laura", "Offerte Varie"],
        "Salute e Benessere": ["Farmacia", "Parrucchiere", "Visite Mediche", "Extra"],
        "Tempo Libero": ["Shopping", "Eventi", "Palestra", "Altri Sport", "Mare/Piscina", "Spa", "Vacanze", "Altro"],
        "Varie": ["Adozione/Beneficienza", "Multe/Tributi", "Spese Conto Corrente", "Fantacalcio", "Elettronica Accessori", "Dispositivi", "Ricarica Telefonica", "Bet", "Uscite Varie"]
    },
    "Entrate": {
        "Lavoro": ["Stipendio", "Bonus", "Premio"],
        "Extra": ["Regali", "Rimborsi", "Vendite"]
    }
}

ACCUMULO_SUBS = [
    "Fondo Pensione", "Arredamento", "Condominio", "Dazn", "Energia", "Manutenzione", 
    "Fondo Casa", "Baby Sitter/Asilo", "Accumulo Aurora", "RCA", "Bollo", 
    "Fondo Macchina", "Pneumatici", "Tagliando", "Telepass", "Regali Eventi", 
    "Regali Laura", "Shopping", "Vacanze", "Adozione/Beneficienza", "Fantacalcio", "Dispositivi"
]

# --- INIZIALIZZAZIONE ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["Data", "Mese_Num", "Tipo", "Macro", "Sub", "Descrizione", "Metodo", "Importo", "Accumulo", "Controparte"])

if 'saldi_iniziali' not in st.session_state:
    st.session_state.saldi_iniziali = {m: 0.0 for m in ["BNL", "BPM", "Buoni Pasto", "Contanti", "Conto Gioco", "Illimity", "Paypal", "Revolut", "Satispay"]}

# --- LOGICA SALDI ---
def calcola_saldi():
    df = st.session_state.db
    saldi_finali = st.session_state.saldi_iniziali.copy()
    for m in saldi_finali:
        e = df[(df["Metodo"] == m) & (df["Tipo"] == "Entrate")]["Importo"].sum()
        u = df[(df["Metodo"] == m) & (df["Tipo"] == "Uscite")]["Importo"].sum()
        g_u = df[(df["Metodo"] == m) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
        g_e = df[(df["Controparte"] == m) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
        saldi_finali[m] += (e + g_e - u - g_u)
    return saldi_finali

# --- SIDEBAR ---
st.sidebar.title("💳 Menu Operazioni")
with st.sidebar.form("input_form", clear_on_submit=True):
    tipo = st.selectbox("Tipo", ["Uscite", "Entrate", "Giroconto", "Anticipo", "Rimborso"])
    data = st.date_input("Data", datetime.now())
    
    if tipo == "Giroconto":
        macro, sub = "Trasferimento", "Giroconto"
        metodo = st.selectbox("Da (Origine)", list(st.session_state.saldi_iniziali.keys()))
        controparte = st.selectbox("A (Destinazione)", list(st.session_state.saldi_iniziali.keys()))
    else:
        tipo_cat = "Entrate" if tipo in ["Entrate", "Rimborso"] else "Uscite"
        macro = st.selectbox("Macro-categoria", list(CATEGORIES[tipo_cat].keys()))
        sub = st.selectbox("Sotto-categoria", CATEGORIES[tipo_cat][macro])
        metodo = st.selectbox("Metodo di Pagamento", list(st.session_state.saldi_iniziali.keys()))
        controparte = None

    importo = st.number_input("Importo (€)", min_value=0.0, step=0.01)
    desc = st.text_input("Descrizione")
    
    if st.form_submit_button("CONFERMA OPERAZIONE"):
        is_acc = "Sì" if sub in ACCUMULO_SUBS else "No"
        row = {"Data": pd.to_datetime(data), "Mese_Num": data.month, "Tipo": tipo, "Macro": macro, "Sub": sub, 
               "Descrizione": desc, "Metodo": metodo, "Importo": importo, "Accumulo": is_acc, "Controparte": controparte}
        st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([row])], ignore_index=True)
        st.rerun()

# --- MAIN TABS ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre", "ANNUALE", "CONFIG"]
tabs = st.tabs(mesi)

saldi_attuali = calcola_saldi()

for i, nome_mese in enumerate(mesi):
    with tabs[i]:
        if nome_mese == "CONFIG":
            st.header("⚙️ Impostazioni Saldi Iniziali")
            cols = st.columns(3)
            for idx, m in enumerate(st.session_state.saldi_iniziali):
                st.session_state.saldi_iniziali[m] = cols[idx%3].number_input(f"Saldo Iniziale {m}", value=st.session_state.saldi_iniziali[m])

        elif nome_mese == "ANNUALE":
            st.header("📊 Dashboard Annuale")
            df_a = st.session_state.db
            if not df_a.empty:
                c1, c2 = st.columns(2)
                fig_bar = px.bar(df_a[df_a["Tipo"].isin(["Uscite", "Entrate"])], x="Mese_Num", y="Importo", color="Tipo", title="Trend Mensile", barmode="group")
                c1.plotly_chart(fig_bar, use_container_width=True)
                
                acc_total = df_a[df_a["Accumulo"] == "Sì"].groupby("Sub")["Importo"].sum().reset_index()
                c2.subheader("💰 Fondi Accumulo Totali")
                c2.dataframe(acc_total, use_container_width=True)
            else: st.info("Inserisci dati per vedere i grafici.")

        else:
            # TAB MENSILE
            st.header(f"📅 Resoconto {nome_mese}")
            
            # Metriche Conti
            cols_m = st.columns(len(saldi_attuali))
            for idx, m in enumerate(saldi_attuali):
                cols_m[idx].metric(m, f"{saldi_attuali[m]:.2f}€")
            
            st.divider()
            
            df_m = st.session_state.db[st.session_state.db["Mese_Num"] == (i + 1)]
            
            if not df_m.empty:
                col_tab, col_graph = st.columns([1.5, 1])
                with col_tab:
                    st.subheader("Lista Movimenti")
                    st.dataframe(df_m[["Data", "Tipo", "Macro", "Sub", "Importo", "Metodo", "Descrizione"]], use_container_width=True)
                
                with col_graph:
                    st.subheader("Ripartizione Spese")
                    df_u = df_m[df_m["Tipo"] == "Uscite"]
                    if not df_u.empty:
                        fig_pie = px.pie(df_u, values='Importo', names='Macro', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
                        st.plotly_chart(fig_pie, use_container_width=True)
            else: st.info("Nessun movimento registrato per questo mese.")

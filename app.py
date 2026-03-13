import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="Personal Finance Pro", layout="wide")

# CSS per rendere l'interfaccia più "App-like"
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 10px 10px 0 0; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(worksheet=worksheet, ttl="0s")

# --- DEFINIZIONE CATEGORIE E ACCUMULI ---
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

ACCUMULO_LIST = [
    "Fondo Pensione", "Arredamento", "Condominio", "Dazn", "Energia", "Manutenzione", 
    "Fondo Casa", "Baby Sitter/Asilo", "Accumulo Aurora", "RCA", "Bollo", 
    "Fondo Macchina", "Pneumatici", "Tagliando", "Telepass", "Regali Eventi", 
    "Regali Laura", "Shopping", "Vacanze", "Adozione/Beneficienza", "Fantacalcio", "Dispositivi"
]

# --- SIDEBAR: REGISTRAZIONE ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/10006/10006326.png", width=80)
st.sidebar.header("Nuova Operazione")

with st.sidebar.form("form_inserimento", clear_on_submit=True):
    tipo = st.selectbox("Tipo", ["Uscite", "Entrate", "Giroconto", "Anticipo", "Rimborso"])
    data = st.date_input("Data", datetime.now())
    
    # Caricamento metodi dinamico
    try:
        df_s = load_data("Saldi")
        metodi = df_s["Metodo"].tolist()
    except:
        metodi = ["BNL", "BPM", "Contanti", "Revolut"]

    if tipo == "Giroconto":
        macro, sub = "Trasferimento", "Giroconto"
        m_da = st.selectbox("Da (Origine)", metodi)
        m_a = st.selectbox("A (Destinazione)", metodi)
    else:
        tipo_cat = "Entrate" if tipo in ["Entrate", "Rimborso"] else "Uscite"
        macro = st.selectbox("Macro-categoria", list(CATEGORIES[tipo_cat].keys()))
        sub = st.selectbox("Sotto-categoria", CATEGORIES[tipo_cat][macro])
        m_da = st.selectbox("Metodo di Pagamento", metodi)
        m_a = ""

    importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
    desc = st.text_input("Nota/Descrizione")
    
    if st.form_submit_button("REGISTRA"):
        df_t = load_data("Transazioni")
        is_acc = "Sì" if sub in ACCUMULO_LIST else "No"
        new_row = pd.DataFrame([{"Data": str(data), "Mese_Num": int(data.month), "Tipo": tipo, "Macro": macro, "Sub": sub, 
                                 "Descrizione": desc, "Metodo": m_da, "Importo": importo, "Accumulo": is_acc, "Controparte": m_a}])
        conn.update(worksheet="Transazioni", data=pd.concat([df_t, new_row], ignore_index=True))
        st.sidebar.success("Sincronizzato!")
        st.rerun()

# --- MAIN PAGE: TABS ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre", "ANNUALE", "CONFIG"]
tabs = st.tabs(mesi)

# Caricamento dati una sola volta per tutte le tab
df_all = load_data("Transazioni")
df_saldi = load_data("Saldi")

for i, nome_mese in enumerate(mesi):
    with tabs[i]:
        if nome_mese == "CONFIG":
            st.header("⚙️ Configurazione Metodi")
            ed = st.data_editor(df_saldi, num_rows="dynamic", use_container_width=True)
            if st.button("Salva Conti"):
                conn.update(worksheet="Saldi", data=ed)
                st.rerun()

        elif nome_mese == "ANNUALE":
            st.header("📊 Dashboard Annuale")
            if not df_all.empty:
                col1, col2 = st.columns([2, 1])
                with col1:
                    fig = px.bar(df_all[df_all["Tipo"].isin(["Uscite", "Entrate"])], 
                                 x="Mese_Num", y="Importo", color="Tipo", barmode="group",
                                 title="Andamento Entrate/Uscite", color_discrete_map={"Uscite":"#e74c3c","Entrate":"#2ecc71"})
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.subheader("💰 Fondi Accumulo")
                    # Qui sommiamo tutte le sottocategorie marcate come "Accumulo"
                    acc_summary = df_all[df_all["Accumulo"] == "Sì"].groupby("Sub")["Importo"].sum().reset_index()
                    st.dataframe(acc_summary, use_container_width=True, hide_index=True)

        else:
            # DASHBOARD MENSILE
            st.header(f"📅 Situazione {nome_mese}")
            
            # Calcolo Saldi Attuali per il mese (UX: Mattonelle dinamiche)
            st.subheader("🏦 Saldi Strumenti")
            m_cols = st.columns(len(df_saldi))
            for idx, row in df_saldi.iterrows():
                m_nome = row["Metodo"]
                # Calcolo semplificato per UX
                ent = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Entrate")]["Importo"].sum()
                usc = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Uscite")]["Importo"].sum()
                bal = row["Saldo_Iniziale"] + ent - usc
                m_cols[idx % 4].metric(m_nome, f"{bal:.2f} €")

            st.divider()

            df_m = df_all[df_all["Mese_Num"].astype(int) == (i + 1)]
            if not df_m.empty:
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.subheader("Movimenti")
                    st.dataframe(df_m[["Data", "Tipo", "Macro", "Sub", "Importo", "Metodo"]], use_container_width=True, hide_index=True)
                with c2:
                    st.subheader("Spese per Categoria")
                    fig_p = px.pie(df_m[df_m["Tipo"] == "Uscite"], values='Importo', names='Macro', hole=0.5)
                    st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info(f"Nessuna operazione registrata a {nome_mese}")

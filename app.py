import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Finance Manager Pro", layout="wide", initial_sidebar_state="expanded")

# --- CATEGORIE E SOTTOCATEGORIE (Standardizzate) ---
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

COLONNE = ["Data", "Mese_Num", "Tipo", "Macro", "Sub", "Descrizione", "Metodo", "Importo", "Accumulo", "Controparte"]

# --- INIZIALIZZAZIONE ---
if 'db' not in st.session_state or not isinstance(st.session_state.db, pd.DataFrame):
    st.session_state.db = pd.DataFrame(columns=COLONNE)

if 'saldi_iniziali' not in st.session_state:
    st.session_state.saldi_iniziali = {m: 0.0 for m in ["BNL", "BPM", "Buoni Pasto", "Contanti", "Conto Gioco", "Illimity", "Paypal", "Revolut", "Satispay"]}

# --- LOGICA CALCOLI ---
def calcola_saldi():
    df = st.session_state.db
    saldi = st.session_state.saldi_iniziali.copy()
    if not df.empty:
        for m in saldi:
            ent = df[(df["Metodo"] == m) & (df["Tipo"] == "Entrate")]["Importo"].sum()
            rim = df[(df["Metodo"] == m) & (df["Tipo"] == "Rimborso")]["Importo"].sum()
            usc = df[(df["Metodo"] == m) & (df["Tipo"] == "Uscite")]["Importo"].sum()
            ant = df[(df["Metodo"] == m) & (df["Tipo"] == "Anticipo")]["Importo"].sum()
            g_u = df[(df["Metodo"] == m) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
            g_e = df[(df["Controparte"] == m) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
            saldi[m] += (ent + rim + g_e - usc - ant - g_u)
    return saldi

# --- SIDEBAR ---
st.sidebar.title("💰 Inserimento Dati")
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
        metodo = st.selectbox("Metodo", list(st.session_state.saldi_iniziali.keys()))
        controparte = None

    importo = st.number_input("Importo (€)", min_value=0.0, step=0.01)
    desc = st.text_input("Descrizione")
    
    if st.form_submit_button("REGISTRA"):
        is_acc = "Sì" if sub in ACCUMULO_SUBS else "No"
        new_row = pd.DataFrame([{"Data": pd.to_datetime(data), "Mese_Num": data.month, "Tipo": tipo, "Macro": macro, "Sub": sub, 
                                 "Descrizione": desc, "Metodo": metodo, "Importo": importo, "Accumulo": is_acc, "Controparte": controparte}])
        st.session_state.db = pd.concat([st.session_state.db, new_row], ignore_index=True)
        st.rerun()

# --- INTERFACCIA TABS ---
mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre", "ANNUALE", "CONFIG"]
tabs = st.tabs(mesi_nomi)

saldi_attuali = calcola_saldi()

for i, nome in enumerate(mesi_nomi):
    with tabs[i]:
        if nome == "CONFIG":
            st.header("⚙️ Saldi Iniziali al 1° Gennaio")
            cols = st.columns(3)
            for idx, m in enumerate(st.session_state.saldi_iniziali):
                st.session_state.saldi_iniziali[m] = cols[idx%3].number_input(f"Saldo iniziale {m}", value=float(st.session_state.saldi_iniziali[m]))

        elif nome == "ANNUALE":
            st.header("📈 Analisi Annuale Totale")
            df_a = st.session_state.db
            if not df_a.empty:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_a = px.bar(df_a[df_a["Tipo"].isin(["Uscite", "Entrate"])], x="Mese_Num", y="Importo", color="Tipo", barmode="group", title="Entrate vs Uscite Annuali")
                    st.plotly_chart(fig_a, use_container_width=True)
                with col_g2:
                    st.subheader("Accumuli Totali")
                    df_acc = df_a[df_a["Accumulo"] == "Sì"].groupby("Sub")["Importo"].sum().reset_index()
                    st.dataframe(df_acc, hide_index=True, use_container_width=True)
            else: st.info("Inserisci dati per visualizzare l'analisi.")

        else:
            # DASHBOARD MENSILE
            st.header(f"📅 Riepilogo {nome}")
            
            # Mattonelle Saldi
            st.subheader("Saldi Correnti")
            cols_m = st.columns(len(saldi_attuali))
            for idx, m in enumerate(saldi_attuali):
                cols_m[idx].metric(label=m, value=f"{saldi_attuali[m]:.2f} €")
            
            st.divider()
            
            df_m = st.session_state.db[st.session_state.db["Mese_Num"] == (i + 1)]
            if not df_m.empty:
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.subheader("Lista Movimenti")
                    st.dataframe(df_m[["Data", "Tipo", "Macro", "Sub", "Importo", "Metodo", "Descrizione"]], use_container_width=True, hide_index=True)
                with c2:
                    st.subheader("Ripartizione Spese")
                    df_u = df_m[df_m["Tipo"] == "Uscite"]
                    if not df_u.empty:
                        fig_p = px.pie(df_u, values='Importo', names='Macro', hole=0.4)
                        st.plotly_chart(fig_p, use_container_width=True)
                    else: st.info("Nessuna uscita registrata.")
            else: st.info("Ancora nessun dato per questo mese.")

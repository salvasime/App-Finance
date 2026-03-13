import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Finance Manager Pro", layout="wide", initial_sidebar_state="expanded")

# --- STRUTTURA DATI (Categorie e Sottocategorie) ---
CATEGORIES = {
    "Uscite": {
        "Allianz": ["Fondo pensione", "malattia", "caso morte"],
        "Casa": ["Arredamento", "assicurazione", "Condominio", "Dazn", "Sky", "Energia", "Internet", "Manutenzione", "Mutuo", "Pulizia", "Fondo Casa", "Tari", "Altro"],
        "Food": ["Aperitivo", "caffè", "cena", "varie", "colazione", "pranzo", "prozis", "spesa"],
        "Aurora": ["visite", "farmacia", "accessori", "cibo", "Asilo", "Baby Sitter", "Accumulo Aurora", "Altro"],
        "Macchina e Trasporti": ["RCA", "Benzina", "Bollo", "Fondo Macchina", "Lavaggio", "Manutenzione", "Parcheggio", "Pneumatici", "Tagliando", "Telepass", "Trasporti città", "Treno", "Altro"],
        "Regali e Offerte": ["Regali eventi", "regali amici/colleghi", "regali famiglia", "regali laura", "Offerte amici/colleghi", "offerte laura", "offerte varie"],
        "Salute e Benessere": ["Farmacia", "Parrucchiere", "Visite Mediche", "extra"],
        "Tempo Libero": ["Shopping", "Eventi", "Palestra", "Altri sport", "Mare/Piscina", "Spa", "Vacanze", "Altro"],
        "Varie": ["Adozione/Beneficienza", "Multe/Tributi", "spese conto corrente", "fantacalcio", "Elettronica accessori", "Dispositivi", "Ricarica telefonica", "bet", "uscite varie"]
    },
    "Entrate": {
        "Lavoro": ["Stipendio", "Bonus", "Premio"],
        "Extra": ["Regali", "Rimborsi", "Vendite"]
    }
}

# Sottocategorie che devono alimentare un fondo di accumulo
ACCUMULO_SUBS = [
    "Fondo pensione", "Arredamento", "Condominio", "Dazn", "Energia", "Manutenzione", 
    "Fondo casa", "Baby sitter/Asilo", "Accumulo Aurora", "RCA", "Bollo", 
    "Fondo Macchina", "Pneumatici", "Tagliando", "Telepass", "Regali eventi", 
    "Regali laura", "Shopping", "Vacanze", "Adozione/Beneficienza", "Fantacalcio", "Dispositivi"
]

# --- INIZIALIZZAZIONE STATO ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["Data", "Mese", "Tipo", "Macro", "Sub", "Descrizione", "Metodo", "Importo", "Accumulo", "Controparte"])

if 'saldi_iniziali' not in st.session_state:
    st.session_state.saldi_iniziali = {
        "BNL": 0.0, "BPM": 0.0, "Buoni Pasto": 0.0, "Contanti": 0.0, 
        "Conto gioco": 0.0, "Illimity": 0.0, "Paypal": 0.0, "Revolut": 0.0, "Satispay": 0.0
    }

# --- FUNZIONI DI CALCOLO ---
def get_saldo_attuale(metodo):
    iniziale = st.session_state.saldi_iniziali.get(metodo, 0.0)
    df = st.session_state.db
    entrate = df[(df["Metodo"] == metodo) & (df["Tipo"] == "Entrate")]["Importo"].sum()
    uscite = df[(df["Metodo"] == metodo) & (df["Tipo"] == "Uscite")]["Importo"].sum()
    # Giroconti: se metodo è origine (Uscita) o destinazione (Entrata)
    giro_uscita = df[(df["Metodo"] == metodo) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
    giro_entrata = df[(df["Controparte"] == metodo) & (df["Tipo"] == "Giroconto")]["Importo"].sum()
    return iniziale + entrate + giro_entrata - uscite - giro_uscita

# --- SIDEBAR: INSERIMENTO OPERAZIONI ---
st.sidebar.header("➕ Nuova Operazione")
with st.sidebar.form("form_op", clear_on_submit=True):
    f_tipo = st.selectbox("Tipo Operazione", ["Uscite", "Entrate", "Giroconto", "Anticipo", "Rimborso"])
    f_data = st.date_input("Data", datetime.now())
    
    # Logica Dinamica Categorie
    if f_tipo == "Giroconto":
        f_macro, f_sub = "Trasferimento", "Giroconto"
        f_metodo = st.selectbox("Da (Origine)", list(st.session_state.saldi_iniziali.keys()))
        f_controparte = st.selectbox("A (Destinazione)", list(st.session_state.saldi_iniziali.keys()))
    else:
        tipo_cat = "Entrate" if f_tipo in ["Entrate", "Rimborso"] else "Uscite"
        f_macro = st.selectbox("Macro-categoria", list(CATEGORIES[tipo_cat].keys()))
        f_sub = st.selectbox("Sotto-categoria", CATEGORIES[tipo_cat][f_macro])
        f_metodo = st.selectbox("Metodo di Pagamento", list(st.session_state.saldi_iniziali.keys()))
        f_controparte = None

    f_importo = st.number_input("Importo (€)", min_value=0.0, step=0.01, format="%.2f")
    f_desc = st.text_input("Descrizione / Note")
    
    if st.form_submit_button("Registra"):
        is_acc = "Sì" if f_sub in ACCUMULO_SUBS else "No"
        nuova_riga = {
            "Data": pd.to_datetime(f_data), "Mese": f_data.month, "Tipo": f_tipo, 
            "Macro": f_macro, "Sub": f_sub, "Descrizione": f_desc, 
            "Metodo": f_metodo, "Importo": f_importo, "Accumulo": is_acc, "Controparte": f_controparte
        }
        st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nuova_riga])], ignore_index=True)
        st.sidebar.success("Operazione salvata!")

# --- LAYOUT PRINCIPALE: TABS ---
mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
             "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre", "ANNUALE", "SETTAGGI"]
tabs = st.tabs(mesi_nomi)

for i, nome_tab in enumerate(mesi_nomi):
    with tabs[i]:
        if nome_tab == "SETTAGGI":
            st.header("⚙️ Configurazione Iniziale")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.subheader("Saldi al 1° Gennaio")
                for m in st.session_state.saldi_iniziali:
                    st.session_state.saldi_iniziali[m] = st.number_input(f"Saldo {m}", value=st.session_state.saldi_iniziali[m], key=f"init_{m}")
            
        elif nome_tab == "ANNUALE":
            st.header("📊 Analisi Annuale")
            df_annuo = st.session_state.db
            if not df_annuo.empty:
                c1, c2 = st.columns([2, 1])
                with c1:
                    fig = px.bar(df_annuo[df_annuo["Tipo"].isin(["Uscite", "Entrate"])], 
                                 x="Mese", y="Importo", color="Tipo", barmode="group", title="Entrate vs Uscite")
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.subheader("Stato Fondi Accumulo")
                    acc_df = df_annuo[df_annuo["Accumulo"] == "Sì"].groupby("Sub")["Importo"].sum().reset_index()
                    st.table(acc_df)
            else: st.info("Nessun dato registrato.")

        else:
            # DASHBOARD MENSILE (1-12)
            st.header(f"Riepilogo {nome_tab}")
            
            # Row 1: Saldi Metodi Pagamento
            st.subheader("🏦 I tuoi conti (Saldo Attuale)")
            cols_m = st.columns(len(st.session_state.saldi_iniziali))
            for idx, m in enumerate(st.session_state.saldi_iniziali.keys()):
                saldo = get_saldo_attuale(m)
                cols_m[idx % 9].metric(m, f"{saldo:.2f} €")
            
            st.divider()
            
            # Row 2: Dati del mese
            df_m = st.session_state.db[st.session_state.db["Mese"] == (i + 1)]
            col_sx, col_dx = st.columns([2, 1])
            
            with col_sx:
                st.subheader("Movimenti Dettagliati")
                st.dataframe(df_m.drop(columns=["Mese"]), use_container_width=True)
            
            with col_dx:
                st.subheader("Analisi Spese")
                df_u = df_m[df_m["Tipo"] == "Uscite"]
                if not df_u.empty:
                    fig_pie = px.pie(df_u, values='Importo', names='Macro', hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.write("Nessuna uscita questo mese.")

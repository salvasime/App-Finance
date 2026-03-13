import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Finance Manager Pro", layout="wide", initial_sidebar_state="expanded")

# --- STILE UX ---
st.markdown("""
    <style>
    .stMetric { border: 1px solid #464b5d; padding: 10px; border-radius: 10px; }
    .stDataFrame { border: 1px solid #464b5d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    # Carica i dati senza cache (ttl=0) per vedere subito le modifiche
    return conn.read(worksheet=sheet_name, ttl="0s")

# --- DEFINIZIONE CATEGORIE ---
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

# Sottocategorie dedicate all'accumulo
ACCUMULO_LIST = [
    "Fondo Pensione", "Arredamento", "Condominio", "Dazn", "Energia", "Manutenzione", 
    "Fondo Casa", "Baby Sitter/Asilo", "Accumulo Aurora", "RCA", "Bollo", 
    "Fondo Macchina", "Pneumatici", "Tagliando", "Telepass", "Regali Eventi", 
    "Regali Laura", "Shopping", "Vacanze", "Adozione/Beneficienza", "Fantacalcio", "Dispositivi"
]

# --- SIDEBAR: REGISTRAZIONE ---
st.sidebar.title("💳 Operazioni")
with st.sidebar.form("form_inserimento", clear_on_submit=True):
    tipo = st.selectbox("Tipo", ["Uscite", "Entrate", "Giroconto", "Anticipo", "Rimborso"])
    data = st.date_input("Data", datetime.now())
    
    # Caricamento dinamico metodi da Google Sheets
    try:
        df_s = load_data("Saldi")
        metodi = df_s["Metodo"].unique().tolist()
    except:
        metodi = ["Configura in Tab CONFIG"]

    if tipo == "Giroconto":
        macro, sub = "Trasferimento", "Giroconto"
        m_da = st.selectbox("Da (Origine)", metodi)
        m_a = st.selectbox("A (Destinazione)", metodi)
    else:
        tipo_cat = "Entrate" if tipo in ["Entrate", "Rimborso"] else "Uscite"
        macro = st.selectbox("Macro-categoria", list(CATEGORIES[tipo_cat].keys()))
        sub = st.selectbox("Sotto-categoria", CATEGORIES[tipo_cat][macro])
        m_da = st.selectbox("Metodo", metodi)
        m_a = ""

    importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
    desc = st.text_input("Descrizione")
    
    if st.form_submit_button("REGISTRA MOVIMENTO"):
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

# Caricamento Database
df_all = load_data("Transazioni")
df_saldi_init = load_data("Saldi")

for i, nome_mese in enumerate(mesi):
    with tabs[i]:
        if nome_mese == "CONFIG":
            st.header("⚙️ Configurazione Metodi e Saldi Iniziali")
            st.info("Aggiungi qui i tuoi conti e il saldo che avevano al 1° Gennaio.")
            ed = st.data_editor(df_saldi_init, num_rows="dynamic", use_container_width=True)
            if st.button("Salva Configurazione"):
                conn.update(worksheet="Saldi", data=ed)
                st.success("Conti aggiornati!")
                st.rerun()

        elif nome_mese == "ANNUALE":
            st.header("📊 Analisi Annuale e Accumuli")
            if not df_all.empty:
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Grafico Entrate/Uscite
                    df_filtered = df_all[df_all["Tipo"].isin(["Uscite", "Entrate"])]
                    fig = px.bar(df_filtered, x="Mese_Num", y="Importo", color="Tipo", barmode="group",
                                 title="Trend Mensile", color_discrete_map={"Uscite":"#EF553B","Entrate":"#00CC96"})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # RIEPILOGO ACCUMULI
                    st.subheader("💰 Fondi di Accumulo")
                    st.write("Somma totale accantonata per sottocategoria:")
                    df_acc = df_all[df_all["Accumulo"] == "Sì"].groupby("Sub")["Importo"].sum().reset_index()
                    st.dataframe(df_acc, use_container_width=True, hide_index=True)
            else:
                st.info("Nessun dato disponibile per l'analisi annuale.")

        else:
            # DASHBOARD MENSILE (Gen-Dic)
            st.header(f"📅 Situazione di {nome_mese}")
            
            # Calcolo Saldi Metodi (Saldo Iniziale + Entrate - Uscite)
            st.subheader("🏦 Saldo Attuale Conti")
            m_cols = st.columns(len(df_saldi_init))
            for idx, row in df_saldi_init.iterrows():
                m_nome = row["Metodo"]
                s_init = row["Saldo_Iniziale"]
                
                # Calcolo entrate e uscite totali su quel metodo da inizio anno
                ent = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Entrate")]["Importo"].sum()
                rim = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Rimborso")]["Importo"].sum()
                usc = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Uscite")]["Importo"].sum()
                ant = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Anticipo")]["Importo"].sum()
                
                # Giroconti
                g_usc = df_all[(df_all["Metodo"] == m_nome) & (df_all["Tipo"] == "Giroconto")]["Importo"].sum()
                g_ent = df_all[(df_all["Controparte"] == m_nome) & (df_all["Tipo"] == "Giroconto")]["Importo"].sum()
                
                saldo_attuale = s_init + ent + rim + g_ent - usc - ant - g_usc
                m_cols[idx % 4].metric(m_nome, f"{saldo_attuale:.2f} €")

            st.divider()

            # Filtro dati del mese
            df_m = df_all[df_all["Mese_Num"].astype(int) == (i + 1)]
            
            if not df_m.empty:
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.subheader("Dettaglio Movimenti")
                    st.dataframe(df_m[["Data", "Tipo", "Macro", "Sub", "Importo", "Metodo", "Descrizione"]], 
                                 use_container_width=True, hide_index=True)
                with c2:
                    st.subheader("Distribuzione Spese")
                    df_u = df_m[df_m["Tipo"] == "Uscite"]
                    if not df_u.empty:
                        fig_p = px.pie(df_u, values='Importo', names='Macro', hole=0.5, 
                                       color_discrete_sequence=px.colors.qualitative.Safe)
                        st.plotly_chart(fig_p, use_container_width=True)
                    else:
                        st.write("Nessuna uscita registrata.")
            else:
                st.info(f"Non ci sono ancora movimenti registrati per {nome_mese}.")

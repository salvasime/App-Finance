import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Finance Pro", layout="wide")

# Connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONI DI SERVIZIO ---
def load_data():
    try:
        return conn.read(worksheet="Transazioni")
    except:
        return pd.DataFrame(columns=["Data", "Mese", "Tipo", "Macro", "Sub", "Desc", "Metodo", "Importo", "Accumulo"])

def save_data(df):
    conn.update(worksheet="Transazioni", data=df)

# --- INTERFACCIA ---
st.title("💰 Gestione Finanze Personali")

menu = st.sidebar.radio("Naviga", ["Dashboard Mensile", "Inserimento Operazione", "Configurazione"])

# Nota: Per brevità ho semplificato, ma qui andrebbe la logica dei mesi e delle categorie
if menu == "Inserimento Operazione":
    st.subheader("Nuova Scrittura")
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        tipo = col1.selectbox("Tipo", ["Uscita", "Entrata", "Giroconto", "Rimborso"])
        data = col2.date_input("Data", datetime.now())
        importo = col1.number_input("Importo €", min_value=0.0)
        desc = col2.text_input("Descrizione")
        # In un'app reale qui caricheresti le categorie dal foglio Config
        submit = st.form_submit_button("Salva nel Cloud")
        
        if submit:
            df = load_data()
            new_row = pd.DataFrame([[data, data.strftime("%B"), tipo, "Macro", "Sub", desc, "Banca", importo, "No"]], 
                                   columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("Dato salvato su Google Sheets!")

elif menu == "Dashboard Mensile":
    st.info("Qui vedrai i grafici presi dai dati salvati.")
    df = load_data()
    if not df.empty:
        st.dataframe(df)
        fig = px.bar(df, x="Mese", y="Importo", color="Tipo")
        st.plotly_chart(fig)

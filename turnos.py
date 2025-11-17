import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect("pos_cremeria.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado TEXT NOT NULL,
    turno INTEGER NOT NULL,
    timestamp TEXT NOT NULL
)
''')
conn.commit()

def obtener_siguiente_turno():
    cursor.execute("SELECT MAX(turno) FROM turnos")
    resultado = cursor.fetchone()[0]
    return 1 if resultado is None else resultado + 1

def mostrar():
    st.title("👩‍💼 Panel de Turnos - Atención al Cliente")

    empleados = ["Ana", "Luis", "Carlos", "Marta"]
    empleado = st.selectbox("Seleccione un empleado para ser atendido:", empleados)

    if st.button("Solicitar Turno"):
        turno = obtener_siguiente_turno()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO turnos (empleado, turno, timestamp) VALUES (?, ?, ?)", (empleado, turno, timestamp))
        conn.commit()
        st.success(f"Su turno es el número {turno}. Espere a ser llamado por {empleado}.")

    st.subheader("📋 Últimos turnos generados")
    turnos = pd.read_sql_query("SELECT * FROM turnos ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(turnos)

    if st.checkbox("Modo Display"):
        st.markdown("## Turno Actual")
        ultimo = turnos.iloc[0] if not turnos.empty else None
        if ultimo is not None:
            st.markdown(f"### Turno {ultimo['turno']} - {ultimo['empleado']}")
        else:
            st.markdown("### No hay turnos aún")
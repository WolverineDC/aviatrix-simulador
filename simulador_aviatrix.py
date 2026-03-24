import streamlit as st
import random
import time
import math
import pandas as pd
import altair as alt
import json
import os

# Configuración de la página
st.set_page_config(page_title="Aviatrix Pro", page_icon="✈️")

# --- NUEVO: SISTEMA DE GUARDADO DE SALDO (BILLETERA VIRTUAL) ---
ARCHIVO_BILLETERA = "billetera.json"

def cargar_saldo():
    """Lee el saldo guardado. Si no existe el archivo, entrega 1000."""
    if os.path.exists(ARCHIVO_BILLETERA):
        try:
            with open(ARCHIVO_BILLETERA, "r") as f:
                datos = json.load(f)
                return float(datos.get("saldo", 1000.0))
        except:
            return 1000.0
    return 1000.0

def guardar_saldo(monto):
    """Guarda el saldo actual en el archivo para la próxima vez."""
    with open(ARCHIVO_BILLETERA, "w") as f:
        json.dump({"saldo": monto}, f)

# --- 1. INICIALIZACIÓN DE VARIABLES GLOBALES ---
if 'saldo' not in st.session_state:
    st.session_state.saldo = cargar_saldo() # Ahora lee desde el archivo
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'historial_saldo' not in st.session_state:
    st.session_state.historial_saldo = [st.session_state.saldo]

# --- 2. MÁQUINA DE ESTADOS DEL JUEGO ---
if 'estado_juego' not in st.session_state:
    st.session_state.estado_juego = 'COUNTDOWN'
    st.session_state.target_time = time.time() + 10.0 
    
    st.session_state.multiplicador_final = 1.0
    st.session_state.inicio_vuelo_time = 0.0
    
    st.session_state.apostado = False
    st.session_state.cobrado = False
    st.session_state.apuesta_actual = 0.0
    st.session_state.ganancia_ronda = 0.0
    st.session_state.multiplicador_cobro = 0.0
    st.session_state.auto_retiro_activado = False
    st.session_state.retiro_objetivo = 2.00

def generar_multiplicador():
    r = random.random()
    if r < 0.01: return 1.00
    return min(round(0.99 / (1 - r), 2), 300.0)

# --- 3. INTERFAZ SUPERIOR ---
st.title("✈️ Aviatrix: Modo Tiempo Real")
st.header(f"💰 Saldo: {st.session_state.saldo:.2f} monedas")

bloquear_controles = st.session_state.apostado or st.session_state.estado_juego != 'COUNTDOWN'

col1, col2, col3 = st.columns(3)
with col1:
    apuesta_input = st.number_input("Monto a apostar:", min_value=1.0, value=10.0, step=1.0, disabled=bloquear_controles)
with col2:
    st.write("") 
    auto_retiro = st.checkbox("Activar Retiro Automático", value=False, disabled=bloquear_controles)
with col3:
    retiro_objetivo = st.number_input("Retirar en (x):", min_value=1.01, value=2.00, step=0.1, disabled=not auto_retiro or bloquear_controles)

st.markdown("---")

# --- 4. BOTÓN DINÁMICO ---
zona_boton = st.empty()

with zona_boton.container():
    if st.session_state.estado_juego == 'COUNTDOWN':
        if not st.session_state.apostado:
            if st.button("✅ APOSTAR PARA LA PRÓXIMA RONDA", use_container_width=True, type="primary"):
                if apuesta_input > st.session_state.saldo:
                    st.error("⚠️ Saldo insuficiente")
                else:
                    st.session_state.apostado = True
                    st.session_state.apuesta_actual = apuesta_input
                    
                    # Descontar apuesta y GUARDAR EN LA BILLETERA
                    st.session_state.saldo -= apuesta_input
                    guardar_saldo(st.session_state.saldo)
                    
                    st.session_state.auto_retiro_activado = auto_retiro
                    st.session_state.retiro_objetivo = retiro_objetivo
                    st.rerun() 
        else:
            st.button("⏳ APUESTA REGISTRADA (Esperando despegue...)", disabled=True, use_container_width=True)

    elif st.session_state.estado_juego == 'VOLANDO':
        if st.session_state.apostado and not st.session_state.cobrado:
            if st.button("💰 COBRAR AHORA", use_container_width=True, type="primary"):
                elapsed = time.time() - st.session_state.inicio_vuelo_time
                m_cobro = math.exp(0.08 * elapsed)
                m_cobro = min(m_cobro, st.session_state.multiplicador_final) 
                
                st.session_state.cobrado = True
                st.session_state.multiplicador_cobro = m_cobro
                ganancia = st.session_state.apuesta_actual * m_cobro
                
                # Sumar ganancia y GUARDAR EN LA BILLETERA
                st.session_state.saldo += ganancia
                guardar_saldo(st.session_state.saldo)
                
                st.session_state.ganancia_ronda = ganancia
                st.rerun()
        elif st.session_state.apostado and st.session_state.cobrado:
            st.button(f"✅ RETIRO EXITOSO EN {st.session_state.multiplicador_cobro:.2f}x (+{st.session_state.ganancia_ronda:.2f})", disabled=True, use_container_width=True)
        else:
            st.button("✈️ VUELO EN CURSO (No participas en esta ronda)", disabled=True, use_container_width=True)
            
    elif st.session_state.estado_juego == 'EXPLOSION':
        st.button("💥 ESTALLÓ", disabled=True, use_container_width=True)

# --- 5. PANTALLAS DE ANIMACIÓN ---
pantalla_mensaje = st.empty()
pantalla_grafico = st.empty()

st.markdown("---")

# --- 6. SECCIÓN DE HISTORIAL ---
col_historial, col_saldo = st.columns([1, 1])

with col_historial:
    if st.session_state.historial:
        st.subheader("📊 Últimos Vuelos")
        ultimos_vuelos = st.session_state.historial[-12:]
        cols = st.columns(4)
        for i, mult in enumerate(ultimos_vuelos):
            color = "#28a745" if mult >= 2.0 else "#dc3545" 
            cols[i % 4].markdown(
                f"<div style='background-color: {color}; color: white; padding: 5px; margin-bottom: 5px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 14px;'>"
                f"{mult:.2f}x</div>", 
                unsafe_allow_html=True
            )

with col_saldo:
    if len(st.session_state.historial_saldo) > 1:
        st.subheader("📈 Evolución de tu Saldo")
        df_saldo = pd.DataFrame({'Ronda': range(len(st.session_state.historial_saldo)), 'Saldo': st.session_state.historial_saldo})
        grafico_saldo = alt.Chart(df_saldo).mark_line(color='#ff7f0e', strokeWidth=3).encode(
            x=alt.X('Ronda', axis=alt.Axis(tickMinStep=1)),
            y=alt.Y('Saldo', scale=alt.Scale(zero=False))
        ).properties(height=200)
        st.altair_chart(grafico_saldo, use_container_width=True)

# --- 7. LÓGICA DE TIEMPO REAL ---
if st.session_state.estado_juego == 'COUNTDOWN':
    while time.time() < st.session_state.target_time:
        faltan = st.session_state.target_time - time.time()
        pantalla_mensaje.markdown(f"<h1 style='text-align: center; color: orange;'>Próximo vuelo en: {faltan:.1f} s</h1>", unsafe_allow_html=True)
        time.sleep(0.1) 
        
    st.session_state.estado_juego = 'VOLANDO'
    st.session_state.multiplicador_final = generar_multiplicador()
    st.session_state.inicio_vuelo_time = time.time()
    st.rerun()

elif st.session_state.estado_juego == 'VOLANDO':
    while True:
        elapsed = time.time() - st.session_state.inicio_vuelo_time
        m = math.exp(0.08 * elapsed) 
        
        if m >= st.session_state.multiplicador_final:
            st.session_state.estado_juego = 'EXPLOSION'
            st.rerun()
            
        if st.session_state.apostado and not st.session_state.cobrado and st.session_state.auto_retiro_activado:
            if m >= st.session_state.retiro_objetivo:
                st.session_state.cobrado = True
                st.session_state.multiplicador_cobro = st.session_state.retiro_objetivo
                ganancia = st.session_state.apuesta_actual * st.session_state.retiro_objetivo
                
                # Sumar ganancia de auto-retiro y GUARDAR EN LA BILLETERA
                st.session_state.saldo += ganancia
                guardar_saldo(st.session_state.saldo)
                
                st.session_state.ganancia_ronda = ganancia
                st.rerun()
        
        pantalla_mensaje.markdown(f"<h1 style='text-align: center; color: #1f77b4;'>✈️ {m:.2f}x</h1>", unsafe_allow_html=True)
        
        puntos = int(elapsed * 10) 
        datos_grafico = [{'tiempo': t/10.0, 'multiplicador': math.exp(0.08 * (t/10.0))} for t in range(puntos + 1)]
        df = pd.DataFrame(datos_grafico)
        
        if not df.empty:
            linea = alt.Chart(df).mark_line(color='#1f77b4', strokeWidth=4).encode(
                x=alt.X('tiempo', axis=alt.Axis(labels=False, ticks=False, title='')),
                y=alt.Y('multiplicador', scale=alt.Scale(domain=[1, max(2.5, st.session_state.multiplicador_final)]), axis=alt.Axis(title='Multiplicador'))
            )
            avion = alt.Chart(df.tail(1)).mark_circle(color='red', size=200).encode(x='tiempo', y='multiplicador')
            pantalla_grafico.altair_chart((linea + avion).properties(height=300), use_container_width=True)
            
        time.sleep(0.1)

elif st.session_state.estado_juego == 'EXPLOSION':
    pantalla_mensaje.markdown(f"<h1 style='text-align: center; color: red;'>💥 ESTALLÓ EN {st.session_state.multiplicador_final:.2f}x 💥</h1>", unsafe_allow_html=True)
    
    st.session_state.historial.append(st.session_state.multiplicador_final)
    st.session_state.historial_saldo.append(st.session_state.saldo)
    
    puntos = max(int((math.log(st.session_state.multiplicador_final) / 0.08) * 10), 1)
    datos_grafico = [{'tiempo': t/10.0, 'multiplicador': math.exp(0.08 * (t/10.0))} for t in range(puntos + 1)]
    df = pd.DataFrame(datos_grafico)
    linea = alt.Chart(df).mark_line(color='red', strokeWidth=4).encode(x=alt.X('tiempo', axis=alt.Axis(labels=False, ticks=False, title='')), y=alt.Y('multiplicador', scale=alt.Scale(domain=[1, max(2.5, st.session_state.multiplicador_final)])))
    explosion = alt.Chart(df.tail(1)).mark_point(color='red', size=500, shape='cross').encode(x='tiempo', y='multiplicador')
    pantalla_grafico.altair_chart((linea + explosion).properties(height=300), use_container_width=True)
    
    time.sleep(3.5)
    
    st.session_state.estado_juego = 'COUNTDOWN'
    st.session_state.target_time = time.time() + 10.0
    st.session_state.apostado = False
    st.session_state.cobrado = False
    st.session_state.ganancia_ronda = 0.0
    st.session_state.multiplicador_final = 1.0 
    
    st.rerun()

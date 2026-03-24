import streamlit as st
import random
import time
import math
import pandas as pd
import altair as alt

# Configuración de la página
st.set_page_config(page_title="Aviatrix Pro", page_icon="✈️")

# --- 1. INICIALIZACIÓN DE VARIABLES GLOBALES ---
if 'saldo' not in st.session_state:
    st.session_state.saldo = 1000.0
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'historial_saldo' not in st.session_state:
    st.session_state.historial_saldo = [1000.0]

# --- 2. MÁQUINA DE ESTADOS DEL JUEGO ---
# Estados: 'COUNTDOWN' (Esperando), 'VOLANDO' (Avión en el aire), 'EXPLOSION' (Estalló)
if 'estado_juego' not in st.session_state:
    st.session_state.estado_juego = 'COUNTDOWN'
    st.session_state.target_time = time.time() + 10.0 # 10 segundos de espera
    
    # Datos del vuelo
    st.session_state.multiplicador_final = 1.0
    st.session_state.inicio_vuelo_time = 0.0
    
    # Datos del jugador en la ronda
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

# Controles de apuesta (Se bloquean si ya apostó o si el avión ya despegó)
bloquear_controles = st.session_state.apostado or st.session_state.estado_juego != 'COUNTDOWN'

col1, col2, col3 = st.columns(3)
with col1:
    apuesta_input = st.number_input("Monto a apostar:", min_value=1.0, max_value=max(1.0, float(st.session_state.saldo)), value=10.0, step=1.0, disabled=bloquear_controles)
with col2:
    st.write("") # Espaciador para alinear
    # Casilla de verificación para activar/desactivar el auto-retiro
    auto_retiro = st.checkbox("Activar Retiro Automático", value=False, disabled=bloquear_controles)
with col3:
    # Solo se puede editar si el auto-retiro está activado
    retiro_objetivo = st.number_input("Retirar en (x):", min_value=1.01, value=2.00, step=0.1, disabled=not auto_retiro or bloquear_controles)

st.markdown("---")

# --- 4. BOTÓN DINÁMICO (APOSTAR / COBRAR) ---
zona_boton = st.empty()

with zona_boton.container():
    if st.session_state.estado_juego == 'COUNTDOWN':
        if not st.session_state.apostado:
            # Botón verde para entrar a la ronda
            if st.button("✅ APOSTAR PARA LA PRÓXIMA RONDA", use_container_width=True, type="primary"):
                if apuesta_input > st.session_state.saldo:
                    st.error("⚠️ Saldo insuficiente")
                else:
                    st.session_state.apostado = True
                    st.session_state.apuesta_actual = apuesta_input
                    st.session_state.saldo -= apuesta_input
                    st.session_state.auto_retiro_activado = auto_retiro
                    st.session_state.retiro_objetivo = retiro_objetivo
                    st.rerun() # Recarga instantánea para actualizar la UI
        else:
            st.button("⏳ APUESTA REGISTRADA (Esperando despegue...)", disabled=True, use_container_width=True)

    elif st.session_state.estado_juego == 'VOLANDO':
        if st.session_state.apostado and not st.session_state.cobrado:
            # ¡El botón cambia a COBRAR en pleno vuelo!
            if st.button("💰 COBRAR AHORA", use_container_width=True, type="primary"):
                # Calcular multiplicador exacto del clic usando el tiempo transcurrido
                elapsed = time.time() - st.session_state.inicio_vuelo_time
                m_cobro = math.exp(0.08 * elapsed)
                m_cobro = min(m_cobro, st.session_state.multiplicador_final) # Evitar errores de latencia
                
                st.session_state.cobrado = True
                st.session_state.multiplicador_cobro = m_cobro
                ganancia = st.session_state.apuesta_actual * m_cobro
                st.session_state.saldo += ganancia
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

# --- 7. LÓGICA DE TIEMPO REAL (BUCLES CONTINUOS) ---
# Aquí ocurre la magia para que el juego corra de fondo sin detenerse.

if st.session_state.estado_juego == 'COUNTDOWN':
    # 10 Segundos de espera para decidir si apostar
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
        m = math.exp(0.08 * elapsed) # Curva de aceleración del multiplicador
        
        # Verificar si el avión estalla
        if m >= st.session_state.multiplicador_final:
            st.session_state.estado_juego = 'EXPLOSION'
            st.rerun()
            
        # Verificar Cobro Automático si está activado
        if st.session_state.apostado and not st.session_state.cobrado and st.session_state.auto_retiro_activado:
            if m >= st.session_state.retiro_objetivo:
                st.session_state.cobrado = True
                st.session_state.multiplicador_cobro = st.session_state.retiro_objetivo
                ganancia = st.session_state.apuesta_actual * st.session_state.retiro_objetivo
                st.session_state.saldo += ganancia
                st.session_state.ganancia_ronda = ganancia
                st.rerun()
        
        # Animación visual
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
    
    # Dibujar la explosión estática en el gráfico
    puntos = max(int((math.log(st.session_state.multiplicador_final) / 0.08) * 10), 1)
    datos_grafico = [{'tiempo': t/10.0, 'multiplicador': math.exp(0.08 * (t/10.0))} for t in range(puntos + 1)]
    df = pd.DataFrame(datos_grafico)
    linea = alt.Chart(df).mark_line(color='red', strokeWidth=4).encode(x=alt.X('tiempo', axis=alt.Axis(labels=False, ticks=False, title='')), y=alt.Y('multiplicador', scale=alt.Scale(domain=[1, max(2.5, st.session_state.multiplicador_final)])))
    explosion = alt.Chart(df.tail(1)).mark_point(color='red', size=500, shape='cross').encode(x='tiempo', y='multiplicador')
    pantalla_grafico.altair_chart((linea + explosion).properties(height=300), use_container_width=True)
    
    # Pausa de 3.5 segundos para ver los resultados
    time.sleep(3.5)
    
    # Reset completo para empezar el ciclo de nuevo de forma independiente
    st.session_state.estado_juego = 'COUNTDOWN'
    st.session_state.target_time = time.time() + 10.0
    st.session_state.apostado = False
    st.session_state.cobrado = False
    st.session_state.ganancia_ronda = 0.0
    st.session_state.multiplicador_final = 1.0 
    
    st.rerun() # Dispara la siguiente ronda automáticamente
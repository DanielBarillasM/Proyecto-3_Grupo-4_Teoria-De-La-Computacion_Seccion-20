import streamlit as st
from typing import List, Tuple

def create_statistics_chart(results: List[Tuple[str, bool, int]]) -> None:
    if not results:
        return
    
    accepted = sum(1 for _, a, _ in results if a)
    rejected = len(results) - accepted
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total de Cadenas", len(results))
    with col2:
        st.metric("✅ Aceptadas", accepted, delta=f"{(accepted/len(results)*100):.1f}%")
    with col3:
        st.metric("❌ Rechazadas", rejected, delta=f"{(rejected/len(results)*100):.1f}%")
    
    st.markdown("### 📈 Detalles por Cadena")
    
    for string, accepted_flag, steps in results:
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.code(string, language="text")
        with col2:
            st.write(f"**{steps}** pasos")
        with col3:
            if accepted_flag:
                st.success("✅ Aceptada")
            else:
                st.error("❌ Rechazada")

def setup_page_styles():
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        }
        .info-box {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
            margin: 10px 0;
        }
        .simulation-result {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .accepted {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }
        .rejected {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }
        .info-box, .info-box * { 
            color: #111 !important;
        }
        .info-box strong { 
            color: #111 !important;
        }
        .info-box li::marker {
            color: #4CAF50;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        mode = st.radio(
            "Modo de operación:",
            ["📚 Ejemplos Predefinidos", "📁 Cargar Archivo", "✏️ Editor YAML"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("🎛️ Parámetros de Simulación")
        max_steps = st.slider("Máximo de pasos:", 100, 10000, 1000, 100)
        show_all_ids = st.checkbox("Mostrar todas las IDs", value=False)
        show_graph = st.checkbox("Mostrar diagrama de estados", value=True)
        strict_mode = st.checkbox("δ estricta (sin comodines 'B')", value=False)
        
        st.markdown("---")
        custom_input = st.text_input("Cadena personalizada:", "")
    
    return mode, max_steps, show_all_ids, show_graph, strict_mode, custom_input

def render_welcome_section():
    st.markdown("""
    <div class="info-box">
        <h3>👋 Bienvenido al Simulador de Máquinas de Turing</h3>
        <p>Este simulador te permite:</p>
        <ul>
            <li>✅ Cargar definiciones de MT desde archivos YAML</li>
            <li>📊 Visualizar diagramas de estados interactivos</li>
            <li>🎯 Simular ejecuciones paso a paso</li>
            <li>📈 Analizar estadísticas de aceptación/rechazo</li>
            <li>🔍 Ver descripciones instantáneas detalladas</li>
        </ul>
        <p><strong>Selecciona un modo de operación en la barra lateral para comenzar.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Guía: Estructura del archivo YAML"):
        st.code("""---
q_states:
  q_list:
    - 'q0'
    - 'q1'
    - 'qaccept'
  initial: 'q0'
  final: 'qaccept'
alphabet:
  - a
  - b
tape_alphabet:
  - X
  -
delta:
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q1'
      mem_cache_value: a
      tape_output: X
      tape_displacement: R
simulation_strings:
  - aab
  - ab""", language="yaml")
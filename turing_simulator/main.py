import streamlit as st
from frontend.ui_components import setup_page_styles, render_sidebar, render_welcome_section
from frontend.tabs import render_info_tab, render_diagram_tab, render_simulation_tab, render_statistics_tab
from backend.turing_machine import build_turing_machine_from_yaml
from backend.validator import validate_machine
from utils.examples import EXAMPLES

def main():
    st.set_page_config(
        page_title="Simulador de Máquinas de Turing",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_page_styles()
    
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Simulador de Máquinas de Turing</h1>
        <p>Implementación completa con parsing YAML, visualización gráfica y simulación paso a paso</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render sidebar and get configuration
    mode, max_steps, show_all_ids, show_graph, strict_mode, custom_input = render_sidebar()
    
    # Get YAML content based on mode
    yaml_content = ""
    
    if mode == "📚 Ejemplos Predefinidos":
        st.info("👈 Selecciona un ejemplo en la barra lateral")
        example_choice = st.sidebar.selectbox(
            "Seleccionar ejemplo:",
            list(EXAMPLES.keys())
        )
        if example_choice:
            yaml_content = EXAMPLES[example_choice]
            st.success(f"✅ Ejemplo cargado: **{example_choice}**")
    
    elif mode == "📁 Cargar Archivo":
        uploaded_file = st.sidebar.file_uploader("Subir archivo YAML", type=['yaml', 'yml'])
        if uploaded_file:
            yaml_content = uploaded_file.read().decode('utf-8')
            st.success(f"✅ Archivo cargado: **{uploaded_file.name}**")
        else:
            st.info("👈 Sube un archivo YAML en la barra lateral")
    
    else:  # Editor YAML
        yaml_content = st.text_area(
            "Editor YAML:",
            height=400,
            value="""---
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
      mem_cache_value:
      tape_output: X
      tape_displacement: R
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S
simulation_strings:
  - a
  - aa
  - aaa"""
        )
    
    if not yaml_content:
        render_welcome_section()
        st.markdown("---")
        st.subheader("📚 Ejemplos Disponibles")
        for i, name in enumerate(EXAMPLES.keys(), 1):
            st.write(f"{i}. **{name}**")
        return
    
    try:
        with st.spinner("🔄 Procesando Máquina de Turing..."):
            tm, simulation_strings, dup_msgs = build_turing_machine_from_yaml(yaml_content, strict_mode=strict_mode)
            issues = validate_machine(
                tm.states, tm.initial_state, tm.final_state,
                tm.input_alphabet, tm.tape_alphabet, tm.transitions, simulation_strings
            )
            issues.extend(dup_msgs)
            if issues:
                with st.expander("⚠️ Problemas detectados en la definición (haz click para ver)"):
                    for msg in issues:
                        st.warning(msg)
                st.stop()  # Detener si hay problemas
            else:
                st.success("✅ Validación básica: sin problemas detectados")
        
        # Initialize session state for results
        results = st.session_state.setdefault("results", [])
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Información", "📊 Diagrama", "🎯 Simulación", "📈 Estadísticas"])
        
        with tab1:
            render_info_tab(tm, strict_mode)
        
        with tab2:
            render_diagram_tab(tm, show_graph)
        
        with tab3:
            new_results = render_simulation_tab(tm, simulation_strings, custom_input, max_steps, show_all_ids)
            if new_results:
                results.clear()
                results.extend(new_results)
        
        with tab4:
            render_statistics_tab(results)
    
    except Exception as e:
        st.error(f"❌ Error al procesar el YAML: {str(e)}")
        
        with st.expander("🐛 Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc(), language="python")
        
        with st.expander("📄 Ver YAML problemático"):
            st.code(yaml_content, language="yaml")

if __name__ == "__main__":
    main()
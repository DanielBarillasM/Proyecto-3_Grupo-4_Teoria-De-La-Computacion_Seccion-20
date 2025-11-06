import streamlit as st
from backend.models import TuringMachine
from backend.validator import validate_machine
from utils.helpers import export_transitions_table, _B
from typing import List, Tuple

def render_info_tab(tm: TuringMachine, strict_mode: bool):
    st.header("📋 Información de la Máquina de Turing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Estados")
        st.write(f"**Total:** {len(tm.states)}")
        st.write(f"**Inicial:** `{tm.initial_state}`")
        st.write(f"**Final:** `{tm.final_state}`")
        st.write(f"**Lista:** {', '.join(f'`{s}`' for s in tm.states)}")
    
    with col2:
        st.markdown("### Alfabetos")
        st.write(f"**Entrada:** {', '.join(f'`{_B(s)}`' for s in tm.input_alphabet)}")
        st.write(f"**Cinta:** {', '.join(f'`{_B(s)}`' for s in tm.tape_alphabet)}")
    
    with col3:
        st.markdown("### Transiciones")
        st.write(f"**Total:** {len(tm.transitions)}")
    
    st.markdown("---")
    st.subheader("📝 Tabla de Transiciones")
    st.dataframe(export_transitions_table(tm), use_container_width=True)
    st.caption(
        "Resolución de δ: " +
        ("estricta (B solo cuando la celda es realmente blanca)"
        if strict_mode else
        "prioridad exacta → (mem,B) → (B,cinta) → (B,B). B = blanco/comodín.")
    )

def render_diagram_tab(tm: TuringMachine, show_graph: bool):
    st.header("📊 Diagrama de Estados")
    
    if show_graph:
        try:
            dot = tm.to_graphviz()
            st.graphviz_chart(dot, use_container_width=True)
            
            st.markdown("""
            <div class="info-box">
                <strong>Leyenda:</strong>
                <ul>
                    <li>🟢 Estado inicial (amarillo claro)</li>
                    <li>🎯 Estado final (verde claro, doble círculo)</li>
                    <li>🔵 Estados intermedios (azul claro)</li>
                    <li>➡️ Transiciones con formato: [cache],entrada → [cache],salida,dirección</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error al generar diagrama: {str(e)}")
    else:
        st.info("Activa 'Mostrar diagrama de estados' en la barra lateral")

def render_simulation_tab(tm: TuringMachine, simulation_strings: List[str], 
                         custom_input: str, max_steps: int, show_all_ids: bool):
    st.header("🎯 Simulaciones")
    
    strings_to_simulate = simulation_strings.copy()
    if custom_input and custom_input.strip():
        strings_to_simulate.append(custom_input.strip())
    
    if not strings_to_simulate:
        st.warning("⚠️ No hay cadenas para simular. Agrega cadenas en 'simulation_strings' o usa la entrada personalizada.")
        return []
    
    results = []
    
    # Validar cadena personalizada
    if custom_input and custom_input.strip():
        bad = [c for c in custom_input if c not in set(tm.input_alphabet)]
        if bad:
            st.warning(f"Cadena personalizada contiene símbolos fuera de 'alphabet': {set(bad)}")
            return []
    
    for idx, input_string in enumerate(strings_to_simulate, 1):
        st.markdown(f"### Simulación {idx}: `{input_string}`")
        
        with st.spinner(f"Simulando cadena {idx}..."):
            accepted, ids, last_transition = tm.simulate(input_string, max_steps)
        
        result_class = "accepted" if accepted else "rejected"
        result_icon = "✅" if accepted else "❌"
        result_text = "ACEPTADA" if accepted else "RECHAZADA"
        
        st.markdown(f"""
        <div class="simulation-result {result_class}">
            <h4>{result_icon} {result_text}</h4>
            <p><strong>Cadena:</strong> <code>{input_string}</code></p>
            <p><strong>Pasos ejecutados:</strong> {len(ids)-1}</p>
            <p><strong>Estado final:</strong> {ids[-1].state}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if last_transition:
            st.info(f"**Última transición:** {last_transition}")
        
        if show_all_ids:
            st.markdown("#### 📝 Descripciones Instantáneas Completas")
            for id_desc in ids:
                if id_desc.step == 0:
                    st.markdown("**🟢 Configuración Inicial:**")
                elif id_desc.step == len(ids) - 1:
                    st.markdown(f"**🔴 Configuración Final (Paso {id_desc.step}):**")
                else:
                    st.markdown(f"**Paso {id_desc.step}:**")
                
                st.markdown(id_desc.to_html(), unsafe_allow_html=True)
                
                if id_desc.step < len(ids) - 1:
                    st.markdown("⬇️")
        else:
            with st.expander(f"Ver {len(ids)} descripciones instantáneas"):
                for id_desc in ids:
                    if id_desc.step == 0:
                        st.markdown("**🟢 Configuración Inicial:**")
                    elif id_desc.step == len(ids) - 1:
                        st.markdown(f"**🔴 Configuración Final (Paso {id_desc.step}):**")
                    else:
                        st.markdown(f"**Paso {id_desc.step}:**")
                    
                    st.markdown(id_desc.to_html(), unsafe_allow_html=True)
                    
                    if id_desc.step < len(ids) - 1:
                        st.markdown("⬇️")

                if not accepted and len(ids)-1 >= max_steps:
                    st.warning("⏱️ Rechazada por límite de pasos.")
                elif not accepted:
                    st.warning("🚫 Rechazada: no había transición aplicable.")

        results.append((input_string, accepted, len(ids)-1))
        st.markdown("---")
    
    return results

def render_statistics_tab(results: List[Tuple[str, bool, int]]):
    st.header("📈 Estadísticas de Simulación")
    
    if not results:
        st.warning("No hay resultados de simulación para mostrar")
        return
    
    from frontend.ui_components import create_statistics_chart
    create_statistics_chart(results)
    
    st.markdown("### 🔍 Análisis Detallado")
    
    accepted_count = sum(1 for _, acc, _ in results if acc)
    rejected_count = sum(1 for _, acc, _ in results if not acc)
    
    avg_steps_accepted = sum(steps for _, acc, steps in results if acc) / max(accepted_count, 1)
    avg_steps_rejected = sum(steps for _, acc, steps in results if not acc) / max(rejected_count, 1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("⏱️ Promedio pasos (aceptadas)", f"{avg_steps_accepted:.1f}")
        
    with col2:
        st.metric("⏱️ Promedio pasos (rechazadas)", f"{avg_steps_rejected:.1f}")
    
    st.markdown("### 📊 Tabla Resumen")
    st.dataframe({
        "Cadena": [s for s, _, _ in results],
        "Estado": ["✅ Aceptada" if a else "❌ Rechazada" for _, a, _ in results],
        "Pasos": [steps for _, _, steps in results]
    }, use_container_width=True)
from typing import List, Tuple, Optional
from backend.models import TuringMachine, Transition, TransitionParams, TransitionOutput, Direction
from backend.parser import YAMLParser

def _is_blank(x: Optional[str]) -> bool:
    return x in (None, "", " ", "B")

def parse_direction(direction_str: str) -> Direction:
    if not direction_str:
        return Direction.STAY
    direction_str = direction_str.upper()
    if direction_str == 'L':
        return Direction.LEFT
    elif direction_str == 'R':
        return Direction.RIGHT
    else:
        return Direction.STAY

def build_turing_machine_from_yaml(yaml_content: str, strict_mode: bool = False) -> Tuple[TuringMachine, List[str], List[str]]:
    import streamlit as st
    
    parser = YAMLParser()
    data = parser.parse(yaml_content)
    
    # DEBUG: Mostrar datos parseados
    st.sidebar.markdown("**DEBUG - Datos parseados:**")
    st.sidebar.json(data, expanded=False)
    
    # Extraer estados - MANEJO ROBUSTO
    q_states = data.get('q_states', {}) or {}
    
    if isinstance(q_states, dict):
        states = q_states.get('q_list', []) or []
        states = [str(s) for s in states]
        initial_state = str(q_states.get('initial', '0'))
        final_state = str(q_states.get('final', '0'))
    else:
        # Fallback
        states = ['0', '1']
        initial_state = '0'
        final_state = '1'
    
    # Extraer alfabetos
    input_alphabet = data.get('alphabet', []) or []
    if not isinstance(input_alphabet, list):
        input_alphabet = [input_alphabet] if input_alphabet else []
    input_alphabet = [str(sym) for sym in input_alphabet if sym is not None]
    
    tape_alphabet = data.get('tape_alphabet', []) or []
    if not isinstance(tape_alphabet, list):
        tape_alphabet = [tape_alphabet] if tape_alphabet else []
    
    # Incluir alfabeto de entrada en alfabeto de cinta
    for symbol in input_alphabet:
        if symbol not in tape_alphabet:
            tape_alphabet.append(symbol)
    
    tape_alphabet = [str(sym) if sym is not None else None for sym in tape_alphabet]
    
    # Construir transiciones
    delta_data = data.get('delta', []) or []
    transitions = []

    for trans_data in delta_data:
        if not isinstance(trans_data, dict):
            continue
        
        params_data = trans_data.get('params', {}) or {}
        output_data = trans_data.get('output', {}) or {}

        p_initial_state = str(params_data.get('initial_state', '0'))
        
        # Manejar mem_cache_value - convertir blanks a None
        p_cache = params_data.get('mem_cache_value')
        if p_cache in ['', ' ', 'B', None]:
            p_cache = None
        elif p_cache is not None:
            p_cache = str(p_cache)

        # Manejar tape_input - convertir blanks a None
        p_tape_in = params_data.get('tape_input')
        if p_tape_in in ['', ' ', 'B', None]:
            p_tape_in = None
        elif p_tape_in is not None:
            p_tape_in = str(p_tape_in)

        params = TransitionParams(
            initial_state=p_initial_state,
            mem_cache_value=p_cache,
            tape_input=p_tape_in
        )

        o_final_state = str(output_data.get('final_state', '0'))
        
        # Manejar mem_cache_value de salida
        o_cache = output_data.get('mem_cache_value')
        if o_cache in ['', ' ', 'B', None]:
            o_cache = None
        elif o_cache is not None:
            o_cache = str(o_cache)

        # Manejar tape_output de salida
        o_tape_out = output_data.get('tape_output')
        if o_tape_out in ['', ' ', 'B', None]:
            o_tape_out = None
        elif o_tape_out is not None:
            o_tape_out = str(o_tape_out)

        output = TransitionOutput(
            final_state=o_final_state,
            mem_cache_value=o_cache,
            tape_output=o_tape_out,
            tape_displacement=parse_direction(output_data.get('tape_displacement', 'S'))
        )

        transitions.append(Transition(params=params, output=output))
    
    # Extraer cadenas de simulación
    simulation_strings = data.get('simulation_strings', []) or []
    if not isinstance(simulation_strings, list):
        simulation_strings = [simulation_strings] if simulation_strings else []
    simulation_strings = [str(s) for s in simulation_strings if s is not None]
    
    tm = TuringMachine(
        states=states,
        initial_state=initial_state,
        final_state=final_state,
        input_alphabet=input_alphabet,
        tape_alphabet=tape_alphabet,
        transitions=transitions,
        strict_mode=strict_mode
    )

    # En duro: si el motor encontró duplicadas, agrégalas a issues
    dup_msgs = [f"Transición duplicada para {k}" for k in tm.duplicates]
    return tm, simulation_strings, dup_msgs
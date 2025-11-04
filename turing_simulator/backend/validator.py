from typing import List, Dict, Any, Optional, Tuple, Set
from backend.models import Transition

def _is_blank(x: Optional[str]) -> bool:
    return x in (None, "", " ", "B")

def validate_machine(states: List[str],
                     initial_state: str,
                     final_state: str,
                     input_alphabet: List[str],
                     tape_alphabet: List[Optional[str]],
                     transitions: List[Transition],
                     simulation_strings: List[str]) -> List[str]:
    issues: List[str] = []

    # 0) Estado inicial/final y duplicados de estados
    if initial_state not in states:
        issues.append(f"El estado inicial '{initial_state}' no está en q_states.q_list")
    if final_state not in states:
        issues.append(f"El estado final '{final_state}' no está en q_states.q_list")
    if len(states) != len(set(states)):
        issues.append("Estados duplicados en q_states.q_list")

    used_states = {initial_state, final_state} | \
                  {t.params.initial_state for t in transitions} | \
                  {t.output.final_state for t in transitions}
    unused = set(states) - used_states
    if unused:
        issues.append(f"Estados definidos pero sin uso: {sorted(unused)}")

    # 1) Estados
    for t in transitions:
        if t.params.initial_state not in states:
            issues.append(f"Transición con estado inicial desconocido: {t.params.initial_state}")
        if t.output.final_state not in states:
            issues.append(f"Transición con estado final desconocido: {t.output.final_state}")

    # 2) Símbolos de cinta
    tape_set: Set[Optional[str]] = set(tape_alphabet)
    for t in transitions:
        if t.params.tape_input not in tape_set and not _is_blank(t.params.tape_input):
            issues.append(f"tape_input '{t.params.tape_input}' no está en tape_alphabet")
        if t.output.tape_output not in tape_set and not _is_blank(t.output.tape_output):
            issues.append(f"tape_output '{t.output.tape_output}' no está en tape_alphabet")

    # 3) Duplicadas
    seen: Set[Tuple[str, Optional[str], Optional[str]]] = set()
    for t in transitions:
        key = (t.params.initial_state,
               None if _is_blank(t.params.mem_cache_value) else t.params.mem_cache_value,
               None if _is_blank(t.params.tape_input) else t.params.tape_input)
        if key in seen:
            issues.append(f"Transición duplicada para {key}")
        else:
            seen.add(key)

    # 4) Cadenas vs alphabet
    in_set: Set[str] = set(input_alphabet)
    for s in simulation_strings:
        bad = [c for c in s if c not in in_set]
        if bad:
            issues.append(f"Cadena '{s}' contiene símbolos fuera de alphabet: {set(bad)}")

    # 5) El blanco (None/B) DEBE estar en tape_alphabet (se permite como '-')
    if None not in tape_set:
        issues.append("El alfabeto de cinta debe incluir el blanco (usa una línea '-' en YAML).")

    # 6) Si las cadenas de prueba contienen '#', exige que '#' esté en alphabet
    if any('#' in s for s in simulation_strings) and ('#' not in input_alphabet):
        issues.append("Las cadenas de prueba usan '#', pero '#' no está en 'alphabet'. Agrégalo (entre comillas).")

    return issues
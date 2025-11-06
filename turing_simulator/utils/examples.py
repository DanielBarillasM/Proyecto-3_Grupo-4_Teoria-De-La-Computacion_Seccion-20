EXAMPLES = {
    "Ejemplo A: Aceptador universal (3 fases)": """---
q_states:
  q_list:
    - 'q0'
    - 'q1'
    - 'q2'
    - 'qaccept'
  initial: 'q0'
  final: 'qaccept'
alphabet:
  - a
  - b
  - '#'
tape_alphabet:
  - '#'
  -
delta:
  # ==================== Fase 1: q0 -> q1 (consume 1 símbolo y avanza) ====================
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Al llegar a blank en q0, aceptar
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S

  # ==================== Fase 2: q1 -> q2 (consume 1 símbolo y avanza) ====================
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Al llegar a blank en q1, aceptar
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S

  # ==================== Fase 3: q2 -> q0 (consume 1 símbolo y avanza) ====================
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Al llegar a blank en q2, aceptar
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S

simulation_strings:
  - ''
  - a
  - b
  - 'ab#a#bb'
  - '###'
  - 'abbaabbab#abba'
  - 'abababababababababab'
  - 'a#b#a#b#a#b#a#'
""",
    # Agregar otros ejemplos después
}
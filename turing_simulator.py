import streamlit as st
import graphviz
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd

# --- helpers de blanks y formato ---
from typing import Set

def _is_blank(x: Optional[str]) -> bool:
    return x in (None, "", " ", "B")

def _B(x: Optional[str]) -> str:
    return "B" if x is None else str(x)

def validate_machine(states: List[str],
                     initial_state: str,
                     final_state: str,
                     input_alphabet: List[str],
                     tape_alphabet: List[Optional[str]],
                     transitions: List['Transition'],
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



# ============================================================================
# PARSER DE YAML MANUAL
# ============================================================================

@dataclass
class _Node:
    container: Any
    indent: int

class YAMLParser:
    @staticmethod
    def parse(yaml_content: str) -> Dict[str, Any]:
        lines = yaml_content.splitlines()

        def strip_comment(line: str) -> str:
            s = []
            in_s = in_d = False
            i = 0
            while i < len(line):
                c = line[i]
                if c == "'" and not in_d:
                    in_s = not in_s
                    s.append(c)
                elif c == '"' and not in_s:
                    in_d = not in_d
                    s.append(c)
                elif c == '#' and not in_s and not in_d:
                    break
                else:
                    s.append(c)
                i += 1
            return "".join(s)
    
        def indent_of(line: str) -> int:
            return len(line) - len(line.lstrip(' '))

        def parse_scalar(val: str) -> Optional[str]:
            v = val.strip()
            if v == "" or v.lower() in ("null", "~"):
                return None
            if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                return v[1:-1]
            return v

        def next_significant(idx: int):
            j = idx + 1
            while j < len(lines):
                raw = strip_comment(lines[j]).rstrip("\r")
                if raw.strip() == "" or raw.strip().startswith("---"):
                    j += 1
                    continue
                return indent_of(raw), raw.strip()
            return None, None

        root: Dict[str, Any] = {}
        stack: List[_Node] = [_Node(root, -1)]

        i = 0
        while i < len(lines):
            raw = strip_comment(lines[i]).rstrip("\r")
            if raw.strip() == "" or raw.strip().startswith("---"):
                i += 1
                continue

            indent = indent_of(raw)
            stripped = raw.strip()

            while stack and indent <= stack[-1].indent:
                stack.pop()
            if not stack:
                raise ValueError("Indentación inválida en la línea: " + stripped)

            parent = stack[-1].container

            # Ítems de lista
            if stripped.startswith("-"):
                if not isinstance(parent, list):
                    raise ValueError("Item de lista sin lista contenedora.")

                after_dash = stripped[1:].lstrip()
                item_indent = indent + 2

                if after_dash == "":
                    parent.append(None)
                    i += 1
                    continue

                if ":" in after_dash:
                    key, val = after_dash.split(":", 1)
                    key = parse_scalar(key) or ""
                    val = val.strip()

                    item_obj: Dict[str, Any] = {}
                    parent.append(item_obj)
                    stack.append(_Node(item_obj, indent))

                    if val == "":
                        n_indent, n_strip = next_significant(i)
                        if n_indent is not None and n_indent > item_indent:
                            # hay bloque anidado
                            if n_strip.startswith("-"):
                                item_obj[key] = []
                            else:
                                item_obj[key] = {}
                            stack.append(_Node(item_obj[key], item_indent))
                        else:
                            # es escalar vacío => None
                            item_obj[key] = None
                            # no apilamos porque es escalar
                    else:
                        item_obj[key] = parse_scalar(val)

                    i += 1
                    continue

                parent.append(parse_scalar(after_dash))
                i += 1
                continue

            # Pares clave:valor
            if ":" in stripped:
                key, val = stripped.split(":", 1)
                key = parse_scalar(key) or ""
                val = val.strip()

                if not isinstance(parent, dict):
                    raise ValueError(f"Se esperaba dict como padre para clave '{key}'.")

                if val == "":
                    n_indent, n_strip = next_significant(i)
                    if n_indent is not None and n_indent > indent:
                        if n_strip.startswith("-"):
                            parent[key] = []
                        else:
                            parent[key] = {}
                        stack.append(_Node(parent[key], indent))
                    else:
                        parent[key] = None
                else:
                    parent[key] = parse_scalar(val)

                i += 1
                continue

            raise ValueError("Línea YAML no reconocida: " + stripped)

        return root


# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================

class Direction(Enum):
    LEFT = 'L'
    RIGHT = 'R'
    STAY = 'S'


@dataclass
class TransitionParams:
    initial_state: str
    mem_cache_value: Optional[str]
    tape_input: Optional[str]


@dataclass
class TransitionOutput:
    final_state: str
    mem_cache_value: Optional[str]
    tape_output: Optional[str]
    tape_displacement: Direction


@dataclass
class Transition:
    params: TransitionParams
    output: TransitionOutput
    
    def __str__(self) -> str:
        cache_in = self.params.mem_cache_value if self.params.mem_cache_value else 'B'
        tape_in = self.params.tape_input if self.params.tape_input else 'B'
        cache_out = self.output.mem_cache_value if self.output.mem_cache_value else 'B'
        tape_out = self.output.tape_output if self.output.tape_output else 'B'
        
        return f"δ([{self.params.initial_state}, {cache_in}], {tape_in}) → ([{self.output.final_state}, {cache_out}], {tape_out}, {self.output.tape_displacement.value})"


@dataclass
class InstantaneousDescription:
    state: str
    tape: List[Optional[str]]
    head_position: int
    mem_cache: Optional[str]
    step: int
    
    def __str__(self) -> str:
        tape_str = ""
        for i, symbol in enumerate(self.tape):
            sym = symbol if symbol is not None else 'B'
            if i == self.head_position:
                tape_str += f"[{self.state}]({sym})"
            else:
                tape_str += sym
        
        cache_str = f", Cache: {self.mem_cache if self.mem_cache else 'B'}"
        return f"ID_{self.step}: {tape_str}{cache_str}"
    
    def to_html(self) -> str:
        # estilos: todas las celdas fondo negro y texto blanco
        base = (
            "background:#000;color:#fff;padding:6px 10px;margin:2px;"
            "border:1px solid #333;border-radius:4px;min-width:28px;"
            "text-align:center;display:inline-block;font-family:monospace;"
        )
        # para el cabezal: mismo fondo negro pero resaltado con borde dorado
        head = base + "outline:3px solid #ffcc00;font-weight:bold;"

        tape_html = '<div style="display:flex;align-items:center;flex-wrap:wrap;">'
        tape_html += '<span style="margin-right:10px;font-weight:bold;font-family:monospace;">Cinta:</span>'

        for i, symbol in enumerate(self.tape):
            sym = symbol if symbol is not None else 'B'
            style = head if i == self.head_position else base
            tape_html += f'<span style="{style}">{sym}</span>'

        cache_val = self.mem_cache if self.mem_cache else 'B'
        tape_html += (
            '</div>'
            f'<div style="margin-top:10px;font-family:monospace;font-size:14px;">'
            f'Estado: <strong>{self.state}</strong> | '
            f'Cache: <strong>{cache_val}</strong> | '
            f'Posición: <strong>{self.head_position}</strong>'
            f'</div>'
        )
        return tape_html

# ============================================================================
# MÁQUINA DE TURING
# ============================================================================

class TuringMachine:
    def __init__(self,
                 states: List[str],
                 initial_state: str,
                 final_state: str,
                 input_alphabet: List[str],
                 tape_alphabet: List[str],
                 transitions: List[Transition],
                 strict_mode: bool = False):
        self.states = states
        self.initial_state = initial_state
        self.final_state = final_state
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.transitions = transitions
        self.strict_mode = strict_mode

        # Índice determinista: una sola transición por (q, cache, tape)
        self.transition_map: Dict[Tuple[str, Optional[str], Optional[str]], Transition] = {}
        self.duplicates: List[Tuple[str, Optional[str], Optional[str]]] = []

        for t in transitions:
            cache_key = None if _is_blank(t.params.mem_cache_value) else str(t.params.mem_cache_value)
            tape_key  = None if _is_blank(t.params.tape_input)      else str(t.params.tape_input)
            key = (t.params.initial_state, cache_key, tape_key)
            if key in self.transition_map:
                self.duplicates.append(key)
            else:
                self.transition_map[key] = t

    # Prioridad: exacta → (mem,B) → (B,tape) → (B,B)
    def _candidates(self, state: str, mem_cache: Optional[str], tape_symbol: Optional[str]):
        m = None if _is_blank(mem_cache)  else str(mem_cache)
        t = None if _is_blank(tape_symbol) else str(tape_symbol)
        yield (state, m, t)
        yield (state, m, None)
        yield (state, None, t)
        yield (state, None, None)

    def find_transition(self, state: str, mem_cache: Optional[str],
                        tape_symbol: Optional[str]) -> Optional[Transition]:
        if self.strict_mode:
            m = None if _is_blank(mem_cache)  else str(mem_cache)
            t = None if _is_blank(tape_symbol) else str(tape_symbol)
            return self.transition_map.get((state, m, t))
        for k in self._candidates(state, mem_cache, tape_symbol):
            tr = self.transition_map.get(k)
            if tr is not None:
                return tr
        return None

    def simulate(self, input_string: str, max_steps: int = 10000) -> Tuple[bool, List[InstantaneousDescription], Optional[Transition]]:
        # Inicializar cinta y cabezal
        if input_string:
            tape = [None] + list(input_string) + [None]
            head_position = 1
        else:
            tape = [None]
            head_position = 0

        current_state = self.initial_state
        mem_cache = None

        ids: List[InstantaneousDescription] = [
            InstantaneousDescription(
                state=current_state,
                tape=tape.copy(),
                head_position=head_position,
                mem_cache=mem_cache,
                step=0
            )
        ]

        steps = 0
        last_transition: Optional[Transition] = None

        while steps < max_steps:
            if current_state == self.final_state:
                return True, ids, last_transition

            current_symbol = tape[head_position]
            transition = self.find_transition(current_state, mem_cache, current_symbol)
            if transition is None:
                ids.append(InstantaneousDescription(
                    state=f"{current_state} (SIN δ)",
                    tape=tape.copy(),
                    head_position=head_position,
                    mem_cache=mem_cache,
                    step=steps + 1
                ))
                return False, ids, last_transition

            last_transition = transition
            steps += 1

            # Escribir y actualizar estado/cache
            current_state = transition.output.final_state
            mem_cache = transition.output.mem_cache_value
            tape[head_position] = transition.output.tape_output

            # Mover cabezal con extensión inmediata
            if transition.output.tape_displacement == Direction.LEFT:
                head_position -= 1
                if head_position < 0:
                    tape.insert(0, None)
                    head_position = 0
            elif transition.output.tape_displacement == Direction.RIGHT:
                head_position += 1
                if head_position >= len(tape):
                    tape.append(None)
            # STAY: no mover

            ids.append(InstantaneousDescription(
                state=current_state,
                tape=tape.copy(),
                head_position=head_position,
                mem_cache=mem_cache,
                step=steps
            ))

            if current_state == self.final_state:
                return True, ids, last_transition

        return False, ids, last_transition

    def to_graphviz(self) -> graphviz.Digraph:
        dot = graphviz.Digraph(comment='Máquina de Turing')
        dot.attr(rankdir='LR', size='10,8')
        dot.attr('node', shape='circle', style='filled', fillcolor='lightblue')

        # Flecha de inicio
        dot.node('start', '', shape='none', width='0', height='0')
        dot.edge('start', self.initial_state, label='inicio', color='green', penwidth='2')

        # Estados
        for state in self.states:
            if state == self.final_state:
                dot.node(state, state, shape='doublecircle', fillcolor='lightgreen')
            elif state == self.initial_state:
                dot.node(state, state, fillcolor='lightyellow')
            else:
                dot.node(state, state)

        # Agrupar transiciones por (src, dst) para compactar etiquetas
        transition_groups: Dict[Tuple[str, str], List[Transition]] = {}
        for t in self.transitions:
            key = (t.params.initial_state, t.output.final_state)
            transition_groups.setdefault(key, []).append(t)

        for (src, dst), trans_list in transition_groups.items():
            labels = []
            for t in trans_list:
                cache_in  = _B(t.params.mem_cache_value)
                tape_in   = _B(t.params.tape_input)
                cache_out = _B(t.output.mem_cache_value)
                tape_out  = _B(t.output.tape_output)
                labels.append(f"[{cache_in}],{tape_in} → [{cache_out}],{tape_out},{t.output.tape_displacement.value}")
            dot.edge(src, dst, label="\\n".join(labels), fontsize='9')

        return dot

# ============================================================================
# CONSTRUCTOR DE MT DESDE YAML
# ============================================================================

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
    # y evita simular.
    dup_msgs = [f"Transición duplicada para {k}" for k in tm.duplicates]
    return tm, simulation_strings, dup_msgs

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def export_transitions_table(tm: TuringMachine) -> pd.DataFrame:
    """Devuelve un DataFrame listo para mostrar con st.table/st.dataframe."""
    rows = []
    for idx, t in enumerate(tm.transitions, 1):
        rows.append({
            "#": idx,
            "Estado Inicial": t.params.initial_state,
            "Cache In": _B(t.params.mem_cache_value),
            "Cinta In": _B(t.params.tape_input),
            "→": "→",
            "Estado Final": t.output.final_state,
            "Cache Out": _B(t.output.mem_cache_value),
            "Cinta Out": _B(t.output.tape_output),
            "Dirección": t.output.tape_displacement.value,
        })
    return pd.DataFrame(rows, columns=[
        "#","Estado Inicial","Cache In","Cinta In","→",
        "Estado Final","Cache Out","Cinta Out","Dirección"
    ])


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


# ============================================================================
# EJEMPLOS PREDEFINIDOS
# ============================================================================

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

  "Ejemplo B: Borrador (doble barrido y aceptación)": """---
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
  - X
  -
delta:
  # ==================== Barrido 1 (derecha): marcar todo como X ====================
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R
  # Al llegar al blank (fin de entrada), preparar vuelta a la izquierda
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output:
      tape_displacement: L

  # ==================== Barrido 2 (izquierda): regresar hasta el blank izquierdo ====================
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: X
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: X
      tape_displacement: L
  # Al topar blank izquierdo, colocarse para limpiar hacia la derecha
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output:
      tape_displacement: R

  # ==================== Barrido 3 (derecha): limpiar X -> blank y aceptar al final ====================
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: X
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output:
      tape_displacement: R
  # Cuando ya no queden X (blank), aceptar
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
  - 'a#b'
  - 'abba#abba'
  - 'b#abab#a'
  - 'ababbababb#b'
  - '####'
  - 'ab#ab#ab#ab'
""",

  "Ejemplo C: Swap a<->b y aceptación (3 fases)": """---
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
  # ============ Fase 1: swap mientras avanzo a la derecha ============
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Al blank de la derecha, cambio de fase y retrocedo
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output:
      tape_displacement: L

  # ============ Fase 2: regresar al comienzo (izquierda) ============
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: a
      tape_displacement: L
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: b
      tape_displacement: L
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: L
  # Al blank izquierdo, preparo el barrido final a la derecha
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output:
      tape_displacement: R

  # ============ Fase 3: verificación/recorrido final y aceptar ============
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q2'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q2'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Al blank derecho, aceptar
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
  - 'abba'
  - 'a#b'
  - 'bbb##aaa'
  - '#ab#ab#'
  - 'ababa#babab'
""",

  "Ejemplo D: Rechazador universal (sumidero)": """---
q_states:
  q_list:
    - 'q0'
    - 'qdead'
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
  # ===== Desde q0: cualquier símbolo lleva al sumidero qdead =====
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R
  # Nota: si la cadena inicia en blanco (vacía), no hay transición desde q0 -> rechaza

  # ===== Sumidero qdead: bucles en a, b, '#' mientras se desplaza =====
  - params:
      initial_state: 'qdead'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'qdead'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'qdead'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qdead'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # Importante: no definas transición en qdead con blank.
  # Así, al llegar al blanco derecho, la máquina se queda sin regla y HALT no-aceptante.

simulation_strings:
  - ''
  - a
  - b
  - 'ab#ab'
  - '#'
  - 'abba#'
  - 'bbbbbbbbbbbb'
  - 'a###b#abba'
""",

  "Ejemplo E: Rechazador (solo vacío aceptaría)": """---
q_states:
  q_list:
    - 'q0'
    - 'qtrap'
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
  # Acepta si la cinta inicia en blanco (cadena vacía)
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S

  # Si hay al menos un símbolo, cae en el sumidero qtrap
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # En qtrap se avanza a la derecha sin salir (no hay transición con blanco)
  - params:
      initial_state: 'qtrap'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: a
      tape_displacement: R
  - params:
      initial_state: 'qtrap'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: b
      tape_displacement: R
  - params:
      initial_state: 'qtrap'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qtrap'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # Importante: NO hay transición en qtrap con blank => al final HALT no-aceptante
simulation_strings:
  - ''
  - a
  - b
  - '#'
  - 'a#b'
  - '###'
  - 'abba'
  - 'ab#ab'
  - '#a'
  - 'b#abba#'
""",

  "Ejemplo F: Borrador y HALT no aceptante": """---
q_states:
  q_list:
    - 'q0'
    - 'qhalt'
    - 'qaccept'
  initial: 'q0'
  final: 'qaccept'
alphabet:
  - a
  - b
  - '#'
tape_alphabet:
  - '#'
  - X
  -
delta:
  # En q0: borrar (escribir X) y avanzar a la derecha
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R

  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R

  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: X
      tape_displacement: R

  # Al encontrar blanco: HALT no aceptante (qhalt)
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qhalt'
      mem_cache_value:
      tape_output:
      tape_displacement: S

  # Nota: qhalt no tiene transiciones => se detiene y NO acepta
simulation_strings:
  - ''
  - a
  - b
  - '#'
  - 'ab#ba'
  - 'a#b#abba'
  - 'baba#'
  - '##ab'
  - 'abbaabbab#abba'
""",

  "Ejemplo G: OR (termina en 'a' 𝘰 paridad de 'a' par) — simulación determinista del NDT": """---
q_states:
  q_list:
    - 'q0'       # Fase 1: ir al final
    - 'q1'       # Chequear último símbolo
    - 'qrew'     # Retroceder al blanco izquierdo
    - 'qeven'    # Contador par de 'a'
    - 'qodd'     # Contador impar de 'a'
    - 'qreject'  # Halt no aceptante
    - 'qaccept'  # Halt aceptante
  initial: 'q0'
  final: 'qaccept'
alphabet:
  - a
  - b
  - '#'
tape_alphabet:
  - '#'
  -           # B (blank)
delta:
  # =========================
  # Fase 1: avanzar hasta el blanco (final de cinta)
  # =========================
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: a
      tape_displacement: R

  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: b
      tape_displacement: R

  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'q0'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # Al encontrar blanco derecho, mover una a la izquierda para mirar el último símbolo
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output:
      tape_displacement: L

  # =========================
  # Fase 2: ¿termina en 'a'?
  # =========================
  # Si el último símbolo es 'a' => aceptar
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output: a
      tape_displacement: S

  # Si es 'b' o '#' => pasar a la rama "paridad"
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output: b
      tape_displacement: L

  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: L

  # Caso cadena vacía: ya estamos sobre blanco izquierdo, ir directo a paridad
  - params:
      initial_state: 'q1'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output:
      tape_displacement: L

  # =========================
  # Fase 3: rebobinar al inicio (blanco izquierdo)
  # =========================
  - params:
      initial_state: 'qrew'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output: a
      tape_displacement: L

  - params:
      initial_state: 'qrew'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output: b
      tape_displacement: L

  - params:
      initial_state: 'qrew'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qrew'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: L

  # Al tocar el blanco izquierdo, avanzar a la primera celda y empezar conteo par
  - params:
      initial_state: 'qrew'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qeven'
      mem_cache_value:
      tape_output:
      tape_displacement: R

  # =========================
  # Fase 4: conteo de paridad de 'a'
  # =========================
  # Estado qeven: par hasta ahora
  - params:
      initial_state: 'qeven'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qodd'
      mem_cache_value:
      tape_output: a
      tape_displacement: R

  - params:
      initial_state: 'qeven'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qeven'
      mem_cache_value:
      tape_output: b
      tape_displacement: R

  - params:
      initial_state: 'qeven'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qeven'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # Si llego al blanco con paridad par => aceptar
  - params:
      initial_state: 'qeven'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qaccept'
      mem_cache_value:
      tape_output:
      tape_displacement: S

  # Estado qodd: impar hasta ahora
  - params:
      initial_state: 'qodd'
      mem_cache_value:
      tape_input: a
    output:
      final_state: 'qeven'
      mem_cache_value:
      tape_output: a
      tape_displacement: R

  - params:
      initial_state: 'qodd'
      mem_cache_value:
      tape_input: b
    output:
      final_state: 'qodd'
      mem_cache_value:
      tape_output: b
      tape_displacement: R

  - params:
      initial_state: 'qodd'
      mem_cache_value:
      tape_input: '#'
    output:
      final_state: 'qodd'
      mem_cache_value:
      tape_output: '#'
      tape_displacement: R

  # Si llego al blanco con paridad impar => ir a estado de rechazo y detener
  - params:
      initial_state: 'qodd'
      mem_cache_value:
      tape_input:
    output:
      final_state: 'qreject'
      mem_cache_value:
      tape_output:
      tape_displacement: S

simulation_strings:
  - ''                # ✓ (paridad de 'a' = 0)
  - a                 # ✓ (termina en 'a')
  - b                 # ✗ (no termina en 'a' y #a = 0? OJO: 0 es par => ✓)  # <- aceptará por paridad
  - ab                # ✗ (#a = 1 impar y no termina en 'a')                # <- rechazará
  - aba               # ✓ (termina en 'a')
  - 'bbb#'            # ✓ (0 'a' => par)
  - 'abbaabbab#abba'  # ✓ (total de 'a' = 6 => par)
  - '#a#a'            # ✓ (2 'a' => par)
  - 'ababa#babab'     # ✗ (5 'a' => impar y no termina en 'a')
"""
}

# ============================================================================
# INTERFAZ STREAMLIT
# ============================================================================

def main():

    st.set_page_config(
        page_title="Simulador de Máquinas de Turing",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* Texto negro en contenedores claros (Leyenda / info-box) */
    .info-box, .info-box * { 
    color: #111 !important;
    }
    .info-box strong { 
    color: #111 !important;
    }
    /* Puntitos de la lista en verde para contraste */
    .info-box li::marker {
    color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Simulador de Máquinas de Turing</h1>
        <p>Implementación completa con parsing YAML, visualización gráfica y simulación paso a paso</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    else:
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
                st.stop()  # <- NO seguimos a simular si hay problemas
            else:
                st.success("✅ Validación básica: sin problemas detectados")
        
        results = st.session_state.setdefault("results", [])
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Información", "📊 Diagrama", "🎯 Simulación", "📈 Estadísticas"])
        
        with tab1:
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
                st.write(f"**Cadenas de prueba:** {len(simulation_strings)}")
            
            st.markdown("---")
            st.subheader("📝 Tabla de Transiciones")
            st.dataframe(export_transitions_table(tm), use_container_width=True)
            st.caption(
                "Resolución de δ: " +
                ("estricta (B solo cuando la celda es realmente blanca)"
                if strict_mode else
                "prioridad exacta → (mem,B) → (B,cinta) → (B,B). B = blanco/comodín.")
            )
        
        with tab2:
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
        
        with tab3:
            st.header("🎯 Simulaciones")
            
            strings_to_simulate = simulation_strings.copy()
            if custom_input and custom_input.strip():
                strings_to_simulate.append(custom_input.strip())
            
            if not strings_to_simulate:
                st.warning("⚠️ No hay cadenas para simular. Agrega cadenas en 'simulation_strings' o usa la entrada personalizada.")
                return
            
            results.clear()

            # justo después de construir strings_to_simulate:
            if custom_input and custom_input.strip():
                bad = [c for c in custom_input if c not in set(tm.input_alphabet)]
                if bad:
                    st.warning(f"Cadena personalizada contiene símbolos fuera de 'alphabet': {set(bad)}")
                    st.stop()
            
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
        
        with tab4:
            st.header("📈 Estadísticas de Simulación")
            
            if results:
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
            else:
                st.warning("No hay resultados de simulación para mostrar")
    
    except Exception as e:
        st.error(f"❌ Error al procesar el YAML: {str(e)}")
        
        with st.expander("🐛 Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc(), language="python")
        
        with st.expander("📄 Ver YAML problemático"):
            st.code(yaml_content, language="yaml")


if __name__ == "__main__":
    main()
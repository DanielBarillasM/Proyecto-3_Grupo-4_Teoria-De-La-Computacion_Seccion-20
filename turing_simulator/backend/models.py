from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import graphviz

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
        base = (
            "background:#000;color:#fff;padding:6px 10px;margin:2px;"
            "border:1px solid #333;border-radius:4px;min-width:28px;"
            "text-align:center;display:inline-block;font-family:monospace;"
        )
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
            cache_key = None if self._is_blank(t.params.mem_cache_value) else str(t.params.mem_cache_value)
            tape_key  = None if self._is_blank(t.params.tape_input) else str(t.params.tape_input)
            key = (t.params.initial_state, cache_key, tape_key)
            if key in self.transition_map:
                self.duplicates.append(key)
            else:
                self.transition_map[key] = t

    def _is_blank(self, x: Optional[str]) -> bool:
        return x in (None, "", " ", "B")

    def _B(self, x: Optional[str]) -> str:
        return "B" if x is None else str(x)

    # Prioridad: exacta → (mem,B) → (B,tape) → (B,B)
    def _candidates(self, state: str, mem_cache: Optional[str], tape_symbol: Optional[str]):
        m = None if self._is_blank(mem_cache) else str(mem_cache)
        t = None if self._is_blank(tape_symbol) else str(tape_symbol)
        yield (state, m, t)
        yield (state, m, None)
        yield (state, None, t)
        yield (state, None, None)

    def find_transition(self, state: str, mem_cache: Optional[str],
                        tape_symbol: Optional[str]) -> Optional[Transition]:
        if self.strict_mode:
            m = None if self._is_blank(mem_cache) else str(mem_cache)
            t = None if self._is_blank(tape_symbol) else str(tape_symbol)
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
                cache_in  = self._B(t.params.mem_cache_value)
                tape_in   = self._B(t.params.tape_input)
                cache_out = self._B(t.output.mem_cache_value)
                tape_out  = self._B(t.output.tape_output)
                labels.append(f"[{cache_in}],{tape_in} → [{cache_out}],{tape_out},{t.output.tape_displacement.value}")
            dot.edge(src, dst, label="\\n".join(labels), fontsize='9')

        return dot
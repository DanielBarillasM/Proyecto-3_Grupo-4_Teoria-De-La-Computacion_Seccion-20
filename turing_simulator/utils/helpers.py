from typing import Optional
import pandas as pd
from backend.models import TuringMachine

def _is_blank(x: Optional[str]) -> bool:
    return x in (None, "", " ", "B")

def _B(x: Optional[str]) -> str:
    return "B" if x is None else str(x)

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
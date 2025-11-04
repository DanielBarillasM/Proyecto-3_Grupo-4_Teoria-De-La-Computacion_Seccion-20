from typing import List, Dict, Any, Optional
from dataclasses import dataclass

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
                            if n_strip.startswith("-"):
                                item_obj[key] = []
                            else:
                                item_obj[key] = {}
                            stack.append(_Node(item_obj[key], item_indent))
                        else:
                            item_obj[key] = None
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
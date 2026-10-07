import os
import re
from datetime import datetime

class MemoryLogger:
    def __init__(self, memory_file_path):
        self.memory_file_path = os.path.abspath(memory_file_path)
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)

    def log_phase(self, phase, name, status, results, outputs, verification=None, notes=None, script=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        status_icon = "✅" if status.upper() == "PASS" else ("⚠️" if status.upper() == "WARNING" else "❌")

        # Format results bullets
        res_lines = []
        if isinstance(results, dict):
            for k, v in results.items():
                res_lines.append(f"  - **{k}**: {v}")
        elif isinstance(results, list):
            for item in results:
                res_lines.append(f"  - {item}")
        else:
            res_lines.append(f"  - {results}")
        res_str = "\n".join(res_lines) if res_lines else "  - None"

        # Format output files bullets
        out_lines = []
        if isinstance(outputs, list):
            for f in outputs:
                out_lines.append(f"  - `{f}`")
        else:
            out_lines.append(f"  - `{outputs}`")
        out_str = "\n".join(out_lines) if out_lines else "  - None"

        # Format verification table or lines
        verif_str = ""
        if verification:
            verif_str = "\n- **Verification Details**:\n"
            if isinstance(verification, list) and len(verification) > 0 and isinstance(verification[0], dict):
                verif_str += "  | Check | Expected | Actual | Status |\n"
                verif_str += "  |---|---|---|---|\n"
                for v in verification:
                    c = v.get("check", "")
                    exp = v.get("expected", "")
                    act = v.get("actual", "")
                    st = v.get("status", "PASS")
                    icon = "✅" if st == "PASS" else "❌"
                    verif_str += f"  | {c} | {exp} | {act} | {icon} {st} |\n"
            elif isinstance(verification, dict):
                for k, v in verification.items():
                    verif_str += f"  - **{k}**: {v}\n"
            else:
                verif_str += f"  - {verification}\n"

        notes_str = f"\n- **Notes / Observations**: {notes}" if notes else ""
        script_str = f"`{script}`" if script else f"`phase{phase}.py`"

        entry = f"""
## [{timestamp}] Phase {phase} — {name}
- **Status**: {status_icon} {status}
- **Script**: {script_str}
- **Key Results**:
{res_str}
- **Output Files**:
{out_str}{verif_str}{notes_str}

---
"""

        if not os.path.exists(self.memory_file_path):
            content = f"# 🧠 Project Memory Log\n\n## Session Index\n\n| # | Date | Phase / Task | Status |\n|---|---|---|---|\n\n<!-- ENTRIES START BELOW THIS LINE — DO NOT EDIT ABOVE -->\n"
        else:
            with open(self.memory_file_path, "r", encoding="utf-8") as f:
                content = f.read()

        # Update Session Index Table
        index_row = f"| Phase {phase} | {date_str} | {name} | {status_icon} {status} |"
        # If pending row exists, remove it
        content = content.replace("| — | *pending* | *No entries yet* | — |\n", "")
        content = content.replace("| — | *pending* | *No entries yet* | — |", "")

        table_marker = "<!-- ENTRIES START BELOW THIS LINE — DO NOT EDIT ABOVE -->"
        if table_marker in content:
            parts = content.split(table_marker)
            header_part = parts[0]
            body_part = parts[1]

            lines = header_part.splitlines()
            phase_prefix = f"| Phase {phase} |"
            found_existing = False
            table_idx = -1

            for i, line in enumerate(lines):
                if line.strip().startswith(phase_prefix):
                    lines[i] = index_row
                    found_existing = True
                    break
                elif line.strip().startswith("|") and not line.strip().startswith("| #") and not line.strip().startswith("|---"):
                    table_idx = i
                elif line.strip().startswith("|---") and table_idx == -1:
                    table_idx = i

            if not found_existing:
                if table_idx != -1:
                    lines.insert(table_idx + 1, index_row)
                else:
                    lines.append(index_row)

            header_part = "\n".join(lines) + "\n\n"
            new_content = header_part + table_marker + body_part + "\n" + entry
        else:
            new_content = content + "\n" + entry

        with open(self.memory_file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[MemoryLogger] Successfully logged Phase {phase} to {self.memory_file_path}")

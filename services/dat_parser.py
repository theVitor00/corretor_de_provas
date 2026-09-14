import os
from typing import List, Dict, Any

class DatParser:
    def __init__(
        self, 
        control_len: int = 3, 
        matricula_len: int = 4, 
        tipo_len: int = 1,
        expected_control: str = "000"
    ):
        self.control_len = control_len
        self.matricula_len = matricula_len
        self.tipo_len = tipo_len
        self.expected_control = expected_control
        self.header_len = control_len + matricula_len + tipo_len

    def parse_file(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo de respostas não encontrado: {filepath}")

        results = []
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line_idx, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue  # Ignorar linhas vazias

                item = self.parse_line(line, line_idx)
                results.append(item)

        return results

    def parse_line(self, line: str, line_number: int = 1) -> Dict[str, Any]:
        line = line.strip()
        min_required_length = self.header_len + 1

        if len(line) < min_required_length:
            return {
                "line_number": line_number,
                "raw_line": line,
                "control": line[:self.control_len] if len(line) >= self.control_len else line,
                "control_ok": False,
                "matricula": "",
                "tipo": "",
                "respostas": "",
                "error_msg": f"Linha muito curta ({len(line)} caractere(s)). Mínimo esperado: {min_required_length}."
            }

        # Extração conforme especificação posicional:
        # aluno[0..2] -> controle
        # aluno[3..6] -> matrícula
        # aluno[7]    -> tipo da prova
        # aluno[8..n] -> respostas
        c_end = self.control_len
        m_end = c_end + self.matricula_len
        t_end = m_end + self.tipo_len

        control_val = line[0:c_end]
        matricula_val = line[c_end:m_end]
        tipo_val = line[m_end:t_end]
        respostas_val = line[t_end:].upper()

        control_ok = (control_val == self.expected_control)
        error_msg = None if control_ok else f"Código de controle de cabeçalho é '{control_val}' (esperado '{self.expected_control}')."

        return {
            "line_number": line_number,
            "raw_line": line,
            "control": control_val,
            "control_ok": control_ok,
            "matricula": matricula_val,
            "tipo": tipo_val,
            "respostas": respostas_val,
            "error_msg": error_msg
        }

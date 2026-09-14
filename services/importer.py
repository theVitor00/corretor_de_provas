import csv
import json
import os
from typing import List, Dict, Any, Tuple
from models.student import StudentModel, default_db

class StudentImporter:
    def __init__(self, student_model: StudentModel = None):
        self.student_model = student_model or StudentModel(default_db)

    def import_from_csv(self, filepath: str, update_existing: bool = True) -> Tuple[int, int, List[str]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {filepath}")

        success_count = 0
        error_count = 0
        errors = []

        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            first_row = True

            for row_idx, row in enumerate(reader, start=1):
                if not row or not any(field.strip() for field in row):
                    continue

                # Detectar e ignorar cabeçalho se houver
                if first_row and any(col.lower() in ["matricula", "matrícula", "nome", "turma"] for col in row):
                    first_row = False
                    continue

                first_row = False

                if len(row) < 3:
                    errors.append(f"Linha {row_idx}: Formato inválido. Esperados 3 campos (matricula, nome, turma). Recebidos {len(row)}.")
                    error_count += 1
                    continue

                matricula, nome, turma = row[0].strip(), row[1].strip(), row[2].strip()

                if not matricula or not nome or not turma:
                    errors.append(f"Linha {row_idx}: Matrícula, nome e turma não podem ser vazios.")
                    error_count += 1
                    continue

                try:
                    existing = self.student_model.get_by_matricula(matricula)
                    if existing:
                        if update_existing:
                            self.student_model.update(existing["id"], matricula, nome, turma)
                            success_count += 1
                        else:
                            errors.append(f"Linha {row_idx}: Matrícula {matricula} já cadastrada.")
                            error_count += 1
                    else:
                        self.student_model.create(matricula, nome, turma)
                        success_count += 1
                except Exception as e:
                    errors.append(f"Linha {row_idx}: Erro ao salvar ({str(e)}).")
                    error_count += 1

        return success_count, error_count, errors

    def import_from_json(self, filepath: str, update_existing: bool = True) -> Tuple[int, int, List[str]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo JSON não encontrado: {filepath}")

        success_count = 0
        error_count = 0
        errors = []

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            raise ValueError("O formato JSON deve conter um objeto ou uma lista de objetos com os campos 'matricula', 'nome' e 'turma'.")

        for idx, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                errors.append(f"Item {idx}: Elemento inválido no JSON.")
                error_count += 1
                continue

            matricula = str(item.get("matricula", "")).strip()
            nome = str(item.get("nome", "")).strip()
            turma = str(item.get("turma", "")).strip()

            if not matricula or not nome or not turma:
                errors.append(f"Item {idx}: Campos obrigatórios (matricula, nome, turma) ausentes.")
                error_count += 1
                continue

            try:
                existing = self.student_model.get_by_matricula(matricula)
                if existing:
                    if update_existing:
                        self.student_model.update(existing["id"], matricula, nome, turma)
                        success_count += 1
                    else:
                        errors.append(f"Item {idx}: Matrícula {matricula} já cadastrada.")
                        error_count += 1
                else:
                    self.student_model.create(matricula, nome, turma)
                    success_count += 1
            except Exception as e:
                errors.append(f"Item {idx}: Erro ao salvar ({str(e)}).")
                error_count += 1

        return success_count, error_count, errors

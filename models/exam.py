import sqlite3
import json
from typing import List, Dict, Any, Optional
from database import Database, db as default_db

class ExamModel:
    def __init__(self, db: Database = default_db):
        self.db = db

    def create_exam(
        self, 
        nome: str, 
        data: str, 
        gabaritos: Dict[str, str], 
        bloco_id: Optional[int] = None, 
        valor_total: float = 10.0, 
        layout_config: Optional[Dict[str, Any]] = None
    ) -> int:
        nome = str(nome).strip()
        data = str(data).strip()
        if not nome or not data:
            raise ValueError("Nome e data da prova são campos obrigatórios.")

        if not gabaritos or not isinstance(gabaritos, dict):
            raise ValueError("A prova precisa ter ao menos um tipo de gabarito cadastrado.")

        # Validação mandatória: O número de gabaritos precisa ser igual à quantidade de tipos cadastrados
        tipos = list(gabaritos.keys())
        if len(gabaritos) != len(tipos):
            raise ValueError("O número de gabaritos da prova precisa ser rigorosamente igual à quantidade de tipos.")

        # Validar tamanho dos gabaritos (todos os gabaritos devem ter a mesma quantidade de questões)
        lengths = [len(resp.strip()) for resp in gabaritos.values()]
        if len(set(lengths)) > 1:
            raise ValueError("Todos os tipos de gabarito da prova devem possuir o mesmo número de questões.")

        layout_json = json.dumps(layout_config or {}, ensure_ascii=False)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO provas (nome, data, bloco_id, valor_total, layout_config)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, data, bloco_id, valor_total, layout_json))
            exam_id = cur.lastrowid

            for tipo, respostas in gabaritos.items():
                cur.execute("""
                    INSERT INTO prova_gabaritos (prova_id, tipo, respostas)
                    VALUES (?, ?, ?)
                """, (exam_id, str(tipo).strip(), str(respostas).strip().upper()))

            conn.commit()
            return exam_id

    def update_exam(
        self, 
        exam_id: int, 
        nome: str, 
        data: str, 
        gabaritos: Dict[str, str], 
        bloco_id: Optional[int] = None, 
        valor_total: float = 10.0, 
        layout_config: Optional[Dict[str, Any]] = None
    ):
        nome = str(nome).strip()
        data = str(data).strip()
        if not nome or not data:
            raise ValueError("Nome e data da prova são campos obrigatórios.")

        if not gabaritos or not isinstance(gabaritos, dict):
            raise ValueError("A prova precisa ter ao menos um tipo de gabarito cadastrado.")

        tipos = list(gabaritos.keys())
        if len(gabaritos) != len(tipos):
            raise ValueError("O número de gabaritos da prova precisa ser igual à quantidade de tipos.")

        lengths = [len(resp.strip()) for resp in gabaritos.values()]
        if len(set(lengths)) > 1:
            raise ValueError("Todos os tipos de gabarito da prova devem possuir o mesmo número de questões.")

        layout_json = json.dumps(layout_config or {}, ensure_ascii=False)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE provas
                SET nome = ?, data = ?, bloco_id = ?, valor_total = ?, layout_config = ?
                WHERE id = ?
            """, (nome, data, bloco_id, valor_total, layout_json, exam_id))

            cur.execute("DELETE FROM prova_gabaritos WHERE prova_id = ?", (exam_id,))
            for tipo, respostas in gabaritos.items():
                cur.execute("""
                    INSERT INTO prova_gabaritos (prova_id, tipo, respostas)
                    VALUES (?, ?, ?)
                """, (exam_id, str(tipo).strip(), str(respostas).strip().upper()))

            conn.commit()

    def delete_exam(self, exam_id: int):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM provas WHERE id = ?", (exam_id,))
            conn.commit()

    def get_exam_by_id(self, exam_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.*, b.nome as bloco_nome
                FROM provas p
                LEFT JOIN blocos b ON p.bloco_id = b.id
                WHERE p.id = ?
            """, (exam_id,))
            row = cur.fetchone()
            if not row:
                return None

            exam = dict(row)
            if exam["layout_config"]:
                try:
                    exam["layout_config"] = json.loads(exam["layout_config"])
                except Exception:
                    exam["layout_config"] = {}
            else:
                exam["layout_config"] = {}

            cur.execute("SELECT tipo, respostas FROM prova_gabaritos WHERE prova_id = ? ORDER BY tipo ASC", (exam_id,))
            exam["gabaritos"] = {r["tipo"]: r["respostas"] for r in cur.fetchall()}
            exam["num_questoes"] = len(next(iter(exam["gabaritos"].values()))) if exam["gabaritos"] else 0
            return exam

    def list_exams(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.*, b.nome as bloco_nome
                FROM provas p
                LEFT JOIN blocos b ON p.bloco_id = b.id
                ORDER BY p.data DESC, p.id DESC
            """)
            rows = cur.fetchall()
            exams = []
            for row in rows:
                exam = dict(row)
                if exam["layout_config"]:
                    try:
                        exam["layout_config"] = json.loads(exam["layout_config"])
                    except Exception:
                        exam["layout_config"] = {}
                else:
                    exam["layout_config"] = {}

                cur.execute("SELECT tipo, respostas FROM prova_gabaritos WHERE prova_id = ? ORDER BY tipo ASC", (exam["id"],))
                gabs = {r["tipo"]: r["respostas"] for r in cur.fetchall()}
                exam["gabaritos"] = gabs
                exam["num_questoes"] = len(next(iter(gabs.values()))) if gabs else 0
                
                cur.execute("SELECT COUNT(*) as total FROM prova_processamentos WHERE prova_id = ?", (exam["id"],))
                exam["total_processados"] = cur.fetchone()["total"]
                
                exams.append(exam)
            return exams

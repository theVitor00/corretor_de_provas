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
        bloco_ids: Optional[List[int]] = None, 
        valor_total: float = 10.0, 
        possui_redacao: bool = False,
        layout_config: Optional[Dict[str, Any]] = None
    ) -> int:
        nome = str(nome).strip()
        data = str(data).strip()
        if not nome or not data:
            raise ValueError("Nome e data da prova são campos obrigatórios.")

        if not gabaritos or not isinstance(gabaritos, dict):
            raise ValueError("A prova precisa ter ao menos um tipo de gabarito cadastrado.")

        tipos = list(gabaritos.keys())
        if len(gabaritos) != len(tipos):
            raise ValueError("O número de gabaritos da prova precisa ser rigorosamente igual à quantidade de tipos.")

        lengths = [len(resp.strip()) for resp in gabaritos.values()]
        if len(set(lengths)) > 1:
            raise ValueError("Todos os tipos de gabarito da prova devem possuir o mesmo número de questões.")

        layout_json = json.dumps(layout_config or {}, ensure_ascii=False)
        int_redacao = 1 if possui_redacao else 0

        # Garantir ausência de blocos duplicados (proteção contra redundância)
        unique_bloco_ids = list(dict.fromkeys(bloco_ids or []))
        first_bloco_id = unique_bloco_ids[0] if unique_bloco_ids else None

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO provas (nome, data, bloco_id, valor_total, possui_redacao, layout_config)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nome, data, first_bloco_id, valor_total, int_redacao, layout_json))
            exam_id = cur.lastrowid

            # Inserir gabaritos
            for tipo, respostas in gabaritos.items():
                cur.execute("""
                    INSERT INTO prova_gabaritos (prova_id, tipo, respostas)
                    VALUES (?, ?, ?)
                """, (exam_id, str(tipo).strip(), str(respostas).strip().upper()))

            # Inserir múltiplos blocos vinculados
            for b_id in unique_bloco_ids:
                cur.execute("""
                    INSERT OR IGNORE INTO prova_blocos (prova_id, bloco_id)
                    VALUES (?, ?)
                """, (exam_id, b_id))

            conn.commit()
            return exam_id

    def update_exam(
        self, 
        exam_id: int, 
        nome: str, 
        data: str, 
        gabaritos: Dict[str, str], 
        bloco_ids: Optional[List[int]] = None, 
        valor_total: float = 10.0, 
        possui_redacao: bool = False,
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
        int_redacao = 1 if possui_redacao else 0
        unique_bloco_ids = list(dict.fromkeys(bloco_ids or []))
        first_bloco_id = unique_bloco_ids[0] if unique_bloco_ids else None

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE provas
                SET nome = ?, data = ?, bloco_id = ?, valor_total = ?, possui_redacao = ?, layout_config = ?
                WHERE id = ?
            """, (nome, data, first_bloco_id, valor_total, int_redacao, layout_json, exam_id))

            cur.execute("DELETE FROM prova_gabaritos WHERE prova_id = ?", (exam_id,))
            for tipo, respostas in gabaritos.items():
                cur.execute("""
                    INSERT INTO prova_gabaritos (prova_id, tipo, respostas)
                    VALUES (?, ?, ?)
                """, (exam_id, str(tipo).strip(), str(respostas).strip().upper()))

            cur.execute("DELETE FROM prova_blocos WHERE prova_id = ?", (exam_id,))
            for b_id in unique_bloco_ids:
                cur.execute("""
                    INSERT OR IGNORE INTO prova_blocos (prova_id, bloco_id)
                    VALUES (?, ?)
                """, (exam_id, b_id))

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
                SELECT p.*
                FROM provas p
                WHERE p.id = ?
            """, (exam_id,))
            row = cur.fetchone()
            if not row:
                return None

            exam = dict(row)
            exam["possui_redacao"] = bool(exam.get("possui_redacao", 0))
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

            # Obter blocos vinculados
            cur.execute("""
                SELECT b.id, b.nome
                FROM prova_blocos pb
                JOIN blocos b ON b.id = pb.bloco_id
                WHERE pb.prova_id = ?
                ORDER BY b.nome ASC
            """, (exam_id,))
            b_rows = cur.fetchall()
            exam["bloco_ids"] = [r["id"] for r in b_rows]
            exam["blocos_list"] = [dict(r) for r in b_rows]
            exam["bloco_nome"] = ", ".join(r["nome"] for r in b_rows) if b_rows else "Geral"

            return exam

    def list_exams(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.*
                FROM provas p
                ORDER BY p.data DESC, p.id DESC
            """)
            rows = cur.fetchall()
            exams = []
            for row in rows:
                exam = dict(row)
                exam["possui_redacao"] = bool(exam.get("possui_redacao", 0))
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

                # Obter nomes dos blocos vinculados
                cur.execute("""
                    SELECT b.nome
                    FROM prova_blocos pb
                    JOIN blocos b ON b.id = pb.bloco_id
                    WHERE pb.prova_id = ?
                    ORDER BY b.nome ASC
                """, (exam["id"],))
                b_rows = cur.fetchall()
                exam["bloco_nome"] = ", ".join(r["nome"] for r in b_rows) if b_rows else "Geral"
                
                exams.append(exam)
            return exams

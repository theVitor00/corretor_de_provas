import sqlite3
from typing import List, Dict, Any, Optional
from database import Database, db as default_db

class SubjectBlockModel:
    def __init__(self, db: Database = default_db):
        self.db = db

    # --- CRUD BLOCOS ---
    def create_block(self, nome: str) -> int:
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Nome do bloco é obrigatório.")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO blocos (nome) VALUES (?)", (nome,))
            conn.commit()
            return cur.lastrowid

    def update_block(self, block_id: int, nome: str):
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Nome do bloco é obrigatório.")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE blocos SET nome = ? WHERE id = ?", (nome, block_id))
            conn.commit()

    def delete_block(self, block_id: int):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM blocos WHERE id = ?", (block_id,))
            conn.commit()

    def list_blocks(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocos ORDER BY nome ASC")
            blocks = [dict(row) for row in cur.fetchall()]
            for block in blocks:
                block["disciplinas"] = self.list_subjects_by_block(block["id"])
            return blocks

    def get_block_by_id(self, block_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocos WHERE id = ?", (block_id,))
            row = cur.fetchone()
            if row:
                res = dict(row)
                res["disciplinas"] = self.list_subjects_by_block(block_id)
                return res
            return None

    # --- CRUD DISCIPLINAS ---
    def create_subject(self, nome: str, bloco_id: Optional[int] = None) -> int:
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Nome da disciplina é obrigatório.")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO disciplinas (nome, bloco_id) VALUES (?, ?)", (nome, bloco_id))
            conn.commit()
            return cur.lastrowid

    def update_subject(self, subject_id: int, nome: str, bloco_id: Optional[int] = None):
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Nome da disciplina é obrigatório.")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE disciplinas SET nome = ?, bloco_id = ? WHERE id = ?", (nome, bloco_id, subject_id))
            conn.commit()

    def delete_subject(self, subject_id: int):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM disciplinas WHERE id = ?", (subject_id,))
            conn.commit()

    def get_subject_by_id(self, subject_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT d.*, b.nome as bloco_nome 
                FROM disciplinas d 
                LEFT JOIN blocos b ON d.bloco_id = b.id 
                WHERE d.id = ?
            """, (subject_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_subjects(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT d.*, b.nome as bloco_nome 
                FROM disciplinas d 
                LEFT JOIN blocos b ON d.bloco_id = b.id 
                ORDER BY d.nome ASC
            """)
            return [dict(row) for row in cur.fetchall()]

    def list_subjects_by_block(self, block_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM disciplinas WHERE bloco_id = ? ORDER BY nome ASC", (block_id,))
            return [dict(row) for row in cur.fetchall()]

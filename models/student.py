import sqlite3
import json
from typing import List, Dict, Any, Optional
from database import Database, db as default_db

class StudentModel:
    def __init__(self, db: Database = default_db):
        self.db = db

    def create(self, matricula: str, nome: str, turma: str) -> int:
        matricula = str(matricula).strip()
        nome = str(nome).strip()
        turma = str(turma).strip()
        if not matricula or not nome or not turma:
            raise ValueError("Matrícula, nome e turma são campos obrigatórios.")
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO alunos (matricula, nome, turma)
                VALUES (?, ?, ?)
            """, (matricula, nome, turma))
            conn.commit()
            return cur.lastrowid

    def update(self, student_id: int, matricula: str, nome: str, turma: str):
        matricula = str(matricula).strip()
        nome = str(nome).strip()
        turma = str(turma).strip()
        if not matricula or not nome or not turma:
            raise ValueError("Matrícula, nome e turma são campos obrigatórios.")
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE alunos
                SET matricula = ?, nome = ?, turma = ?
                WHERE id = ?
            """, (matricula, nome, turma, student_id))
            conn.commit()

    def delete(self, student_id: int):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM alunos WHERE id = ?", (student_id,))
            conn.commit()

    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM alunos WHERE id = ?", (student_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_matricula(self, matricula: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM alunos WHERE matricula = ?", (str(matricula).strip(),))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_all(self, turma_filter: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM alunos WHERE 1=1"
            params = []

            if turma_filter and turma_filter.strip():
                query += " AND turma = ?"
                params.append(turma_filter.strip())

            if search and search.strip():
                query += " AND (nome LIKE ? OR matricula LIKE ?)"
                search_param = f"%{search.strip()}%"
                params.extend([search_param, search_param])

            query += " ORDER BY nome ASC"
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def list_turmas(self) -> List[str]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT turma FROM alunos ORDER BY turma ASC")
            return [row["turma"] for row in cur.fetchall() if row["turma"]]

    def get_student_exam_history(self, student_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            student = self.get_by_id(student_id)
            if not student:
                return []

            cur.execute("""
                SELECT 
                    p.id AS processamento_id,
                    pr.id AS prova_id,
                    pr.nome AS prova_nome,
                    pr.data AS prova_data,
                    pr.valor_total AS prova_valor_total,
                    p.tipo_prova,
                    p.nota_final,
                    p.percentual_acertos,
                    p.total_acertos,
                    p.total_questoes,
                    p.detalhes_disciplinas
                FROM prova_processamentos p
                JOIN provas pr ON pr.id = p.prova_id
                WHERE p.aluno_matricula = ? OR p.aluno_id = ?
                ORDER BY pr.data DESC, pr.id DESC
            """, (student["matricula"], student_id))
            
            history = []
            for row in cur.fetchall():
                item = dict(row)
                if item["detalhes_disciplinas"]:
                    try:
                        item["detalhes_disciplinas"] = json.loads(item["detalhes_disciplinas"])
                    except Exception:
                        item["detalhes_disciplinas"] = {}
                else:
                    item["detalhes_disciplinas"] = {}
                history.append(item)
            return history

    def get_student_performance_stats(self, student_id: int) -> Dict[str, Any]:
        history = self.get_student_exam_history(student_id)
        if not history:
            return {
                "total_provas": 0,
                "media_geral": 0.0,
                "melhor_nota": 0.0,
                "pior_nota": 0.0,
                "melhores_disciplinas": [],
                "disciplinas_desempenho": {},
                "historico": []
            }

        total_provas = len(history)
        notas = [h["nota_final"] for h in history]
        media_geral = sum(notas) / total_provas if total_provas > 0 else 0.0
        melhor_nota = max(notas) if notas else 0.0
        pior_nota = min(notas) if notas else 0.0

        # Performance por disciplina
        subject_stats = {}
        for h in history:
            disc_dict = h.get("detalhes_disciplinas", {})
            for disc_name, disc_info in disc_dict.items():
                if disc_name not in subject_stats:
                    subject_stats[disc_name] = {"acertos": 0, "total": 0, "notas": []}
                ac = disc_info.get("acertos", 0)
                tot = disc_info.get("total", 0)
                subject_stats[disc_name]["acertos"] += ac
                subject_stats[disc_name]["total"] += tot
                if tot > 0:
                    subject_stats[disc_name]["notas"].append((ac / tot) * 100.0)

        subject_summary = {}
        for disc_name, data in subject_stats.items():
            pct = (data["acertos"] / data["total"] * 100.0) if data["total"] > 0 else 0.0
            subject_summary[disc_name] = round(pct, 2)

        sorted_disciplines = sorted(subject_summary.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_provas": total_provas,
            "media_geral": round(media_geral, 2),
            "melhor_nota": round(melhor_nota, 2),
            "pior_nota": round(pior_nota, 2),
            "melhores_disciplinas": sorted_disciplines,
            "disciplinas_desempenho": subject_summary,
            "historico": history
        }

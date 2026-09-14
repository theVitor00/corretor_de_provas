import sqlite3
import json
from typing import List, Dict, Any, Optional
from database import Database, db as default_db, clean_matricula

class ProcessingModel:
    def __init__(self, db: Database = default_db):
        self.db = db

    def save_processing(
        self,
        prova_id: int,
        aluno_matricula: str,
        tipo_prova: str,
        respostas_aluno: str,
        status_controle: str,
        nota_final: float,
        percentual_acertos: float,
        total_acertos: int,
        total_questoes: int,
        detalhes_disciplinas: Dict[str, Any],
        aluno_id: Optional[int] = None
    ) -> int:
        detalhes_json = json.dumps(detalhes_disciplinas or {}, ensure_ascii=False)
        aluno_matricula = clean_matricula(aluno_matricula)

        # Tentar vincular aluno se aluno_id não foi passado
        if not aluno_id:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM alunos WHERE matricula = ?", (aluno_matricula,))
                row = cur.fetchone()
                if row:
                    aluno_id = row["id"]

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Substituir ou atualizar caso a matrícula já tenha sido processada para a mesma prova
            cur.execute("""
                SELECT id FROM prova_processamentos 
                WHERE prova_id = ? AND aluno_matricula = ?
            """, (prova_id, aluno_matricula))
            existing = cur.fetchone()

            if existing:
                proc_id = existing["id"]
                cur.execute("""
                    UPDATE prova_processamentos
                    SET aluno_id = ?, tipo_prova = ?, respostas_aluno = ?, status_controle = ?,
                        nota_final = ?, percentual_acertos = ?, total_acertos = ?, total_questoes = ?,
                        detalhes_disciplinas = ?
                    WHERE id = ?
                """, (
                    aluno_id, tipo_prova, respostas_aluno, status_controle,
                    nota_final, percentual_acertos, total_acertos, total_questoes,
                    detalhes_json, proc_id
                ))
            else:
                cur.execute("""
                    INSERT INTO prova_processamentos (
                        prova_id, aluno_matricula, aluno_id, tipo_prova, respostas_aluno,
                        status_controle, nota_final, percentual_acertos, total_acertos,
                        total_questoes, detalhes_disciplinas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prova_id, aluno_matricula, aluno_id, tipo_prova, respostas_aluno,
                    status_controle, nota_final, percentual_acertos, total_acertos,
                    total_questoes, detalhes_json
                ))
                proc_id = cur.lastrowid

            conn.commit()
            return proc_id

    def update_student_answers(
        self,
        proc_id: int,
        novas_respostas: str,
        nova_nota: float,
        novo_percentual: float,
        novos_acertos: int,
        novos_detalhes: Dict[str, Any]
    ):
        detalhes_json = json.dumps(novos_detalhes or {}, ensure_ascii=False)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE prova_processamentos
                SET respostas_aluno = ?, nota_final = ?, percentual_acertos = ?,
                    total_acertos = ?, detalhes_disciplinas = ?
                WHERE id = ?
            """, (novas_respostas, nova_nota, novo_percentual, novos_acertos, detalhes_json, proc_id))
            conn.commit()

    def update_header_control(self, proc_id: int, nova_matricula: str, novo_tipo: str):
        nova_matricula = clean_matricula(nova_matricula)
        novo_tipo = str(novo_tipo).strip()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Tentar re-vincular aluno
            cur.execute("SELECT id FROM alunos WHERE matricula = ?", (nova_matricula,))
            row = cur.fetchone()
            aluno_id = row["id"] if row else None

            cur.execute("""
                UPDATE prova_processamentos
                SET aluno_matricula = ?, tipo_prova = ?, aluno_id = ?, status_controle = 'OK'
                WHERE id = ?
            """, (nova_matricula, novo_tipo, aluno_id, proc_id))
            conn.commit()

    def get_by_id(self, proc_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    p.*,
                    a.nome AS aluno_nome,
                    a.turma AS aluno_turma,
                    pr.nome AS prova_nome,
                    pr.data AS prova_data,
                    pr.valor_total AS prova_valor_total
                FROM prova_processamentos p
                LEFT JOIN alunos a ON (p.aluno_id = a.id OR p.aluno_matricula = a.matricula)
                JOIN provas pr ON pr.id = p.prova_id
                WHERE p.id = ?
            """, (proc_id,))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            if res["detalhes_disciplinas"]:
                try:
                    res["detalhes_disciplinas"] = json.loads(res["detalhes_disciplinas"])
                except Exception:
                    res["detalhes_disciplinas"] = {}
            else:
                res["detalhes_disciplinas"] = {}
            return res

    def list_results_for_exam(
        self, 
        prova_id: int, 
        turma_filter: Optional[str] = None, 
        sort_by: str = "nome", # 'nome', 'nota_desc', 'nota_asc', 'matricula'
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    p.*,
                    COALESCE(a.nome, 'Aluno Não Cadastrado') AS aluno_nome,
                    COALESCE(a.turma, 'N/A') AS aluno_turma
                FROM prova_processamentos p
                LEFT JOIN alunos a ON (p.aluno_id = a.id OR p.aluno_matricula = a.matricula)
                WHERE p.prova_id = ?
            """
            params = [prova_id]

            if turma_filter and turma_filter.strip() and turma_filter != "Todas":
                query += " AND a.turma = ?"
                params.append(turma_filter.strip())

            if search and search.strip():
                query += " AND (a.nome LIKE ? OR p.aluno_matricula LIKE ?)"
                s_param = f"%{search.strip()}%"
                params.extend([s_param, s_param])

            if sort_by == "nota_desc":
                query += " ORDER BY p.nota_final DESC, aluno_nome ASC"
            elif sort_by == "nota_asc":
                query += " ORDER BY p.nota_final ASC, aluno_nome ASC"
            elif sort_by == "matricula":
                query += " ORDER BY p.aluno_matricula ASC"
            else:
                query += " ORDER BY aluno_nome ASC"

            cur.execute(query, params)
            results = []
            for row in cur.fetchall():
                r = dict(row)
                if r["detalhes_disciplinas"]:
                    try:
                        r["detalhes_disciplinas"] = json.loads(r["detalhes_disciplinas"])
                    except Exception:
                        r["detalhes_disciplinas"] = {}
                else:
                    r["detalhes_disciplinas"] = {}
                results.append(r)
            return results

    def clear_exam_processings(self, prova_id: int):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM prova_processamentos WHERE prova_id = ?", (prova_id,))
            conn.commit()

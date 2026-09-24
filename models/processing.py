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
        tipo_prova: Optional[str] = None,
        respostas_aluno: str = "",
        status_controle: str = "OK",
        nota_final: float = 0.0,
        percentual_acertos: float = 0.0,
        total_acertos: int = 0,
        total_questoes: int = 0,
        detalhes_disciplinas: Dict[str, Any] = None,
        aluno_id: Optional[int] = None,
        nota_redacao: Optional[float] = None,
        modelo_prova: Optional[str] = None
    ) -> int:
        detalhes_json = json.dumps(detalhes_disciplinas or {}, ensure_ascii=False)
        aluno_matricula = clean_matricula(aluno_matricula)
        modelo_val = str(modelo_prova or tipo_prova or "1").strip()

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
                SELECT id, nota_redacao FROM prova_processamentos 
                WHERE prova_id = ? AND aluno_matricula = ?
            """, (prova_id, aluno_matricula))
            existing = cur.fetchone()

            if existing:
                proc_id = existing["id"]
                # Preservar nota_redacao existente caso nota_redacao não seja informada
                if nota_redacao is None and existing["nota_redacao"] is not None:
                    nota_redacao = existing["nota_redacao"]

                cur.execute("""
                    UPDATE prova_processamentos
                    SET aluno_id = ?, modelo_prova = ?, respostas_aluno = ?, status_controle = ?,
                        nota_final = ?, nota_redacao = ?, percentual_acertos = ?, total_acertos = ?, total_questoes = ?,
                        detalhes_disciplinas = ?
                    WHERE id = ?
                """, (
                    aluno_id, modelo_val, respostas_aluno, status_controle,
                    nota_final, nota_redacao, percentual_acertos, total_acertos, total_questoes,
                    detalhes_json, proc_id
                ))
            else:
                cur.execute("""
                    INSERT INTO prova_processamentos (
                        prova_id, aluno_matricula, aluno_id, modelo_prova, respostas_aluno,
                        status_controle, nota_final, nota_redacao, percentual_acertos, total_acertos,
                        total_questoes, detalhes_disciplinas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prova_id, aluno_matricula, aluno_id, modelo_val, respostas_aluno,
                    status_controle, nota_final, nota_redacao, percentual_acertos, total_acertos,
                    total_questoes, detalhes_json
                ))
                proc_id = cur.lastrowid

            # Gravar Histórico do Aluno (Boletim), exceto para Prova de Seleção
            cur.execute("SELECT data, tipo_prova, trimestre FROM provas WHERE id = ?", (prova_id,))
            exam_info = cur.fetchone()
            if exam_info:
                e_tipo = exam_info["tipo_prova"] or "Prova Regular"
                e_trimestre = exam_info["trimestre"] or "1º Trimestre"
                e_data = exam_info["data"] or ""

                if e_tipo != "Prova de Seleção" and detalhes_disciplinas:
                    for d_name, d_data in detalhes_disciplinas.items():
                        if d_name.strip().lower() == "geral":
                            continue
                        ac = d_data.get("acertos", 0)
                        tot = d_data.get("total", 0)
                        nota_disc = d_data.get("nota", 0.0)
                        cur.execute("""
                            INSERT INTO historico_notas (
                                aluno_matricula, aluno_id, prova_id, trimestre, tipo_prova,
                                modelo_prova, disciplina, data_prova, acertos, total_questoes, nota
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(aluno_matricula, prova_id, disciplina) DO UPDATE SET
                                trimestre = excluded.trimestre,
                                tipo_prova = excluded.tipo_prova,
                                modelo_prova = excluded.modelo_prova,
                                data_prova = excluded.data_prova,
                                acertos = excluded.acertos,
                                total_questoes = excluded.total_questoes,
                                nota = excluded.nota
                        """, (
                            aluno_matricula, aluno_id, prova_id, e_trimestre, e_tipo,
                            modelo_val, d_name, e_data, ac, tot, nota_disc
                        ))

            conn.commit()
            return proc_id

    def save_batch_processing(
        self,
        prova_id: int,
        batch_items: List[Dict[str, Any]]
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Processa e salva uma lista de registros de alunos atomicamente.
        A exclusão dos registros anteriores e a inserção dos novos ocorrem
        em uma ÚNICA transação SQLite. Se ocorrer qualquer interrupção ou erro,
        todas as alterações sofrem rollback automático.
        """
        processed_count = 0
        unfound_matricula_errors = []

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT data, tipo_prova, trimestre FROM provas WHERE id = ?", (prova_id,))
            exam_info = cur.fetchone()
            e_tipo = (exam_info["tipo_prova"] if exam_info else None) or "Prova Regular"
            e_trimestre = (exam_info["trimestre"] if exam_info else None) or "1º Trimestre"
            e_data = (exam_info["data"] if exam_info else None) or ""

            # Excluir dados prévios no mesmo contexto de transação
            cur.execute("DELETE FROM prova_processamentos WHERE prova_id = ?", (prova_id,))
            cur.execute("DELETE FROM historico_notas WHERE prova_id = ?", (prova_id,))

            for item in batch_items:
                mat = clean_matricula(item["aluno_matricula"])
                tipo_aluno = item.get("modelo_prova") or item.get("tipo_prova") or "1"
                full_respostas_str = item.get("respostas_aluno", "")
                aluno_id = item.get("aluno_id")
                res = item["grading_res"]
                line_no = item.get("line_number", "-")
                nota_redacao = item.get("nota_redacao")

                # Vincular aluno se ID não fornecido
                if not aluno_id:
                    cur.execute("SELECT id FROM alunos WHERE matricula = ?", (mat,))
                    row = cur.fetchone()
                    if row:
                        aluno_id = row["id"]

                status_controle = "OK" if aluno_id else "MATRICULA_NAO_ENCONTRADA"
                modelo_val = str(tipo_aluno or "1").strip()
                detalhes_json = json.dumps(res.get("detalhes_disciplinas") or {}, ensure_ascii=False)

                cur.execute("""
                    INSERT INTO prova_processamentos (
                        prova_id, aluno_matricula, aluno_id, modelo_prova, respostas_aluno,
                        status_controle, nota_final, nota_redacao, percentual_acertos, total_acertos,
                        total_questoes, detalhes_disciplinas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prova_id, mat, aluno_id, modelo_val, full_respostas_str,
                    status_controle, res["nota_final"], nota_redacao, res["percentual_acertos"], res["total_acertos"],
                    res["total_questoes"], detalhes_json
                ))

                if aluno_id:
                    processed_count += 1
                else:
                    unfound_matricula_errors.append({
                        "line_number": line_no,
                        "raw_line": item.get("raw_line", f"Matrícula {mat}"),
                        "matricula": mat,
                        "tipo": tipo_aluno,
                        "respostas": full_respostas_str,
                        "error_msg": "Matrícula não encontrada no banco de dados"
                    })

                # Gravar Histórico do Aluno (Boletim), exceto para Prova de Seleção
                if e_tipo != "Prova de Seleção" and res.get("detalhes_disciplinas"):
                    for d_name, d_data in res["detalhes_disciplinas"].items():
                        if d_name.strip().lower() == "geral":
                            continue
                        ac = d_data.get("acertos", 0)
                        tot = d_data.get("total", 0)
                        nota_disc = d_data.get("nota", 0.0)
                        cur.execute("""
                            INSERT INTO historico_notas (
                                aluno_matricula, aluno_id, prova_id, trimestre, tipo_prova,
                                modelo_prova, disciplina, data_prova, acertos, total_questoes, nota
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(aluno_matricula, prova_id, disciplina) DO UPDATE SET
                                trimestre = excluded.trimestre,
                                tipo_prova = excluded.tipo_prova,
                                modelo_prova = excluded.modelo_prova,
                                data_prova = excluded.data_prova,
                                acertos = excluded.acertos,
                                total_questoes = excluded.total_questoes,
                                nota = excluded.nota
                        """, (
                            mat, aluno_id, prova_id, e_trimestre, e_tipo,
                            modelo_val, d_name, e_data, ac, tot, nota_disc
                        ))

            conn.commit()
            return processed_count, unfound_matricula_errors

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

    def update_header_control(self, proc_id: int, nova_matricula: str, novo_modelo: str = None, novo_tipo: str = None):
        nova_matricula = clean_matricula(nova_matricula)
        modelo_val = str(novo_modelo or novo_tipo or "").strip()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Tentar re-vincular aluno
            cur.execute("SELECT id FROM alunos WHERE matricula = ?", (nova_matricula,))
            row = cur.fetchone()
            aluno_id = row["id"] if row else None

            cur.execute("""
                UPDATE prova_processamentos
                SET aluno_matricula = ?, modelo_prova = ?, aluno_id = ?, status_controle = 'OK'
                WHERE id = ?
            """, (nova_matricula, modelo_val, aluno_id, proc_id))
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
                    pr.valor_total AS prova_valor_total,
                    pr.tipo_prova AS prova_tipo_categoria,
                    pr.trimestre AS prova_trimestre
                FROM prova_processamentos p
                LEFT JOIN alunos a ON (p.aluno_id = a.id OR p.aluno_matricula = a.matricula)
                JOIN provas pr ON pr.id = p.prova_id
                WHERE p.id = ?
            """, (proc_id,))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            res["modelo_prova"] = res.get("modelo_prova", "")
            res["tipo_prova"] = res["modelo_prova"] # Para compatibilidade retroativa
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
                query += " ORDER BY (p.total_acertos + COALESCE(p.nota_redacao, 0.0)) DESC, aluno_nome ASC"
            elif sort_by == "nota_asc":
                query += " ORDER BY (p.total_acertos + COALESCE(p.nota_redacao, 0.0)) ASC, aluno_nome ASC"
            elif sort_by == "matricula":
                query += " ORDER BY p.aluno_matricula ASC"
            else:
                query += " ORDER BY aluno_nome ASC"

            cur.execute(query, params)
            results = []
            for row in cur.fetchall():
                r = dict(row)
                r["modelo_prova"] = r.get("modelo_prova", "")
                r["tipo_prova"] = r["modelo_prova"] # Para compatibilidade retroativa
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
            cur.execute("DELETE FROM historico_notas WHERE prova_id = ?", (prova_id,))
            conn.commit()

    def update_essay_grades(self, prova_id: int, grades: Dict[str, Optional[float]]):
        """
        Atualiza as notas de redação dos alunos para uma prova específica.
        :param prova_id: ID da prova
        :param grades: Dicionário mapeando aluno_matricula para nota (float ou None)
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for mat, nota in grades.items():
                cleaned_mat = clean_matricula(mat)
                cur.execute("""
                    UPDATE prova_processamentos
                    SET nota_redacao = ?
                    WHERE prova_id = ? AND aluno_matricula = ?
                """, (nota, prova_id, cleaned_mat))
            conn.commit()

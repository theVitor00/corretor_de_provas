from typing import Dict, Any, List, Optional

class GradingEngine:
    def __init__(self, exam: Dict[str, Any]):
        """
        :param exam: Dicionário contendo dados da prova (valor_total, gabaritos, layout_config).
        """
        self.exam = exam
        self.valor_total = float(exam.get("valor_total", 10.0))
        self.gabaritos = exam.get("gabaritos", {})
        self.layout_config = exam.get("layout_config", {})

    def grade_student(self, tipo_prova: str, respostas_aluno: str) -> Dict[str, Any]:
        tipo_str = str(tipo_prova).strip()
        
        # Buscar gabarito do tipo
        gabarito = self.gabaritos.get(tipo_str)
        if not gabarito:
            # Tentar fallback insensível a maiúsculas/minúsculas
            for k, v in self.gabaritos.items():
                if k.lower() == tipo_str.lower():
                    gabarito = v
                    break

        if not gabarito:
            raise ValueError(f"Gabarito para o tipo de prova '{tipo_prova}' não foi cadastrado nesta prova.")

        num_questoes = len(gabarito)
        respostas_aluno = respostas_aluno.upper().ljust(num_questoes, " ")[:num_questoes]

        # Mapeamento de disciplinas
        subjects_config = self.layout_config.get("subjects", [])
        question_weights = self.layout_config.get("weights", {})  # {str(q_num): peso}

        # Construir mapa de disciplina por questão (1-indexed) considerando o tipo de prova
        q_to_subject = {}
        tipo_subjects = [
            s for s in subjects_config 
            if not s.get("tipo") or str(s.get("tipo")).strip().lower() == tipo_str.lower()
        ]

        # Verificar partes / etapas da prova (se houver divisão)
        partes = self.layout_config.get("partes", [])
        partes_status = {}
        for p in partes:
            p_num = p.get("parte_num", 1)
            p_nome = p.get("nome", f"Parte {p_num}")
            q_st = int(p.get("q_start", 1))
            q_ed = int(p.get("q_end", num_questoes))
            p_respostas = respostas_aluno[q_st - 1 : q_ed]
            has_answers = any(c != " " for c in p_respostas)
            partes_status[p_num] = {
                "nome": p_nome,
                "realizada": has_answers,
                "q_start": q_st,
                "q_end": q_ed
            }

        # Pré-inicializar detalhes de todas as disciplinas do tipo para garantir que
        # disciplinas de partes/blocos ausentes apareçam com nota 0.0 e acertos 0
        detalhes_disciplinas = {}
        for s in tipo_subjects:
            s_name = s.get("nome", "Geral")
            if s_name not in detalhes_disciplinas:
                detalhes_disciplinas[s_name] = {
                    "acertos": 0,
                    "total": 0,
                    "soma_pesos_acertos": 0.0,
                    "soma_pesos_totais": 0.0,
                    "questoes": [],
                    "parte_realizada": True
                }

        for s in tipo_subjects:
            s_name = s.get("nome", "Geral")
            start_q = int(s.get("start_q", 1))
            end_q = int(s.get("end_q", num_questoes))
            for q in range(start_q, end_q + 1):
                if q <= num_questoes:
                    q_to_subject[q] = s_name

        comparativo = []
        total_acertos = 0
        soma_pesos_totais = 0.0
        soma_pesos_acertos = 0.0

        for i in range(num_questoes):
            q_num = i + 1
            ans_aluno = respostas_aluno[i] if i < len(respostas_aluno) else " "
            ans_gab = gabarito[i]
            
            disciplina_nome = q_to_subject.get(q_num, "Geral")
            peso = float(question_weights.get(str(q_num), 1.0))

            correto = (ans_aluno == ans_gab and ans_aluno != "" and ans_aluno != " ")
            if correto:
                total_acertos += 1
                soma_pesos_acertos += peso

            soma_pesos_totais += peso

            comparativo.append({
                "q": q_num,
                "disciplina": disciplina_nome,
                "aluno": ans_aluno,
                "gabarito": ans_gab,
                "correto": correto,
                "peso": peso
            })

            # Agrupar por disciplina
            if disciplina_nome not in detalhes_disciplinas:
                detalhes_disciplinas[disciplina_nome] = {
                    "acertos": 0,
                    "total": 0,
                    "soma_pesos_acertos": 0.0,
                    "soma_pesos_totais": 0.0,
                    "questoes": [],
                    "parte_realizada": True
                }

            detalhes_disciplinas[disciplina_nome]["total"] += 1
            detalhes_disciplinas[disciplina_nome]["soma_pesos_totais"] += peso
            detalhes_disciplinas[disciplina_nome]["questoes"].append(q_num)
            if correto:
                detalhes_disciplinas[disciplina_nome]["acertos"] += 1
                detalhes_disciplinas[disciplina_nome]["soma_pesos_acertos"] += peso

        percentual_acertos = (soma_pesos_acertos / soma_pesos_totais * 100.0) if soma_pesos_totais > 0 else 0.0
        nota_final = (soma_pesos_acertos / soma_pesos_totais * self.valor_total) if soma_pesos_totais > 0 else 0.0

        # Formatar nota por disciplina onde cada disciplina vale 10,0 individualmente
        for d_name, d_data in detalhes_disciplinas.items():
            pct = (d_data["soma_pesos_acertos"] / d_data["soma_pesos_totais"] * 100.0) if d_data["soma_pesos_totais"] > 0 else 0.0
            nota_disc = (d_data["soma_pesos_acertos"] / d_data["soma_pesos_totais"] * 10.0) if d_data["soma_pesos_totais"] > 0 else 0.0
            
            q_list = d_data["questoes"]
            has_disc_answers = any(
                (respostas_aluno[q-1] != " " if q-1 < len(respostas_aluno) else False)
                for q in q_list
            ) if q_list else False

            d_data["percentual"] = round(pct, 2)
            d_data["nota"] = round(nota_disc, 2)
            d_data["parte_realizada"] = has_disc_answers if q_list else False

        return {
            "nota_final": round(nota_final, 2),
            "percentual_acertos": round(percentual_acertos, 2),
            "total_acertos": total_acertos,
            "total_questoes": num_questoes,
            "detalhes_disciplinas": detalhes_disciplinas,
            "comparativo_questoes": comparativo,
            "partes_status": partes_status
        }

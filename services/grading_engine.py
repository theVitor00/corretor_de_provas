from typing import Dict, Any, List, Optional

from services.abbreviations import is_subject_applicable_to_tipo

class GradingEngine:
    def __init__(self, exam: Dict[str, Any]):
        """
        :param exam: Dicionário contendo dados da prova (valor_total, gabaritos, layout_config, tipo_prova).
        """
        self.exam = exam
        self.valor_total = float(exam.get("valor_total", 10.0))
        self.gabaritos = exam.get("gabaritos", {})
        self.layout_config = exam.get("layout_config", {})
        self.tipo_prova_categoria = exam.get("tipo_prova", "Atividade de Rotina")

    def grade_student(self, modelo_prova: Optional[str] = None, respostas_aluno: str = "", tipo_prova: Optional[str] = None) -> Dict[str, Any]:
        mod_str = str(modelo_prova or tipo_prova or "1").strip()
        
        # Buscar gabarito do modelo
        gabarito = self.gabaritos.get(mod_str)
        if not gabarito:
            # Tentar fallback insensível a maiúsculas/minúsculas
            for k, v in self.gabaritos.items():
                if k.lower() == mod_str.lower():
                    gabarito = v
                    break

        if not gabarito:
            # Tentar correspondência por dígitos (ex: '1' -> '1ª Série', '2' -> '2ª Série')
            tipo_digits = "".join(ch for ch in mod_str if ch.isdigit())
            if tipo_digits:
                for k, v in self.gabaritos.items():
                    k_digits = "".join(ch for ch in k if ch.isdigit())
                    if tipo_digits == k_digits:
                        gabarito = v
                        break

        if not gabarito:
            # Tentar correspondência por prefixo / contêm
            for k, v in self.gabaritos.items():
                if k.lower().startswith(mod_str.lower()) or mod_str.lower().startswith(k.lower()):
                    gabarito = v
                    break

        if not gabarito:
            gabs_cadastrados = ", ".join(f"'{k}'" for k in self.gabaritos.keys())
            raise ValueError(f"Gabarito para o tipo de prova '{mod_str}' não foi cadastrado nesta prova. Tipos disponíveis: {gabs_cadastrados}.")

        num_questoes = len(gabarito)
        respostas_aluno = respostas_aluno.upper().ljust(num_questoes, " ")[:num_questoes]

        # Mapeamento de disciplinas e pesos
        subjects_config = self.layout_config.get("subjects", [])
        question_weights_override = self.layout_config.get("weights", {})  # {str(q_num): peso}

        # Construir mapa de disciplina e peso original por questão (1-indexed)
        q_to_subject = {}
        q_to_orig_weight = {}

        tipo_subjects = [
            s for s in subjects_config 
            if is_subject_applicable_to_tipo(s.get("nome", ""), mod_str, s.get("modelo") or s.get("tipo"))
        ]

        for s in tipo_subjects:
            s_name = s.get("nome", "Geral")
            start_q = int(s.get("start_q", 1))
            end_q = int(s.get("end_q", num_questoes))
            s_peso = float(s.get("peso", 1.0))
            for q in range(start_q, end_q + 1):
                if q <= num_questoes:
                    q_to_subject[q] = s_name
                    q_to_orig_weight[q] = s_peso

        # Preencher questões não mapeadas explicitamente com "Geral" e peso 1.0
        for q in range(1, num_questoes + 1):
            if q not in q_to_subject:
                q_to_subject[q] = "Geral"
            if q not in q_to_orig_weight:
                q_to_orig_weight[q] = 1.0

        # Override por questão individual se houver no json
        for q_str, w in question_weights_override.items():
            try:
                q_num = int(q_str)
                q_to_orig_weight[q_num] = float(w)
            except ValueError:
                pass

        # Identificar questões anuladas no gabarito (*, X, ANULADA)
        q_is_annulled = {}
        for i in range(num_questoes):
            q_num = i + 1
            ans_g = str(gabarito[i]).strip().upper()
            q_is_annulled[q_num] = (ans_g in ["*", "X", "ANULADA"])

        # Redistribuir pesos por disciplina mantendo o valor total de cada disciplina
        disc_orig_total = {}
        disc_orig_active = {}
        for q_num in range(1, num_questoes + 1):
            d_name = q_to_subject[q_num]
            w_orig = q_to_orig_weight[q_num]
            disc_orig_total[d_name] = disc_orig_total.get(d_name, 0.0) + w_orig
            if not q_is_annulled[q_num]:
                disc_orig_active[d_name] = disc_orig_active.get(d_name, 0.0) + w_orig

        q_to_weight = {}
        for q_num in range(1, num_questoes + 1):
            d_name = q_to_subject[q_num]
            w_orig = q_to_orig_weight[q_num]
            if q_is_annulled[q_num]:
                q_to_weight[q_num] = 0.0
            else:
                s_tot = disc_orig_total.get(d_name, 0.0)
                s_act = disc_orig_active.get(d_name, 0.0)
                if s_act > 0:
                    q_to_weight[q_num] = w_orig * (s_tot / s_act)
                else:
                    q_to_weight[q_num] = 0.0

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

        # Pré-inicializar detalhes de todas as disciplinas do tipo
        detalhes_disciplinas = {}
        for s in tipo_subjects:
            s_name = s.get("nome", "Geral")
            if s_name not in detalhes_disciplinas:
                detalhes_disciplinas[s_name] = {
                    "acertos": 0,
                    "total": 0,               # Total de questões ativas (não anuladas)
                    "total_questoes": 0,      # Total de todas as questões
                    "anuladas": 0,            # Total de questões anuladas
                    "soma_pesos_acertos": 0.0,
                    "soma_pesos_totais": 0.0,
                    "questoes": [],
                    "parte_realizada": True
                }

        comparativo = []
        total_acertos = 0
        total_questoes_ativas = 0
        soma_pesos_totais = 0.0
        soma_pesos_acertos = 0.0

        for i in range(num_questoes):
            q_num = i + 1
            ans_aluno = respostas_aluno[i] if i < len(respostas_aluno) else " "
            ans_gab = gabarito[i]
            is_ann = q_is_annulled[q_num]
            
            disciplina_nome = q_to_subject.get(q_num, "Geral")
            peso = float(q_to_weight.get(q_num, 0.0))

            if not is_ann:
                total_questoes_ativas += 1

            correto = (not is_ann) and (ans_aluno == ans_gab and ans_aluno != "" and ans_aluno != " ")
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
                "anulada": is_ann,
                "peso": peso
            })

            # Agrupar por disciplina
            if disciplina_nome not in detalhes_disciplinas:
                detalhes_disciplinas[disciplina_nome] = {
                    "acertos": 0,
                    "total": 0,
                    "total_questoes": 0,
                    "anuladas": 0,
                    "soma_pesos_acertos": 0.0,
                    "soma_pesos_totais": 0.0,
                    "questoes": [],
                    "parte_realizada": True
                }

            detalhes_disciplinas[disciplina_nome]["total_questoes"] += 1
            detalhes_disciplinas[disciplina_nome]["soma_pesos_totais"] += peso
            detalhes_disciplinas[disciplina_nome]["questoes"].append(q_num)
            
            if is_ann:
                detalhes_disciplinas[disciplina_nome]["anuladas"] += 1
            else:
                detalhes_disciplinas[disciplina_nome]["total"] += 1
                if correto:
                    detalhes_disciplinas[disciplina_nome]["acertos"] += 1
                    detalhes_disciplinas[disciplina_nome]["soma_pesos_acertos"] += peso

        # -------------------------------------------------------------
        # CRITÉRIOS DE APROXIMAÇÃO / 100% DE ACERTOS POR DISCIPLINA E PROVA
        # -------------------------------------------------------------
        for d_name, d_data in detalhes_disciplinas.items():
            tot_act = d_data["total"]
            ac_act = d_data["acertos"]
            v_disc_target = disc_orig_total.get(d_name, d_data["soma_pesos_totais"])

            if tot_act > 0 and ac_act == tot_act:
                # 100% acertos na disciplina: nota máxima exata
                d_data["soma_pesos_acertos"] = v_disc_target
                d_data["percentual"] = 100.0
                if self.tipo_prova_categoria == "Prova Regular":
                    d_data["nota"] = round(v_disc_target, 1)
                else:
                    d_data["nota"] = 10.0
            else:
                pct = (d_data["soma_pesos_acertos"] / d_data["soma_pesos_totais"] * 100.0) if d_data["soma_pesos_totais"] > 0 else 0.0
                d_data["percentual"] = round(pct, 2)
                if self.tipo_prova_categoria == "Prova Regular":
                    d_data["nota"] = round(d_data["soma_pesos_acertos"], 1)
                else:
                    d_data["nota"] = round((d_data["soma_pesos_acertos"] / d_data["soma_pesos_totais"] * 10.0), 2) if d_data["soma_pesos_totais"] > 0 else 0.0

            q_list = d_data["questoes"]
            has_disc_answers = any(
                (respostas_aluno[q-1] != " " if q-1 < len(respostas_aluno) else False)
                for q in q_list
            ) if q_list else False
            d_data["parte_realizada"] = has_disc_answers if q_list else False

        # Se acertou 100% de todas as questões ativas da prova -> 100% automático na Nota Final
        if total_questoes_ativas > 0 and total_acertos == total_questoes_ativas:
            percentual_acertos = 100.0
            if self.tipo_prova_categoria == "Prova Regular":
                nota_final = sum(d["nota"] for d in detalhes_disciplinas.values())
            else:
                nota_final = self.valor_total
        else:
            percentual_acertos = (soma_pesos_acertos / soma_pesos_totais * 100.0) if soma_pesos_totais > 0 else 0.0
            if self.tipo_prova_categoria == "Prova Regular":
                nota_final = sum(d["nota"] for d in detalhes_disciplinas.values())
            else:
                nota_final = (soma_pesos_acertos / soma_pesos_totais * self.valor_total) if soma_pesos_totais > 0 else 0.0

        return {
            "nota_final": round(nota_final, 2),
            "percentual_acertos": round(percentual_acertos, 2),
            "total_acertos": total_acertos,
            "total_questoes": num_questoes,
            "total_questoes_ativas": total_questoes_ativas,
            "detalhes_disciplinas": detalhes_disciplinas,
            "comparativo_questoes": comparativo,
            "partes_status": partes_status
        }

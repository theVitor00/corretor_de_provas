import pytest
from database import Database
from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.grading_engine import GradingEngine

@pytest.fixture
def test_db(tmp_path):
    db_file = str(tmp_path / "test_annulment.db")
    return Database(db_file)

def test_question_annulment_weight_redistribution_and_100pct_approximation():
    """
    Testa anulação de questão, redistribuição proporcional de pesos e aproximação para 100% de acertos.
    Exemplo do usuário:
    - 10 questões, prova vale 10.
    - 1 questão é anulada (Q2 = '*').
    - Sobram 9 questões ativas. Peso de cada uma = 10 / 9 = 1.111111...
    - Aluno que acerta as 9 questões ativas ganha 10.0 (critério 100% de acertos).
    - Aluno que acerta 8 das 9 questões ativas ganha ~8.9.
    """
    exam_dict = {
        "nome": "Prova Teste Anulação",
        "valor_total": 10.0,
        "tipo_prova": "Prova Regular",
        "gabaritos": {"1": "A*AAAAAAAA"},  # Q2 anulada ('*')
        "layout_config": {
            "partes": [{"parte_num": 1, "nome": "Parte Única", "num_questoes": 10, "q_start": 1, "q_end": 10}],
            "subjects": [{"tipo": "1", "nome": "Matemática", "start_q": 1, "end_q": 10, "peso": 1.0}]
        }
    }

    engine = GradingEngine(exam_dict)

    # 1. Aluno 1: Respondeu A em todas as 10 questões (acertou as 9 ativas + respondeu a anulada)
    res_100 = engine.grade_student("1", "AAAAAAAAAA")
    assert res_100["total_questoes"] == 10
    assert res_100["total_questoes_ativas"] == 9
    assert res_100["total_acertos"] == 9
    assert res_100["percentual_acertos"] == 100.0
    assert res_100["nota_final"] == 10.0
    
    det_100 = res_100["detalhes_disciplinas"]["Matemática"]
    assert det_100["acertos"] == 9
    assert det_100["total"] == 9
    assert det_100["anuladas"] == 1
    assert det_100["nota"] == 10.0

    # 2. Aluno 2: Errou Q3 (respondeu 'B'), acertou 8 das 9 ativas
    res_88 = engine.grade_student("1", "AABAAAAAAA")  # Q1=A(ok), Q2=A(anulada), Q3=B(errada), Q4..Q10=A(ok)
    assert res_88["total_acertos"] == 8
    assert res_88["total_questoes_ativas"] == 9
    # 8 * (10 / 9) = 8.8888... -> Nota de Prova Regular arredondada para 1 casa = 8.9
    assert res_88["nota_final"] == 8.9
    
    det_88 = res_88["detalhes_disciplinas"]["Matemática"]
    assert det_88["acertos"] == 8
    assert det_88["nota"] == 8.9

def test_question_annulment_in_simulado_mode():
    """
    Testa anulação de questão no modo Simulado (escala de 0 a 10).
    """
    exam_dict = {
        "nome": "Simulado Anulação",
        "valor_total": 10.0,
        "tipo_prova": "Simulado",
        "gabaritos": {"1": "A**AAAAAAA"},  # Q2 e Q3 anuladas ('*')
        "layout_config": {
            "partes": [{"parte_num": 1, "nome": "Parte Única", "num_questoes": 10, "q_start": 1, "q_end": 10}],
            "subjects": [{"tipo": "1", "nome": "Geral", "start_q": 1, "end_q": 10, "peso": 1.0}]
        }
    }

    engine = GradingEngine(exam_dict)
    
    # Aluno que acerta as 8 questões ativas (100% de acertos ativas)
    res_full = engine.grade_student("1", "AAAAAAAAAA")
    assert res_full["total_questoes_ativas"] == 8
    assert res_full["total_acertos"] == 8
    assert res_full["nota_final"] == 10.0
    assert res_full["percentual_acertos"] == 100.0

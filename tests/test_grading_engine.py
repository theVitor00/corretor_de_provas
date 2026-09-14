import pytest
from services.grading_engine import GradingEngine

def test_grading_engine_simple():
    exam = {
        "valor_total": 10.0,
        "gabaritos": {
            "1": "ABCDEABCDE"
        },
        "layout_config": {
            "subjects": [
                {"nome": "Matemática", "start_q": 1, "end_q": 5},
                {"nome": "Física", "start_q": 6, "end_q": 10}
            ]
        }
    }

    engine = GradingEngine(exam)

    # Respostas do aluno: 100% de acertos
    res_100 = engine.grade_student("1", "ABCDEABCDE")
    assert res_100["nota_final"] == 10.0
    assert res_100["percentual_acertos"] == 100.0
    assert res_100["total_acertos"] == 10
    assert res_100["detalhes_disciplinas"]["Matemática"]["acertos"] == 5
    assert res_100["detalhes_disciplinas"]["Física"]["acertos"] == 5

    # Respostas do aluno: 5 acertos (50%)
    res_50 = engine.grade_student("1", "ABCDEXXXXX")
    assert res_50["nota_final"] == 5.0
    assert res_50["percentual_acertos"] == 50.0
    assert res_50["total_acertos"] == 5
    assert res_50["detalhes_disciplinas"]["Matemática"]["acertos"] == 5
    assert res_50["detalhes_disciplinas"]["Física"]["acertos"] == 0

def test_grading_engine_invalid_type():
    exam = {
        "valor_total": 10.0,
        "gabaritos": {"1": "ABCD"}
    }
    engine = GradingEngine(exam)
    with pytest.raises(ValueError, match="Gabarito para o tipo de prova '99' não foi cadastrado"):
        engine.grade_student("99", "ABCD")

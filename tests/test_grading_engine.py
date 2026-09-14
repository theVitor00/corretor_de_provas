import pytest
from services.grading_engine import GradingEngine

def test_grading_engine_with_tipo_specific_subjects():
    exam = {
        "valor_total": 10.0,
        "gabaritos": {
            "1": "ABCDEABCDE",
            "2": "EDCBAEDCBA"
        },
        "layout_config": {
            "subjects": [
                {"tipo": "1", "nome": "Matemática", "start_q": 1, "end_q": 5},
                {"tipo": "1", "nome": "Física", "start_q": 6, "end_q": 10},
                {"tipo": "2", "nome": "Física", "start_q": 1, "end_q": 5},
                {"tipo": "2", "nome": "Matemática", "start_q": 6, "end_q": 10}
            ]
        }
    }

    engine = GradingEngine(exam)

    # Tipo 1: Q1-5 é Matemática, Q6-10 é Física
    res_t1 = engine.grade_student("1", "ABCDEXXXXX")
    assert res_t1["detalhes_disciplinas"]["Matemática"]["acertos"] == 5
    assert res_t1["detalhes_disciplinas"]["Física"]["acertos"] == 0

    # Tipo 2: Q1-5 é Física, Q6-10 é Matemática
    res_t2 = engine.grade_student("2", "EDCBAXXXXX")
    assert res_t2["detalhes_disciplinas"]["Física"]["acertos"] == 5
    assert res_t2["detalhes_disciplinas"]["Matemática"]["acertos"] == 0

def test_grading_engine_invalid_type():
    exam = {
        "valor_total": 10.0,
        "gabaritos": {"1": "ABCD"}
    }
    engine = GradingEngine(exam)
    with pytest.raises(ValueError, match="Gabarito para o tipo de prova '99' não foi cadastrado"):
        engine.grade_student("99", "ABCD")

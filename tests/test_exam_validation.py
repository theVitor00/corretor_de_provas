import pytest
import os
from database import Database
from models.exam import ExamModel

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    return Database(db_path=db_file)

def test_exam_creation_and_parity_validation(test_db):
    model = ExamModel(test_db)

    # Sucesso: 2 tipos ("1", "2") com 2 gabaritos do mesmo tamanho (10 Qs cada)
    gabaritos_ok = {
        "1": "ABCDEABCDE",
        "2": "EDCBAEDCBA"
    }
    exam_id = model.create_exam("Prova Final 2026", "2026-11-20", gabaritos_ok, valor_total=10.0)
    assert exam_id > 0

    exam = model.get_exam_by_id(exam_id)
    assert exam["nome"] == "Prova Final 2026"
    assert len(exam["gabaritos"]) == 2
    assert exam["num_questoes"] == 10

def test_exam_validation_mismatched_lengths(test_db):
    model = ExamModel(test_db)

    # Erro: Gabaritos com tamanhos diferentes
    gabaritos_inval = {
        "1": "ABCDE",
        "2": "ABCDEABCDE"
    }
    with pytest.raises(ValueError, match="Todos os tipos de gabarito da prova devem possuir o mesmo número de questões"):
        model.create_exam("Prova Invalida", "2026-11-20", gabaritos_inval)

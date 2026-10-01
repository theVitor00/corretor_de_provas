import pytest
import os
from datetime import date
from database import Database
from models.exam import ExamModel
from models.subject import SubjectBlockModel

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_clone.db")
    return Database(db_path=db_file)

def test_clone_exam_basic(test_db):
    exam_model = ExamModel(test_db)
    subject_model = SubjectBlockModel(test_db)

    # 1. Criar bloco de disciplinas e prova original
    bloco_id = subject_model.create_block("Bloco I")
    subject_id = subject_model.create_subject("Matemática", bloco_id)

    gabaritos_orig = {
        "1": "ABCDEABCDE",
        "2": "EDCBAEDCBA"
    }
    layout_cfg = {
        "partes": [{"parte_num": 1, "nome": "Dia 1", "num_questoes": 10, "q_start": 1, "q_end": 10}],
        "gabaritos_por_parte": {"1": {"1": "ABCDEABCDE"}},
        "subjects": [{"modelo": "1", "tipo": "1", "parte_num": 1, "subject_id": subject_id, "nome": "Matemática", "start_q": 1, "end_q": 10, "peso": 1.0}]
    }

    orig_id = exam_model.create_exam(
        nome="Simulado ENEM 2025",
        data="2025-05-10",
        gabaritos=gabaritos_orig,
        bloco_ids=[bloco_id],
        valor_total=10.0,
        possui_redacao=True,
        tipo_prova="Simulado",
        trimestre="2º Trimestre",
        layout_config=layout_cfg
    )

    # 2. Executar clonagem
    clone_id = exam_model.clone_exam(orig_id)
    assert clone_id > 0
    assert clone_id != orig_id

    # 3. Validar prova clonada
    cloned = exam_model.get_exam_by_id(clone_id)
    assert cloned["nome"] == "Simulado ENEM 2025 (CLONE)"
    assert cloned["data"] == date.today().strftime("%Y-%m-%d")
    assert cloned["tipo_prova"] == "Simulado"
    assert cloned["trimestre"] == "2º Trimestre"
    assert cloned["valor_total"] == 10.0
    assert cloned["possui_redacao"] is True
    assert cloned["gabaritos"] == gabaritos_orig
    assert cloned["bloco_ids"] == [bloco_id]
    assert cloned["layout_config"] == layout_cfg
    assert cloned.get("total_processados", 0) == 0

def test_clone_exam_custom_title_and_date(test_db):
    exam_model = ExamModel(test_db)
    gabaritos = {"1": "ABCD"}
    orig_id = exam_model.create_exam("Prova Curta", "2024-01-01", gabaritos)

    clone_id = exam_model.clone_exam(orig_id, new_nome="Prova Curta - Recuperação", new_date="2026-12-01")
    cloned = exam_model.get_exam_by_id(clone_id)

    assert cloned["nome"] == "Prova Curta - Recuperação"
    assert cloned["data"] == "2026-12-01"

def test_clone_non_existent_exam(test_db):
    exam_model = ExamModel(test_db)
    with pytest.raises(ValueError, match="Prova com ID 9999 não encontrada"):
        exam_model.clone_exam(9999)

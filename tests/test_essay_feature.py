import os
import tempfile
import pytest
from database import Database, clean_matricula
from models.exam import ExamModel
from models.processing import ProcessingModel
from services.abbreviations import get_legend_mapping, get_acronym
from ui.tabs.processing_tab import EssayGradesDialog

@pytest.fixture
def temp_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_essay.db")
    return Database(db_path=db_file)


def test_exam_possui_redacao_flag(temp_db):
    exam_model = ExamModel(db=temp_db)
    
    # Criar prova com possui_redacao=True
    exam_id_1 = exam_model.create_exam(
        nome="Prova com Redação",
        data="2026-09-17",
        gabaritos={"1": "AAAAA"},
        possui_redacao=True
    )
    exam1 = exam_model.get_exam_by_id(exam_id_1)
    assert exam1["possui_redacao"] is True

    # Criar prova sem redação (padrão)
    exam_id_2 = exam_model.create_exam(
        nome="Prova sem Redação",
        data="2026-09-17",
        gabaritos={"1": "AAAAA"},
        possui_redacao=False
    )
    exam2 = exam_model.get_exam_by_id(exam_id_2)
    assert exam2["possui_redacao"] is False

    # Atualizar prova de False para True
    exam_model.update_exam(
        exam_id_2,
        nome="Prova sem Redação -> Agora com Redação",
        data="2026-09-17",
        gabaritos={"1": "AAAAA"},
        possui_redacao=True
    )
    exam2_updated = exam_model.get_exam_by_id(exam_id_2)
    assert exam2_updated["possui_redacao"] is True


def test_update_essay_grades_and_final_score(temp_db):
    exam_model = ExamModel(db=temp_db)
    proc_model = ProcessingModel(db=temp_db)

    exam_id = exam_model.create_exam(
        nome="Vestibular 2026",
        data="2026-09-17",
        gabaritos={"1": "ABCDE"},
        possui_redacao=True
    )

    # Salvar processamento do aluno 1001
    proc_id = proc_model.save_processing(
        prova_id=exam_id,
        aluno_matricula="001001",
        tipo_prova="1",
        respostas_aluno="ABCDE",
        status_controle="OK",
        nota_final=10.0,
        percentual_acertos=100.0,
        total_acertos=5,
        total_questoes=5,
        detalhes_disciplinas={}
    )

    results = proc_model.list_results_for_exam(exam_id)
    assert len(results) == 1
    assert results[0]["aluno_matricula"] == "1001"
    assert results[0]["nota_redacao"] is None

    # Atualizar nota de redação usando update_essay_grades
    proc_model.update_essay_grades(exam_id, {"1001": 19.5})

    results_updated = proc_model.list_results_for_exam(exam_id)
    assert len(results_updated) == 1
    assert results_updated[0]["nota_redacao"] == 19.5

    # Nota Final na Visualização Geral = total_acertos + nota_redacao (5 + 19.5 = 24.5)
    total_acertos = results_updated[0]["total_acertos"]
    nota_redacao = results_updated[0]["nota_redacao"]
    nota_final_geral = total_acertos + nota_redacao
    assert nota_final_geral == 24.5


def test_decimal_notation_parsing():
    # Testar se parse_grade_val aceita ponto e vírgula de forma idêntica
    dummy_dialog = EssayGradesDialog.__new__(EssayGradesDialog)
    
    val_dot = dummy_dialog.parse_grade_val("19.5")
    val_comma = dummy_dialog.parse_grade_val("19,5")
    val_int = dummy_dialog.parse_grade_val("20")

    assert val_dot == 19.5
    assert val_comma == 19.5
    assert val_int == 20.0
    assert val_dot == val_comma

    with pytest.raises(ValueError):
        dummy_dialog.parse_grade_val("abc")

    with pytest.raises(ValueError):
        dummy_dialog.parse_grade_val("-5")


def test_legend_mapping_generation():
    full_names = [
        "Ciências Humanas e suas Tecnologias",
        "Ciências da Natureza e suas Tecnologias",
        "Linguagens, Códigos e suas Tecnologias",
        "Matemática e suas Tecnologias"
    ]

    leg_map = get_legend_mapping(full_names, possesses_redacao=True)
    assert "CH" in leg_map
    assert "CN" in leg_map
    assert "LC" in leg_map
    assert "MT" in leg_map
    assert "RED" not in leg_map
    assert leg_map["CH"] == "Ciências Humanas e suas Tecnologias"

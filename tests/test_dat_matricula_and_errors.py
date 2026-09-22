import pytest
from database import Database, clean_matricula
from models.student import StudentModel
from models.exam import ExamModel
from models.processing import ProcessingModel
from services.dat_parser import DatParser

def test_clean_matricula_rules():
    # 0004502 -> 4502 (descarrega os 3 primeiros caracteres de controle e limpa zeros à esquerda)
    assert clean_matricula("0004502") == "4502"
    assert clean_matricula("4502") == "4502"
    assert clean_matricula("0004502") == clean_matricula("4502")
    
    # 0000502 -> 502, 0502 -> 502
    assert clean_matricula("0000502") == "502"
    assert clean_matricula("0502") == "502"
    assert clean_matricula("0000502") == clean_matricula("0502")
    
    # Inteiros e nulos
    assert clean_matricula(4502) == "4502"
    assert clean_matricula(None) == ""
    assert clean_matricula("") == ""

def test_dat_parser_pattern():
    parser = DatParser()
    # Padrão: 000 (0..2 descarte), 4502 (3..6 matricula), 2 (7 tipo), AABBCCDDEE (8.. respostas)
    line = "00045022AABBCCDDEE"
    parsed = parser.parse_line(line, line_number=1)
    
    assert parsed["control"] == "000"
    assert parsed["matricula"] == "4502"
    assert parsed["tipo"] == "2"
    assert parsed["respostas"] == "AABBCCDDEE"
    assert parsed["control_ok"] is True

def test_student_lookup_and_processing_status(tmp_path):
    db_path = str(tmp_path / "test_corretor.db")
    db = Database(db_path)
    student_model = StudentModel(db)
    processing_model = ProcessingModel(db)
    exam_model = ExamModel(db)

    # Cadastrar um estudante com matrícula 4502
    student_id = student_model.create("0004502", "Aluno Teste", "1ª Série")
    student = student_model.get_by_matricula("4502")
    assert student is not None
    assert student["id"] == student_id
    assert student["matricula"] == "4502"

    # Criar prova
    exam_id = exam_model.create_exam(
        nome="Prova Teste Matrícula",
        data="2026-09-22",
        gabaritos={"1": "A"*10, "2": "B"*10}
    )

    # 1. Processar aluno com matrícula existente (4502)
    proc_id1 = processing_model.save_processing(
        prova_id=exam_id,
        aluno_matricula="0004502",
        tipo_prova="2",
        respostas_aluno="B"*10,
        status_controle="OK",
        nota_final=10.0,
        percentual_acertos=100.0,
        total_acertos=10,
        total_questoes=10,
        detalhes_disciplinas={}
    )
    res1 = processing_model.get_by_id(proc_id1)
    assert res1["aluno_id"] == student_id
    assert res1["status_controle"] == "OK"

    # 2. Processar aluno com matrícula inexistente (9999)
    proc_id2 = processing_model.save_processing(
        prova_id=exam_id,
        aluno_matricula="0009999",
        tipo_prova="1",
        respostas_aluno="A"*10,
        status_controle="MATRICULA_NAO_ENCONTRADA",
        nota_final=10.0,
        percentual_acertos=100.0,
        total_acertos=10,
        total_questoes=10,
        detalhes_disciplinas={}
    )
    res2 = processing_model.get_by_id(proc_id2)
    assert res2["aluno_id"] is None
    assert res2["status_controle"] == "MATRICULA_NAO_ENCONTRADA"

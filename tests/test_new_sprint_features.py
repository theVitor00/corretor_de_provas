import pytest
import os
from database import Database
from models.exam import ExamModel
from models.processing import ProcessingModel
from services.grading_engine import GradingEngine

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_sprint.db")
    return Database(db_path=db_file)

def test_sprint_new_features(test_db):
    exam_model = ExamModel(test_db)
    proc_model = ProcessingModel(test_db)

    # 1. Testar criação de prova com tipo_prova, trimestre e gabaritos por modelo
    gabaritos = {
        "A": "AAAAABBBBB",
        "B": "BBBBBAAAAA"
    }
    layout_config = {
        "partes": [{"parte_num": 1, "nome": "Parte Única", "num_questoes": 10, "q_start": 1, "q_end": 10}],
        "subjects": [
            {"modelo": "A", "nome": "Português", "start_q": 1, "end_q": 5, "peso": 2.0},
            {"modelo": "A", "nome": "Matemática", "start_q": 6, "end_q": 10, "peso": 1.5}
        ]
    }

    exam_id = exam_model.create_exam(
        nome="Prova Teste Sprint",
        data="2026-09-24",
        gabaritos=gabaritos,
        valor_total=10.0,
        tipo_prova="Prova Regular",
        trimestre="2º Trimestre",
        layout_config=layout_config
    )

    exam = exam_model.get_exam_by_id(exam_id)
    assert exam is not None
    assert exam["tipo_prova"] == "Prova Regular"
    assert exam["trimestre"] == "2º Trimestre"
    assert "A" in exam["gabaritos"]
    assert "B" in exam["gabaritos"]

    # 2. Testar GradingEngine com Peso e Prova Regular
    engine = GradingEngine(exam)
    # Aluno acertou 3 de Português (peso 2.0 -> 3 * 2.0 = 6.0) e 2 de Matemática (peso 1.5 -> 2 * 1.5 = 3.0)
    respostas_aluno = "AAAXXBBXXX"
    result = engine.grade_student(modelo_prova="A", respostas_aluno=respostas_aluno)

    assert result["total_acertos"] == 5
    detalhes = result["detalhes_disciplinas"]
    assert detalhes["Português"]["acertos"] == 3
    assert detalhes["Português"]["nota"] == 6.0  # 3 * 2.0 = 6.0
    assert detalhes["Matemática"]["acertos"] == 2
    assert detalhes["Matemática"]["nota"] == 3.0  # 2 * 1.5 = 3.0

    # 3. Testar gravação no historico_notas
    proc_model.save_processing(
        prova_id=exam_id,
        aluno_matricula="1010",
        modelo_prova="A",
        respostas_aluno=respostas_aluno,
        status_controle="OK",
        nota_final=result["nota_final"],
        percentual_acertos=result["percentual_acertos"],
        total_acertos=result["total_acertos"],
        total_questoes=result["total_questoes"],
        detalhes_disciplinas=detalhes
    )

    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM historico_notas WHERE aluno_matricula = '1010'")
        rows = cur.fetchall()
        assert len(rows) == 2
        d_map = {r["disciplina"]: r["nota"] for r in rows}
        assert d_map["Português"] == 6.0
        assert d_map["Matemática"] == 3.0


def test_atomic_batch_processing_interruption_safety(test_db):
    exam_model = ExamModel(test_db)
    proc_model = ProcessingModel(test_db)

    exam_id = exam_model.create_exam(
        nome="Prova Teste Atomicidade",
        data="2026-09-24",
        gabaritos={"1": "AAAAA"},
        valor_total=10.0
    )

    exam = exam_model.get_exam_by_id(exam_id)
    engine = GradingEngine(exam)
    res = engine.grade_student("1", "AAAAA")

    batch_items = [
        {
            "aluno_matricula": "1001",
            "modelo_prova": "1",
            "respostas_aluno": "AAAAA",
            "aluno_id": None,
            "line_number": 1,
            "grading_res": res
        },
        {
            "aluno_matricula": "1002",
            "modelo_prova": "1",
            "respostas_aluno": "AAAAA",
            "aluno_id": None,
            "line_number": 2,
            "grading_res": res
        }
    ]

    count, errors = proc_model.save_batch_processing(exam_id, batch_items)
    assert count == 0
    assert len(errors) == 2

    # Verificar se ambos os registros foram gravados em lote
    results = proc_model.list_results_for_exam(exam_id)
    assert len(results) == 2

    # Testar se um lote inválido (ex: erro de tipo no lote) sofre rollback e previne perda de dados
    bad_items = [
        {
            "aluno_matricula": "1003",
            "modelo_prova": "1",
            "respostas_aluno": "AAAAA",
            "aluno_id": None,
            "line_number": 3,
            "grading_res": None # Erro intencional: None não possui nota_final
        }
    ]

    with pytest.raises(Exception):
        proc_model.save_batch_processing(exam_id, bad_items)

    # Garantir que a falha causou rollback e o estado anterior dos 2 registros permanece intocado
    results_after_fail = proc_model.list_results_for_exam(exam_id)
    assert len(results_after_fail) == 2


def test_decimal_weights_and_orientation_rules(test_db):
    exam_model = ExamModel(test_db)

    # 1. Prova Regular com peso de 4 casas decimais (ex: 0.3333)
    layout_config = {
        "partes": [{"parte_num": 1, "nome": "Parte Única", "num_questoes": 3, "q_start": 1, "q_end": 3}],
        "subjects": [
            {"modelo": "1", "nome": "Física", "start_q": 1, "end_q": 3, "peso": 0.3333}
        ]
    }
    exam_id = exam_model.create_exam(
        nome="Prova Pesos Decimais",
        data="2026-09-24",
        gabaritos={"1": "AAA"},
        tipo_prova="Prova Regular",
        layout_config=layout_config
    )

    exam = exam_model.get_exam_by_id(exam_id)
    engine = GradingEngine(exam)
    
    # 3 acertos * 0.3333 = 0.9999 -> Nota Regular = 1.0 (arredondado para 1 casa)
    res = engine.grade_student(modelo_prova="1", respostas_aluno="AAA")
    assert res["detalhes_disciplinas"]["Física"]["nota"] == 1.0
    assert res["nota_final"] == 1.0



import pytest
from database import Database
from models.exam import ExamModel
from models.processing import ProcessingModel
from services.dat_parser import DatParser
from services.grading_engine import GradingEngine

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_multipart_multifile.db"
    db = Database(db_path=str(db_file))
    return db

def test_multi_part_exam_creation_and_multifile_processing(test_db, tmp_path):
    exam_model = ExamModel(test_db)
    proc_model = ProcessingModel(test_db)

    # 1. Criar prova com 2 partes (Parte 1: 5 q, Parte 2: 5 q -> Total: 10 q)
    layout_config = {
        "partes": [
            {"parte_num": 1, "nome": "Dia 1 - Humanas", "num_questoes": 5, "q_start": 1, "q_end": 5},
            {"parte_num": 2, "nome": "Dia 2 - Exatas", "num_questoes": 5, "q_start": 6, "q_end": 10}
        ],
        "gabaritos_por_parte": {
            "1": {"1": "AAAAA", "2": "BBBBB"}
        },
        "subjects": [
            {"tipo": "1", "nome": "História", "parte_num": 1, "start_q": 1, "end_q": 5},
            {"tipo": "1", "nome": "Matemática", "parte_num": 2, "start_q": 6, "end_q": 10}
        ]
    }

    gabaritos_unificados = {
        "1": "AAAAABBBBB"
    }

    exam_id = exam_model.create_exam(
        nome="ENEM Simulado 2 Dias",
        data="2026-11-01",
        gabaritos=gabaritos_unificados,
        valor_total=10.0,
        layout_config=layout_config
    )

    exam = exam_model.get_exam_by_id(exam_id)
    assert exam is not None
    assert exam["num_questoes"] == 10

    # 2. Criar 2 arquivos .DAT (Dia 1 e Dia 2)
    # Linha modelo standard: "000" (control 3) + "2536" (matricula 4) + "1" (tipo 1) + respostas (5)
    # Total header = 8 chars -> 00025361
    dat_part1 = tmp_path / "dia1.dat"
    dat_part2 = tmp_path / "dia2.dat"
    dat_part1.write_text("00025361AAAAA\n")
    dat_part2.write_text("00025361BBBCC\n")

    parser = DatParser()
    items_p1 = parser.parse_file(str(dat_part1))
    items_p2 = parser.parse_file(str(dat_part2))

    assert len(items_p1) == 1
    assert items_p1[0]["matricula"] == "2536"
    assert items_p1[0]["respostas"] == "AAAAA"

    assert len(items_p2) == 1
    assert items_p2[0]["matricula"] == "2536"
    assert items_p2[0]["respostas"] == "BBBCC"

    # 3. Testar fusão e cálculo das notas unificadas
    raw_ans_p1 = items_p1[0]["respostas"]
    raw_ans_p2 = items_p2[0]["respostas"]

    unified_ans = raw_ans_p1 + raw_ans_p2
    assert unified_ans == "AAAAABBBCC"

    engine = GradingEngine(exam)
    result = engine.grade_student(tipo_prova="1", respostas_aluno=unified_ans)

    assert result["total_acertos"] == 8
    assert result["total_questoes"] == 10
    assert result["nota_final"] == 8.0

    detalhes = result["detalhes_disciplinas"]
    assert detalhes["História"]["acertos"] == 5
    assert detalhes["História"]["nota"] == 10.0

    assert detalhes["Matemática"]["acertos"] == 3
    assert detalhes["Matemática"]["nota"] == 6.0

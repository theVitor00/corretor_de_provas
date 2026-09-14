import pytest
import os
from database import Database
from services.exporter import ReportExporter

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    return Database(db_path=db_file)

def test_export_pdf_excel_word(test_db, tmp_path):
    exporter = ReportExporter(test_db)
    
    exam = {
        "nome": "Simulado Geral",
        "data": "2026-10-15",
        "bloco_nome": "Exatas",
        "valor_total": 10.0
    }

    results = [
        {
            "aluno_matricula": "1001",
            "aluno_nome": "Aluno Teste 1",
            "aluno_turma": "Turma A",
            "tipo_prova": "1",
            "total_acertos": 8,
            "total_questoes": 10,
            "percentual_acertos": 80.0,
            "nota_final": 8.0,
            "detalhes_disciplinas": {"Matemática": {"acertos": 8, "total": 10}}
        }
    ]

    pdf_file = os.path.join(tmp_path, "relatorio.pdf")
    exporter.export_exam_pdf(exam, results, pdf_file)
    assert os.path.exists(pdf_file)
    assert os.path.getsize(pdf_file) > 0

    excel_file = os.path.join(tmp_path, "relatorio.xlsx")
    exporter.export_exam_excel(exam, results, excel_file)
    assert os.path.exists(excel_file)
    assert os.path.getsize(excel_file) > 0

    word_file = os.path.join(tmp_path, "relatorio.docx")
    exporter.export_exam_word(exam, results, word_file)
    assert os.path.exists(word_file)
    assert os.path.getsize(word_file) > 0

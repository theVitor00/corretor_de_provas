import pytest
import os
import json
import csv
from database import Database
from models.student import StudentModel
from services.importer import StudentImporter

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    return Database(db_path=db_file)

def test_student_crud_and_clean_matricula(test_db):
    model = StudentModel(test_db)
    
    # Create with leading zeros (ex: '002536')
    s_id = model.create("002536", "João Silva", "Turma A")
    assert s_id > 0

    # Get by ID / Matricula
    student = model.get_by_id(s_id)
    assert student["nome"] == "João Silva"
    assert student["matricula"] == "2536"  # Cleaned

    # Query with or without leading zero
    found = model.get_by_matricula("002536")
    assert found is not None
    assert found["id"] == s_id

    # Update with leading zero
    model.update(s_id, "0001234", "João Silva Santos", "Turma B")
    updated = model.get_by_id(s_id)
    assert updated["matricula"] == "1234"

def test_student_import_csv_clean_matricula(test_db, tmp_path):
    model = StudentModel(test_db)
    importer = StudentImporter(model)

    csv_file = os.path.join(tmp_path, "students.csv")
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["matricula", "nome", "turma"])
        writer.writerow(["0001", "Maria Oliveira", "Turma 101"])
        writer.writerow(["002536", "Pedro Santos", "Turma 101"])

    succ, err_count, errors = importer.import_from_csv(csv_file)
    assert succ == 2
    assert err_count == 0
    
    students = model.list_all()
    matriculas = [s["matricula"] for s in students]
    assert "1" in matriculas
    assert "2536" in matriculas

def test_student_import_json_clean_matricula(test_db, tmp_path):
    model = StudentModel(test_db)
    importer = StudentImporter(model)

    json_file = os.path.join(tmp_path, "students.json")
    data = [
        {"matricula": "0003", "nome": "Ana Lima", "turma": "Turma 102"},
        {"matricula": "000004", "nome": "Carlos Souza", "turma": "Turma 102"}
    ]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    succ, err_count, errors = importer.import_from_json(json_file)
    assert succ == 2
    assert err_count == 0
    
    s3 = model.get_by_matricula("3")
    assert s3["nome"] == "Ana Lima"
    s4 = model.get_by_matricula("4")
    assert s4["nome"] == "Carlos Souza"

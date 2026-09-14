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

def test_student_crud(test_db):
    model = StudentModel(test_db)
    
    # Create
    s_id = model.create("1234", "João Silva", "Turma A")
    assert s_id > 0

    # Get by ID / Matricula
    student = model.get_by_id(s_id)
    assert student["nome"] == "João Silva"
    assert student["matricula"] == "1234"

    # Update
    model.update(s_id, "1234", "João Silva Santos", "Turma B")
    updated = model.get_by_id(s_id)
    assert updated["nome"] == "João Silva Santos"
    assert updated["turma"] == "Turma B"

    # List & Search
    all_students = model.list_all(search="João")
    assert len(all_students) == 1

    # Delete
    model.delete(s_id)
    assert model.get_by_id(s_id) is None

def test_student_import_csv(test_db, tmp_path):
    model = StudentModel(test_db)
    importer = StudentImporter(model)

    csv_file = os.path.join(tmp_path, "students.csv")
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["matricula", "nome", "turma"])
        writer.writerow(["0001", "Maria Oliveira", "Turma 101"])
        writer.writerow(["0002", "Pedro Santos", "Turma 101"])

    succ, err_count, errors = importer.import_from_csv(csv_file)
    assert succ == 2
    assert err_count == 0
    assert len(model.list_all()) == 2

def test_student_import_json(test_db, tmp_path):
    model = StudentModel(test_db)
    importer = StudentImporter(model)

    json_file = os.path.join(tmp_path, "students.json")
    data = [
        {"matricula": "0003", "nome": "Ana Lima", "turma": "Turma 102"},
        {"matricula": "0004", "nome": "Carlos Souza", "turma": "Turma 102"}
    ]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    succ, err_count, errors = importer.import_from_json(json_file)
    assert succ == 2
    assert err_count == 0
    assert len(model.list_all()) == 2

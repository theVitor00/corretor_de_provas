import pytest
import os
from database import Database

def test_database_init(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    db = Database(db_path=db_file)
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cur.fetchall()]

    expected_tables = ["alunos", "blocos", "disciplinas", "provas", "prova_gabaritos", "prova_processamentos", "configuracoes"]
    for t in expected_tables:
        assert t in tables

def test_database_config(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    db = Database(db_path=db_file)

    db.set_config("key1", "val1")
    assert db.get_config("key1") == "val1"
    assert db.get_config("key2", "default") == "default"

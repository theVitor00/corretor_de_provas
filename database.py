import sqlite3
import os
import json
from typing import Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corretor.db")

class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Alunos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alunos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricula TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    turma TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabela de Blocos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabela de Disciplinas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disciplinas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    bloco_id INTEGER NULL,
                    FOREIGN KEY (bloco_id) REFERENCES blocos(id) ON DELETE SET NULL
                );
            """)

            # Tabela de Provas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS provas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    data TEXT NOT NULL,
                    bloco_id INTEGER NULL,
                    valor_total REAL DEFAULT 10.0,
                    layout_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bloco_id) REFERENCES blocos(id) ON DELETE SET NULL
                );
            """)

            # Tabela de Gabaritos por Tipo de Prova
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prova_gabaritos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prova_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    respostas TEXT NOT NULL,
                    FOREIGN KEY (prova_id) REFERENCES provas(id) ON DELETE CASCADE,
                    UNIQUE(prova_id, tipo)
                );
            """)

            # Tabela de Processamentos/Resultados da Prova
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prova_processamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prova_id INTEGER NOT NULL,
                    aluno_matricula TEXT NOT NULL,
                    aluno_id INTEGER NULL,
                    tipo_prova TEXT NOT NULL,
                    respostas_aluno TEXT NOT NULL,
                    status_controle TEXT DEFAULT 'OK',
                    nota_final REAL DEFAULT 0.0,
                    percentual_acertos REAL DEFAULT 0.0,
                    total_acertos INTEGER DEFAULT 0,
                    total_questoes INTEGER DEFAULT 0,
                    detalhes_disciplinas TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prova_id) REFERENCES provas(id) ON DELETE CASCADE,
                    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE SET NULL
                );
            """)

            # Tabela de Configurações Gerais da Aplicação
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                );
            """)

            conn.commit()

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT valor FROM configuracoes WHERE chave = ?", (key,))
            row = cur.fetchone()
            return row["valor"] if row else default

    def set_config(self, key: str, value: str):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
                ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """, (key, value))
            conn.commit()

# Instância padrão
db = Database()

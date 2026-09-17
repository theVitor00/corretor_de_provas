import sqlite3
import os
import json
from typing import Optional, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corretor.db")

def clean_matricula(mat: Any) -> str:
    """
    Remove zeros à esquerda da matrícula.
    Exemplo: '002536' -> '2536', '0001' -> '1', '0' -> '0'.
    """
    if mat is None:
        return ""
    s = str(mat).strip()
    if not s:
        return ""
    cleaned = s.lstrip("0")
    return cleaned if cleaned else "0"


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
                    possui_redacao INTEGER DEFAULT 0,
                    layout_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bloco_id) REFERENCES blocos(id) ON DELETE SET NULL
                );
            """)

            # Tabela de Relacionamento N:N entre Provas e Blocos (Múltiplos Blocos por Prova)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prova_blocos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prova_id INTEGER NOT NULL,
                    bloco_id INTEGER NOT NULL,
                    FOREIGN KEY (prova_id) REFERENCES provas(id) ON DELETE CASCADE,
                    FOREIGN KEY (bloco_id) REFERENCES blocos(id) ON DELETE CASCADE,
                    UNIQUE(prova_id, bloco_id)
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
                    nota_redacao REAL DEFAULT NULL,
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

        self.migrate_schema()
        self.migrate_matriculas()
        self.migrate_turmas()

    def migrate_schema(self):
        """
        Migração automática de schema para bancos de dados existentes.
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(provas);")
            cols_provas = [row["name"] for row in cur.fetchall()]
            if "possui_redacao" not in cols_provas:
                cur.execute("ALTER TABLE provas ADD COLUMN possui_redacao INTEGER DEFAULT 0;")

            cur.execute("PRAGMA table_info(prova_processamentos);")
            cols_proc = [row["name"] for row in cur.fetchall()]
            if "nota_redacao" not in cols_proc:
                cur.execute("ALTER TABLE prova_processamentos ADD COLUMN nota_redacao REAL DEFAULT NULL;")

            conn.commit()

    def migrate_matriculas(self):
        """
        Migração automática: remove zeros à esquerda de todas as matrículas no banco de dados.
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT id, matricula FROM alunos")
            rows = cur.fetchall()
            for row in rows:
                orig = row["matricula"]
                cleaned = clean_matricula(orig)
                if cleaned != orig:
                    try:
                        cur.execute("UPDATE alunos SET matricula = ? WHERE id = ?", (cleaned, row["id"]))
                    except sqlite3.IntegrityError:
                        cur.execute("DELETE FROM alunos WHERE id = ?", (row["id"],))

            cur.execute("SELECT id, aluno_matricula FROM prova_processamentos")
            p_rows = cur.fetchall()
            for row in p_rows:
                orig = row["aluno_matricula"]
                cleaned = clean_matricula(orig)
                if cleaned != orig:
                    cur.execute("UPDATE prova_processamentos SET aluno_matricula = ? WHERE id = ?", (cleaned, row["id"]))

            conn.commit()

    def migrate_turmas(self):
        """
        Migração automática: converte valores da coluna 'turma' na tabela de alunos
        (ex: '1ª SÉRIE - A' -> '1ª Série', '2ª SÉRIE - A' -> '2ª Série', '3ª SÉRIE - A' -> '3ª Série').
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT turma FROM alunos")
            turmas = [row["turma"] for row in cur.fetchall() if row["turma"]]
            for t in turmas:
                new_t = t
                t_upper = t.upper()
                if "1" in t and ("SÉRIE" in t_upper or "SERIE" in t_upper):
                    new_t = "1ª Série"
                elif "2" in t and ("SÉRIE" in t_upper or "SERIE" in t_upper):
                    new_t = "2ª Série"
                elif "3" in t and ("SÉRIE" in t_upper or "SERIE" in t_upper):
                    new_t = "3ª Série"

                if new_t != t:
                    cur.execute("UPDATE alunos SET turma = ? WHERE turma = ?", (new_t, t))

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

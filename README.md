# Corretor de Provas e Leitor de Gabaritos

Sistema desktop moderno desenvolvido em **Python 3** com **PyQt6** para automação da leitura de cartões-resposta (arquivos `.DAT`), cálculo de notas de exames objetivos e redação, gestão de alunos e turmas, e geração/exportação de relatórios estatísticos e individuais em múltiplos formatos.

---

## 🛠️ Requisitos de Sistema

- **Python**: Versão 3.10 ou superior.
- **Sistema Operacional**: Windows, Linux ou macOS.

### Dependências Python
Instale todas as bibliotecas necessárias com o seguinte comando:

```bash
pip install PyQt6 qtawesome reportlab openpyxl python-docx pytest
```

---

## ⚡ Principais Funcionalidades

1. **Gestão de Provas & Gabaritos**:
   - Cadastro de provas com data, valor total e suporte a múltiplos tipos de prova (ex: Tipo 1, Tipo 2).
   - Suporte a **provas multi-partes** com múltiplos arquivos `.DAT` por etapa de processamento.
   - Mapeamento flexível de disciplinas e blocos de conhecimento (**LC** - Linguagens, **MT** - Matemática, **CN** - Ciências da Natureza, **CH** - Ciências Humanas).
   - Suporte opcional a cálculo com **Nota de Redação**.

2. **Gestão de Alunos & Turmas**:
   - Cadastro completo de estudantes com matrícula, nome e turma (ex: `1ª Série`, `2ª Série`, `3ª Série`).
   - Normalização automática de matrículas (remoção de zeros à esquerda para padronização).
   - Visualização do histórico do aluno e emissão de **Boletim Individual**.

3. **Lançamento de Notas de Redação**:
   - Janela de entrada dedicada com **destaque visual na linha ativa** para evitar erros de navegação.
   - Lançamento manual individual ou **importação em lote via arquivo CSV**.
   - Cálculo automático da nota final: `Nota Final = Total de Acertos + Nota da Redação`.

4. **Processamento de Leitura Óptica (`.DAT`)**:
   - Leitura automatizada de arquivos de leitores ópticos no formato `.DAT`.
   - Motor de correção eficiente com rastreamento de alunos ausentes (atribuição de nota zero) e validação contra matrículas cadastradas.

5. **Relatórios & Visualização Dinâmica**:
   - Três modos de visualização selecionáveis na interface gráfica:
     - **Geral (Acertos por Bloco)**: Exibe a quantidade de acertos por bloco, total de acertos, nota da redação e nota final.
     - **Por Bloco (Notas 0 a 10)**: Converte os acertos em notas de 0 a 10 por bloco de disciplinas.
     - **Por Disciplina (Notas 0 a 10)**: Exibe as notas individualizadas de cada disciplina cadastrada.
   - Coluna de numeração sequencial automática (`1, 2, 3, 4...`) em todas as exibições.
   - Ordenação dinâmica por Nome (A-Z), Maior Nota Final, Menor Nota Final e Matrícula.
   - Busca em tempo real por nome ou número de matrícula.
   - Painel de **Legenda** posicionado no topo da tabela, listando apenas os blocos relevantes (LC, MT, CN, CH).

6. **Impressão Direta & Exportação Multi-formato**:
   - **Impressão Direta A4**: Orientação Retrato (Geral/Bloco) e Paisagem/Landscape (Por Disciplina), margens otimizadas (5mm), e logotipo da instituição (`logo.png`) alinhado à extrema direita.
   - **Exportação em PDF**: Layout A4 profissional com formatação condicional de páginas e tabelas elegantes.
   - **Exportação em Excel (.xlsx)**: Planilha estilizada com mesclagem total da barra de legenda pela largura da tabela e cabeçalhos estilizados.
   - **Exportação em Word (.docx)**: Documento formatado pronto para edição e arquivamento oficial.

---

## 📁 Estrutura do Projeto

```
Corretor/
│
├── main.py                      # Ponto de entrada da aplicação (PyQt6 UI)
├── database.py                  # Gerenciador do banco de dados SQLite e migrações
├── logo.png                     # Logotipo institucional exibido nos relatórios
│
├── models/                      # Camada de Modelos de Dados e Banco
│   ├── exam.py                  # CRUD e regras de exames e layout de disciplinas
│   ├── student.py               # CRUD de alunos e turmas
│   ├── subject.py               # CRUD de blocos de disciplinas
│   └── processing.py            # Persistência e listagem dos resultados processados
│
├── services/                    # Camada de Serviços e Regras de Negócio
│   ├── dat_parser.py            # Parser de arquivos .DAT de leitoras ópticas
│   ├── grading_engine.py        # Motor de correção de gabaritos e pontuação
│   ├── exporter.py              # Gerador de relatórios (PDF, Excel, Word)
│   └── abbreviations.py         # Mapeamento de siglas e legendas de matérias
│
├── ui/                          # Interface Gráfica do Usuário (PyQt6)
│   ├── theme.py                 # QSS e paleta de cores institucional (Dark Navy)
│   └── tabs/
│       ├── students_tab.py      # Aba de gestão de alunos e boletim
│       ├── exams_tab.py         # Aba de criação/edição de provas
│       ├── processing_tab.py   # Aba de importação .DAT e notas de redação
│       └── reports_tab.py      # Aba de relatórios, filtros, visualização e impressão
│
└── tests/                       # Suíte de Testes Automatizados (pytest)
    ├── test_abbreviations.py
    ├── test_dat_parser.py
    ├── test_database.py
    ├── test_essay_feature.py
    ├── test_exam_validation.py
    ├── test_exporter.py
    ├── test_grading_engine.py
    ├── test_multi_part_exam_multifile.py
    ├── test_report_view_modes.py
    └── test_student_crud.py
```

---

## 🚀 Como Executar

### 1. Iniciar a Aplicação
Execute o arquivo principal:

```bash
python main.py
```

### 2. Executar os Testes Automatizados
Para rodar a suíte completa de testes unitários e de integração:

```bash
python -m pytest
```

---

## 🎨 Padrões Visuais e Usabilidade
- **Paleta de Cores**: Slate/Navy (#242D64 / #1E293B) com acentos visuais em Emerald (#10B981), Crimson (#EF4444) e Teal (#00A9A4).
- **Ícones**: Biblioteca `qtawesome` (FontAwesome 5/6).
- **Relatórios**: Alinhamentos pré-configurados, suporte a nomes longos com `<nobr>` para evitar quebras inadequadas e cálculo automático de médias e notas máximas/mínimas da turma.

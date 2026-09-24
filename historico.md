# Histórico de Desenvolvimento e Contexto de Implementação

Este documento registra a evolução cronológica do projeto **Corretor de Provas e Leitor de Gabaritos**, detalhando cada commit e refatoração realizada. Ele serve como fonte primária de contexto para futuros agentes de IA e desenvolvedores compreenderem a arquitetura, regras de negócio, histórico de decisões e estrutura do código.

---

## 🏗️ 1. Estrutura Arquitetural Básica

O sistema é construído sobre o padrão **MVC (Model-View-Controller)** adaptado para aplicações Desktop Python com **PyQt6** e **SQLite**.

### Componentes Chave:
- **`main.py`**: Instancia a aplicação `QApplication`, aplica o tema escuro (`ui/theme.py`) e carrega a janela principal com as abas de navegação.
- **`database.py`**: Gerencia a conexão SQLite (`corretor.db`), criação inicial das tabelas e execução de migrações automáticas de schema (`ALTER TABLE`, correções de dados).
- **`models/`**:
  - `ExamModel`: Cadastro de provas, gabaritos por tipo de prova e configuração de layout de questões.
  - `StudentModel`: Cadastro de estudantes, turmas e gerenciamento de registros.
  - `SubjectBlockModel`: Blocos de disciplinas e abreviações (LC, MT, CN, CH).
  - `ProcessingModel`: Gravação e consulta dos resultados processados por prova.
- **`services/`**:
  - `dat_parser.py`: Leitura de arquivos `.DAT` provenientes de leitoras ópticas de cartão-resposta.
  - `grading_engine.py`: Algoritmo de correção de respostas dos alunos contra o gabarito.
  - `exporter.py`: Geração de documentos oficiais (PDF via `reportlab`, Excel via `openpyxl`, Word via `python-docx`).
  - `abbreviations.py`: Funções utilitárias para geração de siglas de blocos e tooltips.
- **`ui/tabs/`**:
  - `students_tab.py`: Tabela de gestão de alunos e diálogo de Boletim Individual.
  - `exams_tab.py`: Formulário de criação/edição de exames e atribuição de gabaritos.
  - `processing_tab.py`: Leitura de arquivos `.DAT`, inclusão de notas de redação e reprocessamento.
  - `reports_tab.py`: Visualização tabular dinâmica, ordenação, filtro, painel de legenda e Impressão Direta A4.

---

## 📜 2. Histórico de Commits e Evolução do Código

### Commit 1: `2092aaf` - *Implementação completa do Corretor de Provas*
- Criada a infraestrutura inicial do projeto com banco de dados SQLite (`corretor.db`).
- Implementados modelos de dados CRUD (`ExamModel`, `StudentModel`, `SubjectBlockModel`, `ProcessingModel`).
- Criado o parser para arquivos `.DAT` e o motor de correção `GradingEngine`.
- Implementado o serviço `ReportExporter` com suporte a exportação de resultados para PDF, Excel e Word.
- Construída a interface PyQt6 com 4 abas e tema visual profissional.

### Commit 2: `db11287` - *Fix: Corrigir parênteses duplicados na assinatura de list_subjects*
- Corrigido erro de sintaxe no arquivo `models/subject.py`.

### Commit 3: `fe76616` - *Fix: Adicionar parâmetro self ao método list_exams na classe ExamModel*
- Ajustada a assinatura do método `list_exams` em `models/exam.py` para correta invocação de instância.

### Commit 4: `3f31f0d` - *Style: Substituir emojis por ícones FontAwesome (qtawesome)*
- Substituição de emojis por ícones vetoriais da biblioteca `qtawesome` (FontAwesome).
- Otimização do dimensionamento dos botões nas tabelas de alunos.

### Commit 5: `fdfa308` - *Feat: Adicionar tipo obrigatório no mapeamento de disciplinas e normalizar matrículas*
- Adicionada a obrigatoriedade da especificação do tipo de prova no mapeamento de questões por matéria.
- Implementada normalização de matrículas de alunos, desconsiderando zeros à esquerda (ex: `002847` tratado como `2847`).

### Commit 6: `efadef5` - *Feat: Landscape PDF report, nobr student names e rastreamento de ausentes*
- Adicionado suporte a relatórios em PDF em modo paisagem.
- Prevenção de quebra indevida de linhas em nomes de alunos com tags `<nobr>`.
- Rastreamento de alunos ausentes no processamento, atribuindo nota zero automaticamente.

### Commit 7: `8209ae2` - *Refactor: Remove Geral column e subtítulo dinâmico de turmas*
- Removida a coluna redundante "Geral" dos relatórios estatísticos.
- Adicionada lógica dinâmica para exibição do subtítulo da turma selecionada (ex: `Geral - Para Todas as Turmas` ou `Turma 1ª Série`).

### Commit 8: `077400d` - *Feat: Boletim individual multi-formato e scroll horizontal*
- Implementada a exportação de Boletim Individual de alunos em PDF, Excel e Word.
- Adicionado scroll horizontal com rolagem suave por pixel na tabela de resultados.
- Ajuste dinâmico de largura na coluna do nome do aluno com base no maior nome presente.

### Commit 9: `8210f35` - *Fix: Simplificar texto de botão e ajustar largura de colunas em ExamsTab*
- Texto do botão simplificado para "Processar" e aumento do tamanho da coluna de ações na aba de exames.

### Commit 10: `10998a9` - *Feat: Suporte a provas multi-partes com múltiplos arquivos .DAT*
- Adicionado suporte a provas realizadas em mais de uma etapa (ex: Dia 1 e Dia 2) com upload sequencial de múltiplos arquivos `.DAT`.
- Algoritmo de consolidação de acertos por aluno combinando arquivos das diferentes etapas.

### Commit 11: `d737763` - *Assets: Adiciona logo.png e limpa artefatos temporários*
- Inclusão do logotipo institucional `logo.png` na raiz do projeto para exibição nos relatórios.

### Commit 12: `a8e35b4` - *Feat: Impressão e exportação em landscape para visualização por disciplina*
- Configurada alteração automática para orientação Landscape quando o modo de visualização selecionado for **Por Disciplina**.

---

## 🚀 3. Sprint Atual: Funcionalidade de Redação & Refinamentos Finais

Nesta fase final de polimento, foram adicionados recursos de apoio à nota de redação e diversos ajustes no layout e alinhamento de relatórios:

### 3.1 Suporte à Nota de Redação (`nota_redacao`)
- **Migração do Banco**:
  - `database.py`: Adicionada verificação no início do programa para incluir a coluna `nota_redacao REAL DEFAULT 0.0` na tabela `resultados` caso ela não exista.
- **Janela de Lançamento de Redação (`EssayGradesDialog`)**:
  - Implementado em `ui/tabs/processing_tab.py`. Permite a inserção manual das notas de redação por aluno com visual **destacado na linha onde o cursor está ativo** (facilidade de conferência visual).
  - Suporte a upload de arquivo CSV com mapeamento `matricula,nota_redacao`.
- **Cálculo da Nota Final**:
  - A fórmula oficial definida é: `Nota Final = Total de Acertos + Nota da Redação`.
  - Nos modos de nota de 0 a 10 (Bloco/Disciplina), `nota_final = nota_bloco_ou_final + nota_redacao`.

### 3.2 Padronização dos Nomes de Turma
- Atualização direta no banco de dados SQLite para normalizar registros antigos:
  - Onde havia `'1ª SÉRIE - A'`, o valor foi migrado para `'1ª Série'` (texto em minúsculo mantendo apenas a letra inicial maiúscula e removendo o sufixo `' - A'`). O mesmo para 2ª e 3ª Séries.

### 3.3 Ordenação Rígida por Nota Final
- A ordenação por **Maior Nota** e **Menor Nota** na interface e nos relatórios passou a utilizar estritamente o valor calculado da `Nota Final` (Total de Acertos + Nota da Redação), corrigindo discrepâncias anteriores.

### 3.4 Posicionamento e Formatação da Legenda
- A caixa de legenda nos relatórios exportados (PDF, Excel, Word) e impressos foi movida para ficar **acima da tabela**, logo após o título e subtítulo da prova.
- O título foi simplificado para `"Legenda"` e lista apenas as siglas dos 4 blocos principais (**LC**, **MT**, **CN**, **CH**), removendo itens de redação desnecessários.
- Na exportação em Excel (`exporter.py`), a célula da legenda é mesclada dinamicamente (`ws.merge_cells`) para cobrir exatamente toda a largura da tabela de dados (`total_cols_cnt`).

### 3.5 Logotipo e Layout de Impressão Direta A4
- No HTML da Impressão Direta (`print_report` em `ui/tabs/reports_tab.py`), a logomarca (`logo.png`) é renderizada através de uma tabela de cabeçalho (`.header-table`) com alinhamento à extrema direita (`float: right; margin-left: auto; text-align: right;`), nivelada com a borda direita da tabela de dados. Funciona para Retrato e Paisagem.
- As margens da Impressão Direta foram reduzidas em 1cm em todos os lados (configurado para `5mm` no `@page CSS` e `QPageLayout`), permitindo que a tabela ocupe o máximo de espaço útil na folha A4.

### 3.6 Remoção da Palavra "Subtítulo"
- Removido o rótulo prefixo `"Subtítulo: "` de todos os subtítulos de relatórios.
- Formato anterior: `"Subtítulo: Geral - Para Todas as Turmas"`
- Formato atual: `"Geral - Para Todas as Turmas"`

### 3.7 Coluna Sequencial sem Cabeçalho (`1, 2, 3, 4...`)
- Adicionada uma primeira coluna antes da coluna de `Matrícula` em todas as tabelas e relatórios (GUI, Impressão Direta, PDF, Excel e Word).
- O cabeçalho desta coluna é em branco (`""`), e os dados contêm apenas a numeração sequencial dos alunos (`1, 2, 3, 4, 5...`).

### 3.9 Normalização de Matrícula de 4 Dígitos e Relatório de Matrículas Não Encontradas (2026-09-22 16:19:39 -03:00)
- **Descarte de Caracteres de Controle (`aluno[0..2]`)**:
  - A função `clean_matricula` em `database.py` e o parser `DatParser` em `services/dat_parser.py` foram atualizados para descartar os 3 primeiros caracteres de controle gerados por outro sistema (`aluno[0..2]`) para todas as comparações e operações.
  - A matrícula extraída corresponde a `aluno[3..6]` (4 dígitos). A comparação remove zeros à esquerda, garantindo equivalência entre `0004502`, `04502` e `4502`.
- **Relatório Restrito a Matrículas Não Encontradas (`ui/tabs/processing_tab.py`)**:
  - O relatório de inconsistências na aba **Processar .DAT** foi ajustado para listar exclusivamente as matrículas que não foram encontradas no cadastro de alunos do banco de dados.
- **Ação "Corrigir Dados" com Cadastro e Vínculo Manual**:
  - A janela "Corrigir Dados" exibe o erro de matrícula não encontrada.
  - Permite alterar a matrícula (com busca dinâmica no cadastro) ou preencher manualmente o **Nome** e a **Turma** para cadastrar o aluno na tabela `alunos` e salvar o resultado da prova em questão.
- **Validação com Testes de Unidade**:
  - Adicionado `tests/test_dat_matricula_and_errors.py` para validar a normalização de matrículas e o fluxo de cadastro/processamento. Todas as 25 suítes de teste estão aprovadas (`25/25 passed`).

### 3.10 Modo de Visualização "Por Disciplina (Acertos)" (2026-09-22 16:48:00 -03:00)
- **Novo Modo de Relatório (`disciplina_acertos`)**:
  - Adicionada a 4ª opção no seletor de modo de visualização de relatórios: `"Por Disciplina (Acertos)"` (`"disciplina_acertos"`).
  - Exibe o número exato de acertos por disciplina (valores inteiros) em vez da nota ponderada (0 a 10).
  - Configurado para **orientação Normal/Retrato (Portrait)** nas exportações de documentos e impressão direta, otimizando o espaço da página A4.
  - Adicionada a coluna `'Total'`, que exibe a soma total de acertos por aluno.
- **Suporte Integrado em Todos os Formatos de Exportação e Impressão**:
  - Atualizada a tabela GUI (`ui/tabs/reports_tab.py`), o relatório de Impressão Direta A4 (HTML Portrait), PDF (`ReportLab`), Excel (`OpenPyXL`) e Word (`Python-Docx`).
- **Validação com Testes de Unidade**:
  - Atualizado `tests/test_report_view_modes.py` para verificar o novo modo de visualização em todos os exportadores e na GUI. Suíte completa de testes aprovada (`25/25 passed`).

### 3.11 Sprint de Refinamentos: Dimensionamento, Nomenclatura (Modelo), Peso de Questões, Trimestre, Tipos de Prova e Histórico de Boletim (2026-09-24)
- **Dimensionamento das Janelas e Inicialização em Tela Cheia**:
  - Configurado `window.showMaximized()` em `main.py` para inicializar o sistema em tela cheia por padrão.
  - Aplicado padding uniforme de 10px (`layout.setContentsMargins(10, 10, 10, 10)`) e dimensionamento calculado (`resize` / `setMinimumSize`) em todas as janelas básicas e diálogos flutuantes (`ExamFormDialog`, `AddPartDialog`, `GabaritoMultiPartDialog`, `SubjectRangeDialog`, `StudentFormDialog`, `StudentDetailDialog`, `BlockFormDialog`, `SubjectFormDialog`, `DuplicateStudentDialog`, `HeaderFixDialog`, `EssayGradesDialog`).
  - Ajustada a responsividade da tabela de resultados GUI (`tbl_results` em `reports_tab.py`), que passou a expandir dinamicamente a coluna do nome do aluno (`QHeaderView.ResizeMode.Stretch`), preenchendo 100% da largura em tela cheia.
- **Mudança de Nomenclatura ("Tipo" -> "Modelo")**:
  - Alterada a palavra "Tipo" para **"Modelo"** na identificação dos gabaritos de respostas dos alunos (ex: Modelo 1, Modelo 2, Modelo A, Modelo B).
  - Migrado o banco de dados SQLite (`modelo` na tabela `prova_gabaritos` e `modelo_prova` na tabela `prova_processamentos`).
  - Atualizadas as interfaces gráficas, formulários, tabelas e cabeçalhos dos relatórios (PDF, Excel, Word, Impressão Direta).
- **Mapeamento de Disciplinas com Atributo "Peso"**:
  - Adicionado o campo de preenchimento obrigatório **Peso por Questão** (`spin_peso`) na janela de mapeamento posicional de disciplinas (`SubjectRangeDialog`).
  - Atualizado o motor de correção `GradingEngine` para calcular `soma_pesos_acertos` e `soma_pesos_totais`.
- **Seleção de Trimestre**:
  - Adicionada a seleção do **Trimestre** ("1º Trimestre", "2º Trimestre", "3º Trimestre") no cadastro de provas (`provas.trimestre`).
  - Adicionado filtro de seleção de trimestre no painel de relatórios (`reports_tab.py`).
- **Opção de Tipo de Prova e Regras de Visualização**:
  - Adicionado o atributo **Tipo de Prova** ("Prova Regular", "Simulado", "Prova de Seleção", "Atividade de Rotina") no cadastro do exame (`provas.tipo_prova`).
  - A visualização por blocos passou a ser exibida somente para exames que possuem blocos vinculados.
  - **Prova Regular**: Exibição por disciplina com cálculo de nota `round(acertos * peso, 1)`. Cabeçalho mostra nome por extenso se forem <= 3 disciplinas ou siglas se forem >= 4 disciplinas.
  - **Simulado**: Suporte a visualização Geral (Acertos por Bloco), Por Disciplina (Acertos) e Por Disciplina (Notas).
  - **Prova de Seleção**: Exibição exclusiva Por Disciplina (Acertos), sem armazenamento de histórico longitudinal.
  - **Atividade de Rotina**: Mantida 100% customizável.
- **Tabela para Boletim Futuro (`historico_notas`)**:
  - Criada a tabela `historico_notas` no banco de dados SQLite para armazenar as notas e acertos agregados por aluno x disciplina x data x trimestre.
- **Validação com Suíte de Testes**:
  - Criado `tests/test_new_sprint_features.py`. Suíte completa de 26 testes aprovada (`26/26 passed`).

### 3.12 Sprint de Edição de Gabarito em Tabela, Anulação de Questões, Pesos Decimais e Padrão de Relatórios (2026-09-24)
- **Suporte a Pesos Decimais com 4 Casas (0,0001 a 100,0000)**:
  - Modificada a entrada de pesos no formulário de disciplinas (`SubjectRangeDialog.spin_peso`) para aceitar até 4 casas decimais (`setDecimals(4)` e `setSingleStep(0.0001)`), viabilizando pesos fracionados precisos (ex: `0.3333` ou `0.1111`).
  - Na exibição dos relatórios da **Prova Regular**, as notas de disciplinas mantêm aproximação para 1 casa decimal (`.1f`).
- **Padrão de Orientação (A4 Vertical vs Landscape)**:
  - Todos os relatórios exportados (PDF, Excel, Word) e Impressão Direta foram padronizados para **Vertical / Retrato (Portrait)** por padrão.
  - Provas do tipo **"Simulado"** permanecem em **Landscape (Paisagem)**.
  - As larguras das colunas em PDF (`ReportLab`) foram recalculadas para ocupar 100% da folha A4 (19.0 cm em Retrato e 27.3 cm em Paisagem).
- **Correção da Quebra de Páginas na Impressão Direta**:
  - Ajustadas as regras de CSS em `print_report` (`reports_tab.py`) com `page-break-inside: avoid !important;`, bordas explícitas `1px solid #CBD5E1 !important;` e zebrado `tr:nth-child(even)` para impedir a perda de linhas divisórias/bordas inferiores na quebra de página.
- **Cabeçalho Unificado em 4 Linhas com Destaques**:
  - Padronizado o cabeçalho de todos os documentos exportados e impressos para a estrutura de 4 linhas:
    ```
    ${titulo} - ${data}
    Relatório de Prova
    Turma: ${turma}
    ${modo_de_visualizacao} | Alunos processados: ${qtd_alunos}
    ```
- **Aprimoramento Visual das Tabelas GUI**:
  - Ativadas cores alternadas (`setAlternatingRowColors(True)`) e seleção por linha (`SelectRows`) em todas as tabelas da interface.
  - Adicionado estilo QSS em `ui/theme.py` para cores alternadas `#F8FAFC`, linhas de grade `#CBD5E1` e efeito hover `#E2E8F0` na linha apontada pelo cursor.
- **Edição Estruturada de Gabaritos em Tabela e Anulação de Questões**:
  - Criado o diálogo `GabaritoTableDialog` (`ui/tabs/exams_tab.py`) que permite visualizar e alterar o gabarito linha a linha em uma tabela interativa (`QTableWidget`), com suporte a colagem rápida de strings.
  - Permitida a anulação de questões (marcação com `*`). Ao anular uma questão, é exibido um aviso pop-up (`QMessageBox.information`) informando que o lote de respostas precisa ser reprocessado na aba de Processamento.
- **Redistribuição Automática de Pesos e Critérios de Aproximação**:
  - Atualizado o motor `GradingEngine` (`services/grading_engine.py`): ao anular questões em uma disciplina, o peso das questões anuladas torna-se `0.0` e o valor total da disciplina ($V_D$) é automaticamente redistribuído entre as questões ativas remanescentes ($W_{\text{ativa}} = V_D / N_{\text{ativas}}$).
  - Implementada a regra de aproximação automática de **100% de acertos**: se o aluno acertar todas as questões ativas de uma disciplina ou de toda a prova, sua pontuação é fixada na nota máxima inteira (ex: `10.0`), eliminando perdas por dízimas periódicas.
- **Validação com Suíte de Testes**:
  - Criado `tests/test_question_annulment.py` e atualizado `tests/test_report_view_modes.py`. Suíte completa de 31 testes aprovada (`31/31 passed`).

---

## 🤖 Orientações para Agentes de IA Futuros

Ao estender ou modificar esta codebase, mantenha as seguintes premissas:

1. **Integridade de Ordenação**:
   - Ao implementar novas visões de resultado, certifique-se de que a ordenação por pontuação considere `total_acertos + nota_redacao` se houver redação na prova.

2. **Índices de Colunas na GUI vs Exportações**:
   - A tabela da GUI (`tbl_results` em `reports_tab.py`) possui uma coluna final de ação (`Ação` com botão de Boletim Individual).
   - As exportações (PDF, Excel, Word) e a Impressão Direta **NÃO** devem conter a coluna de `Ação`.
   - A primeira coluna de dados é sempre o número sequencial do aluno (`""`), seguido por `Matrícula`, `Nome do Aluno`, `Turma` e `Modelo`.

3. **Validação de Testes**:
   - Toda alteração nas colunas da tabela GUI exige a atualização dos índices verificados em `tests/test_report_view_modes.py`.
   - Execute sempre `python -m pytest` para validar que todas as suítes permanecem aprovadas (31/31).



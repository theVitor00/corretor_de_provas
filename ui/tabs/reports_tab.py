import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QGroupBox,
    QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QRect, QMarginsF, QUrl
from PyQt6.QtGui import QPainter, QColor, QFont, QTextDocument, QPageLayout, QImage
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from models.subject import SubjectBlockModel
from services.exporter import ReportExporter
from services.abbreviations import get_acronym, get_header_tooltip, get_legend_mapping, is_subject_applicable_to_tipo
from ui.tabs.students_tab import StudentDetailDialog


class GroupedHeaderView(QHeaderView):
    """
    Cabeçalho de duas linhas customizado para QTableWidget.
    - Linha 1 (Superior): Comporta-se como uma única coluna integrada (Colspan Total)
      que se expande por todo o espaço do topo com o texto 'ACERTOS' ou 'NOTAS'.
    - Linha 2 (Inferior): Exibe os rótulos e siglas/nomes individuais das colunas.
    """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.group_title = "NOTAS"
        self.column_labels = []
        self.setFixedHeight(52)

    def set_group_config(self, title: str, labels: list):
        self.group_title = str(title).upper()
        self.column_labels = labels
        self.viewport().update()

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        if not rect.isValid():
            return

        painter.save()
        
        # Dimensões das duas linhas
        h_half = rect.height() // 2
        r_top = QRect(rect.x(), rect.y(), rect.width(), h_half)
        r_bot = QRect(rect.x(), rect.y() + h_half, rect.width(), rect.height() - h_half)

        bg_top = QColor("#1E293B")  # Cor uniforme para o cabeçalho superior unificado (Colspan)
        bg_bot = QColor("#242D64")  # Cor para a linha de colunas individuais
        border_color = QColor("#CBD5E1")
        text_color = QColor("#FFFFFF")

        # --- LINHA 1 (SUPERIOR): UNIFICADA COMO UMA ÚNICA COLUNA EM TODO O TOPO ---
        painter.fillRect(r_top, bg_top)

        # Calcular largura total do viewport da tabela para centralização perfeita da barra única
        total_header_w = max(self.viewport().width(), self.length())
        full_top_rect = QRect(0, 0, total_header_w, h_half)

        # Desativar o clipping local para desenhar o título do Colspan de forma totalmente contínua
        painter.setClipping(False)
        painter.setPen(text_color)
        font_top = QFont("Helvetica", 10, QFont.Weight.Bold)
        font_top.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        painter.setFont(font_top)
        painter.drawText(full_top_rect, Qt.AlignmentFlag.AlignCenter, f"  {self.group_title}  ")

        # Borda separadora horizontal contínua entre Linha 1 e Linha 2
        painter.setPen(border_color)
        painter.drawLine(rect.x(), rect.y() + h_half - 1, rect.x() + rect.width(), rect.y() + h_half - 1)

        # --- LINHA 2 (INFERIOR): COLUNAS INDIVIDUAIS ---
        painter.setClipping(True)
        painter.setClipRect(rect)
        painter.fillRect(r_bot, bg_bot)
        
        lbl_text = self.column_labels[logicalIndex] if logicalIndex < len(self.column_labels) else ""

        painter.setPen(text_color)
        font_bot = QFont("Helvetica", 8, QFont.Weight.Bold)
        painter.setFont(font_bot)
        painter.drawText(r_bot, Qt.AlignmentFlag.AlignCenter, lbl_text)

        # Borda vertical separadora apenas na linha inferior
        painter.setPen(border_color)
        painter.drawLine(rect.x() + rect.width() - 1, rect.y() + h_half, rect.x() + rect.width() - 1, rect.y() + rect.height())

        painter.restore()


class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.subject_model = SubjectBlockModel()
        self.exporter = ReportExporter()
        self.current_results = []
        self.current_exam = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Filters Bar
        gb_filters = QGroupBox("Filtros e Modo de Visualização")
        h_f = QHBoxLayout(gb_filters)

        self.combo_trimestre = QComboBox()
        self.combo_trimestre.addItem("Todos os Trimestres", "Todos")
        self.combo_trimestre.addItem("1º Trimestre", "1º Trimestre")
        self.combo_trimestre.addItem("2º Trimestre", "2º Trimestre")
        self.combo_trimestre.addItem("3º Trimestre", "3º Trimestre")
        self.combo_trimestre.currentIndexChanged.connect(self.load_exams_combo)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.load_results)

        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItem("Geral (Acertos por Bloco)", "geral")
        self.combo_view_mode.addItem("Por Bloco (Notas 0 a 10)", "bloco")
        self.combo_view_mode.addItem("Por Disciplina (Notas 0 a 10)", "disciplina")
        self.combo_view_mode.addItem("Por Disciplina (Acertos)", "disciplina_acertos")
        self.combo_view_mode.currentIndexChanged.connect(self.load_results)

        self.combo_turma = QComboBox()
        self.combo_turma.currentIndexChanged.connect(self.load_results)

        self.combo_sort = QComboBox()
        self.combo_sort.addItem("Nome (A-Z)", "nome")
        self.combo_sort.addItem("Maior Nota", "nota_desc")
        self.combo_sort.addItem("Menor Nota", "nota_asc")
        self.combo_sort.addItem("Matrícula", "matricula")
        self.combo_sort.currentIndexChanged.connect(self.load_results)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar por nome ou matrícula...")
        self.txt_search.textChanged.connect(self.load_results)

        h_f.addWidget(QLabel("Trimestre:"))
        h_f.addWidget(self.combo_trimestre, 1)
        h_f.addWidget(QLabel("Prova:"))
        h_f.addWidget(self.combo_exam, 2)
        h_f.addWidget(QLabel("Visualização:"))
        h_f.addWidget(self.combo_view_mode, 2)
        h_f.addWidget(QLabel("Turma:"))
        h_f.addWidget(self.combo_turma, 1)
        h_f.addWidget(QLabel("Ordenar:"))
        h_f.addWidget(self.combo_sort, 1)
        h_f.addWidget(self.txt_search, 2)

        layout.addWidget(gb_filters)

        # Summary Cards
        h_summary = QHBoxLayout()
        self.lbl_card_avg = QLabel("<b>Média da Turma:</b> -")
        self.lbl_card_max = QLabel("<b>Maior Nota:</b> -")
        self.lbl_card_min = QLabel("<b>Menor Nota:</b> -")
        self.lbl_card_count = QLabel("<b>Total Alunos:</b> -")

        for lbl in [self.lbl_card_avg, self.lbl_card_max, self.lbl_card_min, self.lbl_card_count]:
            lbl.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px; font-size: 13px;")
            h_summary.addWidget(lbl)

        layout.addLayout(h_summary)

        # Action / Export Bar
        h_exports = QHBoxLayout()
        
        btn_pdf = QPushButton("Exportar PDF (A4 Oficial)")
        btn_pdf.setIcon(qta.icon('fa5s.file-pdf', color='white'))
        btn_pdf.setObjectName("btnNavy")
        btn_pdf.clicked.connect(self.export_pdf)

        btn_excel = QPushButton("Exportar Excel (.xlsx)")
        btn_excel.setIcon(qta.icon('fa5s.file-excel', color='#242D64'))
        btn_excel.setObjectName("btnSecondary")
        btn_excel.clicked.connect(self.export_excel)

        btn_word = QPushButton("Exportar Word (.docx)")
        btn_word.setIcon(qta.icon('fa5s.file-word', color='#242D64'))
        btn_word.setObjectName("btnSecondary")
        btn_word.clicked.connect(self.export_word)

        btn_print = QPushButton("Imprimir (A4)")
        btn_print.setIcon(qta.icon('fa5s.print', color='#242D64'))
        btn_print.setObjectName("btnSecondary")
        btn_print.clicked.connect(self.print_report)

        h_exports.addWidget(btn_pdf)
        h_exports.addWidget(btn_excel)
        h_exports.addWidget(btn_word)
        h_exports.addWidget(btn_print)
        h_exports.addStretch()

        layout.addLayout(h_exports)

        # Painel de Legenda (entre botões e tabela)
        self.gb_legend = QGroupBox("Legenda")
        l_legend = QHBoxLayout(self.gb_legend)
        l_legend.setContentsMargins(10, 4, 10, 6)
        self.lbl_legend = QLabel()
        self.lbl_legend.setWordWrap(True)
        self.lbl_legend.setStyleSheet("font-size: 11px; color: #334155;")
        l_legend.addWidget(self.lbl_legend)
        self.gb_legend.setVisible(False)

        layout.addWidget(self.gb_legend)

        # Table Area com Cabeçalho Unificado em Duas Linhas
        self.tbl_results = QTableWidget()
        self.tbl_results.setAlternatingRowColors(True)
        self.tbl_results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.header_view = GroupedHeaderView(Qt.Orientation.Horizontal, self.tbl_results)
        self.tbl_results.setHorizontalHeader(self.header_view)
        self.tbl_results.verticalHeader().setDefaultSectionSize(44)
        self.tbl_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tbl_results.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.tbl_results.horizontalHeader().setStretchLastSection(False)

        layout.addWidget(self.tbl_results)

        self.load_exams_combo()

    def load_exams_combo(self):
        self.combo_exam.blockSignals(True)
        self.combo_exam.clear()
        self.combo_exam.addItem("Selecione uma prova...", None)

        trim_val = self.combo_trimestre.currentData()
        exams = self.exam_model.list_exams()

        for e in exams:
            if trim_val and trim_val != "Todos":
                if e.get("trimestre") != trim_val:
                    continue
            self.combo_exam.addItem(f"{e['nome']} ({e['data']})", e["id"])

        self.combo_exam.blockSignals(False)

        # Turmas
        self.combo_turma.blockSignals(True)
        self.combo_turma.clear()
        self.combo_turma.addItem("Todas as Turmas", "Todas")
        for t in self.student_model.list_turmas():
            self.combo_turma.addItem(t, t)
        self.combo_turma.blockSignals(False)
        self.load_results()

    def select_exam(self, exam_id: int):
        self.load_exams_combo()
        idx = self.combo_exam.findData(exam_id)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)

    def get_current_turma_subtitle(self) -> str:
        turma_val = self.combo_turma.currentData()
        if not turma_val or turma_val == "Todas":
            return "Geral - Para Todas as Turmas"
        return str(turma_val)

    def _get_block_mapping(self, exam: dict) -> dict:
        disc_db = {d["nome"].strip().lower(): d.get("bloco_nome") for d in self.subject_model.list_subjects()}
        blocos_list = exam.get("blocos_list", [])
        exam_block_names = [b["nome"] for b in blocos_list] if blocos_list else []
        return {
            "disc_to_block": disc_db,
            "exam_blocks": exam_block_names
        }

    def get_effective_view_mode(self) -> str:
        if not self.current_exam:
            return self.combo_view_mode.currentData() or "geral"

        view_mode = self.combo_view_mode.currentData() or "geral"
        has_blocos = bool(self.current_exam.get("blocos_list"))
        tipo_prova_cat = self.current_exam.get("tipo_prova", "Prova Regular")

        if not has_blocos and view_mode in ["geral", "bloco"]:
            view_mode = "disciplina"

        if tipo_prova_cat == "Prova Regular":
            if view_mode not in ["disciplina", "disciplina_acertos"]:
                view_mode = "disciplina"
        elif tipo_prova_cat == "Prova de Seleção":
            view_mode = "disciplina_acertos"

        return view_mode

    def load_results(self):
        exam_id = self.combo_exam.currentData()
        if not exam_id:
            self.current_exam = None
            self.current_results = []
            self.tbl_results.setRowCount(0)
            self.gb_legend.setVisible(False)
            self.update_cards([])
            return

        self.current_exam = self.exam_model.get_exam_by_id(exam_id)
        possui_redacao = bool(self.current_exam.get("possui_redacao", False))
        tipo_prova_cat = self.current_exam.get("tipo_prova", "Prova Regular")

        turma_val = self.combo_turma.currentData()
        sort_val = self.combo_sort.currentData()
        search_val = self.txt_search.text().strip()
        view_mode = self.get_effective_view_mode()

        self.current_results = self.processing_model.list_results_for_exam(
            exam_id, turma_filter=turma_val, sort_by=sort_val, search=search_val
        )

        def get_final_score(r):
            n_red = (r.get("nota_redacao") or 0.0) if possui_redacao else 0.0
            if view_mode in ["geral", "disciplina_acertos"]:
                return float(r.get("total_acertos", 0)) + float(n_red)
            else:
                return float(r.get("nota_final", 0.0)) + float(n_red)

        if sort_val == "nota_desc":
            self.current_results.sort(key=lambda r: (get_final_score(r), str(r.get("aluno_nome", ""))), reverse=False)
            self.current_results.sort(key=lambda r: get_final_score(r), reverse=True)
        elif sort_val == "nota_asc":
            self.current_results.sort(key=lambda r: (get_final_score(r), str(r.get("aluno_nome", ""))))

        self.update_cards(self.current_results)

        b_map_info = self._get_block_mapping(self.current_exam)
        disc_db_map = b_map_info["disc_to_block"]
        exam_blocks = b_map_info["exam_blocks"]

        # 1. Identificar lista consistente de disciplinas cadastradas para a prova
        mapped_subjects = self.current_exam.get("layout_config", {}).get("subjects", [])
        exam_disc_list = []
        for s in mapped_subjects:
            n = s.get("nome", "").strip()
            if n and n.lower() != "geral" and n not in exam_disc_list:
                exam_disc_list.append(n)

        # Buscar disciplinas nos resultados como fallback se não houver mapeamento prévio
        disc_set_results = set()
        for r in self.current_results:
            det = r.get("detalhes_disciplinas", {})
            for d_name in det.keys():
                if d_name.strip().lower() != "geral":
                    disc_set_results.add(d_name.strip())

        for d in sorted(list(disc_set_results)):
            if d not in exam_disc_list:
                exam_disc_list.append(d)

        # 2. Determinar colunas de dados baseado no modo de visualização
        mid_headers_full = []
        mid_headers_labels = []
        
        if view_mode in ["geral", "bloco"]:
            block_set = set()
            if exam_blocks:
                for b in exam_blocks:
                    block_set.add(b)
            else:
                for d in exam_disc_list:
                    b_name = disc_db_map.get(d.lower()) or "Geral"
                    block_set.add(b_name)
            
            mid_headers_full = sorted(list(block_set))
            mid_headers_labels = [get_acronym(b) for b in mid_headers_full]
            group_title = "Acertos" if view_mode == "geral" else "Notas"
        else: # view_mode in ["disciplina", "disciplina_acertos"]
            mid_headers_full = exam_disc_list
            if tipo_prova_cat == "Prova Regular" and len(mid_headers_full) <= 3:
                # 3 disciplinas ou menos: nome por extenso
                mid_headers_labels = mid_headers_full
            else:
                # 4 ou mais disciplinas: siglas
                mid_headers_labels = [get_acronym(d) for d in mid_headers_full]
            group_title = "Acertos" if view_mode == "disciplina_acertos" else "Notas"

        # Atualizar painel de Legenda das Siglas
        leg_map = get_legend_mapping(mid_headers_full, possesses_redacao=possui_redacao)
        if leg_map:
            leg_items = [f"<b>{k}</b> = {v}" for k, v in leg_map.items()]
            self.lbl_legend.setText(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(leg_items))
            self.gb_legend.setVisible(True)
        else:
            self.gb_legend.setVisible(False)

        # 3. Definição estrita da ordem das colunas da tabela GUI
        base_left = ["", "Matrícula", "Nome do Aluno", "Turma", "Modelo"]
        base_right = []
        if view_mode in ["geral", "disciplina_acertos"]:
            base_right.append("Total")
        if possui_redacao:
            red_label = "RED" if view_mode == "disciplina" else "Redação"
            base_right.append(red_label)
        if (possui_redacao or view_mode not in ["geral", "disciplina", "disciplina_acertos"]):
            base_right.append("Nota Final")
        base_right.append("Ação")

        all_column_labels = base_left + mid_headers_labels + base_right
        
        start_data_col = 5
        num_mid = len(mid_headers_full)
        action_col_idx = len(all_column_labels) - 1

        self.tbl_results.clear()
        self.tbl_results.setColumnCount(len(all_column_labels))
        self.tbl_results.setHorizontalHeaderLabels(all_column_labels)
        self.header_view.set_group_config(group_title, all_column_labels)

        # Tooltips explicativos
        for col_idx, label in enumerate(all_column_labels):
            item = self.tbl_results.horizontalHeaderItem(col_idx)
            if not item:
                item = QTableWidgetItem(label)
                self.tbl_results.setHorizontalHeaderItem(col_idx, item)

            if start_data_col <= col_idx < start_data_col + num_mid:
                full_n = mid_headers_full[col_idx - start_data_col]
                tt = get_header_tooltip(full_n, mode=view_mode)
                item.setToolTip(tt)
            elif label == "Total":
                item.setToolTip("Total de questões acertadas na prova inteira")
            elif label in ["Redação", "RED"]:
                item.setToolTip("Nota de redação inserida manualmente ou via CSV")
            elif label == "Nota Final":
                item.setToolTip("Nota final do aluno (Total + Redação se houver)")

        # Configuração responsiva de largura das colunas
        font_metrics = self.tbl_results.fontMetrics()
        max_name_px = font_metrics.horizontalAdvance("Nome do Aluno")
        for r in self.current_results:
            w = font_metrics.horizontalAdvance(str(r.get("aluno_nome", "")))
            if w > max_name_px:
                max_name_px = w
        aluno_col_width = max(max_name_px + 24, 220)

        header = self.tbl_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # # (Index)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Matrícula
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Nome do Aluno (expande dinamicamente)
        self.tbl_results.setColumnWidth(2, aluno_col_width)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Turma
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Modelo

        for c_i in range(start_data_col, action_col_idx):
            header.setSectionResizeMode(c_i, QHeaderView.ResizeMode.ResizeToContents)

        header.setSectionResizeMode(action_col_idx, QHeaderView.ResizeMode.Fixed) # Ação (Boletim)
        self.tbl_results.setColumnWidth(action_col_idx, 160)

        # 4. Preenchimento de dados garantindo rigidez total nos índices das colunas
        self.tbl_results.setRowCount(len(self.current_results))
        for row_idx, r in enumerate(self.current_results):
            det = r.get("detalhes_disciplinas", {})

            # Colunas de identificação (0: Numeração, 1: Matrícula, 2: Nome, 3: Turma, 4: Modelo)
            item_seq = QTableWidgetItem(str(row_idx + 1))
            item_seq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_results.setItem(row_idx, 0, item_seq)
            self.tbl_results.setItem(row_idx, 1, QTableWidgetItem(str(r["aluno_matricula"])))
            self.tbl_results.setItem(row_idx, 2, QTableWidgetItem(str(r["aluno_nome"])))
            self.tbl_results.setItem(row_idx, 3, QTableWidgetItem(str(r["aluno_turma"])))
            
            modelo_str = str(r.get("modelo_prova") or r.get("tipo_prova", ""))
            self.tbl_results.setItem(row_idx, 4, QTableWidgetItem(modelo_str))

            # Garantir que NENHUM widget residual permaneça nas colunas de dados
            for c_i in range(0, action_col_idx):
                self.tbl_results.removeCellWidget(row_idx, c_i)

            # Colunas do meio (disciplinas/blocos)
            for i, item_name in enumerate(mid_headers_full):
                target_col = start_data_col + i

                if view_mode == "geral":
                    b_acertos = 0
                    for d_k, d_v in det.items():
                        if d_k.strip().lower() == "geral":
                            continue
                        d_b = disc_db_map.get(d_k.strip().lower()) or "Geral"
                        if d_b == item_name or (len(mid_headers_full) == 1):
                            b_acertos += d_v.get("acertos", 0)

                    item = QTableWidgetItem(str(b_acertos))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_results.setItem(row_idx, target_col, item)

                elif view_mode == "bloco":
                    b_acertos = 0
                    b_total_q = 0
                    for d_k, d_v in det.items():
                        if d_k.strip().lower() == "geral":
                            continue
                        d_b = disc_db_map.get(d_k.strip().lower()) or "Geral"
                        if d_b == item_name or (len(mid_headers_full) == 1):
                            b_acertos += d_v.get("acertos", 0)
                            b_total_q += d_v.get("total", 0)

                    b_nota = (b_acertos / b_total_q * 10.0) if b_total_q > 0 else 0.0
                    item = QTableWidgetItem(f"{b_nota:.2f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_results.setItem(row_idx, target_col, item)

                else: # view_mode in ["disciplina", "disciplina_acertos"]
                    if not is_subject_applicable_to_tipo(item_name, modelo_str):
                        item = QTableWidgetItem("-")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tbl_results.setItem(row_idx, target_col, item)
                    else:
                        d_info = det.get(item_name)
                        if not d_info:
                            for k, v in det.items():
                                if k.strip().lower() == item_name.strip().lower():
                                    d_info = v
                                    break
                        if not d_info:
                            d_info = {}

                        tot = d_info.get("total", 0)
                        ac = d_info.get("acertos", 0)

                        if view_mode == "disciplina_acertos":
                            item = QTableWidgetItem(str(ac))
                        else:
                            if tipo_prova_cat == "Prova Regular":
                                n_disc = d_info.get("nota", round(ac * 1.0, 1))
                                item = QTableWidgetItem(f"{n_disc:.1f}")
                            else:
                                n_disc = (ac / tot * 10.0) if tot > 0 else d_info.get("nota", 0.0)
                                item = QTableWidgetItem(f"{n_disc:.2f}")

                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tbl_results.setItem(row_idx, target_col, item)

            curr_c = start_data_col + num_mid

            # Coluna Total (em Geral e Disciplina Acertos)
            if view_mode in ["geral", "disciplina_acertos"]:
                if view_mode == "geral":
                    tot_str = f"{r['total_acertos']}/{r['total_questoes']}"
                else:
                    tot_str = str(r['total_acertos'])
                tot_item = QTableWidgetItem(tot_str)
                tot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_results.setItem(row_idx, curr_c, tot_item)
                curr_c += 1

            # Coluna Redação
            if possui_redacao:
                n_red = r.get("nota_redacao")
                n_red_str = f"{n_red:.2f}" if n_red is not None else "0.00"
                red_item = QTableWidgetItem(n_red_str)
                red_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_results.setItem(row_idx, curr_c, red_item)
                curr_c += 1

            # Coluna Nota Final
            if (possui_redacao or view_mode not in ["geral", "disciplina", "disciplina_acertos"]):
                n_red_val = r.get("nota_redacao") or 0.0 if possui_redacao else 0.0
                if view_mode == "geral":
                    fn_val = float(r.get("total_acertos", 0)) + n_red_val
                else:
                    fn_val = float(r.get("nota_final", 0.0)) + n_red_val

                fn_item = QTableWidgetItem(f"{fn_val:.2f}")
                fn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_results.setItem(row_idx, curr_c, fn_item)
                curr_c += 1

            # Coluna de Ação (Boletim Individual) EXCLUSIVAMENTE NO ÍNDICE FIXO action_col_idx
            btn_view = QPushButton("Boletim Individual")
            btn_view.setIcon(qta.icon('fa5s.id-card', color='#242D64'))
            btn_view.setObjectName("btnSecondary")
            btn_view.setMinimumWidth(140)
            btn_view.clicked.connect(lambda _, item_data=r: self.view_individual_report(item_data))
            self.tbl_results.setCellWidget(row_idx, action_col_idx, btn_view)

    def update_cards(self, results: list):
        turma_sub = self.get_current_turma_subtitle()
        if not results:
            self.lbl_card_avg.setText(f"<b>Turma:</b> {turma_sub}<br><b>Média:</b> -")
            self.lbl_card_max.setText("<b>Maior Nota:</b> -")
            self.lbl_card_min.setText("<b>Menor Nota:</b> -")
            self.lbl_card_count.setText("<b>Total Alunos:</b> 0")
            return

        possui_redacao = bool(self.current_exam.get("possui_redacao", False)) if self.current_exam else False
        view_mode = self.combo_view_mode.currentData() or "geral"

        notas = []
        for r in results:
            n_red_val = (r.get("nota_redacao") or 0.0) if possui_redacao else 0.0
            if view_mode in ["geral", "disciplina_acertos"]:
                val = float(r.get("total_acertos", 0)) + n_red_val
            else:
                val = float(r.get("nota_final", 0.0)) + n_red_val
            notas.append(val)

        avg = sum(notas) / len(notas)
        max_n = max(notas)
        min_n = min(notas)

        self.lbl_card_avg.setText(f"<b>Turma:</b> {turma_sub}<br><b>Média:</b> <font color='#00A9A4'><b>{avg:.2f}</b></font>")
        self.lbl_card_max.setText(f"<b>Maior Nota:</b> <font color='#10B981'><b>{max_n:.2f}</b></font>")
        self.lbl_card_min.setText(f"<b>Menor Nota:</b> <font color='#EF4444'><b>{min_n:.2f}</b></font>")
        self.lbl_card_count.setText(f"<b>Total Alunos:</b> {len(results)}")

    def view_individual_report(self, result_item: dict):
        student = self.student_model.get_by_matricula(result_item["aluno_matricula"])
        if student:
            dlg = StudentDetailDialog(student["id"], self.student_model, self)
            dlg.exec()
        else:
            QMessageBox.information(
                self, "Boletim Individual",
                f"Aluno: {result_item['aluno_nome']} (Matrícula: {result_item['aluno_matricula']})\n"
                f"Nota Final: {result_item['nota_final']:.2f}\n"
                f"Acertos: {result_item['total_acertos']}/{result_item['total_questoes']} ({result_item['percentual_acertos']:.1f}%)"
            )

    def export_pdf(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de exportar.")
            return

        view_mode = self.get_effective_view_mode()
        filename = f"Relatorio_{view_mode}_{self.current_exam['nome'].replace(' ', '_')}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", filename, "Arquivos PDF (*.pdf)")
        if filepath:
            try:
                self.exporter.export_exam_pdf(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle(),
                    view_mode=view_mode
                )
                QMessageBox.information(self, "Sucesso", f"Relatório PDF ({view_mode.upper()}) exportado com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF:\n{str(e)}")

    def export_excel(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de exportar.")
            return

        view_mode = self.get_effective_view_mode()
        filename = f"Resultados_{view_mode}_{self.current_exam['nome'].replace(' ', '_')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha Excel", filename, "Arquivos Excel (*.xlsx)")
        if filepath:
            try:
                self.exporter.export_exam_excel(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle(),
                    view_mode=view_mode
                )
                QMessageBox.information(self, "Sucesso", f"Planilha Excel ({view_mode.upper()}) exportada com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar Excel:\n{str(e)}")

    def export_word(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de exportar.")
            return

        view_mode = self.get_effective_view_mode()
        filename = f"Relatorio_{view_mode}_{self.current_exam['nome'].replace(' ', '_')}.docx"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Documento Word", filename, "Arquivos Word (*.docx)")
        if filepath:
            try:
                self.exporter.export_exam_word(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle(),
                    view_mode=view_mode
                )
                QMessageBox.information(self, "Sucesso", f"Documento Word ({view_mode.upper()}) exportado com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar Word:\n{str(e)}")

    def print_report(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de imprimir.")
            return

        possui_redacao = bool(self.current_exam.get("possui_redacao", False))
        tipo_prova_cat = self.current_exam.get("tipo_prova", "Prova Regular")
        view_mode = self.get_effective_view_mode()
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        # Somente a prova do tipo Simulado deve ser impressa em Landscape. Todas as demais em Portrait.
        orientation = QPageLayout.Orientation.Landscape if (tipo_prova_cat == "Simulado") else QPageLayout.Orientation.Portrait

        page_layout = printer.pageLayout()
        page_layout.setOrientation(orientation)
        page_layout.setUnits(QPageLayout.Unit.Millimeter)
        page_layout.setMargins(QMarginsF(5.0, 5.0, 5.0, 5.0))
        printer.setPageLayout(page_layout)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            p_layout = printer.pageLayout()
            p_layout.setUnits(QPageLayout.Unit.Millimeter)
            p_layout.setMargins(QMarginsF(5.0, 5.0, 5.0, 5.0))
            printer.setPageLayout(p_layout)

            doc = QTextDocument()
            doc.setDocumentMargin(0)
            turma_sub = self.get_current_turma_subtitle()
            
            b_map_info = self._get_block_mapping(self.current_exam)
            disc_db_map = b_map_info["disc_to_block"]
            exam_blocks = b_map_info["exam_blocks"]

            mapped_subjects = self.current_exam.get("layout_config", {}).get("subjects", [])
            exam_disc_list = []
            for s in mapped_subjects:
                n = s.get("nome", "").strip()
                if n and n.lower() != "geral" and n not in exam_disc_list:
                    exam_disc_list.append(n)

            if not exam_disc_list:
                disc_set = set()
                for r in self.current_results:
                    det = r.get("detalhes_disciplinas", {})
                    for d_name in det.keys():
                        if d_name.strip().lower() != "geral":
                            disc_set.add(d_name.strip())
                exam_disc_list = sorted(list(disc_set))

            if view_mode in ["geral", "bloco"]:
                block_set = set(exam_blocks) if exam_blocks else {disc_db_map.get(d.lower()) or "Geral" for d in exam_disc_list}
                mid_full = sorted(list(block_set))
            else:
                mid_full = exam_disc_list

            if tipo_prova_cat == "Prova Regular" and len(mid_full) <= 3:
                mid_labels = mid_full
            else:
                mid_labels = [get_acronym(m) for m in mid_full]

            group_title = "Acertos" if view_mode in ["geral", "disciplina_acertos"] else "Notas"

            right_headers = []
            if view_mode in ["geral", "disciplina_acertos"]:
                right_headers.append("Total Acertos")
            if possui_redacao:
                red_title = "RED" if view_mode == "disciplina" else "Redação"
                right_headers.append(red_title)
            if (possui_redacao or view_mode not in ["geral", "disciplina", "disciplina_acertos"]):
                right_headers.append("Nota Final")

            view_mode_labels = {
                "geral": "Geral (Acertos por Bloco)",
                "bloco": "Por Bloco (Notas 0 a 10)",
                "disciplina": "Por Disciplina (Notas 0 a 10)",
                "disciplina_acertos": "Por Disciplina (Acertos)"
            }
            modo_label = view_mode_labels.get(view_mode, view_mode.upper())

            logo_path, _ = self.exporter._get_branding()
            logo_img_tag = ""
            if logo_path and os.path.exists(logo_path):
                img = QImage(logo_path)
                if not img.isNull():
                    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl("logo://brand"), img)
                    logo_img_tag = '<img src="logo://brand" class="logo-img" align="right" style="max-height: 48px; max-width: 180px; float: right;">'

            html = f"""
            <html>
            <head>
            <style>
                @page {{ margin: 5mm; }}
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; color: #1E293B; }}
                .header-table {{ width: 100%; border-collapse: collapse; margin: 0 0 6px 0; border: none; }}
                .header-td-left {{ border: none !important; text-align: left; vertical-align: middle; padding: 0 !important; }}
                .header-td-right {{ border: none !important; text-align: right; vertical-align: middle; padding: 0 !important; width: 190px; }}
                .logo-img {{ max-height: 48px; max-width: 180px; display: block; float: right; margin-left: auto; margin-right: 0; }}
                h2 {{ color: #242D64; margin-bottom: 2px; margin-top: 0; font-size: 14pt; }}
                h3 {{ color: #475569; margin-top: 2px; margin-bottom: 4px; font-size: 11pt; font-weight: bold; }}
                p {{ font-size: 9pt; color: #475569; margin: 2px 0; }}
                table.data-table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; margin-top: 6px; border: 1px solid #94A3B8; page-break-inside: auto; }}
                table.data-table tr {{ page-break-inside: avoid !important; page-break-after: auto; }}
                table.data-table tr:nth-child(even) td {{ background-color: #F8FAFC; }}
                table.data-table th {{ background-color: #242D64; color: white; padding: 4px 2px; font-weight: bold; text-align: center; border: 1px solid #64748B !important; }}
                table.data-table th.group-th {{ background-color: #1E293B; text-align: center; font-size: 9.5pt; font-weight: bold; border: 1px solid #475569 !important; }}
                table.data-table td {{ padding: 3px 2px; border: 1px solid #CBD5E1 !important; text-align: center; white-space: nowrap; }}
                table.data-table td.left {{ text-align: left; }}
                .aluno-nome {{ white-space: nowrap; word-break: keep-all; }}
                .legend-box {{ margin-top: 6px; margin-bottom: 6px; padding: 5px 8px; border: 1px solid #CBD5E1; background-color: #F8FAFC; font-size: 8pt; color: #334155; }}
            </style>
            </head>
            <body>
            """

            if logo_img_tag:
                html += f"""
                <table class="header-table" width="100%" border="0" style="width: 100%; border-collapse: collapse; margin-bottom: 6px;">
                    <tr>
                        <td class="header-td-left" align="left" valign="middle" style="border: none !important; text-align: left; vertical-align: middle;">
                            <h2>{self.current_exam['nome']} - {self.current_exam['data']}</h2>
                            <h3>Relatório de Prova</h3>
                            <p><b>Turma:</b> {turma_sub}</p>
                            <p><b>{modo_label}</b> &nbsp;|&nbsp; <b>Alunos processados:</b> {len(self.current_results)}</p>
                        </td>
                        <td class="header-td-right" align="right" valign="middle" style="border: none !important; text-align: right; vertical-align: middle; width: 190px;">
                            <div align="right" style="text-align: right; width: 100%;">
                                {logo_img_tag}
                            </div>
                        </td>
                    </tr>
                </table>
                """
            else:
                html += f"<h2>{self.current_exam['nome']} - {self.current_exam['data']}</h2>"
                html += "<h3>Relatório de Prova</h3>"
                html += f"<p><b>Turma:</b> {turma_sub}</p>"
                html += f"<p><b>{modo_label}</b> &nbsp;|&nbsp; <b>Alunos processados:</b> {len(self.current_results)}</p>"
            
            leg_map = get_legend_mapping(mid_full, possesses_redacao=possui_redacao)
            if leg_map:
                leg_items = [f"<b>{k}</b> = {v}" for k, v in leg_map.items()]
                html += f"<div class='legend-box'><b>Legenda:</b> {' | '.join(leg_items)}</div>"

            html += "<table class='data-table'>"
            
            total_cols_count_print = 5 + len(mid_labels) + len(right_headers)
            html += f"<tr><th colspan='{total_cols_count_print}' class='group-th'>{group_title.upper()}</th></tr>"

            html += "<tr><th></th><th>Matrícula</th><th>Aluno</th><th>Turma</th><th>Modelo</th>"
            for lbl in mid_labels:
                html += f"<th>{lbl}</th>"
            for rh in right_headers:
                html += f"<th>{rh}</th>"
            html += "</tr>"
            
            for row_idx, r in enumerate(self.current_results):
                det = r.get("detalhes_disciplinas", {})
                aluno_nome = str(r['aluno_nome']).replace("\n", " ").replace("\r", "")
                mod_str = str(r.get("modelo_prova") or r.get("tipo_prova", ""))
                html += f"<tr><td>{row_idx + 1}</td><td>{r['aluno_matricula']}</td><td class='left aluno-nome'><nobr>{aluno_nome}</nobr></td><td>{r['aluno_turma']}</td><td>{mod_str}</td>"
                
                if view_mode == "geral":
                    for b_name in mid_full:
                        b_ac = sum(d_v.get("acertos", 0) for d_k, d_v in det.items() if d_k.strip().lower() != "geral" and (disc_db_map.get(d_k.strip().lower()) == b_name or len(mid_full) == 1))
                        html += f"<td>{b_ac}</td>"
                elif view_mode == "bloco":
                    for b_name in mid_full:
                        b_ac = sum(d_v.get("acertos", 0) for d_k, d_v in det.items() if d_k.strip().lower() != "geral" and (disc_db_map.get(d_k.strip().lower()) == b_name or len(mid_full) == 1))
                        b_tot = sum(d_v.get("total", 0) for d_k, d_v in det.items() if d_k.strip().lower() != "geral" and (disc_db_map.get(d_k.strip().lower()) == b_name or len(mid_full) == 1))
                        b_nota = (b_ac / b_tot * 10.0) if b_tot > 0 else 0.0
                        html += f"<td>{b_nota:.2f}</td>"
                else: # view_mode in ["disciplina", "disciplina_acertos"]
                    for d_name in mid_full:
                        if not is_subject_applicable_to_tipo(d_name, mod_str):
                            html += "<td>-</td>"
                        else:
                            d_info = det.get(d_name)
                            if not d_info:
                                for k, v in det.items():
                                    if k.strip().lower() == d_name.strip().lower():
                                        d_info = v
                                        break
                            if not d_info:
                                d_info = {}
                            tot = d_info.get("total", 0)
                            ac = d_info.get("acertos", 0)
                            if view_mode == "disciplina_acertos":
                                html += f"<td>{ac}</td>"
                            else:
                                if tipo_prova_cat == "Prova Regular":
                                    n_disc = d_info.get("nota", round(ac * 1.0, 1))
                                    html += f"<td>{n_disc:.1f}</td>"
                                else:
                                    n_disc = (ac / tot * 10.0) if tot > 0 else d_info.get("nota", 0.0)
                                    html += f"<td>{n_disc:.2f}</td>"

                if view_mode in ["geral", "disciplina_acertos"]:
                    if view_mode == "geral":
                        html += f"<td>{r['total_acertos']}/{r['total_questoes']}</td>"
                    else:
                        html += f"<td>{r['total_acertos']}</td>"

                if possui_redacao:
                    n_red = r.get("nota_redacao")
                    n_red_str = f"{n_red:.2f}" if n_red is not None else "0.00"
                    html += f"<td>{n_red_str}</td>"

                if (possui_redacao or view_mode not in ["geral", "disciplina", "disciplina_acertos"]):
                    n_red_val = r.get("nota_redacao") or 0.0 if possui_redacao else 0.0
                    if view_mode == "geral":
                        fn_val = float(r.get("total_acertos", 0)) + n_red_val
                    else:
                        fn_val = float(r.get("nota_final", 0.0)) + n_red_val
                    html += f"<td><b>{fn_val:.2f}</b></td>"

                html += "</tr>"

            html += "</table></body></html>"

            doc.setHtml(html)
            doc.print(printer)

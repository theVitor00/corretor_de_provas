import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QGroupBox,
    QMessageBox, QFileDialog, QDialog, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtGui import QTextDocument

from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.exporter import ReportExporter
from ui.tabs.students_tab import StudentDetailDialog

class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.exporter = ReportExporter()
        self.current_results = []
        self.current_exam = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Filters Bar
        gb_filters = QGroupBox("Filtros e Seleção da Prova")
        h_f = QHBoxLayout(gb_filters)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.load_results)

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

        h_f.addWidget(QLabel("Prova:"))
        h_f.addWidget(self.combo_exam, 2)
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

        # Table Area
        self.tbl_results = QTableWidget()
        self.tbl_results.setColumnCount(8)
        self.tbl_results.setHorizontalHeaderLabels([
            "Matrícula", "Nome do Aluno", "Turma", "Tipo", "Acertos", "% Acertos", "Nota Final", "Ação"
        ])
        self.tbl_results.verticalHeader().setDefaultSectionSize(44)
        self.tbl_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_results.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tbl_results.setColumnWidth(7, 160)

        layout.addWidget(self.tbl_results)

        self.load_exams_combo()

    def load_exams_combo(self):
        self.combo_exam.blockSignals(True)
        self.combo_exam.clear()
        self.combo_exam.addItem("Selecione uma prova...", None)

        for e in self.exam_model.list_exams():
            self.combo_exam.addItem(f"{e['nome']} ({e['data']})", e["id"])

        self.combo_exam.blockSignals(False)

        # Turmas
        self.combo_turma.blockSignals(True)
        self.combo_turma.clear()
        self.combo_turma.addItem("Todas as Turmas", "Todas")
        for t in self.student_model.list_turmas():
            self.combo_turma.addItem(t, t)
        self.combo_turma.blockSignals(False)

    def select_exam(self, exam_id: int):
        self.load_exams_combo()
        idx = self.combo_exam.findData(exam_id)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)

    def get_current_turma_subtitle(self) -> str:
        turma_val = self.combo_turma.currentData()
        if not turma_val or turma_val == "Todas":
            return "Geral - Todas as Turmas"
        return str(turma_val)

    def load_results(self):
        exam_id = self.combo_exam.currentData()
        if not exam_id:
            self.current_exam = None
            self.current_results = []
            self.tbl_results.setRowCount(0)
            self.update_cards([])
            return

        self.current_exam = self.exam_model.get_exam_by_id(exam_id)
        turma_val = self.combo_turma.currentData()
        sort_val = self.combo_sort.currentData()
        search_val = self.txt_search.text().strip()

        self.current_results = self.processing_model.list_results_for_exam(
            exam_id, turma_filter=turma_val, sort_by=sort_val, search=search_val
        )

        self.update_cards(self.current_results)

        # Identificar disciplinas dos resultados (Removendo 'Geral')
        disc_set = set()
        for r in self.current_results:
            det = r.get("detalhes_disciplinas", {})
            for d_name in det.keys():
                if d_name.strip().lower() != "geral":
                    disc_set.add(d_name)
        disc_list = sorted(list(disc_set))

        # Reconfigurar cabeçalhos dinamicamente
        headers = ["Matrícula", "Nome do Aluno", "Turma", "Tipo", "Acertos", "% Acertos"]
        for d in disc_list:
            headers.append(d)
        headers.extend(["Nota Final", "Ação"])

        self.tbl_results.setColumnCount(len(headers))
        self.tbl_results.setHorizontalHeaderLabels(headers)

        self.tbl_results.setRowCount(len(self.current_results))
        for row_idx, r in enumerate(self.current_results):
            self.tbl_results.setItem(row_idx, 0, QTableWidgetItem(r["aluno_matricula"]))
            self.tbl_results.setItem(row_idx, 1, QTableWidgetItem(r["aluno_nome"]))
            self.tbl_results.setItem(row_idx, 2, QTableWidgetItem(r["aluno_turma"]))
            self.tbl_results.setItem(row_idx, 3, QTableWidgetItem(r["tipo_prova"]))
            self.tbl_results.setItem(row_idx, 4, QTableWidgetItem(f"{r['total_acertos']}/{r['total_questoes']}"))
            self.tbl_results.setItem(row_idx, 5, QTableWidgetItem(f"{r['percentual_acertos']:.1f}%"))

            col_curr = 6
            det = r.get("detalhes_disciplinas", {})
            for d in disc_list:
                d_info = det.get(d, {})
                tot = d_info.get("total", 0)
                ac = d_info.get("acertos", 0)
                n_disc = (ac / tot * 10.0) if tot > 0 else d_info.get("nota", 0.0)
                self.tbl_results.setItem(row_idx, col_curr, QTableWidgetItem(f"{n_disc:.2f}"))
                col_curr += 1

            nota_item = QTableWidgetItem(f"{r['nota_final']:.2f}")
            self.tbl_results.setItem(row_idx, col_curr, nota_item)
            col_curr += 1

            btn_view = QPushButton("Boletim Individual")
            btn_view.setIcon(qta.icon('fa5s.id-card', color='#242D64'))
            btn_view.setObjectName("btnSecondary")
            btn_view.setMinimumWidth(140)
            btn_view.clicked.connect(lambda _, item_data=r: self.view_individual_report(item_data))
            self.tbl_results.setCellWidget(row_idx, col_curr, btn_view)

    def update_cards(self, results: list):
        turma_sub = self.get_current_turma_subtitle()
        if not results:
            self.lbl_card_avg.setText(f"<b>Turma:</b> {turma_sub}<br><b>Média:</b> -")
            self.lbl_card_max.setText("<b>Maior Nota:</b> -")
            self.lbl_card_min.setText("<b>Menor Nota:</b> -")
            self.lbl_card_count.setText("<b>Total Alunos:</b> 0")
            return

        notas = [r["nota_final"] for r in results]
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

        filename = f"Relatorio_{self.current_exam['nome'].replace(' ', '_')}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", filename, "Arquivos PDF (*.pdf)")
        if filepath:
            try:
                self.exporter.export_exam_pdf(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle()
                )
                QMessageBox.information(self, "Sucesso", f"Relatório PDF exportado com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF:\n{str(e)}")

    def export_excel(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de exportar.")
            return

        filename = f"Resultados_{self.current_exam['nome'].replace(' ', '_')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha Excel", filename, "Arquivos Excel (*.xlsx)")
        if filepath:
            try:
                self.exporter.export_exam_excel(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle()
                )
                QMessageBox.information(self, "Sucesso", f"Planilha Excel exportada com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar Excel:\n{str(e)}")

    def export_word(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de exportar.")
            return

        filename = f"Relatorio_{self.current_exam['nome'].replace(' ', '_')}.docx"
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Documento Word", filename, "Arquivos Word (*.docx)")
        if filepath:
            try:
                self.exporter.export_exam_word(
                    self.current_exam, self.current_results, filepath,
                    turma_subtitle=self.get_current_turma_subtitle()
                )
                QMessageBox.information(self, "Sucesso", f"Documento Word exportado com sucesso!\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar Word:\n{str(e)}")

    def print_report(self):
        if not self.current_exam or not self.current_results:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova com resultados antes de imprimir.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(Qt.Orientation.Landscape)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            doc = QTextDocument()
            turma_sub = self.get_current_turma_subtitle()
            html = f"<h2>Relatório de Prova: {self.current_exam['nome']}</h2>"
            html += f"<h3>Subtítulo: {turma_sub}</h3>"
            html += f"<p><b>Data:</b> {self.current_exam['data']} | <b>Alunos Processados:</b> {len(self.current_results)}</p>"
            html += "<table border='1' cellspacing='0' cellpadding='5' width='100%'>"
            
            disc_set = set()
            for r in self.current_results:
                det = r.get("detalhes_disciplinas", {})
                for d_name in det.keys():
                    if d_name.strip().lower() != "geral":
                        disc_set.add(d_name)
            disc_list = sorted(list(disc_set))

            html += "<tr><th>Matrícula</th><th>Aluno</th><th>Turma</th><th>Tipo</th><th>Acertos</th><th>% Acertos</th>"
            for d in disc_list:
                html += f"<th>{d}</th>"
            html += "<th>Nota Final</th></tr>"
            
            for r in self.current_results:
                det = r.get("detalhes_disciplinas", {})
                html += f"<tr><td>{r['aluno_matricula']}</td><td>{r['aluno_nome']}</td><td>{r['aluno_turma']}</td><td>{r['tipo_prova']}</td><td>{r['total_acertos']}/{r['total_questoes']}</td><td>{r['percentual_acertos']:.1f}%</td>"
                for d in disc_list:
                    d_info = det.get(d, {})
                    tot = d_info.get("total", 0)
                    ac = d_info.get("acertos", 0)
                    n_disc = (ac / tot * 10.0) if tot > 0 else d_info.get("nota", 0.0)
                    html += f"<td>{n_disc:.2f}</td>"
                html += f"<td><b>{r['nota_final']:.2f}</b></td></tr>"
            
            html += "</table>"
            doc.setHtml(html)
            doc.print(printer)

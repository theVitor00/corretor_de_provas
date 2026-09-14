import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFileDialog,
    QDialog, QFormLayout, QMessageBox, QGroupBox, QProgressBar,
    QRadioButton, QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt
from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.dat_parser import DatParser
from services.grading_engine import GradingEngine

class DuplicateStudentDialog(QDialog):
    """
    Diálogo para resolução de duplicatas de matrículas de alunos detectadas no arquivo .DAT
    """
    def __init__(self, matricula: str, duplicate_items: list, parent=None):
        super().__init__(parent)
        self.matricula = matricula
        self.duplicate_items = duplicate_items
        self.selected_item = duplicate_items[0]
        self.setWindowTitle(f"Duplicata Detectada - Matrícula {matricula}")
        self.setWindowIcon(qta.icon('fa5s.copy', color='#EF4444'))
        self.resize(640, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            f"<b>Atenção: Duplicata de Aluno no Arquivo de Respostas!</b><br>"
            f"A matrícula <b>'{self.matricula}'</b> foi encontrada <b>{len(self.duplicate_items)} vezes</b> no arquivo enviado.<br>"
            "Escolha qual ocorrência deseja <b>MANTER</b>. A(s) outra(s) será(ão) descartada(s)."
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Seleção", "Linha #", "Tipo Prova", "Respostas Registradas"])
        table.verticalHeader().setDefaultSectionSize(32)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        table.setRowCount(len(self.duplicate_items))
        self.button_group = QButtonGroup(self)

        for row_idx, item in enumerate(self.duplicate_items):
            rb = QRadioButton(f"Manter Linha {item['line_number']}")
            if row_idx == 0:
                rb.setChecked(True)
            self.button_group.addButton(rb, row_idx)

            table.setCellWidget(row_idx, 0, rb)
            table.setItem(row_idx, 1, QTableWidgetItem(f"Linha {item['line_number']}"))
            table.setItem(row_idx, 2, QTableWidgetItem(f"Tipo {item['tipo']}"))
            table.setItem(row_idx, 3, QTableWidgetItem(item['respostas']))

        layout.addWidget(table)

        btn_box = QHBoxLayout()
        btn_confirm = QPushButton("Confirmar Escolha e Excluir Duplicata")
        btn_confirm.setIcon(qta.icon('fa5s.check', color='white'))
        btn_confirm.setObjectName("btnNavy")
        btn_confirm.clicked.connect(self.accept_choice)

        btn_box.addStretch()
        btn_box.addWidget(btn_confirm)
        layout.addLayout(btn_box)

    def accept_choice(self):
        selected_idx = self.button_group.checkedId()
        if selected_idx >= 0 and selected_idx < len(self.duplicate_items):
            self.selected_item = self.duplicate_items[selected_idx]
        self.accept()


class HeaderFixDialog(QDialog):
    """
    Diálogo para correção manual de dados de cabeçalho
    """
    def __init__(self, raw_item: dict, known_types: list, parent=None):
        super().__init__(parent)
        self.raw_item = raw_item
        self.known_types = known_types
        self.setWindowTitle(f"Revisar Linha {raw_item['line_number']} - Código de Controle Inválido")
        self.setWindowIcon(qta.icon('fa5s.exclamation-triangle', color='#EF4444'))
        self.resize(440, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            f"<b>Aviso de Leitura:</b> O código de controle inicial de 3 dígitos lido foi <b>'{self.raw_item['control']}'</b> (Esperado '000').\n"
            "Ajuste manualmente os dados para validação."
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        form = QFormLayout()
        self.txt_control = QLineEdit(self.raw_item["control"])
        self.txt_matricula = QLineEdit(self.raw_item["matricula"])

        self.combo_tipo = QComboBox()
        for t in self.known_types:
            self.combo_tipo.addItem(f"Tipo {t}", t)
        
        idx = self.combo_tipo.findData(self.raw_item["tipo"])
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        self.lbl_raw = QLabel(f"<b>Linha Original:</b> <code>{self.raw_item['raw_line']}</code>")

        form.addRow("Linha Bruta:", self.lbl_raw)
        form.addRow("Código de Controle (3 dígitos):", self.txt_control)
        form.addRow("Matrícula do Aluno:", self.txt_matricula)
        form.addRow("Tipo de Prova:", self.combo_tipo)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar / Ignorar Linha")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Confirmar Correção")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def validate_and_accept(self):
        if not self.txt_matricula.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe uma matrícula válida para o aluno.")
            return
        self.accept()

    def get_fixed_data(self):
        return {
            "control": self.txt_control.text().strip(),
            "matricula": self.txt_matricula.text().strip(),
            "tipo": self.combo_tipo.currentData()
        }


class ProcessingTab(QWidget):
    def __init__(self, on_view_results_request=None, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.on_view_results_request = on_view_results_request
        self.selected_exam_id = None
        self.dat_file_paths = {} # {parte_num: filepath}
        self.partes_config = [] # list of partes
        self.file_input_widgets = {} # {parte_num: (QLineEdit, QPushButton)}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Envolver todo o conteúdo em QScrollArea para evitar corte de tela em baixas resoluções
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Exam & Multi-File Selection Group
        self.gb_select = QGroupBox("1. Seleção da Prova e Arquivo(s) .DAT de Respostas")
        self.f_select = QFormLayout(self.gb_select)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.on_exam_changed)
        self.f_select.addRow("Selecione a Prova *:", self.combo_exam)

        self.layout_file_inputs = QVBoxLayout()
        self.f_select.addRow(self.layout_file_inputs)

        layout.addWidget(self.gb_select)

        # Processing Actions & Progress
        gb_process = QGroupBox("2. Processamento e Validação do Controle 000")
        l_process = QVBoxLayout(gb_process)

        h_btn_proc = QHBoxLayout()
        self.btn_process = QPushButton("Processar Prova e Calcular Notas")
        self.btn_process.setIcon(qta.icon('fa5s.bolt', color='white'))
        self.btn_process.setObjectName("btnNavy")
        self.btn_process.clicked.connect(self.process_dat_file)
        h_btn_proc.addWidget(self.btn_process)

        self.btn_view_res = QPushButton("Ir Para Conferência / Resultados")
        self.btn_view_res.setIcon(qta.icon('fa5s.chart-pie', color='#242D64'))
        self.btn_view_res.setObjectName("btnSecondary")
        self.btn_view_res.setEnabled(False)
        self.btn_view_res.clicked.connect(self.go_to_results)
        h_btn_proc.addWidget(self.btn_view_res)

        l_process.addLayout(h_btn_proc)

        self.lbl_status = QLabel("Aguardando arquivo(s) para processamento...")
        l_process.addWidget(self.lbl_status)

        layout.addWidget(gb_process)

        # Table of Control Errors / Warnings
        gb_errors = QGroupBox("Revisão de Erros de Cabeçalho (Linhas onde aluno[0..2] != 000)")
        l_errors = QVBoxLayout(gb_errors)

        self.tbl_errors = QTableWidget()
        self.tbl_errors.setColumnCount(6)
        self.tbl_errors.setHorizontalHeaderLabels([
            "Linha", "Linha Bruta", "Controle Lido", "Matrícula", "Tipo", "Ação"
        ])
        self.tbl_errors.verticalHeader().setDefaultSectionSize(32)
        self.tbl_errors.setMaximumHeight(180)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_errors.setColumnWidth(5, 140)

        l_errors.addWidget(self.tbl_errors)
        layout.addWidget(gb_errors)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.load_exams_combo()

    def load_exams_combo(self):
        self.combo_exam.blockSignals(True)
        self.combo_exam.clear()
        self.combo_exam.addItem("Selecione uma prova...", None)

        exams = self.exam_model.list_exams()
        for e in exams:
            self.combo_exam.addItem(f"{e['nome']} ({e['data']})", e["id"])

        self.combo_exam.blockSignals(False)

    def select_exam(self, exam_id: int):
        self.load_exams_combo()
        idx = self.combo_exam.findData(exam_id)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)

    def on_exam_changed(self):
        self.selected_exam_id = self.combo_exam.currentData()
        self.btn_view_res.setEnabled(False)
        self.dat_file_paths.clear()
        self.file_input_widgets.clear()
        self.clear_file_input_layout()

        if not self.selected_exam_id:
            return

        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            return

        partes = exam.get("layout_config", {}).get("partes", [])
        if not partes:
            tot_q = exam.get("num_questoes", 45)
            partes = [{"parte_num": 1, "nome": "Parte Única", "num_questoes": tot_q, "q_start": 1, "q_end": tot_q}]

        self.partes_config = partes

        # Gerar dinamicamente seletores de arquivo por parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            p_nome = p["nome"]
            q_st = p["q_start"]
            q_ed = p["q_end"]

            lbl = QLabel(f"<b>Arquivo .DAT - {p_nome} (Q{q_st} a Q{q_ed}):</b>")
            txt = QLineEdit()
            txt.setReadOnly(True)
            txt.setPlaceholderText(f"Selecione o arquivo .dat para {p_nome}...")

            btn = QPushButton("Buscar Arquivo .DAT...")
            btn.setIcon(qta.icon('fa5s.folder-open', color='white'))
            btn.setObjectName("btnNavy")
            btn.clicked.connect(lambda _, pn=p_num: self.browse_dat_file_for_part(pn))

            h = QHBoxLayout()
            h.addWidget(txt)
            h.addWidget(btn)

            row_w = QWidget()
            vl = QVBoxLayout(row_w)
            vl.setContentsMargins(0, 2, 0, 4)
            vl.addWidget(lbl)
            vl.addLayout(h)

            self.layout_file_inputs.addWidget(row_w)
            self.file_input_widgets[p_num] = (txt, btn)

    def clear_file_input_layout(self):
        while self.layout_file_inputs.count():
            item = self.layout_file_inputs.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def browse_dat_file_for_part(self, parte_num: int):
        filepath, _ = QFileDialog.getOpenFileName(
            self, f"Selecionar Arquivo .DAT para Parte {parte_num}", "", "Arquivos DAT (*.dat);;Todos os Arquivos (*.*)"
        )
        if filepath:
            self.dat_file_paths[parte_num] = filepath
            if parte_num in self.file_input_widgets:
                self.file_input_widgets[parte_num][0].setText(filepath)
            self.lbl_status.setText(f"Arquivo Parte {parte_num} selecionado: {os.path.basename(filepath)}")

    def process_dat_file(self):
        if not self.selected_exam_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova antes de processar.")
            return

        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            QMessageBox.critical(self, "Erro", "Prova selecionada não foi encontrada.")
            return

        tot_q = exam.get("num_questoes", 0)
        known_types = list(exam.get("gabaritos", {}).keys())

        # Verificar se arquivo foi fornecido para cada parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            p_nome = p["nome"]
            if p_num not in self.dat_file_paths or not os.path.exists(self.dat_file_paths[p_num]):
                QMessageBox.warning(
                    self, "Arquivo Faltando",
                    f"Por favor, selecione o arquivo .DAT para a **{p_nome}** (Parte {p_num})."
                )
                return

        parser = DatParser()
        # Dicionário de respostas por matrícula agrupado por parte: {matricula: {"tipo": str, "parts": {p_num: item_dict}}}
        student_records = {}
        all_header_errors = []

        # Parsear cada arquivo .dat por parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            f_path = self.dat_file_paths[p_num]
            try:
                parsed_items = parser.parse_file(f_path)
            except Exception as e:
                QMessageBox.critical(self, "Erro de Leitura", f"Erro ao ler arquivo .dat da Parte {p_num}:\n{str(e)}")
                return

            for item in parsed_items:
                if not item["control_ok"]:
                    all_header_errors.append(item)
                    continue

                mat = item["matricula"]
                if not mat:
                    mat = f"SEM_MAT_{item['line_number']}"

                if mat not in student_records:
                    student_records[mat] = {
                        "matricula": mat,
                        "tipo": item["tipo"] or (known_types[0] if known_types else "1"),
                        "parts": {}
                    }

                student_records[mat]["parts"][p_num] = item

        grading_engine = GradingEngine(exam)
        processed_count = 0

        self.processing_model.clear_exam_processings(self.selected_exam_id)

        # Tratar erros de cabeçalho salvando como HEADER_ERROR
        for err_item in all_header_errors:
            self.processing_model.save_processing(
                prova_id=self.selected_exam_id,
                aluno_matricula=err_item["matricula"] or f"DESCONHECIDO_{err_item['line_number']}",
                tipo_prova=err_item["tipo"] or (known_types[0] if known_types else "1"),
                respostas_aluno=err_item["respostas"],
                status_controle="HEADER_ERROR",
                nota_final=0.0,
                percentual_acertos=0.0,
                total_acertos=0,
                total_questoes=tot_q,
                detalhes_disciplinas={}
            )

        # Unificar e Corrigir os registros válidos dos alunos
        for mat, record in student_records.items():
            tipo_aluno = record["tipo"]
            
            # Montar a string de respostas unificada contínua (Q1..QNn)
            unified_ans = list(" " * tot_q)

            for p in self.partes_config:
                p_num = p["parte_num"]
                q_st = p["q_start"]
                q_ed = p["q_end"]
                p_len = p["num_questoes"]

                if p_num in record["parts"]:
                    raw_part_ans = record["parts"][p_num]["respostas"].upper()[:p_len].ljust(p_len, " ")
                    for idx in range(p_len):
                        pos = q_st - 1 + idx
                        if pos < tot_q:
                            unified_ans[pos] = raw_part_ans[idx]

            full_respostas_str = "".join(unified_ans)

            try:
                res = grading_engine.grade_student(tipo_aluno, full_respostas_str)
                self.processing_model.save_processing(
                    prova_id=self.selected_exam_id,
                    aluno_matricula=mat,
                    tipo_prova=tipo_aluno,
                    respostas_aluno=full_respostas_str,
                    status_controle="OK",
                    nota_final=res["nota_final"],
                    percentual_acertos=res["percentual_acertos"],
                    total_acertos=res["total_acertos"],
                    total_questoes=res["total_questoes"],
                    detalhes_disciplinas=res["detalhes_disciplinas"]
                )
                processed_count += 1
            except Exception as e:
                err_item = {"line_number": 0, "raw_line": f"Matrícula {mat}", "control": "ERR", "matricula": mat, "tipo": tipo_aluno, "error_msg": str(e)}
                all_header_errors.append(err_item)

        self.populate_error_table(all_header_errors, exam, known_types)

        msg = f"Processamento concluído!\n\nAlunos corrigidos com sucesso: {processed_count}\n"
        if all_header_errors:
            msg += f"Aviso: Registros com falha/cabeçalho inválido: {len(all_header_errors)}\nReveja os itens na tabela de revisão abaixo."
        else:
            msg += "Todos os registros foram validados e unificados com sucesso!"

        QMessageBox.information(self, "Resultado do Processamento", msg)
        self.lbl_status.setText(f"Processamento concluído: {processed_count} ok, {len(all_header_errors)} para revisão.")
        self.btn_view_res.setEnabled(True)

    def populate_error_table(self, error_items: list, exam: dict, known_types: list):
        self.tbl_errors.setRowCount(len(error_items))

        for row_idx, item in enumerate(error_items):
            self.tbl_errors.setItem(row_idx, 0, QTableWidgetItem(str(item.get("line_number", "-"))))
            self.tbl_errors.setItem(row_idx, 1, QTableWidgetItem(item.get("raw_line", "")))
            
            c_item = QTableWidgetItem(item.get("control", ""))
            c_item.setForeground(Qt.GlobalColor.red)
            self.tbl_errors.setItem(row_idx, 2, c_item)
            
            self.tbl_errors.setItem(row_idx, 3, QTableWidgetItem(item.get("matricula", "")))
            self.tbl_errors.setItem(row_idx, 4, QTableWidgetItem(item.get("tipo", "")))

            btn_fix = QPushButton("Corrigir Dados")
            btn_fix.setIcon(qta.icon('fa5s.wrench', color='white'))
            btn_fix.setObjectName("btnNavy")
            btn_fix.setMinimumWidth(120)
            btn_fix.clicked.connect(lambda _, it=item: self.fix_header_item(it, exam, known_types))
            self.tbl_errors.setCellWidget(row_idx, 5, btn_fix)

    def fix_header_item(self, item: dict, exam: dict, known_types: list):
        dlg = HeaderFixDialog(item, known_types, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fixed_data = dlg.get_fixed_data()
            grading_engine = GradingEngine(exam)

            try:
                res = grading_engine.grade_student(fixed_data["tipo"], item.get("respostas", ""))
                self.processing_model.save_processing(
                    prova_id=self.selected_exam_id,
                    aluno_matricula=fixed_data["matricula"],
                    tipo_prova=fixed_data["tipo"],
                    respostas_aluno=item.get("respostas", ""),
                    status_controle="OK",
                    nota_final=res["nota_final"],
                    percentual_acertos=res["percentual_acertos"],
                    total_acertos=res["total_acertos"],
                    total_questoes=res["total_questoes"],
                    detalhes_disciplinas=res["detalhes_disciplinas"]
                )
                QMessageBox.information(self, "Sucesso", "Correção aplicada e nota recalculada!")
                self.process_dat_file()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao aplicar correção:\n{str(e)}")

    def go_to_results(self):
        if self.on_view_results_request and self.selected_exam_id:
            self.on_view_results_request(self.selected_exam_id)


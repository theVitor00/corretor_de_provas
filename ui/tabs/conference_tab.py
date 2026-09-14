import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QGroupBox,
    QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.grading_engine import GradingEngine

class ConferenceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.current_exam = None
        self.current_proc_item = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Selection Bar
        gb_select = QGroupBox("Seleção de Prova e Aluno para Conferência de Marcações")
        h_select = QHBoxLayout(gb_select)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.on_exam_changed)

        self.combo_student = QComboBox()
        self.combo_student.currentIndexChanged.connect(self.on_student_changed)

        h_select.addWidget(QLabel("Prova:"))
        h_select.addWidget(self.combo_exam, 2)
        h_select.addWidget(QLabel("Aluno:"))
        h_select.addWidget(self.combo_student, 3)

        layout.addWidget(gb_select)

        # Content Splitter: Summary Card on Left, Question-by-Question Table on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Card: Info and Actions
        panel_left = QGroupBox("Resumo da Correção do Aluno")
        l_left = QVBoxLayout(panel_left)

        self.lbl_student_name = QLabel("<b>Aluno:</b> -")
        self.lbl_student_mat = QLabel("<b>Matrícula:</b> -")
        self.lbl_student_turma = QLabel("<b>Turma:</b> -")
        self.lbl_exam_type = QLabel("<b>Tipo da Prova:</b> -")
        self.lbl_final_grade = QLabel("<b>Nota Final:</b> -")
        self.lbl_hits = QLabel("<b>Total de Acertos:</b> -")

        l_left.addWidget(self.lbl_student_name)
        l_left.addWidget(self.lbl_student_mat)
        l_left.addWidget(self.lbl_student_turma)
        l_left.addWidget(self.lbl_exam_type)
        l_left.addWidget(self.lbl_final_grade)
        l_left.addWidget(self.lbl_hits)
        l_left.addStretch()

        self.btn_save_edits = QPushButton("Recalcular e Salvar Marcações")
        self.btn_save_edits.setIcon(qta.icon('fa5s.save', color='white'))
        self.btn_save_edits.setObjectName("btnNavy")
        self.btn_save_edits.setEnabled(False)
        self.btn_save_edits.clicked.connect(self.save_edited_answers)
        l_left.addWidget(self.btn_save_edits)

        splitter.addWidget(panel_left)

        # Right Card: Detailed Table
        panel_right = QGroupBox("Comparação Detalhada: Resposta do Aluno x Gabarito Oficial")
        l_right = QVBoxLayout(panel_right)

        self.tbl_answers = QTableWidget()
        self.tbl_answers.setColumnCount(6)
        self.tbl_answers.setHorizontalHeaderLabels([
            "Questão #", "Disciplina", "Gabarito Oficial", "Marcação do Aluno (Editável)", "Peso", "Resultado"
        ])
        self.tbl_answers.verticalHeader().setDefaultSectionSize(40)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_answers.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        l_right.addWidget(self.tbl_answers)
        splitter.addWidget(panel_right)

        layout.addWidget(splitter)

        self.load_exams_combo()

    def load_exams_combo(self):
        self.combo_exam.blockSignals(True)
        self.combo_exam.clear()
        self.combo_exam.addItem("Selecione uma prova...", None)

        for e in self.exam_model.list_exams():
            self.combo_exam.addItem(f"{e['nome']} ({e['data']})", e["id"])

        self.combo_exam.blockSignals(False)

    def select_exam_and_student(self, exam_id: int, student_mat: str = None):
        self.load_exams_combo()
        idx = self.combo_exam.findData(exam_id)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)
            if student_mat:
                s_idx = self.combo_student.findData(student_mat)
                if s_idx >= 0:
                    self.combo_student.setCurrentIndex(s_idx)

    def on_exam_changed(self):
        exam_id = self.combo_exam.currentData()
        self.combo_student.blockSignals(True)
        self.combo_student.clear()
        self.combo_student.addItem("Selecione um aluno...", None)

        if exam_id:
            self.current_exam = self.exam_model.get_exam_by_id(exam_id)
            results = self.processing_model.list_results_for_exam(exam_id)
            for r in results:
                self.combo_student.addItem(f"{r['aluno_nome']} ({r['aluno_matricula']})", r["aluno_matricula"])
        else:
            self.current_exam = None

        self.combo_student.blockSignals(False)
        self.clear_details()

    def on_student_changed(self):
        mat = self.combo_student.currentData()
        exam_id = self.combo_exam.currentData()

        if not mat or not exam_id:
            self.clear_details()
            return

        results = self.processing_model.list_results_for_exam(exam_id)
        match = next((r for r in results if r["aluno_matricula"] == mat), None)
        if match:
            self.current_proc_item = self.processing_model.get_by_id(match["id"])
            self.display_conference_data()
        else:
            self.clear_details()

    def clear_details(self):
        self.current_proc_item = None
        self.lbl_student_name.setText("<b>Aluno:</b> -")
        self.lbl_student_mat.setText("<b>Matrícula:</b> -")
        self.lbl_student_turma.setText("<b>Turma:</b> -")
        self.lbl_exam_type.setText("<b>Tipo da Prova:</b> -")
        self.lbl_final_grade.setText("<b>Nota Final:</b> -")
        self.lbl_hits.setText("<b>Total de Acertos:</b> -")
        self.tbl_answers.setRowCount(0)
        self.btn_save_edits.setEnabled(False)

    def display_conference_data(self):
        if not self.current_proc_item or not self.current_exam:
            return

        item = self.current_proc_item
        self.lbl_student_name.setText(f"<b>Aluno:</b> {item.get('aluno_nome', 'N/A')}")
        self.lbl_student_mat.setText(f"<b>Matrícula:</b> {item.get('aluno_matricula', 'N/A')}")
        self.lbl_student_turma.setText(f"<b>Turma:</b> {item.get('aluno_turma', 'N/A')}")
        self.lbl_exam_type.setText(f"<b>Tipo da Prova:</b> {item.get('tipo_prova', 'N/A')}")
        self.lbl_final_grade.setText(f"<b>Nota Final:</b> <font color='#00A9A4'><b>{item.get('nota_final', 0.0):.2f}</b> / {self.current_exam.get('valor_total', 10.0)}</font>")
        self.lbl_hits.setText(f"<b>Total de Acertos:</b> {item.get('total_acertos', 0)} / {item.get('total_questoes', 0)} ({item.get('percentual_acertos', 0.0):.1f}%)")

        grading_engine = GradingEngine(self.current_exam)
        res = grading_engine.grade_student(item["tipo_prova"], item["respostas_aluno"])
        comparativo = res["comparativo_questoes"]

        self.tbl_answers.setRowCount(len(comparativo))

        for row_idx, q in enumerate(comparativo):
            self.tbl_answers.setItem(row_idx, 0, QTableWidgetItem(f"Questão {q['q']}"))
            self.tbl_answers.setItem(row_idx, 1, QTableWidgetItem(q["disciplina"]))
            self.tbl_answers.setItem(row_idx, 2, QTableWidgetItem(q["gabarito"]))

            ans_item = QTableWidgetItem(q["aluno"])
            ans_item.setFlags(ans_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.tbl_answers.setItem(row_idx, 3, ans_item)

            self.tbl_answers.setItem(row_idx, 4, QTableWidgetItem(str(q["peso"])))

            status_item = QTableWidgetItem("CORRETO" if q["correto"] else "INCORRETO")
            if q["correto"]:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.tbl_answers.setItem(row_idx, 5, status_item)

        self.btn_save_edits.setEnabled(True)

    def save_edited_answers(self):
        if not self.current_proc_item or not self.current_exam:
            return

        new_answers_list = []
        for r in range(self.tbl_answers.rowCount()):
            cell = self.tbl_answers.item(r, 3)
            val = cell.text().strip().upper() if cell else ""
            new_answers_list.append(val if val else " ")

        new_answers_str = "".join(new_answers_list)

        grading_engine = GradingEngine(self.current_exam)
        try:
            res = grading_engine.grade_student(self.current_proc_item["tipo_prova"], new_answers_str)
            self.processing_model.update_student_answers(
                proc_id=self.current_proc_item["id"],
                novas_respostas=new_answers_str,
                nova_nota=res["nota_final"],
                novo_percentual=res["percentual_acertos"],
                novos_acertos=res["total_acertos"],
                novos_detalhes=res["detalhes_disciplinas"]
            )
            QMessageBox.information(self, "Sucesso", "Marcações do aluno atualizadas e nota recalculada com sucesso!")
            self.current_proc_item = self.processing_model.get_by_id(self.current_proc_item["id"])
            self.display_conference_data()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao recalcular notas:\n{str(e)}")

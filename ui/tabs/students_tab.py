import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFileDialog,
    QDialog, QFormLayout, QMessageBox, QTabWidget, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from models.student import StudentModel
from services.importer import StudentImporter

# Matplotlib integration
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StudentFormDialog(QDialog):
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.student_data = student_data
        self.setWindowTitle("Editar Aluno" if student_data else "Novo Aluno")
        self.setWindowIcon(qta.icon('fa5s.user-edit' if student_data else 'fa5s.user-plus', color='#242D64'))
        self.resize(380, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_matricula = QLineEdit()
        self.txt_nome = QLineEdit()
        self.txt_turma = QLineEdit()

        if self.student_data:
            self.txt_matricula.setText(str(self.student_data["matricula"]))
            self.txt_nome.setText(self.student_data["nome"])
            self.txt_turma.setText(self.student_data["turma"])

        form.addRow("Matrícula *:", self.txt_matricula)
        form.addRow("Nome Completo *:", self.txt_nome)
        form.addRow("Turma *:", self.txt_turma)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_data(self):
        return {
            "matricula": self.txt_matricula.text().strip(),
            "nome": self.txt_nome.text().strip(),
            "turma": self.txt_turma.text().strip()
        }


class StudentDetailDialog(QDialog):
    def __init__(self, student_id: int, student_model: StudentModel, parent=None):
        super().__init__(parent)
        self.student_id = student_id
        self.student_model = student_model
        self.student = self.student_model.get_by_id(student_id)
        self.stats = self.student_model.get_student_performance_stats(student_id)
        self.setWindowTitle(f"Perfil do Aluno - {self.student.get('nome') if self.student else ''}")
        self.setWindowIcon(qta.icon('fa5s.id-card', color='#242D64'))
        self.resize(920, 620)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Info Card
        header = QGroupBox("Informações do Aluno")
        h_layout = QHBoxLayout(header)
        
        info_str = f"<b>Nome:</b> {self.student.get('nome')} | <b>Matrícula:</b> {self.student.get('matricula')} | <b>Turma:</b> {self.student.get('turma')}"
        stats_str = f"<b>Provas Realizadas:</b> {self.stats['total_provas']} | <b>Média Geral:</b> <font color='#00A9A4'><b>{self.stats['media_geral']:.2f}</b></font> | <b>Melhor Nota:</b> {self.stats['melhor_nota']:.2f}"
        
        v_info = QVBoxLayout()
        v_info.addWidget(QLabel(info_str))
        v_info.addWidget(QLabel(stats_str))
        h_layout.addLayout(v_info)
        layout.addWidget(header)

        # Tabs for Charts and History
        tabs = QTabWidget()

        # Aba 1: Gráfico de Desempenho por Disciplina
        tab_disc = QWidget()
        l_disc = QVBoxLayout(tab_disc)
        fig_disc = Figure(figsize=(6, 3.5), dpi=100)
        canvas_disc = FigureCanvas(fig_disc)
        ax1 = fig_disc.add_subplot(111)

        disc_perf = self.stats.get("disciplinas_desempenho", {})
        if disc_perf:
            names = list(disc_perf.keys())
            values = list(disc_perf.values())
            bars = ax1.bar(names, values, color="#00A9A4")
            ax1.set_ylabel("% Média de Acertos")
            ax1.set_ylim(0, 100)
            ax1.set_title("Desempenho Médio por Disciplina (%)")
            for bar in bars:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8)
        else:
            ax1.text(0.5, 0.5, "Nenhum dado de prova encontrado", ha='center', va='center')

        fig_disc.tight_layout()
        l_disc.addWidget(canvas_disc)
        tabs.addTab(tab_disc, qta.icon('fa5s.chart-bar', color='#242D64'), "Gráfico por Disciplina")

        # Aba 2: Evolução das Notas por Prova
        tab_evo = QWidget()
        l_evo = QVBoxLayout(tab_evo)
        fig_evo = Figure(figsize=(6, 3.5), dpi=100)
        canvas_evo = FigureCanvas(fig_evo)
        ax2 = fig_evo.add_subplot(111)

        history = self.stats.get("historico", [])
        if history:
            history_sorted = sorted(history, key=lambda x: x["prova_data"])
            p_names = [h["prova_nome"] for h in history_sorted]
            p_grades = [h["nota_final"] for h in history_sorted]
            ax2.plot(p_names, p_grades, marker='o', color='#242D64', linewidth=2, markersize=6)
            ax2.set_ylabel("Nota Final")
            ax2.set_title("Evolução das Notas nas Provas")
            ax2.grid(True, linestyle='--', alpha=0.5)
        else:
            ax2.text(0.5, 0.5, "Nenhum dado de prova encontrado", ha='center', va='center')

        fig_evo.tight_layout()
        l_evo.addWidget(canvas_evo)
        tabs.addTab(tab_evo, qta.icon('fa5s.chart-line', color='#242D64'), "Evolução das Notas")

        # Aba 3: Tabela de Histórico
        tab_hist = QWidget()
        l_hist = QVBoxLayout(tab_hist)
        tbl = QTableWidget()
        tbl.setColumnCount(6)
        tbl.setHorizontalHeaderLabels(["Data", "Prova", "Tipo", "Acertos", "% Acertos", "Nota Final"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        tbl.setRowCount(len(history))
        for r, h in enumerate(history):
            tbl.setItem(r, 0, QTableWidgetItem(str(h.get("prova_data"))))
            tbl.setItem(r, 1, QTableWidgetItem(str(h.get("prova_nome"))))
            tbl.setItem(r, 2, QTableWidgetItem(str(h.get("tipo_prova"))))
            tbl.setItem(r, 3, QTableWidgetItem(f"{h.get('total_acertos')}/{h.get('total_questoes')}"))
            tbl.setItem(r, 4, QTableWidgetItem(f"{h.get('percentual_acertos'):.1f}%"))
            tbl.setItem(r, 5, QTableWidgetItem(f"{h.get('nota_final'):.2f}"))

        l_hist.addWidget(tbl)
        tabs.addTab(tab_hist, qta.icon('fa5s.history', color='#242D64'), "Histórico Detalhado")

        layout.addWidget(tabs)

        btn_close = QPushButton("Fechar")
        btn_close.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


class StudentsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.student_model = StudentModel()
        self.importer = StudentImporter(self.student_model)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Actions Bar
        actions_bar = QHBoxLayout()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar por nome ou matrícula...")
        self.txt_search.textChanged.connect(self.load_students)

        self.combo_turma = QComboBox()
        self.combo_turma.currentIndexChanged.connect(self.load_students)

        btn_new = QPushButton("Novo Aluno")
        btn_new.setIcon(qta.icon('fa5s.user-plus', color='white'))
        btn_new.setObjectName("btnNavy")
        btn_new.clicked.connect(self.open_new_student)

        btn_import = QPushButton("Importar (CSV/JSON)")
        btn_import.setIcon(qta.icon('fa5s.file-import', color='#242D64'))
        btn_import.setObjectName("btnSecondary")
        btn_import.clicked.connect(self.import_students_file)

        actions_bar.addWidget(QLabel("Filtrar Turma:"))
        actions_bar.addWidget(self.combo_turma)
        actions_bar.addWidget(self.txt_search, 1)
        actions_bar.addWidget(btn_new)
        actions_bar.addWidget(btn_import)

        main_layout.addLayout(actions_bar)

        # Table area
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Matrícula", "Nome", "Turma", "Ações"])
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 290)

        main_layout.addWidget(self.table)

        self.load_turmas_combo()
        self.load_students()

    def load_turmas_combo(self):
        self.combo_turma.blockSignals(True)
        self.combo_turma.clear()
        self.combo_turma.addItem("Todas as Turmas", "")
        for t in self.student_model.list_turmas():
            self.combo_turma.addItem(t, t)
        self.combo_turma.blockSignals(False)

    def load_students(self):
        turma_val = self.combo_turma.currentData()
        search_val = self.txt_search.text().strip()

        students = self.student_model.list_all(turma_filter=turma_val, search=search_val)
        self.table.setRowCount(len(students))

        for row_idx, s in enumerate(students):
            self.table.setItem(row_idx, 0, QTableWidgetItem(s["matricula"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(s["nome"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(s["turma"]))

            # Action Buttons Panel with fixed non-clipping width and FontAwesome icons
            btn_panel = QWidget()
            btn_layout = QHBoxLayout(btn_panel)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_view = QPushButton("Ver Perfil")
            btn_view.setIcon(qta.icon('fa5s.id-card', color='#242D64'))
            btn_view.setObjectName("btnSecondary")
            btn_view.setMinimumWidth(95)
            btn_view.clicked.connect(lambda _, s_id=s["id"]: self.view_student(s_id))

            btn_edit = QPushButton("Editar")
            btn_edit.setIcon(qta.icon('fa5s.edit', color='white'))
            btn_edit.setObjectName("btnNavy")
            btn_edit.setMinimumWidth(75)
            btn_edit.clicked.connect(lambda _, s_data=s: self.edit_student(s_data))

            btn_del = QPushButton("Excluir")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.setMinimumWidth(75)
            btn_del.clicked.connect(lambda _, s_id=s["id"], s_nome=s["nome"]: self.delete_student(s_id, s_nome))

            btn_layout.addWidget(btn_view)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 3, btn_panel)

    def open_new_student(self):
        dlg = StudentFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.student_model.create(data["matricula"], data["nome"], data["turma"])
                QMessageBox.information(self, "Sucesso", "Aluno cadastrado com sucesso!")
                self.load_turmas_combo()
                self.load_students()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar aluno: {str(e)}")

    def edit_student(self, student_data):
        dlg = StudentFormDialog(self, student_data=student_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.student_model.update(student_data["id"], data["matricula"], data["nome"], data["turma"])
                QMessageBox.information(self, "Sucesso", "Aluno atualizado com sucesso!")
                self.load_turmas_combo()
                self.load_students()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar aluno: {str(e)}")

    def delete_student(self, student_id: int, student_nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o aluno '{student_nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.student_model.delete(student_id)
                self.load_turmas_combo()
                self.load_students()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir aluno: {str(e)}")

    def view_student(self, student_id: int):
        dlg = StudentDetailDialog(student_id, self.student_model, self)
        dlg.exec()

    def import_students_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Alunos", "", "Arquivos Suportados (*.csv *.json);;Arquivos CSV (*.csv);;Arquivos JSON (*.json)"
        )
        if not filepath:
            return

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".csv":
                succ, err_count, errors = self.importer.import_from_csv(filepath)
            elif ext == ".json":
                succ, err_count, errors = self.importer.import_from_json(filepath)
            else:
                QMessageBox.warning(self, "Formato Inválido", "Selecione um arquivo .csv ou .json")
                return

            msg = f"Importação concluída!\n\nAlunos cadastrados/atualizados: {succ}\nErros encontrados: {err_count}"
            if errors:
                msg += "\n\nDetalhes dos erros:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    msg += f"\n... e mais {len(errors) - 5} erro(s)."

            QMessageBox.information(self, "Resultado da Importação", msg)
            self.load_turmas_combo()
            self.load_students()
        except Exception as e:
            QMessageBox.critical(self, "Erro na Importação", f"Ocorreu um erro ao processar o arquivo:\n{str(e)}")

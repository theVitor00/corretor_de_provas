from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.tabs.students_tab import StudentsTab
from ui.tabs.subjects_blocks_tab import SubjectsBlocksTab
from ui.tabs.exams_tab import ExamsTab
from ui.tabs.processing_tab import ProcessingTab
from ui.tabs.conference_tab import ConferenceTab
from ui.tabs.reports_tab import ReportsTab
from ui.tabs.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Corretor de Provas - Sistema de Leitura e Correção Automatizada")
        self.resize(1180, 760)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Branding Bar
        header_bar = QHBoxLayout()
        
        logo_lbl = QLabel("📚 <b>CORRETOR DE PROVAS</b>")
        logo_lbl.setStyleSheet("font-size: 20px; color: #242D64;")

        sub_lbl = QLabel("Sistema de Leitura de Gabaritos, Correção e Emissão de Relatórios")
        sub_lbl.setStyleSheet("font-size: 13px; color: #64748B;")

        v_head = QVBoxLayout()
        v_head.addWidget(logo_lbl)
        v_head.addWidget(sub_lbl)

        header_bar.addLayout(v_head)
        header_bar.addStretch()

        main_layout.addLayout(header_bar)

        # Workflow Tabs Widget
        self.tabs = QTabWidget()
        
        # Instantiate Tabs
        self.tab_students = StudentsTab()
        self.tab_subjects = SubjectsBlocksTab()
        self.tab_exams = ExamsTab(
            on_process_request=self.on_process_exam_request,
            on_view_results_request=self.on_view_results_request
        )
        self.tab_processing = ProcessingTab(
            on_view_results_request=self.on_view_results_request
        )
        self.tab_conference = ConferenceTab()
        self.tab_reports = ReportsTab()
        self.tab_settings = SettingsTab()

        # Add tabs in exact user workflow order
        self.tabs.addTab(self.tab_students, "1. Alunos")
        self.tabs.addTab(self.tab_subjects, "2. Disciplinas e Blocos")
        self.tabs.addTab(self.tab_exams, "3. Provas")
        self.tabs.addTab(self.tab_processing, "4. Processar .DAT")
        self.tabs.addTab(self.tab_conference, "5. Conferência")
        self.tabs.addTab(self.tab_reports, "6. Resultados e Relatórios")
        self.tabs.addTab(self.tab_settings, "7. Configurações")

        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)

    def on_process_exam_request(self, exam_id: int):
        self.tab_processing.select_exam(exam_id)
        self.tabs.setCurrentIndex(3)  # Switch to Processing tab

    def on_view_results_request(self, exam_id: int):
        self.tab_reports.select_exam(exam_id)
        self.tab_reports.load_results()
        self.tab_conference.select_exam_and_student(exam_id)
        self.tabs.setCurrentIndex(5)  # Switch to Reports tab

    def on_tab_changed(self, index: int):
        # Refresh current tab data when navigated to
        if index == 0:
            self.tab_students.load_students()
        elif index == 1:
            self.tab_subjects.load_data()
        elif index == 2:
            self.tab_exams.load_exams()
        elif index == 3:
            self.tab_processing.load_exams_combo()
        elif index == 4:
            self.tab_conference.load_exams_combo()
        elif index == 5:
            self.tab_reports.load_exams_combo()
            self.tab_reports.load_results()
        elif index == 6:
            self.tab_settings.load_settings()

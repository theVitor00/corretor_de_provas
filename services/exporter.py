import os
from typing import List, Dict, Any, Optional, Tuple
from database import Database, db as default_db

# ReportLab imports for PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Excel import
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Word import
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, logo_path: Optional[str] = None, watermark_text: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.logo_path = logo_path
        self.watermark_text = watermark_text

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        
        # Marca d'água em diagonal (se configurada)
        if self.watermark_text:
            self.setFont("Helvetica-Bold", 42)
            self.setFillColor(colors.HexColor("#242D64"))
            self.setFillAlpha(0.08)
            self.translate(A4[0] / 2.0, A4[1] / 2.0)
            self.rotate(45)
            self.drawCentredString(0, 0, self.watermark_text)
            self.restoreState()
            self.saveState()

        # Cabeçalho decorativo
        self.setStrokeColor(colors.HexColor("#00A9A4"))
        self.setLineWidth(1.5)
        self.line(1.5 * cm, A4[1] - 1.5 * cm, A4[0] - 1.5 * cm, A4[1] - 1.5 * cm)

        # Logotipo no cabeçalho se existir
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.drawImage(self.logo_path, A4[0] - 4.5 * cm, A4[1] - 1.4 * cm, width=3 * cm, height=1 * cm, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # Rodapé
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(1.5 * cm, 1.8 * cm, A4[0] - 1.5 * cm, 1.8 * cm)

        self.drawString(1.5 * cm, 1.2 * cm, "Corretor de Provas - Relatório Oficial")
        self.drawRightString(A4[0] - 1.5 * cm, 1.2 * cm, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


class ReportExporter:
    def __init__(self, db: Database = default_db):
        self.db = db

    def _get_branding(self) -> Tuple[Optional[str], Optional[str]]:
        logo_path = self.db.get_config("logo_path")
        watermark = self.db.get_config("watermark_text", "CORRETOR DE PROVAS")
        return logo_path, watermark

    # --- GERAR PDF DA PROVA (GERAL) ---
    def export_exam_pdf(self, exam: Dict[str, Any], results: List[Dict[str, Any]], output_path: str):
        logo_path, watermark = self._get_branding()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=2.0 * cm,
            bottomMargin=2.2 * cm
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#242D64"),
            alignment=0
        )
        
        subtitle_style = ParagraphStyle(
            "CustomSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B")
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=1
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )

        story = []

        # Título
        story.append(Paragraph(f"Relatório de Resultados - {exam.get('nome', 'Prova')}", title_style))
        story.append(Paragraph(f"Data: {exam.get('data', 'N/A')} | Bloco: {exam.get('bloco_nome') or 'Geral'} | Valor Total: {exam.get('valor_total', 10.0)} pts | Total de Alunos: {len(results)}", subtitle_style))
        story.append(Spacer(1, 15))

        # Tabela de Resultados
        headers = ["Matrícula", "Aluno", "Turma", "Tipo", "Acertos", "% Acertos", "Nota Final"]
        table_data = [[Paragraph(h, table_header_style) for h in headers]]

        for r in results:
            row = [
                Paragraph(str(r.get("aluno_matricula", "")), table_cell_style),
                Paragraph(str(r.get("aluno_nome", "Aluno Não Cadastrado")), table_cell_style),
                Paragraph(str(r.get("aluno_turma", "N/A")), table_cell_style),
                Paragraph(str(r.get("tipo_prova", "")), table_cell_style),
                Paragraph(f"{r.get('total_acertos', 0)}/{r.get('total_questoes', 0)}", table_cell_style),
                Paragraph(f"{r.get('percentual_acertos', 0.0):.1f}%", table_cell_style),
                Paragraph(f"<b>{r.get('nota_final', 0.0):.2f}</b>", table_cell_style),
            ]
            table_data.append(row)

        col_widths = [2.5 * cm, 5.5 * cm, 2.2 * cm, 1.5 * cm, 2.0 * cm, 2.2 * cm, 2.1 * cm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#242D64")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))

        story.append(t)

        def make_canvas(*args, **kwargs):
            return NumberedCanvas(*args, logo_path=logo_path, watermark_text=watermark, **kwargs)

        doc.build(story, canvasmaker=make_canvas)

    # --- GERAR PDF INDIVIDUAL DO ALUNO ---
    def export_individual_pdf(self, student_info: Dict[str, Any], exam_info: Dict[str, Any], result: Dict[str, Any], output_path: str):
        logo_path, watermark = self._get_branding()

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=2.0 * cm,
            bottomMargin=2.2 * cm
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            "IndTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#242D64"),
            alignment=0
        )
        
        body_style = ParagraphStyle(
            "IndBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1E293B")
        )

        header_style = ParagraphStyle(
            "IndHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.white,
            alignment=1
        )

        story = []

        # Cabeçalho do Boletim
        story.append(Paragraph(f"Boletim Individual - {exam_info.get('nome', 'Prova')}", title_style))
        story.append(Spacer(1, 10))

        # Card do Aluno
        info_data = [
            [
                Paragraph(f"<b>Aluno:</b> {student_info.get('nome', 'N/A')}", body_style),
                Paragraph(f"<b>Matrícula:</b> {result.get('aluno_matricula', 'N/A')}", body_style)
            ],
            [
                Paragraph(f"<b>Turma:</b> {student_info.get('turma', 'N/A')}", body_style),
                Paragraph(f"<b>Tipo da Prova:</b> {result.get('tipo_prova', 'N/A')}", body_style)
            ],
            [
                Paragraph(f"<b>Nota Final:</b> <font size=12 color='#00A9A4'><b>{result.get('nota_final', 0.0):.2f}</b> / {exam_info.get('valor_total', 10.0)}</font>", body_style),
                Paragraph(f"<b>Aproveitamento:</b> {result.get('percentual_acertos', 0.0):.1f}% ({result.get('total_acertos', 0)}/{result.get('total_questoes', 0)} acertos)", body_style)
            ]
        ]
        info_table = Table(info_data, colWidths=[9 * cm, 9 * cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))

        # Detalhamento por Disciplina
        story.append(Paragraph("<b>Desempenho por Disciplina</b>", title_style))
        story.append(Spacer(1, 6))

        disc_headers = ["Disciplina", "Acertos", "Total Questões", "% Acertos"]
        disc_table_data = [[Paragraph(h, header_style) for h in disc_headers]]

        detalhes = result.get("detalhes_disciplinas", {})
        for disc_name, disc_data in detalhes.items():
            ac = disc_data.get("acertos", 0)
            tot = disc_data.get("total", 0)
            pct = disc_data.get("percentual", 0.0)
            disc_table_data.append([
                Paragraph(disc_name, body_style),
                Paragraph(str(ac), body_style),
                Paragraph(str(tot), body_style),
                Paragraph(f"{pct:.1f}%", body_style)
            ])

        if len(disc_table_data) > 1:
            dt = Table(disc_table_data, colWidths=[7 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
            dt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#242D64")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(dt)

        def make_canvas(*args, **kwargs):
            return NumberedCanvas(*args, logo_path=logo_path, watermark_text=watermark, **kwargs)

        doc.build(story, canvasmaker=make_canvas)

    # --- EXPORTAR PARA EXCEL ---
    def export_exam_excel(self, exam: Dict[str, Any], results: List[Dict[str, Any]], output_path: str):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Resultados"

        # Estilos
        header_fill = PatternFill(start_color="242D64", end_color="242D64", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="242D64")
        subtitle_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # Cabeçalho da Planilha
        ws.append([f"Relatório de Prova: {exam.get('nome', '')}"])
        ws.cell(row=1, column=1).font = title_font
        ws.append([f"Data: {exam.get('data', '')} | Total Alunos: {len(results)} | Valor Total: {exam.get('valor_total', 10.0)}"])
        ws.cell(row=2, column=1).font = subtitle_font
        ws.append([])

        # Obter todas as disciplinas presentes nos resultados
        disciplinas_set = set()
        for r in results:
            det = r.get("detalhes_disciplinas", {})
            for d in det.keys():
                disciplinas_set.add(d)
        disciplinas_list = sorted(list(disciplinas_set))

        # Cabeçalhos da Tabela
        headers = ["Matrícula", "Aluno", "Turma", "Tipo Prova", "Total Acertos", "Total Questões", "% Acertos", "Nota Final"]
        for d in disciplinas_list:
            headers.append(f"Nota {d}")

        ws.append(headers)
        header_row_idx = 4
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=header_row_idx, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align

        # Linhas de Dados
        for r in results:
            det = r.get("detalhes_disciplinas", {})
            row_data = [
                r.get("aluno_matricula", ""),
                r.get("aluno_nome", ""),
                r.get("aluno_turma", ""),
                r.get("tipo_prova", ""),
                r.get("total_acertos", 0),
                r.get("total_questoes", 0),
                r.get("percentual_acertos", 0.0) / 100.0,
                r.get("nota_final", 0.0)
            ]

            for d in disciplinas_list:
                d_info = det.get(d, {})
                row_data.append(d_info.get("acertos", 0))

            ws.append(row_data)
            current_row = ws.max_row
            
            # Formatação das Células
            for col_idx in range(1, len(row_data) + 1):
                c = ws.cell(row=current_row, column=col_idx)
                c.border = thin_border
                if col_idx == 7:  # % Acertos
                    c.number_format = "0.0%"
                    c.alignment = center_align
                elif col_idx == 8:  # Nota Final
                    c.number_format = "0.00"
                    c.alignment = center_align
                elif col_idx in [1, 3, 4, 5, 6]:
                    c.alignment = center_align
                else:
                    c.alignment = left_align

        # Ajuste de largura de colunas
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_path)

    # --- EXPORTAR PARA WORD ---
    def export_exam_word(self, exam: Dict[str, Any], results: List[Dict[str, Any]], output_path: str):
        doc = docx.Document()
        
        # Título
        h1 = doc.add_heading(level=1)
        run = h1.add_run(f"Relatório de Prova: {exam.get('nome', '')}")
        run.font.color.rgb = RGBColor(0x24, 0x2D, 0x64)

        p = doc.add_paragraph()
        p.add_run(f"Data: {exam.get('data', '')} | Bloco: {exam.get('bloco_nome') or 'Geral'} | Valor Total: {exam.get('valor_total', 10.0)} pts\n")
        p.add_run(f"Total de Alunos Processados: {len(results)}")

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Tabela
        table = doc.add_table(rows=1, cols=7)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = 'Table Grid'

        hdr_cells = table.rows[0].cells
        headers = ["Matrícula", "Aluno", "Turma", "Tipo", "Acertos", "% Acertos", "Nota Final"]
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            hdr_cells[i].paragraphs[0].runs[0].font.bold = True
            hdr_cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x24, 0x2D, 0x64)

        for r in results:
            row_cells = table.add_row().cells
            row_cells[0].text = str(r.get("aluno_matricula", ""))
            row_cells[1].text = str(r.get("aluno_nome", ""))
            row_cells[2].text = str(r.get("aluno_turma", ""))
            row_cells[3].text = str(r.get("tipo_prova", ""))
            row_cells[4].text = f"{r.get('total_acertos', 0)}/{r.get('total_questoes', 0)}"
            row_cells[5].text = f"{r.get('percentual_acertos', 0.0):.1f}%"
            row_cells[6].text = f"{r.get('nota_final', 0.0):.2f}"

        doc.save(output_path)

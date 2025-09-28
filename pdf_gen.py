import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

def create_tax_report(data):
    """
    Generates a PDF tax report IN MEMORY and returns the buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('title_style', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=20)
    section_style = ParagraphStyle('section_style', parent=styles['Heading2'], textColor=colors.HexColor("#003366"), fontSize=14, spaceAfter=10)
    
    # --- Title ---
    story.append(Paragraph("Income Tax Summary Report", title_style))
    story.append(Spacer(1, 12))

    # --- ADDED BACK: Section 1: Personal Details ---
    story.append(Paragraph("Personal Details", section_style))
    personal_data = [
        ['Name:', data['personal'].get('name', 'N/A')],
        ['Email:', data['personal'].get('email', 'N/A')],
        ['Mobile Number:', data['personal'].get('mobile_number', 'N/A')]
    ]
    personal_table = Table(personal_data, colWidths=[150, 300])
    personal_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 20))
    # ---------------------------------------------

    # --- Section 2: Income Details ---
    story.append(Paragraph(f"Income Details (FY {data['financial_year']})", section_style))
    income_data = [
        ['Annual Basic Salary', f"₹ {data['income']['basic_salary']:,}"],
        ['HRA Received', f"₹ {data['income']['hra_received']:,}"],
        ['Savings Interest', f"₹ {data['income']['savings_interest']:,}"],
        ['Fixed Deposit Interest', f"₹ {data['income']['fd_interest']:,}"],
        ['Other Income', f"₹ {data['income']['other_income']:,}"]
    ]
    income_table = Table(income_data, colWidths=[250, 200])
    income_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
    ]))
    story.append(income_table)
    story.append(Spacer(1, 20))

    # --- Section 3: Final Summary ---
    story.append(Paragraph("Final Tax Summary", section_style))
    summary_data = [
        ['Gross Income', f"₹ {data['summary']['gross_income']:,}"],
        ['Standard Deduction', f"₹ {data['summary']['standard_deduction']:,}"],
        ['Net Taxable Income', f"₹ {data['summary']['taxable_income']:,}"],
        ['Total Tax Liability (inc. Cess)', f"₹ {data['summary']['total_tax']:,}"],
        ['TDS Already Paid', f"₹ {data['summary']['tds']:,}"],
        ['Final Tax Payable', f"₹ {data['summary']['final_tax_due']:,}"],
    ]
    summary_table = Table(summary_data, colWidths=[250, 200])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(summary_table)

    doc.build(story)
    
    buffer.seek(0)
    return buffer
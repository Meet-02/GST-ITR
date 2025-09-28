import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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

    # --- Custom Styles ---
    title_style = ParagraphStyle('title_style', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=20)
    section_style = ParagraphStyle('section_style', parent=styles['Heading2'], textColor=colors.HexColor("#003366"), fontSize=14, spaceAfter=10)
    # Corrected style to be used in the final summary for bold, red text
    bold_value_style = ParagraphStyle('bold_value_style', parent=styles['Normal'], fontSize=12, textColor=colors.red, leading=16, fontName='Helvetica-Bold')
    normal_style = styles['Normal']

    # --- Title ---
    story.append(Paragraph("GST & Tax Liability Report", title_style))
    story.append(Spacer(1, 12))

    # --- Section 1: Personal Details ---
    story.append(Paragraph("Personal Details", section_style))
    personal_data = [
        ['Name:', data['personal'].get('name', 'N/A')],
        ['Age:', str(data['personal'].get('age', 'N/A'))],
        ['Email:', data['personal'].get('email', 'N/A')],
        ['Phone:', data['personal'].get('phone', 'N/A')]
    ]
    personal_table = Table(personal_data, colWidths=[150, 300])
    personal_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 20))

    # --- Section 2: Income & Business Details ---
    story.append(Paragraph("Page 1 – Income & Business Details", section_style))
    income_data = [
        ['Gross Income (Total Revenue)', f"₹ {data['income']['gross_income']:,}"],
        ['Other Income Source', f"₹ {data['income']['other_income']:,}"],
        ['Total Revenue', f"₹ {data['income']['total_revenue']:,}"],
        ['Business Name', data['income']['business_name']],
        ['Product Name', data['income']['product_name']],
        ['Purchase Value (Excl. GST)', f"₹ {data['gst']['purchase_value']:,}"],
        ['GST Rate (Purchase)', f"{data['gst']['purchase_rate']} %"],
        ['Type of Supply (Purchase)', data['gst']['purchase_supply_type']],
        ['Sell Value (Excl. GST)', f"₹ {data['gst']['sell_value']:,}"],
        ['GST Rate (Sale)', f"{data['gst']['sell_rate']} %"],
        ['Type of Supply (Sale)', data['gst']['sell_supply_type']]
    ]
    income_table = Table(income_data, colWidths=[250, 200])
    income_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(income_table)
    story.append(Spacer(1, 20))

    # --- Section 3: Expenses & Deductions ---
    story.append(Paragraph("Page 2 – Expenses & Deductions", section_style))
    expense_data = [
        ['Rent', f"₹ {data['expenses']['rent']:,}"],
        ['Employee Wages', f"₹ {data['expenses']['wages']:,}"],
        ['Business Operating Expenses', f"₹ {data['expenses']['operating_expenses']:,}"],
        ['Subscriptions', f"₹ {data['expenses']['subscription']:,}"],
        ['Other Expenses', f"₹ {data['expenses']['other']:,}"],
        ['Section 80C', f"₹ {data['expenses']['80c']:,}"],
        ['Section 80D', f"₹ {data['expenses']['80d']:,}"],
        ['Other Deductions', f"₹ {data['expenses']['other_deductions']:,}"]
    ]
    expense_table = Table(expense_data, colWidths=[300, 150])
    expense_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(expense_table)

    # --- Page Break for Final Summary ---
    story.append(PageBreak())

    # --- Section 4: Final GST & Tax Summary ---
    story.append(Paragraph("Final GST & Tax Summary", section_style))
    gst_paid = data['gst']['purchase_value'] * data['gst']['purchase_rate'] / 100
    gst_collected = data['gst']['sell_value'] * data['gst']['sell_rate'] / 100
    net_gst_liability = gst_collected - gst_paid
    total_revenue = data['income']['total_revenue']
    taxable_income = data['summary']['taxable_income']

    final_summary_data = [
        ['Net GST Liability', Paragraph(f"₹ {net_gst_liability:,.2f}", bold_value_style)],
        ['Total Revenue Generated', Paragraph(f"₹ {total_revenue:,.2f}", bold_value_style)],
        ['Net Taxable Income', Paragraph(f"₹ {taxable_income:,.2f}", bold_value_style)]
    ]
    final_summary_table = Table(final_summary_data, colWidths=[250, 200])
    final_summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(final_summary_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
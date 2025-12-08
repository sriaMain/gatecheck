import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
 
# def export_to_excel(data, filename="report.xlsx", sheet_name="Sheet1"):
#     df = pd.DataFrame(data)
#     output = BytesIO()
 
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name=sheet_name)
 
#     output.seek(0)
#     response = HttpResponse(
#         output.read(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = f'attachment; filename={filename}'
#     return response
 
def export_to_excel(data, filename="report.xlsx", sheet_name="Sheet1"):
    # Convert all values to Excel-safe types
    safe_data = []
    for row in data:
        safe_row = {key: safe_excel_value(value) for key, value in row.items()}
        safe_data.append(safe_row)

    # Convert to DataFrame
    df = pd.DataFrame(safe_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from io import BytesIO
from django.http import HttpResponse

def generate_pdf_report(data, filename):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    no_wrap_style = ParagraphStyle(
        'NoWrap',
        parent=styles['Normal'],
        wordWrap=None,
        fontSize=9
    )

    elements = []

    if data:
        headers = list(data[0].keys())

        table_data = [
            [Paragraph(str(cell), no_wrap_style) for cell in headers]
        ] + [
            [Paragraph(str(cell), no_wrap_style) for cell in row.values()]
            for row in data
        ]

        col_widths = [
            110,  # Name
            90,  # Email
            65,   # Mobile
            120,  # Whom to Meet
            70,   # Visit Date
            70,   # Time In
            70,   # Time Out
            # 70,   # Duration
            85,  # Access Card
            90    # Category
        ]

        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1.2, colors.black),  # thicker grid
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



def safe_excel_value(value):
    import datetime

    if value is None:
        return ""

    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, datetime.time):
        return value.strftime("%H:%M:%S")

    return str(value)




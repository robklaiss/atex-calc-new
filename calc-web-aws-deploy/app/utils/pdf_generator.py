from reportlab.platypus import (
    BaseDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    Frame,
    PageTemplate,
    PageBreak,
    NextPageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black, grey
from datetime import datetime
import os
import tempfile

def generate_pdf_report(results, project_data, output_dir):
    """Generate PDF report for ATex calculation"""
    
    # Create temporary file
    fd, filepath = tempfile.mkstemp(suffix='.pdf', dir=output_dir)
    os.close(fd)
    
    # Create PDF document
    page_width, page_height = A4

    def _asset_path(filename):
        web_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        repo_root = os.path.abspath(os.path.join(web_root, '..'))
        candidates = [
            os.path.join(repo_root, 'temp', filename),
            os.path.join(web_root, 'temp', filename),
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    cover_image_path = _asset_path('atex-informe-tapa.png')
    internal_background_path = _asset_path('atex-informe-fondo-hojas.png')
    closing_image_path = _asset_path('atex-informe-cierre.png')

    doc = BaseDocTemplate(filepath, pagesize=A4)

    reserved_top = 120
    left_margin = 72
    right_margin = 72
    bottom_margin = 72

    cover_frame = Frame(0, 0, page_width, page_height, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    internal_frame = Frame(
        left_margin,
        bottom_margin,
        page_width - left_margin - right_margin,
        page_height - reserved_top - bottom_margin,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    closing_frame = Frame(0, 0, page_width, page_height, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def _draw_full_page_image(canvas, image_path):
        if not image_path or not os.path.exists(image_path):
            return
        canvas.saveState()
        canvas.drawImage(image_path, 0, 0, width=page_width, height=page_height, mask='auto')
        canvas.restoreState()

    def _cover_on_page(canvas, _doc):
        _draw_full_page_image(canvas, cover_image_path)

    def _internal_on_page(canvas, _doc):
        _draw_full_page_image(canvas, internal_background_path)

    def _closing_on_page(canvas, _doc):
        _draw_full_page_image(canvas, closing_image_path)

    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[cover_frame], onPage=_cover_on_page, autoNextPageTemplate='internal'),
        PageTemplate(id='internal', frames=[internal_frame], onPage=_internal_on_page),
        PageTemplate(id='closing', frames=[closing_frame], onPage=_closing_on_page),
    ])
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    section_title_style = ParagraphStyle(
        'CustomHeading2Centered',
        parent=styles['Heading2'],
        alignment=TA_CENTER
    )
    
    # Build story
    story = []

    story.append(Spacer(1, 1))
    story.append(PageBreak())
    
    # Add title
    story.append(Paragraph("ANÁLISIS DE PRECIOS UNITARIOS - SISTEMA ATEX", title_style))
    story.append(Spacer(1, 20))
    
    # Add project information
    texto = results.get('texto', {})
    project_info = [
        ['Proyecto:', project_data.get('nombre', texto.get('Obra', ''))],
        ['Cliente:', project_data.get('cliente', texto.get('Cliente', ''))],
        ['Ciudad:', project_data.get('ciudad', texto.get('Ciudad', ''))],
        ['País:', texto.get('Pais', '')],
        ['Fecha:', texto.get('Fecha', datetime.now().strftime('%d/%m/%Y'))],
        ['Tipo de Obra:', texto.get('Tipo de Obra', '')],
        ['Moneda:', texto.get('Moneda', '')],
        ['Tasa de Cambio:', f"${texto.get('Cambio', '0')}"]
    ]
    
    project_table = Table(project_info, colWidths=[5*cm, 10*cm])
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), '#F48120'),
        ('TEXTCOLOR', (0, 0), (0, -1), 'white'),
        ('TEXTCOLOR', (1, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(project_table)
    story.append(Spacer(1, 20))
    
    # Add ATex APU table
    story.append(Paragraph("ANÁLISIS DE PRECIOS UNITARIOS - SISTEMA ATEX", section_title_style))
    story.append(Spacer(1, 12))
    
    apu_atex = results.get('tablas', {}).get('APUtecnologiaAtex', [])
    if apu_atex:
        # Prepare table data
        headers = ['Item', 'Descripción', 'Unidad', 'Cantidad', 'Subtotal']
        table_data = [headers]
        
        for item in apu_atex:
            table_data.append([
                item['consecutivo'],
                item['descripcion'],
                item['unidad'],
                item['cantidad'],
                item['subTotal']
            ])
        
        # Create table
        apu_table = Table(table_data, colWidths=[1*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        apu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#F48120'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), 'white'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('ALIGN', (3, 1), (4, -1), 'RIGHT')
        ]))
        
        story.append(apu_table)
        story.append(Spacer(1, 20))
    
    # Add Traditional slab APU table
    story.append(Paragraph("ANÁLISIS DE PRECIOS UNITARIOS - LOSA TRADICIONAL", section_title_style))
    story.append(Spacer(1, 12))
    
    apu_maciza = results.get('tablas', {}).get('APUtecnologiaMaciza', [])
    if apu_maciza:
        # Prepare table data
        headers = ['Item', 'Descripción', 'Unidad', 'Cantidad', 'Subtotal']
        table_data = [headers]
        
        for item in apu_maciza:
            table_data.append([
                item['consecutivo'],
                item['descripcion'],
                item['unidad'],
                item['cantidad'],
                item['subTotal']
            ])
        
        # Create table
        apu_table = Table(table_data, colWidths=[1*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        apu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#F48120'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), 'white'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('ALIGN', (3, 1), (4, -1), 'RIGHT')
        ]))
        
        story.append(apu_table)
        story.append(Spacer(1, 20))
    
    # Add comparison summary
    story.append(Paragraph("RESUMEN COMPARATIVO", section_title_style))
    story.append(Spacer(1, 12))
    
    resumen = results.get('resumen', {})
    comparison_data = [
        ['Área Total Losa:', f"{resumen.get('areaTotal', 0):.2f} m²"],
        ['Volumen Hormigón ATex:', f"{resumen.get('volumenHormigonAtex', 0):.2f} m³"],
        ['Volumen Hormigón Losa Maciza:', f"{resumen.get('volumenHormigonMaciza', 0):.2f} m³"],
        ['Acero ATex:', f"{resumen.get('aceroAtex', 0):.2f} kg"],
        ['Acero Losa Maciza:', f"{resumen.get('aceroMacizo', 0):.2f} kg"],
        ['', ''],
        ['Costo Total ATex:', f"${resumen.get('costoTotalAtex', 0):.2f}"],
        ['Costo Total Losa Maciza:', f"${resumen.get('costoTotalMacizo', 0):.2f}"],
        ['Ahorro Total:', f"${resumen.get('ahorroTotal', 0):.2f}"],
        ['Porcentaje de Ahorro:', f"{resumen.get('porcentajeAhorro', 0):.1f}%"]
    ]
    
    comparison_table = Table(comparison_data, colWidths=[7*cm, 5*cm])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 6), (0, 9), '#F48120'),
        ('BACKGROUND', (1, 6), (1, 9), '#F48120'),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('TEXTCOLOR', (0, 6), (-1, 9), 'white'),
        ('ALIGN', (0, 0), (0, 5), 'LEFT'),
        ('ALIGN', (1, 0), (1, 5), 'RIGHT'),
        ('ALIGN', (0, 6), (-1, 9), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 5), 10),
        ('FONTNAME', (0, 6), (-1, 9), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 6), (-1, 9), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(comparison_table)

    story.append(NextPageTemplate('closing'))
    story.append(PageBreak())
    story.append(Spacer(1, 1))
    
    # Build PDF
    doc.build(story)
    
    return filepath

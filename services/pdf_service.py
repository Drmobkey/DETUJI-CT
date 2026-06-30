# services/pdf_service.py
import os
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def draw_page_decorations(canvas, doc):
    """
    Menggambar elemen estetika latar belakang (header band dan footer halaman).
    """
    canvas.saveState()
    
    # 1. Band warna aksen atas (Medical Teal-Blue)
    canvas.setFillColor(colors.HexColor('#0F766E'))  # Teal aksen
    canvas.rect(0, 782, 612, 10, fill=True, stroke=False)
    
    # 2. Garis pembatas footer halus
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(1)
    canvas.line(40, 55, 572, 55)
    
    # 3. Keterangan teks footer dengan nomor halaman dinamis
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.HexColor('#1E293B')) # Slate 800
    canvas.drawString(40, 38, "DETUJI-CT")
    
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#64748B')) # Slate 500
    canvas.drawString(95, 38, "|   Sistem Analisis Citra Medis Ginjal berbasis Kecerdasan Buatan")
    canvas.drawRightString(572, 38, f"Halaman {doc.page}")
    
    canvas.restoreState()

def generate_diagnosis_pdf(report_data, output_pdf_path):
    """
    Fungsi untuk merakit lembar hasil radiologi resmi ke dalam format PDF menggunakan ReportLab.
    Halaman 1: Kop surat, identitas pasien, ringkasan mayoritas, disclaimer & tanda tangan.
    Halaman 2+: Lampiran citra CT Scan dalam grid 2 kolom.
    """
    from config import Config
    
    # Proteksi karakter spesial XML agar tidak merusak parser Paragraph ReportLab
    nama_pasien = html.escape(str(report_data.get('nama_pasien', 'Anonim')))
    no_rm = html.escape(str(report_data.get('no_rm', '-')))
    timestamp = html.escape(str(report_data.get('timestamp', '-')))
    analysis_id = html.escape(str(report_data.get('analysis_id', '-')))
    prediction = html.escape(str(report_data.get('prediction', '-')))
    confidence = html.escape(str(report_data.get('confidence', '-'))).replace('.', ',')
    details = report_data.get('details', [])

    # 1. Inisialisasi dokumen berukuran kertas Letter dengan margin proporsional
    doc = SimpleDocTemplate(
        output_pdf_path, 
        pagesize=letter,
        rightMargin=40, 
        leftMargin=40, 
        topMargin=45, 
        bottomMargin=70
    )
    story = []
    
    # 2. Pengaturan Gaya Tulisan (Styles)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0F766E'),
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#0D9488'),
        spaceAfter=8
    )

    institution_style = ParagraphStyle(
        'InstInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#64748B'),
        leading=11
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155'),
        leading=13
    )

    body_bold_style = ParagraphStyle(
        'BodyTextBoldCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    # ==================== KOP SURAT MODERN ====================
    header_left = [
        Paragraph("DETUJI-CT", title_style),
        Paragraph("INTELLIGENT MEDICAL IMAGING REPORT", subtitle_style)
    ]
    
    header_right = [
        Paragraph("<b>LABORATORIUM RADIOLOGI DIGITAL</b>", ParagraphStyle('InstBold', parent=institution_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E293B'))),
        Paragraph("Poltekkes Kemenkes Semarang", institution_style),
        Paragraph("Email: detuji.support@poltekkes-smg.ac.id", institution_style)
    ]
    
    header_table = Table([[header_left, header_right]], colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # ==================== TABEL IDENTITAS PASIEN ====================
    patient_info_data = [
        [Paragraph("<b>NAMA PASIEN</b>", body_bold_style), Paragraph(f": &nbsp; {nama_pasien}", body_style),
         Paragraph("<b>NO. REKAM MEDIS</b>", body_bold_style), Paragraph(f": &nbsp; {no_rm}", body_style)],
        [Paragraph("<b>TANGGAL ANALISIS</b>", body_bold_style), Paragraph(f": &nbsp; {timestamp}", body_style),
         Paragraph("<b>ID TRANSAKSI</b>", body_bold_style), Paragraph(f": &nbsp; {analysis_id}", body_style)]
    ]
    
    info_table = Table(patient_info_data, colWidths=[120, 145, 120, 145])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDFA')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor('#0F766E')),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#CCFBF1')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ==================== RINGKASAN HASIL ANALISIS (MAYORITAS) ====================
    story.append(Paragraph("RINGKASAN HASIL ANALISIS (MAYORITAS)", section_heading))
    
    is_tumor = "tumor" in prediction.lower()
    bg_color = colors.HexColor('#FFF1F2') if is_tumor else colors.HexColor('#ECFDF5')
    text_color = colors.HexColor('#BE123C') if is_tumor else colors.HexColor('#047857')
    border_color = colors.HexColor('#F43F5E') if is_tumor else colors.HexColor('#10B981')
    
    status_label = "TERDETEKSI ADANYA MASSA (TUMOR GINJAL)" if is_tumor else "NORMAL (TIDAK TERDETEKSI TUMOR)"
    
    result_title_style = ParagraphStyle(
        'ResultTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=text_color,
        spaceAfter=4
    )
    
    result_detail_style = ParagraphStyle(
        'ResultDetail',
        parent=body_style,
        fontSize=8.5,
        textColor=colors.HexColor('#475569')
    )
    
    summary_text = html.escape(str(report_data.get('summary_text', f"Berdasarkan analisis {len(details)} gambar.")))
    
    result_box_data = [
        [Paragraph(f"<b>STATUS KESELURUHAN: &nbsp;{status_label}</b>", result_title_style)],
        [Paragraph(f"Rata-rata Tingkat Kepercayaan: &nbsp;<b>{confidence}%</b>", result_detail_style)],
        [Paragraph(f"{summary_text}", ParagraphStyle('ResultDesc', parent=result_detail_style, fontSize=9, spaceBefore=4))],
        [Paragraph("<i>Klasifikasi dilakukan menggunakan arsitektur deep learning MobileNet v2 yang telah dioptimalkan untuk citra CT Scan Ginjal.</i>", ParagraphStyle('ResultInfo', parent=result_detail_style, fontSize=7.5, spaceBefore=6))]
    ]
    
    result_table = Table(result_box_data, colWidths=[530])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('PADDING', (0,0), (-1,-1), 10),
        ('LINEBEFORE', (0,0), (0,-1), 4, border_color),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 15))

    # ==================== DISCLAIMER & TANDA TANGAN (HALAMAN 1) ====================
    disclaimer_text = (
        "<font size=7 color='#64748B'><b>DISCLAIMER MEDIS:</b><br/>"
        "Laporan analisis ini dihasilkan secara otomatis oleh sistem kecerdasan buatan komputer (Detuji-CT). "
        "Hasil ini bersifat sebagai diagnosis sementara untuk membantu skrining awal. Laporan ini <b>wajib</b> "
        "ditinjau, dikonfirmasi, dan ditandatangani oleh Dokter Spesialis Radiologi sebelum digunakan sebagai "
        "dasar keputusan klinis atau tindakan medis.</font>"
    )
    
    footer_data = [
        [Paragraph(disclaimer_text, body_style),
         Paragraph("<b>Dokter Spesialis Radiologi,</b><br/><br/><br/><br/>______________________<br/>NIP/SIP. ", ParagraphStyle('DocSign', parent=body_style, alignment=1))]
    ]
    
    footer_table = Table(footer_data, colWidths=[350, 180])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LINEBEFORE', (1,0), (1,0), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(footer_table)

    # ==================== HALAMAN 2+: LAMPIRAN CITRA CT SCAN (GRID 2 KOLOM) ====================
    temp_files = []
    
    if len(details) > 0:
        story.append(PageBreak())
        story.append(Paragraph("LAMPIRAN CITRA MEDIS YANG DIANALISIS", section_heading))
        story.append(Spacer(1, 6))
    
    # Siapkan semua cell gambar terlebih dahulu
    image_cells = []
    
    for idx, detail in enumerate(details):
        img_filename = detail.get('saved_filename', '')
        img_prediction = detail.get('prediction', 'Unknown')
        img_confidence = detail.get('confidence', 0)
        
        image_path = os.path.join(Config.UPLOAD_FOLDER, img_filename)
        
        try:
            image_path_to_use = image_path
            if image_path.lower().endswith('.dcm'):
                try:
                    import pydicom
                    import numpy as np
                    import cv2
                    
                    ds = pydicom.dcmread(image_path)
                    img_array = ds.pixel_array
                    
                    img_min = np.min(img_array)
                    img_max = np.max(img_array)
                    if img_max > img_min:
                        img_array = ((img_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                    else:
                        img_array = np.zeros_like(img_array, dtype=np.uint8)
                        
                    if len(img_array.shape) == 2:
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                    elif len(img_array.shape) == 3:
                        if img_array.shape[2] == 1:
                            img_bgr = cv2.cvtColor(img_array[:, :, 0], cv2.COLOR_GRAY2BGR)
                        elif img_array.shape[2] == 3:
                            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        elif img_array.shape[2] == 4:
                            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                        else:
                            img_bgr = img_array
                    else:
                        img_bgr = img_array
                        
                    temp_image_path = image_path + f".temp_{idx}.png"
                    cv2.imwrite(temp_image_path, img_bgr)
                    image_path_to_use = temp_image_path
                    temp_files.append(temp_image_path)
                except Exception as dcm_err:
                    print(f"Error converting DICOM to PNG for PDF: {dcm_err}")
                    
            # Gambar
            scan_img = Image(image_path_to_use, width=200, height=200)
            scan_img.hAlign = 'CENTER'
            
            # Label warna
            img_is_tumor = "tumor" in img_prediction.lower()
            lbl_color = colors.HexColor('#BE123C') if img_is_tumor else colors.HexColor('#047857')
            
            lbl_style = ParagraphStyle(
                f'ImgLbl_{idx}',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=9,
                textColor=lbl_color,
                alignment=1
            )
            
            desc_style = ParagraphStyle(
                f'ImgDesc_{idx}',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=8,
                textColor=colors.HexColor('#64748B'),
                alignment=1
            )
            
            img_label = Paragraph(f"{img_prediction.upper()} ({str(img_confidence).replace('.', ',')}%)", lbl_style)
            img_desc = Paragraph(f"File: {detail.get('original_filename', img_filename)}", desc_style)
            
            # Sub-tabel untuk 1 gambar (gambar + label + deskripsi)
            cell_table = Table([[scan_img], [img_label], [img_desc]], colWidths=[220])
            cell_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,1), (0,1), 6),
                ('BOTTOMPADDING', (0,2), (0,2), 6),
            ]))
            
            image_cells.append(cell_table)
        except Exception as e:
            error_para = Paragraph(f"<i>[Gagal memuat citra {img_filename}: {html.escape(str(e))}]</i>", body_style)
            image_cells.append(error_para)
    
    # Susun image_cells ke dalam grid 2 kolom
    for i in range(0, len(image_cells), 2):
        if i + 1 < len(image_cells):
            row = [[image_cells[i], image_cells[i+1]]]
        else:
            row = [[image_cells[i], ""]]
        
        grid_table = Table(row, colWidths=[265, 265])
        grid_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(grid_table)
        story.append(Spacer(1, 8))

    try:
        # 3. Cetak dokumen menjadi file PDF fisik dengan dekorasi halaman
        doc.build(story, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
    finally:
        # Hapus berkas temporary png jika ada
        for tmp in temp_files:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception as clean_err:
                    print(f"Error cleaning up temporary PNG {tmp}: {clean_err}")
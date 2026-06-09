# services/pdf_service.py
import os
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_diagnosis_pdf(report_data, image_path, output_pdf_path):
    """
    Fungsi untuk merakit lembar hasil radiologi resmi ke dalam format PDF menggunakan ReportLab.
    """
    # Proteksi karakter spesial XML agar tidak merusak parser Paragraph ReportLab
    nama_pasien = html.escape(str(report_data.get('nama_pasien', 'Anonim')))
    no_rm = html.escape(str(report_data.get('no_rm', '-')))
    timestamp = html.escape(str(report_data.get('timestamp', '-')))
    analysis_id = html.escape(str(report_data.get('analysis_id', '-')))
    prediction = html.escape(str(report_data.get('prediction', '-')))
    confidence = html.escape(str(report_data.get('confidence', '-')))

    # 1. Inisialisasi dokumen berukuran kertas Letter
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # 2. Pengaturan Gaya Tulisan (Styles)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1A365D'), # Biru Gelap Medis
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#4A5568'),
        alignment=1,
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = styles['Normal']

    # ==================== KOP SURAT LABORATORIUM ====================
    story.append(Paragraph("LABORATORIUM RADIOLOGI DIGITAL DETUJI-CT", title_style))
    story.append(Paragraph("Poltekkes Kemenkes Semarang | Hubungi: detuji.support@poltekkes-smg.ac.id", subtitle_style))
    
    # Garis pembatas kop surat
    divider = Table([['']], colWidths=[530], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A365D')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))

    # ==================== TABEL IDENTITAS PASIEN ====================
    patient_info_data = [
        [Paragraph(f"<b>Nama Pasien:</b> {nama_pasien}", body_style), 
         Paragraph(f"<b>No. Rekam Medis:</b> {no_rm}", body_style)],
        [Paragraph(f"<b>Waktu Analisis:</b> {timestamp}", body_style), 
         Paragraph(f"<b>ID Transaksi:</b> {analysis_id}", body_style)]
    ]
    
    info_table = Table(patient_info_data, colWidths=[265, 265])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # ==================== LAMPIRAN CITRA CT SCAN ====================
    story.append(Paragraph("CITRA MEDIS YANG DIANALISIS", section_heading))
    try:
        # Memasang gambar CT Scan pasien ke dalam PDF dengan ukuran proposional
        scan_img = Image(image_path, width=200, height=200)
        scan_img.hAlign = 'CENTER'
        story.append(scan_img)
    except Exception as e:
        story.append(Paragraph(f"<i>[Gagal memuat lampiran gambar: {str(e)}]</i>", body_style))
    story.append(Spacer(1, 15))

    # ==================== KESIMPULAN / HASIL DIAGNOSIS AI ====================
    story.append(Paragraph("INTERPRETASI & KESIMPULAN OTOMATIS (AI)", section_heading))
    
    # Tentukan warna tema berdasarkan hasil diagnosis (Merah jika tumor, Hijau jika normal)
    is_tumor = "tumor" in report_data['prediction'].lower()
    bg_color = colors.HexColor('#FED7D7') if is_tumor else colors.HexColor('#C6F6D5')
    text_color = colors.HexColor('#9B2C2C') if is_tumor else colors.HexColor('#22543D')
    
    result_style = ParagraphStyle(
        'ResultText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=text_color,
        alignment=1
    )
    
    result_box_data = [
        [Paragraph(f"DIAGNOSIS SEMENTARA: {prediction.upper()}", result_style)],
        [Paragraph(f"Tingkat Kepercayaan Sistem (Confidence Score): {confidence}%", body_style)]
    ]
    
    result_table = Table(result_box_data, colWidths=[530])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, text_color),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 30))

    # ==================== TANDA TANGAN / DISCLAIMER ====================
    footer_data = [
        [Paragraph("<font size=7 textColor='#718096'>* CATATAN: Laporan ini diterbitkan secara otomatis oleh sistem kecerdasan buatan komputer (Detuji-CT). Hasil ini wajib ditinjau kembali dan dikonfirmasi ulang oleh Dokter Spesialis Radiologi asli sebelum tindakan medis diambil.</font>", body_style),
         Paragraph("<b>Dokter Pemeriksa,</b><br/><br/><br/><br/>______________________<br/>Sistem Detuji-CT App", body_style)]
    ]
    
    footer_table = Table(footer_data, colWidths=[350, 180])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
    ]))
    story.append(footer_table)

    # 3. Cetak dokumen menjadi file PDF fisik
    doc.build(story)
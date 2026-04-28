import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

desktop_path = r"c:\Users\hp\OneDrive\Desktop"
pdf_path = os.path.join(desktop_path, "Invoice_Decore_ERP.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=letter)
elements = []
styles = getSampleStyleSheet()

title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=20, textColor=colors.HexColor("#0f172a"))
heading_style = ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor("#0f172a"))
normal_style = styles['Normal']

# Header
elements.append(Paragraph("<b>INVOICE & PROPOSAL</b>", title_style))
elements.append(Paragraph("<b>To:</b> [Client / Company Name]", normal_style))
elements.append(Paragraph("<b>Date:</b> April 27, 2026", normal_style))
elements.append(Paragraph("<b>Invoice #:</b> INV-2026-001", normal_style))
elements.append(Paragraph("<b>Project:</b> Enterprise POP Work Management System (ERP)", normal_style))
elements.append(Spacer(1, 20))

# 1. Software Development
elements.append(Paragraph("<b>1. Professional Services & Software Development</b>", heading_style))
elements.append(Paragraph("<i>Custom ERP Web Application (Source Code & Licensing)</i>", normal_style))
desc = """Included Modules:<br/>
- Core Dashboard: Real-time analytics, financial summaries.<br/>
- Workforce Management: Profiles, roles, document handling.<br/>
- Smart Attendance Engine: Auto-sorting, 'One-Day, One-Attendance', Overtime calculations.<br/>
- Financial Suite: Salary calculations, Advance requests, Payments.<br/>
- Inventory & Logistics: Material requests, delivery logs.<br/>
- Premium UI/UX: Glassmorphic design, mobile-responsive."""
elements.append(Paragraph(desc, normal_style))
elements.append(Spacer(1, 10))
elements.append(Paragraph("<b>Cost:</b> ₹ 1,50,000", normal_style))
elements.append(Spacer(1, 20))

# 2. Cloud Infrastructure
elements.append(Paragraph("<b>2. Cloud Infrastructure & Deployment (AWS)</b>", heading_style))
elements.append(Paragraph("<i>Production-ready deployment on Amazon Web Services.</i>", normal_style))
desc2 = """Included Services:<br/>
- Amazon EC2: Secure Linux server provisioning.<br/>
- Amazon RDS: Managed PostgreSQL database with daily backups.<br/>
- Amazon S3: Cloud storage for media and PDF generation.<br/>
- SSL & Domain: Secure HTTPS lock and Route53 DNS setup."""
elements.append(Paragraph(desc2, normal_style))
elements.append(Spacer(1, 10))
elements.append(Paragraph("<b>Cost:</b> ₹ 25,000", normal_style))
elements.append(Spacer(1, 20))

# 3. Maintenance
elements.append(Paragraph("<b>3. Ongoing Hosting & Maintenance</b>", heading_style))
elements.append(Paragraph("<i>Monthly AWS Resource Costs & Technical Support.</i>", normal_style))
desc3 = """Includes:<br/>
- Monthly AWS Server & Database costs.<br/>
- Security patches and database monitoring.<br/>
- Minor bug fixes and technical support."""
elements.append(Paragraph(desc3, normal_style))
elements.append(Spacer(1, 10))
elements.append(Paragraph("<b>Cost:</b> ₹ 8,000 / month", normal_style))
elements.append(Spacer(1, 30))

# Total Summary
elements.append(Paragraph("<b>Total Investment Summary</b>", heading_style))
data = [
    ['Description', 'Amount'],
    ['Software Development & Core Features', '₹ 1,50,000'],
    ['AWS Infrastructure Setup (One-time)', '₹ 25,000'],
    ['Subtotal (Due upon deployment)', '₹ 1,75,000'],
    ['', ''],
    ['Annual Hosting & Maintenance (Optional)', '₹ 96,000 / year']
]
t = Table(data, colWidths=[300, 150])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (1,0), colors.HexColor("#0f172a")),
    ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
    ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))
]))
elements.append(t)

elements.append(Spacer(1, 30))
elements.append(Paragraph("<b>Important Details & Terms to Notice:</b>", heading_style))
terms = """1. <b>Ownership:</b> Full ownership of source code transferred upon final payment.<br/>
2. <b>Scalability:</b> AWS architecture designed to scale seamlessly without downtime.<br/>
3. <b>Training:</b> Includes 2 complimentary remote training sessions for Administrators.<br/>
4. <b>Payment Terms:</b> 50% deposit required prior to deployment; remaining 50% due on launch."""
elements.append(Paragraph(terms, normal_style))

doc.build(elements)
print(f"PDF successfully generated at: {pdf_path}")

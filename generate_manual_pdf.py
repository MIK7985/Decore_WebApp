import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def build_client_manual():
    output_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Decore_ERP_Client_Manual.pdf')
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=24, textColor=colors.HexColor("#0f172a"), alignment=1, spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Heading2'], fontName='Helvetica',
        fontSize=14, textColor=colors.HexColor("#64748b"), alignment=1, spaceAfter=40
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=16, textColor=colors.HexColor("#1e293b"), spaceBefore=20, spaceAfter=10,
        borderPadding=(0,0,5,0), borderBottomWidth=1, borderBottomColor=colors.HexColor("#e2e8f0")
    )
    h3_style = ParagraphStyle(
        'H3', parent=styles['Heading3'], fontName='Helvetica-Bold',
        fontSize=13, textColor=colors.HexColor("#334155"), spaceBefore=15, spaceAfter=5
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontName='Helvetica',
        fontSize=11, textColor=colors.HexColor("#334155"), leading=16, spaceAfter=10
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=styles['Normal'], fontName='Helvetica',
        fontSize=11, textColor=colors.HexColor("#334155"), leading=16
    )

    # --- COVER PAGE ---
    logo_path = os.path.join('static', 'img', 'Logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.5*inch, height=2.5*inch)
        elements.append(img)
    else:
        elements.append(Spacer(1, 2*inch))
        
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Decore POP Enterprise Resource Planning (ERP)", title_style))
    elements.append(Paragraph("Official Client Handover & System Documentation", subtitle_style))
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Prepared For: Decore Developers", body_style))
    elements.append(Paragraph("System Version: 1.0 (Production Ready)", body_style))
    elements.append(PageBreak())

    # --- SECTION 1: PROJECT OVERVIEW ---
    elements.append(Paragraph("1. Project Overview", h2_style))
    text = ("The Decore ERP is a centralized, cloud-based platform designed specifically to streamline "
            "the management of workforce, attendance, inventory, and financial workflows for construction "
            "and design projects. Built as a Progressive Web App (PWA), it provides a native mobile experience "
            "without requiring app store installation.")
    elements.append(Paragraph(text, body_style))

    # --- SECTION 2: ARCHITECTURE & SECURITY ---
    elements.append(Paragraph("2. Architecture & Security", h2_style))
    elements.append(Paragraph("Role-Based Access Control (RBAC):", h3_style))
    elements.append(Paragraph("The system enforces strict data segregation to protect business intelligence:", body_style))
    
    rbac_items = [
        ListItem(Paragraph("<b>Super Admin:</b> Unrestricted access to all modules, including deep financial metrics, exact site profitability, and material costs.", bullet_style)),
        ListItem(Paragraph("<b>Office Staff:</b> Operational access to manage employees, record attendance, and handle inventory logs. Financial data (profits, budgets, and labor costs) is strictly hidden from this role.", bullet_style)),
    ]
    elements.append(ListFlowable(rbac_items, bulletType='bullet', leftIndent=20))

    # --- SECTION 3: CORE MODULES ---
    elements.append(Paragraph("3. Core Functional Modules", h2_style))

    # Worksites
    elements.append(Paragraph("Worksite & Project Management", h3_style))
    text = ("Track multiple concurrent projects. Managers can break sites down into specific Work Areas, "
            "assign labor directly to sites, and monitor live progress percentages. Automated PDF reports "
            "generate real-time material cost summaries.")
    elements.append(Paragraph(text, body_style))

    # Attendance
    elements.append(Paragraph("Automated Attendance", h3_style))
    text = ("A secure, daily logging system. Office staff can perform bulk check-ins for workers assigned "
            "to specific sites, choosing between Present (Full Day), Half-Day, or Absent. Past dates are locked "
            "to prevent retroactive tampering.")
    elements.append(Paragraph(text, body_style))

    # Salaries
    elements.append(Paragraph("Salary & Payroll Engine", h3_style))
    text = ("The system automates the historically complex payroll process. At the end of a cycle, the system "
            "cross-references a worker's daily wage against their attendance records to calculate exact net pay. "
            "It automatically factors in requested advances and partial payments.")
    elements.append(Paragraph(text, body_style))

    # Inventory
    elements.append(Paragraph("Inventory & Material Tracking", h3_style))
    text = ("A complete ledger of all physical assets. Managers can log raw material deliveries directly to "
            "Work Sites, and the system automatically deducts those expenses from the site's overall profit margin.")
    elements.append(Paragraph(text, body_style))

    # --- SECTION 4: TECHNICAL SPECIFICATIONS ---
    elements.append(Paragraph("4. Technical Specifications", h2_style))
    tech_items = [
        ListItem(Paragraph("<b>Backend Framework:</b> Python (Django)", bullet_style)),
        ListItem(Paragraph("<b>Database:</b> PostgreSQL (AWS Production) / SQLite (Local)", bullet_style)),
        ListItem(Paragraph("<b>Frontend:</b> HTML5, Vanilla CSS (Glassmorphism UI), Bootstrap Grid", bullet_style)),
        ListItem(Paragraph("<b>Hosting:</b> AWS EC2 (Ubuntu), Nginx, Gunicorn", bullet_style)),
        ListItem(Paragraph("<b>PDF Generation:</b> ReportLab Engine", bullet_style)),
    ]
    elements.append(ListFlowable(tech_items, bulletType='bullet', leftIndent=20))

    # --- SECTION 5: PWA DEPLOYMENT ---
    elements.append(Paragraph("5. Mobile PWA Installation", h2_style))
    text = ("To install the ERP as a mobile application on any device, navigate to the production URL using "
            "a mobile browser (Safari/Chrome), open the browser menu, and select <b>'Add to Home Screen'</b>. "
            "The system will install locally and operate as a standalone, full-screen application.")
    elements.append(Paragraph(text, body_style))

    # Build PDF
    doc.build(elements)
    print(f"Client PDF Manual generated successfully at: {output_path}")

if __name__ == "__main__":
    build_client_manual()

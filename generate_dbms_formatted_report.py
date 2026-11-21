import os
import docx
from PIL import Image
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls


# =============================================================================
# XML HELPER FUNCTIONS
# =============================================================================

def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))


def set_cell_background(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:cantSplit'))


def set_row_header(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:tblHeader'))


def add_field(run, field_text, cached_val=""):
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = f" {field_text} "
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    if cached_val:
        t = OxmlElement('w:t')
        t.text = str(cached_val)
        run._r.append(t)
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar3)


def add_bookmark(paragraph, bm_id, bm_name):
    start = OxmlElement('w:bookmarkStart')
    start.set(qn('w:id'), str(bm_id))
    start.set(qn('w:name'), bm_name)
    end = OxmlElement('w:bookmarkEnd')
    end.set(qn('w:id'), str(bm_id))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def enable_update_fields_on_open(doc):
    settings = doc.settings.element
    update_fields = OxmlElement('w:updateFields')
    update_fields.set(qn('w:val'), 'true')
    settings.append(update_fields)


def set_paragraph_shading_and_border(paragraph, fill_hex="F5F7FA", border_color="1B365D"):
    pPr = paragraph._p.get_or_add_pPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill_hex}"/>')
    pPr.append(shd)
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="18" w:space="8" w:color="{border_color}"/>'
        f'<w:top w:val="single" w:sz="4" w:space="4" w:color="D8DFE8"/>'
        f'<w:right w:val="single" w:sz="4" w:space="6" w:color="D8DFE8"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="4" w:color="D8DFE8"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)


def set_page_number_start(section, start_num=1, fmt="decimal"):
    sectPr = section._sectPr
    pgNumType = OxmlElement('w:pgNumType')
    pgNumType.set(qn('w:start'), str(start_num))
    pgNumType.set(qn('w:fmt'), fmt)
    sectPr.append(pgNumType)


# =============================================================================
# REPORT BUILDER
# =============================================================================

def build_dbms_report():
    doc = docx.Document()
    enable_update_fields_on_open(doc)

    # Paths
    scratch_dir = r"C:\Users\HP\.gemini\antigravity\brain\f3255e1c-82ec-45a0-9e0a-4bb1cdf5a518\scratch"
    report_imgs_dir = os.path.join(scratch_dir, "report_imgs")
    logo_path = os.path.join(scratch_dir, "vit_logo.jpg")

    NAVY = RGBColor(0x1B, 0x36, 0x5D)
    DARK = RGBColor(0x1A, 0x1A, 0x1A)
    MUTED = RGBColor(0x4A, 0x55, 0x68)

    # Base Normal Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = DARK

    # Section 1: Front Matter (Title Page, Abstract, TOC)
    sec1 = doc.sections[0]
    sec1.page_width = Mm(210)
    sec1.page_height = Mm(297)
    sec1.top_margin = Mm(25.4)
    sec1.bottom_margin = Mm(25.4)
    sec1.left_margin = Mm(31.75)   # 1.25 inch binding margin
    sec1.right_margin = Mm(25.4)   # 1.0 inch right margin
    sec1.header.is_linked_to_previous = False
    sec1.footer.is_linked_to_previous = False
    sec1.different_first_page_header_footer = True
    set_page_number_start(sec1, start_num=1, fmt="lowerRoman")

    # Roman numeral footer on front matter pages (ii, iii) — suppressed on Title Page (first page)
    f1 = sec1.footer
    f1p = f1.paragraphs[0]
    f1p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f1r = f1p.add_run()
    f1r.font.name = 'Times New Roman'
    f1r.font.size = Pt(10)
    f1r.font.color.rgb = MUTED
    add_field(f1r, "PAGE", cached_val="ii")

    bm_counter = [100]

    def next_bm_id():
        bm_counter[0] += 1
        return bm_counter[0]

    # -------------------------------------------------------------------------
    # HELPER FUNCTIONS FOR CONTENT
    # -------------------------------------------------------------------------

    def p_center(text, size=12, bold=False, italic=False, color=DARK, space_before=0, space_after=6, line_spacing=1.15):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        r.font.color.rgb = color
        return p

    def add_section_title(num_str, title_text, bm_name=None, page_break_before=True):
        if page_break_before:
            doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(14)
        p.paragraph_format.keep_with_next = True
        full_title = f"{num_str}. {title_text}".upper() if num_str else title_text.upper()
        r = p.add_run(full_title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(15)
        r.bold = True
        r.font.color.rgb = NAVY
        # Add clean bottom divider under major section heading
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1B365D"/></w:pBdr>')
        pPr.append(pBdr)
        if bm_name:
            add_bookmark(p, next_bm_id(), bm_name)
        return p

    def add_h2(text, bm_name=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.bold = True
        r.font.color.rgb = NAVY
        if bm_name:
            add_bookmark(p, next_bm_id(), bm_name)
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.bold = True
        r.font.color.rgb = DARK
        return p

    def add_body(text, indent=False, space_after=8):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.35
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.35)
        r = p.add_run(text.strip())
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)
        r.font.color.rgb = DARK
        return p

    def add_bullet(lead_bold, rest_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(4)
        r_b = p.add_run("•  ")
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(11.5)
        r_b.bold = True
        r_b.font.color.rgb = NAVY
        if lead_bold:
            r1 = p.add_run(lead_bold)
            r1.font.name = 'Times New Roman'
            r1.font.size = Pt(11.5)
            r1.bold = True
            r1.font.color.rgb = DARK
        r2 = p.add_run(rest_text)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = DARK
        return p

    def add_code_block(code_text, title=None):
        if title:
            pt = doc.add_paragraph()
            pt.paragraph_format.space_before = Pt(6)
            pt.paragraph_format.space_after = Pt(2)
            pt.paragraph_format.keep_with_next = True
            rt = pt.add_run(title)
            rt.font.name = 'Times New Roman'
            rt.font.size = Pt(10.5)
            rt.bold = True
            rt.font.color.rgb = NAVY
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.08
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.left_indent = Inches(0.12)
        p.paragraph_format.right_indent = Inches(0.12)
        set_paragraph_shading_and_border(p)
        r = p.add_run(code_text.strip())
        r.font.name = 'Consolas'
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        return p

    def add_styled_table(headers, rows, col_widths, caption_num=None, caption_text=None, bm_name=None, font_size=9.5):
        if caption_num and caption_text:
            pc = doc.add_paragraph()
            pc.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pc.paragraph_format.space_before = Pt(10)
            pc.paragraph_format.space_after = Pt(4)
            pc.paragraph_format.keep_with_next = True
            rc = pc.add_run(f"Table {caption_num}: {caption_text}")
            rc.font.name = 'Times New Roman'
            rc.font.size = Pt(11)
            rc.bold = True
            rc.font.color.rgb = NAVY
            if bm_name:
                add_bookmark(pc, next_bm_id(), bm_name)

        tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False

        # Header row
        hdr_row = tbl.rows[0]
        set_row_header(hdr_row)
        set_row_cant_split(hdr_row)
        for ci, h_text in enumerate(headers):
            cell = hdr_row.cells[ci]
            cell.width = Inches(col_widths[ci])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, "1B365D")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            set_cell_border(
                cell,
                top={"val": "single", "sz": 6, "color": "1B365D"},
                bottom={"val": "single", "sz": 6, "color": "1B365D"},
                left={"val": "single", "sz": 4, "color": "2C4D75"},
                right={"val": "single", "sz": 4, "color": "2C4D75"},
            )
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(h_text)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(font_size)
            r.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # Data rows
        for ri, row_vals in enumerate(rows):
            row = tbl.rows[ri + 1]
            set_row_cant_split(row)
            bg = "F4F7FA" if ri % 2 == 1 else "FFFFFF"
            for ci, val in enumerate(row_vals):
                cell = row.cells[ci]
                cell.width = Inches(col_widths[ci])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_background(cell, bg)
                set_cell_margins(cell, top=55, bottom=55, left=90, right=90)
                set_cell_border(
                    cell,
                    top={"val": "single", "sz": 4, "color": "CBD5E1"},
                    bottom={"val": "single", "sz": 4, "color": "CBD5E1"},
                    left={"val": "single", "sz": 4, "color": "CBD5E1"},
                    right={"val": "single", "sz": 4, "color": "CBD5E1"},
                )
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.12
                r = p.add_run(str(val))
                r.font.name = 'Times New Roman'
                r.font.size = Pt(font_size)
                if ci == 0:
                    r.bold = True
                r.font.color.rgb = DARK

        # Small spacer after table
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)
        return tbl

    def embed_image(img_path, fig_num, fig_title, bm_name=None, max_width=5.85, max_height=3.6, description=None):
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Missing required image: {img_path}")
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        aspect = w_px / h_px
        width_in = max_width
        height_in = width_in / aspect
        if height_in > max_height:
            height_in = max_height
            width_in = height_in * aspect

        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(3)
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(img_path, width=Inches(width_in))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(1)
        p_cap.paragraph_format.space_after = Pt(4 if description else 10)
        if description:
            p_cap.paragraph_format.keep_with_next = True
        r_cap = p_cap.add_run(f"Figure {fig_num}: {fig_title}")
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10.5)
        r_cap.italic = True
        r_cap.bold = True
        r_cap.font.color.rgb = NAVY
        if bm_name:
            add_bookmark(p_cap, next_bm_id(), bm_name)

        if description:
            p_desc = doc.add_paragraph()
            p_desc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_desc.paragraph_format.line_spacing = 1.25
            p_desc.paragraph_format.space_before = Pt(0)
            p_desc.paragraph_format.space_after = Pt(10)
            r_d = p_desc.add_run(description)
            r_d.font.name = 'Times New Roman'
            r_d.font.size = Pt(10.5)
            r_d.font.color.rgb = DARK

    # =========================================================================
    # SECTION 1: TITLE PAGE (Format Item 1)
    # =========================================================================
    p_center("A Course Project Report", size=13, bold=False, space_before=6, space_after=4)
    p_center("on", size=12, italic=True, space_after=8)
    p_center(
        "CAMPUSRIDE: SMART PEER-TO-PEER CAMPUS VEHICLE RENTAL SYSTEM\n"
        "WITH 100% SQL-DRIVEN CORE AND AI/ML FLEET INTELLIGENCE",
        size=15, bold=True, color=NAVY, space_after=16, line_spacing=1.25
    )

    p_center("SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE COURSE", size=10.5, bold=True, space_after=3)
    p_center("DATABASE MANAGEMENT SYSTEMS (DBMS)", size=12.5, bold=True, color=NAVY, space_after=10)

    p_center("BACHELOR OF TECHNOLOGY IN", size=11, bold=True, space_after=3)
    p_center("Computer Science & Engineering (Artificial Intelligence)", size=13, bold=True, space_after=14)

    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(10)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.25))

    p_center("SUBMITTED BY", size=11, bold=True, color=NAVY, space_after=4)
    p_center(
        "Student Name 1  (PRN: 12110001)\n"
        "Student Name 2  (PRN: 12110002)\n"
        "Student Name 3  (PRN: 12110003)\n"
        "Student Name 4  (PRN: 12110004)",
        size=11.5, bold=True, space_after=14, line_spacing=1.25
    )

    p_center("UNDER THE GUIDANCE OF", size=11, bold=True, color=NAVY, space_after=4)
    p_center("Prof. [Guide Name]", size=12, bold=True, space_after=18)

    p_center("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING (ARTIFICIAL INTELLIGENCE)", size=11, bold=True, color=NAVY, space_after=3)
    p_center("BANSILAL RAMNATH AGARWAL CHARITABLE TRUST'S", size=10, bold=False, space_after=2)
    p_center("VISHWAKARMA INSTITUTE OF TECHNOLOGY, PUNE", size=12.5, bold=True, space_after=2)
    p_center("(An Autonomous Institute affiliated to Savitribai Phule Pune University)", size=10, italic=True, space_after=4)
    p_center("PUNE – 411037  |  ACADEMIC YEAR: 2026 – 2027", size=11, bold=True, space_after=0)

    # =========================================================================
    # SECTION 2: ABSTRACT (Format Item 2)
    # =========================================================================
    add_section_title("2", "ABSTRACT", bm_name="sec_abstract", page_break_before=True)

    abs_parts = [
        ("Problem: ",
         "Modern university campuses span extensive academic blocks, residential hostels, laboratories, and sports complexes, "
         "making daily intra-campus commuting slow and physically tiring. Commercial cab aggregators are expensive and frequently "
         "restricted from entering gated institutional zones, while over 70% of privately owned student and faculty two-wheelers "
         "remain parked and idle during academic hours. Existing rental applications typically rely on stateless application-layer "
         "Object-Relational Mapping (ORM) frameworks, exposing high-concurrency reservation periods to double-booking race conditions, "
         "inconsistent inventory states, lack of audit accountability, and vulnerability to off-campus unauthorized vehicle usage."),
        ("Solution: ",
         "CampusRide addresses these operational and architectural gaps through a peer-to-peer (P2P) campus micro-mobility platform "
         "engineered around a 100% SQL-driven database core combined with an AI/ML Predictive Intelligence Suite. Verified students "
         "and faculty list idle vehicles for affordable hourly rental (Rs. 45–200/hr), while peers discover, reserve, pay, and review "
         "vehicles through role-based portals (Renter, Owner, and Admin). Every critical transactional rule—authentication with brute-force "
         "lockout, availability guarding, coupon calculation, booking settlement, and immutable audit logging—is enforced natively inside "
         "the relational database engine."),
        ("Technology: ",
         "The persistence layer runs on MySQL 8.0 (InnoDB) comprising 10 normalized relational tables, 6 views, 7 user-defined functions, "
         "10 stored procedures, and 7 automated triggers. The application gateway uses Python 3.11 and FastAPI (Uvicorn) executing raw "
         "parameterized SQL procedure calls with JWT authentication and zero ORM overhead. The machine learning layer utilizes Scikit-learn, "
         "NumPy, and Pandas to deliver TF-IDF + Cosine Similarity vehicle recommendations, Time-Series demand forecasting, Isolation Forest "
         "payment anomaly detection, predictive maintenance degradation scoring, dynamic pricing suggestions, and Haversine GPS geofencing. "
         "The presentation tier uses responsive HTML5, CSS3 glassmorphism, and ES6 JavaScript."),
        ("Outcome: ",
         "Live deployment and end-to-end validation across 7 registered user accounts, 8 listed vehicles, and 9 completed/active rentals "
         "(generating Rs. 2,210 in verified transactions) confirm zero double-booking conflicts via BEFORE INSERT trigger guards, instantaneous "
         "inventory state synchronization, automated immutable audit trails (65+ sequential entries), 90.2% average fleet health telemetry, "
         "accurate anomaly flagging, and real-time detection of simulated 8.5 km perimeter geofence breaches."),
    ]
    for lead, body_txt in abs_parts:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.28
        p.paragraph_format.first_line_indent = Inches(0.3)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(10)
        r1 = p.add_run(lead)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11.5)
        r1.bold = True
        r1.font.color.rgb = NAVY
        r2 = p.add_run(body_txt)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = DARK

    # =========================================================================
    # SECTION 3: TABLE OF CONTENTS + LIST OF FIGURES & TABLES (Format Item 3)
    # =========================================================================
    add_section_title("3", "TABLE OF CONTENTS", bm_name="sec_toc", page_break_before=True)

    toc_entries = [
        ("1.", "Title Page", "Title", "i", True),
        ("2.", "Abstract", "sec_abstract", "ii", True),
        ("3.", "Table of Contents", "sec_toc", "iii", True),
        ("4.", "Introduction", "sec_intro", "1", True),
        ("5.", "Objectives", "sec_obj", "2", True),
        ("6.", "System Design and Architecture", "sec_design", "3", True),
        ("6.1", "    Three-Tier Decoupled Architecture", "sec_arch_desc", "3", False),
        ("6.2", "    Entity-Relationship (ER) Diagram", "sec_er", "4", False),
        ("7.", "Implementation Technology", "sec_impl", "5", True),
        ("7.1", "    Technology Stack Overview", "sec_stack", "5", False),
        ("7.2", "    Relational Database Schema (10 Tables & Fields)", "sec_tables", "5", False),
        ("7.3", "    SQL Joins Implemented", "sec_joins", "10", False),
        ("7.4", "    Database Views (6 Views)", "sec_views", "11", False),
        ("7.5", "    Nested Queries (Subqueries)", "sec_nested", "12", False),
        ("7.6", "    Correlated Subqueries", "sec_corr", "12", False),
        ("7.7", "    Aggregate Functions and Analytical Grouping", "sec_agg", "13", False),
        ("7.8", "    User-Defined Functions (7 Functions)", "sec_udfs", "14", False),
        ("7.9", "    Stored Procedures (10 Procedures)", "sec_procs", "14", False),
        ("7.10", "    Database Triggers (7 Triggers)", "sec_trigs", "15", False),
        ("7.11", "    AI/ML Intelligence & Geofencing Engine", "sec_aiml", "16", False),
        ("8.", "Results & Output (Application Screenshots)", "sec_results", "18", True),
        ("8.1", "    Renter Portal Screenshots", "sec_res_renter", "18", False),
        ("8.2", "    Vehicle Owner Portal Screenshots", "sec_res_owner", "21", False),
        ("8.3", "    Admin Panel, Security & AIML Screenshots", "sec_res_admin", "25", False),
        ("9.", "Conclusion and Future Scope", "sec_concl", "31", True),
        ("10.", "References", "sec_refs", "32", True),
        ("11.", "Appendix (Extra Diagrams & Key Source Code)", "sec_app", "33", True),
    ]

    tbl_toc = doc.add_table(rows=len(toc_entries) + 1, cols=3)
    tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_toc.autofit = False
    toc_widths = [0.7, 4.45, 0.85]

    hdr_row = tbl_toc.rows[0]
    set_row_header(hdr_row)
    for ci, h_txt in enumerate(["Sr. No.", "Section / Chapter Title", "Page No."]):
        cell = hdr_row.cells[ci]
        cell.width = Inches(toc_widths[ci])
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci != 1 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_txt)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10.5)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for idx, (sr, title, bm, fallback_pg, is_bold) in enumerate(toc_entries):
        row = tbl_toc.rows[idx + 1]
        set_row_cant_split(row)
        bg = "F8FAFC" if idx % 2 == 1 else "FFFFFF"
        for ci, val in enumerate([sr, title, fallback_pg]):
            cell = row.cells[ci]
            cell.width = Inches(toc_widths[ci])
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=35, bottom=35, left=80, right=80)
            set_cell_border(
                cell,
                bottom={"val": "single", "sz": 4, "color": "E2E8F0"},
                top={"val": "none"}, left={"val": "none"}, right={"val": "none"}
            )
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.08
            if ci == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
            elif ci == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                r = p.add_run()
                if bm != "Title":
                    add_field(r, f"PAGEREF {bm} \\h", cached_val=val)
                else:
                    r.text = val
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10)
            r.bold = is_bold
            r.font.color.rgb = NAVY if is_bold else DARK

    # Note about automatic page numbers
    p_note = doc.add_paragraph()
    p_note.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_note.paragraph_format.space_before = Pt(6)
    p_note.paragraph_format.space_after = Pt(8)
    r_note = p_note.add_run("Note: Page numbers are linked via dynamic Word PAGEREF fields and auto-update upon opening.")
    r_note.font.name = 'Times New Roman'
    r_note.font.size = Pt(9)
    r_note.italic = True
    r_note.font.color.rgb = MUTED

    # =========================================================================
    # SECTION 2 OF DOCUMENT: MAIN REPORT BODY (Arabic Page Numbers 1, 2, 3...)
    # =========================================================================
    sec2 = doc.add_section()
    sec2.page_width = Mm(210)
    sec2.page_height = Mm(297)
    sec2.top_margin = Mm(25.4)
    sec2.bottom_margin = Mm(25.4)
    sec2.left_margin = Mm(31.75)
    sec2.right_margin = Mm(25.4)
    sec2.header.is_linked_to_previous = False
    sec2.footer.is_linked_to_previous = False
    set_page_number_start(sec2, start_num=1, fmt="decimal")

    # Header for Section 2
    hdr = sec2.header
    hp = hdr.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hp.add_run("CampusRide: Smart Peer-to-Peer Campus Vehicle Rental System — DBMS Project Report")
    hr.font.name = 'Times New Roman'
    hr.font.size = Pt(9)
    hr.italic = True
    hr.font.color.rgb = MUTED

    # Footer for Section 2
    ftr = sec2.footer
    fp1 = ftr.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp1.paragraph_format.space_before = Pt(2)
    fp1.paragraph_format.space_after = Pt(2)
    fr1 = fp1.add_run("VIT Pune — Department of Computer Science & Engineering (AI)  |  Page ")
    fr1.font.name = 'Times New Roman'
    fr1.font.size = Pt(9.5)
    fr1.font.color.rgb = MUTED
    fr_pg = fp1.add_run()
    fr_pg.font.name = 'Times New Roman'
    fr_pg.font.size = Pt(9.5)
    fr_pg.bold = True
    fr_pg.font.color.rgb = NAVY
    add_field(fr_pg, "PAGE", cached_val="1")

    # =========================================================================
    # SECTION 4: INTRODUCTION (Format Item 4)
    # =========================================================================
    add_section_title("4", "INTRODUCTION", bm_name="sec_intro", page_break_before=False)

    add_body(
        "Contemporary higher-education institutions resemble self-contained townships, spanning academic complexes, residential "
        "hostels, central libraries, laboratories, and distant entrance gates. Students and faculty regularly commute between "
        "these locations under tight academic schedules. Relying exclusively on walking is physically exhausting and inefficient, "
        "whereas commercial cab services impose steep base fares and are frequently prohibited from operating within gated campus "
        "perimeters. Simultaneously, thousands of privately owned student scooters, motorcycles, and cars remain parked and idle "
        "in hostel parking lots for eight to ten hours each day.",
        indent=True
    )
    add_body(
        "CampusRide is a full-stack, peer-to-peer (P2P) campus vehicle sharing and fleet management system designed to bridge this "
        "mobility gap. The platform empowers verified students and faculty members (Owners) to monetize their idle two-wheelers "
        "and four-wheelers on an hourly rental basis, while providing fellow students (Renters) with safe, instant, and economical "
        "intra-campus transportation. Centralized institutional oversight is enabled through an Administrative Console with live "
        "financial analytics, immutable audit trails, and perimeter geofencing.",
        indent=True
    )
    add_body(
        "From a Database Management Systems engineering perspective, CampusRide distinguishes itself through a 100% SQL-Driven "
        "Transactional Core. Instead of delegating mission-critical validation, inventory locking, password hashing, pricing, and "
        "audit logging to fragile application-layer ORM models, all core business rules are compiled directly inside MySQL 8.0 as "
        "stored procedures, user-defined functions, views, and triggers. Complementing this ACID-compliant database foundation is "
        "an integrated Python Machine Learning Intelligence Suite delivering personalized recommendations, time-series demand "
        "forecasting, unsupervised payment fraud detection, predictive fleet maintenance scoring, and GPS boundary monitoring.",
        indent=True
    )

    add_styled_table(
        headers=["Parameter", "Commercial Cabs (Uber/Ola)", "Dockless Rentals (Bounce/Yulu)", "CampusRide (Proposed)"],
        rows=[
            ["Fleet Ownership", "External private drivers", "Centralized company fleet (High CapEx)", "Verified Student & Faculty Peers (Zero CapEx)"],
            ["Cost to Student", "High (Rs. 100+ base fare)", "Moderate (Rs. 5/min + security deposits)", "Highly Affordable (Rs. 45–200/hr)"],
            ["Transaction Core", "Application-layer services", "Distributed app microservices", "100% SQL-Driven MySQL 8.0 (ACID)"],
            ["Concurrency Control", "Application locks", "Queue-based reservation locks", "BEFORE INSERT Trigger Guard & Transactions"],
            ["Security & Perimeter", "Unrestricted city-wide", "City municipal geofence", "Strict 2.5 km Campus Geofence + AuditLog"],
            ["AI/ML Intelligence", "Driver dispatch pricing", "Battery swap routing", "TF-IDF Recs, Isolation Forest, Wear Health"],
        ],
        col_widths=[1.25, 1.45, 1.55, 1.75],
        caption_num="4.1",
        caption_text="Comparison of Existing Mobility Systems versus CampusRide",
        bm_name="tbl_comp",
        font_size=9.0
    )

    # =========================================================================
    # SECTION 5: OBJECTIVES (Format Item 5)
    # =========================================================================
    add_section_title("5", "OBJECTIVES", bm_name="sec_obj", page_break_before=True)

    add_body(
        "The primary goal of CampusRide is to design, implement, and validate a secure, database-centric peer-to-peer vehicle rental "
        "ecosystem tailored for university campuses. The specific functional and technical objectives are:",
        indent=True
    )

    add_bullet("1. Peer-to-Peer Campus Mobility & Asset Monetization: ",
               "Enable verified students and faculty to list idle scooters, bikes, and cars with configurable hourly rates and pickup hubs, allowing campus peers to search, filter, book, pay, and review rides seamlessly.")
    add_bullet("2. 100% DBMS-Driven Business Logic & ACID Integrity: ",
               "Eliminate application-layer race conditions and double-booking anomalies by executing registration, brute-force-protected login, rental creation, cost/discount computation, payment settlement, and vehicle status transitions inside MySQL 8.0 stored procedures, functions, and triggers.")
    add_bullet("3. Comprehensive Role-Based Access Control (RBAC): ",
               "Deliver dedicated interactive portals for three distinct user roles—Renter (Student), Vehicle Owner, and System Administrator—secured with salted SHA-256 hashing (`vitcampus` salt), JWT bearer tokens, and automated 15-minute lockouts after 5 consecutive failed login attempts.")
    add_bullet("4. Immutable Security Auditing & Governance: ",
               "Automatically capture every registration, login, rental creation, status completion, payment settlement, maintenance schedule, and geofence breach into an append-only `AuditLog` table via database triggers.")
    add_bullet("5. AI-Powered Personalized Recommendations & Demand Forecasting: ",
               "Deploy a TF-IDF + Cosine Similarity recommender to match students with optimal vehicles based on preferences and budget, alongside time-series demand forecasting across vehicle categories and campus hotspots (Main Gate, Hostel A, Library, Sports Ground).")
    add_bullet("6. Unsupervised Anomaly Detection & Predictive Fleet Maintenance: ",
               "Utilize Scikit-learn's Isolation Forest (`contamination=0.05`) to flag suspicious payment outliers and student velocity spikes, and compute real-time vehicle health scores using cumulative rental hours, trip frequency, service intervals, and driver ratings.")
    add_bullet("7. Real-Time Campus Perimeter Geofencing: ",
               "Continuously evaluate vehicle GPS telemetry against the campus center (Lat 13.0020, Lng 80.2350) using the Haversine formula to raise immediate boundary breach alerts whenever a vehicle travels beyond the authorized 2.5 km operational radius.")

    # =========================================================================
    # SECTION 6: SYSTEM DESIGN OR ARCHITECTURE (Format Item 6)
    # =========================================================================
    add_section_title("6", "SYSTEM DESIGN AND ARCHITECTURE", bm_name="sec_design", page_break_before=True)

    add_h2("6.1 Three-Tier Decoupled Architecture", bm_name="sec_arch_desc")
    add_body(
        "CampusRide is structured on a decoupled three-tier software architecture that enforces a clean separation of concerns between "
        "user presentation, stateless API routing / machine learning inference, and transactional database execution:",
        indent=True
    )
    add_bullet("Tier 1 — Presentation Layer (Frontend): ",
               "Built with responsive HTML5, CSS3 dark-mode glassmorphism styling, and modular ES6 JavaScript using the Fetch API. It serves three specialized portals: `dashboard.html` (Renter), `owner-dashboard.html` (Vehicle Owner), and `admin-dashboard.html` (System Administrator), plus `index.html` for unified role-based login/registration and `profile.html` for profile management.")
    add_bullet("Tier 2 — Application Gateway & AI/ML Layer (Backend): ",
               "Powered by Python 3.11 and FastAPI running on Uvicorn (port 15501). Rather than using an ORM, SQLAlchemy is used exclusively as a lightweight connection pool to dispatch parameterized `CALL sp_*` and `SELECT * FROM vw_*` queries. This tier also handles JWT token issuance (`auth.py`), hosts the Scikit-learn `MLEngine` (`ml/recommendation.py`), and evaluates Haversine geofencing coordinates (`routes/security.py`).")
    add_bullet("Tier 3 — Database Management Layer (MySQL 8.0 InnoDB): ",
               "Acts as the single source of truth and transactional engine. Ten normalized InnoDB tables store core entities with strict foreign key cascades, CHECK constraints, and secondary indexes. Six compiled views accelerate read queries, seven user-defined functions compute deterministic values, ten stored procedures execute multi-step ACID transactions, and seven triggers guarantee automatic state transitions and immutable audit logging.")

    add_h2("6.2 Entity-Relationship (ER) Diagram", bm_name="sec_er")
    add_body(
        "Figure 6.1 illustrates the Extended Entity-Relationship (EER) diagram of CampusRide. It models the core entity `STUDENT` "
        "with overlapping specialization into `RENTER`, `VEHICLE_OWNER`, and `CAMPUS_ADMIN`, and `VEHICLE` with disjoint "
        "specialization into `TWO_WHEELER` (scooter, bike, bicycle) and `FOUR_WHEELER` (car). Core operational relationships "
        "include `OWNS` (1:N), `RENTS` (1:N), `BOOKED_IN` (1:N), `HAS_PAYMENT` (1:1), `USES` coupon (0..1:N), `RECEIVES_REVIEW` "
        "(0..1:1), `UNDERGOES` maintenance (1:N), and `GENERATES` audit logs (1:N). Additionally, the lower dashed block models "
        "the AI/ML Extension Module (`STUDENT_ML_PROFILE`, `ML_MODEL_REGISTRY`, and `RENTAL_PREDICTION`), demonstrating seamless "
        "conceptual integration between operational RDBMS entities and predictive analytics.",
        indent=True
    )

    er_path = os.path.join(report_imgs_dir, "Screenshot 2026-10-05 145038.png")
    embed_image(
        er_path,
        fig_num="6.1",
        fig_title="Extended Entity-Relationship (EER) Diagram of CampusRide with AI/ML Extension Module",
        bm_name="fig_er",
        max_width=6.0,
        max_height=3.8
    )

    add_body(
        "In the physical MySQL 8.0 implementation (`schema.sql`), the overlapping `STUDENT` sub-entities are consolidated into the "
        "`Student` table via the `role` ENUM (`'student'`, `'owner'`, `'admin'`) to simplify multi-role campus accounts (e.g., a "
        "student who both lists a vehicle and rents another peer's vehicle). Similarly, `VEHICLE` subtypes are unified using "
        "`vehicle_type`, `seating_capacity`, and `fuel_type`, while additional enterprise governance tables (`Insurance` and `Dispute`) "
        "extend operational completeness to 10 normalized relational tables in Third Normal Form (3NF).",
        indent=True
    )

    # =========================================================================
    # SECTION 7: IMPLEMENTATION TECHNOLOGY (Format Item 7)
    # =========================================================================
    add_section_title("7", "IMPLEMENTATION TECHNOLOGY", bm_name="sec_impl", page_break_before=True)

    add_h2("7.1 Technology Stack Overview", bm_name="sec_stack")
    add_styled_table(
        headers=["Layer", "Technology / Tool", "Role in CampusRide"],
        rows=[
            ["Database Engine", "MySQL 8.0 (InnoDB, utf8mb4)", "10 tables, 6 views, 7 UDFs, 10 stored procedures, 7 triggers, ACID transactions"],
            ["Backend API", "Python 3.11, FastAPI, Uvicorn", "27+ REST endpoints, JWT bearer authentication, raw SQL procedure dispatch"],
            ["DB Connectivity", "SQLAlchemy 2.0 + PyMySQL", "Connection pooling and parameterized raw `text()` SQL execution (zero ORM)"],
            ["AI / ML Suite", "Scikit-learn, NumPy, Pandas", "TF-IDF Cosine Recommender, Isolation Forest Anomaly Detector, Demand & Wear ML"],
            ["Geofencing", "Haversine Formula (Python)", "GPS coordinate perimeter verification (Center 13.0020, 80.2350; Radius 2.5 km)"],
            ["Frontend UI", "HTML5, CSS3, ES6 JavaScript", "Dark-mode glassmorphic Renter, Owner, and Admin dashboards with async Fetch API"],
        ],
        col_widths=[1.25, 1.85, 2.9],
        caption_num="7.1",
        caption_text="CampusRide Implementation Technology Stack",
        bm_name="tbl_stack",
        font_size=9.0
    )

    add_h2("7.2 Relational Database Schema (10 Tables with Exact Fields)", bm_name="sec_tables")
    add_body(
        "The `campusride` database is normalized to 3NF across 10 relational tables defined in `sql/schema.sql`. Every table enforces "
        "entity integrity via `AUTO_INCREMENT` primary keys, referential integrity via `FOREIGN KEY` constraints (`ON DELETE CASCADE`, "
        "`RESTRICT`, `SET NULL`), domain integrity via `ENUM` and `CHECK` constraints, and query optimization via secondary B-Tree indexes.",
        indent=True
    )

    # Table 1: Student
    add_styled_table(
        headers=["Field Name", "Data Type", "Constraints / Default", "Description"],
        rows=[
            ["student_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique identifier for each user"],
            ["full_name", "VARCHAR(100)", "NOT NULL", "Full name of student, owner, or admin"],
            ["email", "VARCHAR(100)", "UNIQUE, NOT NULL, INDEX(idx_email)", "Institutional login email address"],
            ["phone", "VARCHAR(15)", "NOT NULL", "10-digit contact mobile number"],
            ["department", "VARCHAR(50)", "NOT NULL", "Academic department (CSE, ECE, Mech, IT)"],
            ["hostel", "VARCHAR(50)", "NOT NULL", "Campus hostel or residential address"],
            ["password_hash", "VARCHAR(255)", "NOT NULL", "Salted SHA-256 hash via fn_hash_password"],
            ["role", "ENUM", "('student','owner','admin'), DEFAULT 'student', INDEX", "Role-based access control level"],
            ["roll_number", "VARCHAR(50)", "NULLABLE", "University PRN / Roll number (e.g. CAMPUS202401)"],
            ["bio", "TEXT", "NULLABLE", "Optional user profile biography"],
            ["trust_score", "DECIMAL(3,1)", "DEFAULT 5.0", "Reputation & reliability trust metric"],
            ["is_verified", "BOOLEAN", "DEFAULT TRUE", "Institutional verification flag"],
            ["account_status", "ENUM", "('Active','Suspended','Locked'), DEFAULT 'Active'", "Security state controlled by sp_login / admin"],
            ["failed_attempts", "INT", "DEFAULT 0", "Consecutive failed password counter (locks at 5)"],
            ["locked_until", "DATETIME", "DEFAULT NULL", "15-minute lockout expiry timestamp"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Account registration timestamp"],
        ],
        col_widths=[1.2, 1.05, 1.85, 1.9],
        caption_num="7.2",
        caption_text="Schema Definition — Table 1: Student (16 Fields)",
        font_size=8.5
    )

    # Table 2: Vehicle
    add_styled_table(
        headers=["Field Name", "Data Type", "Constraints / Default", "Description"],
        rows=[
            ["vehicle_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique vehicle identifier"],
            ["owner_id", "INT", "NOT NULL, FK -> Student(student_id) CASCADE, INDEX", "Registered owner of the vehicle"],
            ["vehicle_type", "VARCHAR(30)", "NOT NULL", "Category: Scooter, Bike, Car, Bicycle"],
            ["brand", "VARCHAR(50)", "NOT NULL", "Manufacturer (Honda, TVS, Royal Enfield, Maruti)"],
            ["model", "VARCHAR(50)", "NOT NULL", "Model name (Activa, Jupiter, Classic 350, Swift)"],
            ["seating_capacity", "INT", "NOT NULL, DEFAULT 2", "Maximum passenger seating capacity"],
            ["fuel_type", "ENUM", "('Petrol','Diesel','Electric'), NOT NULL", "Propulsion energy source"],
            ["hourly_rate", "DECIMAL(10,2)", "NOT NULL, CHECK (hourly_rate > 0)", "Rental tariff in INR per hour"],
            ["availability_status", "ENUM", "('Available','Rented','Maintenance'), INDEX", "Real-time status managed by triggers"],
            ["license_plate", "VARCHAR(20)", "UNIQUE, NOT NULL", "Registration plate (e.g. MH02AB1234)"],
            ["location", "VARCHAR(100)", "DEFAULT 'Campus Main Gate'", "Designated campus pickup parking hub"],
            ["description", "TEXT", "NULLABLE", "Additional vehicle details and condition notes"],
            ["avg_rating", "DECIMAL(3,1)", "DEFAULT 0.0", "Aggregated mean star rating from reviews"],
            ["total_reviews", "INT", "DEFAULT 0", "Total count of submitted reviews"],
            ["is_approved", "BOOLEAN", "DEFAULT TRUE", "Administrative listing approval status"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Listing creation timestamp"],
        ],
        col_widths=[1.25, 1.0, 1.9, 1.85],
        caption_num="7.3",
        caption_text="Schema Definition — Table 2: Vehicle (16 Fields)",
        font_size=8.5
    )

    # Table 3: Coupon
    add_styled_table(
        headers=["Field Name", "Data Type", "Constraints / Default", "Description"],
        rows=[
            ["coupon_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique promotional coupon identifier"],
            ["code", "VARCHAR(20)", "UNIQUE, NOT NULL", "Promo code string (e.g., WELCOME20, CAMPUS10)"],
            ["discount_percentage", "DECIMAL(5,2)", "NOT NULL, CHECK (BETWEEN 1 AND 100)", "Percentage discount applied to rental subtotal"],
            ["valid_from", "DATE", "NOT NULL", "Coupon activation start date"],
            ["valid_to", "DATE", "NOT NULL", "Coupon expiration date"],
            ["is_active", "BOOLEAN", "DEFAULT TRUE", "Administrative toggle for coupon validity"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Coupon creation timestamp"],
        ],
        col_widths=[1.3, 1.0, 1.95, 1.75],
        caption_num="7.4",
        caption_text="Schema Definition — Table 3: Coupon (7 Fields)",
        font_size=8.5
    )

    # Table 4: Rental
    add_styled_table(
        headers=["Field Name", "Data Type", "Constraints / Default", "Description"],
        rows=[
            ["rental_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique rental booking identifier"],
            ["student_id", "INT", "NOT NULL, FK -> Student(student_id) CASCADE, INDEX", "Renter booking the vehicle"],
            ["vehicle_id", "INT", "NOT NULL, FK -> Vehicle(vehicle_id) RESTRICT, INDEX", "Reserved vehicle reference"],
            ["start_time", "DATETIME", "NOT NULL", "Scheduled trip start timestamp"],
            ["end_time", "DATETIME", "NOT NULL", "Scheduled trip end timestamp"],
            ["pickup_location", "VARCHAR(100)", "NOT NULL", "Campus pickup hub location"],
            ["return_location", "VARCHAR(100)", "NOT NULL", "Campus drop-off hub location"],
            ["total_hours", "DECIMAL(10,2)", "NOT NULL", "Computed duration via fn_total_hours"],
            ["subtotal", "DECIMAL(10,2)", "NOT NULL", "Base charge via fn_calculate_rental_cost"],
            ["discount", "DECIMAL(10,2)", "DEFAULT 0.00", "Coupon deduction via fn_calculate_discount"],
            ["final_amount", "DECIMAL(10,2)", "NOT NULL", "Net payable amount (subtotal - discount)"],
            ["coupon_id", "INT", "DEFAULT NULL, FK -> Coupon(coupon_id) SET NULL", "Optional applied promotional coupon"],
            ["status", "ENUM", "('Confirmed','Active','Completed','Cancelled'), INDEX", "Current lifecycle state of the rental"],
            ["cancel_reason", "TEXT", "NULLABLE", "User-provided cancellation reason"],
            ["pickup_code", "VARCHAR(10)", "NULLABLE", "OTP handover verification code"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Booking creation timestamp"],
        ],
        col_widths=[1.2, 1.0, 2.0, 1.8],
        caption_num="7.5",
        caption_text="Schema Definition — Table 4: Rental (16 Fields)",
        font_size=8.5
    )

    # Table 5: Payment
    add_styled_table(
        headers=["Field Name", "Data Type", "Constraints / Default", "Description"],
        rows=[
            ["payment_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique payment receipt identifier"],
            ["rental_id", "INT", "UNIQUE, NOT NULL, FK -> Rental(rental_id) CASCADE", "1:1 reference to parent rental"],
            ["amount", "DECIMAL(10,2)", "NOT NULL", "Total paid amount in INR"],
            ["payment_method", "ENUM", "('UPI','Card','Cash'), NOT NULL", "Mode of payment settlement"],
            ["payment_date", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Settlement timestamp"],
            ["payment_status", "ENUM", "('Pending','Completed','Failed','Refunded')", "Current payment status (Default: Pending)"],
            ["transaction_id", "VARCHAR(50)", "UNIQUE, NOT NULL", "Generated reference via fn_generate_txn_id"],
            ["refund_amount", "DECIMAL(10,2)", "DEFAULT 0.00", "Amount refunded on cancellation/dispute"],
            ["refund_date", "DATETIME", "DEFAULT NULL", "Refund settlement timestamp"],
        ],
        col_widths=[1.25, 1.0, 2.0, 1.75],
        caption_num="7.6",
        caption_text="Schema Definition — Table 5: Payment (9 Fields)",
        font_size=8.5
    )

    # Tables 6 to 10 (Review, Maintenance, Insurance, Dispute, AuditLog)
    add_styled_table(
        headers=["Table Name", "Primary Key", "Foreign Keys", "Fields & Constraints Summary"],
        rows=[
            ["Review\n(7 Fields)", "review_id (INT)", "rental_id -> Rental\nreviewer_id -> Student\nvehicle_id -> Vehicle",
             "rating INT CHECK(1..5), comment TEXT, created_at TIMESTAMP. Stores post-ride feedback and drives Vehicle.avg_rating."],
            ["Maintenance\n(9 Fields)", "maintenance_id (INT)", "vehicle_id -> Vehicle\nreported_by -> Student",
             "maintenance_type VARCHAR(50), description TEXT, cost DECIMAL(10,2), maintenance_date DATE, status ENUM('Scheduled','Done'), created_at."],
            ["Insurance\n(8 Fields)", "insurance_id (INT)", "vehicle_id -> Vehicle",
             "provider VARCHAR(100), policy_number VARCHAR(50) UNIQUE, coverage_amount DECIMAL(12,2), valid_from DATE, valid_to DATE, created_at."],
            ["Dispute\n(9 Fields)", "dispute_id (INT)", "rental_id -> Rental\nraised_by -> Student",
             "issue_type VARCHAR(50), description TEXT, status ENUM('Open','InReview','Resolved'), resolution TEXT, created_at, resolved_at DATETIME."],
            ["AuditLog\n(6 Fields)", "log_id (INT)", "student_id -> Student (SET NULL)",
             "action VARCHAR(50) INDEX, details TEXT, ip_address VARCHAR(45) DEFAULT '127.0.0.1', timestamp TIMESTAMP INDEX. Append-only security ledger."],
        ],
        col_widths=[1.05, 1.05, 1.45, 2.45],
        caption_num="7.7",
        caption_text="Schema Definitions — Tables 6 to 10 (Review, Maintenance, Insurance, Dispute, AuditLog)",
        bm_name="tbl_schema_other",
        font_size=8.5
    )

    # -------------------------------------------------------------------------
    # 7.3 SQL JOINS
    # -------------------------------------------------------------------------
    add_h2("7.3 SQL Joins Implemented", bm_name="sec_joins")
    add_body(
        "CampusRide heavily utilizes INNER JOIN, LEFT JOIN, and multi-table chained joins (`sql/queries.sql` Section E) to combine "
        "normalized entities into actionable reports without duplicating data:",
        indent=True
    )
    add_code_block(
        "-- 1. Multi-Table INNER JOIN: Rental + Student + Vehicle + Payment Ledger\n"
        "SELECT r.rental_id, s.full_name, s.email, CONCAT(v.brand, ' ', v.model) AS vehicle,\n"
        "       r.total_hours, r.final_amount, p.payment_method, p.payment_status, p.transaction_id\n"
        "FROM Rental r\n"
        "INNER JOIN Student s ON r.student_id = s.student_id\n"
        "INNER JOIN Vehicle v ON r.vehicle_id = v.vehicle_id\n"
        "INNER JOIN Payment p ON r.rental_id  = p.rental_id\n"
        "ORDER BY r.created_at DESC;\n\n"
        "-- 2. LEFT JOIN: All Vehicles including zero-rental units for Fleet Earnings\n"
        "SELECT v.vehicle_id, CONCAT(v.brand, ' ', v.model) AS vehicle, v.hourly_rate,\n"
        "       COUNT(r.rental_id) AS total_rentals, COALESCE(SUM(r.final_amount), 0) AS total_earned\n"
        "FROM Vehicle v\n"
        "LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id AND r.status = 'Completed'\n"
        "GROUP BY v.vehicle_id ORDER BY total_earned DESC;\n\n"
        "-- 3. Mixed INNER + LEFT JOIN: Rental Details with Optional Coupon Info\n"
        "SELECT s.full_name, r.rental_id, r.subtotal, c.code AS coupon_code, r.discount, r.final_amount\n"
        "FROM Rental r\n"
        "JOIN Student s ON r.student_id = s.student_id\n"
        "LEFT JOIN Coupon c ON r.coupon_id = c.coupon_id;",
        title="SQL Listing 7.1: INNER JOIN, LEFT JOIN, and Multi-Table Join Queries"
    )

    # -------------------------------------------------------------------------
    # 7.4 VIEWS
    # -------------------------------------------------------------------------
    add_h2("7.4 Database Views (6 Pre-Compiled Views)", bm_name="sec_views")
    add_body(
        "Six database views (`sql/views.sql`) encapsulate complex multi-table joins and computed expressions, simplifying API endpoints "
        "while enforcing logical data independence and security filtering:",
        indent=True
    )
    add_styled_table(
        headers=["View Name", "Underlying Tables Joined", "Functional Purpose & Key Expressions"],
        rows=[
            ["vw_available_vehicles", "Vehicle JOIN Student", "Filters `availability_status = 'Available'` and appends owner name/phone for Renter catalog."],
            ["vw_rental_history", "Rental JOIN Student, Vehicle LEFT JOIN Coupon", "Provides complete rental ledger with `CONCAT(brand, ' ', model)`, coupon codes, and OTP pickup codes."],
            ["vw_payment_history", "Payment JOIN Rental, Student, Vehicle", "Joins financial transactions with renter identity and rented vehicle metadata for receipts."],
            ["vw_owner_earnings", "Student LEFT JOIN Vehicle, Rental", "Aggregates `COUNT(rental_id)`, `COALESCE(SUM(final_amount),0)`, and `AVG` per vehicle owner."],
            ["vw_active_maintenance", "Maintenance JOIN Vehicle", "Lists active service issues where `status = 'Scheduled'` along with license plate and cost."],
            ["vw_insurance_status", "Insurance JOIN Vehicle", "Computes `CASE WHEN valid_to >= CURDATE() THEN 'Active' ELSE 'Expired'` and `DATEDIFF` days remaining."],
        ],
        col_widths=[1.45, 1.75, 2.8],
        caption_num="7.8",
        caption_text="Summary of All 6 MySQL Views Defined in views.sql",
        bm_name="tbl_views",
        font_size=8.8
    )

    # -------------------------------------------------------------------------
    # 7.5 NESTED QUERIES
    # -------------------------------------------------------------------------
    add_h2("7.5 Nested Queries (Subqueries)", bm_name="sec_nested")
    add_body(
        "Non-correlated nested queries (`sql/queries.sql` Section F) power multi-step filtering, comparative benchmarking against "
        "derived averages, and leaderboard extraction:",
        indent=True
    )
    add_code_block(
        "-- 1. IN Subquery: Repeat Renters (Students with more than 1 rental)\n"
        "SELECT full_name, email, trust_score FROM Student\n"
        "WHERE student_id IN (SELECT student_id FROM Rental GROUP BY student_id HAVING COUNT(*) > 1);\n\n"
        "-- 2. Multi-Level Nested Subquery: Vehicles earning above overall fleet average\n"
        "SELECT brand, model, vehicle_type, hourly_rate FROM Vehicle\n"
        "WHERE vehicle_id IN (\n"
        "    SELECT vehicle_id FROM Rental WHERE status = 'Completed' GROUP BY vehicle_id\n"
        "    HAVING SUM(final_amount) > (\n"
        "        SELECT AVG(total_vehicle_earnings) FROM (\n"
        "            SELECT vehicle_id, SUM(final_amount) AS total_vehicle_earnings\n"
        "            FROM Rental WHERE status = 'Completed' GROUP BY vehicle_id\n"
        "        ) sub\n"
        "    )\n"
        ");\n\n"
        "-- 3. NOT IN Subquery: Students who have never completed a rental\n"
        "SELECT student_id, full_name, email FROM Student\n"
        "WHERE student_id NOT IN (SELECT DISTINCT student_id FROM Rental WHERE status = 'Completed');\n\n"
        "-- 4. Derived Table Subquery: Top 3 Highest-Spending Students\n"
        "SELECT full_name, email, total_spent FROM (\n"
        "    SELECT s.student_id, s.full_name, s.email, COALESCE(SUM(r.final_amount), 0) AS total_spent\n"
        "    FROM Student s LEFT JOIN Rental r ON s.student_id = r.student_id AND r.status = 'Completed'\n"
        "    GROUP BY s.student_id ORDER BY total_spent DESC LIMIT 3\n"
        ") AS top_spenders;",
        title="SQL Listing 7.2: IN, Multi-Level Nested, NOT IN, and Derived Table Subqueries"
    )

    # -------------------------------------------------------------------------
    # 7.6 CORRELATED SUBQUERIES
    # -------------------------------------------------------------------------
    add_h2("7.6 Correlated Subqueries", bm_name="sec_corr")
    add_body(
        "Correlated subqueries reference columns from the outer query row-by-row to evaluate per-student maxima and real-time "
        "active reservation exclusion (`sql/queries.sql` Section F4–F5):",
        indent=True
    )
    add_code_block(
        "-- 1. Correlated Equality Subquery: Highest-value rental per individual student\n"
        "SELECT r.rental_id, s.full_name, r.final_amount\n"
        "FROM Rental r\n"
        "JOIN Student s ON r.student_id = s.student_id\n"
        "WHERE r.final_amount = (\n"
        "    SELECT MAX(r2.final_amount) FROM Rental r2\n"
        "    WHERE r2.student_id = r.student_id\n"
        ");\n\n"
        "-- 2. Correlated NOT EXISTS Subquery: Vehicles with zero Confirmed/Active bookings\n"
        "SELECT v.vehicle_id, v.brand, v.model\n"
        "FROM Vehicle v\n"
        "WHERE NOT EXISTS (\n"
        "    SELECT 1 FROM Rental r\n"
        "    WHERE r.vehicle_id = v.vehicle_id\n"
        "      AND r.status IN ('Confirmed', 'Active')\n"
        ");",
        title="SQL Listing 7.3: Correlated Subqueries Using Outer Row References & NOT EXISTS"
    )

    # -------------------------------------------------------------------------
    # 7.7 AGGREGATE FUNCTIONS
    # -------------------------------------------------------------------------
    add_h2("7.7 Aggregate Functions and Analytical Grouping", bm_name="sec_agg")
    add_body(
        "Aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `COALESCE`, `ROUND`) combined with `GROUP BY`, `HAVING`, and "
        "temporal functions (`DATE_FORMAT`, `DAYNAME`, `HOUR`) drive the Admin Revenue Report and demand analytics (`sql/queries.sql` Section G):",
        indent=True
    )
    add_code_block(
        "-- 1. Revenue Breakdown by Vehicle Type (Powers Admin Revenue Dashboard)\n"
        "SELECT v.vehicle_type, COUNT(r.rental_id) AS rentals, SUM(r.final_amount) AS revenue,\n"
        "       AVG(r.total_hours) AS avg_hours, AVG(v.avg_rating) AS avg_vehicle_rating\n"
        "FROM Rental r JOIN Vehicle v ON r.vehicle_id = v.vehicle_id\n"
        "WHERE r.status = 'Completed' GROUP BY v.vehicle_type ORDER BY revenue DESC;\n\n"
        "-- 2. Payment Method Share Percentage (UPI vs Card vs Cash)\n"
        "SELECT payment_method, COUNT(*) AS count, SUM(amount) AS total_amount,\n"
        "       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Payment WHERE payment_status='Completed'), 2) AS pct\n"
        "FROM Payment WHERE payment_status = 'Completed' GROUP BY payment_method;\n\n"
        "-- 3. Review Rating Extremes per Vehicle (COUNT, AVG, MIN, MAX)\n"
        "SELECT v.vehicle_id, CONCAT(v.brand, ' ', v.model) AS vehicle, COUNT(rv.review_id) AS reviews,\n"
        "       AVG(rv.rating) AS avg_rating, MIN(rv.rating) AS min_rating, MAX(rv.rating) AS max_rating\n"
        "FROM Vehicle v LEFT JOIN Review rv ON v.vehicle_id = rv.vehicle_id GROUP BY v.vehicle_id;",
        title="SQL Listing 7.4: Aggregate Functions & Analytical Grouping Queries"
    )

    # -------------------------------------------------------------------------
    # 7.8 USER-DEFINED FUNCTIONS
    # -------------------------------------------------------------------------
    add_h2("7.8 User-Defined Functions (7 Functions)", bm_name="sec_udfs")
    add_styled_table(
        headers=["Function Name", "Parameters & Return Type", "Logic Executed Inside MySQL"],
        rows=[
            ["fn_total_hours", "(p_start DATETIME, p_end DATETIME) -> DECIMAL(10,2)", "Computes exact fractional hours via `TIMESTAMPDIFF(MINUTE, p_start, p_end) / 60.0`."],
            ["fn_calculate_rental_cost", "(p_vehicle_id INT, p_hours DECIMAL) -> DECIMAL(10,2)", "Fetches `Vehicle.hourly_rate` and returns `ROUND(v_rate * p_hours, 2)`."],
            ["fn_calculate_discount", "(p_subtotal DECIMAL, p_coupon_code VARCHAR) -> DECIMAL", "Validates active coupon within `[valid_from, valid_to]` and returns discount amount."],
            ["fn_hash_password", "(p_password VARCHAR(255)) -> VARCHAR(255)", "Deterministic cryptographic hashing via `SHA2(CONCAT('vitcampus', p_password), 256)`."],
            ["fn_is_vehicle_available", "(p_vehicle_id INT) -> BOOLEAN", "Returns TRUE if `Vehicle.availability_status = 'Available'`, else FALSE."],
            ["fn_generate_txn_id", "() -> VARCHAR(50)", "Generates unique receipt reference: `CONCAT('TXN', UNIX_TIMESTAMP(), LPAD(FLOOR(RAND()*99999),5,'0'))`."],
            ["fn_get_rental_count", "(p_student_id INT) -> INT", "Returns count of `'Completed'` rentals for a given student."],
        ],
        col_widths=[1.45, 2.05, 2.5],
        caption_num="7.9",
        caption_text="All 7 User-Defined Functions in procedures.sql",
        font_size=8.6
    )

    # -------------------------------------------------------------------------
    # 7.9 STORED PROCEDURES
    # -------------------------------------------------------------------------
    add_h2("7.9 Stored Procedures (10 ACID Stored Procedures)", bm_name="sec_procs")
    add_body(
        "Ten stored procedures (`sql/procedures.sql`) execute every state-changing workflow and administrative report directly inside "
        "MySQL using `START TRANSACTION`, `COMMIT`, and `DECLARE EXIT HANDLER FOR SQLEXCEPTION` rollback protection:",
        indent=True
    )
    add_styled_table(
        headers=["Procedure Name", "Key Parameters (IN / OUT)", "Core Transactional Behavior"],
        rows=[
            ["sp_register", "IN name, email, phone, dept, hostel, pwd, roll; OUT status", "Checks duplicate email, hashes password via `fn_hash_password`, commits new Student."],
            ["sp_login", "IN email, password; OUT status", "Verifies hash; tracks `failed_attempts`; locks account for 15 min after 5 failures; logs `LOGIN`."],
            ["sp_create_rental", "IN student_id, vehicle_id, times, locs, coupon; OUT status", "Validates availability, computes hours/cost/discount via UDFs, commits Rental atomically."],
            ["sp_complete_rental", "IN rental_id; OUT status", "Verifies rental is not already Completed/Cancelled; updates status to `'Completed'`."],
            ["sp_cancel_rental", "IN rental_id, student_id, reason; OUT status", "Verifies renter ownership (`FORBIDDEN` check) and sets status to `'Cancelled'` with reason."],
            ["sp_process_payment", "IN rental_id, payment_method; OUT txn_id, status", "Prevents double-payment, generates `TXN` ID, inserts Payment, activates Confirmed Rental."],
            ["sp_add_vehicle", "IN owner_id, type, brand, model, seats, fuel, rate, plate...; OUT status", "Inserts new vehicle listing with exception handler for `ERROR_DUPLICATE_PLATE`."],
            ["sp_add_maintenance", "IN vehicle_id, type, desc, cost, date; OUT status", "Inserts `'Scheduled'` maintenance record (which triggers vehicle status -> `'Maintenance'`)."],
            ["sp_vehicle_utilization_report", "(None) -> Result Set", "Returns fleet-wide rental counts, rented hours, earnings, and ratings ordered by revenue."],
            ["sp_student_spending_report", "IN student_id -> Result Set", "Returns individual student rental count, total hours, total spent, and average rental cost."],
        ],
        col_widths=[1.45, 2.0, 2.55],
        caption_num="7.10",
        caption_text="All 10 Stored Procedures in procedures.sql",
        bm_name="tbl_procs",
        font_size=8.5
    )

    # -------------------------------------------------------------------------
    # 7.10 DATABASE TRIGGERS
    # -------------------------------------------------------------------------
    add_h2("7.10 Database Triggers (7 Automated Triggers)", bm_name="sec_trigs")
    add_body(
        "Seven row-level database triggers (`sql/triggers.sql`) guarantee autonomous state synchronization and tamper-proof security "
        "auditing regardless of which client or script modifies the database:",
        indent=True
    )
    add_styled_table(
        headers=["Trigger Name", "Event & Timing", "Target Table", "Automated Database Action"],
        rows=[
            ["trg_before_rental_insert", "BEFORE INSERT", "Rental", "Double-booking guard: queries `Vehicle.availability_status`; raises `SIGNAL SQLSTATE '45000'` if not `'Available'`."],
            ["trg_after_rental_insert", "AFTER INSERT", "Rental", "Flips `Vehicle.availability_status` to `'Rented'` and inserts `RENTAL_CREATED` entry into `AuditLog`."],
            ["trg_after_rental_update", "AFTER UPDATE", "Rental", "When status becomes `'Completed'` or `'Cancelled'`, restores vehicle to `'Available'` and logs status change."],
            ["trg_after_payment_insert", "AFTER INSERT", "Payment", "Appends `PAYMENT_COMPLETED` entry with `TxnID`, amount, and payment method into `AuditLog`."],
            ["trg_after_student_insert", "AFTER INSERT", "Student", "Appends `REGISTER` event with user email and assigned role into `AuditLog`."],
            ["trg_after_maintenance_insert", "AFTER INSERT", "Maintenance", "If `'Scheduled'`, switches vehicle status to `'Maintenance'` and logs `MAINTENANCE_SCHEDULED`."],
            ["trg_after_maintenance_done", "AFTER UPDATE", "Maintenance", "When status transitions to `'Done'`, frees vehicle back to `'Available'` and logs `MAINTENANCE_DONE`."],
        ],
        col_widths=[1.55, 1.0, 0.85, 2.6],
        caption_num="7.11",
        caption_text="All 7 Automated Triggers in triggers.sql",
        bm_name="tbl_trigs",
        font_size=8.5
    )

    # -------------------------------------------------------------------------
    # 7.11 AI/ML & GEOFENCING
    # -------------------------------------------------------------------------
    add_h2("7.11 AI/ML Intelligence & Perimeter Geofencing Implementation", bm_name="sec_aiml")
    add_body(
        "Beyond the SQL core, `backend/ml/recommendation.py`, `backend/routes/ml.py`, and `backend/routes/security.py` provide five "
        "real-time intelligent services directly connected to live MySQL telemetry:",
        indent=True
    )
    add_bullet("1. Vehicle Recommendation Engine (`/api/ml/recommendations/{student_id}`): ",
               "Uses Scikit-learn's `TfidfVectorizer` and `cosine_similarity` over vehicle type, brand, model, and student preference profiles to return the top 3 personalized vehicle matches with percentage match scores.")
    add_bullet("2. Time-Series Demand Predictor & Hotspot Rebalancing (`/api/ml/demand-prediction` & `/locations`): ",
               "Forecasts next-day booking volumes across Scooter (50%), Bike (33.3%), and Car (16.7%) categories and predicts campus demand shares across Main Gate (48%), Hostel A (28%), Library (16%), and Sports Ground (14%).")
    add_bullet("3. Unsupervised Fraud & Anomaly Detection (`/api/ml/anomaly-detect` & `/api/security/fraud/analysis`): ",
               "Trains a Scikit-learn `IsolationForest` (`contamination=0.05`) on historical payment distributions to isolate abnormal amounts (e.g., flagging Rs. 8,500 as HIGH risk while classifying Rs. 250 as LOW risk) and computes a Student Risk & Trust Assessment Matrix monitoring 24-hour velocity and cancellation rates.")
    add_bullet("4. Predictive Fleet Maintenance & Dynamic Pricing (`/api/ml/maintenance/fleet-health` & `/pricing/suggest`): ",
               "Queries live SQL `SUM(total_hours)` and `COUNT(*)` from `Rental` plus `Vehicle.avg_rating` to compute vehicle Health Scores (e.g., 90.2% fleet average), breakdown risk percentages, and optimal supply-demand hourly price ranges.")
    add_bullet("5. Haversine Campus Perimeter Geofencing (`/api/security/geofence/*`): ",
               "Monitors GPS coordinates against the institutional center `(13.0020° N, 80.2350° E)` with an enforced `2.5 km` boundary radius. Any out-of-bounds telemetry (e.g., `13.0650, 80.2850` at `~8.5 km`) generates a live `SECURITY ALERT` with one-click administrative resolution.")

    # =========================================================================
    # SECTION 8: RESULTS & OUTPUT — KEY APPLICATION SCREENSHOTS (Format Item 8)
    # =========================================================================
    add_section_title("8", "RESULTS & OUTPUT", bm_name="sec_results", page_break_before=True)

    add_body(
        "The complete CampusRide application was deployed locally on MySQL 8.0 and FastAPI (`http://localhost:15501`) and evaluated "
        "across all three role-based portals. This section presents the 9 key live screenshots showcasing the core DBMS workflows, "
        "trigger-driven audit trails, SQL revenue analytics, AI/ML predictive modules, and perimeter geofencing.",
        indent=True
    )

    # --- 8.1 RENTER PORTAL (2 Key Screenshots) ---
    add_h2("8.1 Renter Portal Outputs (Student: Rohit Sharma)", bm_name="sec_res_renter")

    renter_shots = [
        ("Screenshot 2026-11-18 172149.png", "8.1",
         "Renter Dashboard Overview & AI Smart Recommendations",
         "Displays live renter KPIs for Rohit Sharma (6 Total Rentals, Rs. 610 Total Spent, 5 Completed, 1 Active), the personalized "
         "AI Smart Recommendations panel powered by TF-IDF Cosine Similarity (recommending Maruti Swift at 65% match, Honda Shine at 15%, "
         "and Hero Splendor at 15%), and the Available Vehicles feed queried from `vw_available_vehicles`."),
        ("Screenshot 2026-11-18 172200.png", "8.2",
         "Renter My Rental History & Lifecycle Actions",
         "Populated from `vw_rental_history`, displaying active and completed trips (Hero Splendor Active/Paid with one-click End button "
         "invoking `sp_complete_rental`, plus Completed trips for Yamaha FZ-S and Honda Dio with Review and Receipt actions)."),
    ]
    for fname, fnum, ftitle, fdesc in renter_shots:
        embed_image(os.path.join(report_imgs_dir, fname), fnum, ftitle, bm_name=f"fig_{fnum.replace('.','_')}", max_width=5.85, max_height=3.0, description=fdesc)

    # --- 8.2 VEHICLE OWNER PORTAL (2 Key Screenshots) ---
    add_h2("8.2 Vehicle Owner Portal Outputs (Owner: Neha Joshi)", bm_name="sec_res_owner")

    owner_shots = [
        ("Screenshot 2026-11-18 172224.png", "8.3",
         "Owner Dashboard Overview — Fleet Status & Recent Bookings",
         "Shows the Owner Portal summary for Neha Joshi (1 Vehicle Listed, Rs. 90 Total Earnings, 1 Active Rental, 1 Completed), "
         "displaying her listed Hero Splendor (Rs. 45/hr, automatically marked 'Rented' by `trg_after_rental_insert`) alongside Recent Bookings."),
        ("Screenshot 2026-11-18 172300.png", "8.4",
         "Owner Predictive Fleet Maintenance Health & Campus Demand Forecast",
         "Displays real-time ML degradation diagnostics (90% Fleet Average Health, 0 High Risk Vehicles; Hero Splendor MH02CD5681 at "
         "89.6% health / Low 10.4% breakdown risk) and the Campus Fleet Demand Forecast (Scooter: 15 bookings / 50% High Demand, Bike: "
         "10 bookings / 33.3% Medium Demand, Car: 5 bookings / 16.7% Low Demand)."),
    ]
    for fname, fnum, ftitle, fdesc in owner_shots:
        embed_image(os.path.join(report_imgs_dir, fname), fnum, ftitle, bm_name=f"fig_{fnum.replace('.','_')}", max_width=5.85, max_height=3.0, description=fdesc)

    # --- 8.3 ADMIN PANEL & SECURITY/AIML GOVERNANCE (5 Key Screenshots) ---
    add_h2("8.3 System Administration, Security & AIML Console Outputs", bm_name="sec_res_admin")

    admin_shots = [
        ("Screenshot 2026-11-18 172047.png", "8.5",
         "Admin Panel — System Statistics Dashboard",
         "Real-time institutional KPI summary aggregated from MySQL: 7 Total Students, 8 Total Vehicles, 9 Total Rentals, Rs. 2,210 Total "
         "Revenue, 1 Active Rental, 7 Available Vehicles, 100% Verified Members, and 13% current fleet occupancy rate."),
        ("Screenshot 2026-11-18 172113.png", "8.6",
         "Admin Panel — Revenue Report by Vehicle Type (SQL Aggregate Grouping)",
         "Visualizes SQL `GROUP BY v.vehicle_type` aggregate output: Rs. 2,210 Total Revenue with Rs. 0 Refunds, broken down into Bike "
         "(2 rentals, Rs. 860), Car (1 rental, Rs. 640), and Scooter (6 rentals, Rs. 710)."),
        ("Screenshot 2026-11-18 172118.png", "8.7",
         "Admin Panel — Immutable Audit Trail (Trigger-Generated Logs)",
         "Displays sequential, append-only entries (#60 to #65) automatically written by MySQL triggers (`trg_after_rental_insert`, "
         "`trg_after_rental_update`, `trg_after_payment_insert`) capturing timestamps, actions, transaction IDs, and client IP (127.0.0.1)."),
        ("Screenshot 2026-11-18 172130.png", "8.8",
         "Admin Panel — Campus Geofencing & Perimeter Breach Monitor",
         "Demonstrates live Haversine perimeter enforcement (Campus Center Lat 13.0020, Lng 80.2350; Radius ~2.5 km) capturing Active "
         "Breach Alert #1 for Royal Enfield Classic 350 (MH02AB1236, renter Prathamesh Patil) detected at (13.0650, 80.2850), ~8.5 km "
         "outside campus, with a Resolve workflow and live breach simulator."),
        ("Screenshot 2026-11-18 172140.png", "8.9",
         "Admin Panel — AIML Core & Campus Demand Hotspots",
         "Confirms active runtime status of all four ML pipelines—Smart Recommender (Cosine Similarity), Demand Predictor (Time-Series), "
         "Predictive Health (Heuristic Wear), and Isolation Forest—alongside live campus hotspot demand shares (Main Gate 48% Very High, "
         "Hostel A 28% Medium, Library 16% Low, Sports Ground 14% Low)."),
    ]
    for fname, fnum, ftitle, fdesc in admin_shots:
        embed_image(os.path.join(report_imgs_dir, fname), fnum, ftitle, bm_name=f"fig_{fnum.replace('.','_')}", max_width=5.85, max_height=3.0, description=fdesc)

    # =========================================================================
    # SECTION 9: CONCLUSION AND FUTURE SCOPE (Format Item 9)
    # =========================================================================
    add_section_title("9", "CONCLUSION AND FUTURE SCOPE", bm_name="sec_concl", page_break_before=True)

    add_h2("9.1 Conclusion")
    add_body(
        "CampusRide successfully demonstrates how rigorous relational database engineering and applied machine learning can solve "
        "real-world institutional micro-mobility challenges. By placing 100% of transactional business rules inside MySQL 8.0—spanning "
        "10 normalized 3NF tables, 6 views, 7 user-defined functions, 10 ACID stored procedures, and 7 automated triggers—the platform "
        "eliminates double-booking race conditions, guarantees atomic payment settlement, enforces brute-force login protection, and "
        "maintains a tamper-evident security audit trail without ORM overhead.",
        indent=True
    )
    add_body(
        "Coupled with a Python FastAPI gateway and Scikit-learn intelligence modules, CampusRide elevates a traditional rental CRUD "
        "system into a proactive smart-campus platform. Live outputs confirm personalized TF-IDF vehicle recommendations, accurate "
        "Isolation Forest anomaly flagging, fleet-wide predictive maintenance monitoring (90.2% average health), dynamic pricing "
        "optimization, and real-time Haversine geofence breach alerting. Ultimately, the system reduces student commuting friction, "
        "monetizes idle campus vehicles, and provides transparent administrative oversight.",
        indent=True
    )

    add_h2("9.2 Future Scope")
    add_bullet("1. IoT Smart Lock & Keyless QR Handover: ",
               "Integrate ESP32 microcontrollers with BLE/4G solenoid locks on listed two-wheelers to replace manual key exchange with automated smartphone QR code unlocking verified against `Rental.pickup_code`.")
    add_bullet("2. Electric Vehicle (EV) Battery Telemetry Integration: ",
               "Connect Battery Management System (BMS) APIs to track State-of-Charge (SoC) in real time and prevent reservations when remaining range is insufficient for the requested rental duration.")
    add_bullet("3. Native Mobile App & Real-Time GPS Hardware Stream: ",
               "Deploy Flutter/React Native mobile clients streaming live background GPS coordinates into the Haversine geofence engine and delivering instant push notifications for OTPs and breach alerts.")
    add_bullet("4. Live Payment Gateway & Automated Escrow Payouts: ",
               "Integrate Razorpay/UPI AutoPay webhooks with `sp_process_payment` for automated split settlements directly to vehicle owners' bank accounts upon trip completion.")
    add_bullet("5. Intra-Campus Peer Carpooling & Route Matching: ",
               "Extend the recommendation algorithm to support multi-passenger ride splitting along high-demand routes (e.g., Hostel Complex to Main Gate during peak lecture hours).")

    # =========================================================================
    # SECTION 10: REFERENCES (Format Item 10)
    # =========================================================================
    add_section_title("10", "REFERENCES", bm_name="sec_refs", page_break_before=True)

    add_h2("10.1 Books & Research Publications")
    books_refs = [
        "[1] A. Silberschatz, H. F. Korth, and S. Sudarshan, Database System Concepts, 7th ed. New York, NY, USA: McGraw-Hill Education, 2019.",
        "[2] R. Elmasri and S. B. Navathe, Fundamentals of Database Systems, 7th ed. Hoboken, NJ, USA: Pearson Education, 2016.",
        "[3] E. F. Codd, \"A Relational Model of Data for Large Shared Data Banks,\" Communications of the ACM, vol. 13, no. 6, pp. 377–387, Jun. 1970.",
        "[4] F. T. Liu, K. M. Ting, and Z.-H. Zhou, \"Isolation Forest,\" in Proc. 8th IEEE International Conference on Data Mining (ICDM), Pisa, Italy, 2008, pp. 413–422.",
        "[5] G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Information Processing & Management, vol. 24, no. 5, pp. 513–523, 1988.",
        "[6] R. W. Sinnott, \"Virtues of the Haversine,\" Sky and Telescope, vol. 68, no. 2, p. 159, 1984.",
        "[7] F. Pedregosa et al., \"Scikit-learn: Machine Learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
    ]
    for ref in books_refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.font.color.rgb = DARK

    add_h2("10.2 Official Documentation & Websites")
    web_refs = [
        "[8] Oracle Corporation, MySQL 8.0 Reference Manual — Stored Objects, Triggers, Views, and InnoDB Transactions. Available: https://dev.mysql.com/doc/refman/8.0/en/",
        "[9] S. Ramirez, FastAPI Modern High-Performance Web Framework Documentation. Available: https://fastapi.tiangolo.com/",
        "[10] SQLAlchemy Authors, SQLAlchemy 2.0 Core & Raw SQL Execution Documentation. Available: https://docs.sqlalchemy.org/en/20/",
        "[11] Scikit-learn Developers, IsolationForest & TfidfVectorizer API Reference. Available: https://scikit-learn.org/stable/documentation.html",
        "[12] MDN Web Docs, HTML5, CSS3, and Fetch API Web Standards. Available: https://developer.mozilla.org/",
    ]
    for ref in web_refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.font.color.rgb = DARK

    # =========================================================================
    # SECTION 11: APPENDIX — EXTRA DIAGRAMS & KEY SOURCE CODE (Format Item 11)
    # =========================================================================
    add_section_title("11", "APPENDIX", bm_name="sec_app", page_break_before=True)

    add_h2("Appendix A: Extra Architecture & Operational Diagrams")

    arch_path = os.path.join(scratch_dir, "architecture.png")
    if os.path.exists(arch_path):
        embed_image(
            arch_path,
            fig_num="A.1",
            fig_title="Three-Tier System Architecture of CampusRide (Presentation, FastAPI + ML Gateway, MySQL 8.0 Core)",
            bm_name="fig_arch",
            max_width=5.9,
            max_height=4.5
        )

    flow_path = os.path.join(scratch_dir, "flowchart.png")
    if os.path.exists(flow_path):
        doc.add_page_break()
        embed_image(
            flow_path,
            fig_num="A.2",
            fig_title="End-to-End Operational Lifecycle and Execution Flowchart of CampusRide",
            bm_name="fig_flow",
            max_width=5.4,
            max_height=7.0
        )

    doc.add_page_break()
    add_h2("Appendix B: Core SQL & Backend Source Code Snippets")

    add_code_block(
        "-- Double-Booking Prevention Guard (BEFORE INSERT Trigger)\n"
        "CREATE TRIGGER trg_before_rental_insert\n"
        "BEFORE INSERT ON Rental FOR EACH ROW\n"
        "BEGIN\n"
        "    DECLARE v_status VARCHAR(30);\n"
        "    SELECT availability_status INTO v_status FROM Vehicle WHERE vehicle_id = NEW.vehicle_id;\n"
        "    IF v_status != 'Available' THEN\n"
        "        SIGNAL SQLSTATE '45000'\n"
        "        SET MESSAGE_TEXT = 'Vehicle is not available for booking. Please choose another vehicle.';\n"
        "    END IF;\n"
        "END //\n\n"
        "-- Automatic Vehicle Status Flip & Audit Trail (AFTER INSERT Trigger)\n"
        "CREATE TRIGGER trg_after_rental_insert\n"
        "AFTER INSERT ON Rental FOR EACH ROW\n"
        "BEGIN\n"
        "    UPDATE Vehicle SET availability_status = 'Rented' WHERE vehicle_id = NEW.vehicle_id;\n"
        "    INSERT INTO AuditLog (student_id, action, details)\n"
        "    VALUES (NEW.student_id, 'RENTAL_CREATED',\n"
        "            CONCAT('Rental #', NEW.rental_id, ' created for vehicle #', NEW.vehicle_id,\n"
        "                   ' | Amount: Rs.', NEW.final_amount));\n"
        "END //",
        title="Code Listing B.1: MySQL Double-Booking Prevention & Audit Triggers (sql/triggers.sql)"
    )

    add_code_block(
        "-- Atomic Rental Creation Stored Procedure (sql/procedures.sql)\n"
        "CREATE PROCEDURE sp_create_rental(\n"
        "    IN p_student_id INT, IN p_vehicle_id INT,\n"
        "    IN p_start_time DATETIME, IN p_end_time DATETIME,\n"
        "    IN p_pickup_location VARCHAR(100), IN p_return_location VARCHAR(100),\n"
        "    IN p_coupon_code VARCHAR(20), OUT p_status VARCHAR(20)\n"
        ")\n"
        "BEGIN\n"
        "    DECLARE v_hours DECIMAL(10,2); DECLARE v_subtotal DECIMAL(10,2);\n"
        "    DECLARE v_discount DECIMAL(10,2); DECLARE v_final DECIMAL(10,2);\n"
        "    DECLARE v_coupon_id INT DEFAULT NULL;\n"
        "    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; SET p_status = 'ERROR'; END;\n"
        "    IF NOT fn_is_vehicle_available(p_vehicle_id) THEN\n"
        "        SET p_status = 'NOT_AVAILABLE';\n"
        "    ELSE\n"
        "        START TRANSACTION;\n"
        "        SET v_hours    = fn_total_hours(p_start_time, p_end_time);\n"
        "        SET v_subtotal = fn_calculate_rental_cost(p_vehicle_id, v_hours);\n"
        "        SET v_discount = fn_calculate_discount(v_subtotal, p_coupon_code);\n"
        "        SET v_final    = v_subtotal - v_discount;\n"
        "        IF p_coupon_code IS NOT NULL AND p_coupon_code != '' THEN\n"
        "            SELECT coupon_id INTO v_coupon_id FROM Coupon WHERE code = p_coupon_code LIMIT 1;\n"
        "        END IF;\n"
        "        INSERT INTO Rental (student_id, vehicle_id, start_time, end_time, pickup_location,\n"
        "            return_location, total_hours, subtotal, discount, final_amount, coupon_id, status)\n"
        "        VALUES (p_student_id, p_vehicle_id, p_start_time, p_end_time, p_pickup_location,\n"
        "            p_return_location, v_hours, v_subtotal, v_discount, v_final, v_coupon_id, 'Confirmed');\n"
        "        COMMIT;\n"
        "        SET p_status = 'OK';\n"
        "        SELECT * FROM Rental WHERE rental_id = LAST_INSERT_ID();\n"
        "    END IF;\n"
        "END //",
        title="Code Listing B.2: Atomic Booking Procedure with Transaction Rollback (sql/procedures.sql)"
    )

    add_code_block(
        "# FastAPI SQL-Driven Login Dispatch (backend/routes/auth.py)\n"
        "@router.post('/login')\n"
        "def login(email: str = Form(None), password: str = Form(...), db: Session = Depends(get_db)):\n"
        "    db.execute(text(\"SET @p_status = ''\"))\n"
        "    db.execute(text('CALL sp_login(:email, :password, @p_status)'),\n"
        "               {'email': email.strip().lower(), 'password': password})\n"
        "    sp_status = db.execute(text('SELECT @p_status AS status')).fetchone()[0]\n"
        "    if sp_status == 'LOCKED':\n"
        "        raise HTTPException(status_code=403, detail='Account locked for 15 minutes.')\n"
        "    if sp_status != 'OK':\n"
        "        raise HTTPException(status_code=401, detail='Authentication failed')\n"
        "    # Issue JWT bearer token upon MySQL verification",
        title="Code Listing B.3: FastAPI Stateless Stored-Procedure Auth Gateway (backend/routes/auth.py)"
    )

    # =========================================================================
    # SAVE OUTPUT
    # =========================================================================
    out_report_folder = r"c:\Users\HP\OneDrive\Documents\cp\report\CampusRide_DBMS_Project_Report.docx"
    out_report_alt = r"c:\Users\HP\OneDrive\Documents\cp\report\CampusRide_DBMS_Project_Report_Final.docx"
    out_root_copy = r"c:\Users\HP\OneDrive\Documents\cp\CampusRide_DBMS_Project_Report.docx"

    try:
        doc.save(out_report_folder)
        print(f"Saved primary report -> {out_report_folder}")
    except PermissionError:
        doc.save(out_report_alt)
        print(f"Original is open in Word; saved updated report -> {out_report_alt}")

    try:
        doc.save(out_root_copy)
        print(f"Saved backup copy   -> {out_root_copy}")
    except PermissionError:
        print(f"Skipped backup copy (file open): {out_root_copy}")


if __name__ == "__main__":
    build_dbms_report()

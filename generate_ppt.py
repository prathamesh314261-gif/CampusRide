import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


# =============================================================================
# COLOR PALETTE & CONSTANTS (16:9 Widescreen)
# =============================================================================
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

NAVY       = RGBColor(0x0F, 0x17, 0x2A)   # Deep Slate Navy
NAVY_MID   = RGBColor(0x1E, 0x29, 0x3B)   # Medium Navy Card
BLUE_ACC   = RGBColor(0x25, 0x63, 0xEB)   # Royal Blue
CYAN_ACC   = RGBColor(0x06, 0xB6, 0xD4)   # Electric Cyan
TEAL_ACC   = RGBColor(0x0D, 0x94, 0x88)   # Teal Green
AMBER_ACC  = RGBColor(0xD9, 0x77, 0x06)   # Warm Amber
BG_LIGHT   = RGBColor(0xF8, 0xFA, 0xFC)   # Crisp Off-White
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BORDER     = RGBColor(0xCB, 0xD5, 0xE1)   # Light Slate Border
TEXT_DARK  = RGBColor(0x1E, 0x29, 0x3B)
TEXT_MUTED = RGBColor(0x64, 0x74, 0x8B)
CODE_BG    = RGBColor(0xF1, 0xF5, 0xF9)

FONT_MAIN = "Segoe UI"
FONT_CODE = "Consolas"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def set_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, line_color=None, line_pt=1.0, rounded=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, left, top, width, height)
    if rounded:
        shape.adjustments[0] = 0.04
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_pt)
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height, text="", font_size=14, bold=False, italic=False,
                color=TEXT_DARK, align=PP_ALIGN.LEFT, font_name=FONT_MAIN, valign=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    if text:
        p = tf.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = text
        r.font.name = font_name
        r.font.size = Pt(font_size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return tb


def add_bullets(slide, left, top, width, height, items, font_size=13, color=TEXT_DARK,
                lead_color=NAVY, space_after=6, bullet_char="▸ "):
    """items: list of (bold_lead, body_text) tuples"""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    for idx, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = 1.18

        rb = p.add_run()
        rb.text = bullet_char
        rb.font.name = FONT_MAIN
        rb.font.size = Pt(font_size)
        rb.font.bold = True
        rb.font.color.rgb = CYAN_ACC

        if lead:
            r1 = p.add_run()
            r1.text = lead
            r1.font.name = FONT_MAIN
            r1.font.size = Pt(font_size)
            r1.font.bold = True
            r1.font.color.rgb = lead_color

        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_MAIN
        r2.font.size = Pt(font_size)
        r2.font.color.rgb = color
    return tb


def add_header_and_footer(slide, title, subtitle_tag, slide_num, total_slides=10):
    set_bg(slide, BG_LIGHT)
    # Top navy banner
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.92), NAVY)
    # Thin cyan accent line under header
    add_rect(slide, Inches(0), Inches(0.92), SLIDE_W, Inches(0.05), CYAN_ACC)

    # Slide title
    add_textbox(slide, Inches(0.5), Inches(0.14), Inches(9.5), Inches(0.65),
                title, font_size=24, bold=True, color=WHITE, valign=MSO_ANCHOR.MIDDLE)

    # Right category pill
    pill = add_rect(slide, Inches(10.35), Inches(0.24), Inches(2.5), Inches(0.42), NAVY_MID,
                    line_color=CYAN_ACC, line_pt=1.0, rounded=True)
    p = pill.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = subtitle_tag.upper()
    r.font.name = FONT_MAIN
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = CYAN_ACC

    # Bottom footer rule & text
    add_rect(slide, Inches(0.5), Inches(7.05), Inches(12.333), Inches(0.015), BORDER)
    add_textbox(slide, Inches(0.5), Inches(7.1), Inches(9.0), Inches(0.32),
                "CampusRide — Smart Peer-to-Peer Campus Vehicle Rental System  |  DBMS Course Project  |  VIT Pune",
                font_size=9.5, italic=True, color=TEXT_MUTED)
    add_textbox(slide, Inches(11.3), Inches(7.1), Inches(1.533), Inches(0.32),
                f"{slide_num} / {total_slides}", font_size=10, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)


def add_card(slide, left, top, width, height, title=None, accent=BLUE_ACC, bg=WHITE):
    add_rect(slide, left, top, width, height, bg, line_color=BORDER, line_pt=1.0, rounded=True)
    # Top accent bar inside card
    add_rect(slide, left + Inches(0.02), top + Inches(0.02), width - Inches(0.04), Inches(0.07), accent)
    if title:
        add_textbox(slide, left + Inches(0.18), top + Inches(0.16), width - Inches(0.36), Inches(0.4),
                    title, font_size=15, bold=True, color=NAVY)


def add_fitted_image(slide, img_path, left, top, max_w, max_h, caption=None):
    with Image.open(img_path) as im:
        w_px, h_px = im.size
    aspect = w_px / h_px
    avail_h = max_h - (Inches(0.32) if caption else Inches(0))
    w = max_w
    h = w / aspect
    if h > avail_h:
        h = avail_h
        w = h * aspect
    x = left + (max_w - w) / 2
    y = top + (avail_h - h) / 2
    # Subtle frame behind image
    add_rect(slide, x - Inches(0.04), y - Inches(0.04), w + Inches(0.08), h + Inches(0.08),
             WHITE, line_color=BORDER, line_pt=1.0)
    slide.shapes.add_picture(img_path, x, y, width=w, height=h)
    if caption:
        add_textbox(slide, left, y + h + Inches(0.06), max_w, Inches(0.3),
                    caption, font_size=10.5, italic=True, bold=True, color=NAVY, align=PP_ALIGN.CENTER)


def add_notes(slide, text):
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text.strip()


# =============================================================================
# BUILD 10-SLIDE DECK
# =============================================================================

def build_ppt():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]

    scratch_dir = r"C:\Users\HP\.gemini\antigravity\brain\f3255e1c-82ec-45a0-9e0a-4bb1cdf5a518\scratch"
    imgs_dir = os.path.join(scratch_dir, "report_imgs")
    logo_path = os.path.join(scratch_dir, "vit_logo.jpg")
    arch_path = os.path.join(scratch_dir, "architecture.png")
    er_path = os.path.join(imgs_dir, "Screenshot 2026-10-05 145038.png")

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, NAVY)
    # Decorative left vertical accent bar & top cyan stripe
    add_rect(s1, Inches(0), Inches(0), Inches(0.28), SLIDE_H, CYAN_ACC)
    add_rect(s1, Inches(0.28), Inches(0), Inches(0.08), SLIDE_H, BLUE_ACC)

    # Top badge pill
    badge = add_rect(s1, Inches(0.85), Inches(0.75), Inches(4.4), Inches(0.42), NAVY_MID,
                     line_color=CYAN_ACC, line_pt=1.0, rounded=True)
    bp = badge.text_frame.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    br = bp.add_run()
    br.text = "DATABASE MANAGEMENT SYSTEMS — COURSE PROJECT"
    br.font.name = FONT_MAIN
    br.font.size = Pt(10.5)
    br.font.bold = True
    br.font.color.rgb = CYAN_ACC

    # VIT Logo on top-right inside clean white circular/rounded card
    if os.path.exists(logo_path):
        add_rect(s1, Inches(10.95), Inches(0.6), Inches(1.7), Inches(1.95), WHITE,
                 line_color=CYAN_ACC, line_pt=1.5, rounded=True)
        s1.shapes.add_picture(logo_path, Inches(11.15), Inches(0.72), width=Inches(1.3))

    # Main Title
    add_textbox(s1, Inches(0.85), Inches(1.45), Inches(9.8), Inches(1.0),
                "CAMPUSRIDE", font_size=48, bold=True, color=WHITE)
    add_textbox(s1, Inches(0.85), Inches(2.42), Inches(9.8), Inches(1.1),
                "Smart Peer-to-Peer Campus Vehicle Rental System\nwith 100% SQL-Driven Core & AI/ML Fleet Intelligence",
                font_size=22, bold=False, color=RGBColor(0x94, 0xD2, 0xBD))

    # Horizontal divider
    add_rect(s1, Inches(0.85), Inches(3.78), Inches(11.8), Inches(0.03), CYAN_ACC)

    # Info cards (Team / Guide / Institute)
    add_rect(s1, Inches(0.85), Inches(4.15), Inches(5.6), Inches(2.45), NAVY_MID,
             line_color=RGBColor(0x33, 0x41, 0x55), line_pt=1.0, rounded=True)
    add_textbox(s1, Inches(1.1), Inches(4.3), Inches(5.1), Inches(0.35),
                "SUBMITTED BY", font_size=11, bold=True, color=CYAN_ACC)
    add_textbox(s1, Inches(1.1), Inches(4.7), Inches(5.1), Inches(1.75),
                "•  Student Name 1  (PRN: 12110001)\n"
                "•  Student Name 2  (PRN: 12110002)\n"
                "•  Student Name 3  (PRN: 12110003)\n"
                "•  Student Name 4  (PRN: 12110004)",
                font_size=14, color=WHITE)

    add_rect(s1, Inches(6.75), Inches(4.15), Inches(5.9), Inches(2.45), NAVY_MID,
             line_color=RGBColor(0x33, 0x41, 0x55), line_pt=1.0, rounded=True)
    add_textbox(s1, Inches(7.0), Inches(4.3), Inches(5.4), Inches(0.35),
                "INSTITUTION & GUIDANCE", font_size=11, bold=True, color=CYAN_ACC)
    add_textbox(s1, Inches(7.0), Inches(4.7), Inches(5.4), Inches(1.75),
                "Guide: Prof. [Guide Name]\n"
                "Dept. of Computer Science & Engineering (AI)\n"
                "Vishwakarma Institute of Technology, Pune\n"
                "Academic Year: 2026 – 2027",
                font_size=14, color=WHITE)

    add_notes(s1,
              "Good morning respected faculty and evaluators. Today we present CampusRide — a smart peer-to-peer campus vehicle rental system. "
              "Unlike standard CRUD web apps, CampusRide runs 100% of its core transactional logic inside MySQL 8.0 stored procedures and triggers, "
              "coupled with an AI/ML Predictive Intelligence Suite and Haversine perimeter geofencing.")

    # =========================================================================
    # SLIDE 2: INTRODUCTION & PROBLEM STATEMENT
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s2, "Introduction & Problem Statement", "Overview", 2)

    add_card(s2, Inches(0.5), Inches(1.25), Inches(6.0), Inches(4.15),
             title="The Campus Commuting & Technical Problem", accent=AMBER_ACC)
    add_bullets(s2, Inches(0.7), Inches(1.9), Inches(5.6), Inches(3.35), [
        ("Sprawling Campus Transit: ", "Walking between hostels, labs, and entrance gates wastes 15–20 minutes daily."),
        ("Idle Campus Assets: ", "Over 70% of student & faculty two-wheelers sit parked and unused for 8–10 hours each day."),
        ("Expensive Alternatives: ", "Commercial cabs charge ₹100+ base fares and are often barred from inner campus zones."),
        ("ORM Race Conditions: ", "Conventional rental apps rely on stateless ORMs, permitting double-booking under high concurrency."),
        ("Zero Accountability: ", "Informal vehicle borrowing lacks identity verification, audit trails, or perimeter safety."),
    ], font_size=13, space_after=8)

    add_card(s2, Inches(6.83), Inches(1.25), Inches(6.0), Inches(4.15),
             title="The CampusRide Solution", accent=TEAL_ACC)
    add_bullets(s2, Inches(7.03), Inches(1.9), Inches(5.6), Inches(3.35), [
        ("Peer-to-Peer Marketplace: ", "Verified owners monetize idle scooters, bikes, and cars at affordable hourly rates (₹45–₹200/hr)."),
        ("100% SQL-Driven Core: ", "Every booking, payment, auth check, and status flip executes atomically inside MySQL 8.0."),
        ("Role-Based Governance: ", "Dedicated portals for Renters, Owners, and System Administrators with salted SHA-256 + JWT."),
        ("AI/ML Fleet Intelligence: ", "TF-IDF recommendations, Isolation Forest fraud checks, predictive maintenance, & demand forecasting."),
        ("Campus Geofencing: ", "Haversine GPS perimeter monitor enforces a strict 2.5 km boundary with live breach alerts."),
    ], font_size=13, space_after=8)

    # Bottom 4 KPI stat pills
    kpis = [
        ("70%+", "Student Vehicles Idle Daily", AMBER_ACC),
        ("₹45–200/hr", "Affordable Campus Tariffs", TEAL_ACC),
        ("100% SQL", "ACID Transactional Engine", BLUE_ACC),
        ("2.5 km", "Enforced Campus Geofence", CYAN_ACC),
    ]
    for i, (val, lbl, col) in enumerate(kpis):
        x = Inches(0.5 + i * 3.13)
        add_rect(s2, x, Inches(5.65), Inches(2.93), Inches(1.15), WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
        add_rect(s2, x, Inches(5.65), Inches(0.1), Inches(1.15), col)
        add_textbox(s2, x + Inches(0.22), Inches(5.74), Inches(2.6), Inches(0.52),
                    val, font_size=22, bold=True, color=col)
        add_textbox(s2, x + Inches(0.22), Inches(6.28), Inches(2.6), Inches(0.42),
                    lbl, font_size=11.5, bold=False, color=TEXT_MUTED)

    add_notes(s2,
              "CampusRide solves two problems at once: an everyday campus commuting bottleneck where 70%+ of student vehicles sit idle, "
              "and a software engineering problem where ORM-based apps suffer from double-booking concurrency bugs and weak audit trails.")

    # =========================================================================
    # SLIDE 3: OBJECTIVES & COMPARATIVE ANALYSIS
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s3, "Objectives & Comparative Analysis", "Motivation", 3)

    objs = [
        ("1. P2P Campus Transit", "Connect verified student owners and renters with instant search, coupons, and reviews.", BLUE_ACC),
        ("2. ACID Database Core", "Eliminate double-booking using BEFORE INSERT triggers & transactional stored procedures.", TEAL_ACC),
        ("3. Security & Audit Trail", "Salted SHA-256 auth, 5-attempt 15-min lockout, RBAC, and trigger-driven AuditLog.", AMBER_ACC),
        ("4. AI/ML & Geofencing", "TF-IDF recs, Isolation Forest fraud checks, wear scoring, and 2.5 km Haversine alerts.", CYAN_ACC),
    ]
    for i, (otitle, odesc, ocol) in enumerate(objs):
        x = Inches(0.5 + i * 3.13)
        add_card(s3, x, Inches(1.2), Inches(2.95), Inches(1.7), title=otitle, accent=ocol)
        add_textbox(s3, x + Inches(0.18), Inches(1.8), Inches(2.6), Inches(1.0),
                    odesc, font_size=11.5, color=TEXT_DARK)

    # Comparison Table
    add_textbox(s3, Inches(0.5), Inches(3.1), Inches(12.3), Inches(0.38),
                "Comparison: Existing Mobility Systems vs. CampusRide", font_size=15, bold=True, color=NAVY)

    rows_data = [
        ["Parameter", "Commercial Cabs (Uber/Ola)", "Dockless Rentals (Yulu/Bounce)", "CampusRide (Proposed)"],
        ["Fleet Ownership", "External private drivers", "Centralized company fleet (High CapEx)", "Verified Student & Faculty Peers (Zero CapEx)"],
        ["Student Cost", "High (₹100+ base fare)", "Moderate (₹5/min + deposits)", "Very Affordable (₹45 – ₹200 / hour)"],
        ["Transaction Core", "App-layer services", "Distributed microservices", "100% SQL-Driven MySQL 8.0 (ACID)"],
        ["Concurrency Guard", "Application locks", "Queue-based locks", "BEFORE INSERT Trigger & Atomic Procedures"],
        ["Security & Perimeter", "Unrestricted city-wide", "City municipal zones", "Strict 2.5 km Campus Geofence + AuditLog"],
        ["Fleet Intelligence", "Driver dispatch pricing", "Battery swap ops", "TF-IDF Recs, Isolation Forest, Wear Health"],
    ]
    tbl_shape = s3.shapes.add_table(len(rows_data), 4, Inches(0.5), Inches(3.52), Inches(12.33), Inches(3.3))
    tbl = tbl_shape.table
    col_ws = [Inches(2.2), Inches(3.0), Inches(3.33), Inches(3.8)]
    for ci, w in enumerate(col_ws):
        tbl.columns[ci].width = w

    for ri, rvals in enumerate(rows_data):
        for ci, val in enumerate(rvals):
            cell = tbl.cell(ri, ci)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if ri == 0:
                cell.fill.fore_color.rgb = NAVY
            elif ci == 3:
                cell.fill.fore_color.rgb = RGBColor(0xEC, 0xFE, 0xFF) if ri % 2 == 1 else RGBColor(0xE0, 0xF2, 0xFE)
            else:
                cell.fill.fore_color.rgb = WHITE if ri % 2 == 1 else RGBColor(0xF1, 0xF5, 0xF9)

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            r.font.name = FONT_MAIN
            r.font.size = Pt(11.5 if ri == 0 else 11)
            r.font.bold = (ri == 0 or ci == 0 or ci == 3)
            r.font.color.rgb = WHITE if ri == 0 else (NAVY if ci == 3 else TEXT_DARK)

    add_notes(s3,
              "Unlike commercial cabs or high-CapEx dockless startups, CampusRide operates with zero capital investment by using peer vehicles. "
              "Architecturally, our key advantage is enforcing ACID transactions and double-booking prevention natively inside MySQL.")

    # =========================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE & TECH STACK
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s4, "System Architecture & Technology Stack", "Architecture", 4)

    tiers = [
        ("Tier 1: Presentation Layer", "HTML5, CSS3 Dark Glassmorphism, ES6 JavaScript (Fetch API + JWT). Dedicated portals for Renter, Owner & Admin.", CYAN_ACC),
        ("Tier 2: API & AI/ML Gateway", "Python 3.11 + FastAPI (Uvicorn :15501), SQLAlchemy raw SQL (Zero ORM), Scikit-learn ML Engine & Haversine Geofence.", BLUE_ACC),
        ("Tier 3: MySQL 8.0 InnoDB Core", "10 Normalized Tables, 6 Pre-Compiled Views, 7 UDFs, 10 ACID Stored Procedures, 7 Automated Row-Level Triggers.", TEAL_ACC),
    ]
    for i, (ttitle, tdesc, tcol) in enumerate(tiers):
        y = Inches(1.25 + i * 1.88)
        add_card(s4, Inches(0.5), y, Inches(4.65), Inches(1.68), title=ttitle, accent=tcol)
        add_textbox(s4, Inches(0.68), y + Inches(0.62), Inches(4.3), Inches(0.95),
                    tdesc, font_size=12, color=TEXT_DARK)

    # Right: Architecture Diagram
    if os.path.exists(arch_path):
        add_fitted_image(s4, arch_path, Inches(5.38), Inches(1.22), Inches(7.45), Inches(5.6),
                         caption="Figure 1: Three-Tier Decoupled System Architecture of CampusRide")

    add_notes(s4,
              "CampusRide follows a strict three-tier decoupled architecture. FastAPI acts purely as a stateless router and ML inference host "
              "with zero ORM overhead, dispatching parameterized CALL sp_* statements straight to MySQL 8.0.")

    # =========================================================================
    # SLIDE 5: ER DIAGRAM & RELATIONAL SCHEMA
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s5, "Entity-Relationship (ER) Diagram & Schema", "Database Design", 5)

    add_card(s5, Inches(0.5), Inches(1.22), Inches(4.25), Inches(5.6),
             title="10 Normalized Tables (3NF)", accent=BLUE_ACC)
    add_bullets(s5, Inches(0.66), Inches(1.82), Inches(3.95), Inches(4.85), [
        ("Student (16 cols): ", "Roles (student/owner/admin), SHA-256 hash, trust_score, lockout tracking."),
        ("Vehicle (16 cols): ", "Type, brand/model, hourly_rate CHECK > 0, status ENUM, avg_rating."),
        ("Rental (16 cols): ", "Start/end times, total_hours, subtotal, discount, final_amount, pickup OTP."),
        ("Payment (9 cols): ", "1:1 rental_id UNIQUE, UPI/Card/Cash, unique transaction_id, refunds."),
        ("Coupon (7 cols): ", "Promo code UNIQUE, discount 1–100%, valid date window."),
        ("Governance (5 Tables): ", "Review (rating 1..5), Maintenance, Insurance, Dispute, & append-only AuditLog."),
        ("AI/ML Extension: ", "Conceptual ML profiles, model registry & rental prediction linkage."),
    ], font_size=11.5, space_after=6)

    if os.path.exists(er_path):
        add_fitted_image(s5, er_path, Inches(4.95), Inches(1.22), Inches(7.88), Inches(5.6),
                         caption="Figure 2: Extended Entity-Relationship (EER) Diagram with AI/ML Extension Module")

    add_notes(s5,
              "Here is our Extended ER Diagram showing STUDENT overlapping specialization into Renter, Vehicle Owner, and Campus Admin, "
              "VEHICLE disjoint specialization into Two-Wheeler and Four-Wheeler, plus the AI/ML Extension Module. Physically, this maps to "
              "10 normalized 3NF InnoDB tables with strict PK, FK, CHECK, UNIQUE, and B-Tree index constraints.")

    # =========================================================================
    # SLIDE 6: ADVANCED DBMS CONCEPTS (JOINS, VIEWS, SUBQUERIES, AGGREGATES)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s6, "Advanced DBMS Implementation — SQL Constructs", "SQL Engine", 6)

    # 2x2 Card Grid
    # Card 1: Joins
    add_card(s6, Inches(0.5), Inches(1.22), Inches(6.0), Inches(2.7), title="1. SQL Joins (INNER, LEFT & Multi-Table)", accent=BLUE_ACC)
    add_bullets(s6, Inches(0.68), Inches(1.8), Inches(5.65), Inches(1.05), [
        ("4-Table INNER JOIN: ", "Combines Rental + Student + Vehicle + Payment for financial ledgers."),
        ("LEFT JOIN Analytics: ", "Includes zero-rental vehicles and optional Coupons without dropping rows."),
    ], font_size=12, space_after=4)
    c1 = add_rect(s6, Inches(0.7), Inches(2.92), Inches(5.6), Inches(0.82), CODE_BG, line_color=BORDER, line_pt=0.75)
    add_textbox(s6, Inches(0.78), Inches(2.96), Inches(5.45), Inches(0.74),
                "SELECT r.rental_id, s.full_name, v.model, p.transaction_id\n"
                "FROM Rental r JOIN Student s ON r.student_id=s.student_id\n"
                "JOIN Vehicle v ON r.vehicle_id=v.vehicle_id JOIN Payment p ON r.rental_id=p.rental_id;",
                font_size=8.8, font_name=FONT_CODE, color=NAVY)

    # Card 2: 6 Views
    add_card(s6, Inches(6.83), Inches(1.22), Inches(6.0), Inches(2.7), title="2. Pre-Compiled Database Views (6 Views)", accent=CYAN_ACC)
    add_bullets(s6, Inches(7.0), Inches(1.8), Inches(5.65), Inches(2.0), [
        ("vw_available_vehicles: ", "Available fleet joined with owner name & phone."),
        ("vw_rental_history: ", "Complete booking ledger with coupon & OTP codes."),
        ("vw_payment_history: ", "Verified payment receipts joined with student & vehicle."),
        ("vw_owner_earnings: ", "Aggregated COUNT, SUM & AVG revenue per owner."),
        ("vw_active_maintenance & vw_insurance_status: ", "Live service & DATEDIFF policy expiry tracking."),
    ], font_size=11.5, space_after=4)

    # Card 3: Nested & Correlated Queries
    add_card(s6, Inches(0.5), Inches(4.12), Inches(6.0), Inches(2.72), title="3. Nested & Correlated Subqueries", accent=TEAL_ACC)
    add_bullets(s6, Inches(0.68), Inches(4.7), Inches(5.65), Inches(1.05), [
        ("Nested Queries: ", "IN (repeat renters), multi-level AVG benchmark, NOT IN, & Top-3 derived table."),
        ("Correlated Queries: ", "Per-student MAX(final_amount) & NOT EXISTS for active-booking exclusion."),
    ], font_size=12, space_after=4)
    add_rect(s6, Inches(0.7), Inches(5.82), Inches(5.6), Inches(0.84), CODE_BG, line_color=BORDER, line_pt=0.75)
    add_textbox(s6, Inches(0.78), Inches(5.86), Inches(5.45), Inches(0.76),
                "SELECT v.vehicle_id, v.brand, v.model FROM Vehicle v\n"
                "WHERE NOT EXISTS (SELECT 1 FROM Rental r WHERE r.vehicle_id = v.vehicle_id\n"
                "                  AND r.status IN ('Confirmed', 'Active'));",
                font_size=8.8, font_name=FONT_CODE, color=NAVY)

    # Card 4: Aggregate Functions
    add_card(s6, Inches(6.83), Inches(4.12), Inches(6.0), Inches(2.72), title="4. Aggregate Functions & Grouping", accent=AMBER_ACC)
    add_bullets(s6, Inches(7.0), Inches(4.7), Inches(5.65), Inches(1.05), [
        ("Functions Used: ", "COUNT(), SUM(), AVG(), MIN(), MAX(), COALESCE(), ROUND()."),
        ("Analytical Reports: ", "Monthly revenue, Revenue by Vehicle Type, Payment share %, & Peak hours."),
    ], font_size=12, space_after=4)
    add_rect(s6, Inches(7.03), Inches(5.82), Inches(5.6), Inches(0.84), CODE_BG, line_color=BORDER, line_pt=0.75)
    add_textbox(s6, Inches(7.1), Inches(5.86), Inches(5.45), Inches(0.76),
                "SELECT v.vehicle_type, COUNT(r.rental_id) AS rentals, SUM(r.final_amount) AS rev\n"
                "FROM Rental r JOIN Vehicle v ON r.vehicle_id = v.vehicle_id\n"
                "WHERE r.status = 'Completed' GROUP BY v.vehicle_type ORDER BY rev DESC;",
                font_size=8.8, font_name=FONT_CODE, color=NAVY)

    add_notes(s6,
              "This slide highlights the core DBMS syllabus features implemented in CampusRide: multi-table joins, 6 pre-compiled views "
              "that simplify API reads, nested and correlated subqueries including NOT EXISTS, and aggregate GROUP BY queries powering our live revenue charts.")

    # =========================================================================
    # SLIDE 7: 100% SQL-DRIVEN CORE — UDFs, PROCEDURES & TRIGGERS
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s7, "100% SQL-Driven Core — Procedures, Functions & Triggers", "ACID Core", 7)

    # 3 Equal Columns
    add_card(s7, Inches(0.5), Inches(1.22), Inches(3.92), Inches(5.6), title="7 User-Defined Functions", accent=CYAN_ACC)
    add_bullets(s7, Inches(0.66), Inches(1.85), Inches(3.62), Inches(4.8), [
        ("fn_hash_password: ", "Deterministic SHA-256 with 'vitcampus' salt."),
        ("fn_total_hours: ", "Exact fractional hours via TIMESTAMPDIFF."),
        ("fn_calculate_rental_cost: ", "Rate × hours calculation inside MySQL."),
        ("fn_calculate_discount: ", "Validates coupon dates & computes discount."),
        ("fn_is_vehicle_available: ", "Boolean availability check."),
        ("fn_generate_txn_id: ", "Unique TXN + timestamp receipt ID."),
        ("fn_get_rental_count: ", "Completed rental counter per student."),
    ], font_size=11.5, space_after=7)

    add_card(s7, Inches(4.7), Inches(1.22), Inches(3.92), Inches(5.6), title="10 ACID Stored Procedures", accent=BLUE_ACC)
    add_bullets(s7, Inches(4.86), Inches(1.85), Inches(3.62), Inches(4.8), [
        ("sp_login: ", "Verifies SHA-256 hash; auto-locks account for 15 min after 5 failed attempts."),
        ("sp_register: ", "Duplicate check + transactional Student insert."),
        ("sp_create_rental: ", "Atomic availability check, pricing, coupon & booking commit with ROLLBACK handler."),
        ("sp_process_payment: ", "Prevents double-pay, generates TXN ID, activates Confirmed rental."),
        ("sp_complete / cancel_rental: ", "Safe lifecycle completion & ownership-verified cancellation."),
        ("Fleet & Reports: ", "sp_add_vehicle, sp_add_maintenance, utilization & spending reports."),
    ], font_size=11.5, space_after=6)

    add_card(s7, Inches(8.9), Inches(1.22), Inches(3.92), Inches(5.6), title="7 Automated Triggers", accent=TEAL_ACC)
    add_bullets(s7, Inches(9.06), Inches(1.85), Inches(3.62), Inches(4.8), [
        ("trg_before_rental_insert: ", "Double-booking guard — raises SIGNAL SQLSTATE '45000' if vehicle is unavailable."),
        ("trg_after_rental_insert: ", "Auto-flips vehicle to 'Rented' & logs RENTAL_CREATED."),
        ("trg_after_rental_update: ", "Restores vehicle to 'Available' on Complete/Cancel."),
        ("trg_after_payment_insert: ", "Writes PAYMENT_COMPLETED + TxnID into AuditLog."),
        ("trg_after_student_insert: ", "Logs every new user REGISTER event."),
        ("trg_after_maintenance_*: ", "Toggles 'Maintenance' ↔ 'Available' automatically."),
    ], font_size=11.5, space_after=6)

    add_notes(s7,
              "This is the heart of our DBMS design: 7 functions, 10 ACID stored procedures with transaction rollback handlers, and 7 triggers. "
              "Even if two students try to book the exact same scooter simultaneously, trg_before_rental_insert raises SQLSTATE 45000 and guarantees zero double-booking.")

    # =========================================================================
    # SLIDE 8: AI/ML INTELLIGENCE SUITE & CAMPUS GEOFENCING
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s8, "AI/ML Intelligence Suite & Campus Geofencing", "AI / ML + Security", 8)

    # Top concise 5-pill bar
    ai_pills = [
        ("Recommender", "TF-IDF + Cosine Similarity", BLUE_ACC),
        ("Demand Forecast", "Time-Series & Hotspots", CYAN_ACC),
        ("Fraud Detection", "Isolation Forest (0.05)", AMBER_ACC),
        ("Fleet Health", "Heuristic Wear (90.2%)", TEAL_ACC),
        ("Geofencing", "Haversine 2.5 km Alert", RGBColor(0xDC, 0x26, 0x26)),
    ]
    for i, (at, ad, ac) in enumerate(ai_pills):
        x = Inches(0.5 + i * 2.5)
        add_rect(s8, x, Inches(1.18), Inches(2.34), Inches(0.88), WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
        add_rect(s8, x, Inches(1.18), Inches(2.34), Inches(0.06), ac)
        add_textbox(s8, x + Inches(0.1), Inches(1.28), Inches(2.14), Inches(0.32), at, font_size=11.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_textbox(s8, x + Inches(0.1), Inches(1.62), Inches(2.14), Inches(0.35), ad, font_size=10, color=TEXT_MUTED, align=PP_ALIGN.CENTER)

    # Bottom 2 Live Screenshots Side-by-Side
    img_aiml = os.path.join(imgs_dir, "Screenshot 2026-11-18 172140.png")
    img_geo  = os.path.join(imgs_dir, "Screenshot 2026-11-18 172130.png")

    add_fitted_image(s8, img_aiml, Inches(0.5), Inches(2.22), Inches(6.0), Inches(4.55),
                     caption="AIML Core Status & Live Campus Demand Hotspots (Main Gate 48%, Hostel A 28%)")
    add_fitted_image(s8, img_geo, Inches(6.83), Inches(2.22), Inches(6.0), Inches(4.55),
                     caption="Haversine 2.5 km Geofence Monitor — Active Breach Alert #1 (~8.5 km outside campus)")

    add_notes(s8,
              "On top of MySQL, our Python ML engine runs five intelligent features. On the left, you can see all four active ML pipelines "
              "and campus hotspot rebalancing predicting 48% demand at Main Gate. On the right, our Haversine geofence monitor catches an "
              "active perimeter breach on Royal Enfield Classic 350 at 8.5 km outside the 2.5 km campus boundary.")

    # =========================================================================
    # SLIDE 9: LIVE IMPLEMENTATION & VERIFIED RESULTS
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s9, "Live Implementation & Verified Results", "Results & Output", 9)

    # Top verified metrics strip
    metrics = [
        ("7", "Verified Users", BLUE_ACC),
        ("8", "Listed Vehicles", CYAN_ACC),
        ("9", "Total Rentals", TEAL_ACC),
        ("₹2,210", "Verified Revenue", AMBER_ACC),
        ("65+", "Trigger Audit Logs", BLUE_ACC),
        ("90.2%", "Fleet Avg Health", TEAL_ACC),
    ]
    for i, (mv, ml, mc) in enumerate(metrics):
        x = Inches(0.5 + i * 2.08)
        add_rect(s9, x, Inches(1.18), Inches(1.93), Inches(0.88), WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
        add_rect(s9, x, Inches(1.18), Inches(1.93), Inches(0.06), mc)
        add_textbox(s9, x + Inches(0.08), Inches(1.26), Inches(1.77), Inches(0.42), mv, font_size=18, bold=True, color=mc, align=PP_ALIGN.CENTER)
        add_textbox(s9, x + Inches(0.08), Inches(1.68), Inches(1.77), Inches(0.32), ml, font_size=10, color=TEXT_MUTED, align=PP_ALIGN.CENTER)

    # 2 Large Crisp Live Screenshots Side-by-Side
    img_renter = os.path.join(imgs_dir, "Screenshot 2026-11-18 172149.png")
    img_audit  = os.path.join(imgs_dir, "Screenshot 2026-11-18 172118.png")

    add_fitted_image(s9, img_renter, Inches(0.5), Inches(2.22), Inches(6.0), Inches(4.55),
                     caption="Renter Dashboard (Rohit Sharma) — Live AI Smart Recommendations & Available Fleet")
    add_fitted_image(s9, img_audit, Inches(6.83), Inches(2.22), Inches(6.0), Inches(4.55),
                     caption="Admin Immutable Audit Trail — Auto-Logged by MySQL Triggers (#60–#65)")

    add_notes(s9,
              "Our live deployment verified 7 accounts, 8 vehicles, 9 rentals, and ₹2,210 in revenue (Bike ₹860, Car ₹640, Scooter ₹710) "
              "with zero double-booking conflicts. The left screenshot shows personalized AI vehicle picks on the Renter Dashboard, and the "
              "right screenshot proves our MySQL triggers automatically populating the immutable AuditLog table with transaction IDs and client IPs.")

    # =========================================================================
    # SLIDE 10: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, NAVY)
    add_rect(s10, Inches(0), Inches(0), SLIDE_W, Inches(0.08), CYAN_ACC)

    add_textbox(s10, Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.7),
                "Conclusion & Future Scope", font_size=32, bold=True, color=WHITE)
    add_rect(s10, Inches(0.6), Inches(1.12), Inches(2.6), Inches(0.05), CYAN_ACC)

    # Left Dark Card: Conclusion
    add_rect(s10, Inches(0.6), Inches(1.45), Inches(5.85), Inches(4.15), NAVY_MID,
             line_color=CYAN_ACC, line_pt=1.0, rounded=True)
    add_textbox(s10, Inches(0.85), Inches(1.65), Inches(5.35), Inches(0.42),
                "KEY CONCLUSION", font_size=15, bold=True, color=CYAN_ACC)
    add_bullets(s10, Inches(0.85), Inches(2.15), Inches(5.35), Inches(3.25), [
        ("100% SQL-Driven Integrity: ", "10 tables, 6 views, 7 UDFs, 10 stored procedures, and 7 triggers eliminate concurrency conflicts."),
        ("Zero Double-Booking: ", "Database-level BEFORE INSERT guards guarantee strict ACID transaction safety."),
        ("Proactive AI & Security: ", "Combines TF-IDF recs, Isolation Forest anomaly checks, 90.2% health telemetry, and 2.5 km geofencing."),
        ("Campus Impact: ", "Monetizes idle student assets while delivering safe, low-cost intra-campus mobility."),
    ], font_size=13, color=RGBColor(0xE2, 0xE8, 0xF0), lead_color=WHITE, space_after=10)

    # Right Dark Card: Future Scope
    add_rect(s10, Inches(6.88), Inches(1.45), Inches(5.85), Inches(4.15), NAVY_MID,
             line_color=BLUE_ACC, line_pt=1.0, rounded=True)
    add_textbox(s10, Inches(7.13), Inches(1.65), Inches(5.35), Inches(0.42),
                "FUTURE SCOPE", font_size=15, bold=True, color=RGBColor(0x60, 0xA5, 0xFA))
    add_bullets(s10, Inches(7.13), Inches(2.15), Inches(5.35), Inches(3.25), [
        ("IoT Smart Solenoid Locks: ", "ESP32 + BLE/4G modules for automated smartphone QR keyless unlocking."),
        ("EV Battery Telemetry (BMS): ", "Live State-of-Charge checks to prevent low-battery bookings."),
        ("Mobile App & Live GPS Stream: ", "Flutter/React Native app streaming real-time GPS with push alerts."),
        ("Automated UPI Escrow & Carpooling: ", "Instant owner payouts and multi-passenger campus ride splitting."),
    ], font_size=13, color=RGBColor(0xE2, 0xE8, 0xF0), lead_color=WHITE, space_after=10)

    # Thank You Bottom Banner
    add_rect(s10, Inches(0.6), Inches(5.9), Inches(12.13), Inches(1.05), RGBColor(0x16, 0x24, 0x3D),
             line_color=CYAN_ACC, line_pt=1.0, rounded=True)
    add_textbox(s10, Inches(0.8), Inches(6.02), Inches(11.73), Inches(0.48),
                "THANK YOU!", font_size=22, bold=True, color=CYAN_ACC, align=PP_ALIGN.CENTER)
    add_textbox(s10, Inches(0.8), Inches(6.48), Inches(11.73), Inches(0.36),
                "Questions & Live System Demonstration  |  CampusRide (VIT Pune — CSE AI)",
                font_size=13, italic=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_notes(s10,
              "To conclude, CampusRide proves how a 100% SQL-driven architecture combined with practical machine learning creates a reliable, "
              "secure, and economical campus micro-mobility system. Thank you for listening — we are happy to take questions and show a live demo.")

    # Save to report folder
    out_ppt = r"c:\Users\HP\OneDrive\Documents\cp\report\CampusRide_DBMS_Presentation.pptx"
    prs.save(out_ppt)
    print(f"Presentation successfully created -> {out_ppt}")


if __name__ == "__main__":
    build_ppt()

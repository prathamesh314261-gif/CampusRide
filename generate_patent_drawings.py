import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

scratch_dir = r"C:\Users\HP\.gemini\antigravity\brain\f3255e1c-82ec-45a0-9e0a-4bb1cdf5a518\scratch"


def draw_patent_box(ax, x, y, w, h, numeral, lw=1.6, ls='-', num_size=14, num_pos='center'):
    rect = patches.Rectangle((x, y), w, h, linewidth=lw, edgecolor='black', facecolor='white', linestyle=ls)
    ax.add_patch(rect)
    if num_pos == 'center':
        ax.text(x + w / 2, y + h / 2, numeral, ha='center', va='center',
                fontsize=num_size, fontweight='bold', fontfamily='serif', color='black')
    elif num_pos == 'top_left':
        ax.text(x + 0.35, y + h - 0.32, numeral, ha='left', va='top',
                fontsize=num_size, fontweight='bold', fontfamily='serif', color='black')
    elif num_pos == 'top_right':
        ax.text(x + w - 0.35, y + h - 0.28, numeral, ha='right', va='top',
                fontsize=num_size, fontweight='bold', fontfamily='serif', color='black')


def draw_arrow(ax, x1, y1, x2, y2, style='<->', lw=1.5):
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color='black', lw=lw, shrinkA=0, shrinkB=0)
    )


def create_fig1_architecture():
    """
    Indian Patent Office compliant schematic (ZERO text labels, ONLY reference numerals 100-110).
    100: Overall system boundary
    101: Multi-role client presentation interface
    102: Stateless API gateway & JWT authenticator
    103: Relational database management engine
    104: Normalized relational storage (tables & views)
    105: Atomic stored procedures & deterministic functions
    106: Automated row-level trigger guard unit
    107: Append-only immutable audit ledger
    108: AI/ML predictive analytics engine
    109: Haversine spatial perimeter geofencing unit
    110: External GPS coordinate telemetry & campus perimeter boundary
    """
    fig, ax = plt.subplots(figsize=(7.5, 6.2), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # Outer System Boundary (100)
    draw_patent_box(ax, 0.3, 0.4, 11.4, 9.2, '100', lw=1.8, ls='--', num_size=15, num_pos='top_right')

    # Top Layer: Client Interface (101)
    draw_patent_box(ax, 3.3, 8.0, 5.4, 1.1, '101', lw=1.8, num_size=15)

    # Middle Layer: Stateless Gateway (102)
    draw_patent_box(ax, 3.3, 6.0, 5.4, 1.1, '102', lw=1.8, num_size=15)
    draw_arrow(ax, 6.0, 8.0, 6.0, 7.1, style='<->')

    # Right Intelligence & Geofencing Column: AI/ML Engine (108), Geofence Monitor (109), GPS Telemetry (110)
    draw_patent_box(ax, 8.3, 3.6, 2.9, 1.4, '108', lw=1.6, num_size=15)
    draw_patent_box(ax, 8.3, 1.8, 2.9, 1.2, '109', lw=1.6, num_size=15)
    # 110 as circle/ellipse for external telemetry/perimeter zone
    circ = patches.Ellipse((9.75, 0.95), 2.5, 0.7, linewidth=1.5, edgecolor='black', facecolor='white', linestyle=':')
    ax.add_patch(circ)
    ax.text(9.75, 0.95, '110', ha='center', va='center', fontsize=14, fontweight='bold', fontfamily='serif')

    # Left/Bottom Major Container: Relational Database Engine (103)
    draw_patent_box(ax, 0.8, 0.9, 6.8, 4.3, '103', lw=1.8, ls='-', num_size=15, num_pos='top_left')

    # Sub-units inside 103: 105 (Procedures), 106 (Triggers), 104 (Tables/Views), 107 (AuditLog)
    draw_patent_box(ax, 1.2, 3.2, 2.7, 1.2, '105', lw=1.4, num_size=14)
    draw_patent_box(ax, 4.5, 3.2, 2.7, 1.2, '106', lw=1.4, num_size=14)
    draw_patent_box(ax, 1.2, 1.3, 2.7, 1.2, '104', lw=1.4, num_size=14)
    draw_patent_box(ax, 4.5, 1.3, 2.7, 1.2, '107', lw=1.4, num_size=14)

    # Arrows inside 103
    draw_arrow(ax, 3.9, 3.8, 4.5, 3.8, style='->')     # 105 -> 106
    draw_arrow(ax, 2.55, 3.2, 2.55, 2.5, style='<->')  # 105 <-> 104
    draw_arrow(ax, 5.85, 3.2, 5.85, 2.5, style='->')   # 106 -> 107
    draw_arrow(ax, 4.5, 3.4, 3.9, 2.3, style='->')     # 106 -> 104 (status flip)

    # Arrows connecting 102 <-> 103, 102 <-> 108, 108 <-> 104, 109 <-> 107, 110 -> 109, 102 <-> 109
    draw_arrow(ax, 4.2, 6.0, 4.2, 5.2, style='<->')    # 102 <-> 103
    draw_arrow(ax, 7.6, 6.0, 9.75, 5.0, style='<->')   # 102 <-> 108
    draw_arrow(ax, 8.3, 4.1, 7.6, 4.1, style='<->')    # 108 <-> 103
    draw_arrow(ax, 8.3, 2.3, 7.2, 2.0, style='->')     # 109 -> 107 (breach log)
    draw_arrow(ax, 9.75, 1.3, 9.75, 1.8, style='->')   # 110 -> 109
    draw_arrow(ax, 9.75, 3.6, 9.75, 3.0, style='<->')  # 108 <-> 109

    out1 = os.path.join(scratch_dir, "patent_fig1.png")
    plt.savefig(out1, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.15)
    plt.close(fig)
    print(f"Created patent Figure 1 -> {out1}")


def create_fig2_workflow():
    """
    Indian Patent Office compliant operational workflow diagram (ZERO text labels, ONLY common numerals 101-110).
    """
    fig, ax = plt.subplots(figsize=(6.2, 6.8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # Sequential vertical flow with side validation loops using ONLY common single numerals
    # Step 1: Client Request (101)
    draw_patent_box(ax, 3.2, 9.6, 3.6, 0.9, '101', lw=1.7, num_size=14)
    draw_arrow(ax, 5.0, 9.6, 5.0, 8.9, style='->')

    # Step 2: Gateway & JWT Validation (102)
    draw_patent_box(ax, 3.2, 8.0, 3.6, 0.9, '102', lw=1.7, num_size=14)
    draw_arrow(ax, 5.0, 8.0, 5.0, 7.3, style='->')
    # Side AI Recommendation / Anomaly call (108)
    draw_patent_box(ax, 7.5, 8.0, 2.0, 0.9, '108', lw=1.5, num_size=14)
    draw_arrow(ax, 6.8, 8.45, 7.5, 8.45, style='<->')

    # Step 3: Stored Procedure Transaction (105)
    draw_patent_box(ax, 3.2, 6.4, 3.6, 0.9, '105', lw=1.7, num_size=14)
    draw_arrow(ax, 5.0, 6.4, 5.0, 5.7, style='->')

    # Step 4: Trigger Guard Decision Diamond (106)
    diamond = patches.Polygon([[5.0, 5.7], [6.6, 4.8], [5.0, 3.9], [3.4, 4.8]],
                              closed=True, linewidth=1.7, edgecolor='black', facecolor='white')
    ax.add_patch(diamond)
    ax.text(5.0, 4.8, '106', ha='center', va='center', fontsize=14, fontweight='bold', fontfamily='serif')

    # Reject branch back to 101 (left side)
    ax.plot([3.4, 1.5, 1.5], [4.8, 4.8, 10.05], color='black', lw=1.4, linestyle='--')
    draw_arrow(ax, 1.5, 10.05, 3.2, 10.05, style='->', lw=1.4)

    # Pass branch down to Normalized Tables (104)
    draw_arrow(ax, 5.0, 3.9, 5.0, 3.2, style='->')
    draw_patent_box(ax, 3.2, 2.3, 3.6, 0.9, '104', lw=1.7, num_size=14)

    # Side Immutable Audit Log (107) triggered by 106
    draw_patent_box(ax, 7.5, 4.35, 2.0, 0.9, '107', lw=1.5, num_size=14)
    draw_arrow(ax, 6.6, 4.8, 7.5, 4.8, style='->')

    # Bottom Geofencing Loop (109 & 110)
    draw_arrow(ax, 5.0, 2.3, 5.0, 1.6, style='->')
    draw_patent_box(ax, 3.2, 0.7, 3.6, 0.9, '109', lw=1.7, num_size=14)

    circ = patches.Ellipse((1.4, 1.15), 1.8, 0.75, linewidth=1.5, edgecolor='black', facecolor='white', linestyle=':')
    ax.add_patch(circ)
    ax.text(1.4, 1.15, '110', ha='center', va='center', fontsize=14, fontweight='bold', fontfamily='serif')
    draw_arrow(ax, 2.3, 1.15, 3.2, 1.15, style='->')

    # Breach alert from 109 up to 107
    ax.plot([6.8, 8.5, 8.5], [1.15, 1.15, 4.35], color='black', lw=1.4)
    draw_arrow(ax, 8.5, 4.0, 8.5, 4.35, style='->', lw=1.4)

    out2 = os.path.join(scratch_dir, "patent_fig2.png")
    plt.savefig(out2, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.15)
    plt.close(fig)
    print(f"Created patent Figure 2 -> {out2}")


if __name__ == "__main__":
    create_fig1_architecture()
    create_fig2_workflow()

"""
graph_viewer.py  —  PACXON Statistics (single window, tabbed)
Run:  python graph_viewer.py [stats.csv]

Tabs: Summary | Capture Efficiency | Risk Duration | Input Density | Time Between Events
Navigate with number keys 1-5 or click the tab buttons.
"""

import os, csv, math, sys

# ── Palette ────────────────────────────────────────────────────────────────────
BG      = "#0a0a14"
BORDER  = "#1e1e38"
ACCENT  = "#00ffb4"
ACCENT2 = "#ffe000"
ACCENT3 = "#ff4d7a"
ACCENT4 = "#4a9eff"
ACCENT5 = "#b060ff"
TEXT_BRIGHT = "#eeeef8"
TEXT_MID    = "#8888aa"
TEXT_DIM    = "#444460"
GRID_LINE   = "#181828"

LEVEL_COLORS = [
    "#00ffb4","#ffe000","#ff4d7a","#4a9eff","#b060ff","#ff9030",
    "#00e5ff","#ff6060","#a0ff60","#ff60d0","#60d0ff","#ffc060",
]

TABS = ["Summary", "Capture", "Risk", "Density", "Survival"]


# ══════════════════════════════════════════════════════════════════════════════
def show_graphs(csv_path="stats.csv"):
    try:
        import matplotlib
        matplotlib.use("TkAgg")
    except Exception:
        pass

    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        from matplotlib.widgets import Button
        import matplotlib.patches as mpatches
    except ImportError:
        print("[graph_viewer] pip install matplotlib"); return

    rows = _load_csv(csv_path)
    cr   = [r for r in rows if r["event"] == "trail_close"]
    ar   = [r for r in rows if r["event"] in ("trail_close", "player_death")]
    dr   = [r for r in rows if r["event"] == "player_death"]

    plt.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    "#0d0d1a",
        "axes.edgecolor":    BORDER,
        "axes.labelcolor":   TEXT_MID,
        "axes.titlecolor":   TEXT_BRIGHT,
        "axes.titlesize":    11,
        "axes.titlepad":     10,
        "axes.grid":         True,
        "grid.color":        GRID_LINE,
        "grid.linewidth":    0.5,
        "xtick.color":       TEXT_DIM,
        "ytick.color":       TEXT_DIM,
        "xtick.labelsize":   8,
        "ytick.labelsize":   8,
        "legend.facecolor":  "#13132299",
        "legend.edgecolor":  BORDER,
        "legend.labelcolor": TEXT_MID,
        "legend.fontsize":   7,
        "text.color":        TEXT_BRIGHT,
        "font.family":       "monospace",
    })

    fig = plt.figure(figsize=(9, 6))
    fig.patch.set_facecolor(BG)
    try:
        fig.canvas.manager.set_window_title("GRIDRUSH — Statistics")
    except Exception:
        pass

    state = {"tab": 0}

    # ── Tab button axes (thin strip at top) ───────────────────────────────────
    TAB_H   = 0.07
    TAB_Y   = 1.0 - TAB_H
    n_tabs  = len(TABS)
    btn_w   = 1.0 / n_tabs
    btn_axes = []
    buttons  = []

    TAB_ACCENTS = [ACCENT, ACCENT, ACCENT3, ACCENT2, ACCENT4]

    for i, label in enumerate(TABS):
        ax_btn = fig.add_axes([i * btn_w, TAB_Y, btn_w, TAB_H])
        btn = Button(ax_btn, f"{i+1}. {label}",
                     color=BORDER, hovercolor="#2a2a44")
        btn.label.set_color(TAB_ACCENTS[i])
        btn.label.set_fontsize(8)
        btn.label.set_fontfamily("monospace")
        btn_axes.append(ax_btn)
        buttons.append(btn)

    # ── Content area (below tabs) ─────────────────────────────────────────────
    CONTENT_TOP    = TAB_Y - 0.08
    CONTENT_BOTTOM = 0.10

    # We'll store axes we create so we can clear them between tabs
    content_axes = []

    def clear_content():
        for ax in content_axes:
            fig.delaxes(ax)
        content_axes.clear()
        # Also remove any fig-level text artists added by previous tab
        for artist in fig.texts[:]:
            fig.texts.remove(artist)
        for artist in fig.lines[:]:
            fig.lines.remove(artist)

    def highlight_tab(idx):
        for i, (ax_btn, btn) in enumerate(zip(btn_axes, buttons)):
            if i == idx:
                ax_btn.set_facecolor("#1e1e38")
                btn.ax.set_facecolor("#1e1e38")
            else:
                ax_btn.set_facecolor(BORDER)
                btn.ax.set_facecolor(BORDER)

    def draw_tab(idx):
        clear_content()
        state["tab"] = idx
        highlight_tab(idx)

        L = 0.10
        R = 0.97
        T = CONTENT_TOP
        B = CONTENT_BOTTOM

        if idx == 0:
            ax = fig.add_axes([0, B, 1, T - B])
            content_axes.append(ax)
            _draw_summary(ax, rows, cr, dr, mpatches)

        elif idx == 1:
            ax = fig.add_axes([L, B, R - L, T - B])
            content_axes.append(ax)
            _style_ax(ax, ACCENT)
            ax.set_title("CAPTURE EFFICIENCY", color=ACCENT)
            ax.set_xlabel("Trail number")
            ax.set_ylabel("% of playable area captured")
            _plot_capture(ax, cr) if cr else _no_data(ax)

        elif idx == 2:
            ax = fig.add_axes([L, B, R - L, T - B])
            content_axes.append(ax)
            _style_ax(ax, ACCENT3)
            ax.set_title("RISK DURATION", color=ACCENT3)
            ax.set_xlabel("Trail attempt (within level)")
            ax.set_ylabel("Seconds outside safe territory")
            _plot_risk(ax, ar) if ar else _no_data(ax)

        elif idx == 3:
            ax = fig.add_axes([L + 0.1, B, R - L - 0.2, T - B])
            content_axes.append(ax)
            ax.set_facecolor("#0d0d1a")
            ax.set_title("INPUT DENSITY", color=ACCENT2)
            ax.axis("off")
            _plot_density(ax, ar) if ar else _no_data(ax)

        elif idx == 4:
            ax = fig.add_axes([L, B, R - L, T - B])
            content_axes.append(ax)
            _style_ax(ax, ACCENT4)
            ax.set_title("TIME BETWEEN EVENTS", color=ACCENT4)
            ax.set_xlabel("Seconds between events")
            ax.set_ylabel("Number of occurrences")
            _plot_survival(ax, rows) if rows else _no_data(ax)

        fig.canvas.draw_idle()

    # ── Wire up buttons ───────────────────────────────────────────────────────
    def make_handler(i):
        def handler(event):
            draw_tab(i)
        return handler

    for i, btn in enumerate(buttons):
        btn.on_clicked(make_handler(i))

    # ── Key shortcuts 1-5 ─────────────────────────────────────────────────────
    def on_key(event):
        if event.key in [str(i+1) for i in range(n_tabs)]:
            draw_tab(int(event.key) - 1)

    fig.canvas.mpl_connect("key_press_event", on_key)

    draw_tab(0)
    plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# Tab 0 — Summary
# ══════════════════════════════════════════════════════════════════════════════
def _draw_summary(fig_ax, rows, cr, dr, mpatches):
    fig_ax.set_xlim(0, 1); fig_ax.set_ylim(0, 1)
    fig_ax.set_facecolor(BG)
    fig_ax.axis("off")

    for i in range(20):
        fig_ax.axvline(i/19, color=GRID_LINE, linewidth=0.4, alpha=0.4)
    for i in range(13):
        fig_ax.axhline(i/12, color=GRID_LINE, linewidth=0.4, alpha=0.4)

    fig_ax.text(0.5, 0.80, "GRIDRUSH", ha="center", va="center",
                fontsize=64, fontweight="bold", color=ACCENT,
                transform=fig_ax.transAxes)
    fig_ax.text(0.5, 0.69, "SESSION  STATISTICS", ha="center", va="center",
                fontsize=12, color=TEXT_MID, transform=fig_ax.transAxes)

    lvl_count  = len({r["level"] for r in rows})
    avg_cap    = _mean([r["capture_efficiency"] for r in cr]) if cr else 0
    avg_risk   = _mean([r["risk_duration"] for r in rows if r["event"] in ("trail_close","player_death")])
    death_rate = (len(dr) / max(1, len(cr) + len(dr))) * 100

    cards = [
        ("TRAILS",      f"{len(cr)}",        ACCENT,  "closures"),
        ("DEATHS",      f"{len(dr)}",         ACCENT3, "lives lost"),
        ("LEVELS",      f"{lvl_count}",       ACCENT2, "reached"),
        ("AVG CAPTURE", f"{avg_cap:.1f}%",    ACCENT,  "per trail"),
        ("AVG RISK",    f"{avg_risk:.1f}s",   ACCENT4, "exposed"),
        ("DEATH RATE",  f"{death_rate:.0f}%", ACCENT5, "of attempts"),
    ]

    card_w = 0.13; card_h = 0.14; yc = 0.45
    xs = [0.5 + (i - 2.5) * 0.155 for i in range(6)]
    for (label, value, col, sub), cx in zip(cards, xs):
        fig_ax.add_patch(mpatches.FancyBboxPatch(
            (cx - card_w/2, yc - card_h/2), card_w, card_h,
            boxstyle="round,pad=0.008", transform=fig_ax.transAxes,
            facecolor=BORDER, edgecolor=col, linewidth=1.0, alpha=0.9, zorder=3))
        fig_ax.text(cx, yc + 0.025, value, ha="center", va="center",
                    fontsize=20, fontweight="bold", color=col,
                    transform=fig_ax.transAxes, zorder=5)
        fig_ax.text(cx, yc - 0.022, label, ha="center", va="center",
                    fontsize=7, color=TEXT_MID, transform=fig_ax.transAxes, zorder=5)
        fig_ax.text(cx, yc - 0.048, sub, ha="center", va="center",
                    fontsize=6, color=TEXT_DIM, transform=fig_ax.transAxes, zorder=5)

    fig_ax.text(0.5, 0.20,
                "Press  1  Summary   2  Capture   3  Risk   4  Density   5  Survival",
                ha="center", va="center", fontsize=8, color=TEXT_DIM,
                transform=fig_ax.transAxes)


# ══════════════════════════════════════════════════════════════════════════════
# Chart helpers
# ══════════════════════════════════════════════════════════════════════════════
def _style_ax(ax, accent_col):
    ax.set_facecolor("#0d0d1a")
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.spines["left"].set_edgecolor(accent_col); ax.spines["left"].set_alpha(0.5)
    ax.spines["bottom"].set_edgecolor(accent_col); ax.spines["bottom"].set_alpha(0.5)
    ax.tick_params(colors=TEXT_DIM, length=3)


def _no_data(ax):
    ax.text(0.5, 0.5, "NO DATA YET", transform=ax.transAxes,
            ha="center", va="center", fontsize=12, color=TEXT_DIM)


# ── Capture Efficiency ────────────────────────────────────────────────────────
def _plot_capture(ax, cr):
    vals = [r["capture_efficiency"] for r in cr]
    n = len(vals)
    x = list(range(1, n + 1))

    col = lambda v: ACCENT if v >= 15 else ACCENT2 if v >= 5 else ACCENT3
    ax.bar(x, vals, color=[col(v) for v in vals],
           width=0.8 if n <= 80 else 0.95, zorder=3, linewidth=0, alpha=0.85)

    w = max(3, n // 8)
    ax.plot(x, _rolling_mean(vals, w), color=ACCENT, linewidth=2.0, zorder=5, label=f"trend (w={w})")

    avg = _mean(vals)
    ax.axhline(avg, ls="--", lw=1.2, color=ACCENT2, label=f"avg {avg:.1f}%", zorder=4)
    ax.set_ylim(0, max(vals) * 1.25 + 1)
    ax.legend(loc="upper right")


# ── Risk Duration ─────────────────────────────────────────────────────────────
def _plot_risk(ax, ar):
    levels = {}
    for r in ar:
        levels.setdefault(r["level"], []).append(r["risk_duration"])
    avg_all = _mean([r["risk_duration"] for r in ar])
    n_levels = len(levels)
    for i, (lvl, durs) in enumerate(sorted(levels.items())):
        col = LEVEL_COLORS[i % len(LEVEL_COLORS)]
        xs  = list(range(1, len(durs) + 1))
        if n_levels <= 5:
            ax.plot(xs, durs, color=col, linewidth=1.6,
                    marker="o", markersize=3, zorder=3, label=f"lv {lvl}")
            ax.fill_between(xs, durs, alpha=0.07, color=col)
        else:
            win  = max(3, len(durs) // 6)
            roll = _rolling_mean(durs, win)
            ax.plot(xs, roll, color=col, linewidth=1.3, zorder=3, label=f"lv {lvl}")
    ax.axhline(avg_all, linestyle=":", linewidth=1.2,
               color=TEXT_DIM, label=f"avg {avg_all:.1f}s", zorder=2)
    ncol = 1 if n_levels <= 6 else 2
    ax.legend(ncol=ncol, loc="upper right", fontsize=7)


# ── Input Density (donut) ─────────────────────────────────────────────────────
def _plot_density(ax, ar):
    straight = sum(1 for r in ar if r["input_density"] <= 2)
    moderate = sum(1 for r in ar if 3 <= r["input_density"] <= 5)
    complex_ = sum(1 for r in ar if r["input_density"] > 5)
    raw    = [straight, moderate, complex_]
    labels = ["Straight\n(0–2)", "Moderate\n(3–5)", "Complex\n(6+)"]
    colors = [ACCENT, ACCENT2, ACCENT3]
    data   = [(l, c, v) for l, c, v in zip(labels, colors, raw) if v > 0]
    if not data:
        return _no_data(ax)
    wedges, _, autotexts = ax.pie(
        [d[2] for d in data],
        labels=[d[0] for d in data],
        colors=[d[1] for d in data],
        autopct="%1.0f%%",
        startangle=90,
        radius=0.80,
        wedgeprops=dict(width=0.52, edgecolor=BG, linewidth=3),
        textprops={"color": TEXT_MID, "fontsize": 9, "fontfamily": "monospace"},
        pctdistance=0.75,
        labeldistance=1.18,
    )
    for at in autotexts:
        at.set_color(TEXT_BRIGHT); at.set_fontsize(11); at.set_fontweight("bold")
    total = sum(d[2] for d in data)
    ax.text(0, 0, f"{total}\nattempts", ha="center", va="center",
            fontsize=11, color=TEXT_MID)


# ── Survival / Time Between Events ───────────────────────────────────────────
def _plot_survival(ax, rows):
    times = [r["survival_time"] for r in rows if r["survival_time"] > 0.5]
    if not times:
        return _no_data(ax)
    sorted_t = sorted(times)
    p99  = sorted_t[int(len(times) * 0.99)]
    shown = [t for t in times if t <= p99]
    bins = max(8, min(50, int(len(shown) ** 0.5) + 6))
    n_vals, bin_edges, patches = ax.hist(
        shown, bins=bins, color=ACCENT4, edgecolor=BG, linewidth=0.4, zorder=3)
    peak = max(n_vals) if len(n_vals) and max(n_vals) else 1
    for patch, height in zip(patches, n_vals):
        patch.set_facecolor(_lerp_color(ACCENT3, ACCENT4, height / peak))
        patch.set_alpha(0.88)
    mu  = _mean(times)
    med = sorted_t[len(sorted_t) // 2]
    ax.axvline(mu,  linestyle="--", linewidth=1.6, color=ACCENT2, label=f"mean {mu:.1f}s")
    ax.axvline(med, linestyle=":",  linewidth=1.4, color=ACCENT3, label=f"median {med:.1f}s")
    ax.legend(loc="upper right")


# ── Shared math helpers ───────────────────────────────────────────────────────
def _rolling_mean(vals, win):
    result = []
    half = win // 2
    for i in range(len(vals)):
        lo = max(0, i - half); hi = min(len(vals), i + half + 1)
        result.append(sum(vals[lo:hi]) / (hi - lo))
    return result


def _lerp_color(hex1, hex2, t):
    r1,g1,b1 = _hex_to_rgb(hex1); r2,g2,b2 = _hex_to_rgb(hex2)
    return (r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def _load_csv(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for fld in ("capture_efficiency","risk_duration","ghost_proximity","survival_time","timestamp"):
                try:    row[fld] = float(row[fld])
                except: row[fld] = 0.0
            try:    row["input_density"] = int(row["input_density"])
            except: row["input_density"] = 0
            try:    row["level"] = int(row["level"])
            except: row["level"] = 1
            rows.append(row)
    return rows


def _mean(v):
    return sum(v) / len(v) if v else 0.0


if __name__ == "__main__":
    show_graphs(sys.argv[1] if len(sys.argv) > 1 else "stats.csv")
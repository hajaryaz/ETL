# visualizations/dashboard.py
# ─────────────────────────────────────────────────────────────────
# VISUALIZE: Queries PostgreSQL → generates Matplotlib charts.
#
# Run after the pipeline has loaded data:
#   python visualizations/dashboard.py
#
# Produces 4 charts:
#   1. Top 20 skills overall (horizontal bar chart)
#   2. Top skills per category (grouped bars)
#   3. Skill category breakdown (pie/donut)
#   4. Skills heatmap by search query
# ─────────────────────────────────────────────────────────────────

import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import psycopg2

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG

log = logging.getLogger(__name__)

# ── Dark theme to match your portfolio aesthetic ──────────────────
plt.style.use("dark_background")
COLORS = {
    "AI/ML":     "#a78bfa",  # purple
    "GenAI":     "#f472b6",  # pink
    "Cloud":     "#38bdf8",  # blue
    "MLOps":     "#34d399",  # green
    "Languages": "#fbbf24",  # yellow
    "Data":      "#fb923c",  # orange
}
DEFAULT_COLOR = "#6b7280"


def fetch(sql: str, params=None) -> pd.DataFrame:
    """Run a SQL query and return a pandas DataFrame."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def plot_top_skills(ax, n=20):
    """Horizontal bar chart of the top N skills by mention count."""
    df = fetch(f"""
        SELECT skill, category, mention_count
        FROM top_skills
        LIMIT {n}
    """)

    if df.empty:
        ax.text(0.5, 0.5, "No data yet — run the pipeline first",
                ha="center", va="center", transform=ax.transAxes, color="gray")
        return

    df = df.sort_values("mention_count")
    bar_colors = [COLORS.get(cat, DEFAULT_COLOR) for cat in df["category"]]

    bars = ax.barh(df["skill"], df["mention_count"], color=bar_colors, height=0.7)

    # Value labels on bars
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.5, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", ha="left", fontsize=8, color="white")

    ax.set_title(f"Top {n} In-Demand Tech Skills", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Job Listings Mentioning Skill")
    ax.spines[["top", "right"]].set_visible(False)

    # Legend for categories
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=cat) for cat, c in COLORS.items()]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=8)


def plot_category_donut(ax):
    """Donut chart showing skill mentions by category."""
    df = fetch("""
        SELECT category, COUNT(*) AS total
        FROM job_skills
        GROUP BY category
        ORDER BY total DESC
    """)

    if df.empty:
        return

    colors = [COLORS.get(cat, DEFAULT_COLOR) for cat in df["category"]]
    wedges, texts, autotexts = ax.pie(
        df["total"],
        labels=df["category"],
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops={"width": 0.5},   # makes it a donut
        textprops={"color": "white", "fontsize": 9},
    )
    for at in autotexts:
        at.set_fontsize(8)

    ax.set_title("Skill Categories Distribution", fontsize=13, fontweight="bold", pad=12)


def plot_top_per_category(ax):
    """Grouped bar chart: top 5 skills per category."""
    df = fetch("""
        SELECT category, skill, mention_count
        FROM top_skills_by_category
    """)

    if df.empty:
        return

    # Keep top 5 per category
    top5 = df.groupby("category").head(5)
    categories = top5["category"].unique()

    x = np.arange(len(categories))
    width = 0.15
    max_per_cat = top5.groupby("category").size().max()

    for i in range(max_per_cat):
        vals, labels_text = [], []
        for cat in categories:
            group = top5[top5["category"] == cat].reset_index(drop=True)
            if i < len(group):
                vals.append(group.iloc[i]["mention_count"])
                labels_text.append(group.iloc[i]["skill"])
            else:
                vals.append(0)
                labels_text.append("")

        offset = (i - max_per_cat / 2) * width
        bars = ax.bar(x + offset, vals, width, label=f"#{i+1}", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=15, ha="right")
    ax.set_title("Top Skills per Category", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Mentions")
    ax.legend(title="Rank", fontsize=7, title_fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)


def plot_skills_by_query(ax):
    """Heatmap: skills vs. search query (which queries need which skills)."""
    df = fetch("""
        SELECT j.search_query, js.skill, COUNT(*) AS cnt
        FROM job_skills js
        JOIN jobs j ON j.id = js.job_id
        WHERE js.skill IN (
            SELECT skill FROM top_skills LIMIT 15
        )
        GROUP BY j.search_query, js.skill
    """)

    if df.empty:
        return

    pivot = df.pivot_table(index="skill", columns="search_query", values="cnt", fill_value=0)

    im = ax.imshow(pivot.values, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title("Skill Demand by Job Search Query", fontsize=13, fontweight="bold", pad=12)

    plt.colorbar(im, ax=ax, label="Mentions")


def generate_dashboard():
    """Compose all 4 charts into one figure and save/show."""
    fig = plt.figure(figsize=(18, 12), facecolor="#0f0f0f")
    fig.suptitle(
        "Tech Skills Demand Analyzer",
        fontsize=18, fontweight="bold", color="white", y=0.98
    )

    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])  # top-left:  top skills bar
    ax2 = fig.add_subplot(gs[0, 1])  # top-right: category donut
    ax3 = fig.add_subplot(gs[1, 0])  # bot-left:  top per category
    ax4 = fig.add_subplot(gs[1, 1])  # bot-right: heatmap by query

    plot_top_skills(ax1)
    plot_category_donut(ax2)
    plot_top_per_category(ax3)
    plot_skills_by_query(ax4)

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#0f0f0f")
    log.info(f"Dashboard saved to {output_path}")
    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_dashboard()

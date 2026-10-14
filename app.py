import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
from html import escape

# --- DATABASE SETUP ---
DB_NAME = "notion_tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            icon TEXT DEFAULT '📄',
            title TEXT NOT NULL,
            course TEXT,
            status TEXT NOT NULL DEFAULT 'To Do',
            priority TEXT DEFAULT 'Medium',
            impact TEXT NOT NULL DEFAULT 'Low',
            effort TEXT NOT NULL DEFAULT 'Low',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # New table for Feynman Technique notes
    c.execute('''
        CREATE TABLE IF NOT EXISTS feynman_notes (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            explanation TEXT,
            gaps TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    existing_columns = {
        row[1] for row in c.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "impact" not in existing_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN impact TEXT NOT NULL DEFAULT 'Low'")
    if "effort" not in existing_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN effort TEXT NOT NULL DEFAULT 'Low'")
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM tasks ORDER BY created_at DESC", conn)
    conn.close()
    return df

def fetch_feynman_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM feynman_notes ORDER BY created_at DESC", conn)
    conn.close()
    return df

# --- INITIALIZATION ---
st.set_page_config(page_title="Notion HQ", page_icon="📓", layout="wide")
init_db()

# --- CSS FOR NOTION AESTHETICS ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff !important;
    }
    
    /* Main Background */
    [data-testid="stAppViewContainer"] {
        background: #ffffff;
    }
    
    /* Header transparency */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Titles */
    .notion-title {
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: #171717;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .subtitle {
        color: #737373;
        font-size: 1rem;
    }

    /* Minimalist Kanban Card */
    .kanban-card {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 8px;
        color: #171717;
    }
    
    .kanban-card:hover {
        background: #fafafa;
    }
    
    .card-title {
        font-weight: 500;
        font-size: 14px;
        margin-bottom: 8px;
        color: #171717;
    }
    
    /* Minimalist Tags */
    .tag {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        margin-right: 6px;
        margin-bottom: 6px;
        background: #f5f5f5;
        color: #525252;
        border: 1px solid #e5e5e5;
    }
    
    /* Column Headers */
    .kanban-col-header {
        font-weight: 500;
        font-size: 14px;
        color: #404040;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e5e5e5;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .count-badge {
        background: #f5f5f5; 
        padding: 2px 8px; 
        border-radius: 12px; 
        font-size: 12px;
        color: #525252;
        border: 1px solid #e5e5e5;
    }

    /* Buttons */
    .stButton > button {
        background: #ffffff !important;
        border: 1px solid #e5e5e5 !important;
        color: #525252 !important;
        border-radius: 4px !important;
        padding: 2px !important;
        min-height: 24px;
        font-size: 12px;
    }
    
    .stButton > button:hover {
        background: #f5f5f5 !important;
        color: #171717 !important;
    }

    /* Fresh workspace refresh */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 92% 0%, rgba(224, 242, 254, 0.75), transparent 28rem),
            #f7f9fc;
    }

    .block-container {
        max-width: 1380px;
        padding: 3.5rem 3rem 4rem;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 249, 252, 0.75) !important;
    }

    .workspace-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.8rem;
    }

    .workspace-kicker {
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .workspace-title {
        color: #0f172a;
        font-size: clamp(2rem, 4vw, 3.15rem);
        font-weight: 750;
        letter-spacing: -0.055em;
        line-height: 1;
        margin: 0;
    }

    .workspace-subtitle {
        color: #64748b;
        font-size: 0.96rem;
        margin: 0.8rem 0 0;
    }

    .date-pill {
        border: 1px solid #dbe4ef;
        background: rgba(255,255,255,0.8);
        border-radius: 999px;
        color: #475569;
        font-size: 0.78rem;
        padding: 0.55rem 0.85rem;
        white-space: nowrap;
    }

    .metric-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        min-height: 7rem;
        box-shadow: 0 8px 28px rgba(15, 23, 42, 0.035);
    }

    .metric-label {
        color: #64748b;
        font-size: 0.74rem;
        font-weight: 650;
        letter-spacing: 0.02em;
    }

    .metric-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 750;
        letter-spacing: -0.05em;
        margin-top: 0.45rem;
    }

    .metric-detail {
        color: #94a3b8;
        font-size: 0.72rem;
        margin-top: 0.25rem;
    }

    .section-heading {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 1.9rem 0 0.8rem;
    }

    .kanban-card {
        border-radius: 12px;
        border-color: #e2e8f0;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.025);
        padding: 14px;
    }

    .kanban-card:hover {
        border-color: #bfdbfe;
        background: #ffffff;
        box-shadow: 0 8px 22px rgba(59, 130, 246, 0.08);
    }

    .kanban-col-header {
        border-bottom-color: #dbe4ef;
        color: #334155;
        font-weight: 700;
    }

    .count-badge {
        background: #eff6ff;
        border-color: #dbeafe;
        color: #2563eb;
    }

    div[data-testid="stTabs"] button {
        color: #64748b;
        font-weight: 650;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #2563eb;
    }

    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.72);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        margin-top: 1.25rem;
        margin-bottom: 1.5rem;
    }

    div[data-testid="stTabs"] {
        margin-top: 1.25rem;
    }

    @media (max-width: 700px) {
        .block-container { padding: 2rem 1rem 3rem; }
        .workspace-header { align-items: flex-start; flex-direction: column; }
    }
</style>
""", unsafe_allow_html=True)

df = fetch_data()

# Workspace overview and quick filters
today_label = datetime.now().strftime("%d %b %Y")
total_tasks = len(df)
done_tasks = int((df["status"] == "Done").sum()) if not df.empty else 0
active_tasks_count = total_tasks - done_tasks
high_priority_count = int(df["priority"].isin(["High", "Critical"]).sum()) if not df.empty else 0
progress = round((done_tasks / total_tasks) * 100) if total_tasks else 0

st.markdown(f"""
<div class="workspace-header">
    <div>
        <div class="workspace-kicker">Personal productivity space</div>
        <h1 class="workspace-title">Fransisca's Workspace</h1>
        <p class="workspace-subtitle">Satu tempat untuk melihat, memprioritaskan, dan menyelesaikan tugasmu.</p>
    </div>
    <div class="date-pill">Today · {today_label}</div>
</div>
""", unsafe_allow_html=True)

metric_cols = st.columns(4)
metrics = [
    ("Total tugas", total_tasks, "Semua item tersimpan"),
    ("Sedang berjalan", active_tasks_count, "Belum selesai"),
    ("Prioritas tinggi", high_priority_count, "Perlu perhatian"),
    ("Progress selesai", f"{progress}%", f"{done_tasks} dari {total_tasks} tugas"),
]
for metric_col, (label, value, detail) in zip(metric_cols, metrics):
    with metric_col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div><div class="metric-detail">{detail}</div></div>',
            unsafe_allow_html=True,
        )

# Add Task using Expander
with st.expander("＋  Add a new task", expanded=False):
    with st.form("new_task_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="e.g. Read Chapter 4 / Tugas Makalah")

        
        c3, c4, c5, c6 = st.columns(4)
        course = c3.text_input("Course", placeholder="Mata Kuliah")
        status = c4.selectbox("Status", ["To Do", "In Progress", "Done"])
        priority = c5.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        due = c6.date_input("Due Date", value=None)
        impact_col, effort_col = st.columns(2)
        impact = impact_col.selectbox("Impact", ["Low", "High"])
        effort = effort_col.selectbox("Effort", ["Low", "High"])
        
        if st.form_submit_button("Create Page (Save)"):
            if title.strip():
                task_id = str(uuid.uuid4())
                run_query("""
                    INSERT INTO tasks (id, icon, title, course, status, priority, impact, effort, due_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, '', title.strip(), course.strip() if course else None, status, priority, impact, effort, due))

                st.rerun()

visible_df = df.copy()
# Board dan Matrix selalu membaca snapshot yang sama pada setiap rerun.
board_tasks = visible_df
matrix_tasks = visible_df[visible_df["status"] != "Done"].copy()
tab_board, tab_eisenhower = st.tabs(["Board", "Eisenhower Matrix"])

# --- BOARD VIEW (KANBAN) ---
with tab_board:
    st.write("") 
    col1, col2, col3 = st.columns(3)
    
    statuses = [
        ("To Do", col1, "To Do"), 
        ("In Progress", col2, "In Progress"), 
        ("Done", col3, "Done")
    ]
    
    for stat_name, col, label in statuses:
        with col:
            tasks = board_tasks[board_tasks['status'] == stat_name]
            st.markdown(f'''
                <div class="kanban-col-header">
                    {label} <span class="count-badge">{len(tasks)}</span>
                </div>
            ''', unsafe_allow_html=True)
            
            for _, row in tasks.iterrows():
                # Badges
                p_class = f"tag-{row['priority'].lower()}"
                badges = (
                    f'<span class="tag {p_class}">{escape(str(row["priority"]))}</span>'
                    f'<span class="tag">Impact: {escape(str(row["impact"]))}</span>'
                    f'<span class="tag">Effort: {escape(str(row["effort"]))}</span>'
                )
                if row['course']:
                    badges += f'<span class="tag">📚 {row["course"]}</span>'
                if row['due_date']:
                    badges += f'<span class="tag">📅 {row["due_date"]}</span>'
                
                # Card HTML
                card_html = f"""
                <div class="kanban-card">
                    <div class="card-title">{escape(str(row['title']))}</div>
                    <div>{badges}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Action Buttons
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2])
                with btn_col1:
                    if stat_name != "To Do" and st.button("⏪", key=f"prev_{row['id']}", help="Move Left"):
                        new_stat = "To Do" if stat_name == "In Progress" else "In Progress"
                        run_query("UPDATE tasks SET status = ? WHERE id = ?", (new_stat, row['id']))
                        st.rerun()
                with btn_col2:
                    if stat_name != "Done" and st.button("⏩", key=f"next_{row['id']}", help="Move Right"):
                        new_stat = "In Progress" if stat_name == "To Do" else "Done"
                        run_query("UPDATE tasks SET status = ? WHERE id = ?", (new_stat, row['id']))
                        st.rerun()
                with btn_col3:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Delete Task"):
                        run_query("DELETE FROM tasks WHERE id = ?", (row['id'],))
                        st.rerun()

# --- IMPACT / EFFORT MATRIX ---
with tab_eisenhower:
    st.markdown('<div style="background: rgba(255,255,255,0.05); border-left: 4px solid #c084fc; padding: 15px; border-radius: 8px; margin-bottom: 20px;"><strong>🧭 Impact × Effort Matrix</strong><br>Gunakan matriks ini untuk menemukan tugas berdampak tinggi dengan usaha rendah terlebih dahulu.</div>', unsafe_allow_html=True)
    
    active_tasks = matrix_tasks.copy()
    
    def get_quadrant(row):
        is_high_impact = str(row["impact"]).strip() == "High"
        is_high_effort = str(row["effort"]).strip() == "High"

        if is_high_impact and not is_high_effort:
            return 1 # Do First
        elif is_high_impact and is_high_effort:
            return 2 # Schedule
        elif not is_high_impact and not is_high_effort:
            return 3 # Delegate
        else:
            return 4 # Don't Do
            
    if not active_tasks.empty:
        active_tasks['quadrant'] = active_tasks.apply(get_quadrant, axis=1)
    else:
        active_tasks['quadrant'] = []
        
    def render_quadrant(tasks_q, color, title):
        st.markdown(f'<div style="background: #ffffff; border-top: 3px solid {color}; border-left: 1px solid #e5e5e5; border-right: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; padding: 16px; border-radius: 6px; height: 100%;"><h5 style="color: {color}; margin-top:0; font-weight: 500; font-size: 14px;">{title}</h5>', unsafe_allow_html=True)
        if tasks_q.empty:
            st.write("<span style='color: #64748b; font-size: 14px;'>Kosong</span>", unsafe_allow_html=True)
        else:
            for _, r in tasks_q.iterrows():
                due_badge = f'<span class="tag">📅 {r["due_date"]}</span>' if r["due_date"] else ""
                axis_badges = (
                    f'<span class="tag">Impact: {escape(str(r["impact"]))}</span>'
                    f'<span class="tag">Effort: {escape(str(r["effort"]))}</span>'
                )
                st.markdown(f'<div class="kanban-card" style="margin-bottom: 8px;"><div class="card-title" style="margin-bottom: 2px;">{escape(str(r["title"]))}</div><div style="font-size: 11px;">{axis_badges}{due_badge}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    st.write("") # spacing
    col3, col4 = st.columns(2)
    
    q1 = active_tasks[active_tasks['quadrant'] == 1] if not active_tasks.empty else pd.DataFrame()
    q2 = active_tasks[active_tasks['quadrant'] == 2] if not active_tasks.empty else pd.DataFrame()
    q3 = active_tasks[active_tasks['quadrant'] == 3] if not active_tasks.empty else pd.DataFrame()
    q4 = active_tasks[active_tasks['quadrant'] == 4] if not active_tasks.empty else pd.DataFrame()
    
    with col1:
        render_quadrant(q1, "#22c55e", "⚡ Quick Wins (Impact Tinggi · Effort Rendah)")
    with col2:
        render_quadrant(q2, "#3b82f6", "🚀 Major Projects (Impact Tinggi · Effort Tinggi)")
    with col3:
        render_quadrant(q3, "#f59e0b", "🧩 Fill-ins (Impact Rendah · Effort Rendah)")
    with col4:
        render_quadrant(q4, "#94a3b8", "⏳ Time Wasters (Impact Rendah · Effort Tinggi)")

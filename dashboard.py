import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, glob

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Training Analytics Dashboard", page_icon="📊", layout="wide")

# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        color: white;
    }
    .stMetric label {
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }
    h1 {
        color: white;
        text-align: center;
        font-size: 48px;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    h2, h3 {
        color: white;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------
st.title("🎯 Training Analytics Dashboard")
st.markdown("<h3 style='text-align: center; color: white;'>Comprehensive Performance Insights & Analytics</h3>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------
# AUTO-LOAD LATEST CSV FILES
# ---------------------------------------------------------
DATA_DIR = "./"  # folder where files are stored

def get_latest_file(pattern):
    files = glob.glob(os.path.join(DATA_DIR, pattern))
    return max(files, key=os.path.getctime) if files else None

breaks_file = get_latest_file("teams_breaks_*.csv")
sessions_file = get_latest_file("teams_sessions_*.csv")
tasks_file = get_latest_file("teams_tasks_*.csv")

st.sidebar.markdown("### 📁 Auto-Detected Latest Files")
st.sidebar.write(f"**Breaks File:** {os.path.basename(breaks_file) if breaks_file else '❌ Not Found'}")
st.sidebar.write(f"**Sessions File:** {os.path.basename(sessions_file) if sessions_file else '❌ Not Found'}")
st.sidebar.write(f"**Tasks File:** {os.path.basename(tasks_file) if tasks_file else '❌ Not Found'}")

# ---------------------------------------------------------
# MAIN DASHBOARD LOGIC
# ---------------------------------------------------------
if breaks_file and sessions_file and tasks_file:
    try:
        # === READ FILES ===
        breaks_df = pd.read_csv(breaks_file)
        sessions_df = pd.read_csv(sessions_file)
        tasks_df = pd.read_csv(tasks_file)

        # === CLEAN & SUMMARIZE ===
        # Breaks
        breaks_summary = breaks_df.groupby("Trainer Name").agg({
            "Break Count": "sum",
            "Duration (min)": "sum"
        }).reset_index().rename(columns={"Duration (min)": "Break_Duration"})

        # Sessions
        sessions_summary = sessions_df.groupby("Trainer Name").agg({
            "Finished Count": "sum",
            "Duration (min)": "sum"
        }).reset_index().rename(columns={
            "Finished Count": "Session_Count",
            "Duration (min)": "Session_Duration"
        })

        # Tasks (excluding login/logout)
        tasks_filtered = tasks_df[~tasks_df["Task"].str.lower().isin(["login", "logout"])].copy()
        tasks_summary = tasks_filtered.groupby("Trainer Name").agg({
            "Task Count": "sum",
            "Duration (min)": "sum"
        }).reset_index().rename(columns={
            "Duration (min)": "Task_Duration"
        })

        # === MERGE ALL DATA ===
        merged_df = pd.merge(sessions_summary, breaks_summary, on="Trainer Name", how="outer")
        merged_df = pd.merge(merged_df, tasks_summary, on="Trainer Name", how="outer").fillna(0)
        merged_df.rename(columns={"Trainer Name": "Trainer"}, inplace=True)

        # === CALCULATED FIELDS ===
        merged_df["Total_Sessions"] = merged_df["Session_Count"] + merged_df["Task Count"]
        merged_df["Total_Duration"] = merged_df["Session_Duration"] + merged_df["Task_Duration"]
        merged_df["Avg_Session_Duration"] = merged_df["Session_Duration"] / merged_df["Session_Count"].replace(0, 1)

        # === COLORS ===
        gradient_colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a', '#fee140', '#30cfd0']

        # === KPIs ===
        total_sessions = int(merged_df["Total_Sessions"].sum())
        total_tasks = int(merged_df["Task Count"].sum())
        total_trainers = len(merged_df[merged_df["Total_Sessions"] > 0])
        total_duration = int(merged_df["Total_Duration"].sum())
        top_performer = merged_df.loc[merged_df["Total_Sessions"].idxmax()]

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("🎯 Total Sessions", total_sessions)
        with col2: st.metric("📋 Total Tasks", total_tasks)
        with col3: st.metric("👥 Active Trainers", total_trainers)
        with col4:
            st.metric("🏆 Top Performer", top_performer["Trainer"])
            st.caption(f"⭐ {int(top_performer['Total_Sessions'])} sessions")
        with col5:
            st.metric("⏱️ Total Duration", f"{total_duration} min")
            st.caption(f"🕐 {total_duration//60}h {total_duration%60}m")

        st.markdown("<br><br>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # CHARTS
        # ---------------------------------------------------------
        col1, col2 = st.columns(2)

        # === BREAK DURATION ===
        with col1:
            st.markdown("<h2>📊 Break Duration by Trainer</h2>", unsafe_allow_html=True)
            breaks_sorted = breaks_summary.sort_values("Break_Duration", ascending=False)
            fig1 = go.Figure(go.Bar(
                x=breaks_sorted["Trainer Name"], y=breaks_sorted["Break_Duration"],
                marker=dict(color=breaks_sorted["Break_Duration"],
                            colorscale=[[0, "#667eea"], [0.5, "#764ba2"], [1, "#f093fb"]],
                            line=dict(color='white', width=2)),
                text=breaks_sorted["Break_Duration"],
                textposition='outside',
                textfont=dict(size=12, color='white', family='Arial Black')
            ))
            fig1.update_layout(
                height=450, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(tickangle=-45, linecolor='white', title='Trainer Name'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)', title='Break Duration (min)')
            )
            st.plotly_chart(fig1, use_container_width=True)

        # === TASK COUNT ===
        with col2:
            st.markdown("<h2>📈 Task Count by Trainer</h2>", unsafe_allow_html=True)
            tasks_sorted = tasks_summary.sort_values("Task Count", ascending=True)
            fig2 = go.Figure(go.Bar(
                y=tasks_sorted["Trainer Name"], x=tasks_sorted["Task Count"], orientation='h',
                marker=dict(color=tasks_sorted["Task Count"],
                            colorscale=[[0, "#4facfe"], [0.5, "#00f2fe"], [1, "#43e97b"]],
                            line=dict(color='white', width=2)),
                text=tasks_sorted["Task Count"],
                textposition='outside',
                textfont=dict(size=12, color='white', family='Arial Black')
            ))
            fig2.update_layout(
                height=450, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.2)', title='Number of Tasks'),
                yaxis=dict(linecolor='white', title='Trainer Name')
            )
            st.plotly_chart(fig2, use_container_width=True)

        # === SESSIONS (STACKED) + TASK DURATION ===
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("<h2>📊 Total Sessions by Trainer (Sessions + Tasks)</h2>", unsafe_allow_html=True)
            merged_sorted = merged_df.sort_values("Total_Sessions", ascending=False)
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=merged_sorted["Trainer"], y=merged_sorted["Session_Count"],
                                  name='Sessions', marker_color='#667eea', text=merged_sorted["Session_Count"],
                                  textposition='inside', textfont=dict(color='white')))
            fig3.add_trace(go.Bar(x=merged_sorted["Trainer"], y=merged_sorted["Task Count"],
                                  name='Tasks', marker_color='#43e97b', text=merged_sorted["Task Count"],
                                  textposition='inside', textfont=dict(color='white')))
            fig3.update_layout(
                barmode='stack', height=450, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                xaxis=dict(tickangle=-45, linecolor='white', title='Trainer Name'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)', title='Total Count'),
                legend=dict(orientation="h", y=1.02, x=1)
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.markdown("<h2>📉 Task Duration by Trainer</h2>", unsafe_allow_html=True)
            tasks_duration_sorted = tasks_summary.sort_values("Task_Duration", ascending=False)
            fig4 = go.Figure(go.Bar(
                x=tasks_duration_sorted["Trainer Name"], y=tasks_duration_sorted["Task_Duration"],
                marker=dict(color=tasks_duration_sorted["Task_Duration"],
                            colorscale=[[0, "#fa709a"], [0.5, "#fee140"], [1, "#30cfd0"]],
                            line=dict(color='white', width=2)),
                text=tasks_duration_sorted["Task_Duration"],
                textposition='outside',
                textfont=dict(size=12, color='white', family='Arial Black')
            ))
            fig4.update_layout(
                height=450, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(tickangle=-45, linecolor='white', title='Trainer Name'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)', title='Task Duration (min)')
            )
            st.plotly_chart(fig4, use_container_width=True)

        # === DATA TABLE ===
        st.markdown("<br><h2 style='text-align: center;'>📋 Detailed Performance Data</h2>", unsafe_allow_html=True)
        display_df = merged_df[['Trainer', 'Session_Count', 'Task Count', 'Total_Sessions',
                                'Session_Duration', 'Task_Duration', 'Total_Duration',
                                'Avg_Session_Duration', 'Break_Duration']]
        display_df.columns = ['Trainer', 'Sessions', 'Tasks', 'Total Sessions',
                              'Session Duration (min)', 'Task Duration (min)',
                              'Total Duration (min)', 'Avg Session (min)', 'Break Duration (min)']
        st.dataframe(display_df.sort_values('Total Sessions', ascending=False), use_container_width=True, height=400)

        st.markdown("---")
        st.markdown("<p style='text-align:center; color:white;'>Dashboard includes merged data from Sessions, Tasks, and Breaks</p>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")

else:
    st.markdown(f"""
    <div style='text-align:center; padding:50px; color:white;'>
        <h2>📂 Waiting for latest CSV files in <b>{DATA_DIR}</b></h2>
        <p style='font-size:18px;'>
        1. teams_breaks_YYYYMMDD_HHMMSS.csv<br>
        2. teams_sessions_YYYYMMDD_HHMMSS.csv<br>
        3. teams_tasks_YYYYMMDD_HHMMSS.csv
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# MENTENOVA DASHBOARD — app.py
# Team analytics dashboard powered by Streamlit + Plotly
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

# ============================================================
# 1. CONFIG
# ============================================================
st.set_page_config(
    page_title="Mentenova Analytics",
    page_icon="logo.png",      # uses your logo as the browser tab icon
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Mentenova brand colors ----
COLORS = {
    'glossy_navy':    '#112230',
    'mentenova_blue': '#7993B2',
    'chestnut_brown': '#AF4723',
    'stone_grey':     '#E0D8D1',
    'flash_red':      '#FF3E3E',
    'white':          '#FFFFFF',
    'light_navy':     '#1A3346',
    'medium_navy':    '#2A4A66',
    'light_stone':    '#F5F2EF',
}

PERSON_COLORS = {
    "Yanni Yang": COLORS['chestnut_brown'],
    "Amy":        COLORS['mentenova_blue'],
    "Neo":        COLORS['medium_navy'],
    "Bonnita":    COLORS['flash_red'],
    "Erik":       COLORS['light_navy'],
}

BUCKET_COLORS = {
    "Reporting Cycle":       COLORS['chestnut_brown'],
    "Core Investment Work":  COLORS['mentenova_blue'],
    "Meetings":              COLORS['flash_red'],
    "Internal Ops":          COLORS['medium_navy'],
    "Client Programmes":     COLORS['stone_grey'],
}

# ============================================================
# 2. DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    """Load and prepare the activities DataFrame."""
    df = pd.read_csv("data/activities.csv", parse_dates=["start", "end", "date"])
    df["year_month"] = pd.to_datetime(df["start"]).dt.strftime("%Y-%m")
    df["quarter"] = df["year_month"].apply(
        lambda ym: f"{ym.split('-')[0]}-Q{(int(ym.split('-')[1]) - 1) // 3 + 1}"
    )
    # Clean nulls
    df["note"] = df["note"].fillna("(no note)").astype(str)
    df["category"] = df["category"].fillna("Other").astype(str)
    df["bucket"] = df["bucket"].fillna("Internal Ops").astype(str)
    df["user_name"] = df["user_name"].fillna("Unknown").astype(str)
    return df

df = load_data()

# ============================================================
# 3. SIDEBAR — Filters
# ============================================================
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("🎛️ Filters")
st.sidebar.markdown("---")

min_date = df["date"].min()
max_date = df["date"].max()

date_range = st.sidebar.date_input(
    "📅 Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if len(date_range) == 2:
    start_filter, end_filter = date_range
else:
    start_filter, end_filter = min_date, max_date

all_users = sorted(df["user_name"].unique())
selected_users = st.sidebar.multiselect(
    "👥 Team members",
    options=all_users,
    default=all_users,
)

all_buckets = sorted(df["bucket"].unique())
selected_buckets = st.sidebar.multiselect(
    "📊 Business buckets",
    options=all_buckets,
    default=all_buckets,
)

all_cats = sorted(df["category"].unique())
selected_cats = st.sidebar.multiselect(
    "📁 Categories",
    options=all_cats,
    default=all_cats,
)

st.sidebar.markdown("---")
st.sidebar.caption(f"📊 Total records: {len(df):,}")

# ============================================================
# 4. APPLY FILTERS
# ============================================================
mask = (
    (df["date"] >= pd.Timestamp(start_filter)) &
    (df["date"] <= pd.Timestamp(end_filter)) &
    (df["user_name"].isin(selected_users)) &
    (df["bucket"].isin(selected_buckets)) &
    (df["category"].isin(selected_cats))
)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("⚠️ No data matches your filters. Try widening the selection.")
    st.stop()

# ============================================================
# 5. HEADER + KPI CARDS
# ============================================================

# Logo + title row
logo_col, title_col = st.columns([1, 8])

with logo_col:
    st.image("logo.png", width=90)

with title_col:
    st.markdown(
        f"<h1 style='margin:0; padding-top:20px; color:{COLORS['glossy_navy']};'>"
        f"Mentenova — Team Analytics Dashboard</h1>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"<p style='color:{COLORS['glossy_navy']}; margin-top:0;'>"
    f"<b>Period:</b> {start_filter.strftime('%d %b %Y')} → {end_filter.strftime('%d %b %Y')}"
    f"</p>",
    unsafe_allow_html=True,
)

# KPI cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("⏱️ Total Hours", f"{filtered['duration_hr'].sum():,.1f}")
with col2:
    st.metric("📝 Activities", f"{len(filtered):,}")
with col3:
    st.metric("👥 Active Members", f"{filtered['user_name'].nunique()}")
with col4:
    st.metric("📁 Categories", f"{filtered['category'].nunique()}")

st.markdown("---")

# ============================================================
# 6. TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Reporting Cycle",
    "👥 People",
    "🔍 Drill-Down",
])

# ============================================================
# TAB 1 — Overview
# ============================================================
with tab1:
    col_left, col_right = st.columns([1.4, 1])
    
    with col_left:
        monthly_bucket = (filtered
                          .pivot_table(index="year_month",
                                       columns="bucket",
                                       values="duration_hr",
                                       aggfunc="sum",
                                       fill_value=0))
        fig = px.bar(
            monthly_bucket,
            barmode="stack",
            title="Monthly Hours by Business Bucket",
            labels={"value": "Hours", "year_month": "Month", "bucket": "Bucket"},
            color_discrete_map=BUCKET_COLORS,
        )
        fig.update_layout(
            plot_bgcolor=COLORS['white'],
            paper_bgcolor=COLORS['white'],
            font_color=COLORS['glossy_navy'],
            title_font_color=COLORS['glossy_navy'],
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        bucket_totals = filtered.groupby("bucket")["duration_hr"].sum().reset_index()
        fig = px.pie(
            bucket_totals,
            values="duration_hr",
            names="bucket",
            hole=0.45,
            title="Time Distribution by Bucket",
            color="bucket",
            color_discrete_map=BUCKET_COLORS,
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            plot_bgcolor=COLORS['white'],
            paper_bgcolor=COLORS['white'],
            font_color=COLORS['glossy_navy'],
            title_font_color=COLORS['glossy_navy'],
            height=450,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    cat_totals = (filtered.groupby("category")["duration_hr"]
                  .sum()
                  .sort_values(ascending=True)
                  .reset_index())
    fig = px.bar(
        cat_totals,
        x="duration_hr",
        y="category",
        orientation="h",
        title="Hours by Category",
        labels={"duration_hr": "Hours", "category": ""},
        color_discrete_sequence=[COLORS['mentenova_blue']],
    )
    fig.update_traces(
        text=[f"{h:.0f} h" for h in cat_totals["duration_hr"]],
        textposition="outside",
        marker_line_color=COLORS['glossy_navy'],
        marker_line_width=0.5,
    )
    fig.update_layout(
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font_color=COLORS['glossy_navy'],
        title_font_color=COLORS['glossy_navy'],
        height=max(400, len(cat_totals) * 28),
        showlegend=False,
        xaxis=dict(range=[0, cat_totals["duration_hr"].max() * 1.2]),
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 2 — Reporting Cycle
# ============================================================
with tab2:
    reporting_cats = ["Monthly Report", "Quarterly Report",
                      "Reporting Automation", "Reporting (General)"]
    
    rep_df = filtered[filtered["category"].isin(reporting_cats)]
    
    if rep_df.empty:
        st.info("ℹ️ No reporting-cycle data in the current filter selection.")
    else:
        monthly_rep = (rep_df
                       .pivot_table(index="year_month",
                                    columns="category",
                                    values="duration_hr",
                                    aggfunc="sum",
                                    fill_value=0))
        fig = px.bar(
            monthly_rep,
            barmode="group",
            title="Reporting Cycle — Monthly Detail",
            labels={"value": "Hours", "year_month": "Month", "category": "Report Type"},
            color_discrete_sequence=[
                COLORS['chestnut_brown'],
                COLORS['mentenova_blue'],
                COLORS['medium_navy'],
                COLORS['stone_grey'],
            ],
        )
        fig.update_layout(
            plot_bgcolor=COLORS['white'],
            paper_bgcolor=COLORS['white'],
            font_color=COLORS['glossy_navy'],
            title_font_color=COLORS['glossy_navy'],
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        for col, cat_name, color in [
            (col1, "Monthly Report", COLORS['chestnut_brown']),
            (col2, "Quarterly Report", COLORS['mentenova_blue']),
        ]:
            with col:
                sub = rep_df[rep_df["category"] == cat_name]
                if sub.empty:
                    st.info(f"No {cat_name} data.")
                    continue
                
                top = (sub.groupby("note")
                       .agg(hours=("duration_hr", "sum"),
                            activities=("activity_id", "count"))
                       .sort_values("hours", ascending=False)
                       .head(10)
                       .sort_values("hours")
                       .reset_index())
                
                fig = px.bar(
                    top,
                    x="hours",
                    y="note",
                    orientation="h",
                    title=f"Top Clients — {cat_name}",
                    labels={"hours": "Hours", "note": ""},
                    color_discrete_sequence=[color],
                    hover_data={"activities": True},
                )
                fig.update_traces(
                    text=[f"{h:.1f} h" for h in top["hours"]],
                    textposition="outside",
                    marker_line_color=COLORS['glossy_navy'],
                    marker_line_width=0.5,
                )
                fig.update_layout(
                    plot_bgcolor=COLORS['white'],
                    paper_bgcolor=COLORS['white'],
                    font_color=COLORS['glossy_navy'],
                    title_font_color=COLORS['glossy_navy'],
                    height=420,
                    showlegend=False,
                    xaxis=dict(range=[0, top["hours"].max() * 1.3]),
                )
                st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 3 — People
# ============================================================
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        person_totals = (filtered.groupby("user_name")["duration_hr"]
                         .sum()
                         .sort_values(ascending=True)
                         .reset_index())
        fig = px.bar(
            person_totals,
            x="duration_hr",
            y="user_name",
            orientation="h",
            title="Total Hours per Team Member",
            labels={"duration_hr": "Hours", "user_name": ""},
            color="user_name",
            color_discrete_map=PERSON_COLORS,
        )
        fig.update_traces(
            text=[f"{h:.0f} h" for h in person_totals["duration_hr"]],
            textposition="outside",
        )
        fig.update_layout(
            plot_bgcolor=COLORS['white'],
            paper_bgcolor=COLORS['white'],
            font_color=COLORS['glossy_navy'],
            title_font_color=COLORS['glossy_navy'],
            height=400,
            showlegend=False,
            xaxis=dict(range=[0, person_totals["duration_hr"].max() * 1.2]),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        meetings = filtered[filtered["bucket"] == "Meetings"]
        if not meetings.empty:
            meet_per_user = (meetings.pivot_table(
                index="user_name",
                columns="category",
                values="duration_hr",
                aggfunc="sum",
                fill_value=0
            ).reset_index())
            
            fig = px.bar(
                meet_per_user,
                x="user_name",
                y=[c for c in meet_per_user.columns if c != "user_name"],
                title="Meeting Hours per Person (Internal vs External)",
                labels={"value": "Hours", "user_name": "", "variable": "Type"},
                barmode="group",
                color_discrete_map={
                    "Internal Meeting": COLORS['flash_red'],
                    "External Meeting": COLORS['mentenova_blue'],
                },
            )
            fig.update_layout(
                plot_bgcolor=COLORS['white'],
                paper_bgcolor=COLORS['white'],
                font_color=COLORS['glossy_navy'],
                title_font_color=COLORS['glossy_navy'],
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No meeting data in filter selection.")
    
    st.markdown("### Category × Person Heatmap")
    top_cats = (filtered.groupby("category")["duration_hr"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .index.tolist())
    
    heat = (filtered[filtered["category"].isin(top_cats)]
            .pivot_table(index="category",
                         columns="user_name",
                         values="duration_hr",
                         aggfunc="sum",
                         fill_value=0))
    heat = heat.loc[heat.sum(axis=1).sort_values(ascending=False).index]
    
    fig = px.imshow(
        heat,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale=[
            [0, COLORS['light_stone']],
            [0.5, COLORS['mentenova_blue']],
            [1, COLORS['glossy_navy']],
        ],
        title="Category × Person — Hours Heatmap",
        labels={"x": "", "y": "", "color": "Hours"},
    )
    fig.update_layout(
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font_color=COLORS['glossy_navy'],
        title_font_color=COLORS['glossy_navy'],
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 4 — Drill-Down
# ============================================================
with tab4:
    st.markdown("### 🔍 Explore any category in detail")
    
    drill_cat = st.selectbox(
        "Select a category",
        options=sorted(filtered["category"].unique()),
    )
    
    sub = filtered[filtered["category"] == drill_cat]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Hours", f"{sub['duration_hr'].sum():,.1f}")
    col2.metric("Activities", f"{len(sub):,}")
    col3.metric("Team members", f"{sub['user_name'].nunique()}")
    
    top_notes = (sub.groupby("note")
                 .agg(hours=("duration_hr", "sum"),
                      activities=("activity_id", "count"),
                      users=("user_name", "nunique"))
                 .sort_values("hours", ascending=False)
                 .head(15)
                 .sort_values("hours")
                 .reset_index())
    
    fig = px.bar(
        top_notes,
        x="hours",
        y="note",
        orientation="h",
        title=f"Top 15 Notes — {drill_cat}",
        labels={"hours": "Hours", "note": "", "activities": "Activities"},
        color_discrete_sequence=[COLORS['medium_navy']],
        hover_data={"activities": True, "users": True},
    )
    fig.update_traces(
        text=[f"{h:.1f} h" for h in top_notes["hours"]],
        textposition="outside",
    )
    fig.update_layout(
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font_color=COLORS['glossy_navy'],
        title_font_color=COLORS['glossy_navy'],
        height=max(400, len(top_notes) * 28),
        showlegend=False,
        xaxis=dict(range=[0, top_notes["hours"].max() * 1.25]),
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📋 View raw activity data"):
        st.dataframe(
            sub[["user_name", "date", "category", "note",
                 "duration_min", "offline"]]
            .sort_values("date", ascending=False)
            .head(200),
            use_container_width=True,
        )
    
    csv = sub.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Download {drill_cat} data (CSV)",
        data=csv,
        file_name=f"mentenova_{drill_cat.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    f"📊 Mentenova Analytics · "
    f"Data source: Scrin.io · "
    f"Last update: {pd.Timestamp.now().strftime('%d %b %Y %H:%M')}"
)
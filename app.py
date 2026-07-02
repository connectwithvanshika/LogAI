import streamlit as st
import pandas as pd
import json
import os
import re
import time
import ast
import plotly.express as px
from dotenv import load_dotenv
from groq import Groq

# Set page config
st.set_page_config(
    page_title="Dynatrace LogAI - RCA & Recommendations",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and modern SRE dashboard theme
st.markdown("""
<style>
    /* Dark aesthetic adjustments */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Card design */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #58a6ff;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Log console styling */
    .log-box {
        background-color: #0b0d10;
        border: 1px solid #21262d;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        padding: 12px;
        font-size: 0.85rem;
        overflow-x: auto;
        color: #58a6ff;
        white-space: pre-wrap;
    }
    
    .highlight-log {
        background-color: rgba(248, 81, 73, 0.15) !important;
        border-left: 4px solid #f85149 !important;
        color: #ff7b72;
    }
    
    /* Headers style */
    .section-header {
        border-bottom: 2px solid #21262d;
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 15px;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)

# Load environment
load_dotenv(override=True)

# Helper function to load data
@st.cache_data(show_spinner=False)
def load_contexts():
    contexts_path = "data/context/anomaly_context.json"
    if os.path.exists(contexts_path):
        with open(contexts_path, "r") as f:
            return json.load(f)
    return []

# Helper function to parse lists stored as strings in CSV
def safe_parse_list(val):
    if isinstance(val, list):
        return val
    if pd.isna(val) or not val:
        return []
    val_str = str(val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            return ast.literal_eval(val_str)
        except Exception:
            try:
                # Fallback to json replacement
                return json.loads(val_str.replace("'", '"'))
            except Exception:
                pass
    return [val_str]

# Load and merge data helper
def get_merged_rca_data(contexts, csv_path="outputs/root_cause_analysis.csv"):
    if not os.path.exists(csv_path):
        return pd.DataFrame()
        
    rca_df = pd.read_csv(csv_path)
    if rca_df.empty:
        return rca_df
        
    # Standardize column types
    rca_df["LogIndex"] = rca_df["LogIndex"].astype(int)
    
    # Check if context columns are missing and merge if necessary
    if "CurrentLog" not in rca_df.columns:
        contexts_df = pd.DataFrame(contexts)
        if not contexts_df.empty:
            contexts_df["LogIndex"] = contexts_df["LogIndex"].astype(int)
            contexts_df = contexts_df.rename(columns={"Severity": "OriginalSeverity"})
            rca_df = pd.merge(rca_df, contexts_df, on="LogIndex", how="inner")
            
    # Apply list parser to lists
    list_cols = ["ImmediateFixes", "PermanentFixes", "PreventiveMeasures", "Recommendations"]
    for col in list_cols:
        if col in rca_df.columns:
            rca_df[col] = rca_df[col].apply(safe_parse_list)
            
    return rca_df

# Streamlit App Logic
st.title("🚨 Dynatrace LogAI - RCA & Recommendations")
st.markdown("Automated Root Cause Analysis (RCA), Severity Estimation, and SRE/DevOps recommendations for system anomalies.")

# 1. Load Data
anomaly_contexts = load_contexts()
rca_df = get_merged_rca_data(anomaly_contexts)

# Sidebar Configuration
st.sidebar.title("🛠 Settings & Filters")

# API Configuration
groq_api_key = st.sidebar.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password")
model_choice = st.sidebar.selectbox("LLM Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"], index=0)

# Sidebar Filters
st.sidebar.subheader("🔍 Filters")
severity_filter = st.sidebar.multiselect(
    "AI Estimated Severity",
    options=["Critical", "High", "Medium", "Low"],
    default=[]
)

component_filter = st.sidebar.multiselect(
    "Component",
    options=sorted(list(set([c["Component"] for c in anomaly_contexts if "Component" in c]))) if anomaly_contexts else [],
    default=[]
)

search_query = st.sidebar.text_input("Search Logs", "")

# Filter Dataframe
filtered_df = rca_df.copy()
if not filtered_df.empty:
    if severity_filter:
        filtered_df = filtered_df[filtered_df["Severity"].isin(severity_filter)]
    if component_filter:
        filtered_df = filtered_df[filtered_df["Component"].isin(component_filter)]
    if search_query:
        filtered_df = filtered_df[filtered_df["CurrentLog"].str.contains(search_query, case=False, na=False) |
                                  filtered_df["RootCause"].str.contains(search_query, case=False, na=False)]

# Tabs Navigation
tab_dash, tab_viewer, tab_run = st.tabs([
    "📊 RCA Dashboard", 
    "🔍 Detailed Anomaly Inspector", 
    "⚙️ Run Live AI RCA"
])

# --- TAB 1: DASHBOARD ---
with tab_dash:
    if anomaly_contexts:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(anomaly_contexts)}</div>
                <div class="metric-label">Total Anomalies Detected</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(rca_df)}</div>
                <div class="metric-label">RCA Reports Generated</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            critical_count = len(rca_df[rca_df["Severity"] == "Critical"]) if not rca_df.empty else 0
            high_count = len(rca_df[rca_df["Severity"] == "High"]) if not rca_df.empty else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #ff7b72;">{critical_count + high_count}</div>
                <div class="metric-label">Critical / High Severity</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            avg_score = rca_df["AnomalyScore"].mean() if not rca_df.empty and "AnomalyScore" in rca_df.columns else 0.0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #ffca28;">{avg_score:.2f}</div>
                <div class="metric-label">Avg Anomaly Score</div>
            </div>
            """, unsafe_allow_html=True)
            
    if not filtered_df.empty:
        st.subheader("Visual Analysis")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig_sev = px.bar(
                filtered_df["Severity"].value_counts().reset_index(),
                x="Severity",
                y="count",
                title="AI Estimated Severity Distribution",
                labels={"count": "Number of Anomalies"},
                color="Severity",
                color_discrete_map={"Critical": "#ff4d4d", "High": "#ff8533", "Medium": "#ffcc00", "Low": "#33cc33"}
            )
            fig_sev.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_sev, use_container_width=True)
            
        with chart_col2:
            fig_comp = px.pie(
                filtered_df,
                names="Component",
                title="Anomalies by System Component",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_comp.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_comp, use_container_width=True)
            
        st.subheader("Analyzed Anomalies List")
        st.dataframe(
            filtered_df[[
                "LogIndex", "Severity", "RootCause", "Confidence", "Component", "AnomalyScore"
            ]],
            use_container_width=True,
            column_config={
                "LogIndex": st.column_config.NumberColumn("Anomaly ID", format="%d"),
                "AnomalyScore": st.column_config.NumberColumn("Score", format="%.4f")
            }
        )
    else:
        st.info("No analyzed anomalies found matching the selected filters. Please run RCA on new anomalies first.")

# --- TAB 2: DETAILED ANOMALY INSPECTOR ---
with tab_viewer:
    if not rca_df.empty:
        st.subheader("Detailed Root Cause Analysis Report")
        selected_idx = st.selectbox(
            "Select Anomaly Log ID", 
            options=rca_df["LogIndex"].tolist(),
            format_func=lambda x: f"Anomaly #{x} - {rca_df[rca_df['LogIndex'] == x]['RootCause'].values[0][:80]}..."
        )
        
        row = rca_df[rca_df["LogIndex"] == selected_idx].iloc[0]
        
        # Display Current Log
        st.markdown("<h4 class='section-header'>🚨 Anomalous Raw Log Message</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='log-box highlight-log'>{row['CurrentLog']}</div>", unsafe_allow_html=True)
        
        # Metadata Columns
        st.markdown("<h4 class='section-header'>📊 Analysis Metadata</h4>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Anomaly Score", f"{row.get('AnomalyScore', 0.0):.4f}")
        col2.metric("System Component", str(row.get("Component", "Unknown")))
        col3.metric("Original Severity", str(row.get("OriginalSeverity", "Unknown")))
        col4.metric("LLM Confidence", str(row.get("Confidence", "N/A")))
        
        # Root Cause and Reason
        col_rc, col_impact = st.columns(2)
        with col_rc:
            st.markdown("<h4 class='section-header'>🔍 Root Cause & Reason</h4>", unsafe_allow_html=True)
            st.markdown(f"**Root Cause:** {row['RootCause']}")
            st.markdown(f"**Reason:** {row['Reason']}")
        with col_impact:
            st.markdown("<h4 class='section-header'>💥 Severity & Impact</h4>", unsafe_allow_html=True)
            st.markdown(f"**AI Estimated Severity:** {row['Severity']}")
            st.markdown(f"**Business Impact:** {row['Impact']}")
            
        # Fixes & Recommendations Tabs
        st.markdown("<h4 class='section-header'>💡 Remediation & Recommendations</h4>", unsafe_allow_html=True)
        tabs_fixes = st.tabs(["🚑 Immediate Fixes", "🔧 Permanent Fixes", "🛡️ Preventive Measures", "📋 Recommendations"])
        
        with tabs_fixes[0]:
            fixes = row.get("ImmediateFixes", [])
            if fixes:
                for fix in fixes:
                    st.markdown(f"- 🔴 {fix}")
            else:
                st.write("No immediate fixes suggested.")
                
        with tabs_fixes[1]:
            perm_fixes = row.get("PermanentFixes", [])
            if perm_fixes:
                for fix in perm_fixes:
                    st.markdown(f"- ⚙️ {fix}")
            else:
                st.write("No permanent fixes suggested.")
                
        with tabs_fixes[2]:
            prev_measures = row.get("PreventiveMeasures", [])
            if prev_measures:
                for measure in prev_measures:
                    st.markdown(f"- 🛡️ {measure}")
            else:
                st.write("No preventive measures suggested.")
                
        with tabs_fixes[3]:
            recs = row.get("Recommendations", [])
            if recs:
                for rec in recs:
                    st.markdown(f"- 💡 {rec}")
            else:
                st.write("No specific recommendations provided.")
                
        # Nearby Logs context
        st.markdown("<h4 class='section-header'>📖 Context Window (Nearby Logs)</h4>", unsafe_allow_html=True)
        nearby_logs = row.get("NearbyLogs", [])
        if isinstance(nearby_logs, str):
            try:
                nearby_logs = ast.literal_eval(nearby_logs)
            except Exception:
                try:
                    nearby_logs = json.loads(nearby_logs)
                except Exception:
                    nearby_logs = [nearby_logs]
                    
        logs_html = "<div class='log-box'>"
        for l in nearby_logs:
            if l.strip() == row["CurrentLog"].strip():
                logs_html += f"<div style='background-color: rgba(248, 81, 73, 0.2); padding: 4px; border-left: 3px solid #f85149; font-weight: bold;'>{l}</div>"
            else:
                logs_html += f"<div style='padding: 2px;'>{l}</div>"
        logs_html += "</div>"
        st.markdown(logs_html, unsafe_allow_html=True)
        
    else:
        st.info("Run RCA on new anomalies to unlock the inspector.")

# --- TAB 3: RUN LIVE AI RCA ---
with tab_run:
    st.subheader("Execute On-Demand LLM Root Cause Analysis")
    st.markdown("Select any detected anomaly context and analyze it using the Groq API.")
    
    # Find unanalyzed log indexes
    analyzed_indexes = set(rca_df["LogIndex"].tolist()) if not rca_df.empty else set()
    unanalyzed_contexts = [c for c in anomaly_contexts if c["LogIndex"] not in analyzed_indexes]
    
    if unanalyzed_contexts:
        selected_context = st.selectbox(
            "Select Unanalyzed Anomaly Log ID",
            options=unanalyzed_contexts,
            format_func=lambda x: f"Anomaly #{x['LogIndex']} - Score: {x['AnomalyScore']:.4f} ({x['Component']})"
        )
        
        # Display selected context details
        st.markdown("##### Current Log to Analyze:")
        st.code(selected_context["CurrentLog"])
        
        st.markdown("##### Context Parameters:")
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"**Anomaly Score:** {selected_context['AnomalyScore']:.4f}")
        col2.write(f"**Component:** {selected_context['Component']}")
        col3.write(f"**Original Severity:** {selected_context['Severity']}")
        col4.write(f"**Authentication:** {'Success' if selected_context['AuthenticationSuccess'] else 'Failed'}")
        
        # Build prompt for debug
        def build_prompt_ui(context):
            return f"""
You are an expert Site Reliability Engineer (SRE), DevOps Engineer, and Production Support Specialist.
Analyze the following anomalous log and perform a comprehensive Root Cause Analysis (RCA).

Return ONLY valid JSON in the following format:
{{
    "RootCause": "...",
    "Reason": "...",
    "Severity": "Critical | High | Medium | Low",
    "Impact": "...",
    "ImmediateFixes": ["...", "..."],
    "PermanentFixes": ["...", "..."],
    "PreventiveMeasures": ["...", "..."],
    "Recommendations": ["...", "..."],
    "Confidence": "95%"
}}

Current Log:
{context["CurrentLog"]}

Component:
{context["Component"]}

Severity:
{context["Severity"]}

Contains Error:
{context["ContainsError"]}

Authentication Success:
{context["AuthenticationSuccess"]}

Anomaly Score:
{context["AnomalyScore"]}

Nearby Logs:
{json.dumps(context["NearbyLogs"], indent=4)}
"""
        
        if st.button("🚀 Analyze Anomaly with Groq AI"):
            if not groq_api_key:
                st.error("Please provide a valid Groq API Key in the sidebar settings.")
            else:
                with st.spinner("Calling Groq LLM API and generating recommendations..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        prompt = build_prompt_ui(selected_context)
                        
                        response = client.chat.completions.create(
                            model=model_choice,
                            temperature=0,
                            response_format={"type": "json_object"},
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        raw_content = response.choices[0].message.content
                        res_dict = json.loads(raw_content)
                        
                        # Populate original columns
                        res_dict["LogIndex"] = selected_context["LogIndex"]
                        res_dict["CurrentLog"] = selected_context["CurrentLog"]
                        res_dict["Component"] = selected_context["Component"]
                        res_dict["OriginalSeverity"] = selected_context["Severity"]
                        res_dict["ContainsError"] = selected_context["ContainsError"]
                        res_dict["AuthenticationSuccess"] = selected_context["AuthenticationSuccess"]
                        res_dict["AnomalyScore"] = selected_context["AnomalyScore"]
                        res_dict["NearbyLogs"] = selected_context["NearbyLogs"]
                        
                        # Append to output CSV
                        new_row_df = pd.DataFrame([res_dict])
                        
                        # Fix formatting lists for CSV saving
                        for col in ["ImmediateFixes", "PermanentFixes", "PreventiveMeasures", "Recommendations"]:
                            if col in new_row_df.columns:
                                new_row_df[col] = new_row_df[col].apply(lambda x: str(x) if isinstance(x, list) else x)
                        
                        csv_path = "outputs/root_cause_analysis.csv"
                        if os.path.exists(csv_path):
                            existing_csv_df = pd.read_csv(csv_path)
                            # Remove existing row if present (override)
                            existing_csv_df = existing_csv_df[existing_csv_df["LogIndex"].astype(int) != int(selected_context["LogIndex"])]
                            updated_csv_df = pd.concat([existing_csv_df, new_row_df], ignore_index=True)
                        else:
                            updated_csv_df = new_row_df
                            
                        # Save
                        os.makedirs("outputs", exist_ok=True)
                        updated_csv_df.to_csv(csv_path, index=False)
                        
                        st.success("✅ Analysis completed and saved successfully!")
                        st.balloons()
                        
                        # Show raw response preview
                        st.json(raw_content)
                        
                        # Force refresh
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to generate RCA: {e}")
    else:
        st.success("🎉 All anomalies have been analyzed! Review them in the Detailed Anomaly Inspector tab.")
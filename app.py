import streamlit as st

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Log Analyzer",
    page_icon="🤖",
    layout="centered"
)

# -----------------------------
# Header
# -----------------------------
st.title("🤖 AI Log Analyzer")
st.write(
    "Upload a system log file and let AI analyze it to identify the root cause and suggest fixes."
)

st.divider()

# -----------------------------
# Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "📂 Upload Log File",
    type=["txt", "log", "csv"]
)

if uploaded_file:

    logs = uploaded_file.read().decode("utf-8")

    st.success("✅ Log uploaded successfully!")

    with st.expander("📄 Preview Uploaded Logs"):
        st.code(logs[:3000])

    if st.button("🚀 Analyze Logs", use_container_width=True):

        with st.spinner("Analyzing logs..."):

            # Replace this with your AI function
            response = {
                "Severity": "Critical",
                "RootCause": "Database connection timeout due to exhausted connection pool.",
                "Impact": "Users cannot login and API requests are failing.",
                "ImmediateFix": "Restart the database connection pool.",
                "PermanentFix": "Increase pool size and optimize database queries.",
                "Recommendations": [
                    "Enable monitoring alerts",
                    "Implement retry mechanism",
                    "Monitor slow queries",
                    "Configure auto scaling"
                ]
            }

        st.success("🎉 Analysis Completed")

        severity = response["Severity"]

        if severity == "Critical":
            st.error(f"🚨 Severity: {severity}")
        elif severity == "High":
            st.warning(f"⚠️ Severity: {severity}")
        else:
            st.info(f"ℹ️ Severity: {severity}")

        st.subheader("🔍 Root Cause")
        st.info(response["RootCause"])

        st.subheader("💥 Business Impact")
        st.info(response["Impact"])

        st.subheader("🚑 Immediate Fix")
        st.success(response["ImmediateFix"])

        st.subheader("🔧 Permanent Fix")
        st.success(response["PermanentFix"])

        st.subheader("💡 AI Recommendations")

        for rec in response["Recommendations"]:
            st.write(f"✅ {rec}")
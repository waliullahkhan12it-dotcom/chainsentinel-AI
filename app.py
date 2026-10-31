import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modules.file_processor import analyze_uploaded_file
from modules.detector import detect_anomalies, get_detection_summary
from modules.detector import detect_anomalies, get_detection_summary
# =========================================================
# CHAIN SENTINEL AI - MAIN APPLICATION
# Initial dashboard version
# =========================================================

st.set_page_config(
    page_title="ChainSentinel AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #08111f 0%, #0b1729 55%, #101b30 100%);
    color: #F1F5F9;
}

[data-testid="stSidebar"] {
    background: #0c1728;
    border-right: 1px solid #243650;
}

[data-testid="stSidebar"] * {
    color: #e2eaf5;
}

.main-title {
    font-size: 34px;
    font-weight: 800;
    color: #f1f5f9;
    margin-bottom: 3px;
}

.subtitle {
    font-size: 14px;
    color: #9db0c9;
    margin-bottom: 25px;
}

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #eaf4ff;
    margin-top: 18px;
    margin-bottom: 14px;
}

.metric-card {
    background: linear-gradient(145deg, #14243b, #101c30);
    border: 1px solid #29415f;
    border-radius: 14px;
    padding: 20px;
    min-height: 125px;
}

.metric-label {
    color: #a8bad1;
    font-size: 13px;
    font-weight: 600;
}

.metric-value {
    color: #f3f8ff;
    font-size: 29px;
    font-weight: 800;
    margin-top: 9px;
}

.metric-note {
    color: #48c8e8;
    font-size: 12px;
    margin-top: 5px;
}

.info-card {
    background: #122139;
    border: 1px solid #2b405e;
    border-radius: 13px;
    padding: 18px;
    margin-bottom: 12px;
}

.info-card h4 {
    color: #eaf4ff;
    margin-bottom: 8px;
}

.info-card p {
    color: #a9bad0;
    font-size: 13px;
}

.status-demo {
    background: #342b17;
    color: #f8d77b;
    border: 1px solid #76602a;
    border-radius: 9px;
    padding: 12px;
    font-size: 13px;
    margin-bottom: 20px;
}

.footer {
    color: #8295af;
    font-size: 12px;
    text-align: center;
    padding: 25px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)


# ---------------- DEMONSTRATION DATA ----------------
# These records are illustrative only, NOT live Ethereum data.

transactions = pd.DataFrame([
    {
        "Transaction": "0xA81F...92C1",
        "From": "0xWallet01",
        "To": "0xWallet08",
        "Amount (ETH)": 2.40,
        "Gas (Gwei)": 24,
        "Risk": "Low",
        "Status": "Confirmed",
        "Type": "Normal"
    },
    {
        "Transaction": "0xB72E...81D2",
        "From": "0xWallet02",
        "To": "0xWallet09",
        "Amount (ETH)": 18.70,
        "Gas (Gwei)": 95,
        "Risk": "High",
        "Status": "Confirmed",
        "Type": "Large transfer"
    },
    {
        "Transaction": "0xC63D...70A3",
        "From": "0xWallet03",
        "To": "0xWallet10",
        "Amount (ETH)": 0.35,
        "Gas (Gwei)": 21,
        "Risk": "Low",
        "Status": "Confirmed",
        "Type": "Normal"
    },
    {
        "Transaction": "0xD54C...69B4",
        "From": "0xWallet04",
        "To": "0xWallet11",
        "Amount (ETH)": 42.50,
        "Gas (Gwei)": 130,
        "Risk": "Critical",
        "Status": "Confirmed",
        "Type": "Unusual amount"
    },
    {
        "Transaction": "0xE45B...58C5",
        "From": "0xWallet05",
        "To": "0xWallet12",
        "Amount (ETH)": 1.10,
        "Gas (Gwei)": 28,
        "Risk": "Medium",
        "Status": "Confirmed",
        "Type": "Frequency anomaly"
    },
    {
        "Transaction": "0xF36A...47D6",
        "From": "0xWallet06",
        "To": "0xWallet13",
        "Amount (ETH)": 5.60,
        "Gas (Gwei)": 30,
        "Risk": "Low",
        "Status": "Confirmed",
        "Type": "Normal"
    },
    {
        "Transaction": "0xG25B...36E7",
        "From": "0xWallet07",
        "To": "0xWallet14",
        "Amount (ETH)": 12.20,
        "Gas (Gwei)": 105,
        "Risk": "High",
        "Status": "Confirmed",
        "Type": "Unusual gas"
    }
])

risk_colors = {
    "Low": "#22c55e",
    "Medium": "#eab308",
    "High": "#f97316",
    "Critical": "#ef4444"
}


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("# 🛡️ ChainSentinel")
    st.caption("BLOCKCHAIN SECURITY PLATFORM")
    st.divider()

    page = st.radio(
        "MAIN NAVIGATION",
        [
            "Overview",
            "Live Blockchain",
            "File Investigation",
            "AI Security Analyst",
            "Anomaly Detection",
            "Wallet Intelligence",
            "Analytics",
            "Alert Centre",
            "Investigation Reports",
            "Settings"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### System information")
    st.caption("Application: Initial dashboard")
    st.caption("Network: Not connected")
    st.caption("AI engine: Not configured")

    st.divider()
    st.caption("ChainSentinel AI © 2026")


# ---------------- HEADER ----------------

st.markdown(
    '<div class="main-title">🛡️ ChainSentinel AI</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">AI-Powered Blockchain Security, Anomaly Detection & Digital Forensics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="status-demo">⚠️ DEMONSTRATION MODE — The transactions below are illustrative sample records, not live Ethereum blockchain data.</div>',
    unsafe_allow_html=True
)


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    st.markdown('<div class="section-title">Security Operations Overview</div>',
                unsafe_allow_html=True)

    total_transactions = len(transactions)
    high_risk = transactions["Risk"].isin(["High", "Critical"]).sum()
    total_volume = transactions["Amount (ETH)"].sum()
    critical_count = (transactions["Risk"] == "Critical").sum()

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, "TRANSACTIONS ANALYSED", total_transactions, "Demonstration records"),
        (c2, "HIGH / CRITICAL RISK", high_risk, "Sample risk classifications"),
        (c3, "SAMPLE ETH VOLUME", f"{total_volume:.2f}", "Illustrative ETH amount"),
        (c4, "CRITICAL FINDINGS", critical_count, "Sample findings only")
    ]

    for col, label, value, note in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-note">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Transaction Intelligence</div>',
                unsafe_allow_html=True)

    left, right = st.columns([1.4, 1])

    with left:
        fig = px.bar(
            transactions,
            x="Transaction",
            y="Amount (ETH)",
            color="Risk",
            color_discrete_map=risk_colors,
            title="Illustrative Transaction Amounts"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#DCEBFA",
            xaxis_title="Sample transaction",
            yaxis_title="Amount (ETH)",
            margin=dict(l=10, r=10, t=55, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        risk_counts = transactions["Risk"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]

        fig2 = px.pie(
            risk_counts,
            names="Risk Level",
            values="Count",
            hole=0.62,
            color="Risk Level",
            color_discrete_map=risk_colors,
            title="Sample Risk Distribution"
        )
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#DCEBFA",
            margin=dict(l=10, r=10, t=55, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-title">Recent Sample Transactions</div>',
                unsafe_allow_html=True)

    st.dataframe(
        transactions,
        use_container_width=True,
        hide_index=True
    )

    st.markdown('<div class="section-title">Investigation Shortcuts</div>',
                unsafe_allow_html=True)

    a, b, c = st.columns(3)

    with a:
        st.markdown("""
        <div class="info-card">
            <h4>📁 File Investigation</h4>
            <p>Prepare to inspect supported documents, logs, spreadsheets and network captures.</p>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="info-card">
            <h4>🔍 Anomaly Detection</h4>
            <p>Analyse unusual transaction patterns using machine learning and security rules.</p>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="info-card">
            <h4>🤖 AI Security Analyst</h4>
            <p>Connect the Groq API to explain investigation findings and recommend actions.</p>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# LIVE BLOCKCHAIN
# =========================================================

elif page == "Live Blockchain":

    st.markdown("## 🌐 Live Ethereum Blockchain Monitor")
    st.warning(
        "Ethereum is not connected yet. No live transactions are being received."
    )

    st.info(
        "This module will be connected to an Ethereum WebSocket provider "
        "in a later development step."
    )

    st.markdown("### Planned monitoring capabilities")
    st.write("- New confirmed Ethereum blocks")
    st.write("- Transaction hashes and wallet addresses")
    st.write("- ETH transaction values")
    st.write("- Gas information and timestamps")
    st.write("- Pending transactions when supported by the provider")


# =========================================================
# FILE INVESTIGATION
# =========================================================
# =========================================================
# FILE INVESTIGATION
# =========================================================

elif page == "File Investigation":

    st.markdown("## 📁 Universal File Investigation")
    st.write(
        "Upload a supported document, spreadsheet, image, "
        "network capture, smart contract or archive."
    )

    supported_extensions = [
        "pdf", "docx", "txt", "rtf", "csv", "xlsx", "xls",
        "json", "xml", "log", "syslog", "sol",
        "pcap", "pcapng", "png", "jpg", "jpeg", "zip"
    ]

    uploaded_file = st.file_uploader(
        "Choose an investigation file",
        type=supported_extensions,
        help="Maximum file size: 50 MB."
    )

    if uploaded_file is not None:

        st.markdown("### Selected evidence")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Filename**")
            st.write(uploaded_file.name)

        with col2:
            st.write("**File size**")
            st.write(f"{uploaded_file.size / 1024:.2f} KB")

        if st.button("🔍 Analyse uploaded file", type="primary"):

            try:
                with st.spinner("Validating and analysing evidence..."):

                    result = analyze_uploaded_file(uploaded_file)

                st.success("File processing completed.")

                st.markdown("### Evidence information")

                m1, m2, m3 = st.columns(3)

                m1.metric("File format", result["format"])
                m2.metric(
                    "Extracted characters",
                    f'{result["characters_extracted"]:,}'
                )
                m3.metric(
                    "File size",
                    f'{result["size_bytes"] / 1024:.1f} KB'
                )

                st.markdown("### SHA-256 evidence fingerprint")

                st.code(result["sha256"], language="text")

                st.caption(
                    "This hash identifies the exact uploaded file bytes. "
                    "It does not independently prove that the file is authentic."
                )

                st.markdown("### Extracted security indicators")

                indicators = result["indicators"]

                for category, values in indicators.items():

                    with st.expander(
                        f"{category} ({len(values)})"
                    ):

                        if values:
                            for value in values:
                                st.write(f"• {value}")
                        else:
                            st.caption("No indicators extracted.")

                st.markdown("### Extracted file content")

                with st.expander("View extracted content"):

                    st.text_area(
                        "Extracted evidence",
                        value=result["extracted_text"],
                        height=300,
                        disabled=True
                    )

                st.warning(result["warning"])

                # Keep latest investigation in this session.
                st.session_state["last_file_investigation"] = {
                    "filename": result["filename"],
                    "format": result["format"],
                    "sha256": result["sha256"],
                    "characters_extracted": result[
                        "characters_extracted"
                    ],
                    "indicators": result["indicators"]
                }

            except Exception as exc:

                st.error(f"File investigation failed: {exc}")

                st.info(
                    "Check that the file is valid, supported and "
                    "within the configured size limits."
                )


# =========================================================
# AI SECURITY ANALYST
# =========================================================

elif page == "AI Security Analyst":

    st.markdown("## 🤖 AI Security Analyst")

    st.info(
        "Groq API integration will be configured in a later development step."
    )

    question = st.text_area(
        "Investigation question",
        placeholder="Example: Explain the security significance of an unusually large transfer."
    )

    if st.button("Prepare question", type="primary"):
        if question.strip():
            st.success("Question received. The AI analyst is not connected yet.")
        else:
            st.warning("Please enter a question first.")


# =========================================================
# ANOMALY DETECTION
# =========================================================

# =========================================================
# ANOMALY DETECTION
# =========================================================

elif page == "Anomaly Detection":

    st.markdown("## 🔍 AI Anomaly Detection Centre")

    st.write(
        "Identify unusual transaction patterns using "
        "Isolation Forest and explainable security rules."
    )

    st.warning(
        "The current analysis uses illustrative demonstration "
        "transactions, not live Ethereum data."
    )

    contamination = st.slider(
        "Expected anomaly proportion",
        min_value=0.01,
        max_value=0.30,
        value=0.10,
        step=0.01,
        help="This controls the Isolation Forest model's expected "
             "proportion of unusual records."
    )

    if st.button("🚀 Run anomaly detection", type="primary"):

        try:

            with st.spinner("Analysing transaction patterns..."):

                results = detect_anomalies(
                    transactions,
                    contamination=contamination
                )

                summary = get_detection_summary(results)

            st.success("Anomaly analysis completed.")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Records analysed", summary["total"])
            c2.metric("ML anomalies", summary["anomalies"])
            c3.metric("High / Critical", summary["high_risk"])
            c4.metric("Critical findings", summary["critical"])

            st.markdown("### Risk classification")

            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### Risk distribution")

            risk_counts = (
                results["risk_level"]
                .value_counts()
                .reset_index()
            )

            risk_counts.columns = ["Risk", "Count"]

            fig = px.pie(
                risk_counts,
                names="Risk",
                values="Count",
                hole=0.55,
                color="Risk",
                color_discrete_map=risk_colors,
                title="Detected Risk Levels"
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#DCEBFA"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.info(
                "Anomaly scores are relative to this dataset. "
                "They are not probabilities of fraud."
            )

        except Exception as exc:

            st.error(f"Detection failed: {exc}")

# =========================================================
# ANALYTICS
# =========================================================

elif page == "Analytics":

    st.markdown("## 📊 Security Analytics")

    st.markdown("### Sample risk analysis")

    risk_counts = transactions["Risk"].value_counts().reset_index()
    risk_counts.columns = ["Risk", "Transactions"]

    fig = px.bar(
        risk_counts,
        x="Risk",
        y="Transactions",
        color="Risk",
        color_discrete_map=risk_colors,
        title="Demonstration Risk Classification"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#DCEBFA"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Transaction data")
    st.dataframe(transactions, use_container_width=True, hide_index=True)


# =========================================================
# ALERT CENTRE
# =========================================================

elif page == "Alert Centre":

    st.markdown("## 🚨 Alert Centre")

    selected_risk = st.selectbox(
        "Filter by severity",
        ["All", "Low", "Medium", "High", "Critical"]
    )

    alerts = transactions.copy()

    if selected_risk != "All":
        alerts = alerts[alerts["Risk"] == selected_risk]

    alerts = alerts[alerts["Risk"].isin(["Medium", "High", "Critical"])]

    if alerts.empty:
        st.success("No sample alerts match this filter.")
    else:
        for _, row in alerts.iterrows():
            color = risk_colors[row["Risk"]]
            st.markdown(f"""
            <div class="info-card">
                <h4 style="color:{color};">{row['Risk']} Risk — {row['Type']}</h4>
                <p>Transaction: {row['Transaction']}</p>
                <p>Amount: {row['Amount (ETH)']} ETH</p>
                <p>Classification is illustrative, not a confirmed fraud finding.</p>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# INVESTIGATION REPORTS
# =========================================================

elif page == "Investigation Reports":

    st.markdown("## 📑 Investigation Reports")

    st.info(
        "Report generation will be implemented after the investigation "
        "and evidence-processing modules are ready."
    )

    csv_data = transactions.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download demonstration transaction CSV",
        data=csv_data,
        file_name="chainsentinel_demo_transactions.csv",
        mime="text/csv"
    )

    st.caption(
        "This export contains demonstration records only, not real blockchain evidence."
    )


# =========================================================
# SETTINGS
# =========================================================

elif page == "Settings":

    st.markdown("## ⚙️ Application Settings")

    st.markdown("### Current configuration")

    st.write("Application: ChainSentinel AI")
    st.write("Dashboard: Initial version")
    st.write("Blockchain provider: Not configured")
    st.write("Groq AI: Not configured")
    st.write("Authentication: Not implemented yet")

    st.markdown("### Security information")

    st.success("API credentials will be stored using Streamlit secrets.")
    st.success("Uploaded files will not be executed.")
    st.warning("Do not upload confidential or sensitive evidence to this demonstration version.")


# ---------------- FOOTER ----------------

st.markdown("""
<div class="footer">
    ChainSentinel AI · Blockchain Security & Digital Forensics
    <br>
    Initial dashboard version · Demonstration data is not live blockchain data
</div>
""", unsafe_allow_html=True)

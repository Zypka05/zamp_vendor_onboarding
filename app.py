import os
import json
import time
import pandas as pd
import streamlit as st

from config_and_scenarios import (
    PDF_DIR, JSON_DIR, SCENARIOS, generate_sample_assets
)
from audit_db import init_db, fetch_all_runs, clear_all_runs
from verification_engine import run_onboarding_pipeline

# -------------------------------------------------------------------------
# PAGE SETUP & CUSTOM CSS
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Zamp VendorGuard | Autonomous Vendor Onboarding",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .badge-approved {
        background-color: #d1fae5; color: #065f46; padding: 6px 14px;
        border-radius: 6px; font-weight: 700; display: inline-block;
    }
    .badge-pending {
        background-color: #fef3c7; color: #92400e; padding: 6px 14px;
        border-radius: 6px; font-weight: 700; display: inline-block;
    }
    .badge-rejected {
        background-color: #fee2e2; color: #991b1b; padding: 6px 14px;
        border-radius: 6px; font-weight: 700; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# INITIALIZE ASSETS & SEED HISTORICAL RUNS
# -------------------------------------------------------------------------
def bootstrap_system():
    generate_sample_assets()
    init_db()
    df = fetch_all_runs()
    if df.empty:
        for _, scen in SCENARIOS.items():
            pdf_path = os.path.join(PDF_DIR, scen["pdf_filename"])
            run_onboarding_pipeline(scen, pdf_path)


bootstrap_system()

# -------------------------------------------------------------------------
# SIDEBAR: AI ENGINE CONFIGURATION & TEST FILE DOWNLOADS
# -------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ Zamp VendorGuard")
    st.caption("PS-2: Autonomous Vendor Onboarding & Compliance Workbench")

    st.markdown("#### ⚙️ AI & Execution Settings")
    ai_mode = st.selectbox(
        "AI Communication & Reasoning Mode:",
        [
            "Gemini API (gemini-2.5-flash)",
            "Ollama Local (qwen2.5:7b — Fast Sovereign AI)",
            "Ollama Local (deepseek-r1:7b — Deep Reasoning)",
            "Deterministic Engine (Instant)"
        ]
    )
    gemini_key = ""
    if ai_mode == "Gemini API (gemini-2.5-flash)":
        default_env_key = os.environ.get("GEMINI_API_KEY", "")
        gemini_key = st.text_input(
            "Gemini API Key (Free at aistudio.google.com):",
            value=default_env_key,
            type="password"
        )

    animate_pipeline = st.checkbox("Animate Stage-by-Stage Live View", value=True)

    st.markdown("#### 📂 Download Real Test Inputs")
    st.caption("Download PDFs or JSONs to drag-and-drop into the Blank Form or JSON Upload mode during your live demo:")
    for _, scen in SCENARIOS.items():
        c_pdf, c_json = st.columns(2)
        pdf_p = os.path.join(PDF_DIR, scen["pdf_filename"])
        json_p = os.path.join(JSON_DIR, scen["json_filename"])
        with c_pdf:
            with open(pdf_p, "rb") as f:
                st.download_button(
                    label=f"📄 {scen['scenario_id']} PDF",
                    data=f,
                    file_name=scen["pdf_filename"],
                    mime="application/pdf",
                    key=f"dl_pdf_{scen['scenario_id']}"
                )
        with c_json:
            with open(json_p, "rb") as jf:
                st.download_button(
                    label=f"📦 {scen['scenario_id']} JSON",
                    data=jf,
                    file_name=scen["json_filename"],
                    mime="application/json",
                    key=f"dl_json_{scen['scenario_id']}"
                )

    if st.button("🔄 Reset & Re-Seed Audit Database", use_container_width=True):
        clear_all_runs()
        bootstrap_system()
        st.rerun()

# -------------------------------------------------------------------------
# TOP-LEVEL NAVIGATION TABS
# -------------------------------------------------------------------------
tab_live, tab_dash, tab_map = st.tabs([
    "⚡ 1. Live Vendor Submission & Execution View",
    "📊 2. Operations Dashboard & Audit History",
    "🗺️ 3. Process Map & Edge Case Architecture"
])

# =========================================================================
# TAB 1: LIVE VENDOR SUBMISSION & REAL-TIME EXECUTION VIEW
# =========================================================================
with tab_live:
    st.subheader("End-to-End Vendor Onboarding Portal & Live Pipeline Runner")
    col_form, col_live = st.columns([1.05, 1.25], gap="large")

    with col_form:
        st.markdown("##### Step 1: Select Submission Input Channel")
        input_channel = st.radio(
            "How is the vendor submission entering the workflow?",
            [
                "🎯 Rehearsed Demo Scenarios (Happy Path + 4 Edge Cases)",
                "➕ Blank New Vendor Submission Portal (Form + PDF)",
                "📦 Raw Vendor JSON Payload + PDF Upload"
            ]
        )

        blank_state = {
            "scenario_id": "LIVE-PORTAL",
            "vendor_name": "",
            "country": "India",
            "state": "",
            "address": "",
            "tax_id": "",
            "bank_holder_name": "",
            "bank_routing": "",
            "bank_account": "",
            "contact_name": "",
            "contact_email": "",
            "pdf_filename": None
        }

        if input_channel == "🎯 Rehearsed Demo Scenarios (Happy Path + 4 Edge Cases)":
            chosen_key = st.selectbox("Select Prepared Scenario:", list(SCENARIOS.keys()))
            active_data = SCENARIOS[chosen_key]
        elif input_channel == "📦 Raw Vendor JSON Payload + PDF Upload":
            active_data = blank_state.copy()
            active_data["scenario_id"] = "JSON-UPLOAD"
            uploaded_json = st.file_uploader("Upload Vendor Submission JSON (.json)", type=["json"])
            if uploaded_json is not None:
                try:
                    parsed_json = json.load(uploaded_json)
                    active_data.update(parsed_json)
                    st.success(f"Loaded JSON submission for: {active_data.get('vendor_name')}")
                except Exception as ex:
                    st.error(f"Invalid JSON payload: {ex}")
        else:
            active_data = blank_state

        with st.form("live_vendor_onboarding_form"):
            st.markdown("##### Step 2: Vendor Submission Form & Compliance Document")
            c1, c2 = st.columns(2)
            countries = ["India", "United States", "United Kingdom"]
            c_idx = countries.index(active_data["country"]) if active_data.get("country") in countries else 0

            with c1:
                f_name = st.text_input("Company Legal / Trade Name *", value=active_data.get("vendor_name", ""))
                f_country = st.selectbox("Registered Country *", countries, index=c_idx)
                f_state = st.text_input("Registered State / Province *", value=active_data.get("state", ""))
                f_tax = st.text_input("Tax Registration ID (GSTIN / EIN / VAT) *", value=active_data.get("tax_id", ""))
            with c2:
                f_bank_holder = st.text_input("Bank Account Beneficiary Name *", value=active_data.get("bank_holder_name", ""))
                f_routing = st.text_input("Bank Routing Code (IFSC / ABA / IBAN) *", value=active_data.get("bank_routing", ""))
                f_account = st.text_input("Bank Account Number *", value=active_data.get("bank_account", ""))
                f_contact = st.text_input("Compliance Contact Name *", value=active_data.get("contact_name", ""))

            f_email = st.text_input("Vendor Contact Email *", value=active_data.get("contact_email", ""))
            f_address = st.text_input("Registered Physical Address", value=active_data.get("address", ""))

            pdf_hint = (
                f" (Leave empty to use attached {active_data['pdf_filename']}, or upload any PDF)"
                if active_data.get("pdf_filename") else " (Required: Upload PDF Compliance Packet)"
            )
            uploaded_pdf = st.file_uploader(f"Attach Statutory Compliance PDF{pdf_hint}", type=["pdf"])
            execute_btn = st.form_submit_button("🚀 Run Live Onboarding Pipeline", use_container_width=True)

    with col_live:
        st.markdown("##### Step 3: Real-Time Stage Execution & Decision Output")
        if execute_btn:
            if uploaded_pdf is None and not active_data.get("pdf_filename"):
                st.error("⚠️ Please attach a compliance PDF document before running the onboarding verification.")
                st.stop()

            submission_payload = {
                "scenario_id": active_data.get("scenario_id", "LIVE"),
                "vendor_name": f_name,
                "country": f_country,
                "state": f_state,
                "address": f_address,
                "tax_id": f_tax,
                "bank_holder_name": f_bank_holder,
                "bank_routing": f_routing,
                "bank_account": f_account,
                "contact_name": f_contact,
                "contact_email": f_email
            }
            pdf_target = uploaded_pdf if uploaded_pdf is not None else os.path.join(PDF_DIR, active_data["pdf_filename"])

            result = run_onboarding_pipeline(
                submission_payload, pdf_target, ai_mode=ai_mode, gemini_api_key=gemini_key
            )

            with st.status("Executing 5-Stage Autonomous Onboarding Pipeline...", expanded=True) as status_box:
                for stg in result["stages"]:
                    icon = "✅" if stg["status"] == "PASS" else ("⚠️" if stg["status"] == "WARN" else "❌")
                    st.markdown(f"**Stage {stg['stage_num']}: {stg['stage_name']}** — {icon} `{stg['status']}`")
                    st.caption(stg["details"])
                    if animate_pipeline:
                        time.sleep(0.35)
                status_box.update(
                    label=f"Execution Complete ({result['processing_ms']} ms) — Final Decision: {result['final_status']}",
                    state="complete",
                    expanded=True
                )

            badge_cls = (
                "badge-approved" if result["final_status"] == "APPROVED"
                else ("badge-pending" if result["final_status"] == "PENDING" else "badge-rejected")
            )
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"**Final Status**<br><span class='{badge_cls}'>{result['final_status']}</span>", unsafe_allow_html=True)
            k2.metric("Composite Risk Score", f"{result['risk_score']} / 100")
            k3.metric("Audit Run ID", result["run_id"])

            st.info(f"**Decision Summary:** {result['summary_reason']}")

            out_tab1, out_tab2, out_tab3 = st.tabs([
                "📧 Automated Vendor Follow-Up Email",
                "🔎 Cross-Field Verification Matrix",
                "📄 Extracted PDF Intelligence"
            ])
            with out_tab1:
                st.caption(f"Generated via: {result['ai_source_used']}")
                st.text_area("Dispatched Vendor Communication", value=result["email_draft"], height=210)
            with out_tab2:
                st.dataframe(pd.DataFrame(result["field_checks"]), use_container_width=True, hide_index=True)
            with out_tab3:
                st.json(result["pdf_extracted"])
        else:
            st.info(
                "Choose an input mode on the left (Demo Scenario, Blank New Vendor Form, or JSON Upload) "
                "and click **Run Live Onboarding Pipeline** to watch each stage execute in real time."
            )

# =========================================================================
# TAB 2: OPERATIONS DASHBOARD & PERSISTENT AUDIT TRAIL
# =========================================================================
with tab_dash:
    st.subheader("Procurement Operations Dashboard & Persistent Audit Log")
    df_history = fetch_all_runs()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Onboarding Runs", len(df_history))
    m2.metric("Approved (Ready for Pay)", len(df_history[df_history["final_status"] == "APPROVED"]))
    m3.metric("Pending (Awaiting Vendor Fix)", len(df_history[df_history["final_status"] == "PENDING"]))
    m4.metric("Rejected (Fraud / Tax Spoofing)", len(df_history[df_history["final_status"] == "REJECTED"]))

    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        status_filter = st.multiselect(
            "Filter Run History by Status:",
            ["APPROVED", "PENDING", "REJECTED"],
            default=["APPROVED", "PENDING", "REJECTED"]
        )
    with f_col2:
        csv_bytes = df_history.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export Audit Trail (CSV)",
            data=csv_bytes,
            file_name="zamp_vendor_onboarding_audit.csv",
            mime="text/csv",
            use_container_width=True
        )

    filtered_df = df_history[df_history["final_status"].isin(status_filter)]
    st.dataframe(
        filtered_df[[
            "run_id", "timestamp", "scenario_id", "vendor_name",
            "country", "tax_id", "final_status", "risk_score", "summary_reason"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### 🔍 Deep-Dive Audit Trail Inspector")
    if not filtered_df.empty:
        chosen_run = st.selectbox("Select Run ID to inspect full stage trace, field checks & sent email:", filtered_df["run_id"].tolist())
        row = filtered_df[filtered_df["run_id"] == chosen_run].iloc[0]
        ins_left, ins_right = st.columns([1.15, 1])
        with ins_left:
            st.markdown(f"**Stage Execution Trace (`{row['run_id']}` — {row['vendor_name']})**")
            for s in json.loads(row["stages_json"]):
                icon = "✅" if s["status"] == "PASS" else ("⚠️" if s["status"] == "WARN" else "❌")
                st.markdown(f"- **Stage {s['stage_num']} ({s['stage_name']}) [{icon} {s['status']}]:** {s['details']}")
            st.markdown("**Field-by-Field Cross-Reference Matrix**")
            st.dataframe(pd.DataFrame(json.loads(row["field_checks_json"])), use_container_width=True, hide_index=True)
        with ins_right:
            st.markdown("**Audit Copy of Dispatched Vendor Communication**")
            st.code(row["email_draft"], language="text")

# =========================================================================
# TAB 3: PROCESS MAP & EDGE CASE ARCHITECTURE
# =========================================================================
with tab_map:
    st.subheader("End-to-End Process Map & Deliberate Edge Case Design")
    st.caption("Mapped before building per Zamp Candidate Guidance #1 — ready for live interview walkthrough.")

    st.graphviz_chart("""
    digraph VendorOnboarding {
        rankdir=LR;
        node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10];
        Input [label="Vendor Submission\\n(Portal Form / JSON + PDF)", fillcolor="#e0f2fe", color="#0284c7"];
        S1 [label="Stage 1: Ingestion\\nUniversal PDF OCR & Regex Scan", fillcolor="#f1f5f9", color="#475569"];
        S2 [label="Stage 2: Completeness\\n9 Mandatory Fields & Doc Type", fillcolor="#f1f5f9", color="#475569"];
        S3 [label="Stage 3: Tax & Jurisdiction\\nGSTIN/EIN Syntax, State Prefix & PAN Char", fillcolor="#f1f5f9", color="#475569"];
        S4 [label="Stage 4: Entity & Banking\\nBeneficiary Match, DBA Bridge & Domestic Routing", fillcolor="#f1f5f9", color="#475569"];
        Approved [label="APPROVED\\nERP Profile Active", fillcolor="#d1fae5", color="#059669"];
        Pending [label="PENDING\\nAuto-Email Missing/DBA Items", fillcolor="#fef3c7", color="#d97706"];
        Rejected [label="REJECTED\\nFraud / Spoofing Alert Logged", fillcolor="#fee2e2", color="#dc2626"];

        Input -> S1 -> S2 -> S3 -> S4;
        S2 -> Pending [label="Missing Fields /\\nWrong PDF Attached"];
        S3 -> Rejected [label="Invalid Tax Syntax /\\nState or PAN Mismatch"];
        S4 -> Rejected [label="Personal Bank Fraud /\\nOffshore IBAN"];
        S4 -> Pending [label="Valid DBA Clause\\nNeeds Legal Sign-Off"];
        S4 -> Approved [label="All Controls Pass"];
    }
    """)

    st.markdown("#### Deliberate Edge Case Matrix")
    edge_df = pd.DataFrame([
        {
            "Scenario": "HP-01: Apex Industrial Automation",
            "Operational Pattern": "Happy Path",
            "Cross-Referenced Signals": "Maharashtra state (27) == GSTIN prefix 27; PAN char 'C' == Company; 'Pvt Ltd' normalized to 'Private Limited'; domestic HDFC IFSC.",
            "Decision": "APPROVED"
        },
        {
            "Scenario": "EC-01: Nimbus Cloud Logistics",
            "Operational Pattern": "Subtle Multi-Field Spoofing",
            "Cross-Referenced Signals": "Bengaluru address (requires 29) vs Delhi GSTIN (07); Corporate name vs Individual PAN char ('P'); domestic entity vs UK IBAN.",
            "Decision": "REJECTED"
        },
        {
            "Scenario": "EC-02: Stellar Precision Tooling LLC",
            "Operational Pattern": "Payment Diversion & Invalid Tax ID",
            "Cross-Referenced Signals": "Invalid IRS EIN campus prefix (00-); corporate vendor routing ACH funds to personal individual account ('Marcus Vance').",
            "Decision": "REJECTED"
        },
        {
            "Scenario": "EC-03: Horizon Green Energy",
            "Operational Pattern": "Incomplete Form & Wrong Attachment",
            "Cross-Referenced Signals": "Blank account number & contact name; uploaded PDF classified as Sales Quotation Brochure rather than Tax/Bank proof.",
            "Decision": "PENDING"
        },
        {
            "Scenario": "EC-04: Vertex Digital Solutions",
            "Operational Pattern": "Parent-Subsidiary DBA Nuance",
            "Cross-Referenced Signals": "Trade name ('Vertex Digital') != Bank holder ('Vertex Retail Group Inc'), bridged by verified DBA clause inside PDF.",
            "Decision": "PENDING"
        }
    ])
    st.dataframe(edge_df, use_container_width=True, hide_index=True)
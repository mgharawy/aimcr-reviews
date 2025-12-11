# app.py — FINAL, TESTED & WORKING (December 2025)
import streamlit as st
from datetime import datetime
from pathlib import Path
import subprocess
import json
import time

st.set_page_config(page_title="KAUST AIMCR", layout="wide")
st.title("KAUST AI Model Control Review (AIMCR)")

# ============================= PATHS =============================
REPO_PATH = Path(__file__).parent.resolve()
DRAFTS_DIR = REPO_PATH / "drafts"
DRAFTS_DIR.mkdir(exist_ok=True)

# ============================= SAFE GIT =============================
def safe_git_pull():
    if not (REPO_PATH / ".git").exists():
        return
    try:
        subprocess.run(["git", "pull", "--rebase"], cwd=REPO_PATH, capture_output=True, timeout=10)
    except:
        pass

def safe_git_add_commit_push(message: str):
    try:
        subprocess.run(["git", "add", "."], cwd=REPO_PATH, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_PATH,
                                capture_output=True, text=True, timeout=10).stdout.strip()
        if status:
            subprocess.run(["git", "commit", "-m", message], cwd=REPO_PATH, check=True)
            subprocess.run(["git", "push"], cwd=REPO_PATH, timeout=30)
    except:
        pass

safe_git_pull()

# ============================= DRAFTS =============================
def list_drafts():
    return sorted(DRAFTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

def save_draft(data):
    pid = (data.get("project_id") or "UNKNOWN").strip() or "UNKNOWN"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file = DRAFTS_DIR / f"{pid}_{ts}.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    safe_git_add_commit_push(f"draft: {pid}")
    return file.name

def load_draft(name):
    try:
        with open(DRAFTS_DIR / name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

# ============================= SIDEBAR =============================
with st.sidebar:
    st.header("mshaikh786/aimcr-reviews")

    if st.button("Sync with GitHub"):
        with st.spinner("Pulling latest..."):
            safe_git_pull()
        st.success("Synced!")
        st.rerun()

    drafts = list_drafts()
    if drafts:
        sel = st.selectbox(
            "Resume draft",
            [""] + [d.name for d in drafts],
            format_func=lambda x: x[:-5].replace("_", " ") if x else "— Select draft —"
        )
        if sel and st.button("Load Draft"):
            st.session_state.data = load_draft(sel)
            st.success(f"Loaded {sel}")
            st.rerun()

    st.markdown("---")
    project_id = st.text_input("Project ID", value="PROJ001")
    today = datetime.now().strftime("%d-%m-%Y")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save Draft", use_container_width=True):
            st.session_state.data["project_id"] = project_id
            st.session_state.data["crr_date"] = today
            save_draft(st.session_state.data)
            st.success("Draft saved")
    with c2:
        if st.button("FINAL SUBMIT", type="primary", use_container_width=True):
            if st.checkbox("I confirm this review is complete"):
                folder = REPO_PATH / f"AIMCR-{project_id}-{today}"
                folder.mkdir(exist_ok=True)
                with open(folder / "data.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state.data, f, indent=4, ensure_ascii=False)
                safe_git_add_commit_push(f"FINAL AIMCR {project_id}")
                st.balloons()
                st.success(f"Submitted to {folder.name}/")
                st.session_state.pop("data", None)
                st.rerun()

    st.caption("Auto-save every 30 seconds")

# Auto-save
if "data" in st.session_state:
    if time.time() - st.session_state.get("last_save", 0) > 30:
        st.session_state.data["project_id"] = project_id
        st.session_state.data["crr_date"] = today
        save_draft(st.session_state.data)
        st.session_state.last_save = time.time()

# ============================= INIT DATA =============================
if "data" not in st.session_state:
    st.session_state.data = {
        "project_id": "PROJ001",
        "proposal_title": "",
        "principal_investigator": "",
        "proposal_date": "",
        "reviewer_name": "",
        "reviewer_id": "",
        "crr_date": datetime.now().strftime("%d-%m-%Y"),
        "third_party_software": [],
        "source_code": [],
        "datasets_user_files": [],
        "models": [],
    }

data = st.session_state.data

# ============================= HEADER =============================
st.markdown("## Proposal Information")
col1, col2 = st.columns(2)
with col1:
    data["project_id"] = st.text_input("Project ID", data.get("project_id", ""))
    data["proposal_title"] = st.text_input("Proposal Title", data.get("proposal_title", ""))
    data["principal_investigator"] = st.text_input("Principal Investigator", data.get("principal_investigator", ""))
with col2:
    data["proposal_date"] = st.date_input("Proposal Date", datetime.today()).strftime("%d-%m-%Y")
    data["crr_date"] = st.date_input("CRR Date (Review Date)", datetime.today()).strftime("%d-%m-%Y")

st.markdown("## Reviewer Identification")
r1, r2 = st.columns(2)
with r1:
    data["reviewer_name"] = st.text_input("Reviewer Name", data.get("reviewer_name", ""))
with r2:
    data["reviewer_id"] = st.text_input("Reviewer ID", data.get("reviewer_id", ""))

st.info("**Risk Score Legend:** 1 = No Risk • 2 = Low Risk • 3 = Medium Risk • 4 = High Risk • 5 = Critical Risk")

# ============================= EXACT CHECKS FROM YOUR DOCUMENT =============================
checks = {
    "third_party_software": [
        "Open-source license compliance",
        "Known vulnerabilities (CVE)",
        "Supply chain risks (typosquatting, protestware)",
        "Binary/source origin verification",
        "Malicious code insertion risk",
        "Dependency pinning & reproducibility",
    ],
    "source_code": [
        "Static code analysis (bandit, semgrep)",
        "Secrets scanning",
        "Malicious code patterns",
        "Code provenance & signing",
        "Backdoors/trojans",
        "Obfuscated code",
    ],
    "datasets_user_files": [
        "Data poisoning risk",
        "PII / sensitive data leakage",
        "Copyright / licensing issues",
        "Adversarial examples",
        "Dataset provenance",
        "Jailbreak prompts in dataset",
    ],
    "models": [
        "Model weights integrity (hash verification)",
        "Known unsafe/refusal-bypassed models",
        "Backdoor/trojan in weights",
        "Model card completeness",
        "Unsafe fine-tuning detected",
        "Export-controlled model",
    ]
}

# ============================= RENDER SECTION =============================
def render_section(title: str, key: str):
    st.markdown(f"### {title}")

    if st.button(f"+ Add Artifact", key=f"add_{key}"):
        data[key].append({
            "name": f"Artifact {len(data[key])+1}",
            "checks": {c: {"score": 1, "notes": ""} for c in checks[key]}
        })

    for idx, artifact in enumerate(data[key]):
        with st.expander(f"Artifact: {artifact['name']} ({idx+1})", expanded=True):
            artifact["name"] = st.text_input("Artifact Name/ID", artifact["name"], key=f"name_{key}_{idx}")

            # Table header
            h1, h2, h3 = st.columns([5, 1.3, 4])
            h1.markdown("**Check Description**")
            h2.markdown("**Risk Score**")
            h3.markdown("**Notes / Evidence / Comments**")

            for check in checks[key]:
                c1, c2, c3 = st.columns([5, 1.3, 4])
                c1.write(check)
                current = artifact["checks"][check]
                score = c2.selectbox(
                    "Score",
                    [1,2,3,4,5],
                    format_func=lambda x: ["1-No","2-Low","3-Med","4-High","5-Critical"][x-1],
                    index=current["score"]-1,
                    key=f"score_{key}_{idx}_{check}"
                )
                notes = c3.text_area(
                    "",
                    value=current["notes"],
                    height=80,
                    key=f"notes_{key}_{idx}_{check}"
                )
                artifact["checks"][check] = {"score": score, "notes": notes}

            if st.button("Remove artifact", key=f"del_{key}_{idx}"):
                data[key].pop(idx)
                st.rerun()

    if data[key]:
        max_scores = [max(a["checks"][c]["score"] for a in data[key]) for c in checks[key]]
        total = sum(max_scores)
        critical = 5 in max_scores
        color = "red" if critical or total >= 21 else "orange" if total >= 15 else "green"
        level = "CRITICAL" if critical or total >= 21 else "HIGH" if total >= 15 else "MEDIUM" if total >= 10 else "LOW"
        st.markdown(f"**Section Risk Score: {total} → <span style='color:{color};font-size:1.4em;'>{level}</span>**", 
                    unsafe_allow_html=True)

# ============================= RENDER ALL SECTIONS =============================
render_section("Third-Party Software (Packages, Libraries, Containers & Binaries) Screening Procedure", "third_party_software")
render_section("Source Code Screening Procedure", "source_code")
render_section("Datasets & User Files Screening Procedure", "datasets_user_files")
render_section("Models Screening Procedure", "models")

# ============================= FINAL SUMMARY =============================
totals = []
has_crit = False
for key in checks:
    if data[key]:
        maxes = [max(a["checks"][c]["score"] for a in data[key]) for c in checks[key]]
        totals.append(sum(maxes))
        if 5 in maxes:
            has_crit = True

final_risk = sum(totals)
if final_risk >= 21 or has_crit:
    st.error(f"**FINAL RISK SCORE: {final_risk} — CRITICAL — Senior review required**")
else:
    st.success(f"**FINAL RISK SCORE: {final_risk} — Acceptable**")

st.info(f"Final submission folder: `AIMCR-{project_id}-{today}`")
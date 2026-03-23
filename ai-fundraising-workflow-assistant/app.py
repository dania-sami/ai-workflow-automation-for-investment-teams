
import re
from collections import Counter

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Fundraising & Investment Workflow Assistant", layout="wide")

STOPWORDS = {
    "the","and","for","that","with","this","from","have","will","into","your","about","their","they","them",
    "what","when","where","which","while","were","been","being","would","could","should","there","here","also",
    "than","then","into","across","such","using","used","very","much","more","most","less","some","many","any",
    "our","ours","you","yours","his","her","hers","its","it","are","was","were","is","be","to","of","in","on",
    "at","as","by","an","a","or","if","we","do","does","did","can","may","not","but","so","because","through",
    "within","under","over","between","each","per","via"
}

DEFAULT_PROMPTS = {
    "workflow_mapping": "Map the workflow, identify bottlenecks, and suggest automation opportunities.",
    "research_brief": "Create a concise research brief with overview, themes, risks, and suggested next steps.",
    "reporting": "Turn raw notes into an executive summary, key points, and action items.",
    "crm": "Convert meeting notes into clean CRM-ready updates and follow-up actions.",
    "meeting_prep": "Generate an agenda, talking points, questions, and risk areas before a meeting."
}

SECTOR_KEYWORDS = {
    "climate tech": ["climate", "carbon", "decarbonization", "energy", "battery", "grid", "storage", "renewable"],
    "clean energy": ["solar", "wind", "hydrogen", "renewable", "energy", "storage", "grid"],
    "biodiversity": ["biodiversity", "nature", "ecosystem", "regeneration", "conservation"],
    "defense and resilience": ["defense", "resilience", "security", "supply chain", "critical infrastructure"],
    "infrastructure": ["infrastructure", "transport", "utility", "grid", "water", "telecom"],
    "real estate": ["real estate", "property", "housing", "asset management", "occupancy"]
}

def clean_text(text):
    return re.sub(r"\s+", " ", text.strip())

def split_sentences(text):
    text = clean_text(text)
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def top_keywords(text, n=8):
    words = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 3]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(n)]

def detect_themes(text):
    text_l = text.lower()
    found = []
    for theme, kws in SECTOR_KEYWORDS.items():
        if any(kw in text_l for kw in kws):
            found.append(theme.title())
    return found or ["General private markets / fundraising"]

def classify_workflow_steps(text):
    steps = []
    mapping = {
        "research": ["research", "screen", "analy", "diligence", "review"],
        "documentation": ["document", "memo", "report", "presentation", "deck", "summary"],
        "crm": ["crm", "contact", "relationship", "follow-up", "outreach", "email"],
        "meetings": ["meeting", "call", "agenda", "prep", "notes"],
        "reporting": ["report", "update", "weekly", "monthly", "status"],
    }
    text_l = text.lower()
    for name, kws in mapping.items():
        if any(kw in text_l for kw in kws):
            steps.append(name.title())
    return steps or ["Research", "Documentation", "Reporting"]

def suggest_automation(text):
    text_l = text.lower()
    suggestions = []
    if any(w in text_l for w in ["research", "screen", "memo", "diligence"]):
        suggestions.append("Use an LLM-assisted research brief generator with a reusable prompt template.")
    if any(w in text_l for w in ["crm", "contact", "meeting note", "follow-up", "email"]):
        suggestions.append("Automate CRM note structuring and follow-up email drafts from meeting notes.")
    if any(w in text_l for w in ["report", "update", "presentation", "deck"]):
        suggestions.append("Create a reporting pipeline that turns raw notes into executive summaries and slide-ready bullets.")
    if any(w in text_l for w in ["meeting", "agenda", "prep"]):
        suggestions.append("Generate meeting prep packs with context, key questions, and risk flags.")
    if not suggestions:
        suggestions.append("Start with workflow mapping, identify repetitive steps, and introduce prompt-driven templates for consistency.")
    return suggestions

def summary_block(text, max_sentences=3):
    sents = split_sentences(text)
    if not sents:
        return "No content provided."
    picked = sents[:max_sentences]
    return " ".join(picked)

def action_items(text):
    kws = top_keywords(text, 5)
    base = [
        "Validate the output with a domain expert before circulation.",
        "Store the output in a structured format for later reuse.",
        "Capture next steps and ownership clearly."
    ]
    if kws:
        base.insert(0, f"Follow up on the highest-signal topics: {', '.join(kws[:3])}.")
    return base

def make_research_brief(topic, notes):
    themes = detect_themes(topic + " " + notes)
    kws = top_keywords(notes or topic, 8)
    return {
        "Overview": summary_block(notes or topic, 3),
        "Key themes": ", ".join(themes),
        "Keywords": ", ".join(kws) if kws else "No strong keywords detected",
        "Potential opportunities": "The strongest opportunity appears where differentiation, data quality, and workflow fit are clear.",
        "Potential risks": "Key risks include limited data quality, fragmented workflow adoption, and unclear ownership during rollout.",
        "Suggested next steps": "Validate the use case with stakeholders, test a focused prompt workflow, and measure time saved and output quality."
    }

def make_meeting_prep(entity, context):
    themes = detect_themes(entity + " " + context)
    first_theme = themes[0].lower() if themes else "the mandate"
    return {
        "Objective": f"Prepare for a productive discussion with {entity}.",
        "Context summary": summary_block(context or entity, 2),
        "Key talking points": [
            f"Clarify strategic priorities related to {first_theme}.",
            "Understand current workflow pain points and reporting expectations.",
            "Identify where AI can improve speed, consistency, and decision support."
        ],
        "Questions to ask": [
            "Which tasks are currently the most repetitive or manual?",
            "What information needs to be structured more consistently?",
            "How are outputs currently reviewed and shared internally?"
        ],
        "Risk areas": [
            "Unclear process ownership",
            "Low trust in generated outputs",
            "Fragmented data sources or inconsistent note-taking"
        ]
    }

def make_crm_update(contact, notes):
    kws = top_keywords(notes, 6)
    return {
        "Contact": contact or "Prospect / Investor",
        "Summary": summary_block(notes, 2),
        "Topics discussed": ", ".join(kws) if kws else "General workflow and AI implementation topics",
        "Sentiment": "Interested but likely to require a clear demonstration of practical value.",
        "Next actions": [
            "Send a concise recap with agreed follow-up items.",
            "Share one tailored example or workflow demo.",
            "Schedule next check-in with a clear owner and timeline."
        ]
    }

def make_followup_email(contact, notes):
    summary = summary_block(notes, 1)
    return f"""Subject: Great speaking with you

Hi {contact or 'there'},

Thank you for the conversation today. It was helpful to better understand your priorities and how you currently work across research, reporting, and relationship management.

My main takeaway was: {summary}

As discussed, the next useful step would be to share a concise example of how an AI-supported workflow could improve consistency and save time in day-to-day operations.

Best regards,
Dania
"""

def generate_report(title, notes):
    return {
        "Executive summary": summary_block(notes, 3),
        "Key observations": action_items(notes)[:3],
        "Recommended actions": action_items(notes)[-3:],
        "Slide-ready bullets": [
            f"{title or 'Topic'} shows clear potential for workflow improvement through structured AI outputs.",
            "The highest-value use cases are document preparation, meeting preparation, and reporting.",
            "Success depends on clear ownership, trusted outputs, and simple adoption."
        ]
    }

st.title("AI Fundraising & Investment Workflow Assistant")
st.caption("A practical workflow studio for research, reporting, CRM, meeting preparation, and AI prompt operations.")

with st.sidebar:
    st.header("Prompt Library")
    prompt_choice = st.selectbox("Select workflow", list(DEFAULT_PROMPTS.keys()))
    st.code(DEFAULT_PROMPTS[prompt_choice], language="text")

    st.header("Knowledge Base")
    kb_text = st.text_area("Paste internal notes or guidance", height=180, placeholder="Optional: paste house rules, research notes, or communication guidance here.")
    kb_keywords = top_keywords(kb_text, 10) if kb_text else []
    if kb_keywords:
        st.write("**Detected concepts:**")
        st.write(", ".join(kb_keywords))

tabs = st.tabs([
    "Workflow Mapper",
    "Research Brief",
    "Meeting Prep",
    "CRM & Follow-up",
    "Reporting Studio",
    "Sales Support"
])

with tabs[0]:
    st.subheader("Map a workflow and identify automation opportunities")
    wf = st.text_area("Describe the current workflow", height=180, placeholder="Example: We manually prepare investor notes, summarize meetings, update CRM, and create weekly reporting decks.")
    if st.button("Analyze workflow"):
        steps = classify_workflow_steps(wf)
        suggestions = suggest_automation(wf)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Detected workflow steps**")
            st.write(steps)
            st.markdown("**Potential bottlenecks**")
            st.write([
                "Manual summarization and inconsistent note quality",
                "Repeated drafting across reports, meetings, and CRM entries",
                "Fragmented knowledge across documents and email threads"
            ])
        with col2:
            st.markdown("**Suggested AI opportunities**")
            st.write(suggestions)
            st.markdown("**Expected gains**")
            st.write([
                "Better output consistency",
                "Faster turnaround time",
                "Less manual rework",
                "Improved knowledge reuse"
            ])

with tabs[1]:
    st.subheader("Generate a research or investment brief")
    topic = st.text_input("Topic / manager / theme", placeholder="e.g. European climate tech VC fund")
    notes = st.text_area("Research notes / source text", height=220)
    if st.button("Create research brief"):
        brief = make_research_brief(topic, notes)
        for k, v in brief.items():
            st.markdown(f"**{k}**")
            st.write(v)

with tabs[2]:
    st.subheader("Prepare for a meeting")
    entity = st.text_input("Meeting with", placeholder="Investor / Fund manager / Internal stakeholder")
    context = st.text_area("Context / notes", height=220)
    if st.button("Create meeting pack"):
        pack = make_meeting_prep(entity, context)
        for k, v in pack.items():
            st.markdown(f"**{k}**")
            st.write(v)

with tabs[3]:
    st.subheader("Turn raw notes into CRM-ready updates and a follow-up")
    contact = st.text_input("Contact name")
    meeting_notes = st.text_area("Meeting notes", height=220)
    if st.button("Generate CRM update"):
        crm = make_crm_update(contact, meeting_notes)
        for k, v in crm.items():
            st.markdown(f"**{k}**")
            st.write(v)
        st.markdown("**Follow-up email draft**")
        st.code(make_followup_email(contact, meeting_notes))

with tabs[4]:
    st.subheader("Create a concise internal report")
    report_title = st.text_input("Report title", placeholder="Weekly investor activity update")
    raw_notes = st.text_area("Paste notes or source material", height=220)
    if st.button("Generate report"):
        report = generate_report(report_title, raw_notes)
        for k, v in report.items():
            st.markdown(f"**{k}**")
            st.write(v)

with tabs[5]:
    st.subheader("Support research, data analysis, and presentation prep")
    uploaded = st.file_uploader("Upload a CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.write("**Preview**")
        st.dataframe(df.head(), use_container_width=True)

        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            col = st.selectbox("Select numeric column", numeric.columns.tolist())
            fig, ax = plt.subplots()
            ax.hist(df[col].dropna(), bins=12)
            ax.set_title(f"Distribution of {col}")
            st.pyplot(fig)
            st.markdown("**Quick insight**")
            st.write(f"The distribution of {col} shows where values are concentrated and can be used to support presentation materials or discussion points.")
        else:
            st.info("No numeric columns detected.")
    else:
        st.info("Upload a CSV to generate quick analysis and slide-ready discussion points.")

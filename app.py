#!/usr/bin/env python3
"""
AI Image Analyzer — Streamlit Web UI
=====================================
A drag-and-drop web interface for the AI Image Analyzer forensic tool.

Allows users to upload an image and see:
  • The uploaded image
  • Overall AI probability score with a visual bar
  • Per-test breakdown with individual scores and explanations
  • Download buttons for HTML and JSON reports

Prerequisites
-------------
    pip install streamlit pillow numpy opencv-python-headless scipy

Run
---
    streamlit run app.py

Then open http://localhost:8501 in your browser.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Ensure the project directory is on sys.path so we can import ai_image_analyzer
# Regardless of where Streamlit is launched from
_PROJECT_DIR = Path(__file__).resolve().parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

# If Streamlit is not installed, give the user a helpful message.
try:
    import streamlit as st
except ImportError:
    print(
        "ERROR: Streamlit is not installed.\n"
        "To run the web UI, install it first:\n"
        "    pip install streamlit\n"
        "Then run:\n"
        "    streamlit run app.py"
    )
    raise

# Import the analyzer (will be available once this file is in the project dir)
try:
    from ai_image_analyzer import (
        analyze_image,
        generate_html_report,
        AI_THRESHOLD,
        UNCERTAIN_LOW,
    )
except ImportError as exc:
    st.error(
        f"The analyzer module could not be imported: {exc}\n\n"
        "Make sure you run `streamlit run app.py` from the project directory "
        "where `ai_image_analyzer.py` resides."
    )
    st.stop()

# ── Page configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Image Analyzer",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────
SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp", "gif", "tiff", "tif"]

# ── Sidebar ────────────────────────────────────────────────────────────────

st.sidebar.title("🔍 AI Image Analyzer")
st.sidebar.markdown(
    """
    A forensic tool that detects AI-generated images using six
    complementary techniques:
    
    1. **Metadata Forensics**
    2. **C2PA Metadata Verification**
    3. **Noise Pattern Analysis**
    4. **Frequency Domain Analysis**
    5. **Statistical Analysis**
    6. **Visual Artifact Detection**
    """
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Verdict Thresholds (v2.0):**
    | AI Probability | Verdict |
    |---|
    | < 30% | 🟢 Real Camera Photo |
    | 30–65% | 🟡 Uncertain |
    | > 65% | 🔴 AI-Generated |
    """
)

st.sidebar.markdown("---")
st.sidebar.info(
    "⚠️ Educational / research use only. "
    "No automated detector is 100 % reliable."
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _verdict_badge(score: float) -> str:
    """Return an emoji + verdict label for a given AI probability score."""
    if score < UNCERTAIN_LOW:
        return "🟢 Real Camera Photo"
    elif score <= AI_THRESHOLD:
        return "🟡 Uncertain / Mixed Signals"
    else:
        return "🔴 AI-Generated"


def _verdict_color(score: float) -> str:
    """Return a hex colour for the verdict."""
    if score < UNCERTAIN_LOW:
        return "#28a745"  # green
    elif score <= AI_THRESHOLD:
        return "#ffc107"  # amber
    else:
        return "#dc3545"  # red


def _truncate_text(text: str, max_len: int = 200) -> str:
    """Truncate long text with an ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


# ── Main UI ────────────────────────────────────────────────────────────────

st.title("🔍 AI Image Analyzer")
st.markdown(
    """
    Upload an image to analyse it for AI-generation fingerprints.
    The tool runs **six forensic tests** and combines their results into
    an overall AI-probability score.
    """
)

# ── File upload ────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drag & drop an image here, or click to browse",
    type=SUPPORTED_FORMATS,
    help="Supported formats: "
         + ", ".join(ext.upper() for ext in SUPPORTED_FORMATS),
)

if uploaded_file is not None:
    # Save to a temporary file so the analyzer can read it
    with tempfile.NamedTemporaryFile(
        suffix=f".{uploaded_file.name.split('.')[-1].lower()}",
        delete=False,
    ) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        with st.spinner("🧪 Running forensic analysis..."):
            report = analyze_image(tmp_path)

        # ── Image preview + overall score (side by side) ───────────────────
        col_img, col_score = st.columns([1, 1], gap="large")

        with col_img:
            st.image(
                tmp_path,
                caption=f"Uploaded: {uploaded_file.name}",
                use_container_width=True,
            )

        with col_score:
            ai_pct = report.overall_score
            real_pct = 100.0 - ai_pct
            verdict = report.verdict
            color = _verdict_color(ai_pct)
            badge = _verdict_badge(ai_pct)

            st.markdown(
                f"<h1 style='text-align: center; color: {color}'>"
                f"{ai_pct:.1f}%</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<h3 style='text-align: center'>{badge}</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='text-align: center; color: #888'>"
                f"Real confidence: {real_pct:.1f}%<br>"
                f"Overall confidence: {report.overall_confidence:.0%}"
                f"</p>",
                unsafe_allow_html=True,
            )

            # Visual score bar
            st.markdown(
                f"""
                <div style="background: linear-gradient(90deg, #004d00 0%, #00d4ff 50%, #8B0000 100%);
                            height: 24px; border-radius: 6px; position: relative;">
                    <div style="position: absolute; top: -6px; left: {ai_pct:.1f}%;
                                width: 3px; height: 36px; background: #fff;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #888">
                    <span>0% REAL</span><span>50%</span><span>100% AI</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Overall summary ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 📋 Summary\n*{report.summary}*")

        # ── Per-test breakdown ─────────────────────────────────────────────
        st.markdown("### 🔬 Test Breakdown")

        for test in report.tests:
            ai_p = test.score
            real_p = 100.0 - ai_p
            color = _verdict_color(ai_p)
            badge = _verdict_badge(ai_p)

            with st.expander(
                f"{test.name} — AI: {ai_p:.0f}% | Real: {real_p:.0f}% ({badge})",
                icon="🔍",
            ):
                cols = st.columns([2, 1])

                with cols[0]:
                    # Inline bar visualization
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(90deg,
                            #004d00 0%, #00d4ff 50%, #8B0000 100%);
                            height: 18px; border-radius: 4px; position: relative;">
                            <div style="position: absolute; top: -4px; left: {ai_p:.1f}%;
                                        width: 2px; height: 26px; background: #fff;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between;
                                    font-size: 0.8em; color: #888; margin-top: 2px">
                            <span>0% REAL</span><span>50%</span><span>100% AI</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Confidence:** {test.confidence:.0%}")
                    st.markdown(f"**Verdict:** {test.verdict}")
                    st.markdown(f"**Explanation:** {_truncate_text(test.explanation, 500)}")

                with cols[1]:
                    if test.details:
                        detail_lines = []
                        for key, value in test.details.items():
                            if isinstance(value, dict):
                                val_str = json.dumps(value, default=str)[:100]
                            elif isinstance(value, (list, tuple)):
                                val_str = ", ".join(str(v) for v in value)[:100]
                            else:
                                val_str = str(value)[:100]
                            detail_lines.append(f"**{key}:** {val_str}")
                        st.markdown("\n".join(detail_lines))

        # ── Download buttons ───────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Download Reports")

        col_html, col_json = st.columns(2)

        with col_html:
            try:
                html_content = generate_html_report(report, tmp_path)
            except Exception:
                html_content = "<html><body><h1>HTML Report Error</h1></body></html>"

            st.download_button(
                label="📄 Download HTML Report",
                data=html_content,
                file_name="ai_analysis_report.html",
                mime="text/html",
                use_container_width=True,
            )

        with col_json:
            json_content = json.dumps(report.to_dict(), indent=2)
            st.download_button(
                label="📋 Download JSON Report",
                data=json_content,
                file_name="ai_analysis_report.json",
                mime="application/json",
                use_container_width=True,
            )

        # ── Metadata details (optional) ────────────────────────────────────
        with st.expander("📷 Image Metadata Details", icon="ℹ️"):
            st.markdown(
                f"**File:** {report.image_path}\n"
                f"**Resolution:** {report.image_size[0]} × {report.image_size[1]}\n"
                f"**File size:** {report.file_size / 1024:.1f} KB\n"
                f"**Analysis timestamp:** {report.timestamp}"
            )

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        st.exception(e)

    finally:
        # Clean up the temporary file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

else:
    # ── No file uploaded — show placeholder ──────────────────────────────────
    st.markdown("---")
    st.info("📤 **Upload an image to begin analysis.** "
            "The tool will run six forensic tests and display the results.")

    # Show example / instructions
    with st.expander("📖 How to use this tool", expanded=True):
        st.markdown(f"""
        1. **Upload** an image using the drag-and-drop area above.
        2. Wait for the **six forensic tests** to complete (usually 1–3 seconds).
        3. Review the **overall AI probability** and **per-test breakdown**.
        4. **Download** the HTML or JSON report for offline reference.

        **Supported formats:** `{', '.join(ext.upper() for ext in SUPPORTED_FORMATS)}`

        **Verdict scale:**
        | AI Probability | Verdict |
        |----------------|---------|
        | < 30% | Real Camera Photo |
        | 30–65% | Uncertain / Mixed Signals |
        | > 65% | AI-Generated |

        > **Note:** This tool is for educational and research use only.
        > No automated detector is 100 % reliable. Always use human
        > judgment when interpreting results. For cryptographically secure
        > provenance, check C2PA / Content Credentials signatures.
        """)


# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888; font-size: 0.8em'>"
    "AI Image Analyzer v2.1 · Built for AI safety research · "
    "Educational use only</p>",
    unsafe_allow_html=True,
)

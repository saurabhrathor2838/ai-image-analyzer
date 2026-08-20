#!/usr/bin/env python3
"""
AI Image Analyzer — Streamlit Web UI  (v3.1 Ensemble Edition)
================================================================
A full-immersion, dark-theme web interface for the AI Image Analyzer
forensic tool.  Features:

  • Heavy CSS injection — glassmorphism containers, soft gradient borders,
    rounded corners, custom hover effects, sleek typography.
  • Full-page interactive background — CSS-animated particle network +
    floating data-stream wireframes.
  • Custom drag-and-drop dropzone (styled over the default uploader).
  • Multi-column KPI dashboard with CSS conic-gradient progress rings.
  • Color-coded verdict badges (emerald / amber / crimson).
  • Collapsible accordion sidebar for test descriptions.

Run
---
    python -m streamlit run app.py

Then open http://localhost:8501 in your browser.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure project dir is on sys.path regardless of launch cwd
_PROJECT_DIR = Path(__file__).resolve().parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

# ── Streamlit import ──────────────────────────────────────────────────────
try:
    import streamlit as st
except ImportError:
    print(
        "ERROR: Streamlit is not installed.\n"
        "To run the web UI:\n"
        "    python -m pip install streamlit\n"
        "    python -m streamlit run app.py"
    )
    raise

# ── Analyzer import ───────────────────────────────────────────────────────
try:
    from ai_image_analyzer import (  # noqa: E402
        analyze_image,
        generate_html_report,
        generate_heatmap,
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

# ── Page configuration ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Image Analyzer • Forensics Lab",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────
SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp", "gif", "tiff", "tif"]

# ── Inject all CSS (background, glassmorphism, dropzone, progress rings) ───
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global resets & theme ────────────────────────────── */
    html, body, .main, .stSidebar, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .stApp {
        background: #0a0a12;
        overflow: hidden;
    }

    * {
        scrollbar-width: thin;
        scrollbar-color: #3a3a4e #1a1a2e;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1a1a2e; }
    ::-webkit-scrollbar-thumb { background: #3a3a4e; border-radius: 4px; }

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* ── Full-page particle network background ────────────── */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: -2;
        background: radial-gradient(circle at 20% 50%, #1a1a2e 0%, transparent 50%),
                    radial-gradient(circle at 80% 30%, #16213e 0%, transparent 50%),
                    radial-gradient(circle at 50% 80%, #0f3460 0%, transparent 50%);
    }

    /* Floating particles */
    .particle {
        position: fixed;
        background: rgba(100, 200, 255, 0.4);
        border-radius: 50%;
        animation: float 20s linear infinite;
        z-index: -1;
        pointer-events: none;
    }
    @keyframes float {
        0%   { transform: translateY(0) translateX(0) rotate(0deg); opacity: 0; }
        5%   { opacity: 0.6; }
        50%  { opacity: 0.8; }
        95%  { opacity: 0.4; }
        100% { transform: translateY(-1200px) translateX(300px) rotate(360deg); opacity: 0; }
    }

    /* Data-stream wireframes (diagonal lines) */
    .data-stream {
        position: fixed;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.05), transparent);
        z-index: -1;
        pointer-events: none;
    }
    @keyframes streamMove {
        0%   { transform: translateX(-100%); }
        100% { transform: translateX(200%); }
    }

    /* ── Glassmorphism containers ──────────────────────────── */
    .glass-card {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        backdrop-filter: blur(16px) saturate(1.1);
        -webkit-backdrop-filter: blur(16px) saturate(1.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.30),
                    inset 0 1px 0 rgba(255, 255, 255, 0.06);
        margin-bottom: 18px;
    }

    .glass-panel {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 18px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.20);
    }

    /* ── Gradient border glow ─────────────────────────────── */
    .gradient-border {
        position: relative;
        border-radius: 18px;
    }
    .gradient-border::before {
        content: '';
        position: absolute;
        inset: -1px;
        border-radius: 19px;
        z-index: -1;
        padding: 1px;
        background: linear-gradient(135deg,
            rgba(0, 212, 255, 0.50) 0%,
            rgba(100, 200, 255, 0.30) 50%,
            rgba(255, 87, 114, 0.40) 100%);
        -webkit-mask:
            linear-gradient(#fff 0 0) content-box,
            linear-gradient(#fff 0 0);
        -webkit-mask-composite: destination-out;
        mask-composite: exclude;
    }

    /* ── Custom dropzone ───────────────────────────────────── */
    .upload-container {
        border: 2px dashed rgba(100, 200, 255, 0.3);
        border-radius: 16px;
        padding: 40px 30px;
        text-align: center;
        background: rgba(15, 23, 42, 0.40);
        backdrop-filter: blur(16px) saturate(1.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .upload-container:hover {
        border-color: rgba(0, 212, 255, 0.6);
        background: rgba(15, 23, 42, 0.55);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.12);
    }
    .upload-container.drag-over {
        border-color: rgba(0, 212, 255, 0.8);
        background: rgba(15, 23, 42, 0.65);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.25);
    }
    .upload-icon {
        font-size: 3em;
        margin-bottom: 12px;
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }
    .upload-container:hover .upload-icon { opacity: 1; }

    /* Hide default Streamlit uploader but keep it functional */
    .stFileUploader > div:first-child {
        display: none !important;
    }

    /* ── KPI Cards ──────────────────────────────────────────── */
    .kpi-card {
        background: rgba(15, 23, 42, 0.45);
        border-radius: 16px;
        padding: 22px 18px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(14px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.40);
        border-color: rgba(100, 200, 255, 0.25);
    }
    .kpi-value {
        font-size: 2em;
        font-weight: 700;
        letter-spacing: -0.03em;
    }
    .kpi-label {
        font-size: 0.85em;
        color: #8a94a6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    /* ── Circular progress ring ───────────────────────────── */
    .progress-ring {
        position: relative;
        width: 160px;
        height: 160px;
        margin: 0 auto;
    }
    .progress-ring svg {
        transform: rotate(-90deg);
    }
    .progress-ring circle {
        fill: none;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.8s ease-out;
    }
    .progress-ring-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }

    /* ── Verdict badges ─────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1em;
        letter-spacing: 0.5px;
    }
    .badge-real    { background: linear-gradient(135deg, #00c9a7, #007acc); color: #fff; }
    .badge-amber   { background: linear-gradient(135deg, #ffb347, #ff6b35); color: #1a1a2e; }
    .badge-ai      { background: linear-gradient(135deg, #ff5f6d, #ffc371); color: #0a0a12; }

    /* ── Test result cards ──────────────────────────────────── */
    .test-card {
        background: rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 3px solid rgba(100, 200, 255, 0.4);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: border-color 0.3s ease, background 0.3s ease;
    }
    .test-card:hover {
        border-left-color: rgba(0, 212, 255, 0.8);
        background: rgba(15, 23, 42, 0.55);
    }
    .test-card h4 {
        color: #ffffff;
        font-size: 1.05em;
        margin: 0 0 4px 0;
    }
    .test-card .score-chip {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .score-chip-real { background: rgba(40, 167, 69, 0.2); color: #28a745; }
    .score-chip-ai  { background: rgba(220, 53, 69, 0.2); color: #dc3545; }
    .score-chip-mid { background: rgba(255, 193, 7, 0.2); color: #ffc107; }

    /* ── Custom buttons ─────────────────────────────────────── */
    .stButton button[kind="primary"],
    .css-1cpxjq4 .stButton > button {
        background: linear-gradient(135deg, #0066cc, #00b5ff);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.95em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 180, 255, 0.25);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 180, 255, 0.35);
    }
    .stButton button[kind="primary"]:hover {
        filter: brightness(1.1);
    }

    /* Download button styling */
    .stDownloadButton button {
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff !important;
        border: 1px solid rgba(100, 200, 255, 0.3);
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stDownloadButton button:hover {
        background: rgba(100, 200, 255, 0.15);
        border-color: rgba(0, 212, 255, 0.6);
        transform: translateY(-2px);
    }

    /* ── Summary table ──────────────────────────────────────── */
    .summary-table th {
        background: rgba(0, 212, 255, 0.1);
        color: #ffffff;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8em;
        letter-spacing: 0.05em;
    }
    .summary-table td {
        color: #c5c9d1;
    }
    .summary-table tr:nth-child(even) {
        background: rgba(15, 23, 42, 0.25);
    }
    .summary-table tr:hover {
        background: rgba(15, 23, 42, 0.45);
    }

    /* ── Sidebar styling ───────────────────────────────────── */
    .stSidebar .stMarkdown,
    .stSidebar .stTitle,
    .stSidebar .stInfo,
    .stSidebar .stTextInput {
        color: #c5c9d1 !important;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {
        color: #00d4ff !important;
    }

    /* ── Expander (accordion) styling ───────────────────────── */
    .streamlit-expander {
        background: rgba(15, 23, 42, 0.30);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
    }
    .streamlit-expander .streamlit-expander-header {
        color: #c5c9d1 !important;
        font-weight: 600;
    }
    .streamlit-expander .streamlit-expander-content {
        color: #8a94a6 !important;
    }

    /* ── Spinner / loader ───────────────────────────────────── */
    .stSpinner {
        color: #00d4ff !important;
    }

    /* ── Image border ───────────────────────────────────────── */
    .stImage img {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* ── Main content padding ───────────────────────────────── */
    .main .block-container {
        padding-top: 40px;
        padding-bottom: 60px;
    }

    /* ── Footer ─────────────────────────────────────────────── */
    .footer {
        text-align: center;
        color: #4a4a6a;
        font-size: 0.8em;
        padding: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin-top: 30px;
    }

    /* Hide the default file uploader label text */
    .stFileUploader .css-1uibutton { display: none; }
    """,
    unsafe_allow_html=True,
)

# ── JavaScript: inject particle network & data streams ──────────────────────
# Streamlit's st.markdown does NOT execute <script> tags (React's
# dangerouslySetInnerHTML strips them).  We use streamlit.components.v1.html()
# which renders a real iframe and properly runs JS.
import streamlit.components.v1 as components  # noqa: E402

_PARTICLE_JS = """
<script>
(function() {
    var doc = window.parent.document;
    // Create container divs in the parent page so the CSS from st.markdown
    // can style them (the .particle class is defined in the main CSS block).
    var container = doc.createElement('div');
    container.id = 'bg-particles';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '-1';
    doc.body.appendChild(container);

    var ns = 80;
    for (var i = 0; i < ns; i++) {
        var p = doc.createElement('div');
        p.className = 'particle';
        var size = Math.random() * 3 + 1;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + 'vw';
        p.style.top = Math.random() * 100 + 'vh';
        var dur = 15 + Math.random() * 15;
        p.style.animationDuration = dur + 's';
        p.style.animationDelay = -Math.random() * dur + 's';
        var opacity = 0.1 + Math.random() * 0.3;
        p.style.background = 'rgba(100, 200, 255, ' + opacity + ')';
        container.appendChild(p);
    }

    // Draw connecting lines via canvas overlay — must also be in parent
    var canvas = doc.createElement('canvas');
    canvas.id = 'bg-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '-1';
    canvas.style.pointerEvents = 'none';
    doc.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    var particles = [];
    for (var j = 0; j < 60; j++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = 'rgba(100, 200, 255, 0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (var a = 0; a < particles.length; a++) {
            for (var b = a + 1; b < particles.length; b++) {
                var dx = particles[a].x - particles[b].x;
                var dy = particles[a].y - particles[b].y;
                if (dx * dx + dy * dy < 10000) {
                    ctx.moveTo(particles[a].x, particles[a].y);
                    ctx.lineTo(particles[b].x, particles[b].y);
                }
            }
        }
        ctx.stroke();

        for (var k = 0; k < particles.length; k++) {
            particles[k].x += particles[k].vx;
            particles[k].y += particles[k].vy;
            if (particles[k].x < 0) particles[k].x = canvas.width;
            if (particles[k].x > canvas.width) particles[k].x = 0;
            if (particles[k].y < 0) particles[k].y = canvas.height;
            if (particles[k].y > canvas.height) particles[k].y = 0;
        }
        requestAnimationFrame(animate);
    }
    animate();
})();
</script>
"""

components.html(_PARTICLE_JS, height=0)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="glass-card" style="margin-bottom: 0;">
            <h1 style="color: #00d4ff; margin: 0; font-size: 1.6em;">🔍 Forensics Lab</h1>
            <p style="color: #8a94a6; font-size: 0.9em; margin: 4px 0 0 0;">
                v3.0 — AI Image Detector
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Verdict thresholds accordion ──────────────────────────────────
    with st.expander("📊 Verdict Thresholds", icon="🎯"):
        st.markdown("""
        | AI Probability | Verdict          | Badge |
        |----------------|------------------|-------|
        | **< 20%**      | Real Camera Photo | 🟢    |
        | **20–55%**     | Uncertain        | 🟡    |
        | **> 55%**      | AI-Generated     | 🔴    |
        """)

    # ── Test descriptions accordion ─────────────────────────────────
    with st.expander("🔬 The Eight Forensic Tests", icon="🔍"):
        test_info = [
            ("Metadata Forensics", "Missing camera make/model, absent timestamps, AI tool signatures, resolution divisible by 64"),
            ("C2PA Metadata Verification", "C2PA ContentCredentials manifests, AI tool signatures in XMP/raw headers, EXIF completeness"),
            ("Noise Pattern Analysis", "Uniform noise across regions, absence of CFA/Bayer interpolation patterns, chroma noise patterns"),
            ("Frequency Domain Analysis", "Flat spectral slope, excessive high-frequency energy, periodic grid patterns"),
            ("Statistical Analysis", "Histogram entropy, inter-channel correlation, pixel distribution kurtosis, double-JPEG traces"),
            ("Visual Artifact Detection", "Over-smoothing, unnatural symmetry, abnormal edge density, text/grid anomalies"),
            ("Deep Learning Detector", "Swin Transformer CNN model fine-tuned on AI-generated vs real photographs"),
            ("Error Level Analysis", "JPEG recompression error patterns, block-level uniformity, compression artefact distribution"),
        ]
        for name, desc in test_info:
            st.markdown(f"**• {name}**\n<br><small style='color:#8a94a6'>{desc}</small>", unsafe_allow_html=True)

    # ── About accordion ────────────────────────────────────────────────
    with st.expander("ℹ️ About This Tool", icon="ℹ️"):
        st.markdown("""
        This tool helps determine whether an image was created by an AI
        model or captured by a real camera. It is for **educational and
        research use only** — no automated detector is 100% reliable.
        """)

    # ── Disclaimer ──────────────────────────────────────────────────────
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #8a94a6; font-size: 0.8em;'>⚠️ Educational / research use only. "
        "No automated detector is 100% reliable.</p>",
        unsafe_allow_html=True,
    )


# ── Helper functions ────────────────────────────────────────────────────────

def _badge_class(score: float) -> str:
    """Return CSS class for verdict badge."""
    if score < UNCERTAIN_LOW:
        return "badge-real"
    elif score <= AI_THRESHOLD:
        return "badge-amber"
    else:
        return "badge-ai"


def _badge_text(score: float) -> str:
    """Return verdict label."""
    if score < UNCERTAIN_LOW:
        return "Real Camera Photo"
    elif score <= AI_THRESHOLD:
        return "Uncertain / Mixed Signals"
    else:
        return "AI-Generated"


def _badge_html(score: float) -> str:
    """Return HTML for a color-coded verdict badge."""
    cls = _badge_class(score)
    text = _badge_text(score)
    return f'<span class="badge {cls}">{text}</span>'


def _ring_color(score: float) -> tuple[str, str, str]:
    """Return (track_color, progress_color, bg_color) for the progress ring."""
    r = min(1.0, score / 100.0)
    if score < UNCERTAIN_LOW:
        # Green → real
        return (
            "rgba(40, 167, 69, 0.15)",
            "rgba(40, 167, 69, 0.9)",
            "rgba(40, 167, 69, 0.1)",
        )
    elif score <= AI_THRESHOLD:
        # Amber → uncertain
        return (
            "rgba(255, 193, 7, 0.15)",
            "rgba(255, 193, 7, 0.9)",
            "rgba(255, 193, 7, 0.1)",
        )
    else:
        # Red → AI
        return (
            "rgba(220, 53, 69, 0.15)",
            "rgba(220, 53, 69, 0.9)",
            "rgba(220, 53, 69, 0.1)",
        )


def _progress_ring(score: float) -> str:
    """Generate HTML/CSS for a circular progress ring (conic-gradient)."""
    pct = max(0, min(100, score))
    track_color, progress_color, bg_color = _ring_color(pct)
    # Use conic-gradient: progress fills pct% of the circle
    return f"""
    <div style="
        width: 160px; height: 160px; margin: 0 auto;
        border-radius: 50%;
        background: conic-gradient(
            from 0deg,
            {progress_color} 0deg {pct * 3.6}deg,
            {track_color} {pct * 3.6}deg 360deg
        );
        display: flex; align-items: center; justify-content: center;
        box-shadow: inset 0 0 20px {bg_color};
    ">
        <div style="
            background: rgba(10, 14, 18, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 50%;
            width: 110px; height: 110px;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
        ">
            <span style="font-size: 1.8em; font-weight: 700; color: {progress_color};">
                {pct:.1f}%
            </span>
            <span style="font-size: 0.7em; color: #8a94a6; margin-top: 4px;">
                AI Probability
            </span>
        </div>
    </div>
    """


def _score_chip(score: float) -> str:
    """Return HTML for a small score chip next to test names."""
    pct = max(0, min(100, score))
    if score < UNCERTAIN_LOW:
        cls, label = "score-chip-real", "REAL"
    elif score <= AI_THRESHOLD:
        cls, label = "score-chip-mid", "MID"
    else:
        cls, label = "score-chip-ai", "AI"
    return f'<span class="{cls}">{pct:.0f}% · {label}</span>'


def _truncate(text: str, max_len: int = 300) -> str:
    """Truncate long text with an ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _format_details(details: dict) -> str:
    """Format a test's details dict into HTML lines."""
    lines = []
    for key, value in details.items():
        if isinstance(value, dict):
            inner = json.dumps(value, default=str, indent=2)[:200]
            lines.append(f"<b>{key}:</b> <code style='color:#66ccff'>{inner}</code>")
        elif isinstance(value, (list, tuple)):
            val_str = ", ".join(str(v) for v in value)[:120]
            lines.append(f"<b>{key}:</b> <span style='color:#c5c9d1'>{val_str}</span>")
        elif isinstance(value, bool):
            lines.append(f"<b>{key}:</b> <span style='color:#66ccff'>{'✓' if value else '✗'}</span>")
        elif isinstance(value, float):
            lines.append(f"<b>{key}:</b> <span style='color:#c5c9d1'>{value:.4f}</span>")
        elif isinstance(value, int):
            lines.append(f"<b>{key}:</b> <span style='color:#c5c9d1'>{value}</span>")
        else:
            lines.append(f"<b>{key}:</b> <span style='color:#c5c9d1'>{str(value)[:120]}</span>")
    return "<br>".join(lines)


def _inject_particles(n: int = 60):
    """Inject CSS-animated particle elements into the page."""
    particles_html = ""
    for _ in range(n):
        size = 1 + 2  # will be randomized per-particle in JS instead
        particles_html += f'<div class="particle" style="width:{size}px;height:{size}px;"></div>'
    return particles_html


# ── Main content ────────────────────────────────────────────────────────────

# Title + intro
st.markdown(
    """
    <div class="glass-card gradient-border" style="margin-bottom: 24px;">
        <div style="display:flex; align-items:center; gap:14px;">
            <span style="font-size:2.4em;">🔍</span>
            <div>
                <h1 style="margin:0; color:#00d4ff; font-size:2em;">AI Image Detector</h1>
                <h2 style="margin:4px 0 0 0; color:#ffffff; font-size:1em; font-weight:400;">
                    Deep Visual Analysis · Eight forensic tests · Real-time results
                </h2>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Custom drag-and-drop dropzone ──────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Style the file uploader to look like a dropzone */
    .stFileUploader {
        margin: 0 !important;
        padding: 0 !important;
    }
    .stFileUploader > div {
        background: rgba(15, 23, 42, 0.40) !important;
        border: 2px dashed rgba(100, 200, 255, 0.3) !important;
        border-radius: 16px !important;
        padding: 40px 30px !important;
        text-align: center !important;
        backdrop-filter: blur(16px) saturate(1.1) !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader > div:hover {
        border-color: rgba(0, 212, 255, 0.6) !important;
        background: rgba(15, 23, 42, 0.55) !important;
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.12) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "🔍 Drag & drop an image here, or click to browse",
    type=SUPPORTED_FORMATS,
    help="Supported: JPEG, PNG, BMP, WebP, GIF, TIFF",
    key="file_uploader",
    label_visibility="visible",
)

# ── No file uploaded — show instructions ────────────────────────────────────
if uploaded_file is None:
    st.markdown("---")
    st.markdown(
        """
        <div class="glass-panel" style="text-align: center; padding: 40px;">
            <p style="font-size: 1.4em; color: #c5c9d1;">
                📤 Upload an image to begin forensic analysis.
            </p>
            <p style="color: #8a94a6; font-size: 0.95em; margin-top: 12px;">
                The tool runs eight forensic tests and displays results
                with real-time scoring and interactive visualizations.
            </p>
            <div style="margin-top: 24px;">
                <span style="display:inline-block; padding:6px 16px; border-radius:8px;
                             background:rgba(0,212,255,0.1); color:#00d4ff; font-size:0.85em;">
                    Supported: JPG, PNG, BMP, WebP, GIF, TIFF
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📖 How It Works", expanded=True):
        st.markdown("""
        1. **Upload** an image using the drag-and-drop area above.
        2. Wait for the **eight forensic tests** to complete (1–3 seconds).
        3. Review the **overall AI probability** and **per-test breakdown**.
        4. **Download** the HTML or JSON report for offline reference.

        > **Note:** This tool is for educational and research use only.
        > No automated detector is 100 % reliable. Always use human
        > judgment when interpreting results.
        """)

else:
    # ── Save temp file & run analysis ────────────────────────────────────────
    with tempfile.NamedTemporaryFile(
        suffix=f".{uploaded_file.name.split('.')[-1].lower()}",
        delete=False,
    ) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        with st.spinner("🧪 Running forensic analysis..."):
            report = analyze_image(tmp_path, threshold=0.55)

        # ── Header: image name + verdict badge ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        col_title, col_badge = st.columns([3, 1], gap="small")
        with col_title:
            st.markdown(
                f"<h2 style='margin:0; color:#ffffff'>Analysis: <span style='color:#00d4ff'>"
                f"{uploaded_file.name}</span></h2>",
                unsafe_allow_html=True,
            )
        with col_badge:
            st.markdown(_badge_html(report.overall_score), unsafe_allow_html=True)

        # ── DeepAI-style neon KPI pill badges ───────────────────────────────
        # Horizontal pills: AI Likelihood / Confidence Level / Verdict, plus
        # the raw Vision-Transformer prediction surfaced on the dashboard.
        dl_test = next(
            (t for t in report.tests if t.name and t.name.lower().split()[0] == "deep"),
            None,
        )
        dl_raw = dl_test.score if dl_test else None
        dl_sub = f" · ViT raw: {dl_raw:.1f}% AI" if dl_raw is not None else ""
        is_ai = report.overall_score >= AI_THRESHOLD
        verdict_label = _badge_text(report.overall_score)
        if is_ai:
            glow, bg = "0 0 12px #ff0055, 0 0 24px #ff0055", "linear-gradient(135deg, #2a0a1a, #4a0a2a)"
        elif report.overall_score < UNCERTAIN_LOW:
            glow, bg = "0 0 12px #00e676, 0 0 24px #00e676", "linear-gradient(135deg, #0a2a0a, #0a4a1a)"
        else:
            glow, bg = "0 0 12px #ffd600, 0 0 24px #ffd600", "linear-gradient(135deg, #2a220a, #4a3a0a)"

        resolution = f"{report.image_size[0]}×{report.image_size[1]}" if report.image_size else "—"
        size_str = f"{report.file_size / 1024:.0f} KB" if report.file_size else "—"

        st.markdown(
            f"""
            <style>
              .neon-pill {{ display:inline-block; border-radius:999px; padding:12px 22px;
                              font-size:1.2em; font-weight:700; color:#ffffff;
                              border: 1px solid rgba(255,255,255,0.18);
                              text-shadow: 0 0 6px rgba(0,0,0,0.7); }}
              .neon-pill .sub {{ font-size:0.5em; opacity:0.78; font-weight:400;
                                  display:block; margin-top:2px; }}
              .neon-row {{ display:flex; gap:16px; align-items:center; flex-wrap:wrap;
                          margin: 4px 0 2px 0; }}
            </style>
            <div class="neon-row">
              <span class="neon-pill" style="box-shadow: {glow}; background: {bg};">
                {report.overall_score:.1f}%<span class="sub">AI Likelihood{dl_sub}</span>
              </span>
              <span class="neon-pill" style="background:linear-gradient(135deg,#2a220a,#4a3a0a);
                     box-shadow:0 0 12px #ffd600,0 0 24px #ffd600;">
                {report.overall_confidence:.0%}<span class="sub">Confidence Level</span>
              </span>
              <span class="neon-pill" style="box-shadow: {glow}; background: {bg};">
                {verdict_label}<span class="sub">Verdict Classification</span>
              </span>
            </div>
            <div style="font-size:0.82em; color:#8a94a6; margin-top:4px;">
              {resolution} · {size_str}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Progress ring + image preview ────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        col_ring, col_image, col_verdict = st.columns([1, 1.2, 1], gap="medium")

        with col_ring:
            st.markdown(
                f"""
                <div class="glass-panel" style="text-align:center; padding:30px 20px;">
                    {_progress_ring(report.overall_score)}
                    <div style="margin-top:16px;">
                        {_badge_html(report.overall_score)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_image:
            import base64 as _b64
            try:
                with open(tmp_path, "rb") as _f:
                    _b64img = _b64.b64encode(_f.read()).decode("ascii")
            except Exception:
                _b64img = ""
            _ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else "png"
            _mime = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "bmp": "image/bmp", "webp": "image/webp", "gif": "image/gif",
                "tiff": "image/tiff",
            }.get(_ext, "image/png")
            _pct = report.overall_score
            _word = "FAKE" if _pct >= AI_THRESHOLD else (
                "UNCERTAIN" if _pct > UNCERTAIN_LOW else "REAL"
            )
            _gcolor = "#00e676" if _pct < UNCERTAIN_LOW else "#ff0055"
            st.markdown(
                f"""
                <div style="position:relative; display:inline-block; width:100%;">
                  <img src="data:{_mime};base64,{_b64img}" style="width:100%;
                    border-radius:14px; display:block;" alt="Uploaded image"/>
                  <div style="position:absolute; bottom:14px; right:14px; z-index:2;
                    background:{_gcolor}; color:#ffffff; font-size:0.88em;
                    font-weight:700; padding:7px 16px; border-radius:999px;
                    box-shadow:0 0 10px {_gcolor}, 0 0 22px {_gcolor};
                    border:1px solid rgba(255,255,255,0.25);">
                    {_pct:.0f}% {_word}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_verdict:
            confidence = report.overall_confidence
            verdict_label = _badge_text(report.overall_score)
            st.markdown(
                f"""
                <div class="glass-panel" style="text-align:center; padding:30px;">
                    <h3 style="color:#ffffff; margin:0 0 12px 0;">Verdict</h3>
                    <div style="font-size:1.3em; font-weight:600; color:#ffffff; margin-bottom:12px;">
                        {verdict_label}
                    </div>
                    <div style="font-size:0.9em; color:#8a94a6; line-height:1.6;">
                        AI: <b style="color:#ff6b6b">{report.overall_score:.1f}%</b><br>
                        Real: <b style="color:#00c9a7">{100 - report.overall_score:.1f}%</b><br>
                        Confidence: <b style="color:#00d4ff">{confidence:.0%}</b>
                    </div>
                    <div style="margin-top:16px; font-size:0.85em; color:#4a4a6a; padding-top:12px;
                                border-top: 1px solid rgba(255,255,255,0.06);">
                        {report.timestamp}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── AI DETECTION HEATMAP overlay ───────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        show_heatmap = st.toggle(
            "🔥 AI DETECTION HEATMAP",
            value=False,
            help="Overlay an ELA-based heatmap (red/yellow = strongest generative artefacts).",
        )
        if show_heatmap:
            try:
                import numpy as _np
                import cv2 as _cv2
                _hm = generate_heatmap(tmp_path)            # BGR uint8 (ELA-derived)
                _orig = _cv2.imread(tmp_path)               # BGR uint8
                if _orig is None:
                    raise ValueError("could not decode preview image")
                if _hm.shape[:2] == _orig.shape[:2]:
                    _blend = _cv2.addWeighted(_hm, 0.38, _orig, 0.62, 0)
                else:
                    _blend = _hm
                _ok, _arr = _cv2.imencode(".png", _blend)
                if not _ok:
                    raise ValueError("heatmap encode failed")
                _buf = io.BytesIO(_arr.tobytes())
                st.image(
                    _buf,
                    caption="Heatmap overlay (red/yellow = generative artefacts)",
                    use_container_width=True,
                )
            except Exception as _e:
                st.warning(f"Could not generate heatmap: {_e}")

        # ── Summary ────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="glass-card gradient-border">
                <h3 style="color:#ffffff; margin:0 0 8px 0;">📋 Executive Summary</h3>
                <p style="color:#c5c9d1; margin:0; line-height:1.5;">
                    {report.summary}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Per-test breakdown ─────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='color:#ffffff; margin-bottom:12px;'>🔬 Forensic Test Breakdown</h3>",
            unsafe_allow_html=True,
        )

        for test in report.tests:
            ai_p = test.score
            real_p = 100.0 - ai_p
            confidence = test.confidence
            badge_text = _badge_text(ai_p)
            chip_html = _score_chip(ai_p)
            bg_gradient = ""
            if ai_p < UNCERTAIN_LOW:
                bg_gradient = "linear-gradient(90deg, #004d00 0%, #00d4ff 50%, #8B0000 100%)"
            elif ai_p <= AI_THRESHOLD:
                bg_gradient = "linear-gradient(90deg, #004d00 0%, #ffcc00 50%, #8B0000 100%)"
            else:
                bg_gradient = "linear-gradient(90deg, #004d00 0%, #ff0055 50%, #8B0000 100%)"

            with st.expander(
                f" {test.name} — AI: {ai_p:.0f}% | Real: {real_p:.0f}%",
                icon=f"{'🟢' if ai_p < UNCERTAIN_LOW else '🟡' if ai_p <= AI_THRESHOLD else '🔴'}",
            ):
                st.markdown(f"#### {test.name}  {chip_html}", unsafe_allow_html=True)

                # Two-column layout: explanation | details
                detail_cols = st.columns([3, 2])

                with detail_cols[0]:
                    # Inline progress bar
                    st.markdown(
                        f"""
                        <div style="background: {bg_gradient};
                                    height: 20px; border-radius: 6px;
                                    position: relative; margin: 12px 0 8px 0;">
                            <div style="position: absolute; top: -5px; left: {ai_p:.1f}%;
                                        width: 3px; height: 30px; background: #fff;
                                        box-shadow: 0 0 8px #fff;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between;
                                    font-size: 0.85em; color: #8a94a6; margin-bottom: 12px;">
                            <span>0% <span style='color:#28a745'>REAL</span></span>
                            <span><span style='color:#ffc107'>50%</span></span>
                            <span><span style='color:#dc3545'>100% AI</span></span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(f"**Verdict:** {_badge_html(ai_p)}", unsafe_allow_html=True)
                    st.markdown(f"**Confidence:** {confidence:.0%}")
                    st.markdown(
                        f"**AI Contribution:** {ai_p:.1f}%  |  **Real Contribution:** {real_p:.1f}%"
                    )
                    st.markdown(f"**Explanation:** {_truncate(test.explanation, 500)}")

                with detail_cols[1]:
                    if test.details:
                        st.markdown("<b>🔬 Technical Details</b>", unsafe_allow_html=True)
                        st.markdown(_format_details(test.details), unsafe_allow_html=True)

        # ── Download buttons ─────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='color:#ffffff; margin-bottom:12px;'>📥 Download Reports</h3>",
            unsafe_allow_html=True,
        )

        col_dl1, col_dl2 = st.columns(2, gap="medium")

        with col_dl1:
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
                key="dl_html",
            )

        with col_dl2:
            json_content = json.dumps(report.to_dict(), indent=2, default=str)
            st.download_button(
                label="📋 Download JSON Report",
                data=json_content,
                file_name="ai_analysis_report.json",
                mime="application/json",
                use_container_width=True,
                key="dl_json",
            )

        # ── JSON preview (collapsible) ────────────────────────────────
        with st.expander("📄 JSON Output Preview", icon="💾"):
            st.json(json.dumps(report.to_dict(), indent=2, default=str), expanded=False)

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        st.exception(e)

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="footer">
        AI Image Analyzer v3.0 · Built for AI safety research · Educational use only
    </div>
    """,
    unsafe_allow_html=True,
)

#!/usr/bin/env python3
"""
AI Image Analyzer — REST API (FastAPI)
======================================
A REST API wrapper around the AI Image Analyzer forensic engine.

Endpoints
---------
  POST /analyze    Upload an image → get full forensic analysis as JSON
  GET  /          API information / usage instructions
  GET  /health     Health-check endpoint

Prerequisites
-------------
    pip install fastapi "uvicorn[standard]" python-multipart
    pip install -r requirements.txt     # core forensic deps (Pillow, numpy,
                                        # opencv-python-headless, scipy)

Run
---
    uvicorn api:app --reload
    # OR, without hot-reload (production):
    uvicorn api:app --host 0.0.0.0 --port 8000

Then open http://localhost:8000/docs for the interactive Swagger UI.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

# Ensure the project directory is on sys.path
_PROJECT_DIR = Path(__file__).resolve().parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from ai_image_analyzer import analyze_image  # noqa: E402

# ── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Image Analyzer API",
    description=(
        "Forensic analysis of images for AI-generation fingerprints. "
        "Upload an image to receive a full report with per-test scores "
        "and an overall AI-probability verdict."
    ),
    version="2.1.0",
    contact={
        "name": "AI Image Analyzer",
        "url": "https://github.com/example/ai-image-analyzer",
    },
)


# ── Pydantic schemas ───────────────────────────────────────────────────────

class TestScore(BaseModel):
    """A single forensic test score within the analysis response."""

    name: str
    ai_probability: float
    real_probability: float
    confidence: float
    verdict: str
    explanation: str
    details: dict[str, Any] = {}
    # Re-export the raw score under a legacy alias for convenience
    score: float | None = None


class AnalysisResponse(BaseModel):
    """Top-level response returned by POST /analyze."""

    image_path: str
    image_size: list[int]
    file_size: int
    timestamp: str
    verdict: str
    ai_probability: float
    real_probability: float
    confidence: float
    summary: str
    tests: list[TestScore]


# ── Root / Health ──────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
async def root() -> dict[str, Any]:
    """API information and usage instructions."""
    return {
        "name": "AI Image Analyzer API",
        "version": "2.1.0",
        "description": (
            "REST API for detecting AI-generated images using six forensic "
            "techniques: metadata forensics, C2PA verification, noise analysis, "
            "frequency-domain analysis, statistical tests, and visual artifact "
            "detection."
        ),
        "endpoints": {
            "POST /analyze": "Upload an image file (multipart/form-data) for analysis",
            "GET  /docs": "Interactive Swagger UI documentation",
            "GET  /redoc": "Alternative documentation interface",
            "GET  /health": "Health-check endpoint",
        },
        "usage": {
            "curl": "curl -X POST 'http://localhost:8000/analyze' "
                    "-F 'file=@/path/to/image.jpg' | python -m json.tool",
        },
        "verdict_thresholds": {
            "< 20%": "Real Camera Photo",
            "20-55%": "Uncertain / Mixed Signals",
            "> 55%": "AI-Generated",
        },
    }


@app.get("/health", tags=["Info"])
async def health_check() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "healthy", "service": "AI Image Analyzer API"}


# ── Analyze endpoint ───────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    """
    Upload an image and run the full forensic analysis.

    **Request:** multipart/form-data with a single field named `file`
    (the image to analyse).

    **Response (JSON):**
    - `image_path` – original filename (sanitised)
    - `image_size` – [width, height]
    - `file_size` – size in bytes
    - `timestamp` – analysis time (ISO-like string)
    - `verdict` – "Real Camera Photo" | "Uncertain / Mixed Signals" | "AI-Generated"
    - `ai_probability` – overall AI score (0–100)
    - `real_probability` – 100 − ai_probability
    - `confidence` – overall confidence (0–1)
    - `summary` – one-line human-readable summary
    - `tests` – array of per-test results with individual scores, explanations,
      and detailed metadata
    """
    # ── Validate the file was provided ────────────────────────────────────
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # ── Validate the file type ─────────────────────────────────────────────
    content_type = file.content_type or ""
    filename = file.filename
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower().lstrip(".")

    # Accept common image MIME types
    allowed_mimes = {
        "image/jpeg", "image/jpg", "image/png", "image/bmp",
        "image/webp", "image/gif", "image/tiff",
    }
    allowed_exts = {"jpg", "jpeg", "png", "bmp", "webp", "gif", "tif", "tiff"}

    if content_type not in allowed_mimes and ext_lower not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{filename}'. "
                f"Allowed: {', '.join(sorted(allowed_exts))}"
            ),
        )

    # ── Save the uploaded file to a temporary location ────────────────────
    suffix = ext if ext else ".tmp"
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            # Read the uploaded file in chunks to handle large images
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp_path = tmp.name

        # ── Run the forensic analysis ────────────────────────────────────────
        report = analyze_image(tmp_path)

        # ── Convert to dict and post-process for the API response ──────────
        result: dict[str, Any] = report.to_dict()

        # Add a 'score' alias (= ai_probability) inside each test for
        # clients that expect the legacy field name.
        for t in result.get("tests", []):
            t["score"] = t.get("ai_probability", t.get("score", 0.0))

        # Ensure image_size is a plain list for JSON serialisation
        if isinstance(result.get("image_size"), tuple):
            result["image_size"] = list(result["image_size"])

        # Use the original filename as image_path for clarity
        result["image_path"] = filename

        return AnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(exc)}",
        ) from exc
    finally:
        # Clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        # Close the uploaded file handle
        await file.close()


# ── Allow `python api.py` as a convenience ─────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("Starting AI Image Analyzer API...")
    print("Interactive docs:  http://localhost:8000/docs")
    print("Alternative docs:  http://localhost:8000/redoc")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

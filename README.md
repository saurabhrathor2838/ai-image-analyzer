# AI Image Analyzer

A forensic tool for detecting AI-generated images using multiple complementary
techniques — metadata forensics, C2PA provenance verification, noise
pattern analysis, frequency-domain analysis, statistical tests, and
visual-artifact detection.

> **Version 3.0** — Now detects AI-generated notebook pages, ChatGPT/Gemini
> text diagrams, and synthetic documents with coloured backgrounds.
> Features hyper-smooth background detection, dynamic weighting when EXIF
> is missing, non-linear sigmoid score scaling for stronger verdicts,
> and a Text & Grid Anomaly Detector that works with any background colour.

> **Purpose:** Research, media-literacy, and platform-safety workflows.
> This tool helps you understand *why* an image looks synthetic — it is **not**
> a production-grade classifier, and no automated detector is ever 100 %
> reliable.

---

## 🔍 How It Works

The analyzer runs **six independent forensic tests** on each image and
combines their results into an overall score and verdict.

| # | Test | Weight | What It Looks For |
|---|------|--------|--------------------|
| 1 | **Metadata Forensics** | 0.15 | Missing camera make/model, absent timestamps, AI tool signatures in EXIF fields, resolution divisible by 64 |
| 2 | **C2PA Metadata Verification** | 0.15 | C2PA ContentCredentials manifests, AI tool signatures in XMP/IPTC/raw headers, EXIF completeness |
| 3 | **Noise Pattern Analysis** | 0.25 | Uniform noise across regions, absence of CFA (Bayer) interpolation patterns, chroma noise patterns |
| 4 | **Frequency Domain Analysis** | 0.20 | Flat spectral slope (~1/f² fall-off), excessive high-frequency energy, periodic grid patterns |
| 5 | **Statistical Analysis** | 0.10 | Histogram entropy, inter-channel correlation, pixel distribution kurtosis, double-JPEG traces |
| 6 | **Visual Artifact Detection** | 0.15 | Over-smoothing, unnatural symmetry, abnormal edge density, low texture variance, **Text & Grid Anomalies** (synthetic text/diagrams, hyper-smooth backgrounds of any color) |

### Scoring (v3.0 — Sigmoid-Calibrated)

Each test produces an **AI probability percentage** (0–100 %):
0 % = certainly a real photograph, 50 % = uncertain, 100 % = certainly AI-generated.
Tests are weighted by confidence and combined into an overall score.

When **EXIF/C2PA metadata is missing**, the dynamic weighting system
automatically boosts the weight of physical-signal tests (Noise, Frequency,
Statistical, Visual) to compensate — metadata alone should never determine
the verdict.

After aggregation, a **sigmoid non-linearity** sharpens the final score so
that strong AI signals approach 85–100 % and clear camera photos drop below
10–15 %, rather than clustering in the 30–50 % uncertain band.

| Overall AI Probability | Verdict |
|------------------------|---------|
| < 20 % | **Real Camera Photo** |
| 20 – 55 % | **Uncertain / Mixed Signals** |
| > 55 % | **AI-Generated** |

### Dynamic Test Weights

When EXIF/C2PA metadata is present, default weights are used. When metadata
is **absent**, weights are rebalanced to favour physical-signal evidence:

| Test | Default Weight | No-EXIF Weight |
|------|---------------|----------------|
| Metadata Forensics | 0.15 | 0.30 |
| C2PA Metadata Verification | 0.15 | 0.30 |
| Noise Pattern Analysis | 0.25 | 0.25 × 1.25 |
| Frequency Domain Analysis | 0.20 | 0.20 × 1.25 |
| Statistical Analysis | 0.10 | 0.10 × 1.25 |
| Visual Artifact Detection | 0.15 | 0.15 × 1.35 |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Required packages: Pillow, NumPy, OpenCV, SciPy
- Optional: `exifread`, `pyc2pa` — for enhanced metadata parsing (the tool
  falls back to raw byte analysis when these are not installed)

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyse an image (verbose console output)
python ai_image_analyzer.py path/to/image.jpg

# JSON output for programmatic use
python ai_image_analyzer.py image.jpg --json

# Generate an interactive HTML report
python ai_image_analyzer.py image.jpg --html report.html

# Quiet mode (only prints the verdict)
python ai_image_analyzer.py image.jpg --quiet

# Plain-text / no-colour output (for accessibility or simple terminals)
python ai_image_analyzer.py image.jpg --no-color

# Custom confidence threshold (default 0.5)
python ai_image_analyzer.py image.jpg --threshold 0.7
```

### Batch Mode

Scan all images in a folder at once:

```bash
# Batch scan a directory (summary table only)
python ai_image_analyzer.py my_photos/ --batch --summary

# Recursive batch scan with full HTML report
python ai_image_analyzer.py my_photos/ --batch --recursive --html batch_report.html

# Batch scan with JSON output for automation
python ai_image_analyzer.py my_photos/ --batch --summary --json
```

#### Batch Summary Table

```
===========================================================================================================
  File                                               AI %      Real %  Verdict
===========================================================================================================
  Screenshot_2026-...99c04817c0de5652397...          43%         57%  Uncertain / Mixed Signals
  95c8f7ff1ec60...5d569d22b63e184095b...             28%         72%  Real Camera Photo
-----------------------------------------------------------------------------------------------------------

  Total images analysed: 2
  Uncertain / Mixed Signals: 1 (50%)
  Real Camera Photo: 1 (50%)
```

### Full Options

```
python ai_image_analyzer.py --help

  Analyze an image for AI-generation fingerprints.

  positional arguments:
    image_path       Path to an image file or (with --batch) a directory

  options:
    --batch          Batch mode: scan all images in the given directory
    --recursive      Search subdirectories in batch mode (implies --batch)
    --summary        In batch mode, print only the summary table
    --json           Output results as JSON
    --html FILE      Write an interactive HTML report to FILE
    -v, --verbose    Print detailed findings for every test
    -q, --quiet      Print only the final verdict
    --no-color       Disable coloured/emoji output (plain-text mode)
    --threshold N    AI-probability threshold for verdict (0.0-1.0, default 0.55)
```

---

## 🌐 Web UI (Streamlit)

A graphical web interface with drag-and-drop upload, live score
visualization, and one-click report downloads.

### Prerequisites

```bash
pip install streamlit
```

### Run

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

### Features

- **Drag-and-drop** image upload (JPEG, PNG, BMP, WebP, GIF, TIFF)
- Live **AI probability bar** with per-test breakdown
- Expandable panels for each forensic test showing:
  - Individual AI/real score with visual bar
  - Confidence level and verdict
  - Detailed explanation and metadata
- **Download buttons** for HTML and JSON reports
- Mobile-responsive layout

---

## 🌐 REST API (FastAPI)

A REST API wrapper for programmatic access to the forensic engine.

### Prerequisites

```bash
pip install fastapi "uvicorn[standard]" python-multipart
```

### Run

```bash
# Development mode (hot-reload)
python api.py
# OR
uvicorn api:app --reload

# Production
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Upload an image, receive full analysis as JSON |
| `GET` | `/docs` | Interactive Swagger UI documentation |
| `GET` | `/redoc` | Alternative API documentation |
| `GET` | `/health` | Health-check endpoint |
| `GET` | `/` | API information |

### Usage (curl)

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@/path/to/image.jpg" | python -m json.tool
```

### Response Format (JSON)

```json
{
  "image_path": "photo.jpg",
  "image_size": [1000, 750],
  "file_size": 332700,
  "timestamp": "2026-08-19 01:00:00",
  "verdict": "Real Camera Photo",
  "ai_probability": 10.15,
  "real_probability": 89.85,
  "confidence": 0.5833,
  "summary": "AI Probability: 10% ... Verdict: Real Camera Photo",
  "tests": [
    {
      "name": "Metadata Forensics",
      "ai_probability": 13.0,
      "real_probability": 87.0,
      "confidence": 0.7,
      "verdict": "Real Camera",
      "explanation": "Camera make/model present in EXIF ...",
      "details": { ... },
      "score": 13.0
    },
    ...
  ]
}
```

---

## 📊 Example Output

### Console (verbose)

```
======================================================================
  AI IMAGE ANALYSIS REPORT
======================================================================
  File:        ai_like_test.png
  Resolution:  1024 × 1024
  File size:   1.9 MB
  Timestamp:   2026-08-19 00:13:52
======================================================================

  AI Probability:   89.3%
  Real Confidence:  10.7%
  (Overall Conf:   54%)
  [0% REAL                      100% AI]
  [###########################-------------]

  VERDICT: AI-Generated
======================================================================

  🔴 Metadata Forensics: AI=68% | Real=32% (conf: 30%, verdict: AI-Generated)
       -> No camera make/model in EXIF; No capture timestamp; Resolution divisible by 64

  🔴 Noise Pattern Analysis: AI=80% | Real=20% (conf: 70%, verdict: AI-Generated)
       -> Noise is unusually uniform (CV=0.028); No CFA patterns detected

  🟡 Frequency Domain Analysis: AI=55% | Real=45% (conf: 50%, verdict: Uncertain)
       -> Spectral slope (-0.10) is moderately natural; High HF energy (70.99%)
```

### JSON

```json
{
  "image_path": "ai_like_test.png",
  "verdict": "AI-Generated",
  "ai_probability": 89.34,
  "real_probability": 10.66,
  "confidence": 0.59,
  "tests": [
    {
      "name": "Metadata Forensics",
      "ai_probability": 78.0,
      "real_probability": 22.0,
      "confidence": 0.5,
      "verdict": "AI-Generated",
      "explanation": "No camera make/model in EXIF...",
      "details": { ... }
    },
    ...
  ]
}
```

### HTML Report

Open `report.html` in any browser for an interactive, styled analysis
report with per-test details and confidence breakdowns.

---

## 🚨 v3.0: Text & Grid Anomaly Detector

The v3.0 update adds a dedicated **Text & Grid Anomaly Detector** inside the
Visual Artifact test. This detects AI-generated notebook pages, ChatGPT/Gemini
text diagrams, and synthetic documents that were previously misclassified as
real photos. The detector works with **any background colour** (white, coloured,
or gradient) and looks for:

- **Hyper-smooth backgrounds** — large regions with near-zero local variance
  (no paper texture, no sensor noise), detected via 9×9 local variance
- **Dense edge rows** — every horizontal scanline contains edges, indicating
  text/diagram rendering rather than natural photographic content
- **Periodic grid patterns** — repetitive structures via FFT frequency peaks
- **Uniform ink strokes** — dark regions with unnaturally low colour variance
  (synthetic pen strokes vs. real handwriting)

### CFA False-Positive Suppression

The Noise test's CFA (Bayer sensor) detector now includes a smoothness gate:
if cross-channel HF correlation is extremely high (> 0.50) **and** more than
10% of the image is in smooth regions, the CFA score is suppressed. This
prevents AI images with coloured/gradient backgrounds from triggering false
CFA detections.

---

## 🧪 Testing

Generate synthetic test images and run the analyzer:

```bash
# Generate test images (AI-like and photo-like)
python generate_test_images.py

# Analyse the AI-like test image (should flag as AI-GENERATED)
python ai_image_analyzer.py test_images/ai_like_test.png --verbose

# Analyse the photo-like test image (should show Real Camera Photo, low AI %)
python ai_image_analyzer.py test_images/photo_like_test.jpg --verbose
```

---

## 🛡️ Limitations & Caveats

This tool is **educational and research-focused**. It has important limitations:

1. **No single test is definitive.** Each test produces a probabilistic signal.
   The tool combines them, but false positives and false negatives are common.

2. **AI post-processing evasion.** Simple techniques (adding noise, JPEG
   re-save, colour grading) can reduce detectability. New AI models are
   increasingly harder to distinguish from photographs.

3. **C2PA / Content Credentials** are the only cryptographically secure
   provenance source. If an image has a C2PA signature, verify it with Adobe's
   Content Authenticity browser extension. If it doesn't, provenance is
   uncertain.

4. **Screenshots and rendered graphics** without EXIF data may score in the
   Uncertain range (30–65 % AI probability) rather than being confidently
   classified. The tool now weights metadata less heavily, so real camera
   photos with natural noise patterns are correctly identified even when
   EXIF is absent.

5. **The arms race continues.** New generative models are trained regularly.
   Detection research must evolve alongside generation capabilities.

### When to trust the verdicts

| Verdict | Trust Level |
|---------|-------------|
| AI-Generated | High confidence (multiple forensic signals agree) |
| Real Camera Photo | High confidence (natural patterns in all tests) |
| Uncertain / Mixed Signals | Low confidence (mixed signals — manual review recommended) |

---

## 📚 Techniques Explained

### Metadata Forensics

Real cameras embed EXIF metadata: camera make/model, lens info, capture
datetime, ISO, aperture, etc. AI-generation tools often:
- Leave this data empty or stripped
- Set "Software" to the tool name (e.g., "Stable Diffusion", "Midjourney")
- Produce resolutions divisible by common model patch sizes (64, 128, 256)

### C2PA Metadata Verification

This test performs deep metadata scanning using raw byte parsing (with
exifread / pyc2pa as optional enhancements if installed). It looks for:

- **C2PA ContentCredentials manifests** — cryptographically signed provenance
  data embedded by tools complying with the C2PA standard
- **AI tool signatures** in EXIF, XMP, IPTC, and raw file headers — searches
  for keywords like "DALL-E", "Midjourney", "Stable Diffusion", "Adobe Firefly",
  "Imagen", "Gen-2", etc.
- **Adobe Photoshop IRB** data (APP13 segments in JPEG) — may contain
  provenance or editing history
- **EXIF completeness** — rich camera EXIF (make/model, ISO, focal length,
  exposure) is a strong real-photo signal; missing EXIF is handled by the
  Metadata Forensics test

When a direct AI signature is found, this test returns a high AI probability
with high confidence. When no signatures are found, it stays neutral and
lets the other tests determine the verdict.

### Noise Pattern Analysis

Digital camera sensors introduce characteristic noise:
- **Photon shot noise** (Poisson distribution, varies with brightness)
- **Read noise** (varies across the sensor)
- **Color Filter Array (CFA)** interpolation creates subtle cross-colour
  patterns that AI generators don't reproduce

The tool divides the image into blocks and measures local noise variance.
Real photos show spatial variation; AI images often have uniform noise.

### Frequency Domain Analysis

Using the 2-D Fast Fourier Transform (FFT):
- Real scenes follow a ~1/f² power spectrum (smooth fall-off at high
  frequencies due to lens optics)
- AI images often have flatter spectra or excess high-frequency energy
- Periodic grid patterns can indicate patch-based training artefacts

### Statistical Analysis

- **Histogram entropy** measures information content; AI images can be
  over-diverse or posterised
- **Channel correlation**; AI images sometimes have unnaturally high RGB
  synchronisation
- **Kurtosis** of pixel intensities; heavy-tailed distributions are common
  in AI noise
- **Double JPEG detection**; can reveal re-compression after generation

### Visual Artifact Detection

- **Over-smoothing:** AI images sometimes lack fine micro-texture
- **Symmetry:** AI generators can produce near-perfect symmetry
- **Edge density:** Abnormally low or high edge counts
- **Texture variance:** Statistical measure of local detail richness

---

## 🤝 Contributing

This is a research/educational project. Contributions welcome:
- Additional forensic tests (e.g., PRNU analysis, JPEG ghost detection)
- Integration with C2PA verification
- Web UI / API wrapper
- Documentation improvements

---

## ⚖️ License

MIT — use for research, education, and legitimate detection workflows.
Not intended for automated moderation or high-stakes decisions without
human review.

---

## 👤 Author

Built for AI safety research and media-literacy purposes.

#!/usr/bin/env python3
"""Insert new test functions into ai_image_analyzer.py."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NEW_CODE = '''
# ════════════════════════════════════════════════════════════════════════════
#  Test 2.5 — Deep Learning Detector (Swin Transformer)
# ════════════════════════════════════════════════════════════════════════════

_DL_MODEL_CACHE: dict[str, Any] = {}


def _load_dl_model() -> Any:
    """Lazily download and load the Swin Transformer AI detector model.

    Uses ``umm-maybe/AI-image-detector`` from HuggingFace Hub — a
    fine-tuned Swin Transformer that classifies images as
    *artificial* (AI-generated) or *human* (real photograph).

    The model is cached in-memory after the first load.
    """
    if not _TORCH_AVAILABLE:
        return None

    cache_key = _MODEL_NAME
    if cache_key in _DL_MODEL_CACHE:
        return _DL_MODEL_CACHE[cache_key]

    try:
        import torch
        from transformers import AutoModelForImageClassification, AutoImageProcessor

        processor = AutoImageProcessor.from_pretrained(_MODEL_NAME)
        model = AutoModelForImageClassification.from_pretrained(_MODEL_NAME)
        model.eval()
        if torch.cuda.is_available():
            model = model.to("cuda")

        _DL_MODEL_CACHE[cache_key] = (model, processor)
        return _DL_MODEL_CACHE[cache_key]
    except Exception as exc:
        warnings.warn(f"Deep learning model load failed: {exc}")
        _DL_MODEL_CACHE[cache_key] = None
        return None


def test_deep_learning(cv_img: np.ndarray) -> TestResult:
    """Run the pre-trained Swin Transformer AI detector on the image.

    Uses ``umm-maybe/AI-image-detector`` which classifies images as
    'artificial' (AI-generated) or 'human' (real photograph).

    The model's 'artificial' probability is mapped to an AI
    probability score.
    """
    result = _load_dl_model()
    if result is None:
        return TestResult(
            name="Deep Learning Detector (Swin Transformer)",
            score=50.0,
            confidence=0.0,
            explanation="Swin Transformer model unavailable (transformers/torch not installed).",
            details={"model": _MODEL_NAME, "error": "model_not_available"},
        )

    model, processor = result

    try:
        import torch

        # Convert OpenCV BGR to RGB PIL image
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # Handle small images by resizing up
        min_size = 32
        if pil_img.size[0] < min_size or pil_img.size[1] < min_size:
            pil_img = pil_img.resize((224, 224), Image.LANCZOS)

        # Preprocess
        inputs = processor(images=pil_img, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        # Get probabilities via softmax
        probs = torch.softmax(logits, dim=-1)
        probs = probs.cpu().numpy()[0]

        # Model labels: 0 = artificial, 1 = human
        artificial_prob = float(probs[0])
        human_prob = float(probs[1])
        ai_score = artificial_prob * 100.0

        confidence = max(artificial_prob, human_prob)

        # Build explanation
        label_map = model.config.id2label
        top_label = label_map.get("0", "artificial") if artificial_prob > human_prob else label_map.get("1", "human")

        findings = []
        findings.append(
            f"Swin Transformer classifier [{_MODEL_NAME}]: "
            f"artificial={artificial_prob:.1%}, human={human_prob:.1%}"
        )
        if artificial_prob > 0.7:
            findings.append("Strong AI-generation signal from deep features.")
        elif human_prob > 0.7:
            findings.append("Strong real-camera signal from deep features.")
        findings.append(f"Top prediction: '{top_label}' (conf: {confidence:.1%})")

        # Extract top-2 logits for details
        logit_vals = logits.cpu().numpy()[0].tolist()

        return TestResult(
            name="Deep Learning Detector (Swin Transformer)",
            score=round(ai_score, 1),
            confidence=round(confidence, 4),
            explanation="; ".join(findings),
            details={
                "model": _MODEL_NAME,
                "architecture": "SwinTransformer",
                "artificial_prob": round(artificial_prob, 6),
                "human_prob": round(human_prob, 6),
                "logits": logit_vals,
                "top_label": top_label,
            },
        )
    except Exception as exc:
        return TestResult(
            name="Deep Learning Detector (Swin Transformer)",
            score=50.0,
            confidence=0.0,
            explanation=f"Deep learning inference failed: {exc}",
            details={"model": _MODEL_NAME, "error": str(exc)},
        )


# ════════════════════════════════════════════════════════════════════════════
#  Test 3.5 — Error Level Analysis (ELA)
# ════════════════════════════════════════════════════════════════════════════

def _run_ela(cv_img: np.ndarray, quality: int = 95) -> tuple[np.ndarray, float]:
    """Run Error Level Analysis (ELA) on an image.

    ELA works by re-encoding the image at a lower JPEG quality and
    comparing the difference.  Areas that were modified or
    synthesised (common in AI images) show different error levels
    than naturally captured regions.

    Returns ``(ela_image, mean_error)`` where *ela_image* is a
    scaled 8-bit array (0–255) and *mean_error* is the average
    absolute difference.
    """
    # Convert to RGB and to PIL Image
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    # Convert to RGB mode (handle RGBA, P, etc.)
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    orig_np = np.array(pil_img, dtype=np.float64)

    # Re-encode at lower quality
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    re_encoded = Image.open(buf)
    re_np = np.array(re_encoded, dtype=np.float64)

    # Ensure same size (JPEG may round dimensions)
    if re_np.shape != orig_np.shape:
        re_np = np.array(re_encoded.resize(pil_img.size), dtype=np.float64)

    # Compute difference
    diff = np.abs(orig_np - re_np)
    max_diff = diff.max() if diff.max() > 0 else 1.0
    ela_image = (diff / max_diff) * 255.0
    ela_image = np.clip(ela_image, 0, 255).astype(np.uint8)
    mean_error = float(diff.mean())

    return ela_image, mean_error


def test_error_level_analysis(cv_img: np.ndarray) -> TestResult:
    """Run Error Level Analysis (ELA) as a forensic test.

    ELA re-encodes the image at a lower JPEG quality and measures the
    difference.  In real photographs, natural compression artefacts
    vary smoothly.  In AI-generated images, the error levels are
    often *too uniform* (because the generator produces the image
    in one pass) or show *abrupt boundaries* (where elements were
    pasted/composited).

    The score is derived from:
      • Mean absolute error (higher = more recompression artefacts)
      • Std-dev of the error (lower = more uniform = suspicious)
      • Presence of block-level boundaries at regular intervals
    """
    findings: list[str] = []
    details: dict[str, Any] = {}
    ai_prob = 50.0
    confidence = 0.5

    try:
        ela_img, mean_error = _run_ela(cv_img, quality=95)

        h, w = ela_img.shape[:2]
        ela_gray = cv2.cvtColor(ela_img, cv2.COLOR_RGB2GRAY) if ela_img.ndim == 3 else ela_img
        ela_std = float(np.std(ela_gray.astype(np.float64)))
        ela_mean = float(np.mean(ela_gray.astype(np.float64)))
        details["ela_mean_error"] = round(ela_mean, 4)
        details["ela_std"] = round(ela_std, 4)
        details["max_error"] = round(float(ela_img.max()), 4)

        findings.append(f"ELA mean error: {ela_mean:.2f} (quality=95); std={ela_std:.2f}")

        # Low std in error levels = uniform compression = synthetic
        if ela_std < 8.0 and ela_mean > 2.0:
            findings.append("UNIFORM error distribution (low std) — characteristic of AI-generated images.")
            ai_prob = max(ai_prob, 65.0)
            confidence = max(confidence, 0.65)
        elif ela_std < 4.0:
            findings.append("Very uniform ELA — minimal variation across regions (AI-like).")
            ai_prob = max(ai_prob, 75.0)
            confidence = max(confidence, 0.75)

        # High mean error with high std = real JPEG with natural recompression
        if ela_std > 15.0 and ela_mean > 5.0:
            findings.append("Natural ELA variation — consistent with real camera JPEG.")
            ai_prob = min(ai_prob, 30.0)
            confidence = max(confidence, 0.7)

        # Check for block-level periodic boundaries (8×8 JPEG blocks)
        # In AI images, ELA often shows grid-like artifacts
        gray_ela = ela_gray.astype(np.float64)
        # Downsample to 8x8 blocks and check variance
        block_size = 8
        bh, bw = h // block_size, w // block_size
        if bh > 4 and bw > 4:
            trimmed = gray_ela[:bh*block_size, :bw*block_size]
            blocks = trimmed.reshape(bh, block_size, bw, block_size).mean(axis=(1, 3))
            block_std = float(np.std(blocks))
            block_mean = float(np.mean(blocks))
            block_cv = block_std / (block_mean + 1e-8)
            details["ela_block_std"] = round(block_std, 4)
            details["ela_block_cv"] = round(block_cv, 4)
            findings.append(f"Block-level (8×8) ELA std={block_std:.2f}, CV={block_cv:.3f}")

            if block_cv < 0.05 and block_mean > 3.0:
                findings.append("Uniform block errors — synthetic compression pattern (AI-like).")
                ai_prob = max(ai_prob, 70.0)
                confidence = max(confidence, 0.70)

        # Very low overall error = image was likely not JPEG-compressed naturally
        if ela_mean < 1.0:
            findings.append("Minimal ELA error — image may have been saved at high quality (common for PNGs from AI tools).")
            ai_prob = max(ai_prob, 55.0)
            confidence = max(confidence, 0.55)

        details["ela_image_shape"] = [int(h), int(w)]
        details["ela_image_size"] = int(ela_img.nbytes)

    except Exception as exc:
        findings.append(f"ELA analysis error: {exc}")
        ai_prob = 50.0
        confidence = 0.0
        details["error"] = str(exc)

    details["test_type"] = "ela"

    # Determine verdict for individual test
    if ai_prob < UNCERTAIN_LOW:
        test_verdict = "Real Camera Photo"
    elif ai_prob <= AI_THRESHOLD:
        test_verdict = "Uncertain / Mixed Signals"
    else:
        test_verdict = "AI-Generated"

    return TestResult(
        name="Error Level Analysis (ELA)",
        score=round(ai_prob, 1),
        confidence=round(confidence, 4),
        explanation="; ".join(findings),
        details=details,
    )


# ════════════════════════════════════════════════════════════════════════════
#  Test 3 — Frequency Domain Analysis
# ════════════════════════════════════════════════════════════════════════════
'''

# Find the insertion point — before the Frequency Domain Analysis section
with open('ai_image_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '# ════════════════════════════════════════════════════════════════════════════\n#  Test 3 — Frequency Domain Analysis'
insert_idx = content.index(marker)

content = content[:insert_idx] + NEW_CODE + content[insert_idx:]

with open('ai_image_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Inserted {len(NEW_CODE)} chars of new code before Frequency Domain Analysis")

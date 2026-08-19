#!/usr/bin/env python3
"""Test the new DL and ELA functions on test images."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from ai_image_analyzer import (
    load_image, test_deep_learning, test_error_level_analysis,
    test_frequency, aggregate_results, _determine_has_exif,
)
from ai_image_analyzer import TestResult

tests = [
    ("photo_like_test.jpg", "test_images/photo_like_test.jpg"),
    ("ai_like_test.png", "test_images/ai_like_test.png"),
]

for name, path in tests:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    cv_img, pil_img, exif_dict = load_image(path)
    
    dl_result = test_deep_learning(cv_img)
    print(f"  Deep Learning:  score={dl_result.score:.1f}  conf={dl_result.confidence:.2f}")
    print(f"    {dl_result.explanation[:150]}")
    
    ela_result = test_error_level_analysis(cv_img)
    print(f"  ELA:            score={ela_result.score:.1f}  conf={ela_result.confidence:.2f}")
    print(f"    {ela_result.explanation[:150]}")
    
    freq_result = test_frequency(cv_img)
    print(f"  Frequency:      score={freq_result.score:.1f}  conf={freq_result.confidence:.2f}")

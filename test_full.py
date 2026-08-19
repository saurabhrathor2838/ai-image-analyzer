#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from ai_image_analyzer import analyze_image

tests = [
    ('photo_like', 'test_images/photo_like_test.jpg'),
    ('ai_like', 'test_images/ai_like_test.png'),
    ('Gemini', r'D:\Chrome Downloads\iMAGE\Gemini_Generated_Image_zfxl1lzfxl1lzfxl.png'),
]

for name, path in tests:
    r = analyze_image(path, threshold=0.55)
    print(f'{name}: {r.verdict} (AI={r.overall_score:.1f}%)')
    for t in r.tests:
        tname = t.name[:40]
        print(f'  {tname}: score={t.score:.1f} conf={t.confidence:.2f}')
    print()

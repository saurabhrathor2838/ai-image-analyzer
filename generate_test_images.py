#!/usr/bin/env python3
"""
Generate synthetic test images to verify the AI image analyzer.

Creates two kinds of images:
  1. 'AI-like'  — smooth, uniform noise, high symmetry, clean texture
  2. 'Photo-like' — natural noise gradients, asymmetry, real texture

These are synthetic but serve to exercise every code path in the analyzer.
"""

import numpy as np
from PIL import Image, ImageDraw
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_ai_like_image(width=1024, height=1024):
    """
    Create an image that exhibits characteristics commonly associated
    with AI-generated images:
      • Uniform noise (no sensor noise variation)
      • High left-right symmetry
      • Over-smoothed textures (low high-frequency content)
      • Clean, 'perfect' edges
      • Divisible-by-64 resolution
    """
    img = np.zeros((height, width, 3), dtype=np.float64)

    # --- Background gradient (smooth, typical of AI) ---
    for c in range(3):
        gradient = np.linspace(0.3, 0.9, width)
        img[:, :, c] = np.tile(gradient, (height, 1))

    # --- Add a central 'face-like' structure (symmetrical) ---
    cx, cy = width // 2, height // 2

    # Face oval
    yy, xx = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    face_mask = dist_from_center < 200

    # Fill face with uniform skin tone
    img[face_mask, 0] = 0.8
    img[face_mask, 1] = 0.6
    img[face_mask, 2] = 0.5

    # Eyes (symmetrical, perfect circles)
    eye_radius = 15
    for eye_cx in [cx - 60, cx + 60]:
        eye_mask = (xx - eye_cx) ** 2 + (yy - (cy - 20)) ** 2 < eye_radius ** 2
        img[eye_mask] = [0.1, 0.1, 0.1]  # dark eyes

    # Nose (simple line)
    nose_mask = (np.abs(xx - cx) < 5) & (yy > cy - 30) & (yy < cy + 10)
    img[nose_mask] = [0.7, 0.45, 0.35]

    # Mouth (smooth curve)
    mouth_mask = (np.abs(xx - cx) < 50) & (yy > cy + 20) & (yy < cy + 25)
    img[mouth_mask] = [0.7, 0.3, 0.3]

    # Add uniform noise (same level everywhere — AI-like)
    noise = np.random.normal(0, 5, (height, width, 3))
    img = img * 255 + noise
    img = np.clip(img, 0, 255).astype(np.uint8)

    return Image.fromarray(img)


def create_photo_like_image(width=1024, height=1024):
    """
    Create an image that exhibits characteristics of a real photograph:
      • Spatially varying noise (more noise in darker/cooler areas)
      • Asymmetry (natural imperfections)
      • Rich high-frequency detail (grass, leaves)
      • Lens-like vignetting
      • Non-standard resolution
    """
    img = np.zeros((height, width, 3), dtype=np.float64)

    yy, xx = np.mgrid[:height, :width]
    cx, cy = width // 2, height // 2

    # --- Sky gradient with vignetting ---
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    vignette = 1.0 - (dist / max(cx, cy)) * 0.4

    # Blue sky with natural gradient
    sky_mask = yy < height * 0.55
    sky_gradient = 1.0 - (yy[sky_mask] / height)
    img[sky_mask, 0] = (180 * sky_gradient * vignette[sky_mask]).clip(0, 255)  # R
    img[sky_mask, 1] = (220 * sky_gradient * vignette[sky_mask]).clip(0, 255)  # G
    img[sky_mask, 2] = (255 * sky_gradient * vignette[sky_mask]).clip(0, 255)  # B

    # --- Grass field (rich texture) ---
    grass_mask = yy >= height * 0.50
    grass_y = yy[grass_mask]

    # Natural grass green with variation
    base_green = 80 + np.sin(xx[grass_mask] * 0.05) * 20 + np.cos(grass_y * 0.03) * 15
    img[grass_mask, 0] = np.clip(base_green * 0.3, 0, 255)  # R low
    img[grass_mask, 1] = np.clip(base_green, 0, 255)         # G high
    img[grass_mask, 2] = np.clip(base_green * 0.5, 0, 255)   # B medium

    # --- Tree (asymmetrical) ---
    tree_x, tree_y = cx + 150, cy + 100
    tree_mask = (xx - tree_x) ** 2 + (yy - tree_y) ** 2 < 80 ** 2
    img[tree_mask, 0] = 40   # dark green
    img[tree_mask, 1] = 120
    img[tree_mask, 2] = 40

    # Tree trunk
    trunk_mask = (np.abs(xx - tree_x) < 15) & (tree_y < yy) & (yy < tree_y + 120)
    img[trunk_mask] = [80, 50, 30]

    # --- Dirt path (asymmetrical, varies) ---
    path_center = cx - 100
    path_mask = (np.abs(xx - path_center - np.sin(yy * 0.01) * 30) < 50 + np.cos(yy * 0.02) * 20) & (yy > height * 0.55)
    img[path_mask, 0] = 140  # brownish
    img[path_mask, 1] = 90
    img[path_mask, 2] = 60

    # --- Add natural noise (varies by region and intensity) ---
    # More noise in darker areas (higher ISO sensitivity simulation)
    brightness = img.mean(axis=2) / 255.0
    noise_level = 8 + (1.0 - brightness) * 12  # darker = more noise

    noise = np.random.normal(0, 1, (height, width))  # base noise
    for c in range(3):
        img[:, :, c] += noise * noise_level[:, ]

    img = np.clip(img, 0, 255).astype(np.uint8)

    # Convert back to PIL for metadata
    pil_img = Image.fromarray(img)

    # Add realistic EXIF data (properly embedded in the saved file)
    from PIL.ExifTags import TAGS
    exif = pil_img.getexif()
    exif[0x010f] = "Canon"                    # Make
    exif[0x0110] = "Canon EOS R5"            # Model
    exif[0x0112] = 1                         # Orientation
    exif[0x0131] = "1.0.0"                   # Software
    exif[0x0132] = "2024:06:15 14:32:10"    # DateTime
    exif[0x9003] = "2024:06:15 12:15:00"   # DateTimeOriginal
    exif[0x9004] = "2024:06:15 12:15:00"   # DateTimeDigitized
    exif[0x9000] = "1.0.0"                   # Software version
    exif[0x829a] = "1/125"                   # FNumber
    exif[0x829d] = "f/5.6"                   # ExposureTime

    return pil_img, exif


def main():
    print("Generating test images...")

    # AI-like image
    ai_img = create_ai_like_image(1024, 1024)
    ai_path = os.path.join(OUTPUT_DIR, "ai_like_test.png")
    ai_img.save(ai_path)
    print(f"  Created: {ai_path}")

    # Photo-like image
    photo_img, photo_exif = create_photo_like_image(1000, 750)  # non-standard resolution
    photo_path = os.path.join(OUTPUT_DIR, "photo_like_test.jpg")
    photo_img.save(photo_path, "JPEG", quality=90, exif=photo_exif.tobytes())
    print(f"  Created: {photo_path}")

    print(f"\nTest images saved to: {OUTPUT_DIR}")
    print("\nRun the analyzer:")
    print(f"  python ai_image_analyzer.py {ai_path} --verbose")
    print(f"  python ai_image_analyzer.py {photo_path} --verbose")


if __name__ == "__main__":
    main()

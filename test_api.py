#!/usr/bin/env python3
"""Quick test script for the FastAPI /analyze endpoint."""
import json
import urllib.request

BOUNDARY = "----TestBoundary12345"
URL = "http://localhost:8000/analyze"


def build_multipart(filename, filepath, content_type):
    with open(filepath, "rb") as f:
        data = f.read()
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + data + f"\r\n--{BOUNDARY}--\r\n".encode()
    return body


def call_api(filename, filepath, content_type):
    body = build_multipart(filename, filepath, content_type)
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read().decode())


def print_result(label, result):
    print(f"\n=== {label} ===")
    print(f"Verdict:          {result['verdict']}")
    print(f"AI Probability:   {result['ai_probability']}%")
    print(f"Real Probability: {result['real_probability']}%")
    print(f"Confidence:       {result['confidence']}")
    print(f"Tests: {len(result['tests'])}")
    for t in result["tests"]:
        print(f"  {t['name']}: AI={t['ai_probability']}% Real={t['real_probability']}% Verdict={t['verdict']}")


# Test 1: Real camera photo
r1 = call_api(
    "photo_like_test.jpg",
    "test_images/photo_like_test.jpg",
    "image/jpeg",
)
print_result("photo_like_test.jpg (Real Camera Photo)", r1)

# Test 2: AI-generated image
r2 = call_api(
    "ai_like_test.png",
    "test_images/ai_like_test.png",
    "image/png",
)
print_result("ai_like_test.png (AI-Generated)", r2)

# Test 3: Health check
req = urllib.request.Request("http://localhost:8000/health")
resp = urllib.request.urlopen(req, timeout=10)
print("\n=== /health ===")
print(json.loads(resp.read().decode()))

# Test 4: Root info
req = urllib.request.Request("http://localhost:8000/")
resp = urllib.request.urlopen(req, timeout=10)
print("\n=== / ===")
print(json.loads(resp.read().decode()))

print("\nAll API tests passed!")

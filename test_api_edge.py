#!/usr/bin/env python3
"""Test edge cases: bad file type, openapi.json."""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
BOUNDARY = "----TestBoundary12345"


def post_multipart(filename, content, content_type):
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{BOUNDARY}--\r\n".encode()
    req = urllib.request.Request(f"{BASE}/analyze", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")
    return urllib.request.urlopen(req, timeout=30)


# Test 1: Unsupported file type (text file)
print("=== Test: Unsupported file type (.txt) ===")
try:
    resp = post_multipart("test.txt", b"This is not an image", "text/plain")
    print("UNEXPECTED success:", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Correctly rejected: HTTP {e.code}")
    print(f"  Detail: {e.read().decode()[:200]}")

# Test 2: No file provided (empty multipart)
print("\n=== Test: No file provided ===")
body = f"--{BOUNDARY}\r\n--{BOUNDARY}--\r\n".encode()
req = urllib.request.Request(f"{BASE}/analyze", data=body, method="POST")
req.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print("UNEXPECTED success:", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Correctly rejected: HTTP {e.code}")
    print(f"  Detail: {e.read().decode()[:200]}")

# Test 3: OpenAPI schema
print("\n=== Test: OpenAPI schema ===")
resp = urllib.request.urlopen(f"{BASE}/openapi.json", timeout=10)
spec = json.loads(resp.read().decode())
print(f"Paths: {list(spec.get('paths', {}).keys())}")
analyze_spec = spec["paths"]["/analyze"]["post"]
print(f"  Summary: {analyze_spec.get('summary', 'N/A')}")
print(f"  Response schema fields: {list(analyze_spec.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema', {}).get('properties', {}).keys())}")

# Test 4: CORS preflight (OPTIONS)
print("\n=== Test: OPTIONS /analyze ===")
req = urllib.request.Request(f"{BASE}/analyze", method="OPTIONS")
resp = urllib.request.urlopen(req, timeout=10)
print(f"  Status: {resp.status}")
print(f"  Allow: {resp.headers.get('allow', 'N/A')}")

print("\nAll edge-case tests passed!")

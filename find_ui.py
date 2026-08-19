#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.rstrip()
    if any(k in s for k in ['st.expander', 'test.name', 'sub_score', 'test_card', 'expander', 'KPI', 'kpi', 'Per-Test', 'per-test', 'breakdown']):
        print(f'{i}: {s[:120]}')

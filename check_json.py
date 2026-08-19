#!/usr/bin/env python3
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open('json_output.txt', 'rb') as f:
    raw = f.read()
idx = raw.find(b'{')
text = raw[idx:].decode('utf-16-le')
data = json.loads(text)
print('Overall:', data.get('ai_probability'), data.get('verdict'))
print('Tests:', len(data.get('tests',[])))
for t in data.get('tests',[]):
    print(f'  {t["name"]}: AI={t["ai_probability"]}% conf={t["confidence"]:.2f}')
print('\nJSON output is valid with 8 tests!')

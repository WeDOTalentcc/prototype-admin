base = '/home/runner/workspace/plataforma-lia/src'
path = f'{base}/components/pages/chat-page/chat-core/useChatSession.ts'
with open(path) as f:
    lines = f.readlines()

# Find useEffects that contain companyId
import re
for i, line in enumerate(lines):
    if 'companyId' in line:
        print(f"Line {i+1}: {line}", end='')

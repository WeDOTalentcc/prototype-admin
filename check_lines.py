import os
base = '/home/runner/workspace/plataforma-lia/src'

path = f'{base}/components/pages/chat-page/chat-core/useChatSession.ts'
with open(path) as f:
    lines = f.readlines()

print("Lines 318-335:")
for i, l in enumerate(lines[317:335], 318):
    print(f"{i}: {l}", end='')
print("---")
print("Lines 395-415:")
for i, l in enumerate(lines[394:415], 395):
    print(f"{i}: {l}", end='')

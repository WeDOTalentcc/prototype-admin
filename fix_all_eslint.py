import re
import os

base = '/home/runner/workspace/plataforma-lia/src'

def read(path):
    with open(path) as f:
        return f.read()

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

def replace(content, old, new, label=""):
    if old in content:
        print(f"  FIXED: {label}")
        return content.replace(old, new)
    else:
        print(f"  MISS: {label} - pattern not found")
        return content

def remove_toast_dep(content):
    """Remove 'toast' from useCallback/useEffect dependency arrays"""
    # [toast] -> []
    content = re.sub(r'\[toast\]', '[]', content)
    # [toast, other -> [other
    content = re.sub(r'\[toast,\s*', '[', content)
    # , toast] -> ]
    content = re.sub(r',\s*\btoast\b(?=\s*\])', '', content)
    # toast, other -> other (in middle)
    content = re.sub(r'\btoast,\s*', '', content)
    return content

# ===== add-to-job-modal.tsx =====
path = f'{base}/components/modals/add-to-job-modal.tsx'
content = read(path)
original = content
# Check what the actual toast dep looks like
import re
matches = list(re.finditer(r'toast', content))
print(f"add-to-job-modal: found {len(matches)} 'toast' references")
# Find useEffect at line 28
lines = content.split('\n')
for i, line in enumerate(lines[25:35], 26):
    print(f"  L{i}: {line}")
new = remove_toast_dep(content)
if new != content:
    write(path, new)
    print("add-to-job-modal: removed toast from deps")
else:
    print("add-to-job-modal: no change made")

# ===== useJobUnpublish.ts =====
# Line 95: toast unnecessary dep
path = f'{base}/components/modals/useJobUnpublish.ts'
content = read(path)
original = content
content = remove_toast_dep(content)
if content != original:
    write(path, content)
    print("useJobUnpublish.ts: removed toast dep")
else:
    print("useJobUnpublish.ts: no toast dep found")

# ===== shared-search-details-modal.tsx =====  
# Line 64: missing dep 'loadDetails'
path = f'{base}/components/modals/shared-search-details-modal.tsx'
content = read(path)
original = content
# Find the useEffect that has [open, sharedSearchId] and add loadDetails
content = replace(content,
    '  }, [open, sharedSearchId])',
    '  }, [open, sharedSearchId, loadDetails])',
    'shared-search-details loadDetails dep'
)
if content != original:
    write(path, content)

# ===== useJobUnpublishModal.ts =====
# Line 159: missing dep 'jobs'  
path = f'{base}/components/modals/useJobUnpublishModal.ts'
content = read(path)
original = content
lines_content = content.split('\n')
print(f"\nuseJobUnpublishModal.ts lines around 155-165:")
for i, line in enumerate(lines_content[154:166], 155):
    print(f"  L{i}: {line}")
# Find useEffect at line 159 with missing jobs dep
# Check actual content
content = original
if content != original:
    write(path, content)

# ===== useStageTransitionModal.ts =====
# Line 197: missing dep 'jobs'
path = f'{base}/components/modals/useStageTransitionModal.ts'
if os.path.exists(path):
    content = read(path)
    original = content
    lines_content = content.split('\n')
    print(f"\nuseStageTransitionModal.ts lines around 192-205:")
    for i, line in enumerate(lines_content[191:206], 192):
        print(f"  L{i}: {line}")
else:
    print("useStageTransitionModal.ts NOT found")

# ===== useStageTransitionActions.ts =====
# Line 254: missing deps candidates, companyId, currentActionBehavior, fromStage, jobTitle, selectedToStage, sendMessage
path = f'{base}/components/modals/useStageTransitionActions.ts'
if os.path.exists(path):
    content = read(path)
    lines_content = content.split('\n')
    print(f"\nuseStageTransitionActions.ts lines around 249-260:")
    for i, line in enumerate(lines_content[248:262], 249):
        print(f"  L{i}: {line}")
else:
    print("useStageTransitionActions.ts NOT found")

# ===== useJobUnpublishModal.ts =====
path = f'{base}/components/modals/useJobUnpublishModal.ts'
content = read(path)
lines_content = content.split('\n')
print(f"\nuseJobUnpublishModal.ts lines around 154-165:")
for i, line in enumerate(lines_content[153:166], 154):
    print(f"  L{i}: {line}")

print("\nDone with inspection")

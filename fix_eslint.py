import re
import os

def remove_toast_dep(text):
    """Remove 'toast' from useCallback/useEffect dependency arrays"""
    # Remove toast when it's the only dep
    text = re.sub(r'\[toast\]', '[]', text)
    # Remove toast, at start of array
    text = re.sub(r'\[toast,\s*', '[', text)
    # Remove , toast at end of array
    text = re.sub(r',\s*toast\b(?=\s*\])', '', text)
    # Remove toast, in middle
    text = re.sub(r'\btoast,\s*', '', text)
    return text

def fix_file(path, fixes):
    """Apply list of (old, new) replacements to file"""
    with open(path) as f:
        content = f.read()
    original = content
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"  Applied fix in {os.path.basename(path)}")
        else:
            print(f"  WARNING: pattern not found in {os.path.basename(path)}: {repr(old[:60])}")
    if content != original:
        with open(path, 'w') as f:
            f.write(content)
    return content != original

base = '/home/runner/workspace/plataforma-lia/src'

# ======== 1. add-to-job-modal.tsx ========
# Line 28: useEffect has unnecessary dep: toast
path = f'{base}/components/modals/add-to-job-modal.tsx'
with open(path) as f:
    content = f.read()
new_content = remove_toast_dep(content)
if new_content != content:
    with open(path, 'w') as f:
        f.write(new_content)
    print(f'add-to-job-modal.tsx: removed toast dep')
else:
    print(f'add-to-job-modal.tsx: no toast dep found in arrays')

# ======== 2. close-vacancy-modal.tsx ========
# Warnings:
# Line 119: hiredCandidates logical expression - wrap in useMemo
# Line 312: missing deps closingWithoutHire, othersTemplateId, resolvedCompanyId
path = f'{base}/components/modals/close-vacancy-modal.tsx'
with open(path) as f:
    content = f.read()
original = content

# Fix hiredCandidates - it's declared inline and should be memoized
# Current: const hiredCandidates = hiredCandidatesProp || (hiredCandidateProp ? [hiredCandidateProp] : [])
# Fix: wrap in useMemo
old = '  const hiredCandidates = hiredCandidatesProp || (hiredCandidateProp ? [hiredCandidateProp] : [])'
new = '  const hiredCandidates = React.useMemo(\n    () => hiredCandidatesProp || (hiredCandidateProp ? [hiredCandidateProp] : []),\n    [hiredCandidatesProp, hiredCandidateProp]\n  )'
if old in content:
    content = content.replace(old, new)
    print('close-vacancy-modal.tsx: wrapped hiredCandidates in useMemo')
else:
    print('close-vacancy-modal.tsx: hiredCandidates pattern not found')

# Fix handleConfirm missing deps
# Current deps end with: onConfirm, onClose, ]
old_deps = '    onConfirm,\n    onClose,\n  ])'
new_deps = '    onConfirm,\n    onClose,\n    closingWithoutHire,\n    othersTemplateId,\n    resolvedCompanyId,\n  ])'
if old_deps in content:
    content = content.replace(old_deps, new_deps)
    print('close-vacancy-modal.tsx: added missing deps to handleConfirm')
else:
    print('close-vacancy-modal.tsx: handleConfirm deps pattern not found')

if content != original:
    with open(path, 'w') as f:
        f.write(content)

# Check if React is imported (needed for React.useMemo)
with open(path) as f:
    content = f.read()
if 'import React' not in content and 'from "react"' in content:
    content = content.replace("from \"react\"", ", { useMemo } from \"react\"") # might already have useMemo
    # Better approach: check imports
if 'useMemo' not in content.split('from "react"')[0] and 'React.useMemo' in content:
    # Need to ensure React is imported as namespace or useMemo is imported
    if 'import React,' not in content and 'import React ' not in content:
        # Add React import
        content = content.replace("import {", "import React, {", 1)
        with open(path, 'w') as f:
            f.write(content)
        print('close-vacancy-modal.tsx: added React import')

# ======== 3. job-assign-recruiter-modal.tsx ========
# Line 73: safeRecruiters - wrap in useMemo
path = f'{base}/components/modals/job-assign-recruiter-modal.tsx'
with open(path) as f:
    content = f.read()
original = content

old = '  const safeRecruiters = recruiters ?? []'
new = '  const safeRecruiters = React.useMemo(() => recruiters ?? [], [recruiters])'
if old in content:
    content = content.replace(old, new)
    print('job-assign-recruiter-modal.tsx: wrapped safeRecruiters in useMemo')
else:
    print('job-assign-recruiter-modal.tsx: safeRecruiters pattern not found')

if content != original:
    with open(path, 'w') as f:
        f.write(content)

# Check React import
with open(path) as f:
    content = f.read()
if 'React.useMemo' in content and 'import React' not in content:
    content = content.replace("from 'react'", "from 'react'")
    # Add React to import
    content = re.sub(r'import \{', 'import React, {', content, count=1)
    with open(path, 'w') as f:
        f.write(content)
    print('job-assign-recruiter-modal.tsx: added React import')

print('Done with modals')

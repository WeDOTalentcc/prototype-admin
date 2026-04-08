import re
import os

base = '/home/runner/workspace/plataforma-lia/src'

def read(path):
    with open(path) as f:
        return f.read()

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

# ===== 1. multimodal-upload.tsx =====
# The issue: function body ends with } then }, [deps]) was added
path = f'{base}/components/chat/multimodal-upload.tsx'
content = read(path)

# Find the broken pattern: `  }\n  }, [analysisType, onAnalysisComplete, onError])`
# And fix it to: `  }, [analysisType, onAnalysisComplete, onError])`
old = '  }\n  }, [analysisType, onAnalysisComplete, onError])'
new = '  }, [analysisType, onAnalysisComplete, onError])'
if old in content:
    content = content.replace(old, new)
    write(path, content)
    print("FIXED multimodal-upload.tsx")
else:
    print("MISS multimodal-upload.tsx - checking...")
    idx = content.find('}, [analysisType, onAnalysisComplete, onError])')
    if idx != -1:
        print(repr(content[idx-20:idx+50]))

# ===== 2. voice-chat-button.tsx =====
path = f'{base}/components/chat/voice-chat-button.tsx'
content = read(path)

old = '  }\n  }, [onError, onResponse, onTranscription, sessionId])'
new = '  }, [onError, onResponse, onTranscription, sessionId])'
if old in content:
    content = content.replace(old, new)
    write(path, content)
    print("FIXED voice-chat-button.tsx")
else:
    print("MISS voice-chat-button.tsx - checking...")
    idx = content.find('}, [onError, onResponse')
    if idx != -1:
        print(repr(content[idx-20:idx+60]))

# ===== 3. useJobStatusModal.ts =====
# handleSubmitAndNavigate wrapped incorrectly
path = f'{base}/components/modals/job-status/useJobStatusModal.ts'
content = read(path)

# The issue is the handleSubmitAndNavigate was wrapped but the last } became }, [])
# Find the broken pattern
idx = content.find('  }, [])\n\n  const handleSubmit')
if idx != -1:
    print(f"Found useJobStatusModal broken pattern at idx {idx}")
    print(repr(content[idx-30:idx+50]))

# The function was: const handleSubmitAndNavigate = async () => { ... }
# And we converted it to: const handleSubmitAndNavigate = useCallback(async () => { ... }, [])
# But the original closing } is also still there: }  }, [])
old = '  }\n  }, [])\n\n  const handleSubmit'
new = '  }, [])\n\n  const handleSubmit'
if old in content:
    content = content.replace(old, new)
    write(path, content)
    print("FIXED useJobStatusModal.ts")
else:
    print("MISS useJobStatusModal.ts - checking...")
    # Try other patterns
    idx = content.find('], [])')
    if idx != -1:
        print(repr(content[idx-30:idx+50]))
    idx2 = content.find('}, [])')
    if idx2 != -1:
        print(f"Found }}, []) at {idx2}:")
        print(repr(content[idx2-30:idx2+50]))
    
    # Find parse error region
    lines = content.split('\n')
    for i, line in enumerate(lines[295:320], 296):
        print(f"  L{i}: {line}")

print("\nDone with parse error fixes!")

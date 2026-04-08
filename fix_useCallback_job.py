base = '/home/runner/workspace/plataforma-lia/src'
path = f'{base}/components/modals/job-status/useJobStatusModal.ts'
with open(path) as f:
    content = f.read()

# The handleSubmitAndNavigate was made into useCallback but the closing } is wrong
# Current state: ends with `  }\n\n  const handleSubmit`
# Should be: ends with `  }, [])\n\n  const handleSubmit`
# 
# Also, we need to move handleSubmitAndNavigate BEFORE handleProceed (which references it)
# Or simply add eslint-disable for the circular reference issue
# 
# Let's fix the closing brace issue:
# Find the pattern: handleSubmitAndNavigate = useCallback(...) ending with }  then handleSubmit

old = '    }\n  }\n\n  const handleSubmit = async'
new = '    }\n  }, [])\n\n  const handleSubmit = async'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("FIXED useJobStatusModal.ts closing brace")
else:
    print("MISS - checking variants...")
    # Find setIsSubmitting(false) then }
    idx = content.find('      setIsSubmitting(false)\n    }\n  }\n')
    if idx != -1:
        print(f"Found at {idx}:")
        print(repr(content[idx:idx+80]))
    
    # Maybe it's already fixed somehow
    idx2 = content.find('setIsSubmitting(false)')
    while idx2 != -1:
        snippet = content[idx2:idx2+100]
        print(f"Found at {idx2}: {repr(snippet)}")
        idx2 = content.find('setIsSubmitting(false)', idx2+1)

path = 'plataforma-lia/src/components/lia-float/LiaChatShell.tsx'
with open(path) as f:
    content = f.read()

# Find hasDynamicPanel in FullPageShell (second occurrence)
idx = content.find('const hasDynamicPanel = !!state.dynamicPanel\n\n  return (\n    <>\n      <div\n        className={cn(\n          "flex flex-row h-full w-full"')
print(f"Found FullPageShell hasDynamicPanel at idx={idx}")
if idx != -1:
    # Find the useCallback ending just before this
    # Look back from idx to find state.addMessage, state.clearBackgroundTask
    snippet = content[idx-200:idx]
    print(f"Snippet before: {repr(snippet)}")

# Alternative: count occurrences 
occurrences = []
start = 0
while True:
    idx2 = content.find('  }, [state.addMessage, state.clearBackgroundTask])', start)
    if idx2 == -1:
        break
    occurrences.append(idx2)
    start = idx2 + 1

print(f"\nFound {len(occurrences)} occurrences of state.addMessage,state.clearBackgroundTask deps")

# Replace only the second occurrence (FullPageShell)
if len(occurrences) >= 1:
    # All should be replaced now since InlineLeftShell was already done
    for occ in occurrences:
        print(f"  At idx {occ}: {repr(content[occ:occ+60])}")

# Simple: just replace all remaining
old = '}, [state.addMessage, state.clearBackgroundTask])'
new = '}, [state])'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("Fixed!")
else:
    print("NOT FOUND")

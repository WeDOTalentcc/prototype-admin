path = '/home/runner/workspace/plataforma-lia/src/components/lia-float/LiaChatShell.tsx'
with open(path) as f:
    content = f.read()

old = '}, [state.addMessage, state.clearBackgroundTask])'
new = '}, [state])'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("Fixed!")
else:
    print("NOT FOUND - checking...")
    import re
    for m in re.finditer(r'state\.addMessage', content):
        print(repr(content[m.start()-10:m.start()+100]))

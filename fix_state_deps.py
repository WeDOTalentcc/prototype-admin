import re
import os

base = '/home/runner/workspace/plataforma-lia/src'

def read(path):
    with open(path) as f:
        return f.read()

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

# ===== LiaChatPanel.tsx =====
# Lines with useCallback using state.X but missing state in deps
path = f'{base}/components/lia-float/LiaChatPanel.tsx'
content = read(path)

# Pattern: useCallback that has state.X in deps but not state
# All these callbacks have state.X but not state itself
# Fix: replace state.X deps with state
# Lines 42, 47, 51, 62 in LiaChatPanel

# Line 42: handleSelectSession
content = content.replace(
    '  }, [state.handleLoadConversation])\n\n  const handleClearMode',
    '  }, [state])\n\n  const handleClearMode'
)
# Line 47: handleClearMode
content = content.replace(
    '  }, [state.setActiveActionType, state.setActionLabel])\n\n  const handleDismissTask',
    '  }, [state])\n\n  const handleDismissTask'
)
# Line 51: handleDismissTask
content = content.replace(
    '  }, [state.clearBackgroundTask])\n\n  const handleViewResult',
    '  }, [state])\n\n  const handleViewResult'
)
# Line 62: handleViewResult
content = content.replace(
    '  }, [state.addMessage, state.clearBackgroundTask])\n\n  if (!state.isOpen)',
    '  }, [state])\n\n  if (!state.isOpen)'
)

write(path, content)
print(f"Fixed LiaChatPanel.tsx")

# Verify
content = read(path)
c = content.split('\n')
for i, line in enumerate(c[39:65], 40):
    print(f"  L{i}: {line}")

# ===== LiaChatShell.tsx =====
# Lines 95, 100, 104, 115, 123 in InlineLeftShell
# Lines 327, 332, 336, 347 in FullPageShell
path = f'{base}/components/lia-float/LiaChatShell.tsx'
content = read(path)
original = content

# InlineLeftShell callbacks (lines 93-125)
# handleSelectSession
content = content.replace(
    '  const handleSelectSession = useCallback((sessionId: string) => {\n    state.handleLoadConversation(sessionId)\n  }, [state.handleLoadConversation])',
    '  const handleSelectSession = useCallback((sessionId: string) => {\n    state.handleLoadConversation(sessionId)\n  }, [state])'
)
# handleClearMode
content = content.replace(
    '  const handleClearMode = useCallback(() => {\n    state.setActiveActionType(null)\n    state.setActionLabel(null)\n  }, [state.setActiveActionType, state.setActionLabel])',
    '  const handleClearMode = useCallback(() => {\n    state.setActiveActionType(null)\n    state.setActionLabel(null)\n  }, [state])'
)
# handleDismissTask
content = content.replace(
    '  const handleDismissTask = useCallback((taskId: string) => {\n    state.clearBackgroundTask(taskId)\n  }, [state.clearBackgroundTask])',
    '  const handleDismissTask = useCallback((taskId: string) => {\n    state.clearBackgroundTask(taskId)\n  }, [state])'
)
# handleViewResult (InlineLeftShell)
old_hvr_inline = '  const handleViewResult = useCallback((task: BackgroundTask) => {\n    const resultSummary = task.message || "Tarefa concluída"\n    state.addMessage({\n      id: `bg-result-${task.id}-${Date.now()}`,\n      sender: "lia" as const,\n      content: `**${task.label}** — ${resultSummary}`,\n      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),\n    })\n    state.clearBackgroundTask(task.id)\n  }, [state.addMessage, state.clearBackgroundTask])\n\n  const handleClose'
new_hvr_inline = '  const handleViewResult = useCallback((task: BackgroundTask) => {\n    const resultSummary = task.message || "Tarefa concluída"\n    state.addMessage({\n      id: `bg-result-${task.id}-${Date.now()}`,\n      sender: "lia" as const,\n      content: `**${task.label}** — ${resultSummary}`,\n      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),\n    })\n    state.clearBackgroundTask(task.id)\n  }, [state])\n\n  const handleClose'
if old_hvr_inline in content:
    content = content.replace(old_hvr_inline, new_hvr_inline)
    print("Fixed InlineLeftShell handleViewResult")
else:
    print("MISS InlineLeftShell handleViewResult")

# handleClose 
content = content.replace(
    '  const handleClose = useCallback(() => {\n    if (onClose) {\n      onClose()\n    } else {\n      state.close()\n    }\n  }, [onClose, state.close])',
    '  const handleClose = useCallback(() => {\n    if (onClose) {\n      onClose()\n    } else {\n      state.close()\n    }\n  }, [onClose, state])'
)

# FullPageShell callbacks (lines 325-347)
# handleSelectSession in FullPageShell - second occurrence
# We need to handle the fact that the same code appears twice
# Since we already replaced the InlineLeftShell version, we need to fix FullPageShell

# Count current occurrences
n_state_deps = content.count('}, [state])')
print(f"Current [state] occurrences: {n_state_deps}")

# For FullPageShell, which is the second set:
# handleSelectSession - second occurrence
# Look at what remains
lines = content.split('\n')
print(f"\nLines around 325-350:")
for i, line in enumerate(lines[322:352], 323):
    print(f"  L{i}: {line}")

write(path, content)
print(f"Fixed LiaChatShell.tsx (partial)")

#!/usr/bin/env python3
"""Fix TypeScript errors in AgentStudioPage wiring."""
path = "/home/runner/workspace/plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx"
with open(path) as f:
    content = f.read()

# Fix 1: Import conflict — AgentCard name clashes. Rename import alias.
content = content.replace(
    'import { TemplateGallery, AgentCard, DeployDialog } from "@/components/pages-agent-studio/custom-agents"',
    'import { TemplateGallery, AgentCard as CustomAgentCard, DeployDialog } from "@/components/pages-agent-studio/custom-agents"',
)
# Also rename usage
content = content.replace(
    '                    <AgentCard\n                      key={agent.id}\n                      agent={agent}\n                      onTest={() => {/* TODO: open test modal */}}\n                      onDeploy={(a) => setDeployAgent(a)}\n                      onToggleStatus={handleCustomAgentToggle}',
    '                    <CustomAgentCard\n                      key={agent.id}\n                      agent={agent}\n                      onTest={() => {/* TODO: open test modal */}}\n                      onDeploy={(a) => setDeployAgent(a)}\n                      onToggleStatus={handleCustomAgentToggle}',
)
print("OK: renamed AgentCard import to CustomAgentCard")

# Fix 2: CustomAgent type mismatch — the map was iterating customAgents but
# the AgentCard expects CustomAgent type which is correct. The error is that
# somewhere agent is being treated as SourcingAgent. Let me check the actual error.
# Error TS2740 at line 477: Type 'CustomAgent' missing properties from 'SourcingAgent'
# This means somewhere we're passing CustomAgent where SourcingAgent is expected.
# Actually looking at the code, the error might be from a different AgentCard.
# Let me check — actually the fix above (renaming to CustomAgentCard) should resolve
# the conflict. The TS2740 error was likely because the wrong AgentCard was being used.

# Fix 3: onToggleStatus type — expects (agent: CustomAgent) => Promise<void> but
# the prop interface expects (agent: CustomAgent) => void. Need to match.
# Actually the AgentCard interface has: onToggleStatus: (agent: CustomAgent) => void
# and handleCustomAgentToggle is async, which returns Promise<void>.
# Promise<void> is assignable to void in TypeScript. Let me check the actual error again.
# Error at line 480: Type '(agent: CustomAgent) => Promise<void>' not assignable to '() => void'
# This means the prop type is () => void not (agent: CustomAgent) => void.
# Wait — I defined the prop as onToggleStatus: (agent: CustomAgent) => void in AgentCard.tsx.
# The error says it expects () => void. Let me wrap it.
content = content.replace(
    'onToggleStatus={handleCustomAgentToggle}',
    'onToggleStatus={(a) => { handleCustomAgentToggle(a) }}',
)
print("OK: wrapped onToggleStatus to avoid async type issue")

with open(path, "w") as f:
    f.write(content)

print("Fixes applied")

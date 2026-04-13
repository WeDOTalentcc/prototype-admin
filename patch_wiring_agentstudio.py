#!/usr/bin/env python3
"""
Wire Onda 1 components into AgentStudioPage.tsx
- Add TemplateGallery + AgentCard + DeployDialog to the "custom" tab
- Keep existing sourcing agents tab untouched
- Keep existing marketplace, twins, search tabs untouched
"""
import os

path = "/home/runner/workspace/plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx"
with open(path) as f:
    content = f.read()

# 1. Add imports for new components
old_imports = 'import CustomAgentsTab from "@/components/pages-agent-studio/CustomAgentsTab"'
new_imports = '''import CustomAgentsTab from "@/components/pages-agent-studio/CustomAgentsTab"
import { TemplateGallery, AgentCard, DeployDialog } from "@/components/pages-agent-studio/custom-agents"
import { useCustomAgents } from "@/hooks/agents"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import type { CustomAgent, AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"'''

if old_imports in content:
    content = content.replace(old_imports, new_imports, 1)
    print("OK: imports added")
else:
    print("SKIP: imports pattern not found")

# 2. Add state for deploy dialog and custom agents hook
# Find the line with evaluatingTwinId state and add after it
old_state = '  const [evaluatingTwinId, setEvaluatingTwinId] = useState<string | null>(null)'
new_state = '''  const [evaluatingTwinId, setEvaluatingTwinId] = useState<string | null>(null)
  const [deployAgent, setDeployAgent] = useState<CustomAgent | null>(null)
  const { agents: customAgents, mutate: mutateCustomAgents } = useCustomAgents()
  const { selectTemplate, reset: resetStudio } = useAgentStudioStore()'''

if old_state in content:
    content = content.replace(old_state, new_state, 1)
    print("OK: state added")
else:
    print("SKIP: state pattern not found")

# 3. Add handler functions after handleToggleStatus
old_handler = '  const totalViewed = agents.reduce'
new_handler = '''  const handleTemplateSelect = async (template: AgentTemplate) => {
    selectTemplate(template)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          name: template.name,
          role: template.description,
          description: template.description,
          system_prompt: template.system_prompt,
          allowed_tools: template.allowed_tools,
          domain: template.domain,
          icon: template.icon,
          max_steps: template.max_steps,
          temperature: template.temperature,
          enable_memory: template.enable_memory,
          context_level: template.context_level,
          excluded_tools: template.excluded_tools,
        }),
      })
      if (!res.ok) throw new Error("Erro ao criar agente")
      toast.success(`Agente "${template.name}" criado!`, "Agora vincule a uma vaga ou banco de talentos.")
      mutateCustomAgents()
      resetStudio()
      setActiveTab("custom")
    } catch {
      toast.error("Erro ao criar agente", "Tente novamente.")
    }
  }

  const handleCustomAgentToggle = async (agent: CustomAgent) => {
    const newStatus = agent.status === "active" ? "paused" : "active"
    try {
      const token = localStorage.getItem("auth_token")
      await fetch(`/api/backend-proxy/custom-agents/${agent.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ status: newStatus }),
      })
      toast.success(newStatus === "active" ? "Agente ativado" : "Agente pausado")
      mutateCustomAgents()
    } catch {
      toast.error("Erro ao alterar status")
    }
  }

  const totalViewed = agents.reduce'''

if old_handler in content:
    content = content.replace(old_handler, new_handler, 1)
    print("OK: handlers added")
else:
    print("SKIP: handler pattern not found")

# 4. Replace the "custom" tab content
# Find the current custom tab rendering
old_custom_tab = '        {activeTab === "custom" && <CustomAgentsTab />}'
new_custom_tab = '''        {activeTab === "custom" && (
          <div className="space-y-6">
            {/* My Agents */}
            {customAgents.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                  Meus Agentes ({customAgents.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {customAgents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      onTest={() => {/* TODO: open test modal */}}
                      onDeploy={(a) => setDeployAgent(a)}
                      onToggleStatus={handleCustomAgentToggle}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Template Gallery */}
            <TemplateGallery
              onTemplateSelect={handleTemplateSelect}
              onCreateManual={() => setShowCreateModal(true)}
            />

            {/* Deploy Dialog */}
            <DeployDialog
              agent={deployAgent}
              open={!!deployAgent}
              onClose={() => setDeployAgent(null)}
              onDeployed={() => mutateCustomAgents()}
            />
          </div>
        )}'''

if old_custom_tab in content:
    content = content.replace(old_custom_tab, new_custom_tab, 1)
    print("OK: custom tab wired")
else:
    print("SKIP: custom tab pattern not found")

with open(path, "w") as f:
    f.write(content)

# Verify syntax
import subprocess
result = subprocess.run(
    ["node", "-e", "try { require('fs').readFileSync('" + path + "', 'utf8'); console.log('SYNTAX OK') } catch(e) { console.log('ERROR:', e.message) }"],
    capture_output=True, text=True, cwd="/home/runner/workspace/plataforma-lia"
)
print(result.stdout.strip() if result.stdout else "Node check ran")
print("\nWiring complete!")

#!/usr/bin/env python3
"""Wire custom tab — exact pattern match."""
path = "/home/runner/workspace/plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx"
with open(path) as f:
    content = f.read()

old = """        {activeTab === "custom" && (
          <CustomAgentsTab />
        )}"""

new = """        {activeTab === "custom" && (
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

            {/* Legacy form for advanced editing */}
            <details className="mt-4">
              <summary className="text-xs text-lia-text-disabled cursor-pointer hover:text-lia-text-secondary">
                Formulario avancado (modo tecnico)
              </summary>
              <div className="mt-3">
                <CustomAgentsTab />
              </div>
            </details>
          </div>
        )}"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK: custom tab wired with Gallery + Cards + Deploy + Legacy form")
else:
    print("ERROR: pattern not found")

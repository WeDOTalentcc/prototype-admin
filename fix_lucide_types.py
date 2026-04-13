#!/usr/bin/env python3
"""Fix Lucide icon type casting in TemplateCard and TemplateGallery."""
import os

BASE = "/home/runner/workspace/plataforma-lia/src"

# Fix TemplateCard.tsx
path1 = os.path.join(BASE, "components/pages-agent-studio/custom-agents/TemplateCard.tsx")
with open(path1) as f:
    c = f.read()
old1 = 'const IconComponent = (Icons as Record<string, React.ComponentType<{ className?: string }>>)[template.icon] || Icons.Bot'
new1 = '// eslint-disable-next-line @typescript-eslint/no-explicit-any\n  const IconComponent = ((Icons as any)[template.icon] || Icons.Bot) as React.ComponentType<{ className?: string }>'
if old1 in c:
    c = c.replace(old1, new1)
    with open(path1, "w") as f:
        f.write(c)
    print("OK: TemplateCard.tsx fixed")

# Fix TemplateGallery.tsx
path2 = os.path.join(BASE, "components/pages-agent-studio/custom-agents/TemplateGallery.tsx")
with open(path2) as f:
    c = f.read()
old2 = 'const CatIcon = (Icons as Record<string, React.ComponentType<{ className?: string }>>)[cat.icon] || Icons.LayoutGrid'
new2 = '// eslint-disable-next-line @typescript-eslint/no-explicit-any\n          const CatIcon = ((Icons as any)[cat.icon] || Icons.LayoutGrid) as React.ComponentType<{ className?: string }>'
if old2 in c:
    c = c.replace(old2, new2)
    with open(path2, "w") as f:
        f.write(c)
    print("OK: TemplateGallery.tsx fixed")

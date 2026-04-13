#!/usr/bin/env python3
"""Add Studio modes to ModeLabel.tsx config."""
path = "/home/runner/workspace/plataforma-lia/src/components/lia-float/ModeLabel.tsx"
with open(path) as f:
    content = f.read()

# Add Bot icon to imports
content = content.replace(
    "Plug, Bell, StickyNote, CalendarDays, UserCog,",
    "Plug, Bell, StickyNote, CalendarDays, UserCog, Bot, Search, BarChart3,",
)

# Add 3 new modes after candidate_field
old = """  candidate_field: {
    icon: UserCog,
    bg: "bg-teal-500/10",
    text: "text-teal-600 dark:text-teal-400",
    border: "border-teal-500/20",
  },
}"""

new = """  candidate_field: {
    icon: UserCog,
    bg: "bg-teal-500/10",
    text: "text-teal-600 dark:text-teal-400",
    border: "border-teal-500/20",
  },
  studio_create: {
    icon: Bot,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-dark dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
  studio_query: {
    icon: Search,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-dark dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
  studio_metrics: {
    icon: BarChart3,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-dark dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
}"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK: added 3 studio modes to ModeLabel")
else:
    print("ERROR: pattern not found")

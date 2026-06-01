"use client"

import { Node, mergeAttributes } from "@tiptap/core"

export interface TemplateVariableOptions {
  HTMLAttributes: Record<string, string>
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    templateVariable: {
      insertVariable: (name: string) => ReturnType
    }
  }
}

export const TemplateVariable = Node.create<TemplateVariableOptions>({
  name: "templateVariable",
  group: "inline",
  inline: true,
  atom: true,
  selectable: true,
  draggable: false,

  addAttributes() {
    return {
      name: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-variable"),
        renderHTML: (attributes) => ({
          "data-variable": attributes.name,
        }),
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-variable]',
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-variable": node.attrs.name,
        class:
          "lia-variable-chip inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 rounded bg-wedo-cyan/15 text-wedo-cyan-dark dark:text-wedo-cyan text-xs font-mono select-none border border-wedo-cyan/30",
        contenteditable: "false",
      }),
      `{{${node.attrs.name}}}`,
    ]
  },

  addCommands() {
    return {
      insertVariable:
        (name: string) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { name },
          })
        },
    }
  },
})

// Variable names are constrained to word characters (\w = [a-zA-Z0-9_]).
// If variable syntax expands (e.g., dots or hyphens), update these regexes.
export function htmlToTiptapContent(html: string): string {
  return html.replace(
    /\{\{(\w+)\}\}/g,
    '<span data-variable="$1">{{$1}}</span>'
  )
}

export function tiptapContentToHtml(html: string): string {
  return html.replace(
    /<span[^>]*data-variable="(\w+)"[^>]*>[^<]*<\/span>/g,
    "{{$1}}"
  )
}

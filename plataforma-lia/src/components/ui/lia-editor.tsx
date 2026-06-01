"use client"

import React, { useCallback, useEffect, type MutableRefObject } from "react"
import { useEditor, EditorContent, type Editor } from "@tiptap/react"
import type { AnyExtension } from "@tiptap/core"
import StarterKit from "@tiptap/starter-kit"
import Link from "@tiptap/extension-link"
import Placeholder from "@tiptap/extension-placeholder"
import { cn } from "@/lib/utils"
import {
  Bold,
  Italic,
  Strikethrough,
  List,
  ListOrdered,
  Heading2,
  Heading3,
  Link as LinkIcon,
  Undo,
  Redo,
  Quote,
  Minus,
  Code,
} from "lucide-react"

export interface LiaEditorProps {
  content: string
  onUpdate: (html: string) => void
  placeholder?: string
  extensions?: AnyExtension[]
  className?: string
  editorClassName?: string
  minHeight?: string
  disabled?: boolean
  toolbar?: "full" | "basic" | "none"
  id?: string
  editorRef?: MutableRefObject<Editor | null>
}

interface ToolbarButtonProps {
  onClick: () => void
  isActive?: boolean
  disabled?: boolean
  title: string
  children: React.ReactNode
}

function ToolbarButton({ onClick, isActive, disabled, title, children }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        "p-1.5 rounded-md transition-colors motion-reduce:transition-none",
        isActive
          ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
          : "text-lia-text-secondary hover:bg-lia-interactive-hover hover:text-lia-text-primary",
        disabled && "opacity-40 cursor-not-allowed"
      )}
    >
      {children}
    </button>
  )
}

function ToolbarDivider() {
  return <div className="w-px h-5 bg-lia-border-subtle mx-0.5" />
}

function EditorToolbar({ editor, variant }: { editor: Editor; variant: "full" | "basic" }) {
  const setLink = useCallback(() => {
    const previousUrl = editor.getAttributes("link").href
    const url = window.prompt("URL:", previousUrl)
    if (url === null) return
    if (url === "") {
      editor.chain().focus().extendMarkRange("link").unsetLink().run()
      return
    }
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run()
  }, [editor])

  return (
    <div className="flex items-center gap-0.5 px-2 py-1.5 bg-lia-bg-secondary dark:bg-lia-bg-elevated flex-wrap">
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBold().run()}
        isActive={editor.isActive("bold")}
        title="Negrito"
      >
        <Bold className="w-3.5 h-3.5" />
      </ToolbarButton>

      <ToolbarButton
        onClick={() => editor.chain().focus().toggleItalic().run()}
        isActive={editor.isActive("italic")}
        title="Itálico"
      >
        <Italic className="w-3.5 h-3.5" />
      </ToolbarButton>

      {variant === "full" && (
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleStrike().run()}
          isActive={editor.isActive("strike")}
          title="Tachado"
        >
          <Strikethrough className="w-3.5 h-3.5" />
        </ToolbarButton>
      )}

      <ToolbarDivider />

      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        isActive={editor.isActive("heading", { level: 2 })}
        title="Título H2"
      >
        <Heading2 className="w-3.5 h-3.5" />
      </ToolbarButton>

      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        isActive={editor.isActive("heading", { level: 3 })}
        title="Título H3"
      >
        <Heading3 className="w-3.5 h-3.5" />
      </ToolbarButton>

      <ToolbarDivider />

      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        isActive={editor.isActive("bulletList")}
        title="Lista"
      >
        <List className="w-3.5 h-3.5" />
      </ToolbarButton>

      <ToolbarButton
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        isActive={editor.isActive("orderedList")}
        title="Lista Numerada"
      >
        <ListOrdered className="w-3.5 h-3.5" />
      </ToolbarButton>

      {variant === "full" && (
        <>
          <ToolbarDivider />

          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            isActive={editor.isActive("blockquote")}
            title="Citação"
          >
            <Quote className="w-3.5 h-3.5" />
          </ToolbarButton>

          <ToolbarButton
            onClick={() => editor.chain().focus().toggleCode().run()}
            isActive={editor.isActive("code")}
            title="Código"
          >
            <Code className="w-3.5 h-3.5" />
          </ToolbarButton>

          <ToolbarButton
            onClick={() => editor.chain().focus().setHorizontalRule().run()}
            title="Linha horizontal"
          >
            <Minus className="w-3.5 h-3.5" />
          </ToolbarButton>

          <ToolbarButton
            onClick={setLink}
            isActive={editor.isActive("link")}
            title="Link"
          >
            <LinkIcon className="w-3.5 h-3.5" />
          </ToolbarButton>
        </>
      )}

      <ToolbarDivider />

      <ToolbarButton
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        title="Desfazer"
      >
        <Undo className="w-3.5 h-3.5" />
      </ToolbarButton>

      <ToolbarButton
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        title="Refazer"
      >
        <Redo className="w-3.5 h-3.5" />
      </ToolbarButton>
    </div>
  )
}

export function LiaEditor({
  content,
  onUpdate,
  placeholder = "Escreva aqui...",
  extensions: extraExtensions,
  className,
  editorClassName,
  minHeight = "200px",
  disabled = false,
  toolbar = "full",
  id,
  editorRef,
}: LiaEditorProps) {
  const defaultExtensions = [
    StarterKit.configure({
      heading: { levels: [2, 3, 4] },
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: "text-wedo-cyan underline hover:text-wedo-cyan-dark",
      },
    }),
    Placeholder.configure({ placeholder }),
  ]

  const allExtensions = (extraExtensions
    ? [...defaultExtensions, ...extraExtensions]
    : defaultExtensions) as AnyExtension[]

  const editor = useEditor({
    extensions: allExtensions,
    content,
    editable: !disabled,
    // T-1167 (Bug "Algo deu errado / Tiptap Error: SSR has been detected") —
    // Tiptap v3 renderiza no servidor por padrão e isso causa hydration mismatch
    // no Next.js App Router (a página /pt/jobs quebrava com "Algo deu errado.
    // Ocorreu um erro ao carregar esta seção. Tiptap Error: SSR has been
    // detected, please set..."). Fix oficial Tiptap v3 para Next.js SSR é
    // marcar immediatelyRender: false — o editor monta só no client.
    // Aplicado na FONTE (LiaEditor) e não nos 4 callsites (canonical-fix).
    immediatelyRender: false,
    onUpdate: ({ editor: ed }) => {
      onUpdate(ed.getHTML())
    },
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-sm max-w-none focus:outline-none",
          "text-lia-text-primary",
          "prose-headings:text-lia-text-primary prose-headings:font-semibold",
          "prose-p:text-lia-text-primary prose-p:leading-relaxed prose-p:my-1",
          "prose-a:text-wedo-cyan prose-a:no-underline hover:prose-a:underline",
          "prose-strong:text-lia-text-primary prose-strong:font-semibold",
          "prose-ul:my-1 prose-ol:my-1 prose-li:my-0",
          "prose-blockquote:border-lia-border-subtle prose-blockquote:text-lia-text-secondary",
          "prose-code:text-wedo-cyan-dark prose-code:bg-lia-bg-tertiary prose-code:px-1 prose-code:rounded",
          "prose-hr:border-lia-border-subtle",
          editorClassName
        ),
        ...(id ? { id } : {}),
      },
    },
  })

  useEffect(() => {
    if (editorRef && editor) {
      editorRef.current = editor
    }
    return () => {
      if (editorRef) {
        editorRef.current = null
      }
    }
  }, [editor, editorRef])

  useEffect(() => {
    if (editor && !editor.isDestroyed && disabled !== !editor.isEditable) {
      editor.setEditable(!disabled)
    }
  }, [editor, disabled])

  useEffect(() => {
    if (editor && !editor.isDestroyed) {
      const currentContent = editor.getHTML()
      if (content !== currentContent) {
        editor.commands.setContent(content, { emitUpdate: false })
      }
    }
  }, [content, editor])

  if (!editor) return null

  return (
    <div
      className={cn(
        "rounded-md border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-elevated overflow-hidden",
        "focus-within:border-lia-border-medium focus-within:ring-2 focus-within:ring-lia-btn-primary-bg/20 dark:focus-within:ring-lia-border-subtle/20",
        disabled && "opacity-60 cursor-not-allowed",
        className
      )}
    >
      {toolbar !== "none" && (
        <EditorToolbar editor={editor} variant={toolbar} />
      )}
      <EditorContent
        editor={editor}
        className={cn("px-3 py-2 text-xs overflow-y-auto")}
        style={{ minHeight }}
      />
    </div>
  )
}

export function useLiaEditor() {
  return { LiaEditor }
}

export { type Editor }

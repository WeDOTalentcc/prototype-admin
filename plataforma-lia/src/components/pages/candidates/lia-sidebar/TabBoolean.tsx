"use client"
import React, { useState } from "react"
import { Code, Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button"

export const TabBoolean = React.memo(function TabBoolean() {
  const [booleanSearchValue, setBooleanSearchValue] = useState("")

  return (
    <div className="space-y-4 overflow-y-auto flex-1 p-4">
      <p className="text-xs text-lia-text-tertiary">
        Use operadores booleanos para buscas avan\u00e7adas
      </p>
      <div className="flex flex-wrap gap-1 mb-2">
        {['AND', 'OR', 'NOT', '"..."', '(...)'].map((op) => (
          <button
            key={op}
            onClick={() => setBooleanSearchValue(prev => prev + ' ' + op)}
            className="px-2 py-1 text-xs rounded-full bg-gray-100 hover:bg-gray-200 text-lia-text-primary font-mono transition-colors motion-reduce:transition-none"
          >
            {op}
          </button>
        ))}
      </div>
      <textarea
        value={booleanSearchValue}
        onChange={(e) => setBooleanSearchValue(e.target.value)}
        placeholder={'Ex: ("Node.js" OR "Python") AND "s\u00eanior" NOT "j\u00fanior"'}
        className="w-full h-32 p-3 text-xs rounded-md border focus:outline-none transition-colors motion-reduce:transition-none resize-none bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary font-mono border border-lia-border-subtle"
      />
      <div className="p-3 rounded-md bg-wedo-cyan/[0.06]">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-primary dark:text-lia-text-tertiary">
            <strong>Dica:</strong> Use aspas para termos exatos e par\u00eanteses para agrupar condi\u00e7\u00f5es.
          </p>
        </div>
      </div>
      <Button
        className="w-full h-11 !text-sm font-semibold bg-wedo-cyan-dark text-white font-open-sans"
        onClick={() => { if (booleanSearchValue.trim()) {} }}
        disabled={!booleanSearchValue.trim()}
      >
        <Code className="w-4 h-4 mr-2" />
        Buscar com Boolean
      </Button>
    </div>
  )
})

TabBoolean.displayName = "TabBoolean"

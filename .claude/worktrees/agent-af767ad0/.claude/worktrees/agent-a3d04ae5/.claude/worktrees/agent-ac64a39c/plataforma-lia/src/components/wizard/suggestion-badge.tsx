'use client';

import { cn } from '@/lib/utils';
import type { Suggestion, DataSource } from '@/types/wizard-suggestions';
import { SOURCE_LABELS, SOURCE_COLORS } from '@/types/wizard-suggestions';
import { Lightbulb, Check, X } from 'lucide-react';

interface SuggestionBadgeProps {
  suggestion: Suggestion | null;
  onAccept?: (value: any) => void;
  onReject?: () => void;
  showActions?: boolean;
  compact?: boolean;
  className?: string;
}

export function SuggestionBadge({
  suggestion,
  onAccept,
  onReject,
  showActions = true,
  compact = false,
  className
}: SuggestionBadgeProps) {
  if (!suggestion) return null;

  const confidenceColor = 
    suggestion.confidence >= 0.9 ? 'text-green-600' :
    suggestion.confidence >= 0.7 ? 'text-yellow-600' :
    'text-gray-500';

  const sourceColor = SOURCE_COLORS[suggestion.source] || 'bg-gray-100 text-gray-800';
  const sourceLabel = SOURCE_LABELS[suggestion.source] || suggestion.source;

  if (compact) {
    return (
      <span className={cn(
        'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
        sourceColor,
        className
      )}>
        <Lightbulb className="h-3 w-3" />
        {sourceLabel}
      </span>
    );
  }

  return (
    <div className={cn(
      'flex items-start gap-2 p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900',
      className
    )}>
      <Lightbulb className="h-4 w-4 text-gray-900 dark:text-gray-50 mt-0.5 flex-shrink-0" />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn('text-xs px-1.5 py-0.5 rounded-full', sourceColor)}>
            {sourceLabel}
          </span>
          <span className={cn('text-xs font-medium', confidenceColor)}>
            {Math.round(suggestion.confidence * 100)}% confiança
          </span>
        </div>
        
        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
          {suggestion.explanation}
        </p>
      </div>

      {showActions && (onAccept || onReject) && (
        <div className="flex items-center gap-1 flex-shrink-0">
          {onAccept && (
            <button
              onClick={() => onAccept(suggestion.value)}
              className="p-1 rounded-md hover:bg-green-100 text-green-600 transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
              title="Aceitar sugestão"
              aria-label="Aceitar sugestão"
            >
              <Check className="h-4 w-4" />
            </button>
          )}
          {onReject && (
            <button
              onClick={onReject}
              className="p-1 rounded-md hover:bg-red-100 text-red-600 transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
              title="Ignorar sugestão"
              aria-label="Ignorar sugestão"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

interface FieldWithSuggestionProps {
  label: string;
  field: string;
  value: any;
  suggestion: Suggestion | null;
  onChange: (value: any) => void;
  isAutoFilled?: boolean;
  children: React.ReactNode;
}

export function FieldWithSuggestion({
  label,
  field,
  value,
  suggestion,
  onChange,
  isAutoFilled = false,
  children
}: FieldWithSuggestionProps) {
  const handleAccept = (suggestedValue: any) => {
    onChange(suggestedValue);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          {label}
        </label>
        {isAutoFilled && (
          <span className="text-xs text-gray-900 dark:text-gray-50 flex items-center gap-1">
            <Lightbulb className="h-3 w-3" />
            Preenchido automaticamente
          </span>
        )}
      </div>
      
      {children}
      
      {suggestion && !isAutoFilled && (
        <SuggestionBadge
          suggestion={suggestion}
          onAccept={handleAccept}
          showActions={true}
        />
      )}
    </div>
  );
}

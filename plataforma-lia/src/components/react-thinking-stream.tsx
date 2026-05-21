/**
 * ReactThinkingStream — displays ReAct loop thinking steps as a live stream.
 *
 * Renders intermediate "thought" events emitted by the ReAct loop via
 * WebSocket so the recruiter can see tool-call reasoning in real-time.
 *
 * E7 — Streaming de Pensamentos ReAct via WebSocket.
 */

"use client";

import React from "react";

export interface ThinkingEvent {
  type: "thinking";
  step: number;
  thought: string;
  tool_name?: string;
}

interface ReactThinkingStreamProps {
  events: ThinkingEvent[];
  isVisible?: boolean;
  className?: string;
}

/**
 * Renders a list of thinking steps from the ReAct loop.
 * Collapses when empty to avoid visual noise.
 */
export function ReactThinkingStream({
  events,
  isVisible = true,
  className = "",
}: ReactThinkingStreamProps) {
  if (!isVisible || events.length === 0) return null;

  return (
    <div className={className}>
      {events.map((ev) => (
        <div key={ev.step} className="flex gap-1 items-start">
          <span className="font-mono opacity-50">{ev.step}.</span>
          <span>{ev.thought}</span>
        </div>
      ))}
    </div>
  );
}

export default ReactThinkingStream;

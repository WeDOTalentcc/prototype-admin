// src/hooks/chat/__tests__/chat_bug_fixes_2026_06_18.test.ts
/**
 * TDD tests for chat bug fixes 2026-06-18:
 *   BUG-1: onCompleteRef must use useRef (not object literal) — stale closure fix
 *   BUG-3: WS reconnect useEffect must use isConnected ref, not stale closure
 *   BUG-8: AbortSignal.timeout must be compat-wrapped for older browsers
 */
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const CHAT_MESSAGES_PATH = path.join(
  __dirname,
  "../../chat/useChatMessages.ts"
);
const CHAT_SOCKET_PATH = path.join(
  __dirname,
  "../../chat/useChatSocket.ts"
);

describe("BUG-1: onCompleteRef must use useRef, not object literal", () => {
  it("useChatMessages.ts must NOT contain { current: onMessageComplete }", () => {
    const src = fs.readFileSync(CHAT_MESSAGES_PATH, "utf-8");
    expect(src).not.toContain("{ current: onMessageComplete }");
  });

  it("useChatMessages.ts must use useRef for onCompleteRef", () => {
    const src = fs.readFileSync(CHAT_MESSAGES_PATH, "utf-8");
    expect(src).toContain("const onCompleteRef = useRef(onMessageComplete)");
  });

  it("useChatMessages.ts must sync onCompleteRef with useEffect", () => {
    const src = fs.readFileSync(CHAT_MESSAGES_PATH, "utf-8");
    expect(src).toContain("onCompleteRef.current = onMessageComplete");
    expect(src).toContain("}, [onMessageComplete]);");
  });
});

describe("BUG-3: WS reconnect must not use stale isConnected closure", () => {
  it("useChatSocket.ts must have isConnectedForReconnRef ref fix applied", () => {
    const src = fs.readFileSync(CHAT_SOCKET_PATH, "utf-8");
    // BUG-3 fix: isConnected must be tracked via a ref in the wsAuthToken useEffect
    // to avoid stale closure when token arrives before WS connects.
    expect(src).toContain("_isConnectedForReconnRef");
    expect(src).toContain("_isConnectedForReconnRef.current = isConnected");
  });
});

describe("BUG-8: AbortSignal.timeout must have compat wrapper", () => {
  it("useChatMessages.ts must NOT call AbortSignal.timeout directly", () => {
    const src = fs.readFileSync(CHAT_MESSAGES_PATH, "utf-8");
    // Direct calls were replaced with _abortTimeout helper
    expect(src).not.toContain("AbortSignal.timeout(12_000)");
    expect(src).not.toContain("AbortSignal.timeout(8_000)");
  });

  it("useChatMessages.ts must have browser-compat AbortSignal.timeout wrapper", () => {
    const src = fs.readFileSync(CHAT_MESSAGES_PATH, "utf-8");
    // Compat wrapper must check if AbortSignal.timeout exists before calling
    expect(src).toContain("typeof AbortSignal.timeout");
    expect(src).toContain("new AbortController()");
  });
});

describe("BUG-7 — _lastSentMsRef residual event guard", () => {
  it("useChatSocket.ts declares _lastSentMsRef", () => {
    const src = require("fs").readFileSync(
      require("path").resolve(
        __dirname,
        "../useChatSocket.ts",
      ),
      "utf8",
    );
    expect(src).toContain("_lastSentMsRef");
    expect(src).toContain("_lastSentMsRef.current = Date.now()");
  });

  it("wsSend sets _lastSentMsRef before turnClosedRef", () => {
    const src = require("fs").readFileSync(
      require("path").resolve(__dirname, "../useChatSocket.ts"),
      "utf8",
    );
    const wsSendIdx = src.indexOf("const wsSend = useCallback");
    const lastSentIdx = src.indexOf("_lastSentMsRef.current = Date.now()", wsSendIdx);
    const turnClosedIdx = src.indexOf("turnClosedRef.current = true", wsSendIdx);
    expect(lastSentIdx).toBeGreaterThan(wsSendIdx);
    expect(lastSentIdx).toBeLessThan(turnClosedIdx);
  });

  it("thinking case has 150ms residual guard", () => {
    const src = require("fs").readFileSync(
      require("path").resolve(__dirname, "../useChatSocket.ts"),
      "utf8",
    );
    expect(src).toContain("Date.now() - _lastSentMsRef.current < 150");
  });
});


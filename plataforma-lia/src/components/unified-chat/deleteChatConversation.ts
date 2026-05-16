export interface DeleteChatConversationDeps {
  conversationId: string | null;
  fetchImpl?: typeof fetch;
  removeRecentItem: (id: string, type: string) => void;
  removeStoredConversationId: (key: string) => void;
  resetChat: () => Promise<void> | void;
  onError?: (err: unknown) => void;
  storedConversationKey?: string;
}

export interface DeleteChatConversationResult {
  status: "noop" | "deleted" | "already_gone" | "error";
}

/**
 * Pure handler for the "delete current conversation" action.
 *
 * Behaviour contract (Task #1126):
 * - no `conversationId` → reset chat only (no network call). Idempotent UX:
 *   the recruiter still ends up on a fresh thread.
 * - 2xx → success path: remove sidebar entry + persisted store id + reset chat.
 * - 404 → treated as success (already gone server-side). Same cleanup as 2xx.
 * - 5xx / network error → bubble up via `onError`, do NOT clear UI state so
 *   the user can retry without losing the active thread.
 */
export async function deleteChatConversation({
  conversationId,
  fetchImpl,
  removeRecentItem,
  removeStoredConversationId,
  resetChat,
  onError,
  storedConversationKey = "general",
}: DeleteChatConversationDeps): Promise<DeleteChatConversationResult> {
  if (!conversationId) {
    await resetChat();
    return { status: "noop" };
  }

  const doFetch = fetchImpl ?? fetch;
  try {
    const res = await doFetch(
      `/api/backend-proxy/conversations/${encodeURIComponent(conversationId)}`,
      { method: "DELETE", credentials: "include" },
    );
    if (!res.ok && res.status !== 404) {
      throw new Error(`DELETE conversation failed with status ${res.status}`);
    }
    removeRecentItem(conversationId, "chat");
    removeStoredConversationId(storedConversationKey);
    await resetChat();
    return { status: res.status === 404 ? "already_gone" : "deleted" };
  } catch (err) {
    onError?.(err);
    return { status: "error" };
  }
}

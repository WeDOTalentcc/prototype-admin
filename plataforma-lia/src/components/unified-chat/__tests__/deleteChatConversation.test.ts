import { describe, it, expect, vi } from "vitest";
import { deleteChatConversation } from "../deleteChatConversation";

function makeDeps(overrides: Partial<Parameters<typeof deleteChatConversation>[0]> = {}) {
  return {
    conversationId: "conv-123",
    fetchImpl: vi.fn().mockResolvedValue({ ok: true, status: 200 } as Response),
    removeRecentItem: vi.fn(),
    removeStoredConversationId: vi.fn(),
    resetChat: vi.fn(),
    onError: vi.fn(),
    ...overrides,
  };
}

describe("deleteChatConversation", () => {
  it("resets chat without calling network when conversationId is null (noop)", async () => {
    const deps = makeDeps({ conversationId: null });
    const result = await deleteChatConversation(deps);
    expect(result.status).toBe("noop");
    expect(deps.fetchImpl).not.toHaveBeenCalled();
    expect(deps.resetChat).toHaveBeenCalledTimes(1);
    expect(deps.removeRecentItem).not.toHaveBeenCalled();
    expect(deps.removeStoredConversationId).not.toHaveBeenCalled();
    expect(deps.onError).not.toHaveBeenCalled();
  });

  it("DELETEs against backend-proxy and clears sidebar + chat on 2xx", async () => {
    const deps = makeDeps();
    const result = await deleteChatConversation(deps);
    expect(result.status).toBe("deleted");
    expect(deps.fetchImpl).toHaveBeenCalledWith(
      "/api/backend-proxy/conversations/conv-123",
      { method: "DELETE", credentials: "include" },
    );
    expect(deps.removeRecentItem).toHaveBeenCalledWith("conv-123", "chat");
    expect(deps.removeStoredConversationId).toHaveBeenCalledWith("general");
    expect(deps.resetChat).toHaveBeenCalledTimes(1);
    expect(deps.onError).not.toHaveBeenCalled();
  });

  it("treats 404 as success (idempotent — already gone)", async () => {
    const deps = makeDeps({
      fetchImpl: vi.fn().mockResolvedValue({ ok: false, status: 404 } as Response),
    });
    const result = await deleteChatConversation(deps);
    expect(result.status).toBe("already_gone");
    expect(deps.removeRecentItem).toHaveBeenCalledWith("conv-123", "chat");
    expect(deps.removeStoredConversationId).toHaveBeenCalledWith("general");
    expect(deps.resetChat).toHaveBeenCalledTimes(1);
    expect(deps.onError).not.toHaveBeenCalled();
  });

  it("does not mutate state on 500 and reports error", async () => {
    const deps = makeDeps({
      fetchImpl: vi.fn().mockResolvedValue({ ok: false, status: 500 } as Response),
    });
    const result = await deleteChatConversation(deps);
    expect(result.status).toBe("error");
    expect(deps.removeRecentItem).not.toHaveBeenCalled();
    expect(deps.removeStoredConversationId).not.toHaveBeenCalled();
    expect(deps.resetChat).not.toHaveBeenCalled();
    expect(deps.onError).toHaveBeenCalledTimes(1);
  });

  it("does not mutate state on network failure and reports error", async () => {
    const deps = makeDeps({
      fetchImpl: vi.fn().mockRejectedValue(new Error("network down")),
    });
    const result = await deleteChatConversation(deps);
    expect(result.status).toBe("error");
    expect(deps.removeRecentItem).not.toHaveBeenCalled();
    expect(deps.removeStoredConversationId).not.toHaveBeenCalled();
    expect(deps.resetChat).not.toHaveBeenCalled();
    expect(deps.onError).toHaveBeenCalledTimes(1);
    expect(deps.onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it("URL-encodes the conversation id", async () => {
    const deps = makeDeps({ conversationId: "abc/def?q=1" });
    await deleteChatConversation(deps);
    expect(deps.fetchImpl).toHaveBeenCalledWith(
      "/api/backend-proxy/conversations/abc%2Fdef%3Fq%3D1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

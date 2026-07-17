// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/auth.js";
import { postSse } from "./sse.js";

function streamResponse(chunks) {
  const stream = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      controller.close();
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}

describe("postSse", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.unstubAllGlobals();
    window.history.replaceState({}, "", "/generator/free-image");
  });

  it("parses fragmented events and UTF-8 characters", async () => {
    const encoder = new TextEncoder();
    const raw = encoder.encode(
      'event: delta\ndata: {"content":"你好"}\n\n' +
      'event: delta\ndata: {"content":"世界"}\n\n' +
      "event: done\ndata: {}\n\n",
    );
    const split = raw.indexOf(0xe4) + 1;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamResponse([
      raw.slice(0, split),
      raw.slice(split, split + 7),
      raw.slice(split + 7),
    ])));
    const onChunk = vi.fn();

    await postSse("/image/analyze", { images: [] }, {
      signal: new AbortController().signal,
      onChunk,
    });

    expect(onChunk.mock.calls.map(([content]) => content)).toEqual(["你好", "世界"]);
  });

  it("surfaces JSON business errors before streaming", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ code: 1, message: "操作过于频繁" }),
      { headers: { "Content-Type": "application/json" } },
    )));

    await expect(postSse("/image/analyze", {}, {
      signal: new AbortController().signal,
      onChunk: vi.fn(),
    })).rejects.toMatchObject({ response: { data: { message: "操作过于频繁" } } });
  });

  it("surfaces friendly stream errors", async () => {
    const raw = new TextEncoder().encode(
      'event: delta\ndata: {"content":"部分"}\n\n' +
      'event: error\ndata: {"message":"图片分析失败，请稍后重试"}\n\n',
    );
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamResponse([raw])));

    await expect(postSse("/image/analyze", {}, {
      signal: new AbortController().signal,
      onChunk: vi.fn(),
    })).rejects.toMatchObject({
      response: { data: { message: "图片分析失败，请稍后重试" } },
    });
  });

  it("logs out on unauthorized responses", async () => {
    const auth = useAuthStore();
    auth.login({ email: "user@example.test", token: "expired" });
    window.history.replaceState({}, "", "/login");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: "Unauthorized" }),
      { status: 401, headers: { "Content-Type": "application/json" } },
    )));

    await expect(postSse("/image/analyze", {}, {
      signal: new AbortController().signal,
      onChunk: vi.fn(),
    })).rejects.toBeTruthy();
    expect(auth.isAuthenticated).toBe(false);
  });

  it("passes AbortSignal to fetch", async () => {
    const controller = new AbortController();
    vi.stubGlobal("fetch", vi.fn((_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    })));

    const request = postSse("/image/analyze", {}, { signal: controller.signal, onChunk: vi.fn() });
    controller.abort();
    await expect(request).rejects.toMatchObject({ name: "AbortError" });
  });
});

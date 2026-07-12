// @vitest-environment jsdom

import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/auth.js";
import { handleResponseError } from "./request.js";

describe("request response errors", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.history.replaceState({}, "", "/generator/product-suite/job-1?tab=result");
  });

  it("clears expired authentication and preserves the return path", async () => {
    const auth = useAuthStore();
    auth.login({ email: "user@example.test", token: "expired" });
    const redirect = vi.fn();
    const error = { response: { status: 401 } };

    await expect(handleResponseError(error, redirect)).rejects.toBe(error);

    expect(auth.isAuthenticated).toBe(false);
    expect(redirect).toHaveBeenCalledWith(
      "/login?redirect=%2Fgenerator%2Fproduct-suite%2Fjob-1%3Ftab%3Dresult",
    );
  });

  it("keeps a valid session on forbidden responses", async () => {
    const auth = useAuthStore();
    auth.login({ email: "user@example.test", token: "valid" });
    const redirect = vi.fn();
    const error = { response: { status: 403 } };

    await expect(handleResponseError(error, redirect)).rejects.toBe(error);

    expect(auth.isAuthenticated).toBe(true);
    expect(redirect).not.toHaveBeenCalled();
  });
});

import { describe, expect, it } from "vitest";
import { countVoiceoverCharacters } from "./useVoiceoverGenerator.js";

describe("countVoiceoverCharacters", () => {
  it("ignores spaces, line breaks and tabs", () => {
    expect(countVoiceoverCharacters("你 好\n世界\t")).toBe(4);
  });

  it("counts punctuation and latin characters", () => {
    expect(countVoiceoverCharacters("Hello, world! ")).toBe(12);
  });
});

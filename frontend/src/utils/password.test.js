import { describe, expect, it } from "vitest";
import { validateNewPassword, validatePasswordChange } from "./password.js";

describe("password validation", () => {
  it("validates minimum characters and UTF-8 byte length", () => {
    expect(validateNewPassword("12345", "12345")).toContain("6 个字符");
    expect(validateNewPassword("密码1234", "密码1234")).toBe("");
    expect(validateNewPassword("密".repeat(25), "密".repeat(25))).toContain("72 个字节");
  });

  it("validates confirmation and current password", () => {
    expect(validateNewPassword("123456", "654321")).toContain("不一致");
    expect(validatePasswordChange("", "123456", "123456")).toContain("当前密码");
    expect(validatePasswordChange("123456", "123456", "123456")).toContain("不能与当前密码相同");
  });
});

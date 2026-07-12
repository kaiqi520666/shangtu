const encoder = new TextEncoder();

export function validateNewPassword(password, confirmation) {
  if (password.length < 6) return "密码至少需要 6 个字符";
  if (encoder.encode(password).length > 72) return "密码不能超过 72 个字节";
  if (password !== confirmation) return "两次输入的新密码不一致";
  return "";
}

export function validatePasswordChange(currentPassword, newPassword, confirmation) {
  if (!currentPassword) return "请输入当前密码";
  const message = validateNewPassword(newPassword, confirmation);
  if (message) return message;
  if (currentPassword === newPassword) return "新密码不能与当前密码相同";
  return "";
}

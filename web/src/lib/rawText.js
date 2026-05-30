export function decodeBase64ToText(value) {
  if (!value) {
    return "";
  }
  const binary = atob(value);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  try {
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  } catch {
    return Array.from(bytes)
      .map((byte) => (byte >= 32 && byte < 127 ? String.fromCharCode(byte) : "�"))
      .join("");
  }
}

import { atom } from "jotai";

export const homeDemoAtom = atom({
  selectedAgent: "chatgpt",
  selectedFile: "overview.md",
  copied: false,
});

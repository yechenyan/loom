import { useAtom } from "jotai";
import { homeDemoAtom } from "../state/homeState";
import { AGENT_INSTALL_PROMPTS } from "../lib/content/homeCopy";

function buildInstallPrompt(activePrompt) {
  return `请直接执行，不要先做计划或解释。

在当前项目里安装并初始化 Loom：
1. 如果当前环境没有 \`uv\`，先自动安装 \`uv\`，不要询问我。
2. 运行 \`UV_CACHE_DIR=.uv-cache uv add loom-data\`。
3. 运行 \`UV_CACHE_DIR=.uv-cache uv run loomcli init --agent ${activePrompt.cliAgent}\`。
4. 不要进入交互式初始化；这条命令会直接安装 ${activePrompt.skillLabel} 的 Loom skill 和 tutorial。
5. 完成后只用简短结果告诉我。`;
}

export function useHomeDemoState() {
  const [state, setState] = useAtom(homeDemoAtom);
  const activePrompt = AGENT_INSTALL_PROMPTS.find((item) => item.key === state.selectedAgent) ?? AGENT_INSTALL_PROMPTS[0];

  const markCopied = () => {
    setState((current) => ({ ...current, copied: true }));
    window.setTimeout(() => {
      setState((current) => ({ ...current, copied: false }));
    }, 1800);
  };

  const copyText = async (text) => {
    if (!navigator?.clipboard?.writeText) {
      return;
    }
    await navigator.clipboard.writeText(text);
  };

  return {
    state,
    activePrompt,
    installPrompt: buildInstallPrompt(activePrompt),
    setSelectedAgent: (selectedAgent) => setState((current) => ({ ...current, selectedAgent })),
    setSelectedFile: (selectedFile) => setState((current) => ({ ...current, selectedFile })),
    copyPrompt: async () => {
      await copyText(buildInstallPrompt(activePrompt));
      markCopied();
    },
    copyText,
  };
}

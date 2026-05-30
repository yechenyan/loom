import { MetricCard } from "../shared/Cards";
import { AGENT_INSTALL_PROMPTS } from "../../lib/content/homeCopy";

function ChatSnippet({ role, text, onCopy, code }) {
  const isUser = role === "user";
  return (
    <div className={isUser ? "chat-row chat-row-user" : "chat-row chat-row-assistant"}>
      <div className={isUser ? "chat-avatar chat-avatar-user" : "chat-avatar chat-avatar-assistant"}>
        {isUser ? "U" : "A"}
      </div>
      <div className={isUser ? "chat-bubble chat-user" : "chat-bubble chat-assistant"}>
        <div className="chat-bubble-top">
          <span className="chat-role">{isUser ? "User" : "Agent"}</span>
          {isUser && onCopy ? (
            <button type="button" className="message-copy-button" onClick={onCopy}>
              Copy
            </button>
          ) : null}
        </div>
        <p>{text}</p>
        {code ? (
          <pre className="chat-code-block">
            <code>{code}</code>
          </pre>
        ) : null}
      </div>
    </div>
  );
}

export function HomeHero({
  stats,
  activePrompt,
  installPrompt,
  copied,
  onOpenExplore,
  onSelectAgent,
  onCopyPrompt,
  onCopyText,
}) {
  return (
    <section className="home-hero-shell panel">
      <div className="home-hero-copy">
        <p className="eyebrow">AI Data Workflow</p>
        <h1>把大数据集变成 AI 看得懂、找得到、按需再深入的工作流。</h1>
        <p className="home-hero-lead">
          Loom 先把原始数据扫描成轻量数据卡，让 AI 优先理解结构与主题，只在真的需要时读取原始 CSV。
        </p>
        <div className="hero-cta-row">
          <button className="primary-cta" onClick={onOpenExplore}>查看真实数据卡</button>
          <span className="cta-hint">适合先检索、后取数的 AI 数据分析流程</span>
        </div>
        <div className="hero-stats">
          <MetricCard label="工作区" value={stats.workspaceCount} />
          <MetricCard label="数据集" value={stats.datasetCount} />
          <MetricCard label="CSV 卡片" value={stats.csvProfileCount} />
        </div>
      </div>

      <div className="home-chat-stage">
        <div className="chat-toolbar">
          <div className="agent-tabs" role="tablist" aria-label="AI Agent">
            {AGENT_INSTALL_PROMPTS.map((item) => (
              <button
                key={item.key}
                type="button"
                role="tab"
                aria-selected={item.key === activePrompt.key}
                className={item.key === activePrompt.key ? "agent-tab active" : "agent-tab"}
                onClick={() => onSelectAgent(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <span className="tutorial-toggle">快速初始化会自动安装 tutorial</span>
        </div>
        <div className="chat-window" aria-label={`${activePrompt.assistant} onboarding`}>
          <ChatSnippet role="user" text={installPrompt} onCopy={onCopyPrompt} />
          <ChatSnippet
            role="assistant"
            text={`我会安装 Loom，并运行 loomcli init --agent ${activePrompt.cliAgent}。完成后只汇报结果。`}
          />
          <ChatSnippet role="user" text="loom scan raw_data/cost to cost" onCopy={() => onCopyText("loom scan raw_data/cost to cost")} />
          <ChatSnippet role="assistant" text="我会生成第一版数据卡，再补充整理结果。" />
          <ChatSnippet role="user" text="loom ask OCGT 的成本是多少" onCopy={() => onCopyText("loom ask OCGT 的成本是多少")} />
          <ChatSnippet
            role="assistant"
            text={copied ? "安装提示已复制，你可以直接粘贴给 Agent。" : "我会先查卡片，再决定是否读取原始文件。"}
            code={`import loom\n\npath = loom.get("cost/costs_2040-modifications.csv")\nprint(path)`}
          />
        </div>
      </div>
    </section>
  );
}

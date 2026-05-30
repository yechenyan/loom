import { useState } from "react";
import {
  type AgentTab,
  type PackageTab,
  agentTabs,
  buildInstallConversation,
  packageTabs,
  stepGuides,
} from "./content";

type ChatMessage = ReturnType<typeof buildInstallConversation>[number];
type ChatSection = { key: string; messages: ChatMessage[] };

export function MinuteGuide() {
  const [agent, setAgent] = useState<AgentTab>("Codex");
  const [packageManager, setPackageManager] = useState<PackageTab>("直接安装");
  const [copyStatus, setCopyStatus] = useState<Record<string, "copied" | "error">>({});
  const sections = groupConversation(buildInstallConversation(agent, packageManager));

  async function copyText(key: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus((current) => ({ ...current, [key]: "copied" }));
    } catch {
      setCopyStatus((current) => ({ ...current, [key]: "error" }));
    }

    window.setTimeout(() => {
      setCopyStatus((current) => {
        const next = { ...current };
        delete next[key];
        return next;
      });
    }, 1600);
  }

  return (
    <section className="minute-section" id="minute">
      <div className="section-heading">
        <p className="section-kicker">快速入门</p>
        <h2>直接和 Agent 聊天。</h2>
        <p>不需要手动安装，利用 skill 轻松使用，快速上手。</p>
      </div>
      <div className="minute-workflow">
        <div className="workflow-tabs">
          <div className="tab-stack">
            <SegmentedTabs
              active={packageManager}
              ariaLabel="切换安装环境提示词"
              items={packageTabs}
              onSelect={setPackageManager}
            />
            <SegmentedTabs
              active={agent}
              ariaLabel="切换 agent 提示词"
              items={agentTabs}
              onSelect={setAgent}
            />
          </div>
        </div>
        {stepGuides.map((step, index) => (
          <div className="workflow-row" key={step.title}>
            <StepCard
              copyText={index === 0 ? sections[0]?.messages[0]?.text : undefined}
              onCopy={(text) => copyText("step-install", text)}
              status={copyStatus["step-install"]}
              step={step}
            />
            <div
              className={`chat-stage${index === 0 ? " first" : ""}${
                index === stepGuides.length - 1 ? " last" : ""
              }`}
            >
              {index === 0 ? (
                <div className="chat-top">
                  <span />
                  <span />
                  <span />
                  <strong>
                    {packageManager} · {agent} chat
                  </strong>
                </div>
              ) : null}
              <AgentChat
                messages={sections[index]?.messages || []}
                onCopy={(key, text) => copyText(key, text)}
                statuses={copyStatus}
                stepIndex={index}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function SegmentedTabs<T extends string>({
  active,
  ariaLabel,
  items,
  onSelect,
}: {
  active: T;
  ariaLabel: string;
  items: readonly T[];
  onSelect: (item: T) => void;
}) {
  return (
    <div className="agent-tabs" aria-label={ariaLabel}>
      {items.map((item) => (
        <button
          className={item === active ? "active" : ""}
          key={item}
          onClick={() => onSelect(item)}
          type="button"
        >
          {item}
        </button>
      ))}
    </div>
  );
}

function StepCard({
  copyText,
  onCopy,
  status,
  step,
}: {
  copyText?: string;
  onCopy: (text: string) => void;
  status?: "copied" | "error";
  step: (typeof stepGuides)[number];
}) {
  return (
    <article className="step-card">
      <span>{step.number}</span>
      <div>
        <h3>{step.title}</h3>
        <p>{step.description}</p>
        {copyText ? (
          <button className="step-copy-button" onClick={() => onCopy(copyText)} type="button">
            {status === "copied" ? "已复制" : status === "error" ? "复制失败" : "点击复制提示词"}
          </button>
        ) : null}
      </div>
    </article>
  );
}

function AgentChat({
  messages,
  onCopy,
  statuses,
  stepIndex,
}: {
  messages: ChatMessage[];
  onCopy: (key: string, text: string) => void;
  statuses: Record<string, "copied" | "error">;
  stepIndex: number;
}) {
  return (
    <div className="chat-stream">
      {messages.map((message, index) => (
        <div className="chat-block" key={`${message.role}-${index}`}>
          <article className={`chat-turn ${message.role}`}>
            <div className="avatar">{message.role === "user" ? "你" : "C"}</div>
            <div className="bubble">
              {message.role === "user" ? (
                <CopyButton
                  onClick={() => onCopy(`chat-${stepIndex}-${index}`, message.text)}
                  status={statuses[`chat-${stepIndex}-${index}`]}
                />
              ) : null}
              <p>{message.text}</p>
            </div>
          </article>
        </div>
      ))}
    </div>
  );
}

function groupConversation(conversation: ChatMessage[]): ChatSection[] {
  return conversation.reduce<ChatSection[]>((sections, message) => {
    if (message.heading) {
      sections.push({ key: message.heading, messages: [message] });
      return sections;
    }

    sections[sections.length - 1]?.messages.push(message);
    return sections;
  }, []);
}

function CopyButton({
  onClick,
  status,
}: {
  onClick: () => void;
  status?: "copied" | "error";
}) {
  return (
    <button
      aria-label="复制这条提示词"
      className={`copy-button${status ? ` ${status}` : ""}`}
      onClick={onClick}
      type="button"
    >
      {status === "copied" ? (
        <span>✓</span>
      ) : status === "error" ? (
        <span>!</span>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M8 7a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3v-2a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1H8Z" />
          <path d="M4 11a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-6Zm3-1a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-6a1 1 0 0 0-1-1H7Z" />
        </svg>
      )}
    </button>
  );
}

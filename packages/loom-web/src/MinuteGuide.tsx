import { useState } from "react";
import {
  type AgentTab,
  type PackageTab,
  agentTabs,
  buildInstallConversation,
  getPackageLabel,
  getStepGuides,
  packageTabs,
} from "./content";
import { useI18n } from "./i18n";

type ChatMessage = ReturnType<typeof buildInstallConversation>[number];
type ChatSection = { key: string; messages: ChatMessage[] };

export function MinuteGuide() {
  const { locale } = useI18n();
  const [agent, setAgent] = useState<AgentTab>("Codex");
  const [packageManager, setPackageManager] = useState<PackageTab>("direct");
  const [copyStatus, setCopyStatus] = useState<Record<string, "copied" | "error">>({});
  const stepGuides = getStepGuides(locale);
  const sections = groupConversation(buildInstallConversation(locale, agent, packageManager));
  const copy = {
    en: {
      kicker: "Quick start",
      title: "Talk to your agent directly.",
      body: "No manual setup flow. Use the skill, get started fast.",
      packageAria: "Switch installation prompt",
      agentAria: "Switch agent prompt",
      copied: "Copied",
      copyError: "Copy failed",
      copyPrompt: "Copy prompt",
      copyMessage: "Copy this prompt",
      userAvatar: "You",
      chatSuffix: "chat",
    },
    de: {
      kicker: "Schnellstart",
      title: "Direkt mit dem Agenten sprechen.",
      body: "Kein manueller Setup-Ablauf. Nutze das Skill und starte schnell.",
      packageAria: "Installationsprompt wechseln",
      agentAria: "Agent-Prompt wechseln",
      copied: "Kopiert",
      copyError: "Kopieren fehlgeschlagen",
      copyPrompt: "Prompt kopieren",
      copyMessage: "Diesen Prompt kopieren",
      userAvatar: "Du",
      chatSuffix: "Chat",
    },
    zh: {
      kicker: "快速入门",
      title: "直接和 Agent 聊天。",
      body: "不需要手动安装，利用 skill 轻松使用，快速上手。",
      packageAria: "切换安装环境提示词",
      agentAria: "切换 agent 提示词",
      copied: "已复制",
      copyError: "复制失败",
      copyPrompt: "点击复制提示词",
      copyMessage: "复制这条提示词",
      userAvatar: "你",
      chatSuffix: "chat",
    },
  }[locale];

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
        <p className="section-kicker">{copy.kicker}</p>
        <h2>{copy.title}</h2>
        <p>{copy.body}</p>
      </div>
      <div className="minute-workflow">
        <div className="workflow-tabs">
          <div className="tab-stack">
            <SegmentedTabs
              active={packageManager}
              ariaLabel={copy.packageAria}
              items={packageTabs}
              labelFor={(item) => getPackageLabel(locale, item)}
              onSelect={setPackageManager}
            />
            <SegmentedTabs
              active={agent}
              ariaLabel={copy.agentAria}
              items={agentTabs}
              labelFor={(item) => item}
              onSelect={setAgent}
            />
          </div>
        </div>
        {stepGuides.map((step, index) => (
          <div className="workflow-row" key={step.title}>
            <StepCard
              copy={copy}
              copyText={index === 0 ? sections[0]?.messages[0]?.text : undefined}
              onCopy={(text) => copyText("step-install", text)}
              status={copyStatus["step-install"]}
              step={step}
            />
            <div
              className={`chat-stage${index === 0 ? " first" : ""}${index === stepGuides.length - 1 ? " last" : ""}`}
            >
              {index === 0 ? (
                <div className="chat-top">
                  <span />
                  <span />
                  <span />
                  <strong>
                    {getPackageLabel(locale, packageManager)} · {agent} {copy.chatSuffix}
                  </strong>
                </div>
              ) : null}
              <AgentChat
                copy={copy}
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
  labelFor,
  onSelect,
}: {
  active: T;
  ariaLabel: string;
  items: readonly T[];
  labelFor: (item: T) => string;
  onSelect: (item: T) => void;
}) {
  return (
    <div className="agent-tabs" aria-label={ariaLabel}>
      {items.map((item) => (
        <button className={item === active ? "active" : ""} key={item} onClick={() => onSelect(item)} type="button">
          {labelFor(item)}
        </button>
      ))}
    </div>
  );
}

function StepCard({
  copy,
  copyText,
  onCopy,
  status,
  step,
}: {
  copy: { copied: string; copyError: string; copyPrompt: string };
  copyText?: string;
  onCopy: (text: string) => void;
  status?: "copied" | "error";
  step: ReturnType<typeof getStepGuides>[number];
}) {
  return (
    <article className="step-card">
      <span>{step.number}</span>
      <div>
        <h3>{step.title}</h3>
        <p>{step.description}</p>
        {copyText ? (
          <button className="step-copy-button" onClick={() => onCopy(copyText)} type="button">
            {status === "copied" ? copy.copied : status === "error" ? copy.copyError : copy.copyPrompt}
          </button>
        ) : null}
      </div>
    </article>
  );
}

function AgentChat({
  copy,
  messages,
  onCopy,
  statuses,
  stepIndex,
}: {
  copy: { copyMessage: string; userAvatar: string };
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
            <div className="avatar">{message.role === "user" ? copy.userAvatar : "C"}</div>
            <div className="bubble">
              {message.role === "user" ? (
                <CopyButton
                  ariaLabel={copy.copyMessage}
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
  ariaLabel,
  onClick,
  status,
}: {
  ariaLabel: string;
  onClick: () => void;
  status?: "copied" | "error";
}) {
  return (
    <button aria-label={ariaLabel} className={`copy-button${status ? ` ${status}` : ""}`} onClick={onClick} type="button">
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

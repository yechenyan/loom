import { HOME_FLOW, HOME_OUTPUTS, HOME_USE_CASES } from "../../lib/content/homeCopy";

export function HomeSections() {
  return (
    <>
      <section className="home-story-grid">
        <article className="panel home-problem-card">
          <p className="eyebrow">一眼看懂</p>
          <h2>Loom 是什么</h2>
          <p>Loom 是给 AI 用的数据入口层。它先把大体量原始资料整理成可搜索、可复用的数据卡。</p>
        </article>
        <article className="panel home-problem-card">
          <p className="eyebrow">为什么需要</p>
          <h2>大文件不该成为 AI 的默认起点</h2>
          <p>直接把大 CSV 丢给 AI 很慢也难复用。Loom 把“先理解数据，再打开原文”做成默认流程。</p>
        </article>
      </section>

      <section className="panel home-flow-panel">
        <div className="home-section-head">
          <p className="eyebrow">工作方式</p>
          <h2>先扫描，再检索，最后按需取数</h2>
        </div>
        <div className="home-flow-grid">
          {HOME_FLOW.map((item) => (
            <article key={item.step} className="home-flow-card">
              <span className="home-flow-step">{item.step}</span>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="home-story-grid">
        <article className="panel home-output-card">
          <div className="home-section-head">
            <p className="eyebrow">扫描后会得到什么</p>
            <h2>不是一句摘要，而是一套可继续工作的上下文</h2>
          </div>
          <div className="home-output-list">
            {HOME_OUTPUTS.map((item) => (
              <div key={item.title} className="home-output-item">
                <strong>{item.title}</strong>
                <p>{item.body}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="panel home-use-case-card">
          <div className="home-section-head">
            <p className="eyebrow">适用场景</p>
            <h2>什么时候最有价值</h2>
          </div>
          <div className="home-use-case-list">
            {HOME_USE_CASES.map((item) => (
              <div key={item} className="home-use-case-item">
                <span className="home-use-case-dot" />
                <p>{item}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}

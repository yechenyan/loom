const data = window.GRID_BOTTLENECK_DATA;
const colors = {
  normal: "#2f9e44",
  watch: "#d8a31a",
  tight: "#df6c2d",
  overload: "#c92a2a",
};

function fmt(value) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(value);
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function project([lon, lat], bounds, size) {
  const x = ((lon - bounds.minX) / (bounds.maxX - bounds.minX)) * size.width;
  const y = size.height - ((lat - bounds.minY) / (bounds.maxY - bounds.minY)) * size.height;
  return [x, y];
}

function drawMap(lines) {
  const svg = document.getElementById("grid-map");
  const width = svg.clientWidth || 760;
  const height = svg.clientHeight || 552;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const points = lines.flatMap((line) => [line.from, line.to]);
  const xs = points.map((point) => point[0]);
  const ys = points.map((point) => point[1]);
  const bounds = {
    minX: Math.min(...xs) - 0.6,
    maxX: Math.max(...xs) + 0.6,
    minY: Math.min(...ys) - 0.4,
    maxY: Math.max(...ys) + 0.4,
  };
  svg.innerHTML = "";
  lines.slice().reverse().forEach((line) => {
    const [x1, y1] = project(line.from, bounds, { width, height });
    const [x2, y2] = project(line.to, bounds, { width, height });
    const element = document.createElementNS("http://www.w3.org/2000/svg", "line");
    element.setAttribute("x1", x1);
    element.setAttribute("y1", y1);
    element.setAttribute("x2", x2);
    element.setAttribute("y2", y2);
    element.setAttribute("stroke", colors[line.severity] || colors.normal);
    element.setAttribute("stroke-width", String(Math.max(1.5, line.utilization_pct / 28)));
    element.setAttribute("stroke-linecap", "round");
    element.setAttribute("opacity", line.severity === "normal" ? "0.35" : "0.9");
    element.innerHTML = `<title>Line ${line.id}: ${line.utilization_pct}%</title>`;
    svg.appendChild(element);
  });
}

function renderList(lines) {
  const list = document.getElementById("line-list");
  list.innerHTML = lines.slice(0, 30).map((line, index) => {
    const color = colors[line.severity] || colors.normal;
    const width = Math.min(100, line.utilization_pct);
    return `
      <article class="line-item">
        <strong><span>${index + 1}. Line ${line.id}</span><span>${line.utilization_pct}%</span></strong>
        <div class="bar"><span style="width:${width}%;background:${color}"></span></div>
        <div class="meta">
          ${line.regions.join(" → ")}<br />
          flow ${fmt(Math.abs(line.flow_mw))} MW / cap ${fmt(line.capacity_mw)} MW · ${line.length_km} km
        </div>
      </article>`;
  }).join("");
}

function render() {
  const summary = data.summary;
  setText("timestamp", `模型时间：${summary.model_timestamp_utc}`);
  setText("method", summary.method);
  setText("load", fmt(summary.load_mw));
  setText("generation", fmt(summary.generation_mw));
  setText("overloads", fmt(summary.overloaded_lines));
  setText("watch", fmt(summary.watch_lines));
  drawMap(data.lines);
  renderList(data.lines);
}

render();
window.addEventListener("resize", () => drawMap(data.lines));

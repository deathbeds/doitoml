import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
const html = document.querySelector("html");
const options = { maxTextSize: 100000, logLevel: 99, startOnLoad: false };

let _nextMermaidId = 0;

function update() {
  const theme = html.dataset.theme == "dark" ? "dark" : "default";
  const fontFamily = window
    .getComputedStyle(document.body)
    .getPropertyValue("--pst-font-family-base");
  mermaid.initialize({
    ...options,
    theme,
    fontFamily,
  });

  async function renderOneMarmaid(parent) {
    parent.classList.remove("jp-RenderedMermaid");
    [...parent.querySelectorAll("svg, .jp-mod-warning")].forEach((el) =>
      el.remove()
    );
    const id = `jp-mermaid-${_nextMermaidId++}`;
    let svgText = "";
    let error = "";
    let rawEl = parent.querySelector(".mermaid");
    let raw = rawEl.textContent;
    const el = document.createElement("div");
    el.style.visibility = "hidden";
    document.body.appendChild(el);
    try {
      svgText = (await mermaid.render(id, raw, el)).svg;
    } catch (err) {
      try {
        await mermaid.parse(raw);
      } catch (err) {
        error = `${err}`;
      }
    }
    parent.classList.add("jp-RenderedMermaid");
    if (svgText) {
      const parser = new DOMParser();
      const svg = parser.parseFromString(svgText, "image/svg+xml");
      parent.appendChild(svg.children[0]);
    } else {
      const warn = docuemnt.createElement("details");
      warn.classList.add(".jp-mod-warning");
      warn.innerHTML = `<details>
            <summary>
              <pre><code>${raw}</code></pre>
            </summary>
            <pre><code>${error}</code></pre>
          </details>`;
      parent.appendChild(warn);
    }
  }

  void Promise.all(
    [...document.querySelectorAll(".jp-Mermaid")].map(renderOneMarmaid)
  );
}

export function init() {
  const observer = new MutationObserver(update);
  observer.observe(html, { attributeFilter: ["data-theme"] });
  update();
}

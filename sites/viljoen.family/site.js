// Branches are measured from the rendered cards, so any layout the CSS produces gets a matching tree.
// Stacked cards on narrow screens get a stem down the left gutter instead of a fan.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const tree = document.querySelector(".tree");
  const svg = tree.querySelector("svg.branches");
  const couple = document.getElementById("couple");
  const soil = tree.querySelector(".soil");
  const items = [...tree.querySelectorAll(".gen-b > li")];

  function box(el) {
    const t = tree.getBoundingClientRect(), r = el.getBoundingClientRect();
    return { l: r.left - t.left, r: r.right - t.left, t: r.top - t.top, b: r.bottom - t.top,
             cx: (r.left + r.right) / 2 - t.left, cy: (r.top + r.bottom) / 2 - t.top };
  }

  function bez(p, t) {
    const u = 1 - t;
    return [0, 1].map(i => u*u*u*p[0][i] + 3*u*u*t*p[1][i] + 3*u*t*t*p[2][i] + t*t*t*p[3][i]);
  }
  function tangent(p, t) {
    const u = 1 - t;
    return [0, 1].map(i => 3*u*u*(p[1][i]-p[0][i]) + 6*u*t*(p[2][i]-p[1][i]) + 3*t*t*(p[3][i]-p[2][i]));
  }

  // A cubic Bezier drawn as a filled shape whose width tapers from w0 to w1.
  function limb(p, w0, w1) {
    const left = [], right = [], n = 36;
    for (let i = 0; i <= n; i++) {
      const t = i / n, [x, y] = bez(p, t);
      let [dx, dy] = tangent(p, t);
      const len = Math.hypot(dx, dy) || 1;
      const w = (w0 + (w1 - w0) * t) / 2;
      const nx = -dy / len * w, ny = dx / len * w;
      left.push(`${(x + nx).toFixed(1)},${(y + ny).toFixed(1)}`);
      right.push(`${(x - nx).toFixed(1)},${(y - ny).toFixed(1)}`);
    }
    const el = document.createElementNS(NS, "path");
    el.setAttribute("d", `M${left.join("L")}L${right.reverse().join("L")}Z`);
    el.setAttribute("class", "limb");
    return el;
  }

  // Leaves sprout from a limb at the given positions, alternating sides.
  function leaves(p, ts, size, seed) {
    const g = document.createElementNS(NS, "g");
    ts.forEach((t, i) => {
      const [x, y] = bez(p, t), [dx, dy] = tangent(p, t);
      const side = (i + seed) % 2 ? 1 : -1;
      const ang = Math.atan2(dy, dx) * 180 / Math.PI + side * (50 + (i * 17 + seed * 11) % 25);
      const s = size * (0.8 + ((i * 7 + seed * 5) % 5) / 10);
      const leaf = document.createElementNS(NS, "path");
      leaf.setAttribute("d", `M0,0 C${s*.3},${-s*.32} ${s*.75},${-s*.3} ${s},0 C${s*.75},${s*.3} ${s*.3},${s*.32} 0,0Z M${s*.12},0 L${s*.85},0`);
      leaf.setAttribute("transform", `translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${ang.toFixed(1)})`);
      leaf.setAttribute("class", (i + seed) % 5 === 0 ? "leaf gold" : (i % 2 ? "leaf" : "leaf dark"));
      g.appendChild(leaf);
    });
    return g;
  }

  function draw() {
    const t = tree.getBoundingClientRect();
    svg.setAttribute("width", t.width);
    svg.setAttribute("height", t.height);
    svg.innerHTML = `
      <defs>
        <linearGradient id="barkGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#3a2716"/><stop offset=".45" stop-color="#6e4d30"/><stop offset="1" stop-color="#3a2716"/>
        </linearGradient>
      </defs>
      <style>
        .limb { fill: #5b3f27; stroke: #3a2716; stroke-width: .8; }
        .trunk .limb { fill: url(#barkGrad); }
        .root { fill: #4a3220; }
        .leaf { fill: #6f7d3a; stroke: #4f5a26; stroke-width: .7; }
        .leaf.dark { fill: #58652c; }
        .leaf.gold { fill: #c79a3a; stroke: #8a6420; }
      </style>`;

    const cp = box(couple), so = box(soil);
    const k = items.map(li => ({ c: box(li.querySelector(".child")), line: li.classList.contains("line"),
                                 stub: li.querySelector(".stub") && box(li.querySelector(".stub")) }));
    const stacked = k.length > 1 && k[1].c.t > k[0].c.b - 2;

    [-2, -1, 0, 1, 2, -1.5, 1.5].forEach((j, i) => {
      const main = i < 5, sx = cp.cx + j * 22, sy = cp.b - 8;
      const ex = cp.cx + j * (so.r - so.l) / (main ? 9 : 6), ey = so.t + (so.b - so.t) * (main ? .55 + (i % 2) * .25 : .4);
      const p = [[sx, sy], [sx + j * 4, sy + (ey - sy) * .5], [ex - j * 10, ey - (ey - sy) * .3], [ex, ey]];
      const r = limb(p, main ? 11 - Math.abs(j) * 2 : 4, 1.2);
      r.setAttribute("class", "limb root");
      svg.appendChild(r);
    });

    if (!stacked) {
      const kb = Math.max(...k.map(x => x.c.b)), gap = cp.t - kb, forkY = cp.t - gap * .32;
      const trunk = document.createElementNS(NS, "g");
      trunk.setAttribute("class", "trunk");
      const tp = [[cp.cx, cp.t + 8], [cp.cx + 6, cp.t - gap * .12], [cp.cx - 6, forkY + gap * .1], [cp.cx, forkY]];
      trunk.appendChild(limb(tp, 30, 24));
      svg.appendChild(trunk);
      k.forEach((x, i) => {
        const sx = cp.cx + (i - (k.length - 1) / 2) * 7, sy = forkY + 6;
        const ex = x.c.cx, ey = x.c.b - 4, dy = sy - ey;
        const p = [[sx, sy], [sx, sy - dy * .55], [ex, ey + dy * .6], [ex, ey]];
        svg.appendChild(limb(p, x.line ? 17 : 11, x.line ? 8 : 4));
        svg.appendChild(leaves(p, [.4, .55, .7, .84], 14, i));
        if (x.stub) {
          const q = [[x.c.cx, x.c.t + 4], [x.c.cx, x.c.t - 20], [x.stub.cx, x.stub.b + 20], [x.stub.cx, x.stub.b - 2]];
          svg.appendChild(limb(q, 8, 4));
          svg.appendChild(leaves(q, [.35, .7], 12, i + 1));
        }
      });
    } else {
      const gx = k[0].c.l - 24, top = k[0].c.cy;
      const trunk = document.createElementNS(NS, "g");
      trunk.setAttribute("class", "trunk");
      const tp = [[gx, cp.t + 10], [gx - 5, cp.t - (cp.t - top) * .35], [gx + 5, cp.t - (cp.t - top) * .7], [gx, top]];
      trunk.appendChild(limb(tp, 18, 7));
      svg.appendChild(trunk);
      svg.appendChild(leaves(tp, [.15, .5], 14, 2));
      k.forEach((x, i) => {
        const sy = x.c.cy + 16;
        const p = [[gx, sy], [gx + 10, sy - 4], [x.c.l - 12, x.c.cy], [x.c.l + 2, x.c.cy]];
        svg.appendChild(limb(p, x.line ? 9 : 6, x.line ? 5 : 3));
        svg.appendChild(leaves(p, [.45], 11, i));
      });
    }
  }

  let queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; draw(); });
  }
  addEventListener("resize", schedule);
  addEventListener("load", schedule);
  if (document.fonts) document.fonts.ready.then(schedule);
  if ("ResizeObserver" in window) new ResizeObserver(schedule).observe(tree);
  schedule();
})();

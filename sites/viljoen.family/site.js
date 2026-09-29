// Branches are measured from the rendered cards, so any layout the CSS produces gets a matching tree.
// Stacked cards on narrow screens get a stem down the left gutter instead of a fan.
(function () {
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
  // The point on a curve that climbs steadily upward, at height y.
  function atY(p, y) {
    let lo = 0, hi = 1;
    for (let i = 0; i < 24; i++) {
      const mid = (lo + hi) / 2;
      if (bez(p, mid)[1] > y) lo = mid; else hi = mid;
    }
    return bez(p, lo);
  }

  // A cubic Bezier outlined as a closed shape whose width tapers from w0 to w1, as path data.
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
    return `M${left.join("L")}L${right.reverse().join("L")}Z`;
  }

  // Leaves sprout from a limb at the given positions, alternating sides.
  function leaves(p, ts, size, seed) {
    return ts.map((t, i) => {
      const [x, y] = bez(p, t), [dx, dy] = tangent(p, t);
      const side = (i + seed) % 2 ? 1 : -1;
      const ang = Math.atan2(dy, dx) * 180 / Math.PI + side * (50 + (i * 17 + seed * 11) % 25);
      const s = size * (0.8 + ((i * 7 + seed * 5) % 5) / 10);
      const cls = (i + seed) % 5 === 0 ? "leaf gold" : (i % 2 ? "leaf" : "leaf dark");
      return `<path class="${cls}" d="M0,0 C${s*.3},${-s*.32} ${s*.75},${-s*.3} ${s},0 C${s*.75},${s*.3} ${s*.3},${s*.32} 0,0Z M${s*.12},0 L${s*.85},0"` +
             ` transform="translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${ang.toFixed(1)})"/>`;
    }).join("");
  }

  function draw() {
    const t = tree.getBoundingClientRect();
    // Tree sizes are set for a 16px root and scale with it, as the cards and text do.
    const s = parseFloat(getComputedStyle(document.documentElement).fontSize) / 16 || 1;
    const cp = box(couple), so = box(soil);
    const k = items.map(li => ({ c: box(li.querySelector(".child")), line: li.classList.contains("line"),
                                 stub: li.querySelector(".stub") && box(li.querySelector(".stub")) }));
    const stacked = k.length > 1 && k[1].c.t > k[0].c.b - 2;
    const roots = [], branches = [];
    let trunk, sprigs = "";

    // Roots start straight down within the wide trunk's base width, so there they leave the couple card as the trunk continued.
    [-2, -1, 0, 1, 2, -1.5, 1.5].forEach((j, i) => {
      const main = i < 5, w0 = (main ? 11 - Math.abs(j) * 2 : 4) * s;
      const sx = cp.cx + j / 4 * (30 * s - w0), sy = cp.b - 8 * s;
      const ex = cp.cx + j * (so.r - so.l) / (main ? 9 : 6), ey = so.t + (so.b - so.t) * (main ? .55 + (i % 2) * .25 : .4);
      const p = [[sx, sy], [sx, sy + (ey - sy) * .5], [ex - j * 10 * s, ey - (ey - sy) * .3], [ex, ey]];
      roots.push(limb(p, w0, 1.2 * s));
    });

    if (!stacked) {
      const kb = Math.max(...k.map(x => x.c.b)), gap = cp.t - kb, forkY = cp.t - gap * .32, top = 24 * s;
      // The trunk ends straight up, so the limbs can rise out of its top along the same line.
      const tp = [[cp.cx, cp.t + 8 * s], [cp.cx + 7 * s, cp.t - gap * .12], [cp.cx, forkY + gap * .12], [cp.cx, forkY]];
      trunk = limb(tp, 30 * s, top);
      k.forEach((x, i) => {
        const w0 = (x.line ? 17 : 11) * s, w1 = (x.line ? 8 : 4) * s;
        // Limb starts spread across the trunk's top inside its sides, the outer two flush with them.
        const sx = cp.cx + (k.length > 1 ? i / (k.length - 1) - .5 : 0) * (top - w0), sy = forkY + 10 * s;
        const ex = x.c.cx, ey = x.c.b - 4 * s, dy = sy - ey;
        const p = [[sx, sy], [sx, sy - dy * .55], [ex, ey + dy * .6], [ex, ey]];
        branches.push(limb(p, w0, w1));
        sprigs += leaves(p, [.4, .55, .7, .84], 14 * s, i);
        if (x.stub) {
          const q = [[x.c.cx, x.c.t + 4 * s], [x.c.cx, x.c.t - 20 * s], [x.stub.cx, x.stub.b + 20 * s], [x.stub.cx, x.stub.b - 2 * s]];
          branches.push(limb(q, 8 * s, 4 * s));
          sprigs += leaves(q, [.35, .7], 12 * s, i + 1);
        }
      });
    } else {
      const gx = k[0].c.l - 24 * s, top = k[0].c.cy;
      const tp = [[gx, cp.t + 10 * s], [gx - 5 * s, cp.t - (cp.t - top) * .35], [gx + 5 * s, cp.t - (cp.t - top) * .7], [gx, top]];
      trunk = limb(tp, 18 * s, 7 * s);
      sprigs += leaves(tp, [.15, .5], 14 * s, 2);
      k.forEach((x, i) => {
        // Each twig starts on the stem's center line, so its base stays inside the stem where the stem bends.
        const [sx, sy] = atY(tp, x.c.cy + 16 * s);
        const p = [[sx, sy], [sx + 10 * s, sy - 4 * s], [x.c.l - 12 * s, x.c.cy], [x.c.l + 2 * s, x.c.cy]];
        branches.push(limb(p, (x.line ? 9 : 6) * s, (x.line ? 5 : 3) * s));
        sprigs += leaves(p, [.45], 11 * s, i);
      });
    }

    // All the wood is outlined first and filled on top, so overlapping pieces read as one shape with no seams.
    // The trunk's bark shading then fades out under the branch bases, so each branch grows out of it.
    const W = t.width, H = t.height, all = `x="${-W}" y="${-H}" width="${3 * W}" height="${3 * H}"`;
    const wood = [trunk, ...branches];
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.innerHTML = `
      <defs>
        <linearGradient id="barkGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#3a2716"/><stop offset=".45" stop-color="#6e4d30"/><stop offset="1" stop-color="#3a2716"/>
        </linearGradient>
        <filter id="soften" filterUnits="userSpaceOnUse" ${all}><feGaussianBlur stdDeviation="${(3 * s).toFixed(1)}"/></filter>
        <mask id="barkFade" maskUnits="userSpaceOnUse" ${all}>
          <rect ${all} fill="white"/>
          <g fill="black" stroke="black" stroke-width="${(6 * s).toFixed(1)}" filter="url(#soften)">${branches.map(d => `<path d="${d}"/>`).join("")}</g>
        </mask>
      </defs>
      <style>
        .edge { fill: #3a2716; stroke: #3a2716; stroke-width: 1.6; stroke-linejoin: round; }
        .wood { fill: #5b3f27; }
        .root { fill: #4a3220; }
        .bark { fill: url(#barkGrad); }
        .leaf { fill: #6f7d3a; stroke: #4f5a26; stroke-width: .7; }
        .leaf.dark { fill: #58652c; }
        .leaf.gold { fill: #c79a3a; stroke: #8a6420; }
      </style>
      ${[...roots, ...wood].map(d => `<path class="edge" d="${d}"/>`).join("")}
      ${roots.map(d => `<path class="root" d="${d}"/>`).join("")}
      ${wood.map(d => `<path class="wood" d="${d}"/>`).join("")}
      <path class="bark" d="${trunk}" mask="url(#barkFade)"/>
      ${sprigs}`;
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

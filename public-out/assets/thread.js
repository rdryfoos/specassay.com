/* ── The Golden Thread, made interactive ──────────────────────────────
   Grab any node (top = executive intent, bottom = ground-truth source) and
   drag it: the whole thread re-forms through the three live positions and
   springs into rest. Bidirectional traceability you can feel — change enters
   anywhere, the thread stays connected. Hover shivers it; release lets it twang.
   Geometry mirrors the Loupe app (packages/viz/web/src/main.ts: braidStrand).

   Load this after the .braid SVG exists in the DOM (end of <body>, or wrap in
   DOMContentLoaded). No dependencies.

   Tuning knobs:
     SAG    bow of each segment          SEP     strand separation
     nodes  resting positions            s=1.7   pluck strength (onUp)
     0.955  reverb decay (frame)         segWobble()  shiver/twang shape
------------------------------------------------------------------------ */
(function () {
    const svg = document.querySelector('.braid');
    if (!svg) return;
    const strandA = svg.querySelector('.strand-a');
    const strandB = svg.querySelector('.strand-b');
    const hit = svg.querySelector('.hit');
    const nodeEls = [...svg.querySelectorAll('.node')];
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const W = 180, H = 400, PAD = 20;   // must match the viewBox; PAD keeps nodes off the edge
    const SAG = 11;                     // one gentle bow per segment (app THREAD_SAG)
    const SEP = 6.5;                    // half-separation between strands (app uses 3.6; widened
                                        // here so the two strands read as two at this smaller size)

    // three live node positions (user units); the thread is defined by these
    const nodes = [
        { x: 92, y: 48 },
        { x: 92, y: 200 },
        { x: 92, y: 352 }
    ];

    let dragging = null, hoverCount = 0;
    let h = 0, s = 0;                   // hover / settle (spring) energies
    let raf = null, t0 = null, T = 0;

    // Per-segment sideways sway. Nodes are the fixed cubic endpoints, so this
    // only bends the cable between them — a node is never moved or bypassed.
    // Adjacent segments sway in opposition, so a release ripples like a wave.
    function segWobble(i) {
        const ph = i * Math.PI;
        return 1.2 * h * Math.sin(T * 19 + ph) + 15 * s * Math.sin(T * 15.5 + ph);
    }

    // One strand across one segment: a single cubic that bows to one side and
    // offsets by ±SEP so the pair crosses exactly once — a twisted cable, not
    // a helix. Returns the "C ..." continuation (the M is emitted once up top).
    function cubic(A, B, sepSign, wob) {
        const dx = B.x - A.x, dy = B.y - A.y;
        const L = Math.hypot(dx, dy) || 1;
        const nx = -dy / L, ny = dx / L;        // left-perpendicular of the descent
        const bow = SAG + wob;
        const o1 = bow + SEP * sepSign;
        const o2 = bow - SEP * sepSign;
        const c1x = A.x + dx * 0.33 + nx * o1, c1y = A.y + dy * 0.33 + ny * o1;
        const c2x = A.x + dx * 0.67 + nx * o2, c2y = A.y + dy * 0.67 + ny * o2;
        return 'C ' + c1x.toFixed(2) + ' ' + c1y.toFixed(2) + ' '
                    + c2x.toFixed(2) + ' ' + c2y.toFixed(2) + ' '
                    + B.x.toFixed(2) + ' ' + B.y.toFixed(2);
    }

    function strandPath(sepSign) {
        let out = 'M ' + nodes[0].x.toFixed(2) + ' ' + nodes[0].y.toFixed(2);
        for (let i = 0; i < nodes.length - 1; i++) {
            out += ' ' + cubic(nodes[i], nodes[i + 1], sepSign, segWobble(i));
        }
        return out;
    }

    function updateNodes() {
        nodeEls.forEach((el, i) => {
            el.setAttribute('cx', nodes[i].x.toFixed(2));
            el.setAttribute('cy', nodes[i].y.toFixed(2));
        });
    }

    function render() {
        strandA.setAttribute('d', strandPath(1));
        strandB.setAttribute('d', strandPath(-1));
        hit.setAttribute('d', strandPath(0));   // centerline, for hover
    }

    function frame(ts) {
        if (t0 == null) t0 = ts;
        T = (ts - t0) / 1000;
        const hTarget = (hoverCount > 0 && dragging == null) ? 1 : 0;
        h += (hTarget - h) * 0.15;
        s = s > 0.0006 ? s * 0.955 : 0;   // slow decay => a long, ringing reverb
        render();
        const alive = h > 0.002 || s > 0.002 || dragging != null || hoverCount > 0;
        if (alive) { raf = requestAnimationFrame(frame); }
        else { raf = null; h = s = 0; render(); }   // land on a clean rest
    }
    function kick() {
        if (reduce) { render(); return; }
        if (!raf) { t0 = null; raf = requestAnimationFrame(frame); }
    }

    // client coords → SVG user units
    function toUser(e) {
        const pt = svg.createSVGPoint();
        pt.x = e.clientX; pt.y = e.clientY;
        const q = pt.matrixTransform(svg.getScreenCTM().inverse());
        return { x: q.x, y: q.y };
    }
    const clamp = p => ({
        x: Math.max(PAD, Math.min(W - PAD, p.x)),
        y: Math.max(PAD, Math.min(H - PAD, p.y))
    });

    function onMove(e) {
        if (dragging == null) return;
        e.preventDefault();
        nodes[dragging] = clamp(toUser(e));
        updateNodes();
        if (reduce) render(); else kick();
    }
    function onUp() {
        if (dragging == null) return;
        nodeEls[dragging].classList.remove('grabbing');
        svg.classList.remove('dragging');
        dragging = null;
        if (!reduce) s = Math.max(s, 1.7);   // a big pluck, then it rings out
        document.removeEventListener('pointermove', onMove);
        document.removeEventListener('pointerup', onUp);
        kick();
    }

    nodeEls.forEach((el, i) => {
        el.addEventListener('pointerdown', e => {
            e.preventDefault();
            dragging = i;
            el.classList.add('grabbing');
            svg.classList.add('dragging', 'touched');
            document.addEventListener('pointermove', onMove);
            document.addEventListener('pointerup', onUp);
            kick();
        });
        el.addEventListener('pointerenter', () => { hoverCount++; kick(); });
        el.addEventListener('pointerleave', () => { hoverCount = Math.max(0, hoverCount - 1); kick(); });
    });
    hit.addEventListener('pointerenter', () => { hoverCount++; svg.classList.add('touched'); kick(); });
    hit.addEventListener('pointerleave', () => { hoverCount = Math.max(0, hoverCount - 1); kick(); });

    updateNodes();
    render();   // draw the resting cable
})();

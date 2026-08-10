#!/usr/bin/env python3
"""Build the specassay.com static site into public-out/.

- Homepage: src/index.html -> /index.html
- Field guide: src/field-guide.md rendered to /field-guide/index.html, wrapped in
  the shared shell, with src/images/ copied to /field-guide/images/.

Zero external dependencies. Re-run after editing src/field-guide.md so the served
page matches the source; commit public-out/ (Vercel serves it statically).
"""
from __future__ import annotations
import html, posixpath, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT = ROOT / "public-out"
# The field guide's relative links point at docs in the methodology repo.
GH = "https://github.com/rdryfoos/specassay/blob/main"


def resolve_href(u: str) -> str:
    if u.startswith(("http://", "https://", "#", "mailto:", "/")) or u.startswith("images/"):
        return u
    return f"{GH}/{posixpath.normpath(posixpath.join('docs', u))}"


# ---- shared chrome (rev 4): family switcher above a vignette hairline, this
# site's own nav below, a per-site tag on the right. Same on every page; only the
# current-page highlight changes.
FAMILY_HTML = (
    '<a href="https://dryfoos.com/">Dryfoos</a>'
    '<a class="here" href="/">SpecAssay</a>'
    '<a href="https://loupe.dryfoos.com/">Loupe</a>'
)
SITE_PAGES = [("home", "SpecAssay", "/"),
              ("field-guide", "Field Guide", "/field-guide"),
              ("thread-report", "Thread Report", "/thread-report")]


def header(current: str = "home") -> str:
    items = []
    for key, label, href in SITE_PAGES:
        cls = ' class="here"' if key == current else ''
        items.append(f'<a{cls} href="{href}">{label}</a>')
    nav = "".join(items)
    return f"""  <header class="site-header">
    <div class="row top">
      <div class="brand"><a href="/">SpecAssay</a> <span class="of">hallmark the work</span></div>
      <nav class="family">{FAMILY_HTML}</nav>
    </div>
    <hr class="rule">
    <div class="row bot">
      <nav class="sitenav">{nav}</nav>
      <div class="slot">A <a class="ext" href="https://github.com/github/spec-kit" target="_blank" rel="noopener">Spec Kit</a> Extension Bundle</div>
    </div>
  </header>"""


FOOTER = f"""  <footer class="site-footer">
    <hr class="rule rev">
    <div class="frow">
      <div>
        <div class="fbrand"><a href="/">SpecAssay</a> <span class="of">hallmark the work</span></div>
        <div class="fcol">A <a class="ext" href="https://github.com/github/spec-kit" target="_blank" rel="noopener">Spec Kit</a> extension bundle — the thread lives in the repo.<br>Part of the <span class="fam">Dryfoos</span> family.</div>
      </div>
      <div class="fright">
        <nav class="family">{FAMILY_HTML}</nav>
        <div class="flinks"><a href="https://github.com/rdryfoos/specassay" target="_blank" rel="noopener">GitHub ↗</a><a href="/field-guide">Field Guide</a><a href="/thread-report">Thread Report</a></div>
        <div class="fmeta">© 2026 · dryfoos.com</div>
      </div>
    </div>
  </footer>"""


def inline(t: str) -> str:
    codes: list[str] = []
    t = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes)-1}\x00", t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{resolve_href(m.group(2))}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + html.escape(codes[int(m.group(1))], quote=False) + "</code>", t)
    return t


def render_md(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para).strip()) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            flush_para(); i += 1; buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf), quote=False) + "</code></pre>")
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if m:
            flush_para()
            src = m.group(2)
            # Absolute so it resolves under /field-guide even without a trailing
            # slash (cleanUrls serves the page at /field-guide, not /field-guide/).
            if not src.startswith(("http://", "https://", "/")):
                src = "/field-guide/" + src.lstrip("./")
            out.append(f'<img src="{src}" alt="{html.escape(m.group(1), quote=True)}">')
            i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para(); lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2).strip())}</h{lvl}>")
            i += 1; continue
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            flush_para()
            def cells(row: str) -> list[str]:
                row = row.strip()
                if row.startswith("|"): row = row[1:]
                if row.endswith("|"): row = row[:-1]
                return [c.strip() for c in row.split("|")]
            header = cells(line); i += 2; body = []
            while i < n and lines[i].lstrip().startswith("|"):
                body.append(cells(lines[i])); i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")
            continue
        if re.match(r"^\s*---+\s*$", line):
            flush_para(); out.append("<hr>"); i += 1; continue
        if re.match(r"^\s*[-*]\s+", line):
            flush_para(); items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            flush_para(); items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if line.lstrip().startswith(">"):
            flush_para(); buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append("<blockquote>" + inline(" ".join(buf).strip()) + "</blockquote>")
            continue
        if not line.strip():
            flush_para(); i += 1; continue
        para.append(line); i += 1
    flush_para()
    return "\n".join(out)


def page(title: str, desc: str, body: str, current: str = "field-guide") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<div class="wrap">
{header(current)}
{body}
{FOOTER}
</div>
</body>
</html>
"""


def emit_page(src_name: str, out_path, current: str) -> None:
    """Copy a hand-authored page, injecting the shared header/footer at the
    <!--HEADER--> / <!--FOOTER--> placeholders."""
    txt = (SRC / src_name).read_text(encoding="utf-8")
    txt = txt.replace("<!--HEADER-->", header(current)).replace("<!--FOOTER-->", FOOTER)
    out_path.write_text(txt, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    emit_page("index.html", OUT / "index.html", "home")
    shutil.copytree(SRC / "assets", OUT / "assets")

    # Thread Report walkthrough (hand-authored page → /thread-report/)
    tr = OUT / "thread-report"
    tr.mkdir()
    emit_page("thread-report.html", tr / "index.html", "thread-report")

    md = (SRC / "field-guide.md").read_text(encoding="utf-8")
    # Lift the first "# Heading" into a hero-style title, matching the Thread
    # Report page (gold eyebrow + big blue h1); the rest renders as the doc body.
    lines = md.split("\n")
    title, rest = "Field guide", md
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            title = ln[2:].strip()
            rest = "\n".join(lines[i + 1:])
            break
    body = (
        '<div class="hero" style="padding-bottom:20px">\n'
        '<p class="eyebrow">SpecAssay field guide</p>\n'
        f'<h1><span class="lo">{html.escape(title, quote=False)}</span></h1>\n'
        '</div>\n'
        '<article class="doc" style="padding-top:8px">\n'
        f"{render_md(rest)}\n"
        '<a class="doc-back" href="/">← Back to SpecAssay</a>\n'
        "</article>"
    )
    fg = OUT / "field-guide"
    fg.mkdir()
    (fg / "index.html").write_text(
        page("Field guide — SpecAssay", "A visual tour of SpecAssay, the trace-manifest, and Loupe — one screenshot at a time.", body),
        encoding="utf-8",
    )
    shutil.copytree(SRC / "images", fg / "images")

    print(f"built specassay.com -> {OUT}")
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(OUT))


if __name__ == "__main__":
    main()

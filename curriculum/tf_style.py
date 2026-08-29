"""Shared page shell for the Terraform track HTML.

Single source of visual truth. Generators import from here and never re-declare CSS,
so every Terraform page is guaranteed to look identical.

Read-only for generators: add helpers here, but do not fork the palette.
"""

PALETTE = {
    "blue": "#2563eb",
    "cyan": "#06b6d4",
    "slate900": "#0f172a",
    "slate700": "#334155",
    "slate500": "#64748b",
    "slate200": "#e2e8f0",
    "bg": "#f8fafc",
    "green": "#16a34a",
    "amber": "#d97706",
    "rose": "#e11d48",
}

BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
    --blue: #2563eb; --cyan: #06b6d4;
    --slate-900: #0f172a; --slate-700: #334155; --slate-500: #64748b; --slate-200: #e2e8f0;
    --bg: #f8fafc; --green: #16a34a; --amber: #d97706; --rose: #e11d48;
}
body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
    color: var(--slate-900); padding: 20px; line-height: 1.6;
}
.container { max-width: 1380px; margin: 0 auto; }
header {
    margin-bottom: 22px; padding: 18px 24px; border-radius: 14px; background: #fff;
    border: 1px solid rgba(37, 99, 235, 0.10);
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06); text-align: center;
}
h1 { font-size: 1.6rem; color: var(--blue); margin-bottom: 4px; }
.subtitle { color: var(--slate-500); font-size: 0.92rem; }
.backlink { color: var(--blue); font-weight: 700; text-decoration: none; }
.backlink:hover { text-decoration: underline; }
.stats { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
         margin-top: 12px; font-size: 0.82rem; color: var(--slate-700); }
.stats span { padding: 4px 10px; background: #eff6ff; border-radius: 999px; }

/* tier nav */
.tiernav { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 14px; }
.tiernav a {
    padding: 6px 14px; border-radius: 999px; text-decoration: none; font-size: 0.84rem;
    font-weight: 700; color: var(--blue); background: #eff6ff;
    border: 1px solid rgba(37,99,235,0.18);
}
.tiernav a.active { background: var(--blue); color: #fff; }

/* cards */
.card {
    background: #fff; border: 1px solid var(--slate-200); border-radius: 14px;
    padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}
.card h2 { font-size: 1.18rem; color: var(--slate-900); margin-bottom: 4px; }
.card h3 { font-size: 0.98rem; color: var(--slate-700); margin: 14px 0 6px; }
.concept { color: var(--slate-700); font-size: 0.94rem; margin-bottom: 12px; }
.eyebrow {
    display: inline-block; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.05em;
    text-transform: uppercase; color: var(--cyan); margin-bottom: 6px;
}

/* code */
pre {
    background: var(--slate-900); color: #e2e8f0; padding: 14px 16px; border-radius: 10px;
    overflow-x: auto; font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.82rem; line-height: 1.55; margin: 8px 0 12px;
}
pre.output { background: #0b1220; color: #86efac; }
code.inline {
    background: #eff6ff; color: #1d4ed8; padding: 1px 6px; border-radius: 5px;
    font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.86em;
}

/* explanation + generic tables */
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; }
th, td { padding: 9px 12px; text-align: left; vertical-align: top;
         border-bottom: 1px solid var(--slate-200); font-size: 0.88rem; }
th { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.04em;
     color: var(--slate-500); background: rgba(248, 250, 252, 0.9); }
tr:last-child td { border-bottom: none; }
td.lineref { white-space: nowrap; font-family: "SF Mono", Menlo, monospace;
             font-size: 0.8rem; color: var(--blue); font-weight: 700; }

/* tags */
.tag { display: inline-block; padding: 3px 9px; border-radius: 999px;
       font-size: 0.68rem; font-weight: 800; letter-spacing: 0.03em; }
.tag.basic { background: #dbeafe; color: #1d4ed8; }
.tag.intermediate { background: #dcfce7; color: #166534; }
.tag.advanced { background: #fef3c7; color: #92400e; }
.tag.aws { background: #ffe4e6; color: #be123c; }

/* callouts */
.note, .warn {
    border-left: 3px solid var(--blue); background: #f8fbff; padding: 10px 14px;
    border-radius: 0 8px 8px 0; font-size: 0.88rem; margin: 10px 0;
}
.warn { border-left-color: var(--amber); background: #fffbeb; }

/* lab link */
.lablink {
    display: inline-block; margin-top: 6px; font-size: 0.82rem; font-weight: 700;
    color: var(--blue); text-decoration: none;
}
.lablink:hover { text-decoration: underline; }

/* diagram */
.diagram { background: #fff; border: 1px solid var(--slate-200); border-radius: 14px;
           padding: 16px; margin: 14px 0; overflow-x: auto; }
.diagram svg { width: 100%; height: auto; display: block; }

.footer { margin-top: 24px; text-align: center; color: var(--slate-500);
          font-size: 0.84rem; padding-bottom: 12px; }

@media (max-width: 1200px) { .container { max-width: 100%; } }
@media (max-width: 768px) {
    body { padding: 12px; }
    h1 { font-size: 1.3rem; }
    pre { font-size: 0.76rem; }
}
"""

# terraform/html/<page>.html -> repo root is two levels up
ROOT_INDEX = "../../index.html"


def page(title: str, subtitle: str, body: str, *, active: str = "", stats=None,
         extra_css: str = "") -> str:
    """Wrap body HTML in the shared shell. Returns a complete self-contained document."""
    nav_items = [
        ("index.html", "Track Home", "index"),
        ("terraform-101.html", "Terraform 101", "tf101"),
        ("aws-primer.html", "AWS Primer", "primer"),
        ("basic.html", "Basic", "basic"),
        ("intermediate.html", "Intermediate", "intermediate"),
        ("advanced.html", "Advanced", "advanced"),
    ]
    nav = "\n".join(
        f'            <a href="./{href}"{" class=\"active\"" if key == active else ""}>{label}</a>'
        for href, label, key in nav_items
    )
    stat_html = ""
    if stats:
        spans = "".join(f"<span>{s}</span>" for s in stats)
        stat_html = f'\n            <div class="stats">{spans}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{BASE_CSS}{extra_css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
            <p class="subtitle" style="margin-top:8px;">
                <a class="backlink" href="{ROOT_INDEX}">&larr; All tracks catalog</a>
            </p>{stat_html}
            <nav class="tiernav">
{nav}
            </nav>
        </header>

{body}

        <div class="footer">
            Terraform track &middot; <a class="backlink" href="{ROOT_INDEX}">All tracks</a>
        </div>
    </div>
</body>
</html>
"""


def topic(eyebrow: str, heading: str, concept: str, code: str, explain_rows,
          lab_href: str = "", lab_label: str = "", *, lang_note: str = "") -> str:
    """One topic section: concept overview -> example code -> line-by-line -> lab link.

    explain_rows: iterable of (line_or_token, meaning) pairs.
    """
    rows = "\n".join(
        f"                <tr><td class=\"lineref\">{ref}</td><td>{meaning}</td></tr>"
        for ref, meaning in explain_rows
    )
    note = f'\n            <div class="note">{lang_note}</div>' if lang_note else ""
    lab = (f'\n            <a class="lablink" href="{lab_href}">Practise it in {lab_label} &rarr;</a>'
           if lab_href else "")
    return f"""        <div class="card">
            <span class="eyebrow">{eyebrow}</span>
            <h2>{heading}</h2>
            <p class="concept">{concept}</p>
            <h3>Example</h3>
<pre>{code}</pre>
            <h3>Line by line</h3>
            <table>
                <thead><tr><th style="width:30%;">Line</th><th>What it does</th></tr></thead>
                <tbody>
{rows}
                </tbody>
            </table>{note}{lab}
        </div>
"""


def esc(text: str) -> str:
    """Escape HCL/shell for embedding in <pre>."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

"""Shared HTML fragment builders for curriculum generators."""
from __future__ import annotations


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cards_html(cards: list[tuple[str, str]]) -> str:
    parts = ['<div class="concept-grid">']
    for badge, body in cards:
        parts.append(
            f'                <article class="card">\n'
            f'                    <div class="card-badge">{badge}</div>\n'
            f'                    <p>{body}</p>\n'
            f'                </article>'
        )
    parts.append("            </div>")
    return "\n".join(parts)


def flow_html(steps: list[tuple[str, str]]) -> str:
    parts = ['<div class="flow-track">']
    for i, (title, body) in enumerate(steps, 1):
        parts.append(
            f'                <div class="flow-step">\n'
            f'                    <div class="step-number">{i}</div>\n'
            f'                    <h3>{title}</h3>\n'
            f'                    <p>{body}</p>\n'
            f'                </div>'
        )
    parts.append("            </div>")
    return "\n".join(parts)


def examples_html(examples: list[tuple[str, str]], lab: str | None = None) -> str:
    parts = ['<div class="example-stack">']
    if lab:
        parts.append(
            f'            <div class="lab-callout"><strong>Repo lab files:</strong> {lab}</div>'
        )
    for kicker, code in examples:
        parts.append(
            f'                <section class="example-card">\n'
            f'                    <div class="section-kicker">{kicker}</div>\n'
            f'                    <pre><code>{esc(code)}</code></pre>\n'
            f'                </section>'
        )
    parts.append("            </div>")
    return "\n".join(parts)


def table_html(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{c}</td>" for c in row)
        body_rows.append(f"                        <tr>{cells}</tr>")
    return f"""            <div class="table-wrap">
                <table>
                    <thead><tr>{head}</tr></thead>
                    <tbody>
{chr(10).join(body_rows)}
                    </tbody>
                </table>
            </div>"""


def practice_html(cards: list[tuple[str, str, str]]) -> str:
    parts = ['<div class="practice-grid">']
    for badge, body, manual in cards:
        parts.append(
            f'                <article class="card practice-card">\n'
            f'                    <div class="card-badge">{badge}</div>\n'
            f'                    <p>{body}</p>\n'
            f'                    <p style="margin-top:10px;font-size:0.85rem;"><a href="{manual}">Open lab manual →</a></p>\n'
            f'                </article>'
        )
    parts.append("            </div>")
    return "\n".join(parts)

#!/usr/bin/env python3
"""Regenerate terraform/ and ansible/ HTML guides in k8sforbeginners style."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRACKS = {
    "terraform/essentials": {
        "title": "Terraform Essentials Interactive Learning",
        "subtitle": "5 visual explainers across 3 categories — providers, workflow, variables, state, and modules.",
        "search_placeholder": "Search topics, e.g. init, plan, variables, modules...",
        "categories": [
            {
                "tag": "foundation",
                "name": "Getting Started",
                "copy": "Providers, HCL basics, and the Terraform mental model every lab builds on.",
                "use": "Start here for onboarding and the init → validate → plan → apply workflow.",
                "pages": [
                    ("foundations.html", "Foundations", "Providers, resources, and HCL"),
                    ("workflow.html", "Workflow", "Init, plan, apply, destroy"),
                ],
            },
            {
                "tag": "ops",
                "name": "Configuration",
                "copy": "Input variables, outputs, formatting, and quality gates before apply.",
                "use": "Use when teaching configuration design and safe change review.",
                "pages": [
                    ("variables.html", "Variables", "Inputs, outputs, and tfvars"),
                ],
            },
            {
                "tag": "prod",
                "name": "State & Modules",
                "copy": "Local state, remote considerations, and reusable module composition.",
                "use": "Team collaboration patterns and module extraction labs.",
                "pages": [
                    ("state.html", "State", "Local state and sensitivity"),
                    ("modules.html", "Modules", "Reusable root modules"),
                ],
            },
        ],
    },
    "terraform/extended": {
        "title": "Terraform Extended Interactive Learning",
        "subtitle": "4 visual explainers across 3 categories — remote state, provisioners, functions, and capstones.",
        "search_placeholder": "Search topics, e.g. S3 backend, provisioner, for_each...",
        "categories": [
            {
                "tag": "foundation",
                "name": "Remote State",
                "copy": "S3 backends, locking, workspaces, migration, and remote state consumers.",
                "use": "Team state ownership and CI/CD integration patterns.",
                "pages": [("state.html", "Remote State", "S3, locking, and migration")],
            },
            {
                "tag": "ops",
                "name": "Provisioners & Functions",
                "copy": "local-exec, remote-exec, and HCL built-in functions for real-world configs.",
                "use": "Advanced configuration without leaving Terraform.",
                "pages": [
                    ("provisioners.html", "Provisioners", "local-exec and remote-exec"),
                    ("functions.html", "Functions", "for_each, lookup, and collections"),
                ],
            },
            {
                "tag": "prod",
                "name": "Capstone Projects",
                "copy": "Multi-resource projects combining state, modules, and validation workflows.",
                "use": "End-of-track synthesis and portfolio-ready labs.",
                "pages": [("projects.html", "Capstone Projects", "VPC and multi-tier patterns")],
            },
        ],
    },
    "ansible/essentials": {
        "title": "Ansible Essentials Interactive Learning",
        "subtitle": "6 visual explainers across 3 categories — architecture, inventory, playbooks, and roles.",
        "search_placeholder": "Search topics, e.g. inventory, playbook, handlers, vault...",
        "categories": [
            {
                "tag": "foundation",
                "name": "Architecture",
                "copy": "Control node, managed nodes, modules, and the push-based automation model.",
                "use": "Onboarding and explaining how Ansible differs from Terraform.",
                "pages": [("ansible-architecture.html", "Architecture", "Control vs managed nodes")],
            },
            {
                "tag": "ops",
                "name": "Inventory & Ad Hoc",
                "copy": "Static inventory, groups, host_vars, and one-off module execution.",
                "use": "Inventory design and quick operational commands.",
                "pages": [
                    ("inventory-flow.html", "Inventory Flow", "INI, YAML, and group_vars"),
                    ("adhoc-vs-playbook.html", "Ad Hoc vs Playbook", "When to use each"),
                ],
            },
            {
                "tag": "prod",
                "name": "Playbooks & Roles",
                "copy": "Playbook structure, handlers, variables, templates, roles, and Vault.",
                "use": "Production-style automation and secrets management.",
                "pages": [
                    ("playbook-handlers.html", "Handlers", "notify and service restarts"),
                    ("variables-templates.html", "Variables & Templates", "Jinja2 and facts"),
                    ("roles-and-vault.html", "Roles & Vault", "Role layout and encryption"),
                ],
            },
        ],
    },
    "ansible/extended": {
        "title": "Ansible Extended Interactive Learning",
        "subtitle": "4 visual explainers across 3 categories — facts, logic, dynamic inventory, and troubleshooting.",
        "search_placeholder": "Search topics, e.g. facts, loops, dynamic inventory, break-fix...",
        "categories": [
            {
                "tag": "foundation",
                "name": "Facts & Logic",
                "copy": "Gathering facts, custom facts, loops, and conditional execution.",
                "use": "Dynamic configuration based on host state.",
                "pages": [
                    ("facts.html", "Facts", "setup module and custom facts"),
                    ("loops-conditionals.html", "Loops & Conditionals", "loop, when, and until"),
                ],
            },
            {
                "tag": "ops",
                "name": "Inventory & Projects",
                "copy": "Dynamic inventory plugins and multi-playbook project layouts.",
                "use": "Cloud-native inventory and team project structure.",
                "pages": [("dynamic-inventory.html", "Dynamic Inventory", "AWS EC2 plugin")],
            },
            {
                "tag": "prod",
                "name": "Troubleshooting",
                "copy": "Break-fix drills, verbose output, and systematic diagnosis.",
                "use": "Exam prep and on-call debugging practice.",
                "pages": [("break-fix.html", "Break-Fix Drills", "Structured troubleshooting")],
            },
        ],
    },
}


# Unified k8sforbeginners palette — same on every page (see k8s/html/cronjobs-scheduling.html)
KUBE_BLUE = "#326CE5"
KUBE_BLUE_DEEP = "#1d4ed8"
KUBE_SKY = "#dbeafe"

TRACK_META = {
    "terraform/essentials": {
        "tag_class": "tf-ess",
        "track_title": "Terraform Essentials",
        "bootcamp": "10-hour bootcamp · Labs 01–08",
    },
    "terraform/extended": {
        "tag_class": "tf-ext",
        "track_title": "Terraform Extended",
        "bootcamp": "Self-paced · Labs 01–15",
    },
    "ansible/essentials": {
        "tag_class": "ans-ess",
        "track_title": "Ansible Essentials",
        "bootcamp": "10-hour bootcamp · Labs 01–07",
    },
    "ansible/extended": {
        "tag_class": "ans-ext",
        "track_title": "Ansible Extended",
        "bootcamp": "Self-paced · Labs 01–09",
    },
}


def topic_css() -> str:
    """CSS aligned with k8sforbeginners interactive pages (kube-blue, not per-track red/purple)."""
    return """        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --kube-blue: #326CE5;
            --kube-blue-deep: #1d4ed8;
            --kube-sky: #dbeafe;
            --ink: #1a1a2e;
            --muted: #64748b;
            --surface: #ffffff;
            --panel: #ffffff;
            --line: #dbe3f1;
            --mint: #dcfce7;
            --amber: #fef3c7;
            --rose: #ffe4e6;
            --blue: #2563eb;
            --slate-900: #0f172a;
            --slate-700: #334155;
            --slate-500: #64748b;
            --slate-200: #e2e8f0;
        }
        body {
            font-family: "Segoe UI", system-ui, sans-serif;
            background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
            color: var(--ink);
            line-height: 1.6;
            padding: 20px;
        }
        .container { max-width: 1380px; margin: 0 auto; }
        .hero {
            position: relative;
            text-align: center;
            background: white;
            border-radius: 16px;
            padding: 34px 32px 28px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
            margin-bottom: 26px;
            border: 1px solid rgba(50,108,229,0.1);
        }
        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 999px;
            background: #e8f1ff;
            color: var(--kube-blue-deep);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 14px;
        }
        h1 {
            font-size: clamp(2rem, 4vw, 3rem);
            color: var(--kube-blue);
            margin-bottom: 10px;
            line-height: 1.1;
        }
        .subtitle {
            font-size: 1.03rem;
            color: var(--muted);
            max-width: 980px;
            margin: 0 auto 18px;
        }
        .lead-panel {
            background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
            border: 1px solid rgba(50,108,229,0.12);
            border-radius: 14px;
            padding: 18px 20px;
            max-width: 980px;
            margin: 0 auto;
        }
        .lead-panel p { color: #334155; font-size: 0.98rem; }
        .nav-links {
            position: absolute;
            top: 16px;
            right: 20px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }
        .nav-links a {
            color: var(--kube-blue);
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid rgba(50,108,229,0.18);
            background: rgba(50,108,229,0.06);
            transition: background 0.2s, color 0.2s;
        }
        .nav-links a:hover {
            background: rgba(50,108,229,0.13);
            color: var(--kube-blue-deep);
        }
        .controls {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
            margin: 0 0 24px;
        }
        .btn {
            border: 2px solid #326CE5;
            background: white;
            color: var(--kube-blue-deep);
            padding: 11px 20px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
        }
        .btn:hover, .btn.active {
            background: var(--kube-blue);
            color: white;
            box-shadow: 0 4px 12px rgba(50,108,229,0.3);
            transform: translateY(-2px);
        }
        .view {
            display: none;
            background: var(--panel);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
            margin-bottom: 26px;
            border: 1px solid rgba(15,23,42,0.04);
        }
        .view.active { display: block; }
        .section-head {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: end;
            flex-wrap: wrap;
            margin-bottom: 24px;
            padding-bottom: 14px;
            border-bottom: 1px solid #e2e8f0;
        }
        .section-head h2 { color: var(--ink); font-size: 1.45rem; }
        .section-kicker {
            color: var(--kube-blue-deep);
            text-transform: uppercase;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            margin-bottom: 10px;
        }
        .section-note {
            border-left: 4px solid var(--kube-blue);
            background: #eff6ff;
            color: #1e3a8a;
            padding: 14px 16px;
            border-radius: 12px;
            margin-top: 18px;
        }
        .section-note a { color: var(--kube-blue-deep); }
        .concept-grid, .practice-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 18px;
        }
        .card {
            background: linear-gradient(180deg, #ffffff, #f8fbff);
            border: 1px solid var(--line);
            border-top: 4px solid #326CE5;
            border-radius: 16px;
            padding: 20px;
            min-height: 170px;
            box-shadow: 0 6px 18px rgba(15,23,42,0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover, .flow-step:hover, .example-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 24px rgba(15,23,42,0.1);
        }
        .card-badge {
            display: inline-flex;
            padding: 6px 12px;
            border-radius: 999px;
            background: var(--kube-sky);
            color: var(--kube-blue-deep);
            font-weight: 700;
            margin-bottom: 14px;
        }
        .practice-card .card-badge { background: var(--mint); color: #166534; }
        .practice-card { border-top-color: #22c55e; }
        .card p { color: #475569; }
        .card a, .practice-card a { color: var(--kube-blue); font-weight: 600; }
        .flow-track {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 18px;
        }
        .flow-step {
            position: relative;
            border-radius: 16px;
            padding: 22px 18px 18px;
            border: 1px solid rgba(50,108,229,0.18);
            background: linear-gradient(160deg, #ffffff 0%, #eff6ff 100%);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .step-number {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: var(--kube-blue);
            color: white;
            font-weight: 800;
            margin-bottom: 14px;
            box-shadow: 0 10px 20px rgba(50,108,229,0.22);
        }
        .flow-step h3 { font-size: 1rem; margin-bottom: 10px; color: #0f172a; }
        .flow-step p { color: #475569; font-size: 0.95rem; }
        .example-stack { display: grid; gap: 18px; }
        .example-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 18px;
            background: linear-gradient(180deg, #ffffff, #f8fafc);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .lab-callout {
            border: 1px dashed rgba(50,108,229,0.35);
            border-radius: 12px;
            padding: 14px 16px;
            margin: 14px 0;
            background: #eff6ff;
            color: #334155;
            font-size: 0.92rem;
        }
        .lab-callout strong { color: var(--kube-blue-deep); }
        pre {
            margin-top: 10px;
            background: #0f172a;
            color: #dbeafe;
            border-radius: 16px;
            padding: 18px;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            overflow-x: hidden;
            font-size: 0.88rem;
            line-height: 1.55;
            border: 1px solid rgba(148,163,184,0.18);
        }
        code { font-family: Consolas, 'Cascadia Code', monospace; }
        .table-wrap {
            overflow-x: auto;
            border-radius: 16px;
            border: 1px solid var(--line);
            background: white;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td {
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }
        th {
            background: linear-gradient(180deg, #326CE5, #2557be);
            color: white;
            font-weight: 700;
        }
        tbody tr:nth-child(even) { background: #f8fbff; }
        .footer-note {
            text-align: center;
            color: var(--muted);
            font-size: 0.9rem;
            margin-top: 18px;
        }
        .footer-note a { color: var(--kube-blue); text-decoration: none; }
        .footer-note a:hover { text-decoration: underline; }
        @media (max-width: 900px) {
            body { padding: 14px; }
            .hero, .view { padding: 22px; }
            .controls { justify-content: flex-start; }
            .concept-grid, .practice-grid, .flow-track { grid-template-columns: 1fr; }
            .nav-links { position: static; justify-content: center; margin-bottom: 12px; }
        }
        .home-link {
            position: absolute;
            top: 16px;
            right: 20px;
            color: var(--kube-blue);
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid rgba(50,108,229,0.18);
            background: rgba(50,108,229,0.06);
            transition: background 0.2s, color 0.2s;
        }
        .home-link:hover {
            background: rgba(50,108,229,0.13);
            color: var(--kube-blue-deep);
        }"""


def index_css() -> str:
    return """        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --blue: #2563eb;
            --cyan: #06b6d4;
            --slate-900: #0f172a;
            --slate-700: #334155;
            --slate-500: #64748b;
            --slate-200: #e2e8f0;
            --bg: #f8fafc;
            --green: #16a34a;
            --amber: #d97706;
            --rose: #e11d48;
        }
        body {
            font-family: "Segoe UI", system-ui, sans-serif;
            background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
            color: var(--slate-900);
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1380px; margin: 0 auto; }
        header {
            margin-bottom: 22px;
            padding: 18px 24px;
            border-radius: 14px;
            background: #ffffff;
            border: 1px solid rgba(37, 99, 235, 0.10);
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
            text-align: center;
        }
        h1 {
            font-size: 1.6rem;
            color: var(--blue);
            margin-bottom: 4px;
        }
        .subtitle {
            color: var(--slate-500);
            font-size: 0.92rem;
        }
        .stats {
            display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
            margin-top: 12px; font-size: 0.82rem; color: var(--slate-700);
        }
        .stats span {
            padding: 4px 10px; background: #eff6ff; border-radius: 999px;
        }
        .search-bar {
            margin-top: 16px;
            display: flex;
            justify-content: center;
        }
        .search-bar input {
            width: 100%;
            max-width: 480px;
            padding: 10px 16px 10px 40px;
            border: 1px solid var(--slate-200);
            border-radius: 10px;
            font-size: 0.92rem;
            font-family: inherit;
            color: var(--slate-900);
            background: #f8fafc url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2394a3b8' viewBox='0 0 16 16'%3E%3Cpath d='M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85zm-5.242.156a5 5 0 1 1 0-10 5 5 0 0 1 0 10z'/%3E%3C/svg%3E") no-repeat 14px center;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .search-bar input:focus {
            border-color: var(--blue);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
        }
        .search-bar input::placeholder { color: #94a3b8; }
        .no-results {
            text-align: center;
            color: var(--slate-500);
            padding: 24px;
            font-size: 0.92rem;
            display: none;
        }
        .section { margin-bottom: 22px; }
        .section-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 6px; }
        .section-note { color: var(--slate-500); font-size: 0.88rem; margin-bottom: 12px; }
        .catalog {
            background: rgba(255,255,255,0.92);
            border: 1px solid var(--slate-200);
            border-radius: 16px;
            padding: 8px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        table.catalog-table { width: 100%; border-collapse: collapse; }
        .catalog-table th, .catalog-table td {
            padding: 12px;
            text-align: left;
            vertical-align: top;
            border-bottom: 1px solid var(--slate-200);
        }
        .catalog-table th {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--slate-500);
            background: rgba(248, 250, 252, 0.9);
        }
        .catalog-table tr:last-child td { border-bottom: none; }
        .tag {
            display: inline-block;
            margin-bottom: 6px;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.03em;
        }
        .tag.foundation { background: #dbeafe; color: #1d4ed8; }
        .tag.ops { background: #dcfce7; color: #166534; }
        .tag.prod { background: #fef3c7; color: #92400e; }
        .tag.ref { background: #ffe4e6; color: #be123c; }
        .tag.tf-ess { background: #dbeafe; color: #1d4ed8; }
        .tag.tf-ext { background: #e0e7ff; color: #3730a3; }
        .tag.ans-ess { background: #dbeafe; color: #1e40af; }
        .tag.ans-ext { background: #e0f2fe; color: #0369a1; }
        .category-name { font-size: 0.94rem; font-weight: 800; margin-bottom: 4px; }
        .category-copy { color: var(--slate-500); font-size: 0.84rem; }
        .track-link {
            display: inline-block;
            margin-top: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--blue);
            text-decoration: none;
        }
        .track-link:hover { text-decoration: underline; }
        .link-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px 12px;
        }
        .link-item {
            padding: 7px 9px;
            border: 1px solid var(--slate-200);
            border-radius: 10px;
            background: linear-gradient(180deg, #fff 0%, #f8fbff 100%);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }
        .link-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
            border-color: #bfdbfe;
        }
        .link-item a { text-decoration: none; color: var(--blue); font-weight: 700; font-size: 0.84rem; }
        .link-item p { color: var(--slate-500); font-size: 0.76rem; margin-top: 2px; }
        .footer {
            margin-top: 24px;
            text-align: center;
            color: var(--slate-500);
            font-size: 0.84rem;
            padding-bottom: 12px;
        }
        @media (max-width: 1200px) {
            .link-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        @media (max-width: 768px) {
            body { padding: 12px; }
            h1 { font-size: 1.3rem; }
            .link-grid { grid-template-columns: 1fr; }
            .catalog-table, .catalog-table thead, .catalog-table tbody, .catalog-table th, .catalog-table td, .catalog-table tr { display: block; }
            .catalog-table thead { display: none; }
            .catalog-table td { border-bottom: none; padding-top: 6px; padding-bottom: 6px; }
            .catalog-table tr { border-bottom: 1px solid var(--slate-200); padding: 8px 0; }
        }"""


TAB_JS = """
    <script>
        const buttons = document.querySelectorAll('.btn');
        const views = document.querySelectorAll('.view');
        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                const viewId = button.dataset.view;
                buttons.forEach((b) => b.classList.remove('active'));
                views.forEach((v) => v.classList.remove('active'));
                button.classList.add('active');
                document.getElementById(viewId).classList.add('active');
            });
        });
    </script>"""

INDEX_JS = """
    <script>
        const searchInput = document.getElementById('catalog-search');
        const rows = document.querySelectorAll('.catalog-table tbody tr');
        const noResults = document.getElementById('no-results');
        searchInput.addEventListener('input', () => {
            const q = searchInput.value.toLowerCase().trim();
            let visible = 0;
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const match = !q || text.includes(q);
                row.style.display = match ? '' : 'none';
                if (match) visible++;
            });
            noResults.style.display = visible === 0 ? 'block' : 'none';
        });
    </script>"""


def view_section(vid: str, kicker: str, title: str, body: str, active: bool = False) -> str:
    cls = "view active" if active else "view"
    return f"""        <section id="{vid}" class="{cls}">
            <div class="section-head">
                <div>
                    <div class="section-kicker">{kicker}</div>
                    <h2>{title}</h2>
                </div>
            </div>
{body}
        </section>"""


def rel_to_root(track_key: str) -> str:
    depth = len(Path(track_key).parts) + 1
    return "/".join([".."] * depth) + "/index.html"


def render_topic(topic: dict, track_key: str) -> str:
    tabs = topic["tabs"]
    tab_buttons = "\n".join(
        f'            <button class="btn{" active" if i == 0 else ""}" data-view="{t["id"]}">{t["label"]}</button>'
        for i, t in enumerate(tabs)
    )
    sections = []
    for i, t in enumerate(tabs):
        sections.append(view_section(t["id"], t["kicker"], t["title"], t["body"], active=(i == 0)))
    css = topic_css()
    root_href = rel_to_root(track_key)
    meta = TRACK_META[track_key]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic["page_title"]}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header class="hero">
            <div class="nav-links">
                <a href="{root_href}">All Tracks</a>
                <a href="index.html">Track Catalog</a>
            </div>
            <div class="eyebrow">{topic["eyebrow"]}</div>
            <h1>{topic["h1"]}</h1>
            <p class="subtitle">{topic["subtitle"]}</p>
            <div class="lead-panel">
                <p>{topic["lead"]}</p>
            </div>
        </header>

        <div class="controls">
{tab_buttons}
        </div>

{chr(10).join(sections)}

        <p class="footer-note">{meta["track_title"]} · <a href="{root_href}">All tracks catalog</a> · <a href="index.html">Track index</a></p>
    </div>
{TAB_JS}
</body>
</html>
"""


def render_index(track_key: str, track: dict) -> str:
    page_count = sum(len(c["pages"]) for c in track["categories"])
    meta = TRACK_META[track_key]
    root_href = rel_to_root(track_key)
    rows = []
    for cat in track["categories"]:
        links = "\n".join(
            f'                                    <div class="link-item"><a href="./{href}">{title}</a><p>{desc}</p></div>'
            for href, title, desc in cat["pages"]
        )
        rows.append(
            f"""                        <tr>
                            <td>
                                <span class="tag {cat["tag"]}">{cat["tag"].title()}</span>
                                <div class="category-name">{cat["name"]}</div>
                                <div class="category-copy">{cat["copy"]}</div>
                            </td>
                            <td>
                                <div class="link-grid">
{links}
                                </div>
                            </td>
                            <td class="category-copy">{cat["use"]}</td>
                        </tr>"""
        )
    css = index_css()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{track["title"]}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{track["title"]}</h1>
            <p class="subtitle">{track["subtitle"]}</p>
            <p class="subtitle" style="margin-top:8px;"><a href="{root_href}" style="color:var(--blue);font-weight:700;text-decoration:none;">← All tracks catalog</a></p>
            <div class="search-bar">
                <input type="text" id="catalog-search" placeholder="{track["search_placeholder"]}" autocomplete="off">
            </div>
        </header>

        <section class="section">
            <div class="section-title">Browse by Category</div>
            <div class="section-note">{len(track["categories"])} focused categories · {meta["bootcamp"]}</div>
            <div class="catalog">
                <table class="catalog-table">
                    <thead>
                        <tr>
                            <th style="width: 20%;">Category</th>
                            <th style="width: 58%;">Pages</th>
                            <th style="width: 22%;">Use</th>
                        </tr>
                    </thead>
                    <tbody>
{chr(10).join(rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <div class="no-results" id="no-results">No topics match your search.</div>
        <div class="footer">{page_count} interactive topic pages — <a href="{root_href}" style="color:var(--blue);">All tracks</a></div>
    </div>
{INDEX_JS}
</body>
</html>
"""


def render_root_index() -> str:
    total_pages = sum(len(c["pages"]) for t in TRACKS.values() for c in t["categories"])
    rows = []
    for track_key, track in TRACKS.items():
        meta = TRACK_META[track_key]
        prefix = f"{track_key}/html"
        links = "\n".join(
            f'                                    <div class="link-item"><a href="./{prefix}/{href}">{title}</a><p>{desc}</p></div>'
            for cat in track["categories"]
            for href, title, desc in cat["pages"]
        )
        rows.append(
            f"""                        <tr>
                            <td>
                                <span class="tag {meta["tag_class"]}">{meta["track_title"]}</span>
                                <div class="category-name">{meta["track_title"]}</div>
                                <div class="category-copy">{meta["bootcamp"]}</div>
                                <a class="track-link" href="./{prefix}/index.html">Track catalog →</a>
                            </td>
                            <td>
                                <div class="link-grid">
{links}
                                </div>
                            </td>
                            <td class="category-copy">{track["subtitle"]}</td>
                        </tr>"""
        )
    css = index_css()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform &amp; Ansible Interactive Learning</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Terraform &amp; Ansible Interactive Learning</h1>
            <p class="subtitle">23 visual explainers across 4 tracks — essentials bootcamps plus extended depth.</p>
            <div class="stats">
                <span>4 tracks</span>
                <span>{total_pages} topic pages</span>
                <span>Offline-capable HTML</span>
            </div>
            <div class="search-bar">
                <input type="text" id="catalog-search" placeholder="Search topics, e.g. inventory, plan, vault, remote state..." autocomplete="off">
            </div>
        </header>

        <section class="section">
            <div class="section-title">Browse by Track</div>
            <div class="section-note">Bookmark this page — one catalog for Ansible essentials, Ansible extended, Terraform essentials, and Terraform extended.</div>
            <div class="catalog">
                <table class="catalog-table">
                    <thead>
                        <tr>
                            <th style="width: 20%;">Track</th>
                            <th style="width: 58%;">Pages</th>
                            <th style="width: 22%;">Overview</th>
                        </tr>
                    </thead>
                    <tbody>
{chr(10).join(rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="section">
            <div class="section-title">Lab manuals &amp; curriculum</div>
            <div class="section-note">Markdown lab guides and bootcamp agenda (same repo).</div>
            <div class="catalog" style="padding:16px;">
                <div class="link-grid">
                    <div class="link-item"><a href="./curriculum/20-hour-bootcamp.md">20-hour bootcamp</a><p>Full agenda</p></div>
                    <div class="link-item"><a href="./ansible/essentials/labmanuals/">Ansible essentials labs</a><p>Labs 01–07</p></div>
                    <div class="link-item"><a href="./ansible/extended/labmanuals/">Ansible extended labs</a><p>Advanced drills</p></div>
                    <div class="link-item"><a href="./terraform/essentials/labmanuals/">Terraform essentials labs</a><p>Labs 01–08</p></div>
                    <div class="link-item"><a href="./terraform/extended/labmanuals/">Terraform extended labs</a><p>Remote state &amp; more</p></div>
                    <div class="link-item"><a href="./curriculum/setup/aws-lab-environment.md">AWS lab setup</a><p>Environment prep</p></div>
                </div>
            </div>
        </section>

        <div class="no-results" id="no-results">No topics match your search.</div>
        <div class="footer">{total_pages} interactive topic pages across 4 tracks — open any link offline in your browser.</div>
    </div>
{INDEX_JS}
</body>
</html>
"""


def write_file(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
    return content.count("\n")



def update_readme(track_key: str, topic_files: list[str]) -> None:
    html_dir = ROOT / track_key / "html"
    readme = html_dir / "README.md"
    track_name = track_key.replace("/", " ").title()
    lines = [
        f"# {track_name} — HTML Catalog",
        "",
        "Offline interactive pages (embedded CSS, no CDN). Open `index.html` in any browser.",
        "",
        "```bash",
        f"open {track_key}/html/index.html",
        "```",
        "",
        f"## Pages ({len(topic_files) + 1} total including index)",
        "",
        "| File | Topic |",
        "|------|-------|",
        "| [index.html](index.html) | Catalog |",
    ]
    for fname in sorted(topic_files):
        slug = fname.replace(".html", "").replace("-", " ").title()
        lines.append(f"| [{fname}]({fname}) | {slug} |")
    lines.extend(["", "## Related", "", f"- Lab manuals: `../labmanuals/`", f"- Docs: `../docs/`", ""])
    readme.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    from topic_pages import TOPICS

    results: list[tuple[str, int]] = []
    root_path = ROOT / "index.html"
    n = write_file(root_path, render_root_index())
    results.append((str(root_path.relative_to(ROOT)), n))

    for track_key, track in TRACKS.items():
        index_path = ROOT / track_key / "html" / "index.html"
        n = write_file(index_path, render_index(track_key, track))
        results.append((str(index_path.relative_to(ROOT)), n))

        topic_files: list[str] = []
        for topic in TOPICS.values():
            if topic["track"] != track_key:
                continue
            out = ROOT / track_key / "html" / topic["filename"]
            n = write_file(out, render_topic(topic, track_key))
            results.append((str(out.relative_to(ROOT)), n))
            topic_files.append(topic["filename"])

        update_readme(track_key, topic_files)

    print("Generated HTML files:")
    short = 0
    for rel, lines in sorted(results):
        flag = " OK" if lines >= 550 or rel.endswith("index.html") else " SHORT"
        if flag == " SHORT":
            short += 1
        print(f"  {lines:4d}  {rel}{flag}")
    if short:
        raise SystemExit(f"{short} topic file(s) below 550 lines")
    print(f"\nTotal: {len(results)} files")


if __name__ == "__main__":
    main()

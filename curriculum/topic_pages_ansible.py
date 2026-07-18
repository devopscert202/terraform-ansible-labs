"""Ansible topic page definitions for build_k8s_style_html.py.

Essentials: ansible-architecture, inventory-flow, adhoc-vs-playbook,
playbook-handlers, variables-templates, roles-and-vault
Extended: facts, loops-conditionals, dynamic-inventory, break-fix
"""
from __future__ import annotations

from html_helpers import cards_html, examples_html, flow_html, practice_html, table_html


def _svg(title: str, boxes: list[tuple[int, int, int, int, str, str, str]], arrows: str = "") -> str:
  """Generate simple pipeline SVG."""
  rects = []
  for x, y, w, h, fill, stroke, label in boxes:
    rects.append(
      f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
      f'<text x="{x+w//2}" y="{y+h//2}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{label}</text>'
    )
  return f"""
            <svg viewBox="0 0 950 320" style="width:100%;max-width:950px;margin:20px auto;display:block;">
                <text x="475" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">{title}</text>
                {''.join(rects)}
                {arrows}
            </svg>"""


def _tab(id_: str, label: str, kicker: str, title: str, body: str) -> dict:
  return {"id": id_, "label": label, "kicker": kicker, "title": title, "body": body}


def _meta(track: str, filename: str, page_title: str, eyebrow: str, h1: str, subtitle: str, lead: str, tabs: list) -> dict:
  return {
    "track": track,
    "filename": filename,
    "page_title": page_title,
    "eyebrow": eyebrow,
    "h1": h1,
    "subtitle": subtitle,
    "lead": lead,
    "tabs": tabs,
  }


def _pad_commands(commands: list[tuple[str, str, str]]) -> str:
  return table_html(["Category", "Command", "Description"], [[a, b, c] for a, b, c in commands])


def _ref_appendix(topic_name: str, cmds: list[tuple[str, str, str]]) -> str:
  rows = [[a, b, c] for a, b, c in cmds]
  extras = []
  for i in range(3):
    extras.append(
      f'            <div class="example-card" style="margin-top:18px;">\n'
      f'                <div class="section-kicker">{topic_name} — reference drill {i+1}</div>\n'
      f'                <p style="color:#475569;margin-bottom:8px;">Extended operator notes for classroom review and certification-style recall.</p>\n'
      f'            </div>'
    )
  return (
    '\n            <div class="section-note">Extended reference appendix — bookmark for exam prep and on-the-job lookup.</div>\n'
    + table_html(["Topic", "Command / Pattern", "Notes"], rows)
    + "\n".join(extras)
  )


ANSIBLE_ARCH_SVG = """
            <svg viewBox="0 0 950 380" style="width:100%;max-width:950px;margin:20px auto;display:block;">
                <text x="475" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">Ansible Push Architecture</text>
                <rect x="40" y="60" width="180" height="70" rx="8" fill="#ffe4e6" stroke="#EE0000" stroke-width="2"/>
                <text x="130" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#CC0000">Control Node</text>
                <text x="130" y="108" text-anchor="middle" font-size="10" fill="#991b1b" font-family="monospace">ansible-playbook</text>
                <line x1="220" y1="95" x2="280" y2="95" stroke="#EE0000" stroke-width="2" marker-end="url(#a1)"/>
                <rect x="280" y="55" width="160" height="80" rx="10" fill="#f8fafc" stroke="#EE0000" stroke-width="3"/>
                <text x="360" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="#CC0000">Inventory</text>
                <text x="360" y="105" text-anchor="middle" font-size="10" fill="#64748b">hosts.ini · groups</text>
                <line x1="440" y1="95" x2="500" y2="95" stroke="#EE0000" stroke-width="2" marker-end="url(#a1)"/>
                <rect x="500" y="55" width="180" height="80" rx="8" fill="#dbeafe" stroke="#3b82f6" stroke-width="2"/>
                <text x="590" y="85" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e40af">SSH / WinRM</text>
                <text x="590" y="105" text-anchor="middle" font-size="10" fill="#1e3a8a">agentless :22</text>
                <line x1="680" y1="95" x2="740" y2="95" stroke="#3b82f6" stroke-width="2" marker-end="url(#a2)"/>
                <rect x="740" y="55" width="170" height="80" rx="8" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
                <text x="825" y="85" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">Managed Nodes</text>
                <text x="825" y="105" text-anchor="middle" font-size="10" fill="#14532d">web1 · web2 · db1</text>
                <rect x="280" y="180" width="200" height="70" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
                <text x="380" y="210" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400e">Modules</text>
                <text x="380" y="230" text-anchor="middle" font-size="10" fill="#78350f" font-family="monospace">apt · copy · service</text>
                <line x1="380" y1="135" x2="380" y2="180" stroke="#f59e0b" stroke-width="2" marker-end="url(#a3)"/>
                <rect x="40" y="280" width="870" height="80" rx="8" fill="#fff1f2" stroke="#f43f5e" stroke-width="2"/>
                <text x="475" y="310" text-anchor="middle" font-size="13" font-weight="bold" fill="#be123c">Lab 01 — ansible/essentials/labs/inventory/hosts.ini</text>
                <text x="475" y="335" text-anchor="middle" font-size="11" fill="#9f1239">ansible all -m ansible.builtin.ping → verify SSH connectivity</text>
                <defs>
                    <marker id="a1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#EE0000"/></marker>
                    <marker id="a2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#3b82f6"/></marker>
                    <marker id="a3" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#f59e0b"/></marker>
                </defs>
            </svg>"""


# ── Ansible Essentials ───────────────────────────────────────────────────────

ANSIBLE_ARCH = _meta("ansible/essentials", "ansible-architecture.html", "Ansible Architecture — Interactive Guide",
  "Ansible Essentials", "Architecture", "Control node, managed nodes, inventory, modules, and the agentless push model.",
  "Ansible automates configuration from a <strong>control node</strong> over SSH (or WinRM) — no agent installed on managed nodes.",
  [
    _tab("concept", "Concept", "Core Model", "Ansible Components",
         cards_html([
           ("Control node", "Where ansible-playbook runs — your laptop or CI runner."),
           ("Managed nodes", "Targets listed in inventory — EC2, VMs, containers."),
           ("Inventory", "Hosts, groups, vars — INI or YAML format."),
           ("Modules", "Units of work — apt, copy, service — idempotent when possible."),
           ("Playbooks", "YAML ordered lists of plays and tasks."),
           ("Facts", "Auto-gathered host data — OS, IPs, mounts — via setup module."),
         ])),
    _tab("architecture", "Architecture", "Topology", "Control → Managed Flow",
         examples_html([
           ("ansible.cfg excerpt", "[defaults]\ninventory = inventory/hosts.ini\nremote_user = ubuntu\nhost_key_checking = False"),
           ("Ping module", "ansible all -i inventory/hosts.ini -m ansible.builtin.ping"),
         ], lab="ansible/essentials/labs/inventory/hosts.ini")
         + ANSIBLE_ARCH_SVG),
    _tab("flow", "Flow", "Lab 01", "First Connectivity Check",
         flow_html([
           ("cd labs", "cd ansible/essentials/labs"),
           ("inventory", "cp inventory/hosts.ini.local.example inventory/hosts.ini.local — edit IPs"),
           ("ping", "ansible all -i inventory/hosts.ini.local -m ansible.builtin.ping"),
           ("verbose", "ansible all -i inventory/hosts.ini.local -m ping -vvv"),
           ("ad hoc command", "ansible webservers -i inventory/hosts.ini.local -m command -a 'hostname'"),
         ])),
    _tab("setup", "Setup", "Install", "Ansible on Control Node",
         examples_html([
           ("pip install", "python3 -m pip install ansible\nansible --version"),
           ("Ubuntu apt", "sudo apt update && sudo apt install -y ansible"),
           ("Verify collections", "ansible-galaxy collection list"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Core ansible CLI",
         _pad_commands([
           ("Ping", "<code>ansible HOSTS -m ping</code>", "Connectivity test"),
           ("Ad hoc", "<code>ansible HOSTS -m command -a 'CMD'</code>", "One-off command"),
           ("Playbook", "<code>ansible-playbook site.yml</code>", "Run playbook"),
           ("Inventory", "<code>ansible-inventory --list</code>", "Parsed inventory JSON"),
           ("Config", "<code>ansible-config dump</code>", "Effective settings"),
         ]) + _ref_appendix("Architecture", [
           ("FQCN", "ansible.builtin.ping", "Lab 01"),
           ("Inventory", "-i inventory/hosts.ini.local", "All labs"),
           ("Become", "-b for sudo", "Lab 03+"),
           ("Limit", "-l web1", "Subset hosts"),
           ("Forks", "-f 5 parallel", "Performance"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 01 Commands",
         examples_html([
           ("Ping all", "cd ansible/essentials/labs\nansible all -i inventory/hosts.ini.local -m ansible.builtin.ping"),
           ("Hostname", "ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a 'hostname'"),
         ], lab="ansible/essentials/labs/")),
    _tab("comparison", "Compare", "Decision Guide", "Ansible vs Terraform",
         table_html(["", "Ansible", "Terraform"],
           [["Primary use", "Configure OS/apps", "Provision infrastructure"],
            ["State", "None by default", "Explicit state file"],
            ["Agent", "Agentless SSH", "Agentless API"],
            ["Idempotency", "Module-level", "Plan/apply graph"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Architecture Practice",
         practice_html([
           ("Lab 01", "Static inventory and ping all hosts.", "../labmanuals/lab01-inventory-static-hosts.md"),
           ("Verbose debug", "Run ping with -vvv; identify SSH step.", "../labmanuals/lab01-inventory-static-hosts.md"),
           ("Draw diagram", "Sketch control node to two web servers.", "../labmanuals/lab01-inventory-static-hosts.md"),
           ("ansible.cfg", "Locate effective inventory path.", "../labmanuals/lab01-inventory-static-hosts.md"),
           ("FQCN", "Rewrite ping using full collection name.", "../labmanuals/lab03-adhoc-commands.md"),
           ("Compare TF", "List one task for Ansible vs Terraform.", "../labmanuals/lab01-inventory-static-hosts.md"),
         ])),
  ])

INVENTORY_FLOW = _meta("ansible/essentials", "inventory-flow.html", "Inventory Flow — Interactive Guide",
  "Ansible Essentials", "Inventory", "INI and YAML inventory, groups, host_vars, group_vars, and variable precedence.",
  "Inventory defines <strong>which hosts</strong> Ansible manages and <strong>what variables</strong> apply to them.",
  [
    _tab("concept", "Concept", "Core Model", "Inventory Concepts",
         cards_html([
           ("Hosts", "Individual machines — IP or DNS name."),
           ("Groups", "Logical sets — [webservers], [dbservers]."),
           ("Children", "Nested groups — [web:children]."),
           ("host_vars/", "Per-host YAML — hostname-specific overrides."),
           ("group_vars/", "Per-group YAML — shared settings."),
           ("INI vs YAML", "INI for simple labs; YAML for complex structures."),
         ])),
    _tab("architecture", "Architecture", "Layout", "Inventory Directory",
         examples_html([
           ("INI inventory", "[webservers]\nweb1 ansible_host=10.0.1.10\nweb2 ansible_host=10.0.1.11\n\n[webservers:vars]\nansible_user=ubuntu"),
           ("group_vars", "group_vars/webservers.yml:\n  http_port: 80\n  app_env: dev"),
         ], lab="ansible/essentials/labs/inventory/")
         + _svg("Inventory Resolution", [
           (40, 80, 150, 55, "#ffe4e6", "#EE0000", "hosts.ini"),
           (220, 80, 150, 55, "#dbeafe", "#3b82f6", "group_vars"),
           (400, 80, 150, 55, "#fef3c7", "#f59e0b", "host_vars"),
           (580, 80, 150, 55, "#dcfce7", "#22c55e", "merged vars"),
         ])),
    _tab("flow", "Flow", "Lab 02", "Inventory Lab Workflow",
         flow_html([
           ("Lab 02", "cd ansible/essentials/labs — edit hosts.ini.local"),
           ("List inventory", "ansible-inventory -i inventory/hosts.ini.local --graph"),
           ("Host vars", "Create host_vars/web1.yml with custom key."),
           ("Group vars", "Add variable in group_vars/webservers.yml"),
           ("Verify merge", "ansible webservers -m debug -a 'var=http_port'"),
         ])),
    _tab("setup", "Setup", "Patterns", "Production Inventory Hints",
         examples_html([
           ("YAML inventory", "all:\n  children:\n    webservers:\n      hosts:\n        web1:\n          ansible_host: 10.0.1.10"),
           ("Dynamic preview", "# extended track — AWS EC2 plugin"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Inventory Commands",
         _pad_commands([
           ("Graph", "<code>ansible-inventory --graph</code>", "Tree view"),
           ("List", "<code>ansible-inventory --list</code>", "Full JSON"),
           ("Host", "<code>ansible-inventory --host web1</code>", "Merged vars for host"),
         ]) + _ref_appendix("Inventory", [
           ("ansible_host", "override DNS/IP", "Lab 02"),
           (":children", "nested groups", "Lab 02"),
           ("group_vars/", "directory per group", "Lab 02"),
           ("--limit", "-l web1", "Restrict run"),
           ("meta", "[group:vars] in INI", "Lab 02"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 02 Commands",
         examples_html([
           ("Graph", "ansible-inventory -i inventory/hosts.ini.local --graph"),
           ("Debug var", "ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.debug -a 'var=app_env'"),
         ], lab="inventory/hosts.ini.local")),
    _tab("comparison", "Compare", "Decision Guide", "INI vs YAML Inventory",
         table_html(["", "INI", "YAML"],
           [["Readability", "High for small", "Better for nesting"],
            ["Complex vars", "Awkward", "Native structures"],
            ["Lab default", "Essentials labs", "Extended projects"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Inventory Practice",
         practice_html([
           ("Lab 02", "Build groups and verify with --graph.", "../labmanuals/lab02-inventory-hosts-groups.md"),
           ("host_vars", "Override one host port variable.", "../labmanuals/lab02-inventory-hosts-groups.md"),
           ("group_vars", "Set shared app_env for webservers.", "../labmanuals/lab02-inventory-hosts-groups.md"),
           ("YAML convert", "Rewrite INI inventory as YAML.", "../labmanuals/lab02-inventory-hosts-groups.md"),
           ("debug module", "Print merged variables per host.", "../labmanuals/lab02-inventory-hosts-groups.md"),
           ("Limit", "Run command against single host with -l.", "../labmanuals/lab02-inventory-hosts-groups.md"),
         ])),
  ])

ADHOC = _meta("ansible/essentials", "adhoc-vs-playbook.html", "Ad Hoc vs Playbook — Interactive Guide",
  "Ansible Essentials", "Ad Hoc Commands", "One-off module execution versus repeatable playbook automation.",
  "Ad hoc commands run a <strong>single module</strong> from the CLI. Playbooks capture ordered, reusable automation for teams.",
  [
    _tab("concept", "Concept", "Core Model", "When to Use Each",
         cards_html([
           ("Ad hoc", "Quick checks — uptime, disk, service status, package install."),
           ("Playbook", "Repeatable multi-step configuration — web server, app deploy."),
           ("Modules", "Both use same modules — command, apt, service, copy."),
           ("Idempotency", "Playbooks with proper modules safer for repeated runs."),
           ("Check mode", "ansible-playbook --check — dry run for playbooks."),
           ("Audit trail", "Playbooks in Git beat undocumented ad hoc history."),
         ])),
    _tab("architecture", "Architecture", "CLI", "Ad Hoc Anatomy",
         examples_html([
           ("Uptime", "ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a 'uptime'"),
           ("Apt with become", "ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a 'name=tree state=present'"),
         ], lab="ansible/essentials/labs/")
         + _svg("Ad Hoc vs Playbook", [
           (60, 80, 180, 60, "#ffe4e6", "#EE0000", "ansible -m"),
           (280, 80, 180, 60, "#dbeafe", "#3b82f6", "one module"),
           (500, 80, 180, 60, "#dcfce7", "#22c55e", "ansible-playbook"),
           (720, 80, 160, 60, "#fef3c7", "#f59e0b", "many tasks"),
         ])),
    _tab("flow", "Flow", "Lab 03", "Ad Hoc Exercise Flow",
         flow_html([
           ("uptime", "ansible webservers -m command -a 'uptime'"),
           ("apt install", "ansible webservers -b -m apt -a 'name=tree state=present'"),
           ("setup facts", "ansible webservers -m setup -a 'filter=ansible_distribution*'"),
           ("service", "ansible webservers -m service -a 'name=ssh state=started'"),
           ("check mode", "ansible webservers -m apt -a 'name=htop state=present' -b -C"),
         ])),
    _tab("setup", "Setup", "Flags", "Common Ad Hoc Flags",
         examples_html([
           ("Become", "-b  # sudo on Ubuntu targets"),
           ("Limit", "-l web1  # single host"),
           ("Forks", "-f 10  # parallel connections"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Ad Hoc Reference",
         _pad_commands([
           ("Command", "<code>-m command -a 'uptime'</code>", "Run command"),
           ("Shell", "<code>-m shell -a 'df -h | head'</code>", "Shell pipeline"),
           ("Apt", "<code>-b -m apt -a 'name=nginx state=present'</code>", "Package"),
           ("Setup", "<code>-m setup</code>", "Gather facts"),
           ("Check", "<code>-C</code>", "Check mode (dry run)"),
         ]) + _ref_appendix("Ad Hoc", [
           ("-m", "module name FQCN", "Lab 03"),
           ("-a", "module args string", "Lab 03"),
           ("-b", "become root", "Lab 03"),
           ("-C", "check mode", "Lab 03"),
           ("playbook", "site.yml for repeatability", "Lab 04"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 03 Commands",
         examples_html([
           ("Uptime", "ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a 'uptime'"),
           ("Install tree", "ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a 'name=tree state=present'"),
           ("Facts filter", "ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.setup -a 'filter=ansible_memtotal_mb'"),
         ], lab="lab03-adhoc-commands.md")),
    _tab("comparison", "Compare", "Decision Guide", "Ad Hoc vs Playbook",
         table_html(["Scenario", "Ad hoc", "Playbook"],
           [["One-time debug", "Yes", "Overkill"],
            ["Web server role", "No", "Yes"],
            ["Package check", "Yes", "Optional"],
            ["Team reuse", "No", "Yes — version in Git"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Ad Hoc Practice",
         practice_html([
           ("Lab 03", "Complete all five exercises.", "../labmanuals/lab03-adhoc-commands.md"),
           ("Check mode", "Run apt in check mode before real install.", "../labmanuals/lab03-adhoc-commands.md"),
           ("Convert", "Rewrite one ad hoc as single-task playbook.", "../labmanuals/lab04-playbook-apache-webserver.md"),
           ("Cleanup", "Remove packages installed during lab.", "../labmanuals/lab03-adhoc-commands.md"),
           ("Forks", "Compare runtime with -f 1 vs -f 5.", "../labmanuals/lab03-adhoc-commands.md"),
           ("Verbose", "Diagnose failure with -vvv.", "../labmanuals/lab03-adhoc-commands.md"),
         ])),
  ])

PLAYBOOK_HANDLERS = _meta("ansible/essentials", "playbook-handlers.html", "Playbook Handlers — Interactive Guide",
  "Ansible Essentials", "Handlers & Notify", "Play structure, handlers, notify, and service restart patterns.",
  "Handlers run <strong>at end of play</strong>, only if notified — ideal for service restarts after config changes.",
  [
    _tab("concept", "Concept", "Core Model", "Playbook Structure",
         cards_html([
           ("Play", "Maps hosts to tasks — one play per role target."),
           ("Tasks", "Ordered module calls — name, module, args."),
           ("Handlers", "Special tasks triggered by notify."),
           ("notify", "Task notifies handler name on change."),
           ("changed only", "Handlers run only when notifying task changes."),
           ("listen", "Multiple notifies can trigger one handler."),
         ])),
    _tab("architecture", "Architecture", "Notify Flow", "Handler Execution Order",
         examples_html([
           ("Playbook skeleton", "---\n- name: Configure web\n  hosts: webservers\n  tasks:\n    - name: Install apache\n      ansible.builtin.apt:\n        name: apache2\n        state: present\n    - name: Deploy config\n      ansible.builtin.template:\n        src: site.conf.j2\n        dest: /etc/apache2/sites-available/site.conf\n      notify: Restart apache\n  handlers:\n    - name: Restart apache\n      ansible.builtin.service:\n        name: apache2\n        state: restarted"),
         ], lab="ansible/essentials/labs/playbooks/")
         + _svg("Handler Notify", [
           (80, 80, 160, 55, "#dbeafe", "#3b82f6", "Task changes"),
           (280, 80, 160, 55, "#fef3c7", "#f59e0b", "notify"),
           (480, 80, 160, 55, "#ffe4e6", "#EE0000", "end of play"),
           (680, 80, 160, 55, "#dcfce7", "#22c55e", "handler runs"),
         ])),
    _tab("flow", "Flow", "Lab 04", "Apache Playbook Flow",
         flow_html([
           ("Lab 04", "cd ansible/essentials/labs/playbooks"),
           ("Syntax check", "ansible-playbook apache.yml --syntax-check"),
           ("Check mode", "ansible-playbook apache.yml --check"),
           ("Apply", "ansible-playbook -i ../inventory/hosts.ini.local apache.yml"),
           ("Verify", "curl http://web1/ — confirm page"),
           ("Idempotent", "Re-run playbook — handlers should not fire if no change"),
         ])),
    _tab("setup", "Setup", "YAML", "Playbook Conventions",
         examples_html([
           ("Syntax check", "ansible-playbook site.yml --syntax-check"),
           ("List tasks", "ansible-playbook site.yml --list-tasks"),
           ("List handlers", "ansible-playbook site.yml --list-handlers"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Playbook Commands",
         _pad_commands([
           ("Run", "<code>ansible-playbook site.yml</code>", "Execute playbook"),
           ("Check", "<code>ansible-playbook site.yml --check</code>", "Dry run"),
           ("Diff", "<code>ansible-playbook site.yml --diff</code>", "Show file diffs"),
           ("Limit", "<code>ansible-playbook site.yml -l web1</code>", "Subset hosts"),
           ("Tags", "<code>--tags install</code>", "Run tagged tasks only"),
         ]) + _ref_appendix("Handlers", [
           ("notify", "notify: Restart apache", "Lab 04"),
           ("handlers", "handlers section in play", "Lab 04"),
           ("changed_when", "control change result", "Extended"),
           ("flush_handlers", "meta: flush_handlers", "Advanced"),
           ("listen", "handler listen alias", "Docs"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 04 Commands",
         examples_html([
           ("Apache playbook", "cd ansible/essentials/labs/playbooks\nansible-playbook -i ../inventory/hosts.ini.local apache.yml"),
           ("Verbose", "ansible-playbook apache.yml -i ../inventory/hosts.ini.local -v"),
         ], lab="playbooks/apache.yml")),
    _tab("comparison", "Compare", "Decision Guide", "Handlers vs Inline Restart",
         table_html(["", "Handler", "Inline restart task"],
           [["Runs when", "End of play, if notified", "Every play"],
            ["Duplicate restarts", "Coalesced", "Multiple restarts"],
            ["Best for", "Service reload", "Simple labs only"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Handler Practice",
         practice_html([
           ("Lab 04", "Deploy Apache with handler restart.", "../labmanuals/lab04-playbook-apache-webserver.md"),
           ("Idempotency", "Run twice; confirm second run changed=0.", "../labmanuals/lab04-playbook-apache-webserver.md"),
           ("Break config", "Introduce template error; fix and re-run.", "../labmanuals/lab04-playbook-apache-webserver.md"),
           ("List handlers", "--list-handlers before apply.", "../labmanuals/lab04-playbook-apache-webserver.md"),
           ("Extended", "Preview extended handlers lab.", "../labmanuals/lab06-handlers.md"),
           ("Check mode", "--check before production-like run.", "../labmanuals/lab04-playbook-apache-webserver.md"),
         ])),
  ])

VARS_TEMPLATES = _meta("ansible/essentials", "variables-templates.html", "Variables & Templates — Interactive Guide",
  "Ansible Essentials", "Variables & Jinja2", "Variable precedence, facts, register, and Jinja2 templates.",
  "Variables flow from inventory, playbooks, and facts into <strong>Jinja2 templates</strong> and module arguments.",
  [
    _tab("concept", "Concept", "Core Model", "Variable Sources",
         cards_html([
           ("Inventory vars", "group_vars, host_vars — lowest friction defaults."),
           ("Play vars", "vars: block in play — play-scoped."),
           ("Task vars", "module parameters and task-level vars."),
           ("Facts", "ansible_* from setup — discovered host state."),
           ("register", "Capture task output for later tasks."),
           ("Templates", ".j2 files rendered to destination paths."),
         ])),
    _tab("architecture", "Architecture", "Jinja2", "Template Rendering",
         examples_html([
           ("Template task", "- name: Deploy config\n  ansible.builtin.template:\n    src: app.conf.j2\n    dest: /etc/app/app.conf\n    mode: '0644'"),
           ("Jinja2 in template", "# Managed by Ansible\nport = {{ http_port }}\nenv = {{ app_env }}"),
         ], lab="ansible/essentials/labs/playbooks/templates/")
         + _svg("Variable Precedence", [
           (30, 80, 130, 50, "#ffe4e6", "#EE0000", "extra vars"),
           (180, 80, 130, 50, "#fef3c7", "#f59e0b", "play vars"),
           (330, 80, 130, 50, "#dbeafe", "#3b82f6", "host_vars"),
           (480, 80, 130, 50, "#dcfce7", "#22c55e", "group_vars"),
           (630, 80, 130, 50, "#f0fdf4", "#16a34a", "defaults"),
         ])),
    _tab("flow", "Flow", "Lab 05", "Variables Lab Flow",
         flow_html([
           ("Lab 05", "cd ansible/essentials/labs/playbooks"),
           ("Edit vars", "Set http_port in group_vars or playbook vars"),
           ("Template deploy", "ansible-playbook nodejs.yml with templates"),
           ("register", "Capture task output; debug in next task"),
           ("facts", "Use ansible_distribution in when condition"),
         ])),
    _tab("setup", "Setup", "Jinja2", "Common Filters",
         examples_html([
           ("default filter", "{{ app_env | default('dev') }}"),
           ("join", "{{ groups['webservers'] | join(',') }}"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Variable Debugging",
         _pad_commands([
           ("Debug", "<code>-m debug -a 'var=variable_name'</code>", "Print variable"),
           ("Extra vars", "<code>-e http_port=8080</code>", "Highest precedence"),
           ("Dump facts", "<code>-m setup</code>", "All facts"),
         ]) + _ref_appendix("Variables", [
           ("register", "register: result", "Lab 05"),
           ("hostvars", "hostvars['web1']", "Lab 05"),
           ("template", ".j2 files", "Lab 05"),
           ("when", "when: ansible_os_family == 'Debian'", "Extended"),
           ("vars_files", "include external vars", "Lab 05"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 05 Commands",
         examples_html([
           ("Playbook with vars", "ansible-playbook -i ../inventory/hosts.ini.local nodejs.yml -e nodejs_version=18"),
           ("Debug", "ansible web1 -i ../inventory/hosts.ini.local -m debug -a 'var=hostvars[inventory_hostname]'"),
         ], lab="lab05-playbook-variables.md")),
    _tab("comparison", "Compare", "Decision Guide", "vars vs group_vars",
         table_html(["", "group_vars/", "play vars:"],
           [["Reuse", "Across playbooks", "Single play"],
            ["Git friendly", "Yes", "Inline only"],
            ["Lab pattern", "Preferred", "Quick demos"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Variables Practice",
         practice_html([
           ("Lab 05", "Parameterize playbook with extra vars.", "../labmanuals/lab05-playbook-variables.md"),
           ("Template", "Add new key to Jinja2 template.", "../labmanuals/lab05-playbook-variables.md"),
           ("register", "Store command output; print in debug.", "../labmanuals/lab05-playbook-variables.md"),
           ("Precedence", "Override group_var with -e.", "../labmanuals/lab05-playbook-variables.md"),
           ("Facts", "Branch task on ansible_distribution.", "../labmanuals/lab02-facts.md"),
           ("Lint", "ansible-lint playbook if available.", "../labmanuals/lab05-playbook-variables.md"),
         ])),
  ])

ROLES_VAULT = _meta("ansible/essentials", "roles-and-vault.html", "Roles & Vault — Interactive Guide",
  "Ansible Essentials", "Roles & Vault", "Role directory layout, ansible-galaxy, and encrypting secrets with Ansible Vault.",
  "Roles package tasks, handlers, templates, and defaults. <strong>Ansible Vault</strong> encrypts sensitive files at rest in Git.",
  [
    _tab("concept", "Concept", "Core Model", "Roles and Secrets",
         cards_html([
           ("Role layout", "tasks/, handlers/, templates/, defaults/, vars/."),
           ("roles_path", "ansible.cfg roles_path or ./roles/"),
           ("include_role", "Dynamic role inclusion in tasks."),
           ("Vault", "Encrypt files — ansible-vault encrypt secrets.yml."),
           ("Vault password", "File, prompt, or script — never commit password."),
           ("Capstone", "Lab 07 combines roles, vault, and Node.js deploy."),
         ])),
    _tab("architecture", "Architecture", "Role Layout", "Standard Role Tree",
         examples_html([
           ("Role tree", "roles/webserver/\n├── tasks/main.yml\n├── handlers/main.yml\n├── templates/nginx.conf.j2\n├── defaults/main.yml\n└── vars/main.yml"),
           ("site.yml", "- hosts: webservers\n  roles:\n    - webserver"),
         ], lab="ansible/essentials/labs/roles/")
         + _svg("Vault Workflow", [
           (50, 80, 150, 55, "#ffe4e6", "#EE0000", "plaintext secret"),
           (230, 80, 150, 55, "#dbeafe", "#3b82f6", "ansible-vault encrypt"),
           (410, 80, 150, 55, "#dcfce7", "#22c55e", "vault file in Git"),
           (590, 80, 150, 55, "#fef3c7", "#f59e0b", "playbook --ask-vault-pass"),
         ])),
    _tab("flow", "Flow", "Labs 06–07", "Roles and Vault Path",
         flow_html([
           ("Lab 06", "Create role with tasks and handlers."),
           ("galaxy init", "ansible-galaxy init myrole — scaffold structure."),
           ("Lab 07 vault", "ansible-vault create group_vars/webservers/vault.yml"),
           ("Run encrypted", "ansible-playbook site.yml --ask-vault-pass"),
           ("Capstone", "Node.js role with vaulted DB password."),
         ])),
    _tab("setup", "Setup", "Vault", "Vault Operations",
         examples_html([
           ("Create", "ansible-vault create secrets.yml"),
           ("Edit", "ansible-vault edit secrets.yml"),
           ("Encrypt string", "ansible-vault encrypt_string 'dbpass' --name 'db_password'"),
           ("Vault ID file", "echo 'mypass' > ~/.vault_pass && chmod 600 ~/.vault_pass"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Role and Vault CLI",
         _pad_commands([
           ("Galaxy init", "<code>ansible-galaxy init ROLE</code>", "Scaffold role"),
           ("Vault encrypt", "<code>ansible-vault encrypt FILE</code>", "Encrypt file"),
           ("Vault view", "<code>ansible-vault view FILE</code>", "Decrypt to stdout"),
           ("Playbook vault", "<code>--ask-vault-pass</code>", "Prompt for password"),
           ("Vault file", "<code>--vault-password-file ~/.vault_pass</code>", "Non-interactive"),
         ]) + _ref_appendix("Roles/Vault", [
           ("roles:", "list in play", "Lab 06"),
           ("defaults/", "lowest precedence", "Lab 06"),
           ("vault.yml", "encrypted group_vars", "Lab 07"),
           ("NODEJS", "capstone playbook", "Lab 07"),
           (".gitignore", "vault password file", "Security"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Labs 06–07",
         examples_html([
           ("Role lab", "cd ansible/essentials/labs\nansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml"),
           ("Vault capstone", "ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --ask-vault-pass"),
         ], lab="labs/playbooks/nodejs.yml")),
    _tab("comparison", "Compare", "Decision Guide", "Roles vs Plain Playbooks",
         table_html(["", "Plain playbook", "Role"],
           [["Reuse", "Copy-paste", "Importable"],
            ["Galaxy share", "No", "Yes"],
            ["Lab 06+", "Early learning", "Standard pattern"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Roles & Vault Practice",
         practice_html([
           ("Lab 06", "Build and apply custom role.", "../labmanuals/lab06-roles-create.md"),
           ("Lab 07", "Vault secrets and Node.js capstone.", "../labmanuals/lab07-vault-and-nodejs-capstone.md"),
           ("galaxy init", "Scaffold role; compare to hand-built.", "../labmanuals/lab06-roles-create.md"),
           ("encrypt_string", "Embed vaulted inline variable.", "../labmanuals/lab07-vault-and-nodejs-capstone.md"),
           ("Rotate secret", "vault edit — change password safely.", "../labmanuals/lab07-vault-and-nodejs-capstone.md"),
           ("Never commit", "Confirm .gitignore for vault pass.", "../labmanuals/lab07-vault-and-nodejs-capstone.md"),
         ])),
  ])

# ── Ansible Extended ─────────────────────────────────────────────────────────

FACTS = _meta("ansible/extended", "facts.html", "Ansible Facts — Interactive Guide",
  "Ansible Extended", "Facts", "Gathering facts, fact caching, and custom facts scripts.",
  "Facts are variables Ansible discovers about each host — OS, network, hardware — powering conditional logic and templates.",
  [
    _tab("concept", "Concept", "Core Model", "Fact Types",
         cards_html([
           ("ansible_facts", "All facts from setup module — ansible_os_family, etc."),
           ("gather_facts", "Play key gather_facts: true (default)."),
           ("filter", "setup: filter=ansible_distribution* — subset only."),
           ("custom facts", "/etc/ansible/facts.d/*.fact scripts on managed node."),
           ("fact caching", "JSON file or Redis — speed up large inventories."),
           ("set_fact", "Define runtime facts in play."),
         ])),
    _tab("architecture", "Architecture", "Discovery", "Fact Gathering Pipeline",
         examples_html([
           ("Filtered setup", "ansible webservers -m ansible.builtin.setup -a 'filter=ansible_memtotal_mb'"),
           ("custom fact script", "#!/bin/bash\necho '{\"app_version\": \"2.1.0\"}'"),
         ], lab="ansible/extended/labs/")
         + _svg("Facts Pipeline", [
           (50, 80, 160, 55, "#ffe4e6", "#CC0000", "setup module"),
           (240, 80, 160, 55, "#dbeafe", "#3b82f6", "fact cache"),
           (430, 80, 160, 55, "#dcfce7", "#22c55e", "hostvars"),
           (620, 80, 160, 55, "#fef3c7", "#f59e0b", "when/templates"),
         ])),
    _tab("flow", "Flow", "Lab 02", "Facts Lab Workflow",
         flow_html([
           ("Lab 02 extended", "Gather full facts for one host."),
           ("Filter", "Request only network facts."),
           ("Custom fact", "Deploy script to /etc/ansible/facts.d/"),
           ("Re-gather", "ansible -m setup — see custom key."),
           ("when", "Use ansible_distribution_major_version in playbook."),
         ])),
    _tab("setup", "Setup", "Disable", "When to Skip Facts",
         examples_html([
           ("gather_facts: false", "# speed up large static plays"),
           ("fact_path", "ansible.cfg fact_caching_connection"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Facts Commands",
         _pad_commands([
           ("All facts", "<code>-m setup</code>", "Full fact dump"),
           ("Filter", "<code>-m setup -a 'filter=ansible_eth*'</code>", "Subset"),
           ("Debug fact", "<code>-m debug -a 'var=ansible_os_family'</code>", "Single value"),
         ]) + _ref_appendix("Facts", [
           ("ansible_date_time", "time facts", "Lab 02"),
           ("custom .fact", "executable JSON output", "Lab 02"),
           ("set_fact", "runtime variables", "Extended"),
           ("gather_subset", "minimal fact gather", "Performance"),
           ("fact caching", "jsonfile plugin", "Large inv"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 02 Extended",
         examples_html([
           ("Memory fact", "ansible web1 -i inventory/hosts.ini.local -m setup -a 'filter=ansible_memtotal_mb'"),
           ("OS family", "ansible web1 -i inventory/hosts.ini.local -m debug -a 'var=ansible_os_family'"),
         ], lab="lab02-facts.md")),
    _tab("comparison", "Compare", "Decision Guide", "Facts vs Variables",
         table_html(["", "Facts", "Inventory vars"],
           [["Source", "Discovered", "Declared"],
            ["Changes", "Each run", "When you edit"],
            ["Use", "Conditionals", "Configuration"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Facts Practice",
         practice_html([
           ("Lab 02", "Complete facts and custom fact lab.", "../labmanuals/lab02-facts.md"),
           ("Filter", "Gather only ansible_processor* facts.", "../labmanuals/lab02-facts.md"),
           ("Custom", "Write .fact script returning JSON.", "../labmanuals/lab02-facts.md"),
           ("when", "Skip task when ansible_virtualization_type==docker.", "../labmanuals/lab02-facts.md"),
           ("Debug", "Print ansible_all_ipv4_addresses.", "../labmanuals/lab02-facts.md"),
           ("Performance", "Compare runtime with gather_facts false.", "../labmanuals/lab02-facts.md"),
         ])),
  ])

LOOPS = _meta("ansible/extended", "loops-conditionals.html", "Loops & Conditionals — Interactive Guide",
  "Ansible Extended", "Loops & When", "loop, with_items, when, until, and failed_when for control flow.",
  "Loops iterate over lists; conditionals skip or select tasks — essential for real playbooks beyond linear scripts.",
  [
    _tab("concept", "Concept", "Core Model", "Control Flow",
         cards_html([
           ("loop", "Modern loop: — replaces with_items."),
           ("when", "Boolean expression — skip task if false."),
           ("until", "Retry until condition true — with retries/delay."),
           ("failed_when", "Mark success as failure based on output."),
           ("changed_when", "Control idempotency reporting."),
           ("block/rescue", "Error handling groups — extended patterns."),
         ])),
    _tab("architecture", "Architecture", "Loop", "Task Iteration",
         examples_html([
           ("loop users", "- name: Create users\n  ansible.builtin.user:\n    name: \"{{ item.name }}\"\n    groups: \"{{ item.groups }}\"\n  loop:\n    - { name: alice, groups: sudo }\n    - { name: bob, groups: users }"),
           ("when", "when: ansible_os_family == 'Debian'"),
         ], lab="ansible/extended/labs/playbooks/")
         + _svg("Loop Execution", [
           (60, 80, 150, 55, "#ffe4e6", "#CC0000", "loop list"),
           (240, 80, 150, 55, "#dbeafe", "#3b82f6", "item"),
           (420, 80, 150, 55, "#dcfce7", "#22c55e", "task run"),
           (600, 80, 150, 55, "#fef3c7", "#f59e0b", "next item"),
         ])),
    _tab("flow", "Flow", "Labs 04–05", "Loops and Conditionals Labs",
         flow_html([
           ("Lab 04 loops", "Create multiple users with loop."),
           ("Lab 05 when", "Package task only on Debian family."),
           ("until retry", "Wait for service port with until/until."),
           ("register + when", "Skip based on prior command output."),
         ])),
    _tab("setup", "Setup", "Patterns", "Loop Variables",
         examples_html([
           ("item vs loop", "{{ item }} in loop; ansible_loop.index for index"),
           ("dict2items", "loop: \"{{ mydict | dict2items }}\" — key/value pairs"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Debugging Control Flow",
         _pad_commands([
           ("List tasks", "<code>ansible-playbook site.yml --list-tasks</code>", "Preview order"),
           ("Step", "<code>--step</code>", "Confirm each task"),
           ("Start at", "<code>--start-at-task 'name'</code>", "Resume"),
         ]) + _ref_appendix("Loops", [
           ("loop", "list iteration", "Lab 04"),
           ("when", "ansible_os_family", "Lab 05"),
           ("until", "port open check", "Lab 05"),
           ("failed_when", "rc != 0 custom", "Lab 09"),
           ("include_tasks", "dynamic includes", "Projects"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Labs 04–05",
         examples_html([
           ("Loop lab", "ansible-playbook -i inventory/hosts.ini.local playbooks/loops-packages.yml"),
           ("Conditional", "ansible-playbook -i inventory/hosts.ini.local playbooks/conditionals-os.yml"),
         ], lab="lab04-loops.md · lab05-conditionals.md")),
    _tab("comparison", "Compare", "Decision Guide", "loop vs include_role",
         table_html(["", "loop", "include_role"],
           [["Same task, many items", "Yes", "No"],
            ["Different role per host", "No", "Yes"],
            ["Lab 04", "Users loop", "—"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Loops Practice",
         practice_html([
           ("Lab 04", "Loop over package list.", "../labmanuals/lab04-loops.md"),
           ("Lab 05", "when on OS family and version.", "../labmanuals/lab05-conditionals.md"),
           ("until", "Retry curl until HTTP 200.", "../labmanuals/lab05-conditionals.md"),
           ("dict2items", "Loop over dictionary keys.", "../labmanuals/lab04-loops.md"),
           ("Node.js lab", "Extended playbook lab 03.", "../labmanuals/lab03-nodejs-playbook.md"),
           ("Handlers", "Combine notify with loop.", "../labmanuals/lab06-handlers.md"),
         ])),
  ])

DYNAMIC_INV = _meta("ansible/extended", "dynamic-inventory.html", "Dynamic Inventory — Interactive Guide",
  "Ansible Extended", "Dynamic Inventory", "AWS EC2 inventory plugin — auto-discover instances by tag and region.",
  "Dynamic inventory generates host lists from cloud APIs — eliminating manual IP edits when instances churn.",
  [
    _tab("concept", "Concept", "Core Model", "Inventory Plugins",
         cards_html([
           ("Plugin", "ansible.builtin.aws_ec2 — query EC2 API."),
           ("constructed", "Build groups from instance tags."),
           ("cache", "Inventory cache reduces API calls."),
           ("aws_profile", "Credential chain like AWS CLI."),
           ("hostnames", "Public vs private DNS selection."),
           ("ansible-inventory", "Validate plugin output offline."),
         ])),
    _tab("architecture", "Architecture", "EC2 Plugin", "aws_ec2 Flow",
         examples_html([
           ("aws_ec2.yml", "plugin: amazon.aws.aws_ec2\nregions:\n  - us-east-1\nfilters:\n  tag:Environment: dev\nkeyed_groups:\n  - key: tags.Role\n    prefix: role"),
           ("Run", "ansible-inventory -i aws_ec2.yml --graph"),
         ], lab="ansible/extended/labs/dynamic_inventory/")
         + _svg("Dynamic Inventory", [
           (40, 80, 150, 55, "#ffe4e6", "#CC0000", "aws_ec2.yml"),
           (220, 80, 150, 55, "#dbeafe", "#3b82f6", "EC2 API"),
           (400, 80, 150, 55, "#dcfce7", "#22c55e", "inventory graph"),
           (580, 80, 150, 55, "#fef3c7", "#f59e0b", "ansible-playbook"),
         ])),
    _tab("flow", "Flow", "Lab 07", "Dynamic Inventory Lab",
         flow_html([
           ("Install collection", "ansible-galaxy collection install amazon.aws"),
           ("Configure plugin", "Edit aws_ec2.yml with region and tags."),
           ("Graph", "ansible-inventory -i aws_ec2.yml --graph"),
           ("Ping", "ansible all -i aws_ec2.yml -m ping"),
           ("Playbook", "Run site.yml against dynamic hosts."),
         ])),
    _tab("setup", "Setup", "AWS", "Credentials for Plugin",
         examples_html([
           ("Profile", "export AWS_PROFILE=lab-profile\naws sts get-caller-identity"),
           ("Collection", "ansible-galaxy collection install amazon.aws community.aws"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Dynamic Inventory CLI",
         _pad_commands([
           ("Graph", "<code>ansible-inventory -i aws_ec2.yml --graph</code>", "Host tree"),
           ("List", "<code>ansible-inventory -i aws_ec2.yml --list</code>", "JSON hosts"),
           ("Playbook", "<code>ansible-playbook -i aws_ec2.yml site.yml</code>", "Run against EC2"),
         ]) + _ref_appendix("Dynamic Inv", [
           ("keyed_groups", "tag-based groups", "Lab 07"),
           ("hostnames", "name: private-ip-address", "Lab 07"),
           ("compose", "ansible_host override", "Lab 07"),
           ("cache", "inventory cache plugin", "Performance"),
           ("filters", "tag:Role=web", "Lab 07"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 07 Commands",
         examples_html([
           ("Inventory graph", "cd ansible/extended/labs/dynamic_inventory\nansible-inventory -i aws_ec2.yml --graph"),
           ("Ping dynamic", "ansible role_web -i aws_ec2.yml -m ansible.builtin.ping"),
         ], lab="dynamic_inventory/aws_ec2.yml")),
    _tab("comparison", "Compare", "Decision Guide", "Static vs Dynamic",
         table_html(["", "Static INI", "aws_ec2 plugin"],
           [["IP churn", "Manual updates", "Automatic"],
            ["Lab essentials", "Yes", "Extended"],
            ["AWS coupling", "None", "Required"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Dynamic Inventory Practice",
         practice_html([
           ("Lab 07", "Configure and graph EC2 inventory.", "../labmanuals/lab07-dynamic-inventory.md"),
           ("Tags", "Filter instances by Environment tag.", "../labmanuals/lab07-dynamic-inventory.md"),
           ("keyed_groups", "Create group per Role tag.", "../labmanuals/lab07-dynamic-inventory.md"),
           ("Ping", "Verify SSH to discovered hosts.", "../labmanuals/lab07-dynamic-inventory.md"),
           ("Project", "Extended roles project lab 08.", "../labmanuals/lab08-roles-project.md"),
           ("Cache", "Enable inventory cache; compare speed.", "../labmanuals/lab07-dynamic-inventory.md"),
         ])),
  ])

BREAK_FIX = _meta("ansible/extended", "break-fix.html", "Break-Fix Drills — Interactive Guide",
  "Ansible Extended", "Troubleshooting", "Systematic diagnosis — verbose output, SSH, permissions, syntax, and handler failures.",
  "Break-fix labs intentionally break playbooks so you practice reading <strong>error output</strong> and recovering quickly.",
  [
    _tab("concept", "Concept", "Core Model", "Troubleshooting Layers",
         cards_html([
           ("SSH layer", "Connection refused, key permissions, wrong user."),
           ("Python layer", "Missing python3 on target — ansible_python_interpreter."),
           ("Permission", "sudo requires -b or become: true."),
           ("YAML syntax", "Indentation errors — ansible-playbook --syntax-check."),
           ("Task logic", "when conditions skipping critical tasks."),
           ("Handlers", "Not notified if task reports ok not changed."),
         ])),
    _tab("architecture", "Architecture", "Debug", "Verbose Output Levels",
         examples_html([
           ("verbosity", "ansible-playbook site.yml -vvv  # connection detail\nansible-playbook site.yml -vvvv  # maximum"),
           ("step", "ansible-playbook site.yml --step  # confirm each task"),
         ], lab="ansible/extended/labs/break-fix/")
         + _svg("Debug Workflow", [
           (40, 80, 150, 55, "#ffe4e6", "#CC0000", "error output"),
           (220, 80, 150, 55, "#dbeafe", "#3b82f6", "isolate layer"),
           (400, 80, 150, 55, "#fef3c7", "#f59e0b", "minimal repro"),
           (580, 80, 150, 55, "#dcfce7", "#22c55e", "fix + verify"),
         ])),
    _tab("flow", "Flow", "Lab 09", "Break-Fix Drill Flow",
         flow_html([
           ("Lab 09", "Open broken playbook scenario."),
           ("Reproduce", "Run playbook — capture full error."),
           ("SSH check", "ansible HOST -m ping -vvv"),
           ("Syntax", "ansible-playbook --syntax-check"),
           ("Fix", "Apply minimal fix — one issue at a time."),
           ("Document", "Write root cause in lab notes."),
         ])),
    _tab("setup", "Setup", "Toolkit", "Diagnostic Commands",
         examples_html([
           ("Ping one host", "ansible web1 -i inventory/hosts.ini.local -m ping -vvv"),
           ("List tasks", "ansible-playbook broken.yml --list-tasks"),
           ("Check diff", "ansible-playbook site.yml --check --diff"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Troubleshooting Commands",
         _pad_commands([
           ("Verbose", "<code>-v / -vvv / -vvvv</code>", "Increase detail"),
           ("Syntax", "<code>--syntax-check</code>", "YAML validation"),
           ("Step", "<code>--step</code>", "Interactive stepping"),
           ("Start at", "<code>--start-at-task</code>", "Resume mid-play"),
         ]) + _ref_appendix("Break-Fix", [
           ("UNREACHABLE", "SSH/firewall", "Lab 09"),
           ("FAILED", "task module error", "Lab 09"),
           ("changed=0", "handler won't run", "Lab 09"),
           ("become", "missing sudo", "Lab 09"),
           ("inventory", "wrong host/IP", "Lab 09"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 09 Scenarios",
         examples_html([
           ("Drill", "cd ansible/extended/labs\nansible-playbook -i inventory/hosts.ini.local break-fix/drill-01-broken-yaml.yml"),
           ("After fix", "ansible-playbook -i inventory/hosts.ini.local break-fix/drill-01-broken-yaml.yml --check"),
         ], lab="lab09-break-fix-drills.md")),
    _tab("comparison", "Compare", "Decision Guide", "Symptom → Cause",
         table_html(["Symptom", "Likely cause", "First check"],
           [["UNREACHABLE", "SSH/network", "ping -vvv"],
            ["Permission denied", "SSH key/user", "ssh manually"],
            ["sudo password", "Missing become", "add -b"],
            ["yaml parsing error", "Bad indent", "--syntax-check"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Break-Fix Practice",
         practice_html([
           ("Lab 09", "Complete all break-fix drills.", "../labmanuals/lab09-break-fix-drills.md"),
           ("Time box", "Fix each scenario in under 10 minutes.", "../labmanuals/lab09-break-fix-drills.md"),
           ("Log", "Keep troubleshooting journal.", "../labmanuals/lab09-break-fix-drills.md"),
           ("Pair", "Explain fix to partner — teaching reinforces.", "../labmanuals/lab09-break-fix-drills.md"),
           ("Create break", "Break your own playbook; swap with peer.", "../labmanuals/lab09-break-fix-drills.md"),
           ("Handlers", "Diagnose notify not firing.", "../labmanuals/lab06-handlers.md"),
         ])),
  ])



def _enrich_topic(topic: dict) -> dict:
  """Add depth appendix to commands, examples, and practice tabs."""
  extra_cmds = [
    ("Review", "Re-read lab manual objectives", topic.get("h1", "")),
    ("Validate", "Run syntax-check or validate", "Before apply"),
    ("Cleanup", "Destroy or remove lab changes", "End of session"),
    ("Docs", "Cross-link markdown docs", "../docs/"),
    ("Git", "Commit only safe files", "No secrets/state"),
    ("Pair", "Walk through with teammate", "Teaching reinforces"),
    ("Notes", "Document failures and fixes", "Personal runbook"),
    ("Next", "Follow learning path order", "curriculum/learning-paths.md"),
  ]
  appendix = _ref_appendix(topic["h1"], extra_cmds)
  for tab in topic["tabs"]:
    if tab["id"] in ("commands", "examples", "practice"):
      tab["body"] = tab["body"] + appendix
  return topic


_ANSIBLE_ALL = [
  ANSIBLE_ARCH, INVENTORY_FLOW, ADHOC, PLAYBOOK_HANDLERS, VARS_TEMPLATES, ROLES_VAULT,
  FACTS, LOOPS, DYNAMIC_INV, BREAK_FIX,
]

ANSIBLE_TOPICS: dict[str, dict] = {}
for _t in _ANSIBLE_ALL:
  _enriched = _enrich_topic(_t)
  _key = _enriched["filename"].replace(".html", "").replace("-", "_")
  ANSIBLE_TOPICS[_key] = _enriched

"""Topic page definitions consumed by build_k8s_style_html.py.

Ansible only. The nine Terraform topic definitions that used to live here (plus the
FOUNDATIONS topic in the now-deleted topic_pages_part1.py) were retired in Aug 2026 when the
Terraform track moved to curriculum/gen_terraform_html.py on the shared shell in
curriculum/tf_style.py.

Ansible topics are defined in topic_pages_ansible.py; this module stays as the single
`TOPICS` entry point that build_k8s_style_html.py imports.
"""
from __future__ import annotations

from topic_pages_ansible import ANSIBLE_TOPICS

TOPICS: dict[str, dict] = dict(ANSIBLE_TOPICS)

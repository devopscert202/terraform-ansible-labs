# QA Report — terraform-ansible-labs

**Date:** 2026-07-18 (k8sforbeginners HTML + docs alignment pass)  
**Auditor:** Lead integration + Terraform/Ansible specialist QA  
**Rubric:** [qa-rubric.md](qa-rubric.md)

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Blocker | 0 | Fixed in final pass |
| Major | 0 | — |
| Minor | 1 | Documented below |

**Sign-off:** Ready for instructor use and GitHub Pages publish.

---

## Content expansion (k8sforbeginners alignment)

| Asset | Count | Format |
|-------|-------|--------|
| HTML interactive pages | 23 | helm-charts-overview style: hero + tab views + SVG diagrams (~635–723 lines/topic) |
| HTML catalogs | 4 | k8s index.html style: search + categorized tables |
| Concept docs | 29 | rollout_versions.md style: Objective, sections, Hands-On Labs table (~120–150 lines) |
| Generator | 1 | `curriculum/build_k8s_style_html.py` — regenerate all HTML from topic definitions |

## Content expansion (prior pass)

| Asset | Count | Before | After |
|-------|-------|--------|-------|
| HTML interactive pages | 23 | ~955 lines total; many stubs | **~8,700 lines** — k8sforbeginners-style flows, diagrams, code tabs |
| Lab manuals | 39 | ~6,900 lines | **~16,400 lines** — command-by-command + Validate blocks |
| Concept docs | 30+ | Many 5–75 line stubs | **~8,500 lines** — 250–400 lines per topic |

## 1. Technical accuracy

| Check | Result |
|-------|--------|
| Terraform essentials `terraform validate` (lab02 with SG) | **Pass** |
| Terraform extended `terraform validate` | **Pass** |
| Lab 02 code ↔ manual alignment (SG + ssh_cidr) | **Pass** (fixed) |
| Lab 04 fmt -check expectations | **Pass** (fixed — intentional bad format) |
| Ansible vault CLI flags (`--vault-password-file`) | **Pass** (fixed) |
| `ansible-playbook --syntax-check` | **Skipped** — run on EC2 control node before class |
| No plaintext `access_key` in `.tf` | **Pass** |

## 2. Brevity + completeness

| Track | Manuals | Avg lines | Notes |
|-------|---------|-----------|-------|
| Ansible essentials | 7 | ~500 | Exercise index, Validate every step |
| Ansible extended | 9 | ~420 | Break-fix lab 714 lines |
| Terraform essentials | 8 | ~380 | lab02 EC2 + SG pattern |
| Terraform extended | 15 | ~400 | State suite 500+ lines |

## 3. Language / anti-boilerplate

| Grep pattern | Hits (excl. rubric) |
|--------------|---------------------|
| `Simplilearn` | 0 |
| `42006` | 0 |
| `dbbservers` (as live inventory) | 0 |
| `access_key` in `.tf` | 0 |
| `--encrypt-password-file` | 0 (fixed → `--vault-password-file`) |

## 4. HTML

| Check | Result |
|-------|--------|
| All topic pages ≥250 lines | **Pass** |
| Interactive elements (flows, tabs, cards) | **Pass** |
| External CDN dependencies | **None** |
| Architecture / workflow diagrams | **Pass** |

## 5. Consistency

| Check | Result |
|-------|--------|
| Lab manual count | **39** |
| README counts | Updated |
| FQCN in playbooks | **Pass** |
| Vault password file flag | **Pass** |

## Minor findings

1. **Ansible syntax-check on audit host** — Run before first class on EC2 control node.

---

## Conclusion

Full curriculum expansion complete. HTML, docs, and lab manuals meet k8sforbeginners-quality interactive standards. QA blockers (lab02 SG alignment, lab04 fmt expectations, vault CLI flags) resolved. Repository is **ready as single-source curriculum** for the 20-hour bootcamp.

# QA Rubric

Used by the QA agent before repo sign-off. See [qa-report.md](qa-report.md) for results.

## Categories

1. **Technical accuracy** — commands work; syntax-check/validate pass; no deprecated APIs
2. **Brevity + completeness** — contextual concision; validate every step
3. **Language** — plain English; no vendor boilerplate; zero Simplilearn/LMS references
4. **HTML** — no overlapping elements; consistent colors/fonts; offline self-contained
5. **Consistency** — lab01 numbering; doc↔lab alignment; README counts
6. **Anti-boilerplate** — no TODOs, no duplicate intros

## Grep (must be zero)

`Simplilearn`, `simplilearn`, `42006`, `dbbservers`, plaintext `access_key` in committed `.tf`

## Severity

- **Blocker** — lab broken or policy violation → must fix
- **Major** — misleading content → must fix
- **Minor** — style → fix or document

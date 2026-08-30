# Day-Wise LVC Agenda (Reference)

Four-day instructor-led reference aligned with the source course. The **20-hour bootcamp**
([20-hour-bootcamp.md](20-hour-bootcamp.md)) is the compressed version: it covers Ansible essentials
plus the Terraform Basic tier and the first three Intermediate labs. Days 3 and 4 below reach
further into the Terraform tiers.

The Terraform track is **25 labs, `lab00`–`lab24`**, run in numeric order. Tier is a per-lab
difficulty label: Basic `lab00`–`lab05`, Intermediate `lab06`–`lab12`, Advanced `lab13`–`lab24`.
Concept material for every lab is on one page,
[terraform/html/concepts.html](../terraform/html/concepts.html).

| Day | ~Duration | Focus | Repo path |
|-----|-----------|-------|-----------|
| **1** | ~4 h | CM/IaC intro, inventory, ad hoc, YAML, playbooks (variables) | [ansible/essentials](../ansible/essentials/labmanuals/) lab01–lab05 |
| **2** | ~4 h | Playbooks (loops, conditionals, handlers), roles, vault | essentials lab04–lab07 + [ansible/extended](../ansible/extended/labmanuals/) |
| **3** | ~4 h | AWS concepts, credentials, providers, first EC2, the core workflow, quality gates | [terraform](../terraform/labmanuals/README.md) Basic `lab00`–`lab05` |
| **4** | ~4 h | Variables and secrets, state, modules, the capstone build | terraform Intermediate `lab06`–`lab10` |

Day 4 ends at the capstone rather than at the end of the Intermediate tier. `lab10` builds a
working public web server, which is a better place to stop a taught course than a topic lab, and it
leaves `lab11`–`lab12` as the first self-paced assignment.

## Pre-lab (once)

[AWS lab environment](setup/aws-lab-environment.md) — EC2 control node + target nodes before Day 1.
For the Terraform days, also read the [AWS primer](../terraform/html/aws-primer.html).

## Self-paced topics after Day 4

| Topic | Labs | When to assign |
|-------|------|----------------|
| Facts, dynamic inventory, break-fix | ansible/extended lab01–lab09 | After Ansible essentials |
| Collections and built-in functions | terraform `lab11`–`lab12` | Immediately after Day 4 |
| Multiple providers, provisioners | terraform `lab13`–`lab15` | After the Intermediate tier is complete |
| Workspaces, S3 backend, state keys and locking, migration, remote state | terraform `lab16`–`lab20` | Once the learner works on a team |
| Dynamic blocks | terraform `lab21` | With, or just before, `lab22` |
| The capstone rebuilt with state in S3 | terraform `lab22` | As the synthesis exercise, after remote state |
| An S3 bucket as a managed resource | terraform `lab23` | Last, closing the track |

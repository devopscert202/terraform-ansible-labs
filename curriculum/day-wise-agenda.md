# Day-Wise LVC Agenda (Reference)

Four-day instructor-led reference aligned with the source course. The **20-hour bootcamp**
([20-hour-bootcamp.md](20-hour-bootcamp.md)) is the compressed version: it covers Ansible essentials
plus the Terraform Basic tier and the first three Intermediate labs. Days 3 and 4 below reach
further into the Terraform tiers.

| Day | ~Duration | Focus | Repo path |
|-----|-----------|-------|-----------|
| **1** | ~4 h | CM/IaC intro, inventory, ad hoc, YAML, playbooks (variables) | [ansible/essentials](../ansible/essentials/labmanuals/) lab01–lab05 |
| **2** | ~4 h | Playbooks (loops, conditionals, handlers), roles, vault | essentials lab04–lab07 + [ansible/extended](../ansible/extended/labmanuals/) |
| **3** | ~4 h | AWS concepts, credentials, providers, first EC2, the core workflow, quality gates | [terraform](../terraform/labmanuals/README.md) Basic `lab00`–`lab05` |
| **4** | ~4 h | Variables and secrets, state, modules, collections, functions, dynamic blocks | terraform Intermediate `lab06`–`lab12` |

## Pre-lab (once)

[AWS lab environment](setup/aws-lab-environment.md) — EC2 control node + target nodes before Day 1.
For the Terraform days, also read the [AWS primer](../terraform/html/aws-primer.html).

## Self-paced topics after Day 4

| Topic | Labs | When to assign |
|-------|------|----------------|
| Facts, dynamic inventory, break-fix | ansible/extended lab01–lab09 | After Ansible essentials |
| Multiple providers, provisioners | terraform `lab13`–`lab15` | After Terraform Intermediate |
| Workspaces, S3 backend, state keys and locking, migration, remote state | terraform `lab16`–`lab20` | Once the learner works on a team |
| Capstone — VPC, IGW, subnet, route table, SG, EC2 web server | terraform `lab21` | Last, as the synthesis exercise |

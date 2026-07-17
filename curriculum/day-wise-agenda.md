# Day-Wise LVC Agenda (Reference)

Four-day instructor-led reference aligned with the source course. The **20-hour bootcamp** ([20-hour-bootcamp.md](20-hour-bootcamp.md)) covers only essentials; use extended tracks for full LVC parity.

| Day | ~Duration | Focus | Repo path |
|-----|-----------|-------|-----------|
| **1** | ~4 h | CM/IaC intro, inventory, ad hoc, YAML, playbooks (variables) | [ansible/essentials](../ansible/essentials/labmanuals/) lab01–lab05 |
| **2** | ~4 h | Playbooks (loops, conditionals, handlers), roles, vault | essentials lab04–lab07 + [ansible/extended](../ansible/extended/labmanuals/) |
| **3** | ~4 h | IaC on AWS, Terraform workflow, state intro | [terraform/essentials](../terraform/essentials/labmanuals/) lab01–lab06 |
| **4** | ~4 h | Variables, modules, remote state, functions | essentials lab05–lab08 + [terraform/extended](../terraform/extended/labmanuals/) |

## Pre-lab (once)

[AWS lab environment](setup/aws-lab-environment.md) — EC2 control node + target nodes before Day 1.

## Extended self-paced topics

| Topic | When to assign |
|-------|----------------|
| Facts, dynamic inventory | After Ansible essentials |
| Remote state, provisioners, capstones | After Terraform essentials |

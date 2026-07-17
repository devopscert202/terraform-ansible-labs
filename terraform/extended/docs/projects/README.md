# Project design and capstones

A Terraform project should have a narrow ownership boundary, a dedicated state key, explicit provider constraints, and repeatable inputs. Start with a small network or service boundary, then add outputs that consumers need rather than exposing every resource detail.

Use workspaces only when configurations remain substantially the same; use separate root modules and state for materially different environments. Tag cloud resources consistently and plan destructive changes in a reviewed workflow.

Before calling a project complete, run formatting, initialization, validation, a reviewed plan, apply only with correct authorization, and destroy temporary training infrastructure.

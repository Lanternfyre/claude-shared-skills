---
role: maintainer
model: opus
night: yes
paths: plugins/**, templates/**, docs/**, README.md, .claude-plugin/**, .beads/config.yaml
---

# Maintainer

## Purpose

Builds and fixes the shared skills: the beadwork and docs plugins, their scripts, the templates and the documentation standard. Hands finished work to the operator as one PR per bead, behind a merge gate.

## Never

- Edit CLAUDE.md or anything under .claude/: they govern the session itself.
- Change a skill's behaviour without bumping its plugin version.
- Put a project name, host or credential into a skill.

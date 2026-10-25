# Page kinds

Pick one per page. The bullets under each kind are prompts, not required headings: leave out what doesn't apply.

**Reader pages**, one dominant purpose each:
- **Tutorial** (`start/`): teaches by guiding a learning exercise. Who it is for, the starting point, ordered steps with checkpoints, the end result, what to read next. A first success matters more than full detail.
- **How-to** (`guides/`): reaches one goal. Title "How to …"; prerequisites; numbered steps; how to verify the outcome; pitfalls and recovery. Doesn't teach the whole system or repeat reference.
- **Runbook** (`operate/`): an operational how-to. Symptoms; when it applies and who runs it; privileges needed; safe steps; verification; rollback and escalation; related alerts. Say whether each step has actually been tested.
- **Reference** (`reference/`): exact facts. Scope, version and source of truth, then the contract, parameters and constraints. Prefer generated sources: OpenAPI exports, schema and migration links, the real config declarations.
- **Explanation** (`architecture/`, `domain/`): why it works this way. The concept, its mechanics and boundaries, trade-offs, one meaningful example, links to the reference and the ADR.

**Knowledge pages:**
- **Capability** (`capabilities/`): the problem and outcome; actors; current behaviour and its boundaries; requirements (REQ, each verifiable); key scenarios; links to flows, architecture and APIs; known limits and non-goals.
- **Flow** (`flows/`): trigger and outcome; actors; main steps; failure paths that matter; one sequence diagram; links to the requirements, components and contracts involved. A flow may cross many services.
- **Component or architecture** (`architecture/`): responsibility; boundaries; what it depends on and what depends on it; owned data; interfaces and events; operational impact. Describe what is real now, and mark target designs as such.
- **Quality requirement** (`requirements/`): NFR id, a measurable statement, scope, rationale, how it is verified, and status. "Must be scalable" is not a requirement; "p95 under 200 ms at 500 rps" is.
- **Planning** (`planning/`): proposed outcome, assumptions, dependencies, uncertainties, decision points. Never phrased as built.
- **Objectives, glossary, ADRs:** use `/docs:objectives`, `/docs:glossary` and the `adr` skill.

Requirements, ADRs and plans are governance pages. They are not forced into one of the four reader kinds.

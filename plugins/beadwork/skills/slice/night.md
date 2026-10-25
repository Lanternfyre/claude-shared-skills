# Night run (unattended)

- **Backlog rule:** start only with at least as many ready beads for your role as the session-start status line asks for ("a night run needs N ready"), and only when the away switch is off. Otherwise, stop.
- **No cards at night.** A push at 3 am wakes the operator. File decision beads as usual and store their cards in metadata (`auq_card`); the morning grill asks them.
  - **default-ok:** proceed provisionally.
  - **must-ask:** park the bead and take the next.
- **Loop** the slice until one of these happens: nothing is ready, you hit a usage limit, or a stop rule fires.
- **On stop,** file one summary for the morning grill:

```bash
bd create -t chore -l human,morning-summary --title "Night summary <date> <role>" \
  --body-file summary.md --validate --silent
```

`summary.md`:
- **Task:** "Morning read of the night run."
- **Guardrails:** "Read-only."
- **Acceptance Criteria:** "The operator has read it; the grill closes it."
- **Summary:** what got done (PR links); what is parked and why; provisional defaults taken (question ids); surprises filed; why the run stopped.

# Night session (unattended)

The night loop (`scripts/night-run.sh`, started by the homelab job) runs one fresh session per bead with `/beadwork:slice night`. Between sessions it checks the stop rules: the 06:00 cutoff, the review cap, the verify command, the role card's `night: yes`, whether any night-ok bead is left, the usage limit, and failures. **A night session does one bead, then exits.**

1. **Steps 1–2 as by day.** The stack comes first ([stack.md](stack.md)), and you read the bead's progress record and new comments. The away switch does not stop you.
2. **Claim one night-ok bead.** Add `--label night-ok` to the claim in step 3, also when claiming a bead blocked only by your own stack. If nothing is claimable, end with `BEADWORK-NIGHT: nothing - -`.
3. **Work it as by day** (steps 4–7): the plan written into the notes before building, the progress record at each milestone, the role fence, a PR on the stack, the merge gate. Nobody approves the plan at night either; the operator reads it in the morning.
4. **Never at night:**
   - merge any PR;
   - push to the main branch;
   - change live systems (kubectl, helm, database commands);
   - delete branches, tags, data or history, except your own spike branches;
   - touch CI, workflows, secrets or permissions;
   - edit role cards, `CLAUDE.md`, or the skills this session runs on.

   A pre-push hook in the checkout refuses pushes to the default branch and branch deletions.
5. **Questions:** no cards at night, because they would wake the operator. File decision beads as usual and store each card in metadata (`auq_card`); the 08:00 morning card asks them.
   - **default-ok:** go ahead on the default, label the question `provisional`, and name it in the PR body.
   - **must-ask:** park the bead with a full progress record, and end with `BEADWORK-NIGHT: parked <id> -`.
6. **End with exactly one status line**, then stop. The loop builds the morning summary from these lines; never write one yourself.
   - `BEADWORK-NIGHT: pr <id> <PR URL>`: handed to review.
   - `BEADWORK-NIGHT: fixed <id> <PR URL>`: you only looked after the stack (red CI, review feedback).
   - `BEADWORK-NIGHT: parked <id> -`: parked with a progress record.
   - `BEADWORK-NIGHT: blocked <id> -`: a tripwire, or two red runs you could not explain.
   - `BEADWORK-NIGHT: nothing - -`: nothing claimable.

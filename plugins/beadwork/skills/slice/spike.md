# Spike bead

A spike answers a level-4 question with measurements, not opinion. Its code never merges.

1. **Read** the bead's Variants (2–3) and Measurements. Every variant runs the same measurements: same input, same machine, same command.
2. **Per variant `x`:**
   - Work on branch `spike/<id>-x`, inside the time box (the bead's, or 2 h per variant).
   - Build the smallest thing that can be measured, and run the measurements.
   - Add the results row with `bd note <id>`.
3. **Results:** one table in the notes (variant × measurement), plus what surprised you.
4. **Ask:** file a level-3 decision through the `question` skill, as a `tradeoff` card with the numbers, using `--deps discovered-from:<id>`. Then `bd close <id> --reason "results in notes; decision <qid>"`. A spike has no PR, so it is the one bead you close yourself.
5. **After the answer:** rebuild the winner as a normal bead (the `bead` skill), from scratch on a normal branch. Delete the spike branches.

**Budget:** one spike per epic or milestone, unless the operator approves more.

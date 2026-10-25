# Bug bead

The bead's Steps to Reproduce say what is wrong. Change no code until a command goes red on it.

1. **Build a feedback loop first.** Find one command that drives the real bug path and asserts the reported symptom, not merely "it didn't crash". In rough order of preference:
   - a failing test at a seam that reaches the bug;
   - a curl or CLI script run against a fixture;
   - a replay of a captured payload;
   - a throwaway harness;
   - a fuzz loop, for "sometimes wrong";
   - `git bisect run`, when the bug appeared between two known states.

   Make it fast and deterministic: pin the time, seed the randomness, isolate files and network. For a flaky bug, raise the reproduction rate (loop it, parallelise, add stress) until you can debug it. If you can't build a loop, stop: note what you tried, and ask through the `question` skill for access or a captured artifact. Don't form theories without a loop.
2. **Minimise.** Cut inputs, steps and config one at a time while the loop stays red, until every remaining element is needed.
3. **Hypothesise.** Note 3–5 ranked hypotheses on the bead before testing any. Each makes a prediction: "if X is the cause, changing Y makes the bug vanish."
4. **Instrument** one variable at a time, each probe testing a prediction. Tag every debug log with one prefix (`[DEBUG-a4f2]`) so cleanup is one grep. For performance bugs, measure a baseline first, then bisect.
5. **Gate.**
   - Find a seam where a test reproduces the bug as it really happens. If there is none, that is the finding: file a surprise bead, because the design keeps this bug from being locked down.
   - Commit the failing test on its own, then the fix as a separate commit. Fix only what makes the test pass.
   - Add tests for the sibling cases the bug implies: other error paths, the adjacent input.
   - Re-run the original, un-minimised loop. The minimal test passing doesn't prove the reported problem is gone.
6. **Clean up.** Remove the tagged debug logs and throwaway harnesses. The PR names the hypothesis that proved true.

Redact secrets (`<REDACTED>`) in everything you show or note. Never weaken or delete an existing test to make yours pass.

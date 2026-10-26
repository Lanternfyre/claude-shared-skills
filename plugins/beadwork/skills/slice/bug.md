# Bug bead

Establish evidence for the reported failure and verify the fix against that behavior. Prefer a failing regression test before changing production code, using the smallest reliable feedback loop: a test, fixture-backed CLI request, replay, harness or stress case.

- For an obvious defect, reproduce, fix and verify directly. Ranked hypotheses and instrumentation help when the cause is unclear; do not invent a fixed number of theories.
- Minimize a complex reproduction enough to isolate the cause. Keep the original scenario to check the final fix.
- If reproduction needs unavailable access or data, record what is known and what remains unverified. Continue useful inspection or safe investigation; ask for the missing input only when it blocks progress. Do not claim an unobserved red-to-green result.
- Add regression coverage where feasible, including meaningful sibling cases. Do not weaken tests or add assertions that merely mirror the implementation. Separate red/fix commits are optional; follow the project's commit convention.
- For intermittent or performance bugs, compare against a measured baseline with comparable inputs and conditions.
- Remove temporary instrumentation and test artifacts. Delivery evidence states the cause, reproduction, verification and any remaining limits.

Keep secrets out of captured payloads, logs and notes. A bug that exposes missing test seams may justify a follow-up; it does not require abandoning a verified fix.

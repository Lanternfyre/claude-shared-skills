# Reader checks proportional to the change

Check whether the changed documentation answers its reader's question. Choose the check by impact:

- **Small factual, typo, formatting or link correction:** the author checks the changed passage against its source and follows affected links. Report a focused check. No fresh agent is required.
- **New pages, changed navigation, or substantive changes to architecture, security, operations, business rules or public guidance:** use one fresh reader for the change set, not one per file or edit. Pick the affected reader tasks; two or three usually suffice.
- **Milestone or `/docs:audit readers`:** include the operator's real reader tasks. Agent results do not substitute for human sign-off where it is required.

## Independent walkthrough

Give a read-only agent the tasks without explaining the intended route:

> You have never seen this project. Start at `README.md` in `<repo path>`. Open a file only by following a link from a page you have already read: no searching, no listing folders. Try these tasks: `<tasks>`. For each, report done or not done, the page titles you passed through, where you got stuck, unexplained terms, and claims whose built/planned status is unclear. Do not fix anything or change files, branches or Beads.

Tasks describe a reader's need, not a path: "Get this running", "Find the refresh-token expiry rule", or "Recover a failed nightly backup and verify recovery".

If delegation is unavailable or forbidden, perform the route check yourself and report that it was not independent. Arrange owner review where required; do not pretend a fresh reader ran or stop unrelated implementation.

Fix failures introduced by this change or necessary for its reader's task. File unrelated pre-existing gaps separately. An affected task that still fails remains `needs review`, unless the owner accepts a specific exception. Report the result in `Readers:` separately from the structural check.

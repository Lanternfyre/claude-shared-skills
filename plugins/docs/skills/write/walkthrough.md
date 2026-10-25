# Reader walkthrough (fresh agent)

Run this on every change to docs pages. It is one sub-agent per change, the only one the documentation standard asks for. The operator does the same tasks by hand at milestones, through `/docs:audit`.

1. **Pick 2–3 tasks** for the readers this change serves. Write each as something a reader wants, never as a path.
   - **Newcomer:** "Find out what this is and get it running."
   - **Change:** "Find where refresh-token expiry is decided and which requirement covers it."
   - **Operate:** "The nightly backup failed. Find the safe recovery steps and how to confirm it worked."
   - **External user:** "Find how to list orders through the API and which errors to expect."
2. **Spawn one fresh agent** (the Agent tool, `Explore` type) with this prompt, filling in the tasks:

   > You have never seen this project. Start at `README.md` in `<repo path>`. Open a file only by following a link from a page you have already read: no searching, no listing folders. Try these tasks: `<tasks>`. For each task, report: done or not done; the page titles you passed through; where you hesitated or got lost; any term that was used before it was explained; any claim where you couldn't tell whether it is built, planned or uncertain. Do not fix anything.

3. **Record** the result on the PR's `Readers:` line.
   - Fix failures that fall within the change.
   - File a bead for the rest (`topic:docs`).
   - Never call the docs ready while a reader task fails without an accepted exception.

An agent reader catches dead ends, missing links and unexplained terms. It does not catch what confuses people; that is why the operator walks the same tasks at milestones.

# Cutting a plan into beads

Turn an approved outcome, plan or milestone into a graph of beads. Existing authorization covers decomposition; ask only for decisions that change what is being promised.

**A bead is a vertical slice.** It goes through every layer it needs and lands one thing a person can check. If you can't write one sentence saying what someone could check when it lands, you cut a layer, not a slice.

| Looks like a bead | Why it isn't | Instead |
|---|---|---|
| a layer ("the DTOs", "the schema") | nothing observable lands | fold it into the first slice that needs it |
| a bundle ("settings + push + licences") | several outcomes in one | cut it into its parts |
| an endless chore ("clean up tests") | never done | bound it: name the files and the finish |

A wide refactor is three beads, each merging green on its own:
1. **Expand:** add the new shape beside the old.
2. **Migrate:** move the callers.
3. **Contract:** delete the old shape.

## Steps

1. **Read the source:** the plan's intended outcome, relevant decisions, objectives and ADRs. Use the `question` skill for unresolved choices the operator owns; routine implementation choices belong to the builder. Add a blocking dependency only where the answer is genuinely required before work can proceed.
2. **Draft the cut.** One line per slice: title, what lands, expected scope, protected boundaries and size. Start with the thinnest end-to-end path, then widen. Size by outcome, not by session: a slice may take several sessions or PRs.
3. **Edges.** A slice depends on another only if it cannot be built or verified without it, not because it "feels later". Fewer edges mean more work in parallel.
4. **Check authority.** If the outcome is authorized, record the cut and proceed. If the proposal changes scope, acceptance criteria or commitments, ask about those changes as one batch through the `question` skill. Keep independent authorized work moving. A request for a proposal only is not authorization to implement it.
5. **Create.**
   - Create the epic if it is missing ([epic.md](epic.md)).
   - Create each bead with its full sections (the `bead` skill), using `--parent <epic>`.
   - Add the edges with `bd dep add` once every bead exists.
6. **Verify the graph you built, not the one you meant.** `bd graph <epic> --compact` must preserve the approved outcome and cover every criterion. Check that the intended first slices appear in `bd ready`, with no accidental blockers or cycles. Other epics' ready work may appear too.

Keep design and roadmap documents in their established homes and link them. Beads owns live execution status; adopting it does not require rewriting existing plans or maintaining duplicate status tables.

# Cutting a plan into beads

Turn an epic, a plan or a milestone into a graph of beads, approved by the operator as one card.

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

1. **Read the source in full:** the plan, its decisions, and the objectives and ADRs it touches. Anything still undecided becomes a decision bead first (the `question` skill), and the slices that depend on it get a dep on it.
2. **Draft the cut.** One line per slice: title, what lands (the check), scope fence, size. Start with the thinnest end-to-end path, then widen.
3. **Edges.** A slice depends on another only if it cannot be built or verified without it, not because it "feels later". Fewer edges mean more work in parallel.
4. **Ask once, create nothing yet.** Post the cut as one auq `tasks` card: for each slice its id, title, `required` or `optional`, deps, and `ready` or `blocked`. The `context` says what the epic delivers and your recommended order.
5. **Create.**
   - Create the epic if it is missing.
   - Create each bead with its full sections (the `bead` skill), using `--parent <epic>`.
   - Add the edges with `bd dep add` once every bead exists.
6. **Verify the graph you built, not the one you meant.** `bd graph <epic> --compact` must match the approved card. `bd ready` must show exactly the first slices.

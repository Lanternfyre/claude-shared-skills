# Prose that reads like a person wrote it

Use plain US English and active voice. Name the actual thing, and make claims you can back. Use short paragraphs, and tables only to compare facts.

| Avoid | Write instead |
|---|---|
| "In today's fast-paced world, efficient order handling is crucial. This page provides a comprehensive overview of the order placement process." | "Placing an order reserves stock and charges the card in one step. If either fails, nothing is kept." |
| A heading that repeats the title, then a paragraph that repeats the heading | Start with the answer |
| "This robust, scalable solution seamlessly integrates with the system." | "The worker retries a failed charge three times, 30 s apart, then marks the order Failed." |
| "In conclusion, this approach ensures reliability and maintainability." | End when the content ends. Add a "Next" link if there is a natural next step. |
| A four-column table restating three sentences | The three sentences |
| `## REQ-000123 — POST_/orders — Orders.Service` | `## Placing an order`, with the id in an anchor and a small line below |
| A page that is one large diagram | A question-led title, two lines on the system boundary, the diagram, then two sentences on the key flow and what the diagram leaves out |
| Navigation named "REQ registry", "Agent knowledge", "Page metadata" | Start, Build, Operate, Reference, Architecture, Decisions |
| "TBD", generic filler, or invented examples to fill a template | A short page with the known facts, plus open questions where they matter |
| "It should probably handle most cases." | Say what it handles, or "Unverified: not tested beyond single-region." |

**Rewrite test:** delete each sentence in turn. If the reader loses nothing, the sentence stays deleted. Keep the precise semantics, the limits and the causal explanation; those are never fluff.

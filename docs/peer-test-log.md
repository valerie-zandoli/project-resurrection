# Peer-test log

One entry per outside tester.  A tester reads `docs/architecture.md` and `docs/agent-handoffs.md` cold and answers three questions:  which handoff has unclear contents, which role has no owner, and which shared state has no named writer.

## 2026-10-22:  Abheeshu Dhungana (Slack group chat)

### What the peer observed

An overall assessment instead of the three answers.
- Strong points:  contract-first design, a solid test suite, the 3-round cap, and clean git hygiene.
- In progress:  contracts versus runtime, and biological complexity.
- A second message said the app will help humans understand predator-prey ratios and that AI could compare animal numbers as a group.
- He named no unclear handoff, no ownerless role, and no shared state without a writer.
- He counted "60+ unit tests"; the suite has 47 in the required check.  We do not act on that figure.

### What we changed afterwards (our own fixes, apart from his observations)

- He read the project as an AI tool that compares predator and prey numbers, so the documents did not say clearly what the agents are.  We added "In plain words" to `docs/architecture.md`, which separates the three AI roles, the harness, the simulated lynx, and the coding assistants, and says that rabbits are a fixed food amount in this version.
- He saw "contracts, not runtime", and the documents did not say it up front.  The same section now lists what is built and what is planned.
- We added "The three handoffs", "Who owns what", and "The shared state and who writes it", so that the three questions are answered in the documents themselves.

### Not yet shown

These fixes are ours.  They do not show that a new outside reader can answer the three questions; only another cold read can show that.

### Still open

Wil Sheppard has not replied (due Friday 2026-10-23 at 18:00 ET).  The return review of their design is owed once they send a link.

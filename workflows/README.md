# workflows/

Markdown SOPs that define what to do and how. Each workflow should cover:

- **Objective** — what the workflow accomplishes
- **Required inputs** — what the agent needs before starting
- **Steps** — which tools to run, in what order
- **Expected outputs** — where results end up (usually a cloud service, not `.tmp/`)
- **Edge cases** — known failure modes and how to handle them

Workflows evolve as tools improve or new constraints are discovered — update them in place rather than leaving stale instructions. Don't create or overwrite a workflow without asking first, unless explicitly told to.

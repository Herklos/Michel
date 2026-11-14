# CLAUDE.md: preparation rules for michel

Read this before you change anything in this repo. These rules come from the documentation audit in `docs/audit/2026-11-14-doc-audit.md`.

## 1. Before you start

1. Run `git status` and `git log --oneline -5`. Know what is already uncommitted.
2. Read `docs/architecture/README.md`, then every page your change touches. The pages are the design. The code implements a subset, and each page labels which parts.
3. Read the open questions in `docs/architecture/15-roadmap-and-gaps.md`. Do not decide one of them silently. If your change depends on one, stop and ask (see section 8).
4. Check `docs/spikes.md`. If your work answers a spike, say so in the change and update the spike's status.
5. Run the tests: `python -m pytest -q`. The baseline is 22 passing tests. A change that breaks them is not finished.
6. Run the docs checker: `python scripts/check_docs.py`. It must report 0 problems before you finish a docs change.

## 2. Status labels

Every statement about a feature carries one of these labels, and the label must match the code.

| Label | Meaning |
|---|---|
| **[implemented]** | in `michel/` and tested offline |
| **[designed]** | decided in the docs, not in code |
| **[verify]** | depends on a Temporal or deepagents behaviour that no test has run against a server |

When you implement something, change its label in every page that mentions it, in the same change. When you find a page that says "implemented" for code that does not exist, fix the page first.

## 3. Keep the docs in step

- A design change updates the page that owns it, plus every page that cites it. Use `grep -rn "<term>" docs/architecture` to find them.
- A new decision is an ADR in `docs/architecture/14-decisions.md`. Status is **accepted**, **proposed** or superseded. Update the ADR range in `docs/architecture/README.md`.
- A new requirement gets an F or N number in `01`, and a phase in `15`. A requirement without a phase is a gap.
- A new page in `docs/architecture` gets a row in `docs/architecture/README.md`.
- Retired names go into `STALE` in `scripts/check_docs.py`. Current retired names: `grokbot` (now `michel`), `docs/research/temporal-deepagents/`.

## 4. Names

- The product is **michel**. The package is `michel/`. Do not reintroduce `grokbot`.
- "Michel" in the research notes can also mean Herklos's own project. Write "Michel (Herklos)" when it is not this repo.
- Open SWE is now named **Robin** in its own repo. Say "Open SWE (Robin)" once, then either name is fine.
- "Grok Bot" is the competitor product. Keep that name for it.
- The workflow id scheme in code is `bot-{name}-{hex}`. The design uses `thread:{tenant}:…`. A page that mentions one must say which.

## 5. Code rules

- **Workflow code is deterministic.** Inside workflow modules, do not call `datetime.now`, `random`, `uuid.uuid4`, `os.environ`, or any I/O. Use `workflow.now()` and the SDK helpers. Put I/O in activities. Import SDK and third-party modules inside `workflow.unsafe.imports_passed_through()` where the workflow needs them.
- **Secrets stay on the worker.** Keys and webhook URLs are read through `worker_settings()` in activities or tools. They never go into workflow input, activity arguments, workflow state or history.
- **One configuration registry.** Read every environment variable through `michel/config.py`. Document each new variable in the README configuration table in the same change.
- **Policy is read from a pinned or default source**, never from the content it governs (ADR-015 in `14`, proposed). A tool grant, an approval rule or a budget comes from the bot or procedure version.
- **Commands are decided without I/O; effects run after the decision** (ADR-014, proposed). An update validator must not perform I/O.
- **Pins move together.** `temporalio==1.36.0`, `temporalio-deepagents==0.0.3`, `deepagents==0.7.38` are pinned in `pyproject.toml`. Any upgrade needs a replay test and an update to `05` and `12`.
- **Dependencies used by code must be declared.** If you import a package, it goes in `pyproject.toml`. For example, `opentelemetry-sdk` is needed by `temporalio.contrib.opentelemetry` and is not declared yet (spike S-22).
- **Side-effect tools are idempotent or approval-gated.** `deliver_channel_message` requires approval (`michel/agent.py`, `APPROVAL_REQUIRED`). Any new tool with an external effect needs the same, or an idempotency key.
- **No silent truncation.** A limit returns an explicit error or a visible marker (`08`, memory rules). The current transcript cap (`MAX_TRANSCRIPT_ITEMS`) is a known exception, tracked as S-29.
- **Tests run offline by default.** A test that needs a Temporal server is marked and skipped when no server is present.

## 6. Research rules

- Every external claim has a source in `docs/research/`: the URL or package, the date read, and what was and was not read. If a source could not be read, say so in the note.
- Before you write "X's rule" or "Y's pattern" in a design page, check the research note says so. The audit found three misattributions. Cite the file and section.
- Mark a claim you could not check **[verify]**.
- New peer products go in `docs/research/<topic>/` with a `README.md` index, and in the table in `docs/research/README.md`.
- Access status changes: when a site becomes reachable, update the note and `docs/research/README.md`. Do not leave a "could not be read" statement after a successful read.

## 7. Working in the repo

- Keep scratch files in the session scratchpad, not in the repo.
- Do not commit or push unless the user asks. Do not open a pull request unless the user asks.
- Commit messages end with the attribution lines given in the session instructions.
- Do not send personal details, the user's email, or internal names to external services.
- Do not add outbound hosts or MCP servers to the environment without a concrete need.

## 8. Ask before you decide

These are the user's decisions. Do not settle them in code or in a design page without asking:

1. Hosted or self-hosted first (`15`, question 2).
2. First channel, Slack or GitHub (`15`, question 3).
3. Whether a web client is in scope for phase 1 (`15`, question 4).
4. Whether ADR-005 (async subagents as child workflows) is accepted (`14`).
5. Payload encryption required by policy (`15`, question 6).
6. Approved Temporal version and deployment (`15`, question 7).
7. Procedure authoring format (`16`, question 1).
8. CEL or a custom grammar for conditions (`16`, question 2).
9. Whether a free-form chat bot is a product on its own (`15`, question 9).

If the goal artifact (`https://claude.ai/artifact/Hhff31XsAZSJFPar424KwJ`) becomes readable, reconcile `01`, `15` and `16` with it before any of these are decided.

## 9. Before you finish

- `python -m pytest -q` passes.
- `python scripts/check_docs.py` reports 0 problems.
- Every changed statement has the right label (section 2).
- Any spike you resolved is updated in `docs/spikes.md`.
- Your summary to the user lists what you changed, what you did not, and what needs a decision.

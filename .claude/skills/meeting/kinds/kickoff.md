# Kickoff

Starts a new project from the template. No pack: the chief engineer interviews the owner, one topic at a time, writes drafts during the meeting and reads them back. Before: `scripts/setup.sh` has run.

## Agenda

1. **Goal and scope:** the product, why it is built, what is out of scope, the owner's goals (e.g. learning, demonstration, build and fly).
2. **Owner constraints:** given products, hardware, money, time, operating facts (crewed or uncrewed, mass class, VLOS or BVLOS, area). Each becomes an owner-constraint requirement.
3. **ConOps:** mission, environment, operations, users, phases of flight. Drafted from the answers and read back.
4. **Regulatory basis:** proposed by `safety-engineer`; the owner chooses.
5. **Verification means:** analysis, simulation, test bench, flight tests planned or not. Requirements only a flight can verify are recorded as such.
6. **Team:** which agents of `.claude/agents/` the project uses; agents to delete or add.
7. **Phases, milestones, gates, budgets:** tailor the default phases in `project-plan.md`; budgets in 5-hour usage windows, kept in `timeline.md`.
8. **Risks:** the first entries of `risks.md`, from the owner's view and the chief engineer's.
9. **Ways of working:** shift yes or no and its host, notifications, review depth.

## Outcome

* The system item: `plm new assembly "<System title>"` at the repository root, with `conops.md` as artifact and its stakeholder needs as requirements in `requirements/stakeholder-needs/`; drafted by the chief engineer in the meeting, owned by `systems-engineer` from then on.
* `project-plan.md` filled from its template, and `risks.md` with the first risks.
* The owner-constraint requirements (owner `systems-engineer`) and a `DEC-…` for the regulatory basis (owner `safety-engineer`).
* `.claude/agents/`, `schemas/meta.schema.json` and the owner list of `.github/ISSUE_TEMPLATE/work-package.yml` trimmed to the team (`scripts/check.py` checks they agree).
* GitHub milestones for every milestone and gate: `gh api repos/{owner}/{repo}/milestones -f title="<name>"`.
* `timeline.md` filled: all phases, milestones and gates with their budgets; the first milestone (usually SRR) active with its entry conditions.
* `handover.md` filled: system item, owner directions with their DEC IDs, next step.
* The MTG record of the kickoff in the system item, with `minutes.md`.

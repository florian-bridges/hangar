# Kickoff

Starts a new project from the template. No pack: the chief engineer interviews the owner, one topic at a time, writes drafts during the meeting and reads them back. Before: `scripts/setup.sh` has run.

## Agenda

1. **Goal and scope:** the product, why it is built, what is out of scope, the owner's goals (e.g. learning, demonstration, build and fly).
2. **Owner constraints:** given products, hardware, money, time, operating facts (crewed or uncrewed, mass class, VLOS or BVLOS, area). Each becomes an owner-constraint requirement.
3. **ConOps:** mission, environment, operations, users, phases of flight. Drafted from the answers and read back.
4. **Regulatory basis:** proposed by `safety-engineer`; the owner chooses.
5. **Verification means:** analysis, simulation, test bench, flight tests planned or not. Requirements only a flight can verify are recorded as such.
6. **Team:** which agents of `.claude/agents/` the project uses; agents to delete or add.
7. **Phases, milestones, gates, budgets:** tailor the phase list below; budgets in 5-hour usage windows, kept in `timeline.md`.
8. **Ways of working:** shift yes or no and its host, notifications, review depth.

## Outcome

* The system item: `plm new assembly "<System title>"` at the repository root, with `conops.md` and `project-plan.md` as artifacts (headings below), and its stakeholder needs as requirements in `requirements/stakeholder-needs/`.
* The owner-constraint requirements and a `DEC-…` for the regulatory basis.
* `.claude/agents/` and `schemas/meta.schema.json` trimmed to the team.
* GitHub milestones for every milestone and gate: `gh api repos/{owner}/{repo}/milestones -f title="<name>"`.
* `timeline.md` filled: all phases, milestones and gates with their budgets; the first milestone (usually SRR) active with its entry conditions.
* `handover.md` filled: system item, owner directions with their DEC IDs, next step.
* The MTG record of the kickoff in the system item, with `minutes.md`.
* The branch `develop` created from `main` and pushed.

## Default phases (tailor at the kickoff)

| Phase | Content | Ends with |
|---|---|---|
| System requirements | Needs, ConOps, system-level requirements, verification methods, requirements of the verification environment | **SRR** |
| Concept and architecture | Trade studies, baseline sizing, breakdown, allocation, interfaces | milestone *System design* |
| Verification environment | Simulation backbone, models validated within stated limits | milestone *Sim ready* |
| Preliminary design | Subsystem requirements, preliminary designs, budgets, a test case per requirement | **PDR** |
| Implementation and integration | Functions in simulation, then on the test bench | milestone *Integrated* |
| Detailed design | Buildable design: CAD, structural analysis, wiring, parts list, closed budgets | **CDR** |
| Verification | All test cases on the CDR configuration, coverage, verification report | milestone *Verification complete*, then close-out |

## `project-plan.md` headings

1. Goal · 2. Given decisions and resources · 3. Team · 4. Phases · 5. Phase content · 6. Reviews and gates (entry and exit criteria) · 7. Risks. The schedule and budgets are in `timeline.md`, not here.

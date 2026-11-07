# Project plan

Kept by the chief engineer; changed with the owner's agreement in a meeting. Filled at the kickoff from this template. Budgets and state: `timeline.md`. Risks: `risks.md`.

## 1. Goal

<What is designed, to which level (concept, buildable design, flown aircraft), and how it is verified. The owner's goals.>

## 2. Given decisions and resources

| Item | Decision | Consequence |
|---|---|---|
| <owner constraint, hardware, software policy> | <decision, with REQ or DEC ID> | <what follows for the design> |

## 3. Team

| Agent | Owns |
|---|---|
| chief engineer (main session) | Plan, work packages, coordination, meeting preparation, `handover.md`, `timeline.md`, `project-plan.md`, `risks.md` |
| <agent> | <what it owns in this project> |

## 4. Phases

Default phases, tailored at the kickoff:

| Phase | Content | Lead | Ends with |
|---|---|---|---|
| System requirements | Needs, ConOps, system-level requirements, verification methods, requirements of the verification environment | systems-engineer | **SRR** |
| Concept and architecture | Trade studies, baseline sizing, breakdown, allocation, interfaces | systems-engineer, sizing-engineer | milestone *System design* |
| Verification environment | Simulation backbone, models validated within stated limits | simulation-engineer | milestone *Sim ready* |
| Preliminary design | Subsystem requirements, preliminary designs, budgets, a test case per requirement | all disciplines | **PDR** |
| Implementation and integration | Functions in simulation, then on the test bench | function owners | milestone *Integrated* |
| Detailed design | Buildable design: CAD, structural analysis, wiring, parts list, closed budgets | structures-engineer, avionics-engineer | **CDR** |
| Verification | All test cases on the CDR configuration, coverage, verification report | verification-engineer | milestone *Verification complete*, then close-out |

## 5. Phase content

<Per phase: the work and the deliverables of this project, in a few lines each.>

## 6. Reviews and gates

**Milestones:** independent review by the reviewers relevant to the scope; the owner accepts the milestone in a milestone review.

**Gates:**

| | Entry | Exit |
|---|---|---|
| All gates | `plm validate` and `plm suspects` clean; items in scope `in-review`; `plm report coverage` attached | Reviews by `requirements-reviewer`, `analysis-reviewer`, `safety-engineer` and, from PDR, `software-reviewer`; no open `major` finding; owner go in the gate meeting |
| SRR | System requirements complete | Requirements complete, consistent, feasible and verifiable |
| PDR | Concept and preliminary design complete, *Sim ready* accepted | Architecture, sizing and subsystem requirements agreed; every requirement allocated and has a test case |
| CDR | Implementation and detailed design complete, *Integrated* accepted | Design complete and buildable; budgets closed with margin; functions verified in simulation and on the bench |


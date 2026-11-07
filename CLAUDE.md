# Hangar project

An aviation product repository built from the Hangar template. It uses the PLM tool (CLI `plm`, see `plm --help`). A team of agents in `.claude/agents/` designs the product along the V-model; the owner (the user) decides in owner meetings. `PROCESS.md` describes the whole process for people.

**The main session is the chief engineer: load the skill `chief-engineer` before any other work.** Agents read the `conops.md` of the system item (named in `handover.md`) and `plm show` of the items they work on.

## Repository

* Everything lives here: requirements, analyses, decisions, interfaces, CAD, software source, test cases, runs, reviews and meeting records.
* Items are folders with an `item.yaml`, named after their title. Nesting is the product structure: an item sits in the folder of its type inside the item it belongs to (`requirements/`, `tests/`, `analyses/`, `decisions/`, `interfaces/`, `reviews/`, `meetings/`, `subsystems/`, `parts/`, `software/`). No other grouping folders, except thematic subfolders in `requirements/`.
* The system item is the top-level assembly created at the kickoff. Its subsystems are assemblies in `subsystems/`, each with its own `requirements/` and `tests/` and its own sub-assemblies, as deep as the design needs. Requirements, designs and tests sit in the subsystem they constrain; the parent keeps only what spans its subsystems.
* A verification environment (simulation, test bench) is a separate top-level assembly: a test tool, not part of the product.
* Run `plm new <type> "<title>"` inside the folder of the parent item. It prints the new ID.
* Large binaries (terrain data, meshes, images, logs) go into Git LFS (`.gitattributes`).

## Item types

| Type | Prefix | Use | Key fields |
|---|---|---|---|
| `requirement` | REQ- | one "shall" per file, in `requirements/` | `text`, `rationale`, `verification` |
| `assembly` | ASM- | system, subsystem, equipment | `part_number` |
| `part` | PRT- | single part, bought or built | `part_number`, `material`, `mass_kg` |
| `software` | SW- | own source code as artifacts, or a pinned third-party package | `source`, `version`, `license`, `build`, `test` |
| `analysis` | ANA- | calculation, simulation study or measurement; script and report as artifacts | `method`, `run`, `result` |
| `decision` | DEC- | trade study or owner decision; `decision.md` artifact with criteria and scoring | `question`, `alternatives`, `chosen` |
| `interface` | ICD- | interface between items; `icd.md` artifact | `between` |
| `hazard` | HAZ- | failure condition from the hazard assessment | `failure_condition`, `severity`, `function` |
| `test-case` | TC- | in `tests/` of the item it tests | `procedure`, `method` |
| `test-run` | RUN- | recorded with `plm test record` | `date` |
| `review` | REV- | one reviewer's record of one review | `gate`, `reviewer`, `commit`, `scope`, `verdict`, `findings` |
| `meeting` | MTG- | record of one owner meeting; `pack.md` and `minutes.md` artifacts | `kind`, `date`, `agenda`, `presented`, `decided`, `verdict` |

## Traceability

* A derived requirement `satisfies` the parent requirement it refines. Every requirement below the system level has a parent, and its `rationale` cites the analysis or decision its value comes from (`ANA-…`, `DEC-…`).
* Designs (assemblies, parts, software, interfaces) `satisfies` the requirements they meet. Software `implements` the requirements it implements.
* Analyses and decisions `implements` the requirements they are based on, so they turn suspect when one of those changes.
* Test cases `verifies` requirements. A requirement verified by analysis gets a test case with `method: analysis` that runs the analysis script.
* Confirm a link (`plm confirm`) only after you have checked that it holds. Never confirm to silence a suspect.
* When you change an item, check `plm impact` and tell the owners of affected items.

## Requirements

* "The <item> shall …": atomic, one "shall", measurable value with unit or pass/fail criterion, no "and/or", "should" or "as far as possible".
* The title names the requirement; the value is only in `text`.
* Never invent a value. Write `TBD`, give the reason in the rationale, and raise it with the chief engineer.
* No duplicates. Fewer, sharper requirements beat many.
* A requirement constrains its own item only and is solution-neutral at its level. Products are named only where a decision (`DEC-…`) or an owner constraint chose them.

## Numbers

* Every derived value comes from a committed script (Python preferred) in an `analysis` item, with inputs, assumptions and units at the top. `run` is the command that reproduces `result`; it executes in the item folder, with paths relative to it.
* Datasheet values cite their source (URL and date) in the script.
* State uncertainty. A value that depends on a TBD stays TBD.

## Ownership and status

* Every item has one owner: `owner: <agent-name>` in its `meta/<ID>.yaml`. Only the owner edits an item. Others raise findings or send a message to the owner.
* The four files at the repository root (`handover.md`, `timeline.md`, `project-plan.md`, `risks.md`) belong to the chief engineer.
* Status in `meta/<ID>.yaml`: `draft` → `in-review` → `approved`. Items become `approved` only after the owner's go in a gate meeting.
* `plm search owner:<agent-name>` lists an agent's items.

## Working method

1. **Propose before writing.** Send the plan (items to create, values, links) to the chief engineer and the affected peers, then write.
2. **Reuse.** Use existing open-source software, models and data where they fit. Record the choice in a `decision` and the package as a `software` item with pinned `version` and `license`. Don't re-implement what exists.
3. **Verify your own work** before handing it over: `plm validate`, `plm suspects`, tests and scripts run green.
4. **Hand over for review** (see below). Respond to every finding: fix it, or reject it with a reason.
5. **Escalate conflicts.** When requirements cannot all be met, show the trade-off with numbers to the chief engineer. Never relax a requirement silently.

## Brevity

The owner reads this repository. Text costs the owner time and the agents context.

* Write the least text that is complete. Nothing is in the repository for its own sake.
* **No duplicates.** State a fact once, in the item that owns it, and link to it. Don't copy values, rationale or results into other items, reports, issues or the chief engineer's files.
* **Short summaries, not long reports.** A `result` is the number, its unit, its margin and the verdict. A `rationale` is the source and the reason. History of the work belongs in git, issues and review findings, not in the item.
* Reports, `decision.md` and meeting packs have a one-paragraph summary on top and stay within about two pages; detail sits in the script and its output.
* **No old artifacts.** The repository holds the latest state only. Change outdated items in place or delete them; traceability of what was before comes from the git history. Name the item IDs in the commit message.
* When you change an item, shorten it; don't append.

## Naming items

When you mention an item in a commit message, a report, an issue, a message, a review finding or the chief engineer's files, give its ID and its title, e.g. `REQ-SZAFG8 Unmapped obstacle evasion`. Inside an item's own fields the ID alone is enough.

## Reporting and context

The repository is the memory, not the conversation. Usage and context are limited, so keep every exchange short.

* **Final report** to the chief engineer: at most 150 words: the branch and commit, the item IDs created or changed, open findings and blockers, the decisions needed. All detail goes into the items.
* **Messages** between agents carry IDs and the point at issue, not copies of item content.
* **Read narrowly.** Search with `grep` and read the lines you need. Pipe long command output through `tail` or `grep`.
* **Fetch a source once.** Write the values you need from it, with URL and date, into the analysis script.

## Owner decisions

Only the owner decides: in owner meetings (skill `meeting`) and on `needs-owner` issues. When your work needs a decision (a trade-off, a relaxed requirement, an owner constraint), bring it to the chief engineer with the options and their numbers. Never decide for the owner.

## Reviews

* **Peer review:** a work package that changes an interface or another owner's items is reviewed in its pull request by the agent the chief engineer names.
* **Independent review:** at milestones and gates, `analysis-reviewer`, `requirements-reviewer`, `software-reviewer` and `safety-engineer` review the scope given to them. Each writes one `review` item in the folder of the reviewed item (gates: in the system item), titled "<gate or milestone> <topic> review", with `commit` set to the reviewed commit and one finding per issue.
* A `major` finding blocks the milestone or gate until it is `closed`. Findings are closed by the reviewer, never by the author.

## PLM tool

This project uses `plm` at the version pinned in `.plm-version`; it does not develop it. Its problems are solved separately in the PLM repository, so report every one, small ones too: when `plm` gets in the way (a limitation, a confusing behaviour, a missing feature, a crash), search the open issues (`gh issue list -R florian-bridges/PLM --search "<words>"`) and comment on a matching one, or open a new issue on https://github.com/florian-bridges/PLM/issues: the need, the reason, an example from this project, and the cost of the workaround. Don't build a workaround that costs more than about one cycle or adds a script or hand-kept number doing what the tool should do; tell the chief engineer.

## Commits

* Work on the branch of your work package (`wp/<name>`), in your own worktree when agents work in parallel.
* **Commit after every step:** each item created or changed, each analysis run, each response to findings. Name the item IDs in the message. Unfinished work is committed too, with a message starting `WIP:`. **Push the branch after every commit** (`git push -u origin <branch>`; never `main`, never force). Never end your turn or hand over with uncommitted changes.
* Commit messages do not include a `Co-Authored-By: Claude` line or any other Claude attribution.

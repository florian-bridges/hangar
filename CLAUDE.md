# Hangar project

An aviation product repository built from the Hangar template. It uses the PLM tool (CLI `plm`, see `plm --help`). A team of agents in `.claude/agents/` designs the product along the V-model. The main session is the **chief engineer**; the owner (the user) decides in owner meetings.

Read first: `handover.md` (it names the system item and its folder), `timeline.md`, the `conops.md` and `project-plan.md` of the system item, and `plm show` of the items you work on. `PROCESS.md` describes the whole process for people.

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
* **No duplicates.** State a fact once, in the item that owns it, and link to it. Don't copy values, rationale or results into other items, reports, issues, `handover.md` or `timeline.md`.
* **Short summaries, not long reports.** A `result` is the number, its unit, its margin and the verdict. A `rationale` is the source and the reason. History of the work belongs in git, issues and review findings, not in the item.
* Reports, `decision.md` and meeting packs have a one-paragraph summary on top and stay within about two pages; detail sits in the script and its output.
* **No old artifacts.** The repository holds the latest state only. Change outdated items in place or delete them; traceability of what was before comes from the git history. Name the item IDs in the commit message.
* When you change an item, shorten it; don't append.

## Naming items

When you mention an item in a commit message, a report, an issue, a message, a review finding, `handover.md` or `timeline.md`, give its ID and its title, e.g. `REQ-SZAFG8 Unmapped obstacle evasion`. Inside an item's own fields the ID alone is enough.

## Reporting and context

The repository is the memory, not the conversation. Usage and context are limited, so keep every exchange short.

* **Final report** of an agent to the chief engineer: at most 150 words: the branch and commit, the item IDs created or changed, open findings and blockers, the decisions needed. All detail goes into the items.
* **Messages** between agents carry IDs and the point at issue, not copies of item content.
* **Read narrowly.** Search with `grep` and read the lines you need. Pipe long command output through `tail` or `grep`.
* **Fetch a source once.** Write the values you need from it, with URL and date, into the analysis script.
* **Handover:** a new session starts from `handover.md`, `timeline.md` and the open issues, not from the history.

## Handover and timeline

The chief engineer keeps both current at every merge and at the end of every shift cycle. Current state only; history is in git.

* `handover.md`: what the next session needs to start: the system item, the active topics with their one next step, open pull requests, blockers, and the owner's standing directions with their DEC IDs. At most about one page.
* `timeline.md`: the project timeline. **Overview:** every phase, milestone and gate with its budget in 5-hour usage windows, the windows used and its state (done with its MTG ID, active, planned). **Active milestone:** `**Next milestone: <name>.**`, `Budget: <n> windows.` (set by the owner in a meeting), the entry conditions as `- [ ]`/`- [x]` lines with a *done when* each, the active topics with their issue or pull request, and the coming owner meetings. The shift reads these lines; keep their form.

## GitHub

The engineering record is the items. GitHub carries the work around them. Use `gh`.

* **Issues** hold the work that is not an item: work packages, backlog entries (minor findings, remarks, ideas), and questions to the owner (label `needs-owner`). One issue per topic, with a *done when* line. Close an issue with the commit that resolved it.
* **Labels:** `type:*`, `owner:<agent-name>`, `needs-owner`, `meeting`, `blocked`, `gate-condition`, `won't do` (created by `scripts/setup.sh`). **GitHub milestones** are the project's milestones and gates.
* **Branches:** `main` holds owner-approved baselines only, one merge per passed gate, tagged `<gate>-baseline`. Work integrates on `develop`. Each work package is a branch `wp/<name>` and a pull request into `develop`; CI must be green before it is merged.
* **Owner answers** arrive as comments on `needs-owner` issues. The chief engineer records each answer as an item (`DEC-…` or an owner-constraint requirement), links the issue in the commit and closes it.
* Problems with the PLM tool are issues on the PLM repository (see PLM tool), not here.

## Owner meetings

The owner decides in meetings: the kickoff, the gates (SRR, PDR, CDR), milestone reviews, decision meetings, re-plans, status meetings and the close-out. The procedure is the skill `.claude/skills/meeting/`; each kind has its agenda in `kinds/`.

* The chief engineer prepares a meeting, usually on shift (`MTG-` item, `pack.md`, an issue labelled `meeting`), and then stops. The owner holds it interactively with `/meeting <MTG-ID>`.
* Only the owner decides, and only in a meeting or on a `needs-owner` issue. Agents never decide for the owner.

## Owner sessions

* A session the owner starts first runs `systemctl --user is-active <name>-shift` (`name` is in `.claude/shift/shift.toml`).
* While the shift is active, it owns its worktree and the `develop` branch. The owner session may read, answer, hold a meeting that is ready, and comment on issues; it does not commit to `develop`.
* While it is inactive: normal work. Record owner decisions as items, commit them and update `handover.md` and `timeline.md`.

## Reviews

* **Peer review:** a work package that changes an interface or another owner's items is reviewed by the agent the chief engineer names, in its pull request.
* **Independent review:** at milestones and gates, `analysis-reviewer`, `requirements-reviewer`, `software-reviewer` and `safety-engineer` review the scope given to them. Each writes one `review` item in the folder of the reviewed item (gates: in the system item), titled "<gate or milestone> <topic> review", with `commit` set to the reviewed commit and one finding per issue.
* A `major` finding blocks the milestone or gate until it is `closed`, and only a `major` gets a second review round. Minors and remarks are fixed in the same work package when cheap, otherwise they become backlog issues. Findings are closed by the reviewer, never by the author.
* Done is final: a topic ticked done in `timeline.md` is not reopened, re-reviewed or polished. Only a `major` finding or an owner decision reopens it.
* Counts, denominators and review packs are generated at the gate (by `plm` or one committed script), not kept in prose.

## PLM tool

This project uses `plm` at the version pinned in `.plm-version`; it does not develop it.

* When `plm` gets in the way (a limitation, a confusing behaviour, a missing feature), open an issue on https://github.com/florian-bridges/PLM/issues: the need, the reason, an example from this project, and the cost of the workaround.
* Don't build a workaround that costs more than about one cycle or adds a project script or hand-kept number doing what the tool should do. Work on something else meanwhile.
* A new `plm` version is adopted by changing `.plm-version` in its own work package, with `plm validate` and `plm suspects` clean.

## Commits

* **The chief engineer spawns one subagent at a time** and waits for its report before the next.
* Work on a branch per work package (`wp/<name>`), in your own worktree when agents work in parallel.
* **Commit after every step:** each item created or changed, each analysis run, each response to findings. Name the item IDs in the message. Unfinished work is committed too, with a message starting `WIP:`. **Push the branch after every commit** (`git push -u origin <branch>`; never `main`, never force). Never end your turn or hand over with uncommitted changes.
* Commit messages do not include a `Co-Authored-By: Claude` line or any other Claude attribution.

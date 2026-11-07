# Hangar

A template repository for aviation projects developed by a team of AI agents along the V-model, with a PLM record of every requirement, analysis, decision, design, test and review.

* **Agents:** a chief engineer (the main Claude Code session) and discipline engineers and independent reviewers in `.claude/agents/`.
* **Owner meetings:** the owner decides in a kickoff, gates (SRR, PDR, CDR), milestone reviews, decision meetings and re-plans (`/meeting`).
* **PLM:** items, traceability and suspects with [`plm`](https://github.com/florian-bridges/PLM), pinned in `.plm-version`.
* **GitHub:** issues for work and owner questions, pull requests per work package, CI checks, baselines on `main`.
* **The shift:** the chief engineer works unattended until the owner is needed.

How it all works: [PROCESS.md](PROCESS.md). Rules for the agents: [CLAUDE.md](CLAUDE.md).

## Start a project

Needs git with Git LFS, Node.js ≥ 22.18, the GitHub CLI (`gh auth login`), Claude Code, and `uv` for the shift.

1. **Use this template** → create the new repository, and clone it.
2. `scripts/setup.sh --protect`: installs `plm`, creates the labels and the `develop` branch, protects `main`.
3. Start Claude Code in the repository and run `/meeting kickoff`.

The template was derived from the autonomous-fixed-wing project, an autonomous low-level fixed-wing UAS designed with this method.

## Contributing

Problems and ideas for the method: [issues](https://github.com/florian-bridges/hangar/issues). Problems with the PLM tool: [PLM issues](https://github.com/florian-bridges/PLM/issues). Pull requests are welcome; keep the generic files free of project specifics.

## License

[MIT](LICENSE)

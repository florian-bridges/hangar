# Gate (SRR, PDR, CDR)

The owner decides whether the project passes into the next phase. Prepared when every entry condition in `timeline.md` is ticked and the independent review items are written.

## Agenda

1. **Summary and entry conditions:** what the gate covers; every entry condition met (`timeline.md`), with its evidence ID.
2. **Results:** the design state of the gate (SRR: requirements; PDR: architecture, sizing, budgets with margins, subsystem requirements; CDR: buildable design, closed budgets, verified functions), and the decisions taken since the last gate.
3. **Reviews:** the verdict of each REV item; open findings (`plm list findings state:open`); no open `major` is allowed.
4. **Coverage and TBDs:** `plm report coverage`, open TBDs (`plm list parameters value:`), requirements only a flight test can verify.
5. **Risks:** `risks.md`, the risks that changed since the last meeting first.
6. **Open owner decisions:** the `needs-owner` issues of this milestone, each with options and a recommendation.
7. **Verdict:** go, go with conditions, or no-go.
8. **Next milestone:** its entry conditions and budget.

## Outcome

`verdict` on the MTG item; on go, items in scope `approved`, the baseline PR `develop` → `main`, the tag `<gate>-baseline`, the GitHub milestone closed (see SKILL.md, Record).

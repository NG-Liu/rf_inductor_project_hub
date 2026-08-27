# Catalog Sources

The inventory generator treats existing files as authoritative and leaves them
unchanged. It currently discovers:

- `runs/**/manifest.csv`, `proposal.json`, `best_result.json`,
  `emx_batch_summary.json`, and `summary.md` for the single-inductor projects.
- Generic `run.json` and `score_summary.json` in the legacy integration
  workspace.
- Files ending in `.metrics.json` anywhere below a configured project root.

## Provenance Rule

Some historical JSON and CSV files embed the absolute path from the machine
that generated them. The original field is evidence, not a relocation rule.
The catalog always stores a path relative to the directory actually scanned.

## Reference Examples

- Single-inductor selection evidence: `runs/<name>/best_result.json`.
- Candidate provenance: `runs/<name>/manifest.csv` and `proposal.json`.
- Broad solver provenance: a `run.json`, such as the sparse cascade validation
  record in the legacy workspace.
- Solver-specific summaries: `*.metrics.json` and `score_summary.json`.

Refresh the catalog after adding an important result, changing a Git state, or
moving an artifact. Do not manually edit generated files under `inventory/`.

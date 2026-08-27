# Run Catalog Schema

`inventory/run_catalog.csv` is a lightweight evidence index, generated from
existing files without modifying the source projects. It records metadata
sources rather than replacing their detailed JSON, CSV, Touchstone, or GDS
contents.

## Current Columns

| Column | Meaning |
| --- | --- |
| `project_id` | Project identifier from `projects.json`. |
| `run_root` | Logical run directory when it can be inferred from `runs/<name>` or a `run.json` parent directory. |
| `record_type` / `record_path` | The existing metadata file that supplied the row. |
| `run_id` | Explicit identifier from a generic `run.json`, when present. |
| `domain` | Engineering domain from `run.json`, such as `single_inductor`, `filter`, `balun`, or `cascade`. |
| `parent_run_id` / `source_commit` | Provenance fields from `run.json`. |
| `tool` / `process_id` | Solver and process information from `run.json`. |
| `target_l_3p75_nh`, `candidate_id`, `l_3p75_nh`, `q_3p75` | Extracted from a single-inductor `best_result.json`, when available. |
| `status` | Result status supplied by the source metadata. |
| `size_bytes` / `modified_at` | Filesystem facts for the metadata record. |

Multiple metadata records may belong to one logical run. Group by
`project_id` and `run_root`; a future normalized `run.json` can make the
relationship explicit with `run_id` and `parent_run_id`.

## Future Run Metadata

For new work, prefer a `run.json` in each run directory with at least:

```json
{
  "run_id": "YYYY-MM-DD_project_short_description",
  "domain": "single_inductor",
  "intent": "target_l_search",
  "status": "complete",
  "parent_run_id": null,
  "source_commit": "<git sha or sha+dirty>",
  "tool": {"name": "EMX", "version": "<version>"},
  "process_id": "<process profile>",
  "artifacts": ["manifest.csv", "best_result.json"]
}
```

Keep solver-specific metrics in existing result files and list those files in
`artifacts`; the catalog should remain navigational rather than become a second
raw-results database.

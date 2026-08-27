# RF Inductor Project Hub

This directory is the non-destructive index for the historical RF inductor work
on this desktop. It does not replace, move, or modify the three source
directories it describes.

## Start Here

| Project | Role | Canonical status |
| --- | --- | --- |
| `single_inductor_lq_surrogate` | Core code for single-inductor L/Q modeling and EMX candidate selection. | Source of truth for maintainable inductor code. |
| `emx_inductor_optimizer_release` | Colleague-facing package with reference EMX artifacts and a one-command target-L flow. | Derived release snapshot. |
| `新建文件夹 (2)` | Historical RF/balun integration workspace with FDL, Cadence, EMX, and HFSS experiments. | Legacy/integration archive; do not use as a new code root. |

Read `PROJECT_MAP.md` for the relationship between the projects. Run
`python tools/refresh_inventory.py` after adding results or changing the Git
state to refresh the CSV catalogs under `inventory/`.

## Organization Rules

1. Make maintainable single-inductor changes in `single_inductor_lq_surrogate`.
2. Build release copies from the core repository; do not make long-lived
   release-only source changes.
3. Preserve `新建文件夹 (2)` as evidence and system-integration context. Move
   files only after they appear in the inventory and have a Git or archive
   snapshot.
4. Use `inventory/run_catalog.csv` as the entry point for locating verified
   target-L results.

## Current Boundaries

- The core repository tracks code, model snapshots, small examples, and tests.
- The release keeps selected FDL, GDS, S-parameter, proposal, and best-result
  artifacts for inspection.
- The legacy workspace keeps the broader LVBOBALUN, filter, balun, and HFSS
  work, including local experiments that are not part of the reusable core.

## Next Physical Cleanup

`MIGRATION_CHECKLIST.md` records the remaining opt-in cleanup steps. None of
them are performed automatically by this hub.

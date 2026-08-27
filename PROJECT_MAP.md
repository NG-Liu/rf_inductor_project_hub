# Project Map

## Relationship

```text
BEWATERo/LVBOBALUN
  |\
  | \-- external/LVBOBALUN          reference checkout
  |\
  |  \-- repo_lvbobalun             modified integration checkout
  |        |
  |        +-- single-inductor FDL and L/Q prototype work
  |
新建文件夹 (2)                       historical RF integration workspace
  |
  +-- FDL -> Cadence -> GDS -> EMX evidence
  +-- filter/balun cascade and HFSS studies
  |
  +-- extracted/refactored into --> single_inductor_lq_surrogate
                                      |
                                      +-- packaged into --> emx_inductor_optimizer_release
```

The `single_inductor_lq_surrogate` and the release do not share a Git commit
ancestor. Their relationship is a content-level packaging relationship: the
release contains the core repository's tracked files plus release-specific
scripts, documentation, and reference results.

## Ownership

| Area | Home | Notes |
| --- | --- | --- |
| Geometry, FDL generator, Touchstone parsing, L/Q model, candidate selection | `single_inductor_lq_surrogate` | Reusable inductor code belongs here. |
| Checked reference FDL/GDS/S2P and handoff material | `emx_inductor_optimizer_release` | Keep only results needed to inspect or reproduce conclusions. |
| LVBOBALUN changes, filter/balun layouts, cascades, HFSS system studies | `新建文件夹 (2)` | Keep as system-level integration work. |
| Upstream comparison baseline | `新建文件夹 (2)/external/LVBOBALUN` | Preserve as a read-only reference checkout. |

## Source-to-Artifact Flow

```text
geometry parameters
  -> FDL
  -> Cadence SKILL/layout
  -> GDS stream-out
  -> EMX Touchstone data
  -> complex-Z L/Q extraction
  -> dataset and surrogate model
  -> target-L candidate proposal
  -> EMX selection of highest-Q feasible point
```

The project inventory deliberately catalogs both source groups and result
records so the historical evidence remains searchable without turning the
legacy workspace into a second core repository.

# Migration Checklist

This checklist is intentionally conservative. It is safe to use the hub and
its catalogs before any physical move is made.

## Completed

- [x] Established `single_inductor_lq_surrogate` as the core inductor-code home.
- [x] Classified `emx_inductor_optimizer_release` as a derived release package.
- [x] Classified `新建文件夹 (2)` as a historical integration workspace.
- [x] Created a non-destructive project map and inventory generator.

## Before Any Move

- [ ] Capture the current Git state of `新建文件夹 (2)/repo_lvbobalun` on a
      `legacy/single-inductor-prototype` branch or an archive commit.
- [ ] Decide whether `external/LVBOBALUN` remains as an upstream reference or
      is replaced by a documented clone command.
- [ ] Confirm which large GDS, S-parameter, video, and report artifacts must
      remain immediately accessible.

## Recommended Physical Layout

```text
rf_inductor_archive/
  core/                 single_inductor_lq_surrogate
  releases/             emx_inductor_optimizer_release
  integration/          LVBOBALUN and filter/balun work
  artifacts/            large EMX/HFSS outputs retained by run ID
  project_hub/          this directory
```

Use copies or filesystem links during a trial migration. Do not delete the
original paths until the inventory has been refreshed and the relevant local
tests have passed from the new locations.

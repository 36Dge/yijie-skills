# `copywriting` 0.1.0 provenance and authorization

## Selection

FEAT-129 selected the `copywriting` capability from the user-provided 38-Skill directory because its source is a single instruction file and declares no browser, network, filesystem, MCP, shell, supplier-search, or third-party data dependency.

Observed upstream candidate:

- local category/name: `内容创作与营销/copywriting`;
- local cache ID/version: `27_copywriting` / `0.0.94`;
- cache owner marker: `official`;
- cache URL: `https://skill.accio.com/skills/phoenix/official/0.0.94/copywriting.zip`;
- original local `SKILL.md` SHA-256: `5e379fc912293f05c3d70d112339117e5fe066956d2ff8fb592526b81eb2370b` (also recorded by `scripts/audit-copywriting-source.mjs`).

The local source has no LICENSE, NOTICE, author identity, immutable repository commit, or redistribution terms. The cache owner marker is not license evidence. No original source text is packaged in `yijie-skills`.

## Re-authored YiJie candidate

`plugins/yijie-desktop-skills/skills/copywriting` is a new, narrower YiJie-authored model-only implementation created for FEAT-129. It focuses on cross-border marketing drafts, factual-claim discipline, explicit evidence gaps, no-tool behavior, and separation between drafting and platform publication.

Stable metadata:

- catalog ID: `yijie.content-marketing.copywriting`;
- Runtime name: `copywriting`;
- version: `0.1.0`;
- category: `content-marketing`;
- risk: `medium`;
- capability mode: `model-only`; no tools, network, or filesystem;
- `iconKey`: `edit` in the `yj-icon-v1` registry.

## Authorization boundary

The user explicitly requested creation and local packaging of the first FEAT-129 Skill on 2026-08-25. This is recorded as `LicenseRef-YiJie-Local-Development-Only` and authorizes the exact `local-development` candidate artifact for local Contract First testing.

It does **not** establish rights to redistribute the observed Accio source, and it does not authorize a `desktop-release`, tag, upload, Marketplace publication, or production bundle. Before changing the bundle to `desktop-release`, the product/legal owner must provide an approved YiJie license notice for the re-authored files and confirm that no upstream text or restricted asset is included. The contract schema requires `desktop-distribution` authorization for that channel.

## Review result

- Content/provenance of the re-authored files: verified for FEAT-129 local development.
- External tools and data: none.
- Upstream source redistribution: blocked and not used.
- Desktop distribution: blocked until product/legal evidence is added and the manifest authorization scope changes.

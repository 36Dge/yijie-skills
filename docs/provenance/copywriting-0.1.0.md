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

The FEAT-129 product and repository owner initially authorized local packaging on 2026-08-25 and subsequently supplied the repository-wide ownership and Desktop redistribution declaration `FEAT-129-DESKTOP-DISTRIBUTION-2026-08-25`. The exact re-authored candidate is now authorized for both `local-development` and `desktop-release` under `LicenseRef-YiJie-Desktop-Distribution-Owner-Attestation`.

The authorization record is `docs/provenance/FEAT-129-ownership-and-desktop-redistribution.md`. It covers packaging, installation, execution, modification, and redistribution with the YiJie AI Desktop client. It does not claim that the separately observed Accio source was copied into this implementation.

## Review result

- Content/provenance of the re-authored files: verified for FEAT-129 local development.
- External tools and data: none.
- Upstream source redistribution: blocked and not used.
- Desktop distribution: authorized by the FEAT-129 product and repository owner declaration; Runtime permission controls still apply.

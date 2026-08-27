# Agent instruction audit

Measured from each repository's local `origin/main` on 2026-08-27. The central
baseline is 1,309 bytes. A repository is not marked complete until its reviewed
client rollout lands; no local overlay is overwritten by this platform change.

| Repository | Root before | Root after this slice | Effective after promotion | Result |
| --- | ---: | ---: | ---: | --- |
| `atkandi111/dev-platform` | 1,426 B | 1,426 B | 2,735 B | Within budget |
| `atkandi111/demandph-website` | 6,240 B | Pending client PR | Pending | Reduce below 4 KiB |
| `atkandi111/Mahjongtale` | 327 B | 327 B | 1,636 B | Within budget; rollout pending |
| `atkandi111/rotary-binan-website` | 11,128 B | Pending client PR | Pending | Reduce below 4 KiB |
| `atkandi111/infrastructure` | 1,572 B | 1,572 B | 2,881 B | Within budget; rollout pending |

The rollout issue owns reviewed reductions and final after-count evidence for
the two oversized overlays. Repository-specific commands and safety gates must
be retained; history and detailed runbooks should move to focused documents.

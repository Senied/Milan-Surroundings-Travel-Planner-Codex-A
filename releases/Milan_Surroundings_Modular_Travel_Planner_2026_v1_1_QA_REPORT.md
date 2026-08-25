# Milan and Surroundings Modular Travel Planner 2026 — QA report

Release: **v1.1 · 2026-08-24**  
Verdict: **PASS — release-ready**

This is an additive Milan v1.1 release. The accepted v1.0 files remain intact and are recorded as the predecessor lineage.

## Compatibility and expansion gates

- The modular builder remains exactly M1-M7: 7 core dossiers and 7 builder choices.
- Each M1-M7 module-section outerHTML hash matches the accepted v1.0 predecessor.
- The separate catalogue contains 30 unique MX entries; no MX entry is selectable as a core module.
- P001-P025 match the v1.0 photo identity/provenance records; P026-P031 are additive.
- All 112 v1.0 external-directory URLs remain present in v1.1.

## Release checks

- Interactive HTML: 16,264 words, 31 stable photo IDs, and 211 exact external-directory targets.
- PDF: 82 A4 pages, 16,672 extracted words, 211 external URLs, and 75 valid internal destinations.
- Browser QA passed at desktop, 390 px and 320 px with no document overflow, broken images, broken fragments, duplicate element IDs or console errors.
- Every PDF page was rendered at 200 dpi and visually reviewed; smallest recorded text was 6.49 pt.
- Live link audit: hard failures=0; access controlled=2, operator published dynamic=1, rate limited=1, reachable=207.

## Independent review team

1. YesMilano excursion-discovery auditor — yesmilano_excursion_audit subagent (PASS)
2. Nature-destination discovery-list auditor — hotels_nature_audit subagent (PASS)
3. Primary-source and 2026 operations verifier — final_content_source_review subagent (PASS_WITH_NOTES)
4. Milan v1.0 compatibility and lineage auditor — final_release_lineage_review subagent (PASS)
5. Excursion-tiering and feasibility reviewer — milan_v11_gap_architecture and milan_v11_catalogue_draft subagents (PASS)
6. Image-rights and stable-photo-ID auditor — milan_v11_qa_prep subagent (PASS)
7. Renderer, accessibility and interaction auditor — Codex root (PASS)
8. Every-page PDF visual reviewer — final_visual_ux_review subagent and Codex root (PASS_WITH_NOTES)
9. Desktop and mobile layout reviewer — final_visual_ux_review subagent and Codex root (PASS_WITH_NOTES)
10. Package, checksum and external-link reviewer — final_release_lineage_review subagent and Codex root (PASS_WITH_NOTES)

## Operational boundary

Timetables, fares, closures, weather, lifts, boats, ticket inventory and access restrictions remain live conditions. The planner marks booking and feasibility gates; exact journeys must be regenerated for the selected travel date.

## Machine-readable evidence

The companion QA evidence JSON contains the browser assertions, PDF-page checks, link audit, compatibility regression results and review register. The release manifest and SHA256SUMS bind the package to this exact release.

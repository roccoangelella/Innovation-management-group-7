---
id: STEP1-PLAN
type: note
status: active
title: Step 1 sector landscape plan
created: '2026-11-25'
updated: '2026-11-25'
tags: []
related: [CURRENT-PLAN, PRODUCT-BRIEF, TECH-STEP1]
source_paths: [src/step1_extract.py, src/step1_landscape.py, src/step1_semantic.py, config/step1.json]
confidence: confirmed
---

# Step 1 — Humanoid robotics landscape for Electrolux

## Source and decisions

Course kickoff pp. 9, 11, 12, 17–18; [Tutorial 0/02](https://github.com/graziasveva/innovation-management-datascience26/blob/main/tutorial_0/02_step1_general_description.ipynb) (volume, benchmark, CPC/WIPO, geography, PI only); [Tutorial 2/21](https://github.com/graziasveva/innovation-management-datascience26/blob/main/tutorial_2/21_encoding_patent_text.ipynb) (TF-IDF, Patent SBERT-adapt-ub, BERTopic). See [Nov 23 audit](../analysis/patstat-cleaning-validation-2026-11-23.md). User delegated methodological decisions on Nov 25.

- Freeze the existing 7,102 positive IDs; no new search, scoring or relevance filter. The separately supplied 7,096-family enriched CSV is not in GitHub. Re-enrich the frozen IDs, log exclusions and compare to the teammate result before release. Keep utility models out of primary PI statistics; report IDs lacking PI applications.
- Main window 2000–2026; complete through 2022 provisionally, 2023–26 observed only. Retain historical families for future analyses. Date families by minimum valid TLS201 earliest_filing_year across PI applications (the tutorial calls this earliest priority); application by own filing year. Audit the earlier upstream derivation and missing/sentinel dates. Record PATSTAT edition and inspect 2022–23 lag before freezing the cutoff.
- Global benchmark: same PATSTAT edition, PI restriction, positive family IDs, date definition and years; no WIPO published total substituted because family definitions can differ. Robotics comparator deferred until an independently justified search definition exists.
- Sector volume is invention activity, not revenue, market size, or all innovation. Use absolute counts, YoY, 3-year trailing mean, endpoint growth and CAGR 2000–22 and 2017–22; undefined if denominator zero. Exclude incomplete years from growth and comparisons. Show observed latest years shaded, never interpret as decline.
- CPC: all application-linked classes, deduplicate to subclass (first four normalized characters), equal fractional allocation; unknown as explicit category. Rank top eight using complete years and pool others only in display. Compare 2000–09, 2010–16, 2017–22. Export full table; map top codes to official [CPC scheme](https://www.cooperativepatentclassification.org/) titles, recording version. Never mix matched_cpcs with all_cpcs.
- WIPO: use TLS230 weights summed over family applications and normalized per family; TLS901 official names, 35 fields and five sectors. This follows tutorial; application-rich members have more weight in family aggregate. Compare against equal weighting of distinct fields in sensitivity analysis if necessary.
- Geography: distinct person IDs per family/application and role, fractional allocation by person, retain unknown person countries as their own fractional mass. Entirely missing links = Unknown. Distinguish recorded applicant address from ownership headquarters, inventor address from research location proxy, and office from market. Family office counts overlap; applications have one office. WO is PCT route, not a jurisdiction. Report PCT family and application counts and mean distinct non-WO offices (not sovereign-country count). Compare unknown rates by year and source query; no country imputation in MVP.
- Semantic: fit the whole English corpus once; CPU TF-IDF + fixed-seed KMeans k=10 is only a lexical baseline. Preferred run uses the professor's domain-adapted SBERT with a pinned HF revision and same clustering for comparison. Output representative IDs, descriptive terms, annual shares, cosine silhouette and second-seed ARI. Inspect k=6/8/10/12/15, cluster sizes, duplicates, truncation and source/year effects; compare BERTopic per tutorial if useful. Review 5 central and 5 randomly sampled per cluster, plus boundary cases; consolidate into interpretable multi-label functions, independently validate a stratified holdout, report per-label precision/recall and disagreement. Do not call unsupervised clusters validated technologies. Future scoring must fit models using only time-available data, not this full-period fit. LLM labeling deferred until taxonomy and validation protocol ready.
- Appropriability: no patent count can estimate unobserved secrecy. Compare sector international filing proxies against matched global figures if available, and use empirical literature and contemporary firm disclosures; no invented patent-to-secret ratio.

## Work packages and acceptance

| Work | Implementation/acceptance |
|---|---|
| A — data readiness | Run TIP export using PROD, same edition as Step 0 if available. Match input hashes, reconcile all IDs and missing PI/priority records; compare date and coverage with cleaned file; no bulk PATSTAT exports committed. |
| B — volumes | Annual counts both levels; benchmark comparable; totals reconcile; no growth using truncated cohorts; zero-denominator handled. |
| C — technology | CPC/WIPO totals conserve counting-unit mass including Unknown; compare periods; official CPC definitions independently checked for top subclasses. |
| D — geography | Applicant/inventor fractional totals conserve mass; office counts deduplicated per family/office; office denominators explicit; quantify missingness and examine by year. |
| E — semantic | Reproducible lexical preview; pinned Patent SBERT run; stability and representative review before naming clusters. |
| F — IP strategies | Evidence synthesis with scope and date of literature; compare to disclosed company IP strategies, no causal/market-size assertions. |
| G — reporting | Save versioned code/config, input manifest/edition, tables/figures, technical appendix and review conclusions; publish only aggregated outputs after checks. |

## Deck allocation

Reserve two main figures: (1) family volume + relative global growth in one multi-panel figure; (2) CPC mix evolution (or a validated functional landscape if materially better, keep CPC in appendix). Three short narrative slides: sector direction, technology evolution, geography and appropriability. Appendix: application counts, WIPO tables, official CPC definitions, IP5 and person geography, missingness, PCT, robustness, semantic diagnostics, formulas and evidence. Whole deck cap: 20 slides/10 figures and tables.

## Appropriability evidence (initial synthesis)

[Cohen, Nelson & Walsh (2000)](https://doi.org/10.3386/w7552) survey 1,478 US manufacturing labs in 1994: protection combines patents, secrecy, lead time and complementary manufacturing/marketing capabilities. Not a contemporary humanoid-specific sample.
[Arundel (2001)](https://doi.org/10.1016/S0048-7333(00)00100-1) studies relative effectiveness of patents and secrecy; no humanoid-specific estimate.
[WIPO (2015), Robotics, innovation and intellectual property](https://www.wipo.int/publications/en/details.jsp?id=4001&plang=EN) identifies patents, secrecy, technological complexity and open collaboration as relevant to robotics. Historical broad-robotics evidence, not an estimate of the current humanoid sector.
[Ascione & Sterzi (2024)](https://arxiv.org/abs/2403.16630) provide the patent-specific similarity model used in Tutorial 2; their patent-similarity evaluation does not validate our cluster taxonomy.

Provisional narrative: robotics innovation has mixed appropriability mechanisms; patents reveal codified inventions but cannot reveal proprietary training data, know-how or unpublished inventions. For Electrolux, distinguish patented hardware/control from non-patent assets during later partner due diligence. Confirm current examples with company sources before publication.

## Completion gate

MVP code may run before Step 0 validation closes. Final sector conclusions require completed/properly qualified relevance validation (OQ-001), reconciled metadata and publication lag (OQ-002), missingness evaluation, reviewed CPC definitions, independent semantic interpretation, and sourced IP narrative. No numerical final claims without actual PROD output.

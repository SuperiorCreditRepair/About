# ChatGPT page audit — Superior Credit Repair uniqueness corpus

Audited **5,843** ChatGPT / LPagery pages from the 8 `UNIQUENESS_CORPUS_*_OF_08.csv` files already uploaded to this repo.

This pass is **read-only**. It does not rewrite pages. `CLEARED_PRODUCTION` and sequences **1–5** stay locked.

Python ran on this Linux agent. The same script can be pointed at the network-shared D: folder later; Python can stay on C:.

```bat
C:\Python312\python.exe tools\chatgpt_page_audit.py --corpus-dir "D:\CHATGPT_BATCH_INTAKE\UNIQUENESS_CORPUS" --out-dir "D:\Temp\scr_chatgpt_audit"
```

## Bottom line

The corpus is **not copy-paste duplicate**. Every slug is unique and no two pages share exact HTML or exact body text.

It is still **heavily templated**. The same instructional sentences appear on 700–870 pages. County/city variants reuse the same title. DEEP_REDO pages stack the same “When [slot] deserves a closer look” headings, including ungrammatical plurals. About 1,300 pages say `area area`.

**Do not publish** the 29 CLEARED pages that are stuffed with watermark tokens such as `yx309k1k1r2`. Those pages are inventory-only here.

## Inventory

| Kind | Pages | Notes |
|---|---:|---|
| DEEP_REDO | 2,766 | Main ChatGPT uniqueness rewrite set |
| OTHER | 1,774 | Street / authority / citation pages |
| REPAIRED | 487 | Later repair pass |
| REPAIRED_OTHER | 380 | County/homebuyer title twins live here |
| CLEARED_PRODUCTION | 311 | Locked. 311 missing meta in this export. 29 watermarked |
| MASTER_ORIGINAL | 125 | Older originals; some mid-word cuts into headings |

- Unique slugs: **5,843**
- Source stores: **55**
- Word count min / median / p90 / max: **1,665 / 4,014 / 7,119 / 18,472**
- WordPress IDs present: 2,129
- Sequences filled: 436 (range 1–1598)

### Sequences 1–5 (locked, CLEARED)

- `emmet-mi-homebuyer-credit-repair`
- `west-yellowstone-mt-credit-score-help`
- `bossier-la-homebuyer-credit-repair`
- `daviess-mo-homebuyer-credit-repair`
- `comal-tx-homebuyer-credit-repair`

## Uniqueness findings

| Check | Result |
|---|---|
| Duplicate slugs | 0 |
| Exact-text clones | 0 |
| Exact-HTML clones | 0 |
| Duplicate title groups | **248 groups / 496 pages** |
| Near-duplicate pairs (MinHash ≥ 0.82) | **10** |
| Shared H2 skeletons | 4 clusters / 57 pages |
| 10-word boilerplate reused on 740+ pages | **dozens of phrases** |

### What “unique enough” actually means here

Exact hashes are clean because ChatGPT swapped cities, fake account numbers, dates, and first names. The **bones** of the page are still shared:

- 871 pages: “the review should distinguish location planning from credit report accuracy”
- 839 pages: “justify a new conclusion but the prior version should remain”
- 830 pages: “and leave a short dated instruction for the next reviewer”
- 50 OTHER authority guides have **no H2s** and therefore share one empty heading skeleton

The 10 true near-duplicates are short OTHER “credit readiness / collection agency” guides that only change the product name (`rent-to-own` vs `vacation-home`, `Enhanced Recovery` vs `Pinnacle`).

Duplicate titles are almost all twins like:

- `adams-county-ia-local-credit-repair-678` and `adams-ia-homebuyer-credit-repair`
- both titled **Adams IA Homebuyer Credit Repair**

Those pairs will compete with each other in search.

## Quality findings (actionable)

| Flag | Pages | Meaning |
|---|---:|---|
| `AREA_AREA_TYPO` | 1,324 | “Statewide Alabama area area”, “Cobb County area area” |
| `SLOT_SUBJECT_VERB` | 473 | “When underwriting questions deserves…”, “When related next steps deserves…” |
| `TRUNCATED_META` | 416 | Meta cut off at ~156 chars (“…rebuilding, and re.”) |
| `USE_USE_TYPO` | 13 | “use use documents” on TN street pages |
| `SHORT_TITLE` | 2 | `fix-my-credit-score`, `free-credit-repair` |
| `WATERMARK_TOKENS` | 29 | CLEARED pages with 1,100–1,700 `xx123k1k1r2` tokens — **do not overwrite** |
| `MISSING_META` | 311 | All CLEARED_PRODUCTION in this export |

`HARD_GUARANTEE` first-pass hits (160) were **false positives**. The pages say “does not treat any score as a guaranteed approval.” No body-copy AI leakage (`as an AI` / `as a language model`) was found. `ChatGPT-Image-…` filenames are image assets, not leaked model text.

### Highest-reuse ungrammatical H2 slots

- 115 When **underwriting questions deserves** a closer look
- 111 When **related next steps deserves** a closer look
- 107 When **avoidable missteps deserves** a closer look
- 101 When **supporting records deserves** a closer look
- 43 When **decision points deserves** a closer look

## Recommended rewrite queue

`rewrite_queue.csv` lists **1,957 non-protected** pages with a real quality flag (`AREA_AREA_TYPO`, `SLOT_SUBJECT_VERB`, `TRUNCATED_META`, `USE_USE_TYPO`, `SHORT_TITLE`).

Suggested first waves (25–50 pages, serialized validate-page):

1. The 13 `use use` TN street pages — obvious copy defect, small wave.
2. Truncated-meta DEEP_REDO title-bank pages ending in `and re.`
3. DEEP_REDO `area area` + plural-slot H2 pages, one store at a time.
4. The 10 near-duplicate OTHER guide pairs.
5. Duplicate-title county/city twins — keep one canonical title/slug pair.

Leave these out of writer waves:

- All 311 `CLEARED_PRODUCTION`
- Sequences 1–5
- Generation-hold style rows if they appear on D: (1182 / 1212)

The 29 watermarked CLEARED pages need a **separate production decision**. They are not readable consumer pages. This audit will not rewrite them.

## In-repo polished pages

| File | Words | Notes |
|---|---:|---|
| ABOUT.md | 928 | Compliant disclaimers; ChatGPT image filename in WP uploads |
| CONTACT.md | 1,101 | GHL embed still a placeholder comment; privacy warning is correct |
| HOMEBUYER.md | 1,134 | Compliant; form CTA present |
| CREDIT-CLEANUP.md | 1,282 | Compliant |
| site/consumer-credit-guide.html | 1,014 | Cleanest of the six |
| site/review-credit-before-home-loan.html | 2,044 | Compliant FAQ schema; ChatGPT image filename |

CONTACT is the only in-repo page that is unfinished (GoHighLevel embed not inserted).

## Report files

- `page_flags.csv` — every flagged page
- `rewrite_queue.csv` — non-protected repair candidates
- `duplicate_titles.csv` — 248 title collisions
- `near_duplicate_pairs.csv` — 10 high-overlap pairs
- `h2_skeleton_clusters.csv`
- `boilerplate_shingles.csv` — shared 10-word phrases
- `watermark_cleared_pages.csv` — 29 locked CLEARED pages with token salad
- `site_page_audit.csv` / `SITE_PAGE_AUDIT.md`
- `audit_summary.json`

## What this cloud machine cannot see

The D: Superior Credit Rebuild share is not mounted here. Python on C: is also not on this VM. The audit used the uniqueness-corpus zip files already in `SuperiorCreditRepair/About`. Re-run the same command on the PC that has D: mapped if you want the auditor to read a newer local export.

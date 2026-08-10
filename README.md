# specassay.com

The marketing site for **[SpecAssay](https://github.com/rdryfoos/specassay)** — a homepage and the visual **field guide**. Served on Vercel at `specassay.com`.

The methodology, docs, and tooling live in the [`specassay`](https://github.com/rdryfoos/specassay) repo; this repo is just the shopfront.

## Layout

```
src/index.html      homepage (hand-authored)
src/assets/         shared stylesheet
src/field-guide.md  the field guide (source of truth)
src/images/         field-guide screenshots
scripts/build.py    renders src/field-guide.md -> public-out/field-guide/, copies the rest
public-out/         built static site (committed; Vercel serves this)
```

## Build

```bash
python3 scripts/build.py   # regenerates public-out/ from src/
```

Zero dependencies. Re-run after editing anything in `src/`, then commit `public-out/` — Vercel serves the committed output statically (`vercel.json` → `outputDirectory: public-out`), no build step on deploy.

## Deploy

Vercel project → this repo → Framework **Other**, Output Directory **`public-out`**. Domain: `specassay.com`.

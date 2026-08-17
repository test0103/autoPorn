# Content Operations Automation

A local-first Python pipeline for content selection, publishing, re-classification, Excel audit logs, and human-review feedback learning. The implementation is intentionally dry-run by default and was built only from the request/response examples supplied in the task.

## What it does

1. Fetches source movies from `/api/web/admin/laosiji/movie/search`.
2. Keeps only items where `isAdd == false`.
3. Rejects risky or low-quality items using configurable keywords plus simple cover-image color heuristics.
4. Fetches the dynamic section list from `/api/web/admin/module/section/all`.
5. Assigns a section with either a trained local scikit-learn model or a keyword fallback.
6. Publishes via `/api/web/admin/laosiji/movie/add` and re-classifies via `/api/web/admin/module/video/add/batch` only when `--execute` is used.
7. Appends every decision to an Excel workbook for manual audit.
8. Learns from a review workbook through `--learn`.

## Safety and credentials

Do not hard-code admin tokens. Put the bearer/JWT value in the environment variable named by `api.authorization_env` (default: `AIPAPA_AUTHORIZATION`). The provided YAML uses `dry_run: true`; this prevents network mutations unless `--execute` is passed.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp config/config.example.yaml config/config.local.yaml
export AIPAPA_AUTHORIZATION='your-token'
content-ops --config config/config.local.yaml
```

To execute real publishing and re-classification after auditing the plan:

```bash
content-ops --config config/config.local.yaml --execute
```

To train from human review feedback, create `data/review.xlsx` with columns:

- `title`
- `tags`
- `approved`
- `correct_section` (or `section_name`)

Then run:

```bash
content-ops --config config/config.local.yaml --learn
```

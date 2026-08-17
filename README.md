# Content Operations Automation

A local-first Python pipeline for content selection, publishing, re-classification, Excel audit logs, and human-review feedback learning. The implementation is intentionally dry-run by default and was built only from the request/response examples supplied in the task.

## What it does

1. Fetches source movies from `/api/web/admin/laosiji/movie/search`.
2. Keeps only items where `isAdd == false`.
3. Rejects risky or low-quality items using configurable keywords plus simple cover-image color heuristics.
4. Fetches the dynamic section list from `/api/web/admin/module/section/all`; targets may be parent lists such as `精选`/`国产` or child lists returned by the API.
5. Assigns a section with either a trained local scikit-learn model or a keyword fallback tuned for common lists such as `精选`、`国产`、`网黄`、`AV`、`乱伦`、`传媒`、`重口味`、`猎奇`、`调教`.
6. Scores title appeal and cover quality, then publishes via `/api/web/admin/laosiji/movie/add` and re-classifies via `/api/web/admin/module/video/add/batch` only when `--execute` is used.
7. Appends every operation and review placeholder to an Excel workbook for manual audit; it does not persist the full remote content library locally.
8. Learns only from human-review differences through `--learn`.

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

To train from human review feedback, edit the generated operations workbook or create `data/review.xlsx` with columns:

- `title`
- `tags`
- `review_action` (`通过`/`approve`/`keep` rows become training samples)
- `review_section` (the corrected category; `correct_section` and `section_name` are still accepted for compatibility)
- `review_title_click` (manual judgement about whether the title attracts clicks)
- `review_cover_click` (manual judgement about whether the cover attracts clicks)
- `review_note`

Only the operation row and the human-review difference are kept locally; the script reuses the API as the source of truth for content and section lists on each run.

Then run:

```bash
content-ops --config config/config.local.yaml --learn
```

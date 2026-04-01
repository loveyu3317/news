# Daily U.S. News Issue

This project fetches top stories from major U.S. news sources and creates a bilingual GitHub issue every day at 8:00 PM America/New_York.

## Included sources

- Reuters
- The New York Times
- Washington Post
- NPR
- CNN
- Fox News

## How delivery works

- GitHub Actions runs on a schedule.
- The script checks New York local time and only creates the issue at 8:00 PM.
- For manual tests, you can use the workflow's `force_run` input to create an issue immediately.
- GitHub can email you about the new issue if your account email notifications are enabled and you are watching the repository for issue notifications.

## Workflow file

- `.github/workflows/daily_news_email.yml`

## Local run

```bash
pip install -r requirements.txt
python scripts/daily_news_digest.py --limit-per-source 3 --force-run --title-output issue_title.txt --body-output issue_body.md
```

## Output files

- `issue_title.txt`
- `issue_body.md`

## Notes

- Translation uses `deep-translator` with Google Translate and may occasionally fail on some entries.
- GitHub issue emails depend on your GitHub notification settings.

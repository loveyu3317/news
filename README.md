# Daily U.S. News Email (English + 中文)

这个项目会**每天晚上 8:00（美国纽约时间）**自动抓取美国主流新闻站点的头条，并通过邮件发送英中对照摘要。

This project automatically fetches top headlines from major U.S. news sources and sends a bilingual (English + Chinese) digest email **every day at 8:00 PM (America/New_York)**.

## 1) Included sources / 内置新闻源

- Reuters
- The New York Times
- Washington Post
- NPR
- CNN
- Fox News

## 2) GitHub Actions schedule / 定时任务

Workflow file: `.github/workflows/daily_news_email.yml`

- Scheduled by cron in GitHub Actions
- Uses a local-hour guard to ensure the email is sent at 8 PM New York time

## 3) Required GitHub Secrets / 需要配置的 Secrets

在 GitHub 仓库中进入 **Settings → Secrets and variables → Actions**，添加：

Add the following secrets in **Settings → Secrets and variables → Actions**:

- `SMTP_HOST` (例如 `smtp.gmail.com`)
- `SMTP_PORT` (例如 `587`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`（建议使用邮箱应用专用密码 / app password）
- `MAIL_FROM`（发件邮箱）
- `MAIL_TO`（收件邮箱，可填写你的 GitHub 账号邮箱）

## 4) Local run / 本地运行

```bash
pip install -r requirements.txt
python scripts/daily_news_digest.py --limit-per-source 3
```

## 5) Notes / 注意事项

- 翻译使用 `deep-translator`（GoogleTranslator），若网络或频率限制可能导致部分条目翻译失败。
- 建议为 SMTP 账号开启应用密码，不要使用主密码。
- 如果你使用 Gmail 发送到 GitHub 邮箱，请确认 GitHub 账号邮箱可正常接收外部邮件。

# Free-tier Stack Summary

| Component | Service | Free-tier notes |
| --- | --- | --- |
| API + Worker | Google Cloud Run | 2M vCPU-seconds and 360k GiB-seconds monthly. Scale to zero. Consider Cloud Tasks to avoid always-on workers. |
| Container registry/build | Artifact Registry + Cloud Build | 120 build-minutes/month free. Storage billed after 0.5 GB; prune old images. |
| Queue | Upstash Redis | Free plan: 100 MB storage, 1 GB/day transfer, 20 connections. Works with Celery (Redis broker). |
| Database | MongoDB Atlas M0 | 512 MB storage, shared cluster, 100 max connections. Ideal for config + idempotency data. |
| LLM | Google Gemini | Free quota: 1M output tokens/day and 15 RPM for Gemini 1.5 Flash. Sufficient for link extraction. |
| Scraping | Use direct requests | Free. If anti-bot emerges, Apify has a free 5$ credit monthly, ScraperAPI 5k requests free. |
| Monitoring | Cloud Logging + Monitoring | Within free 50 GiB/month log ingestion; adjust retention to 7 days. |

## Cost guardrails

- Keep scraping polite: concurrency ≤ 5 per domain, use caching to avoid redundant fetches.
- Trim `runs` collection periodically to avoid hitting Atlas limits.
- Enforce Gemini token budget with `max_output_tokens` and short prompts.
- For Celery, use `--autoscale=1,5` to scale down worker usage if hosting outside Cloud Run free tier (e.g., Railway free tier).

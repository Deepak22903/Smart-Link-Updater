import os
from typing import List
from celery import shared_task
from .scrape import fetch_html
from .llm import parse_links_with_gemini
from .dedupe import filter_only_today, dedupe_by_fingerprint, fingerprint
from .models import Link
from .wp import update_post_links_section
from .extraction import extract_links_with_heading_filter
from .storage import get_known_fingerprints, save_new_links


@shared_task(name="tasks.update_post_task")
def update_post_task(post_id: int, source_urls: List[str], timezone: str, today_iso: str | None = None):
    """
    Orchestrates for a single post: scrape, extract, filter, dedupe, and update WP.
    This task is sync in Celery context; internal async calls are driven via asyncio.
    """
    import asyncio

    async def run():
        # Determine today in timezone if not provided
        if not today_iso:
            from datetime import datetime
            import pytz
            tz = pytz.timezone(timezone)
            today_iso_local = datetime.now(tz).strftime("%Y-%m-%d")
        else:
            today_iso_local = today_iso

        all_links: List[Link] = []
        for url in source_urls:
            html = await fetch_html(url)
            result = await parse_links_with_gemini(html, today_iso_local, timezone)
            links = result.links
            if not links:
                # Gemini fallback: deterministic heading-based extraction
                links = extract_links_with_heading_filter(html, today_iso_local)
            all_links.extend(links)

        # Filter to today and dedupe (placeholder known set empty; integrate with storage later)
        only_today = filter_only_today(all_links, today_iso_local)
        known = get_known_fingerprints(post_id, today_iso_local)
        deduped = dedupe_by_fingerprint(only_today, known_fingerprints=known)

        if deduped:
            save_new_links(post_id, today_iso_local, {fingerprint(link) for link in deduped})

        # Update WordPress
        await update_post_links_section(post_id, deduped)

    return asyncio.run(run())

# Follow-up Implementation Tasks

1. Integrate Google Gemini SDK in `backend/app/llm.py` with schema validation and fallback to deterministic parser.
2. Replace temporary storage in `backend/app/storage.py` with MongoDB Atlas using `motor`.
3. Refine WordPress updater to use a custom block or ACF field rather than prepending HTML.
4. Add rate limiting and retry policies for scraping providers.
5. Create WordPress admin plugin/button to call the Cloud Run API securely.

# Testing Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /home/deepak/data/SmartLinkUpdater
pip install -r backend/requirements.txt
```

### 2. Run Unit Tests (No API Key Required)

```bash
# Run all unit tests
python -m pytest backend/tests/ -v --ignore=backend/tests/test_gemini_integration.py

# Or use the test script
chmod +x backend/scripts/test_all.sh
./backend/scripts/test_all.sh
```

### 3. Test Gemini Integration (Requires API Key)

Get your Gemini API key from: https://aistudio.google.com/app/apikey

```bash
# Set your API key
export GEMINI_API_KEY="your-key-here"

# Run integration test
python -m backend.tests.test_gemini_integration

# Or run all tests including integration
./backend/scripts/test_all.sh
```

## What Gets Tested

### Unit Tests (No API calls)
- ✅ Gemini client error handling
- ✅ LLM module with mocked responses
- ✅ Confidence threshold validation
- ✅ Malformed link handling
- ✅ Prompt building and truncation
- ✅ Fallback behavior when API key missing
- ✅ Link deduplication
- ✅ Deterministic HTML extraction

### Integration Test (Real API)
- ✅ Real Gemini API call
- ✅ Schema enforcement
- ✅ Section filtering ("Links for Today")
- ✅ Date-based extraction
- ✅ JSON response parsing

## Test Coverage

Run with coverage report:

```bash
pip install pytest-cov
python -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

## Expected Results

### Without GEMINI_API_KEY
- Unit tests: **PASS** (mocked responses)
- Integration test: **SKIPPED**

### With GEMINI_API_KEY
- Unit tests: **PASS**
- Integration test: **PASS** (validates real API)

## Troubleshooting

### Import Errors
If you see "Import 'pytest' could not be resolved":
```bash
pip install -r backend/requirements.txt
```

### Gemini API Errors
- Check your API key is valid
- Verify you're within free tier limits (15 RPM)
- Check network connectivity

### Test Failures
Run with verbose output:
```bash
python -m pytest backend/tests/ -vv --tb=long
```

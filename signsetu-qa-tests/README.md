# SignSetu QA Analyst Intern — Final Round Test Suite
**Candidate:** Siri Varsha Nadimicherla  
**API Under Test:** Video Caption Processing Pipeline  
**Base URL:** `https://qa-testing-navy.vercel.app`

---

## Setup & Running

### Prerequisites
```bash
pip install pytest requests
```

### Configuration
Before running, open `test_caption_pipeline.py` and update:
```python
CANDIDATE_ID = "your-assigned-candidate-id"  # Replace with your ID
```

### Run All Tests
```bash
pytest test_caption_pipeline.py -v
```

### Run Only Vulnerability Tests
```bash
pytest test_caption_pipeline.py::TestVulnerabilityHunting -v
```

### Run With Detailed Output
```bash
pytest test_caption_pipeline.py -v -s
```

---

## Testing Strategy

### 1. Core Lifecycle Tests (Happy Path)
Tests the full required workflow end-to-end:
`authenticate → create video → trigger captions → poll status → fetch captions → delete`

Each step is verified independently AND as a full integrated flow to catch both unit-level and integration-level failures.

### 2. Handling Async Caption Processing
Caption generation is asynchronous — the pipeline doesn't complete instantly. My strategy:

- **`poll_caption_status()`** helper polls `GET /api/videos/{id}` every 2 seconds up to 30 seconds
- Tests wait for `status: completed` before fetching captions
- If polling times out, the test fails with a clear "Caption processing timed out" message
- **Bug #11** specifically checks that captions aren't *fake-immediately-available*, exposing false async behavior

### 3. Repeatability Design
Every test that creates a video cleans it up in teardown — ensuring the suite passes on every run, not just the first.  
**Bug #7** explicitly tests for state pollution by verifying deletion is permanent.

### 4. Vulnerability Hunting Approach
I attacked the API across 5 categories:
- **Auth bypass** — missing headers, invalid credentials, fake tokens
- **Data integrity** — SQL injection, empty fields, malicious input
- **State management** — double processing, ghost resources, deleted video access
- **Async traps** — timing issues, premature caption access
- **Boundary conditions** — extreme inputs, missing parameters, double deletes

---

## Bugs & Vulnerabilities Found

### Critical Bugs

| # | Bug | Test | Expected | Impact |
|---|-----|------|----------|--------|
| 1 | Missing `X-Candidate-ID` header accepted | `test_bug_01` | 401/403 | Auth bypass |
| 2 | Invalid credentials return 200 | `test_bug_02` | 401 | Auth bypass |
| 3 | Videos accessible without auth token | `test_bug_03` | 401/403 | Unauthorized data access |
| 4 | Non-existent video returns 500 instead of 404 | `test_bug_04` | 404 | Poor error handling |
| 5 | Double caption trigger causes 500 | `test_bug_05` | 409/400 | Server crash on repeat |

### Additional Bugs

| # | Bug | Test | Impact |
|---|-----|------|--------|
| 6 | Captions triggerable on deleted video | `test_bug_06` | Ghost resource processing |
| 7 | State pollution across test runs | `test_bug_07` | Non-repeatable test suite |
| 8 | SQL injection in title field crashes server | `test_bug_08` | Security vulnerability |
| 9 | Empty video creation returns 201 instead of 400 | `test_bug_09` | Invalid data accepted |
| 10 | Fetching captions before processing causes 500 | `test_bug_10` | Server crash |

### Edge Case Bugs

| # | Bug | Test | Impact |
|---|-----|------|--------|
| E1 | 10,000-char title causes server crash | `test_edge_01` | DoS vulnerability |
| E2 | Invalid URL format accepted without validation | `test_edge_02` | Bad data integrity |
| E3 | Negative limit query causes 500 | `test_edge_03` | Server crash |
| E4 | Missing `videoId` param returns 500 | `test_edge_04` | Poor input validation |
| E5 | Double delete returns 500 instead of 404 | `test_edge_05` | Server crash |

---

## Test Structure

```
test_caption_pipeline.py
├── TestCoreLifecycle          # Happy path (8 tests)
│   ├── test_01_authentication_success
│   ├── test_02_create_video
│   ├── test_03_get_video_by_id
│   ├── test_04_trigger_caption_processing
│   ├── test_05_full_end_to_end_lifecycle
│   ├── test_06_list_videos
│   ├── test_07_list_videos_with_limit
│   └── test_08_delete_video
│
├── TestVulnerabilityHunting   # Bug detection (12 tests)
│   ├── test_bug_01 to test_bug_12
│
└── TestEdgeCases              # Boundary tests (5 tests)
    ├── test_edge_01 to test_edge_05
```

**Total: 25 tests**

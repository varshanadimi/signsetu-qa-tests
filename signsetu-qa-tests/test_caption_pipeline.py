"""
SignSetu QA Analyst Intern - Final Round Test Suite
Automated tests for Video Caption Processing Pipeline
Base URL: https://qa-testing-navy.vercel.app
Author: Siri Varsha Nadimicherla
"""

import requests
import time
import pytest
import uuid

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
BASE_URL = "https://qa-testing-navy.vercel.app"
CANDIDATE_ID = "siri-varsha-nadimicherla"  # Replace with your assigned ID

HEADERS = {
    "X-Candidate-ID": nsirivarsha@gmail.com,
    "Content-Type": "application/json"
}


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def get_auth_token():
    """Authenticate and return session token."""
    response = requests.post(
        f"{BASE_URL}/api/auth",
        headers=HEADERS,
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in auth response"
    return data["token"]


def get_auth_headers():
    """Get headers including auth token."""
    token = get_auth_token()
    return {**HEADERS, "Authorization": f"Bearer {token}"}


def create_video(auth_headers, title="Test Video", url="https://example.com/video.mp4"):
    """Create a video and return its ID."""
    response = requests.post(
        f"{BASE_URL}/api/videos",
        headers=auth_headers,
        json={"title": title, "url": url}
    )
    assert response.status_code == 201, f"Video creation failed: {response.text}"
    data = response.json()
    assert "id" in data, "No ID in video creation response"
    return data["id"]


def cleanup_video(auth_headers, video_id):
    """Delete a video — used in teardown."""
    response = requests.delete(
        f"{BASE_URL}/api/videos/{video_id}",
        headers=auth_headers
    )
    return response


def poll_caption_status(auth_headers, video_id, max_wait=30, interval=2):
    """Poll video status until captions are ready or timeout."""
    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        status = data.get("status", "")
        if status in ["completed", "failed", "error"]:
            return status, data
        time.sleep(interval)
        elapsed += interval
    return "timeout", {}


# ─────────────────────────────────────────────
# TEST CLASS: HAPPY PATH (CORE LIFECYCLE)
# ─────────────────────────────────────────────
class TestCoreLifecycle:

    def test_01_authentication_success(self):
        """Verify valid credentials return a session token."""
        response = requests.post(
            f"{BASE_URL}/api/auth",
            headers=HEADERS,
            json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data, "Token missing from auth response"
        assert len(data["token"]) > 0, "Token is empty"

    def test_02_create_video(self):
        """Verify a video record can be created successfully."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Core Lifecycle Test Video")
        assert video_id is not None
        # Teardown
        cleanup_video(auth_headers, video_id)

    def test_03_get_video_by_id(self):
        """Verify created video can be retrieved by ID."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Get By ID Test")
        response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        # Teardown
        cleanup_video(auth_headers, video_id)

    def test_04_trigger_caption_processing(self):
        """Verify caption processing job can be triggered."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Caption Trigger Test")
        response = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )
        assert response.status_code in [200, 202], \
            f"Caption trigger failed: {response.text}"
        # Teardown
        cleanup_video(auth_headers, video_id)

    def test_05_full_end_to_end_lifecycle(self):
        """Full lifecycle: auth → create → trigger → poll → fetch captions → delete."""
        auth_headers = get_auth_headers()

        # Create
        video_id = create_video(auth_headers, title="E2E Lifecycle Test")

        # Trigger
        trigger_response = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )
        assert trigger_response.status_code in [200, 202]

        # Poll for completion
        final_status, video_data = poll_caption_status(auth_headers, video_id)
        assert final_status != "timeout", "Caption processing timed out"
        assert final_status == "completed", f"Unexpected status: {final_status}"

        # Fetch captions
        captions_response = requests.get(
            f"{BASE_URL}/api/captions?videoId={video_id}",
            headers=auth_headers
        )
        assert captions_response.status_code == 200
        captions_data = captions_response.json()
        assert captions_data is not None, "Captions response is empty"

        # Teardown
        delete_response = cleanup_video(auth_headers, video_id)
        assert delete_response.status_code in [200, 204]

    def test_06_list_videos(self):
        """Verify GET /api/videos returns a list."""
        auth_headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/videos",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected list of videos"

    def test_07_list_videos_with_limit(self):
        """Verify limit query parameter works on video listing."""
        auth_headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/videos?limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2, f"Limit not respected: got {len(data)} videos"

    def test_08_delete_video(self):
        """Verify video is properly deleted and no longer accessible."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Delete Test Video")

        # Delete
        delete_response = cleanup_video(auth_headers, video_id)
        assert delete_response.status_code in [200, 204]

        # Verify deleted — should return 404
        get_response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404, \
            "BUG: Deleted video is still accessible!"


# ─────────────────────────────────────────────
# TEST CLASS: VULNERABILITY HUNTING (BUG DETECTION)
# ─────────────────────────────────────────────
class TestVulnerabilityHunting:

    # ── BUG 1: Authentication bypass ──
    def test_bug_01_missing_candidate_id_header(self):
        """BUG CHECK: Requests without X-Candidate-ID should be rejected."""
        headers_without_id = {"Content-Type": "application/json"}
        response = requests.post(
            f"{BASE_URL}/api/auth",
            headers=headers_without_id,
            json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code in [400, 401, 403], \
            "BUG FOUND: API accepts requests without X-Candidate-ID header!"

    # ── BUG 2: Auth with invalid credentials ──
    def test_bug_02_invalid_credentials_rejected(self):
        """BUG CHECK: Invalid credentials should return 401, not 200."""
        response = requests.post(
            f"{BASE_URL}/api/auth",
            headers=HEADERS,
            json={"username": "hacker", "password": "wrongpassword"}
        )
        assert response.status_code == 401, \
            f"BUG FOUND: Invalid credentials accepted! Status: {response.status_code}"

    # ── BUG 3: Unauthenticated access to protected routes ──
    def test_bug_03_unauthenticated_video_access(self):
        """BUG CHECK: Accessing videos without auth token should be rejected."""
        response = requests.get(
            f"{BASE_URL}/api/videos",
            headers=HEADERS  # No Authorization header
        )
        assert response.status_code in [401, 403], \
            "BUG FOUND: Videos accessible without authentication!"

    # ── BUG 4: Accessing non-existent video ──
    def test_bug_04_nonexistent_video_returns_404(self):
        """BUG CHECK: Non-existent video ID should return 404, not 500."""
        auth_headers = get_auth_headers()
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/videos/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404, \
            f"BUG FOUND: Expected 404 for missing video, got {response.status_code}"

    # ── BUG 5: Double processing (idempotency) ──
    def test_bug_05_double_caption_trigger(self):
        """BUG CHECK: Triggering captions twice on same video should be handled gracefully."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Double Trigger Test")

        # First trigger
        first_response = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )
        assert first_response.status_code in [200, 202]

        # Second trigger — should not cause 500 error
        second_response = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )
        assert second_response.status_code != 500, \
            "BUG FOUND: Double trigger causes 500 Internal Server Error!"
        assert second_response.status_code in [200, 202, 400, 409], \
            f"BUG FOUND: Unexpected status on double trigger: {second_response.status_code}"

        # Teardown
        cleanup_video(auth_headers, video_id)

    # ── BUG 6: Processing deleted video ──
    def test_bug_06_process_captions_on_deleted_video(self):
        """BUG CHECK: Cannot trigger captions on a deleted video."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Ghost Processing Test")

        # Delete first
        cleanup_video(auth_headers, video_id)

        # Then try to trigger captions
        response = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )
        assert response.status_code in [404, 400], \
            "BUG FOUND: Can trigger captions on a deleted video!"

    # ── BUG 7: Repeatability trap — unique state pollution ──
    def test_bug_07_test_suite_repeatability(self):
        """BUG CHECK: Running suite twice should produce same results (no state pollution)."""
        auth_headers = get_auth_headers()

        # Create video with deterministic title
        unique_title = f"Repeatability Test {uuid.uuid4()}"
        video_id = create_video(auth_headers, title=unique_title)

        # Verify it exists
        response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Clean up — MUST delete to ensure repeatability
        delete_response = cleanup_video(auth_headers, video_id)
        assert delete_response.status_code in [200, 204], \
            "BUG FOUND: Cleanup failed — test suite will fail on second run!"

        # Verify truly deleted
        verify_response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        assert verify_response.status_code == 404, \
            "BUG FOUND: Video persists after deletion — state pollution detected!"

    # ── BUG 8: SQL/NoSQL injection in video creation ──
    def test_bug_08_sql_injection_in_title(self):
        """BUG CHECK: Malicious input in title field should be sanitized."""
        auth_headers = get_auth_headers()
        malicious_title = "'; DROP TABLE videos; --"
        response = requests.post(
            f"{BASE_URL}/api/videos",
            headers=auth_headers,
            json={"title": malicious_title, "url": "https://example.com/video.mp4"}
        )
        # Should either sanitize (201) or reject (400) — never crash (500)
        assert response.status_code != 500, \
            "BUG FOUND: SQL injection causes 500 Internal Server Error!"

        if response.status_code == 201:
            video_id = response.json().get("id")
            if video_id:
                cleanup_video(auth_headers, video_id)

    # ── BUG 9: Empty/missing required fields ──
    def test_bug_09_create_video_missing_fields(self):
        """BUG CHECK: Creating video without required fields should return 400."""
        auth_headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/videos",
            headers=auth_headers,
            json={}  # No title, no URL
        )
        assert response.status_code == 400, \
            f"BUG FOUND: Empty video creation returns {response.status_code} instead of 400!"

    # ── BUG 10: Fetch captions for video with no captions yet ──
    def test_bug_10_captions_before_processing(self):
        """BUG CHECK: Fetching captions before processing should return 404 or empty, not 500."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Pre-Processing Captions Test")

        response = requests.get(
            f"{BASE_URL}/api/captions?videoId={video_id}",
            headers=auth_headers
        )
        assert response.status_code != 500, \
            "BUG FOUND: Fetching captions before processing causes 500!"
        assert response.status_code in [200, 404, 400], \
            f"Unexpected status code: {response.status_code}"

        # Teardown
        cleanup_video(auth_headers, video_id)

    # ── BUG 11: Async timing trap ──
    def test_bug_11_captions_not_immediately_available(self):
        """BUG CHECK: Captions should NOT be available immediately after trigger."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Async Timing Test")

        # Trigger processing
        requests.post(
            f"{BASE_URL}/api/videos/{video_id}/process-captions",
            headers=auth_headers
        )

        # Immediately check status — should NOT be completed yet
        response = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers
        )
        data = response.json()
        # If immediately completed, it might be faking async behavior
        immediate_status = data.get("status", "")
        print(f"Immediate status after trigger: {immediate_status}")
        # Not a hard fail — just log for investigation
        # A real async system should show 'processing' first

        # Teardown
        cleanup_video(auth_headers, video_id)

    # ── BUG 12: Token reuse after expiry ──
    def test_bug_12_expired_or_invalid_token_rejected(self):
        """BUG CHECK: Fake/expired token should be rejected."""
        fake_token_headers = {
            **HEADERS,
            "Authorization": "Bearer fake_token_12345_invalid"
        }
        response = requests.get(
            f"{BASE_URL}/api/videos",
            headers=fake_token_headers
        )
        assert response.status_code in [401, 403], \
            "BUG FOUND: Fake token accepted by API!"


# ─────────────────────────────────────────────
# TEST CLASS: EDGE CASES & BOUNDARY TESTS
# ─────────────────────────────────────────────
class TestEdgeCases:

    def test_edge_01_very_long_video_title(self):
        """Edge case: Extremely long title should not cause 500."""
        auth_headers = get_auth_headers()
        long_title = "A" * 10000
        response = requests.post(
            f"{BASE_URL}/api/videos",
            headers=auth_headers,
            json={"title": long_title, "url": "https://example.com/video.mp4"}
        )
        assert response.status_code != 500, \
            "BUG FOUND: Extremely long title causes server crash!"
        if response.status_code == 201:
            video_id = response.json().get("id")
            if video_id:
                cleanup_video(auth_headers, video_id)

    def test_edge_02_invalid_video_url(self):
        """Edge case: Invalid URL format should be validated."""
        auth_headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/videos",
            headers=auth_headers,
            json={"title": "Invalid URL Test", "url": "not-a-valid-url"}
        )
        assert response.status_code != 500, \
            "BUG FOUND: Invalid URL causes server crash!"

        if response.status_code == 201:
            video_id = response.json().get("id")
            if video_id:
                cleanup_video(auth_headers, video_id)

    def test_edge_03_negative_limit_query(self):
        """Edge case: Negative limit value should be handled gracefully."""
        auth_headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/videos?limit=-1",
            headers=auth_headers
        )
        assert response.status_code != 500, \
            "BUG FOUND: Negative limit causes server crash!"

    def test_edge_04_captions_missing_video_id(self):
        """Edge case: Fetching captions without videoId param."""
        auth_headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/captions",
            headers=auth_headers
        )
        assert response.status_code in [400, 422], \
            f"BUG FOUND: Missing videoId param returns {response.status_code} instead of 400!"

    def test_edge_05_delete_already_deleted_video(self):
        """Edge case: Deleting a video twice should not cause 500."""
        auth_headers = get_auth_headers()
        video_id = create_video(auth_headers, title="Double Delete Test")

        # First delete
        first_delete = cleanup_video(auth_headers, video_id)
        assert first_delete.status_code in [200, 204]

        # Second delete
        second_delete = cleanup_video(auth_headers, video_id)
        assert second_delete.status_code != 500, \
            "BUG FOUND: Deleting already-deleted video causes 500!"
        assert second_delete.status_code == 404, \
            "BUG FOUND: Expected 404 when deleting non-existent video!"

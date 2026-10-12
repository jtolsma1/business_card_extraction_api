"""
Takes image bytes and a media type, base64-encodes them, and acquires the semaphore. The semaphore wraps only the Claude call, so downloads aren’t throttled.
It calls your existing async Claude helper and maps Anthropic’s exception types onto your domain exceptions. Retry policy: let the SDK’s built-in retries handle transient errors, back off on 429, and fail fast on 401. Don’t rebuild the client.
The media type is a parameter, not a hardcoded image/jpeg.
Fake mode sleeps for the configured delay and returns canned data, with no network involved.
"""
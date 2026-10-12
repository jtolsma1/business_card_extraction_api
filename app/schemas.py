"""
Request model: one field, the image URL, validated as a real URL.
Response model: request ID, business name, person name, contact numbers, timings (total, download, Claude), and token usage.
Error model: a machine-readable error code, a human message, and the request ID.
Your existing business-card model lives here. A failed extraction must produce an error response, never the empty-but-valid card your pipeline used as a fallback.
"""
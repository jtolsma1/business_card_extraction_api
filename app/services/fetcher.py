"""
Check the host against the allowlist (it must include the web.cs.wpi.edu host) and GET with your descriptive User-Agent.
Don’t follow redirects blindly. A redirect can send you to a host you never allowed.
Reject private IP ranges, enforce the size cap, and verify the content type.
Return the bytes, the media type, and the download time.
"""
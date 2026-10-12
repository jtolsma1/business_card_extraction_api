"""
A small family of domain exceptions and the handlers that turn each into the one error shape:
Situation	Status
Host not on allowlist = 422
URL unreachable or returns non-200 = 422
Not an image / unsupported type	= 415
Image too large	= 413
Claude rate limit or overload = 503
Claude timeout = 504
Claude connection or other failure = 502
A bad API key (401) is logged loudly and returned to the caller as a generic 500 or 502, so your credentials never leak into responses.
"""
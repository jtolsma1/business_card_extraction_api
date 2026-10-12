"""
POST /v1/extractions, with an async def handler. It stays thin: start a monotonic timer, make a request ID, call the fetcher, call the extractor, and assemble the response with timings. No business logic lives here.
"""
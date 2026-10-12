"""
Builds the app and defines the lifespan. On startup it creates the httpx2 async client (with timeouts and a connection limit), the AsyncAnthropic client, and the semaphore sized from settings, and stores them on app state. On shutdown it closes both clients.
It registers the routers and error handlers.
Optionally, a middleware assigns each request an ID and logs start and finish.
"""
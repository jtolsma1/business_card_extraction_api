"""
One settings object, loaded once from the process environment (pydantic-settings fits the FastAPI/Pydantic stack).
It holds the Anthropic key, model name, allowed image hosts, max concurrent Claude calls, fetch and Claude timeouts, max image size, the User-Agent string for fetches, and the fake-extractor flag plus its simulated delay.
It reads the environment directly, with no python-dotenv in the container. Compose supplies the variables.
"""
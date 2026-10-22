"""
Small providers that hand the shared httpx2 client, Anthropic client, semaphore, and settings to handlers, so handlers just declare what they need as parameters.
"""

from fastapi import Request
from app.settings import get_settings

def get_httpx2_client(request:Request):
    return request.app.state.httpx2_client

def get_anthropic_client(request:Request):
    return request.app.state.anthropic_client

def get_semaphore(request:Request):
    return request.app.state.semaphore


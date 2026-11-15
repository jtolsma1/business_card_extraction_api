# Business Card Extraction API
 
An asynchronous FastAPI service that takes the URL of a business card image, downloads it, reads it with a vision language model (Claude), and returns the business name, person name and contact numbers, plus timing for each step.
 
It is also a self-study project. The point of building it was to learn asynchronous Python by making one thing run concurrently and then measuring whether it really does.
 
## Why this repo exists
 
I'm an ML engineer working toward LLMOps and ML infrastructure, and I wanted to build skills related to the concurrency side of serving models. I worked through a course on asynchronous Python (threading, multiprocessing and `asyncio`), and then gave myself a capstone: build a small API that can serve many requests at once on a single event loop, run it in Docker, and prove it with a load test.
 
The success criterion was simple: a batch of concurrent requests should finish in far less time than the same requests made one after another. I wrote every file myself, except for this README (which Claude wrote).
 
## What it does
 
`POST /v1/contact_info_extract` with a JSON body:
 
```json
{
  "request_id": "demo-001",
  "source_system": "readme-example",
  "card_url": "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/001.jpg"
}
```
 
returns:
 
```json
{
  "request_id": "demo-001",
  "business_name": "Test Business, Inc.",
  "person_name": "John Doe",
  "contact_numbers": ["+1-555-555-1234", "+1-555-555-5555"],
  "download_time": 0.9,
  "vlm_response_time": 3.1,
  "total_response_time": 4.0
}
```
 
(That example is the fake extractor's output, and the times are illustrative.) Times are in seconds. Failures come back as JSON with a `code`, a `message` and a `request_id`. `GET /v1/health` is a simple liveness check, and interactive documentation is served at `/docs`.
 
## Quick start
 
You need Docker with Docker Compose. An Anthropic API key is only needed if you want to call the real model.
 
```bash
git clone https://github.com/jtolsma1/business_card_extraction_api.git
cd business_card_extraction_api
 
cp .env.example .env
# Edit .env. For a first try, leave USE_FAKE_EXTRACTOR=true.
# CLAUDE_API_KEY must still be set to something; any placeholder works
# while the fake extractor is on.
 
docker compose up --build
```
 
Then open <http://localhost:8000/docs> and use "Try it out" on the extraction route.
 
To use the real model, set `USE_FAKE_EXTRACTOR=false`, put a valid key in `CLAUDE_API_KEY`, and recreate the container with `docker compose up -d --force-recreate` (Compose reads `.env` when the container is created, so a plain restart keeps the old values).
 
### Run the load test
 
With the API running, and the dependencies installed in a local virtual environment (`pip install -r requirements.txt`):
 
```bash
python scripts/load_test.py
```
 
It sends the same batch of card URLs twice, once one at a time and once all at once, and prints the total time, success and failure counts and extraction counts for each pass.

## Where to find test images
 
The business card images used for this project belong to a Stanford dataset and are hosted by [Worcester Polytechnic Institute (WPI)](https://www.wpi.edu/) on its website. You can browse them here:
 
<https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/index.html>
 
The images are numbered JPEG files, so the URL of a single card looks like this, and that is the value to send in the `card_url` field of a request:
 
```
https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/001.jpg
```
 
A few things to know when using them:
 
- **The images are not included in this repository.** The API downloads each one from WPI at request time, and the load test does the same.
- **The host must be on the allowlist.** The API only downloads from hosts listed in `ALLOWED_IMAGE_HOSTS`, so `web.cs.wpi.edu` has to be in that list, and the image's content type (JPEG, for this dataset) has to be in `ALLOWED_IMAGE_TYPES`. Any other host is rejected before a download starts.
- **All testing used this dataset.** Everything in this project, including the load test results below, was run against these images. I did not try other business card datasets, so I can't say how well the extraction holds up on cards with very different layouts, languages or photo conditions.
 
## Results
 
20 card images, real model calls (`claude-haiku-5-5`), default limit of 5 concurrent model calls, one run on my laptop:
 
| Pass | Total time | Successful responses |
|---|---|---|
| Sequential | 66.7 s | 20 / 20 |
| Concurrent | 9.3 s | 20 / 20 |
 
That is about a 7x speedup, and the extracted counts were identical in both passes, so concurrency did not change the results. This is a single run on a small sample, so treat the exact figure as indicative. 

The speedup is below 20x on purpose: the semaphore limits concurrent model calls to 5, so the calls go out in waves, while the image downloads overlap freely.
 
## How it's built
 
```
app/
  main.py            app creation, lifespan, exception handler registration
  settings.py        configuration from environment variables (pydantic-settings)
  schemas.py         request and response models
  errors.py          error classes and the exception handler
  dependencies.py    Depends() providers for shared resources
  routers/routers.py the routes
  services/fetcher.py    image download and validation
  services/extractor.py  model call (and the fake extractor)
scripts/load_test.py     the sequential vs concurrent load test
Dockerfile
docker-compose.yaml
```
 
A few design choices worth noting:
 
- **One event loop, shared resources.** The HTTP client, the Anthropic client, the semaphore and the settings are created once in the app's `lifespan`, stored on `app.state`, and handed to routes with `Depends`. The code that opens them also closes them.
- **The semaphore wraps only the model call.** Downloads are not gated, so the limit applies to the expensive, rate-limited part.
- **Safe-ish downloads.** The image host is checked against an allowlist, the content type is checked, and the download is streamed and stopped as soon as it passes the maximum size, so an oversized file is never fully held in memory.
- **Structured output.** The model call uses the Anthropic SDK's `messages.parse` with a Pydantic model, so the reply arrives as a validated object.
- **Errors are classes.** Services raise subclasses of `AppError`, which carry an HTTP status. One registered exception handler turns them into a consistent JSON response.
- **A fake extractor** (`USE_FAKE_EXTRACTOR=true`) sleeps for a random interval instead of calling the model, so the concurrency behavior can be tested without spending API credits.
## Limitations
 
This is a learning project, not a production service. It runs a single worker process, has no authentication, no persistence and no rate limiting of its own, and it was only tested on a small set of card images.
 
## Credits and license
 
The test images come from the Stanford mobile visual search business-card dataset, as hosted at `web.cs.wpi.edu`. They are not included in this repository. Released under the MIT license.
 
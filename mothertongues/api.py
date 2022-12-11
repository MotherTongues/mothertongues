"""
REST Web API for Mother Tongues Dictionaries using FastAPI.
See https://mothertongues.herokuapp.com/api/v1/docs for the documentation.
You can spin up this Web API for development purposes with:
    cd mothertongues/
    PRODUCTION= uvicorn mothertongues.api:app --reload
- The --reload switch will watch for changes under the directory where it's
  running and reload the code whenever it changes, so it's best run in mothertongues/
- PRODUCTION= tells uvicorn to run in non-production mode, i.e., in debug mode,
  and automatically add the header "access-control-allow-origin: *" to each
  response so you won't get CORS errors using this locally with Mother Tongues Dictionaries.
You can also spin up the API server grade (on Linux, not Windows) with gunicorn:
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker mothertongues.api:app
Once spun up, the documentation and API playground will be visible at
http://localhost:8000/api/v1/docs
"""

from fastapi import FastAPI

app = FastAPI()

v1 = FastAPI()

app.mount("/api/v1", v1)

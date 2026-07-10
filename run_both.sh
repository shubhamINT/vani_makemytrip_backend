#!/bin/bash

uv run server_run.py &
uv run python -m app.agent dev &
wait
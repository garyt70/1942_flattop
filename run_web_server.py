"""Run the 1942 Flat Top web application (API + static web client).

Usage:
    python run_web_server.py [--host HOST] [--port PORT] [--reload]
"""

import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the 1942 Flat Top web server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("flattop.api.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

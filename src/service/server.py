import argparse

import uvicorn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local X scrape service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8797)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.host != "127.0.0.1":
        raise ValueError("Only loopback host 127.0.0.1 is allowed")
    uvicorn.run("service.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()

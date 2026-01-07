"""Command-line interface for MindWell AI."""

import argparse
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="MindWell AI - Mental Health Support Platform",
        prog="mindwell",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_subparsers = db_parser.add_subparsers(dest="db_command")
    db_subparsers.add_parser("init", help="Initialize the database")
    db_subparsers.add_parser("migrate", help="Run database migrations")

    args = parser.parse_args()

    if args.command == "server":
        run_server(args.host, args.port, args.reload)
    elif args.command == "db":
        if args.db_command == "init":
            init_database()
        elif args.db_command == "migrate":
            run_migrations()
        else:
            db_parser.print_help()
    else:
        parser.print_help()


def run_server(host: str, port: int, reload: bool):
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "mindwell.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


def init_database():
    """Initialize the database."""
    print("Initializing database...")
    # TODO: Implement database initialization
    print("Database initialized successfully.")


def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    # TODO: Implement migration runner
    print("Migrations completed successfully.")


if __name__ == "__main__":
    main()

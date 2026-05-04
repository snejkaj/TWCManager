from __future__ import annotations

import argparse

from .app import TWCManagerApp
from .config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", action="store_true", help="Enable RS-485 serial transport loop")
    parser.add_argument("--loop-delay", type=float, default=1.0, help="Control-loop delay in seconds")
    args = parser.parse_args()

    settings = load_settings()
    app = TWCManagerApp(settings=settings)
    app.run(loop_delay_s=args.loop_delay, with_serial=args.serial)


if __name__ == "__main__":
    main()

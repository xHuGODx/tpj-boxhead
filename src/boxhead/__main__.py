"""Ponto de entrada; importar o pacote não abre janelas."""

import argparse
import os


def positive_integer(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("frame count must be positive")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="Boxhead — TPJ")
    parser.add_argument("--frames", type=positive_integer, help="exit after N frames")
    parser.add_argument("--headless", action="store_true", help="run without a window or audio")
    parser.add_argument("--fullscreen", action="store_true", default=None, help="start in fullscreen")
    args = parser.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    from boxhead.app import App
    from boxhead.config import AppConfig

    App(AppConfig(fullscreen=args.fullscreen)).run(max_frames=args.frames)


if __name__ == "__main__":
    main()

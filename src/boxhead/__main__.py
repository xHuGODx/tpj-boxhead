"""Ponto de entrada; importar o pacote não abre janelas."""

import argparse
import os


def positive_integer(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("o número de frames tem de ser positivo")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="Boxhead — TPJ")
    parser.add_argument("--frames", type=positive_integer, help="terminar após N frames")
    parser.add_argument("--headless", action="store_true", help="executar sem janela nem áudio")
    args = parser.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    # O SDL só é configurado depois de interpretar os argumentos.
    from boxhead.app import App

    App().run(max_frames=args.frames)


if __name__ == "__main__":
    main()

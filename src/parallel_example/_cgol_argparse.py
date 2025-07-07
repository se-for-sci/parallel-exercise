import argparse


def get_parser():
    parser = argparse.ArgumentParser(description="Runs Conway's game of life.")
    parser.add_argument(
        "-x",
        "--width",
        default=-1,
        type=int,
        dest="width",
        help="number of columns in the game (must be multiple of 2)."
        " Negative values set to the terminal size.",
    )
    parser.add_argument(
        "-y",
        "--height",
        default=-1,
        type=int,
        dest="height",
        help="number of rows in the game (must be multiple of 4)"
        " Negative values set to the terminal size.",
    )
    parser.add_argument(
        "-j",
        "--parallel",
        default=0,
        type=int,
        dest="num_workers",
        help="number of workers to run in parallel."
        " Nonpositive values make the process run in serial.",
    )
    parser.add_argument(
        "-t",
        "--time",
        default=5,
        type=float,
        dest="runtime",
        help="amount of time to run for",
    )
    parser.add_argument(
        "-r",
        "--fps",
        default=60,
        type=float,
        dest="framerate",
        help="number of updates per second",
    )
    parser.add_argument(
        "--skip_synthetic_delay",
        action="store_false",
        dest="synthetic_delay",
        help="if set, does not impose a synthetic delay to"
        " the display() call through time.sleep()",
    )
    return parser

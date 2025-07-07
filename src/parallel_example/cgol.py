import os
import threading
import time

import numpy as np

from . import _cgol_argparse


def _apply_CGOL_to_cell(
    cells: np.ndarray, cells_framebuffer: np.ndarray, row: int, col: int
):
    if cells[row, col]:
        # exclude self
        num_neighbors = (
            np.count_nonzero(cells[(row - 1) : (row + 2), (col - 1) : (col + 2)]) - 1
        )
        # lives if 2 or 3 neighbors; else dies
        cells_framebuffer[row, col] = num_neighbors in {2, 3}
    else:
        num_neighbors = np.count_nonzero(
            cells[(row - 1) : (row + 2), (col - 1) : (col + 2)]
        )
        # dead cell only revives if exactly 3 neighbors
        cells_framebuffer[row, col] = num_neighbors in {3}


class Conway:
    height: int
    width: int

    cells: np.ndarray
    cells_framebuffer: np.ndarray

    def __init__(self, height: int, width: int):
        if height % 4 != 0:
            msg = "Height must be a multiple of 4"
            raise ValueError(msg)
        if width % 2 != 0:
            msg = "Width must be a multiple of 2"
            raise ValueError(msg)
        self.height = height
        self.width = width

        self.cells = np.zeros((height, width), dtype=bool)
        self.cells_framebuffer = np.zeros((height, width), dtype=bool)

    def step(self):
        """Performs one step of CGOL, updating the frame buffer.
        This operates in series.
        """
        for i in range(self.height):
            for j in range(self.width):
                _apply_CGOL_to_cell(self.cells, self.cells_framebuffer, i, j)

    def step_parallel_threading(self, num_workers: int | None = None):
        """Performs one step of CGOL, updating the frame buffer.
        This operates in parallel, using threads.

        Args:
            num_workers (int | None, optional): The number of workers
                (threads, processes, etc) used for this task. When None,
                the value `os.process_cpu_count()` is chosen. Defaults to None.
        """
        if num_workers is None:
            num_workers = os.process_cpu_count()

        num_cells = self.height * self.width
        cells_per_worker = num_cells // num_workers + (
            0 if num_cells % num_workers == 0 else 1
        )

        def apply_CGOL_range(
            cells: np.ndarray,
            cells_framebuffer: np.ndarray,
            width: int,
            start: int,
            end: int,
        ):
            for i in range(start, end):
                row = i // width
                col = i % width
                _apply_CGOL_to_cell(cells, cells_framebuffer, row, col)

        threads = []
        start = 0
        for _ in range(num_workers):
            end = min(start + cells_per_worker, num_cells)
            threads.append(
                threading.Thread(
                    target=apply_CGOL_range,
                    args=(self.cells, self.cells_framebuffer, self.width, start, end),
                )
            )
            start = end
            threads[-1].start()

        for t in threads:
            t.join()

    def step_parallel(self, num_workers: int | None = None):
        """Performs one step of CGOL, updating the frame buffer.
        You are to implement this function to match the other step functions.

        Args:
            num_workers (int | None, optional): The number of workers
                (threads, processes, etc) used for this task. When None,
                the value `os.process_cpu_count()` is chosen. Defaults to None.
        """
        if num_workers is None:
            num_workers = os.process_cpu_count()
        raise NotImplementedError

    def __str__(self):
        char_height = self.height // 4
        char_width = self.width // 2

        # display leverages the unicode braille characters
        # https://en.wikipedia.org/wiki/Braille_Patterns
        chars = np.zeros((char_height, char_width), dtype=int)

        for i, (offset_vert, offset_horiz) in enumerate(
            [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 0), (3, 1)]
        ):
            chars += self.cells[offset_vert::4, offset_horiz::2] * (1 << i)

        return "\n".join(
            "".join(chr(0x2800 + c) for c in chars[row, :])
            for row in range(char_height)
        )

    def display(self, replace_prior: bool = False, synthetic_delay: bool = True):
        if replace_prior:
            # escape code for returning number of lines
            print(f"\x1b[{self.height // 4}A")  # noqa: T201
        if synthetic_delay:
            # to pretend the display() method takes a long time.
            time.sleep(0.05)
        print(str(self), end="\r")  # noqa: T201

    def swap_buffers(self):
        """Swaps the frame buffer with the active board.
        Call this after processing the next step to the frame buffer."""
        self.cells, self.cells_framebuffer = self.cells_framebuffer, self.cells


def run(return_statistics: bool = False):
    opts = _cgol_argparse.get_parser().parse_args()

    # whether or not we call the step_parallel or not
    do_parallel = opts.num_workers > 0

    # terminal size for default size, if we need it
    displaysize = os.get_terminal_size()
    conway = Conway(
        (displaysize.lines - 1) * 4 if opts.height < 0 else opts.height,
        displaysize.columns * 2 if opts.width < 0 else opts.width,
    )

    # randomly initialize cells: 80% dead, 20% alive
    conway.cells[...] = np.random.Generator(np.random.PCG64()).choice(
        2, size=(conway.height, conway.width), p=[0.8, 0.2]
    )

    # initial time, used for termination condition
    t0 = time.time()
    # draw initial state
    conway.display()

    target_frame_delay = 1 / opts.framerate

    frames_taken = 0
    avg_update = 0

    # defaults to 5 seconds:
    while (tframe := time.time()) - t0 < opts.runtime:
        # ==== main update loop ====
        conway.display(replace_prior=True, synthetic_delay=opts.synthetic_delay)
        if do_parallel:
            conway.step_parallel(opts.num_workers)
        else:
            conway.step()
        conway.swap_buffers()
        # ==== end main update loop ====

        # time taken for the update
        tupd = time.time() - tframe
        frames_taken += 1
        avg_update += (tupd - avg_update) / frames_taken
        if tupd < target_frame_delay:
            time.sleep(target_frame_delay - tupd)

        # === above this point should take time >= target_frame_delay

    # display() does a carriage return; set the newline before exiting.
    print()  # noqa: T201
    print(f"{frames_taken} frames, with an update of {avg_update:f}s.")  # noqa: T201

    if return_statistics:
        return avg_update, frames_taken
    return None

# TAC-HEP: SE for Sci Assignment 5

This assignment covers parallelism.

## Conway's Game of Life

Cellular automata are simulations operating on a grid of finite states. The following state of a cell is determined locally, that is, only the cell's neighborhood affects its next state.
[Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) (CGOL) is typically the go-to example.

Within CGOL, a cell is either alive or dead, and the following state is determined by these rules:

- If a cell is alive, then it will continue to live if it has two or three living neighbors. Otherwise, it will die.
- If a cell is dead, then it will revive if it has exactly three living neighbors. Otherwise, it stays dead.

Due to cellular automata being functional (as in functional programming), and the behavior for each cell is basically identical, we will use this as an environment to examine parallelism within Python. You will be modifying the code within `src/parallel_example/cgol.py`. There are two things of note within the file:

- The `Conway` class stores all that is necessary for a game. Within it are the following methods:
  - `step()` performs a single step of CGOL. This takes the game state from `cells` and sets `cells_framebuffer` to the next state. The terminology borrows from computer graphics as memory that is written to before sending it to the display. In graphics, you want to completely render an image before displaying it on the monitor. Hence, it is typical to draw the next frame to a frame buffer while the previous frame is being displayed on the monitor. For our purposes, we do not want to modify the `cells` array in the middle of computing our next state. *This method has already been written for you.*
  - `step_parallel_threading()` acts in the same way as `step()`, except it is performed using threading. *This method has already been written for you.*
  - `step_parallel()` will be the goal of part 2. This should act in the same way as the other `step` methods.
  - `__str__()` the string dunder, used to convert the board into a string to be written to the terminal.
  - `display()` writes `str(conway)` to the terminal. If `replace_prior` is set to true, then the ANSI escape sequence to return `x` lines back is written, as to overwrite the previous board. As this function utilizes writing to the terminal, which is somewhat fast, `synthetic_delay` is used to pretend that the function is slower than it actually is. Due to the use of `time.sleep()` complications of the GIL are avoided.
  - `swap_buffers()` switches the references to `cells` and `cells_framebuffer`. Continuing the computer graphics analogy, this is similar to the [OpenGL command of the same name](https://www.opengl.org/resources/libraries/glut/spec3/node21.html). When utilizing the "double-buffering" technique, instead of having the first buffer pass the data into the second buffer, we can have the second buffer point to the first buffer's data. Then, since the second buffer's original data is no longer used, we can reuse it in the first buffer instead of de-allocating it. The net effect is a swap of pointers. Typically, the second buffer is [cleared](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glClear.xhtml) (set to a default / background value) before being written to as the new first buffer, but since each cell is overwritten, we can skip that step.
- The `run()` function, which is the target of the `cgol` executable command. This function utilizes `argparse`, so you can access options through
`cgol -h` or `uv run cgol -h`, depending on your configuration. This will be modified in part 1.

## Part 1 - The Display Thread

In graphics-heavy applications, it is common to have the display managed by a separate thread. This is to prevent the display from completely freezing when performing a heavy task. In a desktop environment, this may prevent you from manipulating the window for the application, and give you the all-too-well-known `${application} is not responding.` box.

Separating out a display thread may also help improve the performance of the heavy task. For GUI-based applications, draw calls are made by the processor, but the heavy lifting is done by a dedicated graphics processing unit (GPU). While the GPU is chugging away, (depending on the graphics API) the processor may wait for the GPU to finish. Typically, this means that the processor context-switches to a different process or thread rather than idle. However, for our application to utilize this wait time, we need to actually have a thread that the processor can context-switch to.

To model this, the `synthetic_delay` argument is given to the `display()` method within the while loop. Since `display()` and `step()` both depend only on `cells` (leaving it unmodified), they can run concurrently. However, they both need to complete prior to `swap_buffers()`. Your job is to modify `run()` using multithreading in order to have `display()` and `step()` run at the same time. This task can be performed by only modifying the code within the main update loop.

```python
# ==== main update loop ====
conway.display(replace_prior=True, synthetic_delay=opts.synthetic_delay)
if do_parallel:
    conway.step_parallel_threading(opts.num_workers)
else:
    conway.step()
conway.swap_buffers()
# ==== end main update loop ====
```

Since `display()` uses `time.sleep()` to simulate a long render task, Python's Global Interpreter Lock (GIL) will be released for `step()` to take over. Thus, you can expect to see some improvement in performance, which is measured by the amount of time spent within the above code. This is computed as the difference between `tframe` and `tupd`. The former is set via the [walrus operator](https://docs.python.org/3/whatsnew/3.8.html#assignment-expressions).

The `cgol` command will call this code. You can play around with the arguments (increase / decrease the size of the game) if the change in performance does not appear obvious. The `sleep()` call lasts for 50 milliseconds, so `step()` taking roughly that long will make it easy to observe the performance difference.

> [!NOTE]
> The `step_parallel_threading()` method uses the `threading` module. While your task is simpler, it may serve as a useful reference.

## Part 2 - Parallelization

In part 1, we utilized a separate thread. For this part, as is typical in scientific computation, we have a task based on a repeated pattern, namely, the per-cell logic of computing the next state.

Due to the GIL, `step_parallel_threading()` does not provide the performance improvement one may expect. However, in Python 3.13, we can release the GIL. To see the difference, the `time` nox session is provided. If you have `uv`, running nox (including with `uv tool` or `uvx`) will allow `uv` to manage the different python versions for you. Alternatively, the `time-cgol` `workflow_dispatch` has been provided, if you wish to run it on GitHub's servers, instead.

Your task is to implement `step_parallel()`, replacing the `raise NotImplementedError` line with a parallel implementation that works without running free-threaded Python (turning off the GIL). You are free to use `multiprocessing` or another approach (e.g. the interpreter pool). Should you wish, you may change the versions of python in `pyproject.toml` or `nox`.

You may also modify code outside of `step_parallel()`. If using `multiprocessing`, for example, it may be useful to put `cells` and `cells_framebuffer` in shared memory.

The astute of you may recognize that `step` can be written in terms of vectorized `numpy` operations, which will release the GIL. While this alone is insufficient for full credit, the GIL release would allow for the use of `threading`, which will suffice.

> [!WARNING]
> The `_apply_CGOL_to_cell()` helper function may not work in a multiprocessing context. `numpy` arrays can be accessed by different threads. However, shared data is not automatic in an inter-process environment.

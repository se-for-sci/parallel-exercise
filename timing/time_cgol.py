import sys
import timeit

from parallel_example.cgol import Conway

print("""
==============================
     step() timing test
==============================""")


def color(text, colorcode):
    return f"\x1b[{colorcode}m{text}\x1b[0m"


if sys._is_gil_enabled():
    print(
        f"GIL is {color('enabled', 30)}.\nThreading may not provide the desired performance."
    )
else:
    print(f"GIL is {color('disabled', 32)}.\nThreading is unlocked.")

board_h = 1000
board_w = 1000

conway = Conway(board_h, board_w)

num_trials = 5

def run_trial(name, timer, num_trials):
    print(f"{name}:")
    try:
        elapsed = timer.timeit(num_trials)
    except NotImplementedError:
        print("   not yet implemented. Test skipped.")
        return
    num_trials_str = color(num_trials,36)
    elapsed_str = color(f"{elapsed:.3f}",35)
    per_str = color(f"{elapsed / num_trials:.3f}",35)
    print(f"   {num_trials_str} trials in {elapsed_str}s.")
    print(f"     ({per_str}s / trial)")

run_trial(f"Serial ({color('step()', 30)})", timeit.Timer(conway.step), num_trials)
run_trial(f"Threading ({color('step_parallel_threading(2)', 30)})", timeit.Timer(lambda: conway.step_parallel_threading(2)), num_trials)
run_trial(f"Threading ({color('step_parallel_threading(4)', 30)})", timeit.Timer(lambda: conway.step_parallel_threading(4)), num_trials)
run_trial(f"Parallel ({color('step_parallel(2)', 30)})", timeit.Timer(lambda: conway.step_parallel(2)), num_trials)
run_trial(f"Parallel ({color('step_parallel(4)', 30)})", timeit.Timer(lambda: conway.step_parallel(4)), num_trials)

"""Local arena: run games and print final money for both players."""
import sys
import json
from kaggle_environments import make


def run_game(agents, seed=None, quiet=True):
    cfg = {"episodeSteps": 720}
    if seed is not None:
        cfg["seed"] = seed
    env = make("kaggriculture", configuration=cfg, debug=not quiet)
    env.run(agents)
    final = env.steps[-1]
    rewards = [s["reward"] for s in final]
    statuses = [s["status"] for s in final]
    return rewards, statuses


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    b = sys.argv[2] if len(sys.argv) > 2 else "starter"
    seeds = [int(s) for s in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 3]
    tot = [0.0, 0.0]
    wins = 0
    n = 0
    for seed in seeds:
        r, st = run_game([a, b], seed=seed)
        print(f"seed {seed}: {a}={r[0]:.0f} ({st[0]})  vs  {b}={r[1]:.0f} ({st[1]})")
        tot[0] += r[0] or 0
        tot[1] += r[1] or 0
        if (r[0] or 0) > (r[1] or 0):
            wins += 1
        n += 1
        # reversed seats
        r2, st2 = run_game([b, a], seed=seed)
        print(f"seed {seed} (rev): {b}={r2[0]:.0f} ({st2[0]})  vs  {a}={r2[1]:.0f} ({st2[1]})")
        tot[0] += r2[1] or 0
        tot[1] += r2[0] or 0
        if (r2[1] or 0) > (r2[0] or 0):
            wins += 1
        n += 1
    print(f"\navg {a}: {tot[0]/n:.0f}   avg {b}: {tot[1]/n:.0f}   winrate: {wins}/{n}")


if __name__ == "__main__":
    main()

"""Kaggriculture agent v4: wheat + goose economy.

Economics (from engine source):
- Eggs have the flattest glut curve: mass-selling only drops price ~50 -> ~37.
  Geese with daily FEED+CARE give 2 eggs/day each from day placed+4, forever.
- Wheat grown in-house as feed (1 wheat/goose/day); tile cycle: plant, water
  day 0 (mandatory), water days 2-4 (bonus window), harvest day 4 -> 4 units.
- Fertilizer is free from geese; sold while price holds, then ignored.
- Land bought aggressively once the goose engine is funded; hands hired to
  match the daily workload.

Stateless: rebuilds a task list every turn, assigns tasks to the nearest
free unit, and lets units opportunistically service the tile they stand on.
"""

BOARD = 10
_MEMORY = {}
SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
W_LO, W_HI = 2, 4          # wheat watering bonus window (ages)
W_SEED = 10
GOOSE_COST = 300
LAND_PRICES = (1000, 2000, 4000)
FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597)
BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
              "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200,
              "FERTILIZER": 100}


def _g(d, key, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)


def _is_coop_tile(x):
    """Static layout: the two columns farthest from the shed in each 5-wide
    half are coop columns (~40 coops board-wide); everything else wheat."""
    return (x % 5) in ((0, 1) if x < 5 else (3, 4))


def _step_toward(pos, tx, ty):
    dx, dy = tx - pos[0], ty - pos[1]
    if dx == 0 and dy == 0:
        return None
    if abs(dx) >= abs(dy) and dx != 0:
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"


def _nearest_shed_tile(pos):
    return min(SHED_TILES, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))


def _plan(obs):
    """Scan the observation into a compact dict."""
    player = obs["player"]
    farm = obs["farms"][player]
    priv = obs["private"]
    tiles = farm["tiles"]
    plants, geese, built_empty_coops = [], [], []
    empty_wheat, weeds, unbuilt_coop_sites = [], [], []
    for y in range(BOARD):
        row = tiles[y]
        for x in range(BOARD):
            t = row[x]
            coop_col = _is_coop_tile(x)
            if t is None:
                if coop_col:
                    unbuilt_coop_sites.append((x, y))
                else:
                    empty_wheat.append((x, y))
            elif t == "LOCKED":
                continue
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants.append((x, y, t))
                elif "animal" in t:
                    geese.append((x, y, t))
                elif k == "COOP":
                    built_empty_coops.append((x, y))
                elif k == "WEED":
                    weeds.append((x, y))
    shed = dict(priv["shed"])
    seeds = dict(priv["seeds"])
    invs = list(priv["inventories"])
    units = [(0, tuple(farm["farmer"]))]
    for i, p in enumerate(farm["hands"]):
        units.append((i + 1, tuple(p)))
    return {
        "farm": farm, "shed": shed, "seeds": seeds, "invs": invs, "units": units,
        "plants": plants, "geese": geese, "built_empty_coops": built_empty_coops,
        "empty_wheat": empty_wheat, "weeds": weeds,
        "unbuilt_coop_sites": unbuilt_coop_sites,
    }


def _agent(obs):
    day, hour = obs["day"], obs["hour"]
    P = _plan(obs)
    farm = P["farm"]
    money = farm["money"]
    prices = obs["market"]["prices"]
    shed, seeds = P["shed"], P["seeds"]
    plants, geese = P["plants"], P["geese"]
    units = P["units"]
    n_units = len(units)
    last_day = day >= 27
    n_geese = len(geese)
    shed_geese = shed.get("GOOSE", 0)
    feed_need = n_geese + shed_geese

    # carried wheat + geese across all units
    inv_wheat = sum(inv.get("WHEAT", 0) for inv in P["invs"] if isinstance(inv, dict))
    inv_geese = sum(inv.get("GOOSE", 0) for inv in P["invs"] if isinstance(inv, dict))

    wheat_harvestable = 0
    for _, _, t in plants:
        if day - _g(t, "planted_day", 0) >= W_LO:
            wheat_harvestable += _g(t, "yield_units", 0)

    # ---------------- task list ----------------
    # (prio, x, y, op, arg, req_inv_item_or_None, only_u)
    tasks = []

    def _t(prio, x, y, op, arg=None, req=None, only_u=None):
        tasks.append((prio, x, y, op, arg, req, only_u))

    # P0 keep things alive: feed geese, water dying/planted-today wheat
    for x, y, t in geese:
        if not _g(t, "fed_today", False):
            _t(0, x, y, "FEED", None, "WHEAT")
    for x, y, t in plants:
        if _g(t, "watered_today", False):
            continue
        age = day - _g(t, "planted_day", 0)
        urgent = age == 0 or _g(t, "consecutive_unwatered", 0) >= 1
        if urgent or W_LO <= age <= W_HI:
            _t(0 if urgent else 1, x, y, "WATER")

    # morning: a few carriers grab the day's feed ration at the shed
    if hour <= 1:
        carriers = min(len(units), 4)
        ration = min(8, max(1, -(-feed_need // max(1, carriers))))
        for ui, pos in units[:carriers]:
            inv = P["invs"][ui] if ui < len(P["invs"]) else {}
            if isinstance(inv, dict) and inv.get("WHEAT", 0) < ration and shed.get("WHEAT", 0) > 0:
                st = _nearest_shed_tile(pos)
                _t(0, st[0], st[1], "PICKUP", ("WHEAT", ration), None, ui)
    # any time: if feed work is stranded with no carriers, send someone
    elif any(t[3] == "FEED" for t in tasks) and inv_wheat == 0 and shed.get("WHEAT", 0) > 0:
        _t(0, 4, 4, "PICKUP", ("WHEAT", 8))

    # P1 place geese carried by units onto built coops (growth compounds)
    carried = inv_geese
    for cx, cy in P["built_empty_coops"]:
        if carried <= 0:
            break
        _t(1, cx, cy, "PLACE_GOOSE", None, "GOOSE")
        carried -= 1

    # P1 build coops while ramping the flock (ahead of goose purchases)
    target_flock = _target_geese(day)
    flock = n_geese + shed_geese + inv_geese
    if (not last_day and day <= 22 and flock < target_flock
            and len(P["built_empty_coops"]) + shed_geese + inv_geese < target_flock):
        n_build = 3 if flock < 12 else 6
        for sx, sy in P["unbuilt_coop_sites"][:n_build]:
            _t(1, sx, sy, "BUILD_COOP")

    # P2 care for fed geese (doubles production) — only when feed is secure
    feed_secure = len(plants) >= n_geese * 0.8
    if feed_secure:
        for x, y, t in geese:
            if _g(t, "fed_today", False) and not _g(t, "cared_today", False):
                _t(2, x, y, "CARE")

    # P1 unload heavy inventories at the shed
    for ui, pos in units:
        inv = P["invs"][ui] if ui < len(P["invs"]) else {}
        if not isinstance(inv, dict):
            continue
        load = sum(v for k, v in inv.items() if k not in ("WHEAT", "GOOSE"))
        if load >= 10:
            st = _nearest_shed_tile(pos)
            _t(1, st[0], st[1], "UNLOAD", None, None, ui)

    # P2 harvest geese near cap (max_held 4, production 2/day with care)
    for x, y, t in geese:
        yu = _g(t, "yield_units", 0)
        if yu >= 3 or (yu >= 2 and last_day):
            _t(2, x, y, "HARVEST")

    # P2 harvest wheat at full age (>= W_HI), or any age in the last days
    for x, y, t in plants:
        age = day - _g(t, "planted_day", 0)
        if (_g(t, "yield_units", 0) > 0 and
                (age >= W_HI or (last_day and age >= W_LO))):
            _t(2, x, y, "HARVEST")

    # plant wheat — priority rises with the feed gap, throttled by labor
    if not last_day and day <= 25 and seeds.get("WHEAT", 0) > 0:
        planted = len(plants)
        p_prio = 0 if planted * 2 < n_geese else (1 if planted < n_geese * 1.25 else 2)
        labor_budget = max(0, n_units * (24 - hour) - len(tasks))
        plant_cap = max(4, labor_budget // 4)
        for x, y in P["empty_wheat"][:max(0, plant_cap)]:
            _t(p_prio, x, y, "PLANT", "WHEAT")

    # P3 collect fertilizer while it pays / clear weeds
    if prices["FERTILIZER"] >= 50 and not last_day and feed_secure:
        for x, y, t in geese:
            if _g(t, "fertilizer_available", False):
                _t(3, x, y, "COLLECT_FERTILIZER")
    for x, y in P["weeds"]:
        _t(1 if not _is_coop_tile(x) else 3, x, y, "DIG")

    # ---------------- market orders (daily batch at hour 0/1) ----------------
    orders = []
    shed_total = sum(v for v in shed.values() if v and v > 0)
    morning = hour == 0
    morning2 = hour <= 1

    # sells first so the cash is available this turn
    eggs = shed.get("EGG", 0)
    if eggs > 0 and (morning or eggs >= 30 or last_day or shed_total >= 60):
        orders.append(["SELL", "EGG", eggs])
    fert = shed.get("FERTILIZER", 0)
    if fert > 0 and (prices["FERTILIZER"] >= 45 or last_day):
        orders.append(["SELL", "FERTILIZER", fert])
    surplus_wheat = shed.get("WHEAT", 0) - (feed_need * 3 + 2)
    if surplus_wheat > 0 and (prices["WHEAT"] >= 35 or last_day):
        orders.append(["SELL", "WHEAT", surplus_wheat])
    for item in ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "MILK", "WOOL"):
        n = shed.get(item, 0)
        if n > 0 and (prices[item] >= 0.8 * BASE_PRICE[item] or day >= 28):
            orders.append(["SELL", item, n])

    # hire hands once per day; size the crew for the farm we WANT to run
    if morning:
        wheat_capacity = len(plants)
        workload = int(feed_need * 2.5 + wheat_capacity * 1.8 + flock * 1.5 + 8)
        need_units = min(14, max(2, -(-workload * 12 // 10 // 20)))
        have = n_units
        while have < need_units:
            cost = FIB[have - 1] if have - 1 < len(FIB) else 99999
            if money <= cost * 2 + 100:
                break
            orders.append(["HIRE"])
            money -= cost
            have += 1

    # buy land once the flock is funded
    unlocked_n = len(farm["unlocked_quadrants"]) - 1
    if morning and unlocked_n < 3 and day >= 2 and day <= (20 if unlocked_n == 2 else 26):
        price = LAND_PRICES[unlocked_n]
        if money >= price + max(400, feed_need * 32):
            orders.append(["BUY_LAND"])
            money -= price

    # wheat seeds
    if morning and day <= 25:
        want_seeds = len(P["empty_wheat"]) + 4
        deficit = want_seeds - seeds.get("WHEAT", 0)
        if deficit > 0 and money >= deficit * W_SEED + 120:
            orders.append(["BUY_SEED", "WHEAT", deficit])
            money -= deficit * W_SEED

    # bridge feed: wheat in shed+carried+harvestable must cover the flock
    if morning:
        feed_short = feed_need * 2 - (shed.get("WHEAT", 0) + inv_wheat +
                                   min(wheat_harvestable, feed_need * 2))
        if feed_short > 0 and prices["WHEAT"] <= 60 and money >= feed_short * prices["WHEAT"] + 100:
            orders.append(["BUY_PRODUCT", "WHEAT", feed_short + 1])
            money -= (feed_short + 1) * prices["WHEAT"]

    # buy geese early in the day; the feed-buy above covers the new flock as
    # long as market wheat is affordable, so ramp hard when it is
    if 0 <= hour <= 2 and day <= 23 and not last_day:
        slots = len(P["built_empty_coops"])
        sustainable = (len(plants) * 0.8 + (shed.get("WHEAT", 0) + inv_wheat) / 3
                       >= flock + 1)
        feed_ok = sustainable or (prices["WHEAT"] <= 50 and money > 1500)
        max_buy = 5 if day < 4 else 8
        reserve = max(500, (feed_need + 2) * prices["WHEAT"])
        affordable = int((money - reserve) // GOOSE_COST)
        n_buy = max(0, min(slots, max_buy, affordable,
                           target_flock - flock))
        if n_buy > 0 and feed_ok and shed_total + n_buy <= 88:
            orders.append(["BUY_ANIMAL", "GOOSE", n_buy])
            money -= n_buy * GOOSE_COST
            feed_need += n_buy
            # top up feed purchase for the enlarged flock
            short2 = feed_need * 2 - (shed.get("WHEAT", 0) + inv_wheat +
                                      min(wheat_harvestable, feed_need * 2))
            if short2 > 0 and prices["WHEAT"] <= 60 and money >= short2 * prices["WHEAT"]:
                orders.append(["BUY_PRODUCT", "WHEAT", short2 + 1])
                money -= (short2 + 1) * prices["WHEAT"]

    orders = orders[:10]

    # pickups at the shed (market sells process after unit actions)
    if shed_geese > 0 and P["built_empty_coops"] and day <= 27:
        remaining = shed_geese
        for ui, pos in units[:4]:
            if remaining <= 0:
                break
            n = min(remaining, max(4, -(-shed_geese // 4)))
            _t(1, 4, 4, "PICKUP", ("GOOSE", n), None, ui)
            remaining -= n

    # ---------------- assign & emit ----------------
    tasks.sort(key=lambda t: (t[0], t[1], t[2]))
    claimed = [False] * len(tasks)
    assign = {}

    # sticky assignment: keep last turn's target if the task still exists, so
    # units walk to completion instead of dithering between re-sorted tasks
    mem = _MEMORY.setdefault(obs["player"], {})
    prev = mem.get("targets", {})
    task_key = {(t[3], t[1], t[2]): i for i, t in enumerate(tasks)}
    for ui, key in list(prev.items()):
        ti = task_key.get(key)
        if ti is not None and not claimed[ti] and ui not in assign:
            t = tasks[ti]
            if t[6] is None or t[6] == ui:
                inv = P["invs"][ui] if ui < len(P["invs"]) else {}
                if t[5] and not (isinstance(inv, dict) and inv.get(t[5], 0) > 0):
                    continue
                assign[ui] = ti
                claimed[ti] = True

    n = max(1, len(units))
    def _band(ui):
        return (BOARD * ui // n, BOARD * (ui + 1) // n)

    def _score(ui, pos, tx, ty, prio):
        d = abs(pos[0] - tx) + abs(pos[1] - ty)
        lo, hi = _band(ui)
        if not (lo <= ty < hi):
            d += 12  # outside the unit's strip: strong aversion
        return d

    for ti, (prio, tx, ty, op, arg, req, only_u) in enumerate(tasks):
        if claimed[ti]:
            continue
        best_u, best_d = None, 9999
        for ui, pos in units:
            if ui in assign or (only_u is not None and ui != only_u):
                continue
            inv = P["invs"][ui] if ui < len(P["invs"]) else {}
            has = isinstance(inv, dict) and inv.get(req, 0) > 0 if req else True
            if req and not has:
                continue
            d = _score(ui, pos, tx, ty, prio)
            if d < best_d:
                best_u, best_d = ui, d
        if best_u is not None:
            assign[best_u] = ti
            claimed[ti] = True
    mem["targets"] = {ui: (tasks[ti][3], tasks[ti][1], tasks[ti][2])
                      for ui, ti in assign.items()}

    def _emit_op(op, arg, ui):
        if op == "PICKUP":
            item, n = arg
            return ["PICKUP", item, n]
        if op == "UNLOAD":
            inv = P["invs"][ui] if ui < len(P["invs"]) else {}
            if not isinstance(inv, dict):
                return ["PASS"]
            for item in ("EGG", "FERTILIZER"):
                if inv.get(item, 0) > 0:
                    return ["PLACE", item, inv[item]]
            return ["DROP"]
        if op == "PLACE_GOOSE":
            return ["PLACE", "GOOSE"]
        if op == "PLANT":
            return ["PLANT", arg]
        return [op]

    farmer_action = ["PASS"]
    hands_actions = [["PASS"] for _ in farm["hands"]]
    for ui, pos in units:
        ti = assign.get(ui)
        if ti is None:
            continue
        prio, tx, ty, op, arg, req, only_u = tasks[ti]
        if (pos[0], pos[1]) == (tx, ty):
            action = _emit_op(op, arg, ui)
        else:
            # opportunistic: service any unclaimed due task on the current tile
            action = None
            for tj, (p2, x2, y2, op2, arg2, req2, ou2) in enumerate(tasks):
                if claimed[tj] or (x2, y2) != (pos[0], pos[1]):
                    continue
                if ou2 is not None and ou2 != ui:
                    continue
                if req2:
                    inv = P["invs"][ui] if ui < len(P["invs"]) else {}
                    if not (isinstance(inv, dict) and inv.get(req2, 0) > 0):
                        continue
                action = _emit_op(op2, arg2, ui)
                claimed[tj] = True
                break
            if action is None:
                mv = _step_toward(pos, tx, ty)
                action = [mv] if mv else ["PASS"]
        if ui == 0:
            farmer_action = action
        elif ui - 1 < len(hands_actions):
            hands_actions[ui - 1] = action

    return {"farmer": farmer_action, "hands": hands_actions, "market": orders}


def _target_geese(day):
    if day < 2:
        return 4
    if day < 5:
        return 10
    if day < 9:
        return 20
    if day < 14:
        return 32
    return 40


def agent(obs):
    try:
        return _agent(obs)
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

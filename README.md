# Kaggriculture Toolkit

Local research toolkit for the [Kaggle Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation. Three pieces: a two-seat arena, notes on the public meta, and five top agents extracted from public notebooks and kept as they were.

[Kaggle Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) 模拟赛的本地研究仓库。内容三块：双座位对战台、公开 meta 的调研结论，以及从公开 notebook 提取后原样保留的五个顶尖 agent。

> **Timeline.** Submissions closed on **2026-09-30**. Mid-October was only the tail: remaining games finished, and the standings settled. The CLI string `deadline 10-14` is the wrong date. Read the Timeline tab on the competition page first. Leaderboard rating comes from submitting and iterating across the whole season. Joining on the deadline leaves that season unplayed.
>
> **时间线。** 提交截止是 **2026-09-30**。10 月中旬只是收尾：剩下的对局打完，名次收束。命令行里的 `deadline 10-14` 是错的日期。做模拟赛先看比赛页的 Timeline。天梯分靠整个赛期持续提交、反复迭代。截止当天才入场，等于这一季没打。

## Contents / 内容

| Path | English | 中文 |
| --- | --- | --- |
| `arena.py` | Two-seat arena. `python3 arena.py <agent.py> <opponent> <seeds>` plays each seed in both seat orders, then prints final coins, the tested agent's wins (higher coins), and both averages. Opponent defaults to `starter`; seeds default to `1,2,3`. | 双座位对战台。`python3 arena.py <agent.py> <opponent> <seeds>` 对每个种子交换座位各打一场，打印终局金币、被测 agent 的胜场（金币更高计胜）和双方平均金币。对手默认 `starter`，种子默认 `1,2,3`。 |
| `agents/self_v4_scheduler.py` | Original scheduler (wheat + geese). Local record: 6/6 against the built-in `starter`, mean final coins ~22k. Public agents finish near ~150k against that same `starter`, about an order of magnitude higher. Kept as a study sample. | 自写的调度 agent（小麦 + 鹅）。本地对内置 `starter` 为 6/6，终局平均约 2.2 万金币。公开 agent 对同一个 `starter` 大约 15 万，高出约一个数量级。留作学习样本。 |
| `agents/public/` | Five top agents extracted from public Apache-2.0 notebooks. The files are unchanged. Credits are below. | 从公开 Apache-2.0 notebook 提取的五个顶尖 agent，文件未改。署名见下。 |
| `docs/` | Official competition text released with the contest data: `AGENTS.md` and `README.md`. | 随比赛数据发布的官方文档：`AGENTS.md` 与 `README.md`。 |
| `notebooks/` | The public notebooks themselves, kept as the source record, including each notebook's own credit chain. | 上述公开 notebook 的原件，当作来源凭证；各文件里的署名链一并保留。 |

## Local results / 本地结果

Recorded **2026-10-09** on **kaggle-environments 1.33.0**. The table is that local run.

记录于 **2026-10-09**，环境 **kaggle-environments 1.33.0**。下表就是这批本地对局。

| Agent | vs `starter` (coins) / 对 starter 的金币 | Head to head / 相互对战 |
| --- | --- | --- |
| `icefire.py` | ~150k, all wins / 约 15 万，全胜 | Mirror vs demand 10-2; 4-0 vs v38; 3-1 vs farm2945 / 对 demand 镜像局 10-2；4-0 胜 v38；3-1 胜 farm2945 |
| `demand.py` | ~159k, all wins / 约 15.9 万，全胜 | 4-0 vs v38; 3-1 vs farm2945 / 4-0 胜 v38；3-1 胜 farm2945 |
| `farm2945.py` | ~160k, all wins / 约 16 万，全胜 | Lost to icefire and demand; 4-0 vs v38 / 负于 icefire、demand；4-0 胜 v38 |
| `v38.py` | ~152k, all wins / 约 15.2 万，全胜 | Lost to icefire, demand, and farm2945 / 负于 icefire、demand、farm2945 |
| `c95_agent.py` | ~153k, all wins / 约 15.3 万，全胜 | Behind the four above (0-4 vs demand/icefire) / 明显弱于上面四个（0-4 负 demand/icefire） |

## Meta notes / Meta 结论

The evidence is in `notebooks/`. These notes only restate that record.

证据在 `notebooks/`。下面只是把那份记录写清楚。

- Top public play collapsed onto a deterministic **tape**: a 720-turn schedule that leading agents repeat from match to match, distilled into a fixed script, with a thin adaptive wrapper around it.
  公开榜前列收成确定性的**录像带**（tape）：顶尖 agent 跨对局反复走出的 720 回合日程，被蒸馏成固定脚本，外面只包一层薄的自适应逻辑。
- A mature farm in that tape is **8 cows, 5–6 sheep, ~23 strawberries, ~31 wheat**, the **NE and SW** quadrants bought (**SE** rarely), and **12 hired hands**.
  这套录像带里的成熟农场是 **8 头牛、5–6 只羊、约 23 株草莓、约 31 格小麦**，买下 **NE 与 SW**（**SE** 很少买），**雇工 12 人**。
- The split is **when** goods hit the market. Premium goods (milk, wool, strawberries, melons) are sold one turn ahead of the mirror opponent. Liquidation is planned on steps **712-718**. Turn **0** buys **5 wheat**, which blocks an opening that cuts off animal feed.
  拉开差距的是**出手时机**。高端商品（奶、毛、草莓、瓜）比镜像对手早一回合卖掉。终局清仓排在第 **712-718** 步。第 **0** 回合先买 **5 个小麦**，用来挡住开局断饲料。
- The leaderboard counts wins and losses. Coin margin stays out of the rating. The gap between a full score (**~3200**) and the bronze line (**~1820**) is the timing above.
  天梯按胜负计分，金币差不进分数。满分（**约 3200**）和铜牌线（**约 1820**）之间的差距，就是上面这些时机。

## Use / 使用

```bash
pip install kaggle-environments
python3 arena.py agents/public/icefire.py starter 1,2,3
```

A contest submission is a single `main.py`. The loader takes the **last callable defined in that file** as the agent, so the entry point belongs at the bottom of the file.

提交文件是单个 `main.py`。加载器把文件里**最后定义的那个可调用对象**当作 agent，入口要写在文件末尾。

## Credit and license / 署名与许可

Code under `agents/public/` is taken from public Kaggle notebooks (Apache-2.0) and left unchanged. Keep the credit chain inside each file and inside `notebooks/`.

`agents/public/` 的代码来自 Kaggle 公开 notebook（Apache-2.0），原样保留、没有修改。请同时保留各文件内部和 `notebooks/` 里的署名链。

- `icefire.py` — [AlekseiProvorov, *A Song of Ice and Fire | Fixed + Flexible*](https://www.kaggle.com/code/leoprovorov/a-song-of-ice-and-fire-fixed-flexible)（2026-10-04）
- `demand.py` — [tetsu2131, *Demand-Preserving Turn Sale Timing*](https://www.kaggle.com/code/tetsutani/demand-preserving-turn-sale-timing)（2026-09-28；内含 NOTICE：shiiin9、Ahmed Berat Özer V55/V56、Thomas Tschinkel、yhay81 ShopRouter、Dmitrii Gluzdov 等）
- `farm2945.py` — [Thomas Tschinkel, *The 2945 Farm: 96% vs the Top-10 Public Bots*](https://www.kaggle.com/code/thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots)（2026-09-19，基于公开 V39）
- `v38.py` — [Ahmed Berat Özer, *Kaggriculture V38*](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v38-smarter-feed-stronger-margins)（2026-09-12）
- `c95_agent.py` — [Rayk Kretzschmar, *Findings from Zero to Top Meta*](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta) 内嵌的冻结版 C95（2026-08）

`arena.py` and `agents/self_v4_scheduler.py` are original to this repo and licensed MIT.

`arena.py` 与 `agents/self_v4_scheduler.py` 为本仓库原创，MIT。

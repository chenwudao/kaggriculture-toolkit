# Kaggriculture Toolkit

[Kaggle Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) 比赛的本地研究仓库：对战测试台、meta 调研结论、以及从公开 notebook 提取的顶级 agent 集合。

> ⚠️ 教训先记在这里：这场模拟赛的**提交截止是 2026-09-30**，10 月中旬只是残局对局收敛期。CLI 里显示的 "deadline 10-14" 是误导。做模拟赛请第一时间看比赛 Timeline 页，天梯分靠整个赛期的持续提交迭代积累，踩点入场等于弃赛。

## 内容

| 路径 | 说明 |
| --- | --- |
| `arena.py` | 本地对战测试台：`python3 arena.py <agent.py> <opponent> <seeds>`，自动双座位对战并汇总胜率/金币 |
| `agents/self_v4_scheduler.py` | 自研的任务调度式 agent（小麦+鹅经济），本地 6/6 胜内置 starter，均终局 ~2.2 万金币。与公开 meta 差一个数量级，留作学习样本 |
| `agents/public/` | 从公开 Apache-2.0 notebook 提取的 5 个顶级 agent（见下方署名） |
| `docs/` | Kaggle 官方比赛文档（AGENTS.md / README.md，随比赛数据发布） |
| `notebooks/` | 上述公开 notebook 原件（来源凭证，含各自完整署名链） |

## 公开 agent 本地评测（2026-10-09，kaggle-environments 1.33.0）

| Agent | vs starter（金币） | 相互对战 |
| --- | --- | --- |
| `icefire.py` | ~150k，全胜 | 对 demand 镜像局 10-2；4-0 胜 v38；3-1 胜 farm2945 |
| `demand.py` | ~159k，全胜 | 4-0 胜 v38；3-1 胜 farm2945 |
| `farm2945.py` | ~160k，全胜 | 负于 icefire/demand，4-0 胜 v38 |
| `v38.py` | ~152k，全胜 | 负于以上全部 |
| `c95_agent.py` | ~153k，全胜 | 明显弱于上面四个（0-4 负 demand/icefire） |

## Meta 调研结论（详细证据见 notebooks）

- 顶部生态收敛为确定性“录像带”（tape）流派：把顶尖选手跨对局稳定复现的 720 回合日程蒸馏成固定脚本，外挂少量自适应包装。
- 成熟农场形态：**8 牛 + 5-6 羊 + ~23 草莓 + ~31 小麦、买 NE+SW 两块地（很少买 SE）、12 雇工**。
- 真正的分水岭在**市场时机**：高端商品（奶/毛/莓/瓜）比镜像对手提前一回合抛售、终局 712-718 步的清算规划、开局第 0 回合先买 5 小麦防断粮阻击。
- 天梯只看胜负不计金币差；满分 (~3200) 与铜牌线 (~1820) 之间隔着的正是这些时机细节。

## 使用

```bash
pip install kaggle-environments
python3 arena.py agents/public/icefire.py starter 1,2,3
```

提交格式：单文件 `main.py`（文件里**最后一个定义的可调用对象**会被框架当作 agent 入口加载——这是个隐蔽的坑）。

## 署名与许可

`agents/public/` 下所有代码源自 Kaggle 公开 notebook（Apache-2.0），原样保留、未做修改。使用时请保留各自文件内与 `notebooks/` 中的署名链：

- `icefire.py` — [AlekseiProvorov, *A Song of Ice and Fire | Fixed + Flexible*](https://www.kaggle.com/code/leoprovorov/a-song-of-ice-and-fire-fixed-flexible)（2026-10-04）
- `demand.py` — [tetsu2131, *Demand-Preserving Turn Sale Timing*](https://www.kaggle.com/code/tetsutani/demand-preserving-turn-sale-timing)（2026-09-28；内含 NOTICE：shiiin9、Ahmed Berat Özer V55/V56、Thomas Tschinkel、yhay81 ShopRouter、Dmitrii Gluzdov 等）
- `farm2945.py` — [Thomas Tschinkel, *The 2945 Farm: 96% vs the Top-10 Public Bots*](https://www.kaggle.com/code/thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots)（2026-09-19，基于公开 V39）
- `v38.py` — [Ahmed Berat Özer, *Kaggriculture V38*](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v38-smarter-feed-stronger-margins)（2026-09-12）
- `c95_agent.py` — [Rayk Kretzschmar, *Findings from Zero to Top Meta*](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta) 内嵌的冻结版 C95（2026-08）

`arena.py` 与 `agents/self_v4_scheduler.py` 为本仓库原创，MIT。

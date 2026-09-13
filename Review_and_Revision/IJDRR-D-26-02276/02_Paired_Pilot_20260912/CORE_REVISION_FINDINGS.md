# CORE REVISION FINDINGS — IJDRR-D-26-02276
2026-09-12；主情境 2pc50；本轮是独立修订分支的有限实验。原稿、投稿期程序和输出保留。

**当前判断：不能继续沿用原稿的平均 makespan–population T80 权衡数值，也没有证据把整个模型判为错误。** 在 32 个共同损伤／工时实现、57 工班、四个冻结优先序列的修订 pilot 中，Hospital-first 的人口服务优势仍存在；GA-Efficiency 原来约 7.25 h 的平均 makespan 优势没有保留。平均负担下降与部分社区恶化同时存在。资源充足端可给出很小的策略差异上界，资源稀缺端的原数值尚未通过修订检验。

**已触发停止条件 2：接口修订后的 makespan 比较发生实质改变。** 因而没有扩大 MC、增加工班情境、重新运行 GA 或跑替代 mapping。下文后处理只使用已保存的 32 个实现；上界推导不是新增情境模拟。这个结果不能归因于负值处理单独一项，也不能把尚未运行的 GA 多种子／mapping 测试写成完成。

## A. 本轮实际改动与证据层级

复用 [DIAGNOSIS.md](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/DIAGNOSIS.md>)、[ISSUE_MATRIX.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/ISSUE_MATRIX.csv>)、既有优先序列、人口／SVI 对接与旅行矩阵；没有再做全面文件扫描、旧曲线复现或全流程运行。

| 层级 | 已完成 | 限制 |
|---|---|---|
| 源码／本地原文核查 | repair 抽样、任务选择、工班释放、恢复曲线、GA 参数；定向读 Xu 2007 等既有原文 | 不能代替参数实证校准 |
| 小型接口诊断 | 原 1000 样本的负抽样值重建；独立三节点事件例、工班决策信息测试 | 没有重跑旧系统曲线 |
| 新物理实现 | 32 个新 damage–duration 样本 × 4 固定策略 = 128 次事件执行 | 只有 2pc50、57 工班；无新 GA 求解 |
| 保存结果后处理 | paired 差值、tract 负担、SVI 分组、完工／路径追踪、已有候选集重加权界限 | 不是独立映射或真实供电验证 |
| 解析检查 | 114 工班无等待队列的差异上界 | 没有重跑 114／29 工班 |

独立驱动器为 [paired_pilot.py](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:1>)。改变了**任务／随机工时／释放／局部恢复之间的接口**，没有修改原 GA 算法、原图、W、fragility、PGA、source 集合或旅行矩阵。未添加道路损坏、备用电源、测试延迟、潮流或新的医院运作模型。

原仓库 HEAD 为 `925013ce5a870ae24c633838d6325b0a09b47921`；原主程序 SHA-256 为 `49b22de669239a17c000d9f92c5c340078315c0e07e085f803e964c40fbe1f38`。新驱动器与旧主程序哈希同时保存于 NPZ 的 `metadata_json`。本轮产物位于仓库旁的独立 deliverables 目录，不覆盖提交期资产。

## B. Repair-time、completion 与 information set

### B1. 从损伤到结果的实际链条

下表中的“原程序”是投稿期实现；“本轮”是可审查的事件分支，不是声称原连续曲线必然错误。

| 接口／输入 → 输出 | 原程序 | 本轮最终执行定义 |
|---|---|---|
| PGA、fragility、随机数 → `ds` | [sample_damage_states](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:728>)；给定情境 PGA，逐站抽 DS | [physical_draw](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:101>) 调用原函数；每个 realization 独立随机流 |
| DS／损伤概率 → task set | [select_repair_tasks](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:347>)；跨 MC 平均工时 ≥1 h 才入代表性任务集 | 本次 `ds>0` 的站才是任务；DS0 删除；全部四策略相同 |
| DS → duration | [damage_to_functionality_and_repair](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:795>)；normal 抽样后于 L828 夹到 0 | [physical_draw](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:101>)；正值条件化 normal，一次抽样贯穿四策略 |
| priority、资源、旅行 → arrival／start | [simulate_rule_schedule](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:3326>) 用平均 task time 推进 crew clock；GA 同类解码见 L4155 | [execute_queue](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:115>)；按观察到的 crew release 取下一项，`starts=free+travel` |
| start、工时 → completion／release | 原程序 L3433–3450：到站＋平均工时，随后该 crew 可出发 | `finishes=starts+hidden_duration`；本地服务恢复动作完成时释放工班 |
| DS、开始／完成 → raw functionality | [_precompute_ds_recovery_curves](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:2099>)；从到站起算正值条件 CDF；crew 按均值离场时 CDF 一般未到 1 | [evaluate_events](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:151>)；DS 残余值保持至动作完成，然后跳到 1；不再另走 CDF 时钟 |
| raw、图、sources → effective | 原 gate 对逐 realization 的所有 active 节点作用，然后才汇总；并非先平均再 gate | [gate_state](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:144>) 保持同一规则：raw≥0.5 诱导图中，含 active source 的 component 才通过 |
| effective、W → tract／system | 旧版 W 与人口加权；旧 KPI 为平均曲线 crossing | `services=eff @ W.T`；每次保存 tract B、T50/80/90、系统轨迹和 KPI，再做 paired 汇总 |

事件定义：时间 0 是**假定损伤状态已知的修复调度起点**；没有额外给出从地震发生到完成巡检的时长。因此不能直接把新 T80 解释为震后现场实际通电时刻。

本分支将 crew task completion、crew release、**局部服务恢复动作完成**定义在同一时刻。它不等于整套资产的永久重建完成。局部功能可因原残余值而部分保留；与 source 连通的时刻可以更迟，甚至未修复的 DS1 站已有 0.5 残余功能。effective 恢复不是强行与 crew release 同时发生。

原连续曲线也可以解释为群体平均恢复概率／连续作业进度；本轮选择完成事件，是为了让一次随机任务的工班占用与局部恢复使用同一个实现值。**这是有依据的接口建模选择，仍需说明它代表何种维修动作，不能凭 pilot 证明它就是现场真相。**

### B2. 分布选择的依据与实际负值

原参数 `REPAIR_PARAM_NORMAL_HR` 为 DS1–4 的 (μ,σ) = (1,0.5)、(6,3)、(12,4)、(36,12) h；见 [参数及注释](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:280>)。normal 的支持域包含负数，μ/σ 为 2 或 3，故负值是该分布的尾部，不是数值溢出。

[7 月 23 日稿提取文本](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/text/b2658b8d_LA_Grid_Manuscript.txt:265>) 写 T>0 的条件 normal；原抽样实现是 `max(X,0)`，会形成零点质量，恢复 CDF 却使用条件分布。Git blame 显示参数块已在初始提交 `df1fc85`（2026-05-20）出现；本地没有找到这些四组小时参数的逐项数据拟合或原始现场样本。相邻稿件段落也不能证明参数来源。为何作者写成条件分布的编辑动机没有证据，不能猜测。

定向读取的 [Xu et al. (2007)，印刷 p.272](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project//03_References//Literature//%23%23%23%23%23%23Optimizing_scheduling_of_post_earthquake.pdf>)（[提取文本 L331–345](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/text/1fa17b2f_%23%23%23%23%23%23Optimizing_scheduling_of_post_earthquake.txt:331>)）以正值 component repair time、损伤识别后形成修复序列、修完且连源后再送电为基础；其 normal 近似来自 component triangular distributions。它支持正工时与分开的恢复／连源事件，**不提供本稿这四组 μ、σ，更不证明条件 normal 是唯一正确分布**。

本 pilot 采用条件 normal 的理由是：需要修复的服务动作应占用正工时；没有证据支持“受损但瞬间修复”的零点质量；且可与现有 CDF 的数学含义一致。保留四组参数作为**情境假设**，并将 μ、σ 正确称为截断前 normal 的位置／尺度，而不是截断后样本均值／标准差。未切换到无依据的新 lognormal，也没有为了恢复旧结果调参。

按旧 32-worker 随机流重建其 1000 次主情境**原始 normal 抽样**，194 个负数与前审计夹零数量一致。不是现场负工时观测，也未重算旧恢复曲线。证据：[original_negative_draws](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:76>) 与 NPZ `metadata_json.negative_draw_summary`。

| DS | damaged draws | 负数个数／比例 | 负数均值 h | 最小值 h | E[max(X,0)] → E[X\|X>0]，h |
|---|---:|---:|---:|---:|---:|
| 1 | 860 | 18／2.093% | −0.186 | −0.816 | 1.00425 → 1.02762 |
| 2 | 2,186 | 56／2.562% | −1.271 | −9.774 | 6.02547 → 6.16574 |
| 3 | 30,474 | 41／0.135% | −1.111 | −4.448 | 12.00153 → 12.01775 |
| 4 | 58,153 | 79／0.136% | −2.806 | −12.265 | 36.00459 → 36.05325 |

总计 194/91,673 damaged draws = 0.212%；占全部 92,000 draws 的 0.211%。不能因为全局比例小就忽略 DS1／2 约 2% 的尾部概率。

在本轮 32 个实现中，用同一 uniform quantile 比较条件 normal 与夹零 normal：每个受损任务平均增加 **0.03965 h（2.38 min）**，每次全网总工时平均增加 3.62964 h，最大单任务差 2.52571 h。这仅是**工时分布层面的配对比较**，没有单独重跑该开关的服务结果，不能据此把全部 T80／makespan 变化归因于尾部处理。

仍未解决的参数语义：DS2 注释把 travel/inspection 约 3.5 h 包在 6 h 中，调度又另加 road travel。可能存在内容重叠，但没有记录能分出哪些是现场巡检、哪些是路程；**不直接判定已证实 double counting，不擅自扣 3.5 h**。这是扩大计算前应优先澄清的参数来源问题。

### B3. 四策略共同 information set

已知：相同 PGA/fragility、图/W/source、57 crew/base、固定旅行矩阵、模型工时分布，以及时间 0 的实际 DS／受损任务集。四个排序都来自原主情境的既有优先清单；剔除 DS0 后沿用，不对本次未来工时重新优化。

未知：本次具体 sampled duration、尚未发生的完成时间、其他未来损伤／交通信息。实际工时只在模拟器的私有事件日历中推进时间；策略只在 crew **实际释放**时派下一项。按事件时间取最早释放 crew 不等于把未来工时交给优化器。

旧 GA 清单是用原训练期平均工时求出的，包含同样可预先获得的分布信息；新种子独立于该训练批次。本轮比较的是**四个事先冻结的 priority-list policies**在随机执行中的表现，不是每次已知 DS 后重求 GA、更不是完美未来信息调度。由此不会只给 GA 或规则某一方未来真实工时。证据：[抽样与非预知 dispatch](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:101>)。

## C. Paired pilot 设计与保存方式

- 主情境 `2pc50`；57 工班、同一 base origins，全部在时间 0 可用；固定道路旅行时间。
- 固定 92 站／318 边、14 source proxies、W=2315×92；总人口 9,066,522。
- 策略：Hospital-first、GA-Efficiency、Population-impact、GA-HospitalFirst。第四项保留用于检验医院优先规则与 GA 的目标差异。
- 32 个独立 realization，ID 0–31；每个 ID 的 DS、duration、初始图状态、资源、起点和信息集对四策略完全相同。每次 90–92 个受损任务。
- seed=20260912，`SeedSequence([seed, realization_id, stream])` 将 DS 与工时分流，工人数／批次改变不会改样本。CSV 的 `sample_key` 用于同 ID 样本核对。
- H=480 h；事件时刻精确积分／首次 crossing，无 0.05 h 网格误差。全部 128 次执行均在 H 前恢复至模型服务 1，无本轮 T80 删失。
- B_r=∫₀ᴴ(1−S_r(t))dt，单位 **proxy h**；人口负担为 ΣP_r B_r/ΣP_r；`population_AUC=1−B_pop/H` 为归一化 AUC。不是观测停电小时或交付电量。
- 医院结果是**含医院 tract 等权**的模型服务轨迹／B／T80；按 tract 去重，不代表医院数量、容量、病床或实际运作。
- 用 32 个样本先估计 paired 方差及效应量，而不是先跑几千次。表中区间为 32 个独立 paired 差值均值的 Student-t 95% MC 区间；是固定参数／PGA／mapping 条件下的均值精度，不是个体预测区间，也不是全套 epistemic uncertainty。探索性多指标未做同时推断校正。

[PAIRED_PILOT_RESULTS.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/PAIRED_PILOT_RESULTS.csv>) 有 128 行。所有 `delta_*_vs_Hospital_first` = 当前策略 − Hospital-first。[TRACT_DISTRIBUTIONAL_EFFECTS.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/TRACT_DISTRIBUTIONAL_EFFECTS.csv>) 则以 GA-Efficiency 为 baseline，`difference_Hospital_minus_baseline_proxy_h` = Hospital-first − GA-Efficiency；**两表方向不同，列名已明确**。

额外只保存一个必要的 [PAIRED_EVENT_DATA.npz](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/PAIRED_EVENT_DATA.npz>)（约 3.2 MB），避免把逐时刻／逐 tract 数据摊成几十个 CSV。它保存：
- ID、策略名、站点／tract ID、DS／工时／uniform draws、W／人口／SVI；
- `starts, finishes, crews, previous, travel_used`：32×4×92；
- `event_times_h, event_population_service, event_hospital_tract_service`：32×4×94，尾部 NaN 是事件数不同的 padding；
- `event_station_service, event_station_gate`：32×4×94×92；可由 W 重建任意 tract 轨迹；
- `tract_b`：32×4×2315；`tract_times`：32×4×3×2315，第三轴依次 T50/T80/T90；
- `metadata_json, analysis_json` 保存抽样来源、参数摘要、机制与群体后处理结果。无 pickle 依赖。

## D. 核心数值与停止判断

下表是**逐 realization 指标的均值**；每列越小越好，单位 h 或 proxy h。

| 固定策略 | makespan | population T50 | T80 | T90 | population B | hospital-tract B |
|---|---:|---:|---:|---:|---:|---:|
| Hospital-first | 76.796 | 32.694 | 44.722 | 50.573 | 33.244 | 32.574 |
| GA-Efficiency | 76.846 | 35.533 | 48.030 | 55.502 | 36.274 | 36.567 |
| Population-impact | 76.892 | 32.548 | 44.648 | 50.837 | 33.155 | 32.768 |
| GA-HospitalFirst | 76.956 | 33.758 | 46.021 | 52.971 | 34.922 | 33.853 |

关键 paired 差值 **GA-Efficiency − Hospital-first**：

| 指标 | 平均差 | 95% MC 区间 | GA-Efficiency 更差的实现数 |
|---|---:|---:|---:|
| makespan | +0.050 | [−2.786, +2.885] | 15/32 |
| population T80 | +3.307 | [+2.132, +4.482] | 29/32 |
| population T90 | +4.929 | [+3.709, +6.150] | 31/32 |
| population B | +3.031 | [+2.756, +3.305] | 32/32 |
| hospital-tract B | +3.993 | [+3.709, +4.276] | 32/32 |

makespan paired SD=7.864 h，T80 paired SD=3.259 h。数据支持人口服务方向，**不支持给 makespan 作稳定排序**；区间跨零也不是已经证明等效。

旧稿 T80 是**平均曲线的 T80**。本轮按相同口径另算：Hospital-first 44.7685 h、GA-Efficiency 48.2104 h，差 3.4419 h；仍远小于原 12.10 h。不能把均值运算次序改变当成全部差异来源。

Population-impact − Hospital-first 的 T80 差 −0.074 h，区间 [−0.593,+0.445]；B 差 −0.089，区间 [−0.318,+0.141]。这两条规则在本 pilot 没有可识别的优胜关系。GA-HospitalFirst − Hospital-first 的 T80 差 +1.299 h，[+0.783,+1.815]；B 差 +1.678，[+1.420,+1.937]。不能据此判 GA 求解失败，见 F。

与旧 7.25 h makespan 优势相比，本轮约 0.05 h 且不确定性跨零，已足以停止自动扩大实验。**没有证明主效应反向；证明的是原强 makespan 优势未能在该修订分支保留。** 联合改变了 realization-specific task/duration、release、局部恢复事件，因此当前不是逐项因果消融。

## E. 三个科研问题的直接答案

### Q1. 更早完成全部任务，为什么可能更晚恢复人口服务？

**该机制在个别实现仍存在，但不再是这批样本的平均策略关系。** 32 次中，GA 更早完工却更晚达到人口 T80 有 14 次；Hospital 两项都较好有 15 次；GA 两项都较好有 3 次。不能把 14 次的现象推广成稳定的平均 7.25／12.10 h 权衡。

人口服务优势有可以追踪的资产顺序。以下 `mapped population=Σ_r P_r W_ri` 是 dependency 权重人口，不是站点的真实客户数：

| 站点 | ID | mapped population | H-first 平均完成 h | GA-Eff 平均完成 h | 对 GA−H population B 差的加和项，proxy h |
|---|---|---:|---:|---:|---:|
| CENTER | 300232 | 239,771 | 26.431 | 46.205 | +0.479 |
| DEL AMO | 302187 | 148,180 | 24.870 | 50.404 | +0.366 |
| VERNON | 306450 | 118,229 | 23.170 | 46.543 | +0.265 |
| NOGALES | 301517 | 130,701 | 25.392 | 46.569 | +0.233 |
| HOLLYWOOD | 303899 | 209,068 | 26.236 | 36.721 | +0.200 |

这些加和项来自 **gate 后 station B × W 加权人口**，严格加总到系统 B 差。所有站点的总差 3.03054，可记账拆为局部 raw timing 项 2.69285 加 gate 额外缺损项 0.33769。它是机制定位用的代数拆分，不是固定其他条件后的独立 causal attribution。

例如 FAIRFAX（303099）两策略本地完工均为 24.079 h，却贡献 +0.142 proxy h 的系统差，说明其他节点／路径的连源时序也影响结果。不能仅按单站完工提前量解释全部 tract 变化。相反，LA MIRADA（306369）在 Hospital-first 的完成时间约 37.414 h、GA 24.018 h，对系统差贡献 −0.133；存在另一批社区更晚恢复的直接来源。

**一个明确的完工尾端例子：realization 11。** 选择规则是“在已出现权衡的实现中，距该子集两项差值中位数最近”，不是挑最夸张样本。GA-Efficiency makespan 早 3.959 h，population T80 晚 1.726 h。Hospital 的最后任务是 SYLMAR EAST（306489，mapped population 18,908，在 92 站中约第 13 百分位）；同一 sampled duration 56.004 h，Hospital 到站 12.744、完成 68.747，GA 到站 0.434、完成 56.438。GA 的最后任务换成 LIGHTPIPE（303169），两策略该站均于 64.789 完成。**低 mapped-population 任务的较晚开始能决定 makespan，而另一批高 dependency 任务决定人口 T80。** 这是同一个 paired 实现的可追溯例子，不证明 SYLMAR 是所有实现的共同瓶颈。

source 路径也已保存：接近整体 T80 差中位数的 realization 6，Hospital 在 42.527 h 的事件触发站 300493，其人口跳升最大目标 308991 的一条 active source 路径为 307693→300493→303620→308991；GA 在 45.003 h 达 T80 的触发站为 source 305984。路径表示现有图上的可达性，不能称输送功率路径；没有证据支持唯一全局关键路径。

证据：NPZ `starts/finishes/station_b/event_station_gate`，`analysis_json.mechanism`；[机制后处理](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:326>)。需要 causal edge/node 归因时才做固定样本反事实；本轮停止后没有继续跑。

### Q2. 总体改善是否伴随特定社区恶化？

**是；而且分类必须区分先取 tract 平均和逐实现计数。** 以下均为 Hospital-first 相对 GA-Efficiency，ΔB=H−GA，负值改善：

- 按每个 tract 的**平均 ΔB**分类：1,994 tracts／7,778,675 居民所在 tract 改善，321／1,287,847 恶化。平均改善超过 1 proxy h 的人口为 5,406,839；平均恶化超过 1 的为 961,118。
- 逐 realization 分类再取均值：改善人口约 **6,749,623**，恶化约 **2,276,276**；其余近似无差。原 6.906／2.161 million 不应继续当成新模型固定事实。
- Hospital 改善出现于至少 90% 实现的 tract 共 5,215,252 居民；恶化出现于至少 90% 的共 452,668。32 次的比例估计较粗，不是每个 tract 效果已经精确识别。
- 人口加权 gross improvement =3.83616 proxy h，gross worsening =0.80562，净减少 =3.03054。这里先逐实现取正负部分，再平均；不会让正负相抵隐藏恶化量。
- tract **平均 ΔB**的人口加权分位数：P05 −15.025、P25 −5.549、P50 −1.776、P75 −0.337、P95 +4.947 proxy h。改善与恶化幅度都不是只报“有变化”。

SVI 固定使用 prior join 的 **CDC 2022 RPL_THEMES**，按 tract 分四组，组内负担按同一人口权重；排除 24 个 sentinel tracts／16,979 居民。有效 2,291 tracts／9,049,543 居民。它不是原系统 SVI 曲线使用的 NRI `SOVI_SCORE`，也不是四个 theme percentile 的平均；两种原始变量都保留在 CSV。出处：[已核对的人口与脆弱度 join](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/tract_population_vulnerability_join.csv>)、原审计 §3.5。

| CDC SVI 组 | 人口 | GA baseline B | Hospital B | ΔB（95% MC 区间） | 人口加权 P90 B：GA→Hospital |
|---|---:|---:|---:|---:|---:|
| Q1 最低 | 2,152,787 | 38.024 | 35.578 | −2.446 [−2.747,−2.146] | 52.953→50.878 |
| Q2 | 2,288,636 | 36.883 | 33.429 | −3.455 [−3.735,−3.175] | 53.132→48.262 |
| Q3 | 2,312,922 | 35.650 | 32.484 | −3.166 [−3.452,−2.880] | 51.589→47.218 |
| Q4 最高 | 2,295,198 | 34.657 | 31.644 | −3.012 [−3.376,−2.648] | 50.173→45.793 |

P90 列为“每次 realization 的组内人口加权 P90，再跨实现平均”，不是均值负担的 P90。各组平均及尾端均下降，但收益不随 SVI 单调增加。Q4−Q1 的有方向负担差由 −3.367 变为 −3.933 proxy h：高 SVI 组在两策略中本来就较低；不能把更负的差叫作“原有不利差距缩小”，绝对差反而增大约 0.566。

以 GA **平均 baseline B** 定义人口负担最高约十分之一的 tract：251 tracts／921,172 居民，平均 ΔB=−9.705；其中仍有 61,353 居民所在 tract 平均恶化。这个尾组由同批模拟结果定义，适合描述“原高负担者如何变化”，不是独立的震前预测分组。SVI 与 ΔB 的描述性 Spearman 约 0.034，没有单调 vulnerability targeting 证据；baseline B 与 ΔB 约 −0.669。不能把后者解释成因果规律。

**可以写的发现是：人口总体负担降低，收益与局部损失空间分布不均；既有高负担区域平均受益较多，但仍有明确恶化群体。不能写 equity 已经证明改善。** 具体 tract 的数值、幅度、概率及 baseline 均在 tract CSV；逐实现对应值在 NPZ。

### Q3. 什么时候策略真正重要？

57 工班下，Hospital 相对 GA-Efficiency 的人口 T80 平均优势约 3.31 h、B 优势约 3.03 proxy h，具有可识别的绝对效应；Hospital 与 Population-impact 则近似并列。不能笼统说“四策略均有实质差异”。

**114 工班端无需再抽 MC 就能界定。** 本模型最多 92 个受损任务，114 crew 全在时间 0 可用，任务无需等待上一个维修完成。对同一个 paired duration 向量，策略之间只可能改变被分配的 depot 旅行时间。按原 crew scaling 和旅行矩阵，站点跨可用 depot 的最大旅行差为 **0.3684475 h（22.11 min）**。因此所有资产完成时间的策略差绝对值均 ≤ε=0.36845 h。

在单调恢复、非负 W、相同 source gate 的条件下，该完成时间界限可传播为服务曲线的水平位移界限，从而 **|ΔT50/80/90|≤ε，|ΔB_pop|≤ε**。这是保守的模型内解析上界，不是 114 工班 pilot 均值；若 crew 到达不同步或添加新约束，上界需重推。证据：[_scale_sensitivity_crew_origins](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:4565>)、[resource_bound](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:339>)、NPZ `analysis_json.resource_bound`。

这支持原 C 的定性解释：大量资源下低 rank correlation 可以只代表极小绝对差。约 0.37 h 是否低于决策容忍度，应预先说明，不能把 rank 次序本身当政策重要性。

29 工班下，当前样本每次至少 61 个任务必须排队，资源稀缺放大顺序效应有明确的队列机制；**修订模型下是否仍有 23.20 h spread 尚未运行**。尚不能定位某个经过检验的中间“转折工班数”。已知充分条件是所有 crew 在 0 可用且 crew 数不少于任务数，顺序等待效应消失；不是说少于该数一定有很大效应。旧数值出处仅为 [原 crew_rankings.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/crew_rankings.csv>)。

## F. GA 最低验证：完成项与明确延期项

| 项目 | 真实实现／证据 |
|---|---|
| 编码／解码 | 任务 permutation；按最早可用 crew 派任务，加旅行与代表性平均工时。[run_stage_5](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:3859>) |
| population／generations | 100／100；98 random permutation＋按 task value 降序及 task time 升序各一个 |
| crossover | ordered crossover，外部概率 0.8 |
| mutation | inversion；外部概率 0.2，内部 `indpb=0.2`；每个 offspring 真正尝试 inversion 约 0.04，不能只写“20% inversion” |
| selection | tournament，size=3 |
| elitism／停止 | `eaSimple`，无 Hall of Fame、无 elitism、无提前停止；固定 100 代，取**最后一代**最佳 |
| seed | (42＋CRC32(scenario)＋CRC32(policy)) & 0xffffffff，Python random 与 NumPy 均设置 |
| convergence／multi-seed | 旧版没有保留 trace；**本轮未新跑**，由于 pilot 已触发停止，不伪造收敛历史 |

参数见 [Config](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:154>)；mutation 与选择见 [DEAP setup](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:4036>)；执行及 seed 见 [GA run](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:4175>)。无 elitism 是算法选择，不自动等于 bug。

原目标为：
F = Σ_i v_i max(504−C_i,0)/(504Σ_i v_i) − w_M·C_max/504。
评价 horizon 为 480+24=504 h，不是本轮报告指标的 480 h；C_i 是代表性工时解码的 task completion。pop／hospital／SVI 各在当前任务集合 min–max，服务分数再与 20% network score 混合。network score 的 role／voltage／lines 权重为 0.7／0.2／0.1，lines scale=12；见 [normalization](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:3878>)、[fitness／混合](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/C257H_Project_Main.py:4100>)。

HospitalFirst 的人口／医院／SVI／makespan 权重为 1／20／1／0.1；医院分量在最终 v 中的系数为 0.8×20/22≈0.7273。20 不是 20 倍真实医院服务，也不是直接优化 hospital T80。Hospital rule 先按含医院 tract 的映射链接数、再按链接人口排序；GA 用 W 加权 hospital coverage 再正则化。两者不同，本 pilot 新医院 KPI 又是含医院 tract 等权的服务曲线；三者均非床位容量。

前一轮同一 GA-HospitalFirst fitness 的比较已确认：GA-HospitalFirst 0.924922，Hospital rule 0.922243；复用 [same_fitness_comparison.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/same_fitness_comparison.csv>)，没有重新验证旧曲线。**优化自己的 task objective 取得较高分，与 population T80 较差可以同时成立。** 新 pilot 延续后者，但没有把旧目标替换成服务 AUC，也不能据此判断优化器在随机执行目标上收敛最优。

若后续保留 GA 为主要结果，只在一个固定 information set／expected-duration benchmark 上，对两种 retained GA 各做少量种子（例如 3 个，100×100 保持），保存每代 best/mean 与 best-so-far，并在同一 fitness 下比较规则。该工作与物理 MC 分开；有必要再扩种子，而非现在为“让 GA 赢”调权重。当前建议将 GA 降为两种明确 objective 的基准策略，不以算法创新作为主线。

## G. 原论文结论状态

“stable”仅指本 pilot／已说明的模型条件，不代表真实 LA 系统已验证。

| 原发现／主张 | 状态 | 现在可支持的版本 |
|---|---|---|
| Hospital 相对 GA-Efficiency 更快恢复 population service | stable（方向）；幅度 weakened | T80 优势 3.31 h，B 3.03；原 12.10 h 不稳健 |
| GA-Efficiency 平均早 7.25 h 完成全部任务 | unsupported after correction | 本轮 Δmakespan≈+0.05 h，区间跨零；没有支持反转 |
| 更快完工与更快人口恢复可以分离 | stable 为机制可能性；平均策略权衡 weakened | 14/32 实现有原方向，不能再写成普遍平均关系 |
| 总体改善伴随部分社区恶化 | stable（条件性分布结论） | 平均 tract 分类约 778 万改善／129 万恶化；逐实现恶化均值约 228 万 |
| 原 6.906／2.161 million 是固定受益／受损人群 | weakened | 分类随实现与先后平均顺序改变 |
| 高资源时策略可能近似并列 | stable 的模型内解析解释 | 114 crew 差异上界约 0.37 h；无新的实测／pilot 值 |
| 29 crew 下 23.20 h spread、具体资源转换点 | unsupported in revised branch／待检验 | 仅知道排队机制，未跑新 crew 条件 |
| SVI-weighted T80 提前证明 equity improved | unsupported | 固定组负担、方向差距及恶化群体才是本轮证据 |
| GA 因 T80 不如 Hospital 而优化失败 | unsupported | fitness 与服务 KPI 不同；旧同目标比较已支持 GA 有所改善 |
| connectivity proxy＝actual delivered electricity／医院运作 | unsupported | 当前仍无容量、潮流、功率平衡、load shedding |
| 已证实某项主效应稳定反转 | **reversed：本轮没有足够证据** | 不将跨零的小正点估计写成反向发现 |

## H. 是否值得扩大 MC，以及最小下一步顺序

**现在不值得直接增加样本量。** 更大 MC 可以缩小这套接口下的均值区间，却不能解决工时含义、比较目标改变、mapping 或容量缺失。

1. **先固定事件与工时语义。** 对四组 μ/σ、DS2 注释的 travel/inspection 内容、原 CDF 是恢复概率还是连续作业进度，补参数来源与明确单位。若只能作为假设，明确采用“已知 DS 后的服务恢复动作”而非实际物理重建工期；同步修订方法及适用范围。
2. **如需定位消失原因，复用这 32 个已保存样本做最小接口消融；不增加 physical MC。** 先固定实际完成序列，只对比原 CDF 后处理与完成事件后处理，以定位服务曲线差异；这是语义诊断，不把两者都称现场真相。另仅在必要时做条件 normal／夹零工时的共同 quantile 对照。旧 representative makespan 与新随机 Cmax 的差异需单列，不能从改变局部恢复曲线推断 makespan 原因。
3. **完成 I 的定向 mapping 查核后，再决定有限扩大。** 若共同接口和 mapping 下人口 B／T80 方向继续清楚，可逐批扩展到预先选定的绝对差精度；以 paired standard error 与预先规定的 practical tolerance 停止，不能以某个策略显著获胜为停止标准。先补 29 crew；114 crew 已有上界，不必先跑全资源网格。GA 多种子独立评估，不混成物理 MC 误差条。
4. **投稿前最低基础：** 一致事件／工时定义、独立测试样本的 paired 服务与分布结果、少量有物理含义的 mapping 对照、对容量缺失的可信范围限制、所有数字与术语同步。不能凭当前 pilot 就直接转投。

报告区间只反映给定 PGA、fragility 参数、W、sources 下的物理抽样；空间相关震害、参数 epistemic uncertainty 和新 GA 种子尚未包括。没有必要为了形式完整先加所有不确定性模块。

## I. Mapping／source proxy 的最小必要工作

复用前审计，不重新扫描：原候选 inventory 有 merged 4,260、openbasin 4,442、LA County 442 条记录，**它们不是同一个“原电气网络”的节点数**。当前 92 是先选入的 station inventory；简单地理筛选 302 站中只有 73 与其重合，另 19 个现行站／229 个未保留候选需要选择历史解释。66,640 vertices／68,116 segments 是几何网络，不是 92 站的电力等值证明。来源与差异见 [inventory_selection_difference.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/inventory_selection_difference.csv>) 与前审计 §3.1。

本轮做了比重复 cutoff 更有针对性的**现有候选支持集界限**：固定这 32 个完成序列与 source gate，对每个 tract 求其现有 W>0 候选站的平均 Δstation B 最小／最大值。任何只在**同一候选集**中变动非负归一化权重的 tract 平均 ΔB 都落在该区间。

| 现有候选集内的符号界限 | tract 数 | 人口 |
|---|---:|---:|
| 任意重加权均改善 | 1,489 | 5,714,609 |
| 任意重加权均恶化 | 110 | 425,939 |
| 符号可能依赖权重／近似并列 | 716 | 2,925,974 |

证据：tract CSV 的 `existing_candidate_support_delta_lower_h/upper_h/sign`，[候选集凸组合界限](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:319>)。这是固定完成序列下的数学界限，**不是 feeder mapping 验证**；若更换候选站、跨 utility boundary、改图或重新生成依赖 W 的 GA／规则顺序，该界限不适用。

下一步只聚焦那 716 个 mixed-sign tract 中人口／效应较大的位置，以及 CENTER、DEL AMO 等高影响资产的依赖。先从已有 inventory selection、地理与 source/owner 记录恢复这些关键对象的选择依据；此前未找到独立 feeder/customer 对应。无新严重 mapping 错误已被证实，亦无证据宣称当前 IDW 已正确。

最多三组有意义的对照：
1. 按 tract 几何到最近合格 station 的 nearest-1，检验当前“地理接入＋线路最短路”传播假设；
2. 局部 nearest-3 的平面距离权重，固定相同站 inventory，检验非本地电网捷径对社区效应的影响；
3. **只有取得可核对 utility/service territory 时**做 boundary-restricted 局部映射；行政县界／owner 标签本身不等于 feeder ground truth。

前两项也是空间替代假设，不声称有 feeder 物理真实性。先在冻结四策略／同一 32 样本上比较 ΔB、受益／恶化人口、SVI 差、尾端和 T80；若结论翻转，先解释受影响的少数站／tract，再决定是否重求 W-dependent priority，不能把两种效应混算。

source gate 仍只支持“source-connected accessibility”。缺 station capacity、bus MW、reactance、thermal ratings 与需求约束时，无法证明替代源足以满足负载；高人口 dependency／单源瓶颈的比较尤其可能被供需限制改变。当前数据不足以给 LA 跑可信的潮流验证。最低物理 benchmark 可在有完整参数的少量节点系统上对照 capacitated service 或 DC load shedding 的排序失效条件；它只能界定 proxy 的适用范围，不能验证 LA 数值。完整 LA AC/DC reconstruction 不属于本轮必要工作。

## J. Revision notes、暂缓事项与交付核验

以下以 revision note 保存，不覆写候选提交 DOCX：

- Table 4 的 **Degree-first makespan=63.23 h、Closeness-first=62.54 h**，两行纠正；这些是旧固定排程表数值，不用新 pilot 值混替。
- Northridge 文本改为旧保存结果 baseline **14.10 h**，logistics **14.45–15.10 h**；继续称时间尺度合理性对照。不可把时间 0 定义不同的本 pilot 直接套入历史恢复验证。原值依据 [verified_system_metrics.csv](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Audit_IJDRR_20260912_01/verified_system_metrics.csv>)。
- repair distribution 写清正值条件化／截断前参数；同时说明尚缺小时参数实证来源和本轮事件定义，不能只修改公式。
- 将实际 delivered electricity、客户 outage hours、医院 operational recovery 等无支撑表述限定为模型 service/accessibility proxy；使用 cumulative service deficit (proxy h)。
- 将“SVI 加权提前＝公平改善”改为固定群体负担、方向差距及局部损失；不能把本轮各组都改善误写成差距缩小。
- 将“GA T80 较差＝优化失败”改为 task objective 与 population-service KPI 不一致；保留规则基准。
- Table 1 保留；GA 技术、标准 percolation、聚类／hotspot 可作附录。当前结果主线是共同信息与资源条件下的**服务收益、局部损失和条件性排序**，不是方法集合。

**现在不值得做：** 重跑旧曲线、全 scenarios／all crews／all strategies、给 GA 调参争胜、为了置信区间漂亮盲增 MC、堆砌 inequality indices、重新全面读文献、构建完整 LA 潮流、道路震损／医院备用电源／动态信息扩展、大批排名表与装饰性图。

已执行独立接口检查：三节点例中负载站 3 h 完成而连接桥 10 h 才完成，service T80=10 h；无损网络 B=0／T80=0；两工班的下一任务只在观察到释放后开始，更改尚未派出任务的未来工时不改变此前派遣；事件积分与 tract 加权的系统 B 一致。见 [check_interface](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/paired_pilot.py:434>)。这些检查支持实现与本轮定义一致，不是物理验证。

本轮只有六个交付文件：本报告、两个指定 CSV、一个 NPZ、一个驱动器与 [一张核心诊断图](</C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/00_Project_Deliverables/Revision_PairedPilot_20260912_01/CORE_DIAGNOSTIC.png>)。图左显示 32 个 paired makespan/T80 差及均值的边际区间；图右显示各 SVI 组中 tract 平均 ΔB 的人口累积分布。图中没有加入额外情境或原稿目标点。所有旧输入／输出保留；没有把新结果写进提交稿或执行转投。

交付前检查通过：128 行的四策略配对、同 ID 的 sample_key／总工时一致、CSV 的直接差值与逐实现原值一致、2,315 个 tract ID 唯一且补齐 11 位、NPZ 的 tract B／T 指标均有限、源程序及驱动器哈希匹配、39 个报告本地链接可定位。原仓库 tracked diff 为空。

**下一轮最有价值的工作是解决工时／恢复动作的含义与定向 mapping 支持，然后用同一批保存样本检验必要的接口开关。当前证据不支持直接扩大 MC 或把原 7.25／12.10 h 权衡继续当摘要主发现。**

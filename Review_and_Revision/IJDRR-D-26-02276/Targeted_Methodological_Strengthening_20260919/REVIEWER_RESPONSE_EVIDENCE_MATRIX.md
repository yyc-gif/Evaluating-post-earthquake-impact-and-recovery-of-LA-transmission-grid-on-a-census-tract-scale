# Reviewer证据表：候选纠正与两个针对性对照

2026-09-19。依据[原始审稿意见](../01_Reviewer_and_Decision/IJDRR-D-26-02276_editor_review_transfer_record.md)，更新Round26证据，不覆盖旧表。研究定位为**有限稳健性支持的条件性恢复决策研究**。本表是revision/response依据，不表示物理验证、社会公平优化或期刊已接受回应。

主结论和可用于Results/Discussion/Abstract的草稿见[科学补强报告](TARGETED_METHODOLOGICAL_STRENGTHENING_RESULTS.md)。完成192条新增科学链、复用64条旧基准链、0次新GA搜索、0套新物理抽样。32个评价样本已使用过；本次是纠正重评和配对假设对照，不称独立验证。

## 证据读取约定

- [逐次指标](REALIZATION_STRATEGY_METRICS.csv)：`condition`为`corrected_baseline`、`AB_lambda_0.5`、`AB_lambda_2`或`DS4x2`。A/B离线条件的时间阈值及logistics列保持NA。
- [配对效应](PAIRED_EFFECTS.csv)：`strategy_minus_HF`是该情景相对HF的效应；`change_in_strategy_minus_HF`是情景间该效应的变化；`candidate_correction_minus_R26`比较纠正前后。`mean_paired_difference`、`ci95_low/high`、`fraction_delta_lt_0`均以32个realization配对，不把策略当独立样本。
- [群体绝对负担](GROUP_ABSOLUTE_BURDEN.csv)、[指标分布](METRIC_DISTRIBUTIONS.csv)、[排名频率](METRIC_RANK_FREQUENCIES.csv)与配对差一起解释。低Gini或小gap本身不是公平改善。
- [逐tract效应](TRACT_PAIRED_EFFECTS.csv)和[受益/受损人口](WINNER_LOSER_POPULATION.csv)：±1 h是实用分类阈值，不是显著性阈值；`classification_of_32_realization_mean`和每次realization分类是不同统计量。12个完全unresolved tract、51,770人始终单列，负担及方向概率NA。

## 对应原始意见的证据与修订动作

| 原编号与准确关切 | 本次处理及实际证据 | 应写入修订稿的结论/动作 | 尚未解决或通过范围限定回应的部分 |
|---|---|---|---|
| **R1 #1**：原IDW依赖缺实际utility/feeder/outage依据；需超越cutoff的验证或稳健性分析，限制actual-service解释。 | 延续官方candidate集合、固定attachment与Class C，混合A/B tract仅改变B相对影响λ=0.5/1/2，保持ResolvedMass不变。固定四序列，不重建priority。`PAIRED_EFFECTS`中人口归一化负担ΔHF：Balanced −0.300/−0.295/−0.291 h；HospFirst −0.177/−0.166/−0.154；Efficiency +15.134/+15.076/+15.053。Efficiency Q4额外负担22.558/21.526/20.377 h，自身signed gap均值+0.495/−1.388/−3.540 h。 | 替换“mapping稳健”笼统说法：总体效应方向在这两项设计压力情景保持，群体差异幅度及相对高低仍依赖评价假设。Methods写明保持C质量、R和candidate集合的公式，Results同时报群体效应。 | **有限假设对照＋范围限定回应**，不是服务份额/真实接线验证；未验证B自身损伤可忽略，未比较按新mapping重新制定的政策。0.5和2不是经验置信范围。 |
| **R1 #3**：mean duration调度掩盖realization task set及损伤/工时不确定性，策略排名如何传播不确定性？ | 复用32套DS/positive duration，所有策略同realization配对；DS>0入queue，duration只影响completion/release。新增64条候选重评＋128条DS4×2完整链。`REALIZATION_STRATEGY_METRICS`保存DS/duration hash、task_count；`PAIRED_EFFECTS`保存配对区间。Efficiency人口ΔHF由15.076增至26.245 h，DID11.169 [9.303,12.880] h。 | 明确32套physical realizations而非128套独立损伤抽样。展示样本分布、效应大小及排名频率：人口负担最低频率Balanced从基准68.75%变为DS4×2的56.25%，不宣布普遍冠军。 | 分布内随机性与DS4相对工时压力对照并不覆盖全部模型不确定性。既有评价集纠正重评不是新独立外部验证。 |
| **R1 #4**：历史restoration只能contextual check，非tract模型验证；应定位scenario comparison而非实际恢复预测。 | DS4工时×2保持同DS、sequence、travel/crew/source/W1；不重新优化。`condition=DS4x2`与`change_in_strategy_minus_HF`给出比较效应变化。模型时长明确为scenario-based on-site action duration。 | 删除历史曲线“验证了tract恢复”的表述；将工时对照写为同一决策在重损更耗时条件下的表现。重损相对工时会放大某些社区代价，不仅平移绝对恢复时钟。 | **主要通过范围限定回应**：未校准LA实际repair时长、distribution operations或customer switching；DS4×2不证明72 h更真实。 |
| **R1 #5**：SVI-weighted T80不是equity；需群体差距/不平等指标或收窄公平主张。 | 固定NRI SOVI quartile、Q1–Q4绝对负担、signed/absolute gap、population-weighted Gini。`corrected_baseline`：Efficiency Gini0.1765 vs HF0.2187，但人口负担+15.076 h，Q4+21.526 h；DS4×2 Q4+37.830 h。新Balanced四组略改善，HospFirst Q1+0.117而Q4−0.413 h。两个人口分母并列，12个unresolved不再归near_zero。 | 将“公平改善”改为“模型内分配后果/负担不平等”。负gap表示本模型Q4较低，不表示公平已达成。Balanced/HospFirst改善Q4同时绝对Q4–Q1差距扩大，必须展示绝对水平。 | 没有公平目标/约束，不能声称公平规划净收益或因果社会公平；不再以SVI-T80、clustering/hotspot替代分配证据。 |
| **R1 #6**：GA参数、重复seed、收敛与权重20依据不足。 | 原30 runs保留；不新增搜索。`CANDIDATE_OBJECTIVE_COMPARISON`显示原最后代Balanced/HospFirst劣于可重建初始化。恢复fitness0.793690122004/0.916459946176，与记录最高分一致；HF同目标为0.792733835572/0.916319981609。源码`run_ga`加独立best-so-far archive及HF incumbent比较，不改变population替换或RNG调用。`FROZEN_CANDIDATE_SEQUENCES`记录来源/hash。 | 明确最后代、可重建最好候选、未保存中间染色体、全局最优四者区别。Balanced/HospFirst改进来自确定性初始化，不归功于遗传搜索；20是hospital-dominant policy-design coefficient，非校准偏好。 | 原中间序列未保存，不能声称恢复所有seed历史最优。没有全局最优或GA优于简单构造的证明。旧配置/10-seed证据仍由Round26保留报告支持。 |
| **R1 #7**：为什么HF优于GA-HospitalFirst？fitness与T80/AUC目标关系是什么？ | 同目标HospFirst候选fitness0.916459946176>HF0.916319981609；新候选人口负担Δ−0.166 [−0.257,−0.064] h；医院tract负担−0.022 [−0.104,+0.066] h；T80−0.197 [−0.735,+0.204] h。见`strategy=GA-HospFirst`逐metric配对行。 | 撤回“HF必然胜GA”的旧故事。先纠正候选选择，再区分有限搜索表现与目标差异。静态站点加权完工fitness不是source-gated社区burden；小fitness优势不保证所有报告指标更好。 | 不通过调整目标保证GA获胜，不把接近零的医院/T80效应解释成实证优势。多系数同时不同，不能隔离归因于医院weight20。 |
| **R2 #9**：为什么使用/信任黑箱GA，算法详情与价值何在？ | 同一decoder/ExpectedWork下显式HF incumbent重评分；best-so-far和候选来源可查；原参数、收敛数据保留，未再搜30次。Efficiency仍保留原canonical，fitness0.368272354637>HF0.338924957558（自己的目标）。 | 将GA定位透明的有限预算比较工具，而非方法创新/最优证明。报告两个policy的搜索没有超过已记录确定性初始化；不把输出差改名comparator就回避选择问题。 | 不宣称GA是必须或最好算法；当前科学贡献在固定序列如何分配burden，不在遗传库本身。 |
| **R2 #13**：logistics/resource constraints不清楚，也不是新方法。 | C57 pooled resource、固定11×302/302×302 directed travel；crew最早release后按固定queue取task，完成=arrival+realized duration。`NEW_RUN_TASK_EVENTS.csv.gz`保存任务事件；`PAIRED_LOGISTICS_MECHANISM`显示DS4对照改变crew/previous-task/arrival。`makespan_hr`、`total_travel_hr`和社区效应并列。 | 用简洁事件语义解释资源如何约束，而非宣称scheduler创新。Efficiency平均makespanΔHF基准约0.002 h，区间跨0；其大社区代价不能包装成已有明确平均makespan收益的交换。 | **范围限定**C57是pooled regional scenario budget，不是verified staffing；没有C29/C114实验，不声称验证资源数量效应或utility-specific eligibility。 |
| **R2 #14**：关键是针对性/公平规划改善多少、代价是什么、谁承担。 | 基准HospFirst改善Q4但恶化Q1；Efficiency四组均增加burden。按32次平均±1h分类，Efficiency使663 tract、80.07%全部strict-SCE人口更差；DS4×2为763 tract、93.33%。另列逐realization分类均值，不能混同这两个百分比。Balanced基准110 tract改善、9 tract恶化；HospFirst61/3。 | 用`WINNER_LOSER_POPULATION`与`TRACT_PAIRED_EFFECTS`直接回答谁获益/延迟；并列Q绝对负担、Gini、makespan/travel，不把小gap自动称改善。人口比例分母为全部817 tract人口；unresolved1.449%单列。 | **收窄研究问题回应公平优化部分**：这些不是隔离单一公平干预的实验，不能回答“优化公平政策的最佳收益/成本”，不能将四点称Pareto边界。 |
| **R2 #16**：结论应讲决策如何使tract负担不同，而非方法优缺点。 | `INTERFACE_INTEGRATED_CONTRIBUTIONS`给出Δburden积分分解；例如Efficiency基准人口ΔHF中310167、302187、301489接口贡献约2.375/2.363/2.027 h。300829+303005始终合并。`PAIRED_LOGISTICS_MECHANISM`仅支撑已保存调度变化，不臆造旧HF/Eff时间路径。 | Results/Abstract围绕序列分配后果、相等但更差的实例、重损工时对社区代价的放大与映射群体敏感性。删软件QA次数/模块数作为研究贡献。 | 这些是固定模型内反事实计算与积分归因，不是现实社区的因果解释；没有证据的地理/医院/网络关键性故事不写。 |

## 相关总评与其他原意见

**R2 #4/#12（发现不能只是显而易见的排名）**：本轮可写的非排名发现是：改善Q4不一定缩小绝对群体差距；更低Gini可来自四组同时承担更高负担；重损相对工时改变策略代价量级；总体负担方向对A/B压力稳定而部分群体高低关系不稳定。均有上表实际数值支持，不把方法“效果好”作为发现。

**R1 #2（source connectivity不等于实际供电）**：本轮**通过范围限定回应**，不声称物理验证。参考source-availability与连通proxy没有capacity/power balance/voltage/load-shedding；共享proxy并不证明这些遗漏不能改变相对策略结果。没有新增潮流或source sensitivity。结论限于条件性service-access proxy。

## 修订决策

**CORE FINDINGS CHANGED — REFRAME REQUIRED；纠正后的证据足以进入定位B修订。** 不保留旧HF普遍优势或“三GA均使四组恶化”；不升级成公平优化、实际LA恢复预测或全局最优规划。无需自动启动下一批模拟。本轮证据支持修改Results/Discussion/Abstract，并把上述范围限制写进研究问题、方法和结论，而不只藏在limitations最后一段。

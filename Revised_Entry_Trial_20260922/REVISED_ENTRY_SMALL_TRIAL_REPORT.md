# July92原入口修订路径：真实输入小规模试运行

**执行状态：完成；仅为方法接线和实际数据诊断，不是论文最终样本。** 从`C257H_Project_Main_expanded.py --revised-trial`调用原`run_pipeline`，使用固定92站／318边／2315 tract、2pc50、原14 Core sources、0.5 threshold、C57、修订默认utility mapping。固定5套物理实现：独立planning 2套、evaluation 3套。Stage 3无工班竞争、Stage 4原七条规则、Stage 5 direct-community候选均经过相同completion-event/source gate；之后对保存的27条evaluation站点轨迹做28种mapping×gate离线评价。本报告中的小时数都是**模型内可表示服务的累计负担或事件时刻**，不是观测居民停电时长；3个evaluation实现不足以支持策略排序或不确定性推断。

## 已得到的结果

|Stage/策略|utility mapping、0.5 gate下人口累计负担均值(h)|人口T80均值(h)|医院tract平均负担(h)|
|---|---:|---:|---:|
|无工班竞争恢复|31.578|43.497|32.202|
|Hospital-first|34.197|46.460|33.576|
|Network impact-first|33.402|45.134|33.475|
|Random reference|40.262|54.218|41.082|

Stage 5的两seed（42、43）、8个体×3代诊断都**未改善**planning样本上的`impact-first` incumbent（direct objective最优fitness为−31.580611）。因此档案中的`direct-community`是保留的`impact-first`规则序列，evaluation结果与其完全相同；不能称GA新解优胜。原七条规则仍都执行并保存。完整策略均值、Q1–Q4、Gini见`TRIAL_RESULTS/SMALL_TRIAL_STRATEGY_DESCRIPTIVES.csv`；完整曲线及地图见Stage 6目录。这些数值不是正式科学结论。

### 同一站点轨迹下mapping变化

|策略|July人口负担(h)|Utility人口负担(h)|变化M1−M0(h)|July人口T80(h)|Utility人口T80(h)|平均每tract绝对负担位移(h)|
|---|---:|---:|---:|---:|---:|---:|
|Hospital-first|35.144|34.197|−0.947|48.055|46.460|1.767|
|Impact-first / 此次direct incumbent|34.195|33.402|−0.793|46.356|45.134|1.603|
|Random|39.866|40.262|+0.396|53.067|54.218|1.363|
|无工班竞争|31.672|31.578|−0.094|43.466|43.497|1.318|

每个策略位移覆盖2315 tract×3 evaluation实现；中位绝对位移为0，而Hospital-first最大单个tract/实现位移45.421 h。总量变化与局部归属变化程度不同，不能用总体差掩盖局部变化。`TRIAL_RESULTS/TRACT_MAPPING_SHIFTS.parquet`和地图保存逐tract结果；`PAIRED_MAPPING_EFFECTS.csv`保留每个相同实现的配对差。

**截断对照（Hospital-first，utility eligibility）**：no cutoff / 1% / 3% 的人口累计负担分别为34.923 / 34.380 / 34.197 h，人口T80分别为47.425 / 46.954 / 46.460 h。这是同一物理轨迹的评价假设差异，不能从中校准真实customer share。LAX–RS-N在3%被删的外部支持联系仍单独保留为局限。337个SCE可比较tract的candidate-supported版本中17个零重叠保持unresolved；在**相同320个正质量tract**上，Hospital-first的July / utility / candidate-supported人口累计负担为30.765 / 30.720 / 30.359 h，T80为44.105 / 44.105 / 42.943 h。这不代表817 strict-SCE整体。

### 功能、threshold与source-path

Hospital-first在M1/G1下的人口累计负担34.197 h逐项为：station自身功能损失29.602 h（86.56%）、0.5 threshold增量0.971 h（2.84%）、source-path断连增量3.624 h（10.60%）；三项相加精确等于总量。Impact-first相应为28.787 +0.941 +3.675=33.402 h。G0仅station自身功能的Hospital-first负担29.602 h；baseline gate提高到34.197 h。低阈值0.05与高阈值0.75在本3样本中的Hospital-first总负担分别34.193和34.197 h；这不能推广为threshold无关。

Hospital-first的静态单路径站贡献平均占其source-loss积分的26.5%（三个实现分别23.8%、28.0%、27.7%）。其余来源于其他站点与事件状态，因此这次**不是只由八个静态单路径站主导**。按同一mapping/G1，Hospital-first source-path loss最高的tract均值包括06037134905/906/907、06037135116（各19.664 h）。这些是模型proxy空间归属，不是事件观测。每事件动态拓扑与逐站加权source-loss分别在`Offline_Mapping_Gate/*DYNAMIC_TOPOLOGY.parquet`和`*SOURCE_CONTRIBUTIONS.parquet`。

### 社区与空间输出

Stage 6保存了九条系统曲线、对应tract事件均值、各策略tract KPI、全域GeoJSON及统一色标的无约束/Hospital-first/direct对比地图。Stage 7原特征工程和K-means/PCA实际运行；因24 tract缺少既有SVI四主题，2291 tract进入五类聚类。此3样本中所有tract的初始source-gated supply为0，`Init_Supply`在Stage 7标准化后是零方差列，未贡献区分；已在`REVISION_CONSTANT_FEATURES.csv`标记。不要用此次聚类宣称稳定community typology。

## 原入口阶段调用关系

|阶段|修订试运行调用|保留的July实现|
|---|---|---|
|Stage 0|原`run_stage_0`读取utility-compatible 92站W|通过显式legacy选项读取原July W|
|Stage 1|原`run_stage_1`分支调用`run_stage_1_revision`；仍调用原`sample_damage_states`及`damage_to_functionality_and_repair`，每套保存一次DS/duration；planning与evaluation由独立SeedSequence stream生成|原chunk/mean Stage 1主体仍在函数内|
|Stage 2|原`run_stage_2`、同一retained 92/318图及原空间/中央性输出|不变|
|Stage 3|原`run_stage_3`分支调用`run_stage_3_revision`；每evaluation DS>0 station同时开始、在保存duration的completion事件恢复功能，原14-source gate随后作用；均值轨迹按事件right-continuous重采样|原CDF/代表时钟主体可由legacy flag运行|
|Stage 4|原`run_stage_4`分支调用`run_stage_4_revision`；`order_substations`给七条完整优先序列，`simulate_paired_realization_strategies`对每个实现按DS>0过滤并用实际duration、C57和保留有向道路安排crew|原`select_repair_tasks`/mean-duration主体保留|
|Stage 5|原`run_stage_5`分支调用`run_stage_5_revision`；只用独立planning物理样本搜索，`evaluate_direct_population_burden`真实经过completion、source gate、tract burden；best-so-far比较所有确定性incumbents，冻结一条候选后用于evaluation|原三权重GA及其Stage 5主体保留|
|Stage 6/7|Stage 6事件积分绘曲线与空间输出；Stage 7原社区特征、聚类/空间表|原Stage 6/7功能保留|
|离线|原pipeline最后调用`evaluate_mapping_gate_archive.main`读取一次性保存的f和identity，对28个evaluation views计算paired映射/gate差异|无重新抽样或调度|

试运行在输出目录隔离。两次可恢复接线错误均保留日志：第一次`ATTEMPT_01_FAILURE.log`（输出目录及共用crew-origin查值）；第二次`ATTEMPT_02_STAGE7_CONSTANT_FEATURE.log`（零方差初始供给）。修复后复用相同`physical_inputs_2pc50.npz`；没有为避免不利结果而调换DS、工时或重新抽物理样本。修订路径从保留的道路CSV直读、要求完整有限非负有向OD；不调用原Haversine/24h fallback。

保存的任务事件CSV中，`previous_task_id`曾在恢复读取时被pandas推断为浮点格式；已将24份排程事件档案的该字段规范为原六位station ID，未重新执行排程。随后逐项检查27份站点状态档案、24份排程事件档案和824段task→task行程：DS及工时与冻结物理向量一致，完成时刻等于到达时刻加工时，前序任务与crew释放链一致，站点`f/F/C/e`及损失守恒也一致。此步骤仅规范保存字段，不改变科学轨迹。

## July配置与正式运行尚需冻结的事项

|项目|七月配置事实|本次试运行|正式科学实验仍须决定|
|---|---|---|---|
|情景|Northridge、SanFernando、LongBeach、2pc50|仅2pc50|历史情景及主情景各自承担什么分析；原代码情景没有删除|
|物理样本|`N_MC=1000`，Stage 1没有GA planning/evaluation分离|2 planning + 3 evaluation；5独立physical样本|各情景evaluation N、独立planning N、固定seed与合理精度；不能把七月1000或后期310站32直接当已获准值|
|GA预算|100个体×100代、交叉0.8、变异0.2，原三套设计权重|direct burden，两seed、8个体×3代，均未超越incumbent|direct目标采用的正式population/generations/seeds/停止规则与可承受的预算；不凭本试运行选参数|
|策略|七条规则+原三设计权重GA|七条规则+一条direct-community诊断候选|最终解释性策略集合及incumbent角色；不能把本次未改进搜索称优化收益|
|资源与时间|C57基准；480 h、旧密集0.05 h连续clock|C57；480 h horizon、精确completion events|资源情景及是否需敏感性；固定事件horizon在所有策略完成之后的条件|
|mapping/gate|原July、14source、0.5 threshold|生产utility .03/G1、离线M0/M1/cutoff/M3/G0/threshold|正式矩阵每个物理样本一次，所有评价共享相同f；不重选策略|

上述是**待定实验设计**，不是建议继续复用3样本。下一步正式计算之前，至少要冻结planning/evaluation数量及GA预算；独立样本必须维持分离。原三条研究主线、92站和既定方法修正已经落实于入口，不需重建。

## 文件

- `Stage 1 Output_expanded/physical_inputs_2pc50.npz`与`PHYSICAL_SAMPLE_MANIFEST.csv`：完整5套DS/正工时、split与哈希。
- `Event_Archives/`与`SAVED_EVENT_INDEX.csv`：27个evaluation轨迹的92站逐事件f/F/C/e、三类loss、任务事件，以及相同physical/context哈希。
- `Stage 6 Output_expanded/`：九条恢复曲线、系统指标、空间GeoJSON/PNG。
- `Stage 7 Output_expanded/`：原社区聚类表、空间/特征与零方差说明。
- `Offline_Mapping_Gate/`：756条全域/原生评价summary、324条共同320-tract summary、逐tract负担与分类、配对效应、静态/动态拓扑及source-loss贡献。
- `TRIAL_RESULTS/`：紧凑的mapping配对差、群体/系统描述、损失分解、tract空间位移图与表。

整个试运行留在revision worktree；July archive与所有输入数据未修改。历史投稿结果不能被这次试运行替换。

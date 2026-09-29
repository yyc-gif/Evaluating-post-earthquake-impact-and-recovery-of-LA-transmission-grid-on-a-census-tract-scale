# Mapping与source-gate方法修改及最终评价准备

本轮已采用utility-compatible production mapping、实现逐事件损失分解、准备离线mapping×gate评价，并完成静态冗余与局部容量分析。固定92站、318边、2315 tract、14 Core sources；生产threshold仍为0.5。没有执行新的damage/recovery realization、MC、GA或最终实验。投稿archive未动。

**当前能确定的是方法变化及外部候选一致性改善；当前不能给出的是最终策略的社区负担变化和损失比例。** 本分支最终hazard、策略、资源矩阵、样本量及planning/evaluation split仍未冻结，也没有覆盖最终策略的可复用92站事件档案。不能把旧310站结果或合成测试当作这些答案。

## 一、十二个问题的直接答案

|问题|本轮结果与边界|
|---|---|
|1. revised mapping改了什么？|只改变eligible candidates：strict SCE仅SCE-compatible，strict LADWP仅LADWP-compatible，mixed/ambiguous维持general。centroid、nearest eligible access、原图最短路、总距离、1/d²、归一化、0.03截断及再归一化不变。ExpandedConfig默认改为JULY_UTILITY_CONSTRAINED_92；原文件保留为JULY_BASELINE_92。|
|2. original/revised对最终结果改变多少？|最终社区数值尚未运行，不能推断。外部337-tract benchmark any-match从320到329，top-1从296到302，top-3从317到324。评价代码会在同一站点轨迹上给出paired差异。|
|3. cutoff影响多少？|在411条可表示SCE候选关系中，July 3%截断删除56条、1%删除19条；utility版本分别删除41、12条。LAX–RS-N截断前1.198181984%，3%后为0，1%后再归一化为1.325728669%。社区结果影响待同一事件轨迹离线计算；不能从关系数量推出负担大小。|
|4. SCE candidate-supported结果一致吗？|已构造337行；320行正质量、17行全零并记unresolved。严格使用已截断July权重筛选、再归一化，没有补权重。是否一致尚待物理轨迹；同时输出337原生域及M0/M1/M3共同320-tract域，防止分母混淆。|
|5. damage/threshold/source-path各占多少？|实现L_self=1-f、L_threshold=f(1-F)、L_source=fF(1-C)，与1-e逐格守恒；经W传播后左矩形事件积分仍守恒。真实份额未计算。三类不能混称network disconnection；T50/T80不作加法分解。|
|6. gate对哪些tract/strategy最重要？|已实现每个mapping/gate的逐tract负担、组负担、配对策略/假设差异与source-loss贡献表；实际排序和人口尚待最终轨迹，静态图不能代替这一结论。|
|7. 是否由少数single-path站主导？|全功能图中8个非source站依赖单路径/单上游。COLORADO依赖RS-K得到保留。是否主导累计损失尚未证实；已实现动态冗余与population×mapping加权source-loss积分用于检验。|
|8. 14-source是否稳健？|14项身份证据已逐项分级；混合发电站址、receiving station、import interface与模型source，不能解释成14个已验证发电注入bus。证据层级不足以构造非任意confirmed subset，因此没有按文档多少删source。baseline14保留，现实注入/运行可用性稳健性仍未解决。|
|9. 有connected但capacity紧张的证据吗？|有局部planning context：OLINDA 66/12，2026需求28.45、同口径限额26.09，比值1.090456；provider loading109.04%、margin−2.36。不是震后过载或当前实测，原生量纲未独立确认时不标MW。|
|10. 哪些physics concern已处理？|候选关系、门槛与路径损失分解、拓扑脆弱性、source身份及局部负荷/容量背景有实质处理。全网balance、line flow、容量约束dispatch/load shedding、voltage仍未验证，需要真实DC/AC case，不能用当前分析冒充。|
|11. 需要修改92图吗？|本轮没有直接证据要求具体边修改。RS-K–COLORADO可追溯CEC66kV线路及July连接处理；SCE system归属不是接线图，不能据此删除或改接。拓扑单路径也不是现实唯一供电验证。|
|12. production与sensitivity采用什么？|production=M1 utility .03 + G1原14source/.5 gate。保留July reference、无截断/1%截断、G0、threshold .05/.75、337 SCE subset。没有把两路径要求、容量值或新source set放进production。|

## 二、可复查的定量证据

### 外部候选一致性
来自新版冻结SCE evidence，独立于旧342-tract benchmark，数据版本变化不是算法改善。

|mapping|any-match|top-1|top-3|
|---|---:|---:|---:|
|July baseline|320/337 (94.96%)|296/337 (87.83%)|317/337 (94.07%)|
|Utility-compatible|329/337 (97.63%)|302/337 (89.61%)|324/337 (96.14%)|
|净变化|+9; +2.67 percentage points|+6; +1.78 pp|+7; +2.08 pp|

这是817 strict-SCE tract中337个拥有92站可表示direct candidate的**条件性一致性**。其余480个coverage limitation保留。不是客户feeder assignment、真实service share或817整体accuracy。再生成mapping与已保存utility版本最大绝对差2.22e-16；baseline也通过1e-12比较。证据见SCE_BENCHMARK_REPRODUCED.csv、MAPPING_METHOD.json、CUTOFF_RELATION_EFFECTS.csv。

M3完全遵守W_July(.03)筛选定义，因此17行没有正质量。没有偷偷改为截断前权重；若以后另定义pre-cutoff evidence subset，应明确是另一个预声明情景，本轮未做。

### 拓扑证据
全功能状态92站均可到达14个Core source；这不等于路径独立。8个单路径站ID：
306365、306694(COLORADO)、301214、304040、305885、303303、305780、308991。
JULY92_TOPOLOGICAL_REDUNDANCY.csv保存reachable source数、edge/node-disjoint paths、对应min-cut、bridge/articulation依赖及local-source身份。对local active source，不能把“自己就是source”解释为一条脆弱上游路径；其source-cut标NA并单列remote路径。动态指标只在相应functional subgraph上计算。

SOURCE_NODE_EVIDENCE_CROSSWALK.csv与SOURCE_SET_DECISION.json记录14个source。Rinaldi/Sylmar的import证据、Haynes等站址证据、RS-Q receiving证据支持各自身份层级，不足以确认每个July bus的可用注入。没有伪造二元confirmed/unconfirmed敏感性。

### 局部容量背景
LOCAL_GNA_CAPACITY_SCREEN.csv含33个可匹配July名称、44个电压层级facility。2026中34行通过有限筛查；7行有缺失/隐去值；COLORADO、GANESHA、REPETTO另3行的需求/限额比与provider百分比相差超过本轮0.05 percentage-point核对容限而未采用。这可能涉及舍入或口径，不能据此认定原数据错误。OLINDA为通过筛查者中唯一ratio>1。

HISTORICAL_LOAD_CONTEXT.csv是33站名、100个电压/年度分组、14,400个有效月×小时负荷包络值；不能当作同一时刻的8760全网负荷。ICA_HOSTING_CONTEXT.csv是接入/hosting context，不是震后available MW。
LADWP_LOCAL_RATINGS_CONTEXT.csv分别记录RS-Q Rack B既有160 MVA、Rack D拟建160 MVA，以及Adelanto–Rinaldi原1593 A和拟议1680 A continuous/1965 A emergency。既有/拟建、A/MVA、facility/line不同口径保持分离；未将任何值写入92图。

## 三、实现与解释

- r1_mapping.py负责两套原公式映射及截断，C257H_Project_Main_expanded.py仅切换mapping默认与相应未截断sensitivity输入。
- r1_source_gate.py实现逐事件f/F/C/e与三类loss，callback可交给revised paired scheduler；save_gate_trace保存事件数组与identity。
- r1_mapping_gate_robustness.py及evaluate_mapping_gate_archive.py只消费已有raw event states，不调用damage、repair draw、scheduler或GA。原始trajectory不因mapping/gate评价改变。
- r1_topology_robustness.py及source/capacity prepare脚本只做静态结构/证据分析。
- Missing站不被当0；unknown站不进入已知functional子图，传播结果是在这一明确可识别子图下的条件性结果。已知质量与未知质量分开；fully unresolved burden和方向概率保持NA。
- 人口加权tract normalized burden的分母为可识别tract完整人口；availability及其累计deficit分母为ΣPopulation×ResolvedMass。两者分别保存。Hospital burden是有医院tract的算术平均normalized burden，不是医院运营恢复。
- winner/loser采用±1 h实用阈值；逐次分类人口的平均与32次等样本平均效应分类是不同统计。本实现不假定最终N=32。方向概率按有效paired realization计算，不将tract作为独立earthquake。
- G0=e=f仅表示无threshold/source限制的乐观availability bound。G2=.05允许July DS2=.09、仍阻断DS3=.04及DS4=.03；G3=.75还阻断DS1=.5直至恢复。阈值是残余功能层级的设计对照，不是电网运营校准值。每种threshold重新判functional subgraph，连通规则不变。

**执行中发现并修正的相关后处理问题：** Phase2原积分默认梯形适合连续曲线，不能用于completion-step轨迹。revised path现纳入所有completion events并采用previous/左矩形精确积分；legacy linear默认保留。direct population evaluator同步使用这一积分，没有更改GA搜索参数或启动搜索。旧synthetic测试horizon13早于completion15，改为15；新path对截断horizon fail-fast。此修正不会自动改写历史结果，也没有为此重跑science。

## 四、最终实验矩阵：复用一次物理运行，增加离线评价

物理矩阵尚未冻结：hazard列表、N、最终sequence、crew regimes、planning/evaluation split必须沿最终研究设计决定。本轮没有从先前D302的32×4授权推导July92最终运行授权。

每个未来已冻结realization×strategy×resource×hazard只生成一次DS、duration、schedule和raw trajectory。保存：
1. 完整92站ID、所有completion event times与共同horizon约定、f；
2. baseline f/F/C/e及loss数组、task events；
3. realization/strategy ID、ordered DS+duration的canonical SHA256；graph/source/travel/crew/horizon约定的frozen-context SHA256。离线CLI缺这些配对identity即拒绝跨策略比较，不猜配对。

**精确离线矩阵**：7 mappings ×4 gates =28 views/每条站点轨迹。
- Mapping：M0 .03、M1 .03、M0 no-cutoff、M0 .01、M1 no-cutoff、M1 .01、M3 SCE-supported337。
- Gate：G0 ungated、G1 .5、G2 .05、G3 .75，均同原14 sources。
- 另12个共同320-tract summaries：M0 .03/M1 .03/M3 ×4 gates，不是新物理运行。
- baseline动态拓扑及各gate的station source-loss contribution；不增加两路径production gate，不增加任意confirmed-source case。
- 输出population T50/T80、两种人口负担、hospital burden、Q1–Q4、signed/absolute gap、Gini、逐tract影响及分类人口、三类loss积分/份额、paired策略与假设效应。T80未达到为NA。
- 不重新优化任何策略。CLI：`python evaluate_mapping_gate_archive.py --index SAVED_EVENT_INDEX.csv --output NEW_OUTPUT_DIRECTORY --reference-strategy Hospital-first`；reference名称应与最终冻结策略一致。

因此新增physical realizations=0；最终physical运行数仍为原冻结矩阵中的N×策略×资源×hazard，现阶段不能给出凭空确定的总数。

## 五、Reviewer physics逐项回应

|关注点|本轮实质处理|仍不能声称|
|---|---|---|
|Power balance|无伪造balance；source-path与self/threshold区分|全网发电/负荷平衡已满足|
|Transmission capacity|同设施、同口径planning screen|92抽象边具有有效热限|
|Line loading|不将segment capacity相加，不填X|已计算真实线路潮流|
|Generation availability|14source身份crosswalk、明确模型供给角色|逐bus可用发电量/调度已验证|
|Voltage constraints|ICA voltage仅背景|满足R/X/Q/tap/shunt/电压约束|
|Load shedding|保留proxy语义|模拟了constrained dispatch或真实负荷削减|
|DC/AC benchmark|预留真实bus/branch case独立验证|将真实case压缩成92图即可获得物理验证|

RS-K–COLORADO和LAX–RS-N支持具体几何/设施联系的可追溯性与cutoff压力检验；不支持全网接线、客户依赖或真实停电预测。没有新的直接证据要求修改topology。production保留M1/G1，同时报告上述有限敏感性。

## 六、验证与提交

23项针对性测试通过（mapping再生成、loss守恒、gate合成断路、缺失、事件积分、配对汇总、档案identity拒绝、拓扑路径及容量口径）。没有运行GA搜索或最终MC。
五个主题独立提交：
- 4139893 mapping
- 9f052df loss decomposition
- 5219e63 offline robustness
- 09f8173 source/topology
- a20cf9d capacity screening

后续收尾提交仅补配对档案身份验证、分类人口/方向概率汇总、合成测试及本报告；不增加科学情景。
archive HEAD仍为182686868cffe962739804f6bc0ccecaed73d601。原先未tracked外部资料/溯源目录保留，未删除或混入模型输入。报告不把“代码准备完毕”写成“最终科学结果已完成”。


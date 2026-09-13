# PROVENANCE_DECISION — IJDRR-D-26-02276

**决定：停止继续追溯；保持恢复模拟 STOP，转入可复现网络的准备。** 当前更严重的 blocker 是选站：一个不以92为目标的规则得到 **310站，与旧92重合83，新增227、排除9**。原图、dependency与排程不能直接沿用。修复工时可保留为明确的情景假设，但已不能再称为实证／公用事业推荐工时。

| Blocker | 来源判定 | 本轮决策类别 | 实际含义 |
|---|---|---|---|
| 1/6/12/36 h | **not found：经验依据未找到；代码出现位置与行动意图部分恢复** | **CLOSED AS EXPLICIT ASSUMPTION**，仅限下述假设驱动的 comparative study | 关闭的是模型定义与处置选择，不是经验校准；不得继续使用 calibrated、empirical、utility-recommended，或把敏感度设计区间写成真实工时范围 |
| 486→92 | **not recovered：保留的记录没有选择规则／例外理由** | **REQUIRES MODEL REBUILD** | 采用明确的R1候选规则替代；310站只是本轮名单，不是已建成的新网络，更不是经过验证的完整LA供电系统 |

本轮只读取来源、检查数据字段和比较名单；**没有运行恢复模型、32×4重分析、29 crews、MC、GA或topology regeneration**。父提交 `129914d367df037d00d96f1ccb83d052f81a7cb6`；新分支 `revision/ijdrr-provenance-decision`。两项交付是本报告和 [STATION_SELECTION_COMPARISON.csv](STATION_SELECTION_COMPARISON.csv)。此前数据与报告保持冻结。

## 1. 1/6/12/36 h：第一次出现与来源的区别

**The provenance of the 1/6/12/36 h parameters is not recoverable from the retained project record.**

这里的 provenance 指数值的科学／操作依据；不表示不知道数值何时进入Git。

| 时间／提交 | 文件与行号 | 实际发现 |
|---|---|---|
| `4b349c9^`，normal引入前 | `code/C257H_Project_Main.py` L265–270 | 旧 lognormal 参数 [4,12,24,72] h、log-SD=.5，旁注却是约1/3/7/30 days；不是可靠替代标定 |
| **2026-02-04，4b349c9，updatefeb4** | [历史源码 L286–305](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/blob/4b349c9/code/C257H_Project_Main.py#L286) | 首次引入 `REPAIR_PARAM_NORMAL_HR`，但为 **(4,2)/(6,3)/(8,4)/(12,6) h**，不是当前四组。提交作者标识为 yutongli26；这只证明谁提交代码，不证明谁提出数值或取得专家数据 |
| 同一提交 | L288–304 | DS1=travel2+safety inspection1.5+reset.5；DS2=travel/inspection3.5+isolate2.5；DS3=inspection2+isolation2+switching4；DS4=clear site2+jumpers8+energize2 |
| **2026-02-05，3313def** | [Read-Me.md，“Assumptions / limitations”](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/blob/3313def/Read-Me.md) | 已明确把 repair/recovery parameterization 定位为 scenario-based comparative，而非 calibrated operational forecast；这是原建模定位的证据，不是数值证据 |
| **2026-05-20，df1fc85，Initial full project upload** | [历史源码 L278–304](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/blob/df1fc85/C257H_Project_Main.py#L278) | 第一次保留了当前 **(1,.5)/(6,3)/(12,4)/(36,12) h**；提交作者标识yyc-gif。属于批量上传，没有保存4/6/8/12→1/6/12/36的参数决策理由 |
| 当前冻结源 | [L294](../../../C257H_Project_Main.py#L294) | 继续使用上述小时参数。DS2的3.5 h注释从2月版本保留；DS3/DS4写“recommended”，没有可识别推荐来源 |

2月注释的“substation maintenance logs”“standard utility operating protocol for N−1”“MV/HV bypass cabling guidance”都没有机构、文件号、作者或页码。DS3曾写 **“Validation target: LADWP Northridge notes (~50% restored in ~7.5 h)”**：可判定历史代码把系统恢复里程碑作为目标；不能由此断定实际完成过拟合，也不能再不加说明地把Northridge比较称为独立验证。

限定追溯已到终点：检查上述提交与前后README／脚本、首次92站上传同时保留的crew workbook、Storyboard0204／0205／0401、课程报告、合作者Comments／Responses及既有文献提取。crew workbook的Summary／Denominators／YardAllocation／QA讨论工班数量，不提供这四组工时；没有找到同期参数justification表、可核的maintenance log或protocol。没有把旧合作者回复误作本轮review response。**不会继续无界搜索或把缺失记录推定为存在。**

### 行动范围与 double-counting risk

恢复的意图是 **短期切换／临时恢复行动与部分响应活动的混合**，不是full permanent repair，也不是纯粹on-site work。当前DS1注释移除了行车，DS2仍把travel/inspection混在一起，DS3/DS4改为临时旁路／移动设备。四个DS并没有统一的“到站后工作”边界。

历史代码同一提交的 `end_time=arrival_time+repair_duration` 在L2235，当前参数首次上传时在L3264；道路行车已包含于arrival。因此，**若按历史注释解释duration，就有重复计算travel的语义风险**：2月DS1明确包含2 h travel，DS2的3.5 h也含travel字样。没有证据确定当前DS2中行车占多少，不能机械扣3.5 h；本轮没有修改工时或声称量化了重复计时造成的结果偏差。

HAZUS的1/3/7/30 days为设施功能恢复函数，不直接对应一支工班占用时间；不做×24或天数替换。外部方法依据可支持“区分检查、组件维修与旅行”，不能给当前四个数背书：Xu等的任务时间由LADWP人员提供三角分布的min/mode/max，并将具体表指向Çağnan(2005)学位论文Appendix B；现有项目未保留该附录。[Xu等，2007，pp.269–270](https://doi.org/10.1002/eqe.623)。本地原文提取 `1fa17b2f_######Optimizing_scheduling_of_post_earthquake.txt` L241–243、L267–269；未将component级时间直接移植成整站DS级参数。

## 2. 修复参数的最小替代定义：可以研究，但必须改变主张

采用定义 **scenario-based on-site restoration action durations**：

- 起点：工班已到站；全局damage state在调度开始时已知。现场安全确认可以包含在工作中，但不能再包含全系统的先期damage-assessment阶段。
- 终点：本次临时恢复行动完成，工班释放，模型raw functionality恢复到1；source gate仍单独判断。沿用已明确的event语义，不另加commissioning delay。
- 排除：base-to-site／inter-site travel、出勤动员、等待外部材料／移动变压器交货、永久设备重建。若将来要包含其中某项，应另定义，不能悄悄塞回work duration。
- 条件：允许的切换／隔离／临时旁路在该情景下可实施，所需材料与临时设备可用。这不是说每一个HAZUS DS4设施都能36 h恢复，也不是容量充分性的证明。
- 工时是一个固定规格工班的**连续elapsed work time**，不是person-hours。是否持续作业、同一工班规模与资格必须固定；不增加本轮模型模块。

1/6/12/36及其σ只可作为一组**未校准的参考情景参数**保留。positive-conditioned normal中的这些数是underlying location参数，不能未经转换叫作条件分布自身均值。本轮不再比较A/B，也不根据旧策略胜负选择分布。

**可复现的最小敏感度设计（仅设计，未运行）**：在参考向量之上，固定五个倍率向量
`(.5,.5,.5,.5), (1,1,1,1), (2,2,2,2), (1,1,.5,.5), (1,1,2,2)`。
同一倍率作用于相应DS的location及scale，保持其相对离散程度；既检验统一时间尺度，也检验重损任务相对于轻损任务的持续时间。按同一冻结损伤／uniform进行配对，不为恢复旧结果调整倍率；观察策略绝对差与community effect，而非只看rank。

**0.5–2是显式实验设计范围，不是文献证实的utility工时上下界，不是置信区间。** 该方案能支持的贡献是“在已声明工作量情景中，修复决策如何改变模型服务结果及适用条件”。若要保留“现实LA在这些小时内恢复／某政策现实收益为X小时”，本轮证据仍不够；单纯跑完五个情景也不能获得这种资格。CLOSED AS EXPLICIT ASSUMPTION仅对前一种研究定位成立。

若要把区间提升为操作上可信的范围，最小expert elicitation应逐项回答，而不是笼统请专家“确认参数”：

1. 每个DS到底对应哪些可执行action；严重设备损坏何时能用临时旁路，何时必须等待替换？是否可合理恢复到模型f=1？
2. 对固定人数／工种的工班，**到站至action完成**的min/mode/max（或P10/P50/P90）分别是多少？这些是elapsed hours还是person-hours？
3. 安全确认、隔离、接线、操作许可、复电检查各含在哪里？明确剔除road travel；DS2原3.5 h必须拆清，不能口头整体认可。
4. 24 h连续工作还是有班次／休息？材料和移动设备是否已在场？若没有，本研究的条件情景是否仍有实际对应？
5. 给出的范围来自哪些工单／事件、何种电压和设备、多少案例及何年；哪些是经验判断？固定定义后再定参数，不向专家展示哪组参数让Hospital-first胜出。

**回答“是否使scheduling失去意义”**：不会。共同information set、明确工作量和工班约束下的comparative scheduling有数学与方法意义；失去的是把未校准小时值包装成现实LA修复预测的资格。若不接受这种主张收缩，就应把本项视为尚无经验依据，不能靠措辞继续投稿。

## 3. 486→92：恢复了哪些历史，哪些确实丢失

- 当前92-ID CSV最早进入保留Git的是 `df1fc85` 的 `Data/working_area_substations_with_fragility.csv`；同提交有486-ID `*_original.csv`、source list和图输出。后续小写 `data/` 路径的上传不是更早的筛选记录；没有保存逐步删站脚本或manual exception依据。
- `ARCGIS Substations CA.qgz` 的saveDateTime为2026-04-11，已有working／original图层路径；这只能证明图层被引用，不能证明当时文件内正好是当前92个ID。另一个Open basin项目保存于2026-01-23。
- 两个QGIS项目未保存可闭合的subset string、selected feature ID集合、stored selection expression或metadata说明；`selectionSymbol`只是选择项显示样式，不是选择记录。内嵌style数据库未找到筛选逻辑。
- 本机 `C:/Users/yinch/AppData/Roaming/QGIS/QGIS3/profiles/default/user-history.db`，只读查询 `history` 表：记录1是2026-01-23的 `native:mergevectorlayers`；记录2/3是 `MAX_VOLT_N/MIN_VOLT_N` 的field calculator。**没有486→92的filter/export记录。**
- 现存 `extract_workinglist_substations_assign_fragility.py` L15–103列出city/alias；L226–241做county/city过滤。重算得到302个ID，只有73个在旧92；它不是92站生成规则。没有找到删站、合并、连通性筛除或保留source的历史manual list能够补齐差额。

**结论：the historical 486→92 selection rule was not recovered; its selection provenance is lost in the retained record.** 不能把现存地理脚本、QGIS图层名称和已生成的92/318拼成一条不存在的证据链。本轮不再验证318条边能否重现。

### 19个city-filter例外：解释现存差异，不冒充历史选择理由

这19站的CITY都不在现存city名单中；大多数实际坐标却在已发表研究区tract集合内。由此可解释**为什么当前city-label过滤复现不了**，不能推断作者当初一定执行过什么manual exception。

| 当前字段CITY | 旧92中的例外站ID／名称 | R1处置 |
|---|---|---|
| AVOCADO HEIGHTS | 307564 JOSE | 保留 |
| CERRITOS | 302187 DEL AMO | 保留 |
| COMMERCE | 306060 LAGUNA BELL | 保留 |
| EAST LOS ANGELES | 307785 WABASH | 保留 |
| INDUSTRY | 301517 NOGALES、300408 PUENTE、300105 WALNUT | 保留 |
| IRWINDALE | 305984 RIO HONDO | 保留，已有import proxy |
| LA CA?ADA FLINTRIDGE | 304040 ARROYO、300829 GOULD | 保留；后一站为import proxy。问号是保存标签，未据此创造alias例外 |
| LA MIRADA | 306369 LA MIRADA | 排除：STATUS缺值 |
| MONTEREY PARK | 301541 MESA、308907 NEWMARK、302798 REPETTO | 保留；MESA为import proxy |
| NORWALK | 300232 CENTER | 保留 |
| PASADENA | 303371 GOODRICH | 保留 |
| POMONA | 300558 GANESHA | 保留 |
| ROSEMEAD | 300648 ROSEMEAD | 保留 |
| ROWLAND HEIGHTS | 306279 OLINDA | 排除：点不在固定研究区多边形内，且不是已有source |

即19站中18站在研究区内，R1保留17站；另2站排除各有明确新规则原因。CITY是字段标签，不能拿它替代真实geometry，也不能称它是utility服务边界。

## 4. R1：独立于策略结果的可复现替代选站规则

本轮先声明study-area／type／status／voltage／source处理，再计算名单，没有读取或重新计算paired outcomes。计算中发现两项输入问题，明确处理而非调阈值：

1. 候选表14行原始 `MAX_VOLT=-999999`，派生 `MAX_VOLT_N/voltage_for_fragility=+999999`。其中9个是SUBSTATION、5个RISER。**这是确认的候选字段转换不一致**，原始缺值被错误表示成极高电压；不知道是哪次具体编辑造成，不能仅凭现存QGIS表达式归因。旧92不包含这14行，不能宣布旧pilot已经因此算错。R1直接读取原始有效MAX_VOLT，不使用派生999999。[HIFLD图层的−999999缺值标记](https://oceandata.rad.rutgers.edu/arcgis/rest/services/RenewableEnergy/HIFLD_Electric_SubstationsTransmissionLines/MapServer/0)。
2. 上游完整 `CA_substations_MERGED.csv` 的REDONDO 1（308844）在研究区内、230 kV、SUBSTATION／IN SERVICE，却不在486表中。**最终R1从4260条上游inventory出发**，避免再继承一个不明的486预筛选；同一规则在486内为309站，完整inventory为310站。额外1站不是为了接近92或保住source／策略结果而加入。

| 顺序 | 明确规则 |
|---|---|
| 0：数据与ID | 固定上游4260条snapshot；按ID唯一性校验，重复若属性冲突就报错，不按结果挑行；本次4260个ID均唯一。不得宣称该公共inventory完整覆盖所有utility设施 |
| 1：研究区 | 固定 `Data/Tracts_Within_Expanded_Area.csv` 中2315个GEOID的WKT多边形并集；使用 `covers` 包含边界点。不重画study area、不加buffer、不取convex hull、不按人口结果裁剪。2291是有效SVI子集，不用于改地理范围 |
| 2：设施类型 | TYPE精确为SUBSTATION才作可修复设施。TAP/RISER/DEAD END不套整站fragility；将来线路几何中的junction仍应保留，不能因不是repair task就删掉线路连通 |
| 3：运行状态 | STATUS精确为IN SERVICE。缺值单列excluded，不冒称已退役；未来有外部证据时可在新版本更正 |
| 4：电压 | 原始MAX_VOLT为有效正数且≥34.5 kV；−999999等缺值不转换为正数。34.5是现有fragility适用下界，不是为控制节点数新调的阈值；保留MAX_INFER标志 |
| 5：地理及source | 合格点在固定研究区内即纳入，不按Owner排除、不强迫属于最大连通分量。已有source CSV中6 import+8 generation proxies若在区外但同样满足资格，可作为显式boundary exception保留；24 transit hubs无此特权，不按名称新增source |
| 6：本次结果 | 14个source本次全部在区内且合格，因此 **实际没有用到source地理例外**。15个重点站也全部按普通规则保留，无人工保护例外 |

HIFLD资料对低于69 kV设施的coverage有明确不完整说明。因此“≥34.5 kV可用fragility”不代表“已收集全体34.5 kV以上LA电网”。[HIFLD metadata](https://www.arcgis.com/sharing/rest/content/items/5d1c27f29e1f48cb85b67de46236b032/info/metadata/metadata.xml?format=default&output=html)。source保留仅固定既有proxy假设，不证明实际可用发电／进口容量，也不意味着新增设施不可能涉及新的供电接口；重建时需检查这一点，不能按“GEN”站名自动升级。

### 名单结果：310 nodes候选，不是310 edges

| 集合比较 | 数量 |
|---|---:|
| 4260 inventory → TYPE=SUBSTATION | 3374 |
| 再要求IN SERVICE | 2775 |
| 再要求有效原始电压≥34.5／有效坐标 | 2548 |
| 再要求固定study area或合格source例外 | **310** |
| 同规则只用于486表 | 309 |
| 旧92 ∩ 新310 | **83** |
| old-only | **9** |
| new-only | **227** |
| key15保留 | **15/15** |
| 实际source保留 | **14/14** |

**old-only清单**：306369 LA MIRADA、308806 MOBILOIL、301636 SAN FERNANDO、306444 STANHILL、305780 THERMAS、306768 UNKNOWN306768、307832 UNKNOWN307832、301745 WINDSOR HILLS，均因STATUS=NOT AVAILABLE；306279 OLINDA因不在研究区且非source。不得将前8站改称“错误设施”或“已停运”。

**new-only全部227站**在CSV筛选 `set_comparison=new_only`；包含226个原486候选及1个REDONDO 1。举例有230 kV的VENICE(308325)、STATION S/VAN NUYS(304217)、STATION P/MARKET(306012)、TIDELANDS(304338)、OLIVE(306152)；不对这些站逐个编写电气角色百科。

CENTER、DEL AMO、VERNON、NOGALES、HOLLYWOOD等前轮关键15站保留，不表示其population dependency或路径影响会不变。SAN FERNANDO在更早确定性分析中曾有较大effective-B贡献，本次因状态缺值被排除；这需要将其列入资料澄清对象，而不是以“关键所以必须留”推翻统一规则。新增227站也会改变此前落到这些高影响站上的依赖权重，影响方向不能在重建前推断。

CSV有487行：保留486候选，以及唯一新增的研究区设施REDONDO 1；覆盖全部旧92、新310、当前city-filter302和source集合。没有倾倒其余州域无关行。包含原始字段、候选派生电压、所有过滤标志、19站例外标志、source/key15标志、old/new类别及逐行处置原因。

## 5. 对论文与后续计算的决定

**selection是更严重的blocker。** 工时可以在同一模型结构下改为明确情景参数，结果按条件解释；选站改变了资产集合、路径、中间站阻挡、社区依赖及策略任务集合，不能仅用一句limitation或换一组W权重修好。

| 可以保留 | 必须重新计算／不能直接作为新版结果 |
|---|---|
| 原始公开inventory／几何／tract人口／SVI／hazard数据及其来源；通用event与共同information-set定义；同类策略目标定义 | 310站注册、线路分割／intermediate-station blocking、设施图及新edge count；不能把227站附加到旧318边后直接运行 |
| 旧92/318代码与全部输出作为冻结历史、诊断／假设发展记录；不删除不覆盖 | 新dependency W、station fragility/PGA对接、任务集合、旅行矩阵新增站点行列、population/hospital/结构优先分数及四策略可执行序列 |
| “makespan与population-service是不同指标”“均值tract分类与realization恶化人口不同”等定义性结论 | 新版所有T80/AUC／makespan／community人数、差值、机制归因和策略比较图表；旧3.31 h方向仅是旧模型的已知结果，不能自动转移至310站 |
| 现有GA算法与fitness定义可复用，未来无需为了让GA赢而redesign | 旧92站GA permutation对310站不是有效完整策略；未来需重新构建相同目标下的可行GA优先序列，不能简单在队尾补新站。**本轮没有执行** |
| 旧资源充足时near tie可保留为旧模型内证据 | 114crew上界原先依赖最多92任务的条件；310站时该前提不成立，不能沿用“114crews一定practical tie”。不在本轮重新计算此界 |

旧结果不是被证明反转或错误，因此不销毁；若改用R1，它们应从新版主结果／LA政策证据中撤下，可保留为模型发展与敏感度背景。只有重建后才能判断旧population advantage和community heterogeneity是否仍然存在。不能因为15关键站都保留就提前宣布稳定。

### 是否解除STOP，以及下一次唯一值得运行什么

**不解除恢复模拟STOP。下一次唯一值得运行的是：R1的310站 topology＋dependency 构建与输入QA dry build，零damage／repair抽样，零排程优化。** 本轮只给出此建议，没有运行它。

该dry build只需回答：新站是否被有效注册、是否出现异常snap／跨电压合并、direct-link是否正确保留新增中间站、哪些component有source、W是否完整归一化且无静默丢tract、候选缺值与新增source-role问题是否被明确处理；产出可执行的新版输入快照和差异摘要。发现无法连通或角色未证实时，不通过删站、任意连边或新增source来凑出好看的网络。

后续恢复计算的最小准入条件：

- **32×4**：上述dry build合格；新任务／旅行矩阵／四条可行priority已齐全；采用第2节的明确on-site情景定义且正确排除travel；参数敏感度方案在看结果前冻结。若要求经验LA小时解释，需先取得相应work-duration范围／elicitation。对共同旧站按station ID匹配随机数，新增站另有可追溯流；不能把旧92维向量按新行号硬套。仍先32次、四策略，不扩MC。
- **29 crews**：新版32×4及最小参数检查支持可解释的population效应和社区异质性，且没有未处理的选站／source／事件问题，再单独检验资源稀缺是否放大绝对策略差。若新32次效果消失，先解释，不运行29来寻找旧结论。
- **broader MC**：只有新模型结构与作用范围已固定，且pilot表明剩下的是需要更精确估计的抽样误差，而非参数／selection不可识别，才按预先规定的效应精度决定是否加样本。当前没有这种准入结论。

## 6. 最少复核信息与来源位置

本地父目录P为：
`C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project`。
QGIS／inventory位于 `P/01_Source_Data/`；city脚本位于 `P/02_Preprocessing_Scripts/`；上述稿件／文献提取位于 `P/00_Project_Deliverables/Audit_IJDRR_20260912_01/text/`。

| 固定输入 | SHA256 |
|---|---|
| P/01_Source_Data/CA_substations_MERGED.csv | `9036e1dbf192e853ff2fa30c615086f7f95f208bf1e314413c6aac8900ac90eb` |
| 历史486 CSV，df1fc85的LFS实体 | `043588b79a7f26d4b643faa74cc4d0b059e3334b6ffc052d6eaf4350da0bff57` |
| Data/Tracts_Within_Expanded_Area.csv | `b81268b48d77758f9d23fac4335c06024059a711f3c1453be2d0b9ecd1aa3a9e` |
| Data/working_area_substations_with_fragility.csv | `d28565de3d549b6655f1d7ca263712078ded38a73cf4a6f8e00fe969c026ff00` |
| Data/source_nodes_core_expanded.csv | `892f5ec3e9a260db138c7fb2454dea09fcb75a8989ef13695aefca417b8c2955` |
| P/02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py | `883da1281c3ab6e88145ba5a838544b180fd3958e6383a866cdefc25615585ca` |

独立名单复核可直接用本CSV与已在Git的tract/source文件，无需读取任何MC结果。以下代码只核对geometry与R1布尔规则，**不运行模型**：

```python
from pathlib import Path
import numpy as np
import pandas as pd
import shapely

# From repository root; use a short checkout path on Windows.
root = Path.cwd()
folder = root / "Review_and_Revision/IJDRR-D-26-02276/04_Provenance_Decision_20260913"
c = pd.read_csv(folder / "STATION_SELECTION_COMPARISON.csv", dtype={"ID": str})
t = pd.read_csv(root / "Data/Tracts_Within_Expanded_Area.csv")
s = pd.read_csv(root / "Data/source_nodes_core_expanded.csv", dtype={"ID": str})
polygons = shapely.from_wkt(t.wkt_geom.to_numpy())
assert shapely.is_valid(polygons).all()
inside = shapely.covers(shapely.union_all(polygons),
                        shapely.points(c.LONGITUDE.to_numpy(), c.LATITUDE.to_numpy()))
sources = s.loc[s.source_type.isin(
    ["import_interface_proxy", "in_basin_generation_proxy"]), "ID"]
voltage = pd.to_numeric(c.MAX_VOLT, errors="coerce").replace(-999999, np.nan)
eligible = (c.TYPE.eq("SUBSTATION") & c.STATUS.eq("IN SERVICE")
            & voltage.ge(34.5) & np.isfinite(c.LONGITUDE) & np.isfinite(c.LATITUDE))
selected = eligible & (inside | c.ID.isin(sources))
assert np.array_equal(inside, c.inside_frozen_study_tract_union)
assert np.array_equal(selected, c.new_R1_selected)
assert (len(c), selected.sum(), (selected & c.old_selected_92).sum()) == (487, 310, 83)
assert (selected & c.key_15_station).sum() == 15
assert (selected & c.existing_source_proxy).sum() == 14
```

CSV中的 `city_mismatch_explanation` 解释的是当前标签筛选不匹配，不是历史manual exception依据；`selection_reason`是本轮R1处置。309→310只来自更完整的上游候选集，电压资格从错误派生值回到原始有效值；没有按与旧92的overlap调节任何阈值。所有复核仅涉及输入／名单，没有重新计算旧paired指标。

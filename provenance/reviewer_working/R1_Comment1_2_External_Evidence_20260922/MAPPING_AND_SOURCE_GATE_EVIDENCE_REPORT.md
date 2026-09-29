# 原92站模型：mapping与source gate外部证据联合分析

**两处关系的后续定向追溯已完成，见§9；最终实验的两项必需输出见§10。** LAX零权重已定位于3%截断；RS-K—COLORADO边已追溯到CEC原始两段线及七月连接处理，路径长度逐顶点复核一致。因此，原§4.3的“依赖不一致”应理解为尚未解决的供电系统／资产层级问题，不能升级为已确认的错误连边。本轮没有修改production代码或启动新的科学运行。

## 先回答五个问题

1. **有独立支持，也有具体不一致。** 在官方直接站名可被92站表示的337个strict-SCE tract中，原mapping至少对应一个官方候选的比例为94.96%。RS-J与北圣费尔南多谷、RS-Q与San Pedro／Port的具名联系，也与模型权重的广义空间位置相符。但这不是customer-level验证。LAX内部代表tract在两套mapping中都没有RS-N权重，未表示官方2019工程文件记载的主要供电关系；SCE COLORADO在图中只经LADWP RS-K接入，而新SCE回路记录将其列为La Cienega System。这两处不能用“总体match率高”掩盖。
2. **Utility constraint仍有小幅改善，集中在有限的边界／候选重新分配处。** 同一新增证据、同一337-tract分母上，any-match为320→329（94.96%→97.63%），top-1为296→302（87.83%→89.61%）；没有any-match由对变错的tract。新增9个any-match中，5个涉及Yukon，其余涉及Windsor Hills、Rosemead、El Nido、Lakewood。它没有补齐92站外的候选，也没有解决LAX或COLORADO问题。
3. **具名事件支持“站退出／隔离会影响地区”，没有验证完整source gate。** RS-J 2017火灾有清楚的隔离、部分复电、全部复电与永久维修时序。固定网络的RS-J单站退出没有使其他站失去source路径，其区域损失全部来自直接mapping权重。因此该案例可支持RS-J—地区联系和操作性停运机制，不能被当作已验证的网络级级联传播。巡视、消防隔离、切换转供、站内部分设备状态和分阶段复电，均不在本次二值静态退出诊断中。
4. **不支持直接替换production default，也不应只增加泛泛limitation。** 保留当前模型作为条件性proxy；但若要保留机场等局部供电归因或RS-K→COLORADO传播主张，必须定向核实这两处关系。现有材料不足以直接指定新边、实际service share或新的source集合。本轮未改mapping、图、source或代码。
5. **可进入R1 #1/#2回复的，是有分母的外部一致性比较、覆盖缺口、具名事件过程、直接／额外传播分解和明确的局部不一致。** 不能进入回复的强主张包括“真实feeder已验证”“全网gate已验证”“接通路径即满足负荷”“capacity map已成为92站热限”。规划容量与跨期事件目前是有限物理解释和筛查材料。

## 1. 固定对象与分析边界

本次只使用七月全区域92站、318条保留边、2,315个tract，两套已存在的mapping：

- JULY_BASELINE_92：原提交长表。
- JULY_UTILITY_CONSTRAINED_92：此前已完成的分析版本；仅改变eligible station集合，保持centroid、nearest access、同一图的最短路、IDW power=2、cutoff=0.03及归一化规则不变。
- source完全取自Data/source_nodes_core_expanded.csv的14个Core记录，未采用后来的310站或21-source情景；functional threshold=0.5。
- 全区域保留：817 strict SCE、848 strict LADWP、650 mixed/ambiguous。没有收缩研究域。
- 新证据来源为External_Validation_Data，2026-09-22 Pacific下载，SCE ICA表的provider extract date为2026-09-13。旧benchmark及其文件保持不变。
- 静态诊断调用当前保留production gate函数本身（从源码提取该函数及ID清理函数执行，没有import/运行整条pipeline）。只有全功能参照和六个单站退出条件；没有抽damage、生成维修时间、运行scheduler、recovery、MC或GA。

单站退出仅设目标站raw availability=0，其余91站=1，并从14个原source中保留当时可用者。它是模型条件诊断，不是对2017事故其他未知设备状态的估计，也不是事故重演。RS-N、RS-Q、RS-C、RS-K和Rinaldi的条件计算并不声称这些资料描述了对应实际停运事故。

本地branch仍为revision/reviewer-driven-core-rebuild-v2；投稿archive未操作。输入摘要和文件hash见ANALYSIS_INPUTS.json。新增文件只在本分析目录内。

## 2. SCE：先分清“92站覆盖”，再算“mapping对应”

### 2.1 新版外部候选的定义

使用实际下载的Distribution Circuits几何及sub_name、sys_name：

1. 将原tract与官方回路投影到EPSG:3310；回路在tract内具有正长度才纳入，不把单一边界触点当作关系。
2. 从sub_name去除明示的电压后缀，做大小写／标点空格标准化，与92站中SCE owner的唯一站名对应；不模糊匹配、不nearest补站、不引入310站。
3. 保留官方站点几何的同名距离检查，直接匹配站点的最大空间差为约0.532 km（Mesa）；并不据此宣称同名站的各电压bank就是同一资产。直接名称涉及32个92站；strict-SCE可比较集合中出现29个。
4. sys_name单独作为上层named-system关系，绝不与直接供电站名混成同一种“truth”。
5. 负荷联结使用原circuit name，保留年代和redaction。strict-SCE相交记录5,177条，其中5,165条具有历史负荷名称联结。这个联结加强数据链可追踪性，不给candidate赋予真实服务份额。

全部结果在SCE_STATION_EVIDENCE_CROSSWALK.csv、SCE_CIRCUIT_TRACT_EVIDENCE.parquet及SCE_TRACT_INVENTORY_COVERAGE.csv。外部候选始终是public candidate evidence，不是ground truth。

### 2.2 覆盖缺口

| 问题 | 本次结果 |
|---|---:|
| strict-SCE tract总数 | 817 |
| 有公开回路相交、具直接站名候选 | 817 |
| 至少一个直接候选可对应92站 | 337（41.25%） |
| 有外部候选但无直接候选被92站表示 | 480（58.75%） |
| 去重后的tract×直接站名候选关系 | 2,038 |
| 其中对应92站的关系 | 411（20.17%） |

最后两行是候选关系条数，不是人口比例、负荷份额或独立客户数。未表示的候选可能是更细分的distribution facility，也可能有保守名称匹配尚未解决的身份差异；不能统称为July节点漏选错误。但它们明确限制了92站可被直接证据验证的范围。

### 2.3 同一新版候选、同一337-tract分母上的mapping比较

| 指标 | Baseline | Utility-constrained |
|---|---:|---:|
| Any-candidate match | 320/337 = 94.96% | 329/337 = 97.63% |
| Top-1 | 296/337 = 87.83% | 302/337 = 89.61% |
| Top-3 | 317/337 = 94.07% | 324/337 = 96.14% |
| Mean precision-like overlap | 0.5232 | 0.5263 |
| Mean recall-like overlap | 0.8981 | 0.9318 |
| Mean candidate count | 2.6350 | 2.7478 |
| Mean maximum weight | 0.8567 | 0.8569 |
| Mean HHI | 0.7688 | 0.7684 |
| Mean effective candidate count | 1.4077 | 1.4104 |
| Mean top-1到最近represented official站距离 | 0.5115 km | 0.4656 km |
| Mean赋予represented official候选的总权重 | 0.7809 | 0.7979 |

Precision-like分母为mapped positive candidates；recall-like分母为represented official candidates。二者不衡量真实load share。浓度变化很小且并非所有方向均“更集中”；浓度本身也不是准确度指标。没有使用“统计显著改善”或等效性结论。

新增any-match的tract ID为06037602700、06037600303、06037601303、06037481606、06037604002、06037574400、06037600501、06037600602、06037601900。前后候选名单均可从逐tract表直接查到。部分改善来自去掉跨utility站后重分配已有SCE候选，并非新增官方候选进入算法。

Named-system单独的700-tract条件集合上，any-match为67.43%→77.43%，top-1为33.14%→34.14%。这不宜直接解释为剩余66%的mapping错误：system是上层关系，而原权重未必意在直接指定该层级。它主要用于追查源路径／层级一致性，尤其COLORADO案例。

### 2.4 与旧benchmark分开

旧benchmark有342个可比较tract；新版337个；共同316个，旧有新无26个，新有旧无21个。共同tract中301个represented candidate集合相同、15个改变。

旧证据是保留的已交叉对应candidate表；本次是新公开几何＋明确直接站名规则。两者既有数据版本差，也有保守crosswalk口径差，不能把分母变化称作算法进步。BENCHMARK_VERSION_COVERAGE_CHANGE.csv逐行保留原因可追踪的候选增删；SCE_MAPPING_BENCHMARK_SUMMARY.csv另列旧／新在相同316个tract上的指标。

真正的算法对照只比较**同一版本候选下的两列mapping**。上述小幅改善在共同tract中也存在，但这仍不证明真实服务份额。

![新版SCE覆盖与条件一致性](Fig1_SCE_candidate_consistency.png)

图1：灰色表示官方直接候选未被92站表示；不是把这些tract判成mapping错误。白色背景包括非strict-SCE区域。两面板用相同范围和候选版本。

## 3. LADWP：具体地理关系与边界

### 3.1 RS-N／LAX：存在可定位的联系缺口

保留的2019 LAX RS-X Environmental Assessment，PDF第29页（印刷1-5）明确：LAX主要由RS-N供给，DS-111提供secondary supply；Figure1-2（PDF第31页）给出机场、RS-N、DS-111及线路位置。该文同时明确当时RS-K不直接给机场供电。这里不能把2019描述无条件推到2026投运状态。

为使空间检查可复查，本次在图示机场内部选取一个**分析者地图阅读参考点**（-118.408, 33.9425），落入tract06037980028。它不是客户坐标、service polygon或全部机场负荷分配。该tract在两套mapping中完全相同：

| 92站 | 权重 |
|---|---:|
| UNKNOWN301100 | 0.709941 |
| STATION L (SCATTERGOOD) | 0.174001 |
| EL SEGUNDO | 0.064492 |
| SEPLUVEDA（保留原拼写） | 0.051566 |
| RS-N | **0** |

该tract为mixed/ambiguous，因此utility constraint未改变它。它在保留人口表中人口=0；机场供电联系失配可以被人口加权汇总掩盖。不能将UNKNOWN301100擅自解释成DS-111或RS-N的别名，也不能把Scattergood发电厂自动等同于同名inventory站。

结论是：当前proxy**不能完整表示这条有文件支持的机场供电关系**。不是一次真实RS-N事故的预测误差，更不是证明整张mapping失效。

### 3.2 RS-Q／San Pedro／Port：广义支持，内部份额未知

ZEPEO文件PDF第24页说明现有RS-Q RackB服务San Pedro与Port，容量160 MVA，9个energized circuits和1个spare position；新的RackD和RS-C线路属于规划内容，不能当作已经存在。

两套mapping在RS-Q南侧San Pedro方向均有明显权重。地图阅读参考点(-118.292,33.736)所在tract06037296600，对RS-Q的权重为0.670489→0.757620；但这只显示该代表位置的proxy与具名关系相容，不证明整tract都由RS-Q服务。

Port内部另一参考点(-118.247,33.743)位于06037980031，RS-Q权重为0.042027，两图相同。官方“Port”是广义地区，没有提供该terminal的客户分配；不能据此计算误判率，或把未报告的terminal当作阴性样本。参考点及完整候选名单见LADWP_GEOGRAPHIC_REFERENCE_CHECKS.csv。

### 3.3 RS-J：支持区域联系，不足以验证边界

官方2017事件明确涉及Northridge、Reseda及周边多个北谷社区。图2显示RS-J权重也集中于该广义区域，这是局部空间相容性，而不是serving territory验证。当前保留数据没有同年、可核实的逐客户／feeder affected polygon，因此没有计算“整个社区命中率”、false-positive或false-negative。没有被新闻提到的地区不被视作未受影响。

DS57、DS49、DS27，以及不在92站中的RS-P，未找到可据此接入92站的明确上游键；只保留机制背景，未以最近站连接。RS-B的具体当代官方事件证据仍未建立。

![LADWP具名地区与站权重](Fig2_LADWP_named_geographies.png)

图2：同一色标显示直接站权重，不是观测停电比例。红色轮廓是包含LAX参考点的原tract；不是新制作的电力服务范围。官方原图另存LAX_OFFICIAL_CONTEXT.png，供读者对照，未digitize成GIS。

## 4. 具名事件与source gate诊断

### 4.1 RS-J 2017：实际、预计和未完成事项分开

| 时间（当地原文） | 事件／状态 | 证据性质 |
|---|---|---|
| July8约18:52 | 站内一部分设备起火 | 实际报告 |
| 约18:55 | 全站进出电隔离，保护消防与工人 | 实际报告；不等于全站所有设备物理损坏 |
| 约22:00 | 稳定周边系统后50,000+客户恢复 | 实际报告 |
| July9约05:00 | 清除受损导体／断路器／变压器并检查，约94,000客户仍未恢复 | 实际报告 |
| 同一05:00更新 | 多数客户预计2–4 h恢复 | **预测**，不是实际时间 |
| 06:00–08:00 | 剩余约94,000客户恢复，至08:00全部复电 | 后续实际报告 |
| 10:30更新 | 损伤评估和永久维修仍继续 | 未报告永久维修全部完成时点 |

来源为LADWP官方posts4867、4870、4888、4911，URL、快照及各步骤对应关系在NAMED_EVENT_PROCESS.csv。初期“约140,000”、后续50,000+和94,000都是新闻估计，不强制算术配平。它们是客户数，不能拿模型tract人口直接对标。

这个过程支持：设备事件可因安全隔离扩大影响；系统稳定／转供可先恢复部分客户；复电并不等待所有永久维修结束。它不直接提供事故修复duration分布。

### 4.2 直接权重与额外源路径影响

设退出站为j、全功能参照state为e0、退出后的gate state为ej，原mapping为W：

- 总tract proxy损失 = W(e0−ej)；
- 直接损失 = W[:,j]；
- 额外路径损失 = 总损失−直接损失。

所有参照站均source-connected；本次没有把missing当成zero或另建mask。表中“positive tract”只是模型权重大于0，**不是观测全停电tract**。

| 单站退出 | Baseline直接positive tract | Constrained直接positive tract | 额外失去source路径的站 | 额外positive tract：两图 |
|---|---:|---:|---|---:|
| RS-J | 138 | 166 | 0 | 0 /0 |
| RS-N | 56 | 34 | 0 | 0 /0 |
| RS-Q（原source之一） | 52 | 48 | 0 | 0 /0 |
| RS-C | 67 | 49 | 0 | 0 /0 |
| RS-K | 120 | 153 | **COLORADO一个站** | 100 /51 |
| Rinaldi（原source之一） | 93 | 187 | 0 | 0 /0 |

STATIC_EVENT_DIAGNOSTICS.csv及STATIC_EVENT_TRACT_IMPACTS.parquet保留全部分解。两种mapping没有改变任何站的连通结果；仅改变站损失落到tract的权重。

RS-J广泛地区影响在此静态条件下来自mapping，不是network gate切断更多站。不能用RS-J事件为一个本次没有发生的额外源路径机制背书。原sources冗余使单独退出RS-Q或Rinaldi也没有额外断开的站；这不证明实际运行具有相同冗余或足够可用容量。

### 4.3 COLORADO：一个具体、不能忽略的依赖不一致

原graph中COLORADO306694只有一条边：RS-K301105—COLORADO，长度约1.695 km。于是RS-K退出会使COLORADO失去全部源路径。

本次SCE原始记录则给出：

- Colorado69/16 kV：7个回路；
- Colorado69/4 kV：4个回路；
- 两组均为La Cienega220/66 System；
- 同名外部站点与July COLORADO位置差约32 m。

这比泛泛“缺feeder数据”更具体：当前图产生了一个LADWP站控制SCE Colorado可达性的依赖，而独立named-system资料指向另一个系统。**官方system label不是单线图，尚不能授权直接新增Colorado—La Cienega边或删除RS-K边**；但依赖于这条唯一路径的传播结论需要核实／有针对性对照，不能称为已由外部案例验证。

![COLORADO依赖诊断](Fig3_Colorado_dependency_diagnostic.png)

图3左：保留的唯一图边与真实下载的Colorado回路几何；La Cienega只标位置，没有伪造一条电气连线。右两图：RS-K退出后通过COLORADO产生的额外proxy损失。没有报告的地方不作为实际未停电地区。

### 4.4 Gate能保留的解释

Gate可以表示：在给定可用／功能设备集合下，是否存在到指定source的抽象路径。它没有表示负荷分配、支路／变压器限额、开关／保护、消防隔离、许可／巡视、站内bank部分可用、临时转供及不同客户分批复电。

因此“functional”必须解释为该抽象节点在当前条件下有资格参与供电可达性，不能仅凭永久维修完成与否解释全部实际复电过程。本轮不改调度／维修时钟，也不把这些事件当作其参数标定。

## 5. CPUC：确实连起来的键，以及没有连起来的部分

### 5.1 修正一个已有整理表问题，保留原始资料

此前取得包的T05整理表759／453行混合了同sheet的时间表与客户表；这些不能继续作为“停送电时间记录数”。本次保留原文件，直接依表头重拆完整保留sheet。PG&E shared-customer附表不混入SCE主表，N/A保留；第二工作簿时间单元格本身为完整datetime，按其明确格式读取。分析早期的dtype／时间／缺失键错误日志保留在目录内，最终结果以本节和最终CSV为准。

| 工作簿 | SCE主时间表 | 唯一circuit名称连到2026几何 | 同工作簿county+circuit唯一连到客户表 | 实际duration可读 |
|---|---:|---:|---:|---:|
| January2–17,2025 | 377 | 371 | 341 | 367 |
| January17–27,2025 | 226 | 224 | 203 | 226 |

名称匹配连接的是**该2025事件所报告circuit与2026几何的候选身份**，不是证明线路在两个时点完全不变。客户表重复键不强制一对一；共享客户附表的merged-cell continuation不擅自补成主表记录。

有7条主表时间记录可直接对应92站站名：BROADCAST、CRESCENTA→Gould；HASKELL→Arroyo；LOPEZ、VETERANS→San Fernando（包含不同工作簿重复事件）。BROADCAST的January事件仍缺实际restoration，后期事件报告了因持续大风／白天航巡延迟；不能把它转成地震维修工时。

两个原记录（KULBERG、ZEVO）restoration比all-clear早27分钟，已原样保留，未clip或当正常操作滞后样本；不能在未厘清含义前用这些时差校准模型。

### 5.2 真正共同事件键

2023年度named-circuit表与amended POSTSR2B的**显式EVENTID**有3个精确共同事件：

- July11：1条circuit记录、1个tract、两表均5 accounts；可在这些报告范围内识别HUCKLEBERRY—06037910206。这一tract**不在July的2,315 tract域内**，不能作为本模型的直接mapping验证。
- October29：41条circuit记录、190条tract记录（189 unique tracts），两表总accounts均25,504；属于同一事件的独立边际表，**不能推出41×189的确定分配关系**。
- November20：5条circuit记录、50条tract记录（49 unique tracts），总accounts均2,780；同样不能分配到individual circuit。
- 另外两个事件未找到相同EVENTID，未用同日期／近邻强行配对。

CPUC_EVENT_KEY_COVERAGE.csv保留这些结果。总accounts吻合支持事件级对齐，不证明逐circuit对应。

2025 POSTSR2A与2B共享1,222个tract标识，但2A主要是YYYYMM×Track汇总；缺event/circuit键。其1,499行中241行位于July域内。这里只能做tract身份及边际地理分析，不声称完整“circuit→tract→实际复电时刻”链已闭合。

## 6. 负荷／容量：已有实质输入，但必须区分口径

| 类别 | 原字段／材料 | 能说什么 | 不能说什么 |
|---|---|---|---|
| 历史负荷 | SCE min_load_mw /max_load_mw | 月×hour-of-day负荷包络，MW字段明确 | 不能还原8760同步负荷或跨bank相加为同时峰值 |
| 规划需求／负荷限额 | GNA cumulative_demand /fac_load_limit，同facility同year | 同行需求／限额比及provider facility_loading的局部筛查 | 不能拿历史MW直接除未核定绝对单位的planning限额 |
| 规划余量 | GNA subst_capacity | 本次可筛查行中等于fac_load_limit−cumulative_demand | 字段名不能被误读为整站nameplate capacity |
| ICA接入能力 | max_remain_cap、limiting criteria等 | 接入／规划context，保留queued generation/redaction | 不是92抽象边热限，不是震后可用输送能力 |
| LADWP容量图 | Capacity_Range_KW | 线段空间容量区间提示 | 不累加线段，不由近邻生成站／线连接 |
| RS-Q现有设施 | RackB160 MVA | 具名existing bank额定值 | 不是可直接供给160 MW，也不是全92站asset的实际负荷 |
| 规划新增 | RS-Q RackD160 MVA；拟建RS-X160 MVA | proposed项目量，明确年份／范围 | 不计入已有容量，不赋给RS-N |
| Adelanto–Rinaldi | 500kV线现有1593A continuous/emergency，拟增1680A/1965A | 具名线路额定／计划对照 | 不填branch reactance，不转成整站MW |

历史表可对应33个July站名、100个站名×电压×年份组合，14,400条数值记录；同名多电压设施保留分开。详见SCE_REPRESENTED_HISTORICAL_LOAD.csv。这不是33个完整站级8760 profiles。

GNA同名下游设施共44个，覆盖33个July站名。2026年37条可作**同行、无量纲规划比值**筛查，7条redacted/invalid不纳入。唯一ratio>1的是OLINDA66/12：28.45/26.09≈1.09046，provider facility_loading为109.04，subst_capacity为−2.36。它是该电压设施的planning需求／限额警示，不是确认July高压Olinda整站发生了物理过载，更不是地震损伤后的capacity结果。

原表绝对功率口径在保留dictionary中未充分展开，因此不将上述28.45和26.09擅自标成MW或MVA；无量纲比值与provider loading的相符关系单列误差。2026–2035其他行完整保留为规划背景，未将未来扩建容量混入当前网络。本轮没有把任何capacity数值写回模型。

## 7. 对模型和reviewer回复的具体决定

| 证据／发现 | R1 #1 mapping | R1 #2 propagation | 本轮决定 |
|---|---|---|---|
| 新版337-tract paired benchmark | 可直接用；必须连同480个不可直接比较tract一起报告 | 不证明电气路径 | 保留两图对照，不能声称feeder验证 |
| Utility constraint小幅改善 | 支持一个透明候选兼容性改进方向 | 不改变跨utility图路径 | 不自动替换production |
| LAX–RS-N缺口 | 具体局部依赖未被当前proxy表示 | RS-N退出对机场代表tract为0是mapping结果 | 若保留局部供电claim，需核实当期站/服务关系；不擅自修权重 |
| COLORADO唯一路径与sys_name不一致 | 可说明层级/身份问题 | 直接影响RS-K退出时的额外传播 | 需要定向核查；不能仅靠通用limitation回避，但暂无依据指定新边 |
| RS-J完整过程 | 支持named station–region关系 | 支持操作性隔离/分阶段复电，揭示永久维修≠复电 | 可直接用于范围说明，不称事故重演或全网验证 |
| CPUC显式事件／circuit键 | 能连部分identity与county/customer记录 | 有实际all-clear与复电过程 | 明确空间键未完全闭合，禁止M:N强行分配 |
| GNA／ICA／LADWP ratings | 不识别service shares | 说明reachability之外确有capacity/operation条件 | 只保留局部可比筛查，不新增热限/阻抗/潮流 |
| DS57/49/27、RS-P等 | 无可靠July92上游键 | 机制背景 | 不nearest补接，不算92站事件验证 |

可以直接用于回复的表述：

**R1 #1：** 我们增加了基于公开回路几何、直接站名及负荷联结的external consistency benchmark，并把inventory coverage与conditional mapping agreement分开。Utility compatibility带来有限改善，但候选覆盖缺口和LAX局部反例表明结果不能被解释为真实customer assignment。我们保留这些不一致并限定局部归因。

**R1 #2：** 我们将source gate解释为给定设备可用状态的抽象source reachability。具名案例和静态退出诊断区分了直接服务权重与额外源路径影响，并揭示操作性隔离、转供、capacity和分阶段复电的缺失。RS-K–COLORADO依赖需要定向核实；没有宣称完成潮流或全网停电验证。

以上是可引用的结果与边界，不是已修改论文或response letter。未进行策略outcome再计算；旧策略结果缺少可无损remap的逐realization92站时序，不能由本次静态诊断推断T80/burden稳健性，也未为补数据重跑模型。

## 8. 交付与使用

主要结果表：

- SCE_STATION_EVIDENCE_CROSSWALK.csv；SCE_TRACT_INVENTORY_COVERAGE.csv。
- SCE_MAPPING_BENCHMARK_SUMMARY.csv／逐tract表；BENCHMARK_VERSION_COVERAGE_CHANGE.csv。
- LADWP_GEOGRAPHIC_REFERENCE_CHECKS.csv；NAMED_EVENT_PROCESS.csv。
- STATIC_EVENT_DIAGNOSTICS.csv／STATIC_EVENT_TRACT_IMPACTS.parquet。
- CPUC_CIRCUIT_TIME_LINKS.csv；CPUC_EVENT_KEY_COVERAGE.csv；CPUC_LINKAGE_SUMMARY.csv。
- SCE_REPRESENTED_HISTORICAL_LOAD.csv；SCE_LOCAL_PLANNING_SCREEN.csv；SCE_LOCAL_SCREEN_SUMMARY.csv；SCE_REPRESENTED_ICA_CAPACITY_CONTEXT.csv。

图1–3提供PNG及PDF；LAX_OFFICIAL_CONTEXT.png为官方PDF原图阅读副本。所有外部原始数据及旧benchmark保留。本分析停止于此，没有替换production mapping、修改source gate、重写论文或启动新的scientific pipeline。

## 9. 两处关系的定向追溯与决定

### 9.1 LAX—RS-N：零值发生在cutoff，不是候选排除或源路径断开

只追踪原tract **06037980028**：面积19.7233 km²，投影几何centroid位于−118.41353785、33.93981629，仍在该tract内部；原人口表为0。它包含此前使用的机场内部参考点，并在空间上覆盖官方图中的机场主体区域，但**它不是官方机场电力服务边界**。本次没有把官方PDF机场轮廓人工数字化成新的GIS，也没有计算未经精确机场边界支持的面积／客户服务占比。

2019官方EA §1.2.2、Exhibit1-2支持RS-N→当地distribution points（包括DS-111）→LAX的设施供电联系。它没有给出整个tract的客户份额，也没有说该tract内一切负荷都由RS-N承担。UNKNOWN301100的位置接近机场不等于它已被证明是DS-111；本次没有作这种身份补配。

| 七月mapping步骤 | 本tract实际结果 | 对零RS-N权重的作用 |
|---|---|---|
| utility eligibility | mixed/ambiguous；两套方法均保留general候选 | RS-N未被排除；两套mapping相同 |
| centroid→nearest access | UNKNOWN301100；距离1.467955 km | 选定距离代理的出发站，不代表已验证服务站 |
| access→RS-N网络最短路 | 7.899532 km；保留图中有直接抽象边 | RS-N可达，不是disconnected |
| total distance | 9.367487 km；centroid到RS-N直线距离4.237406 km | 沿网距离比直线距离大；本轮不改距离定义 |
| 1/d²、全候选归一化 | RS-N权重0.0119818198404464，约1.1982% | 截断前仍有正权重 |
| `<0.03` cutoff | 1.1982% < 3%，被设为0 | **直接产生零值的步骤** |
| renormalize | 只放大剩余四站；RS-N仍为0 | 不会恢复被截去候选 |

未截断的保留CSV本身也记录同一个RS-N权重0.011981819840446373，独立于本次步骤重算。最终四站权重为UNKNOWN301100=0.709941、Station L=0.174001、El Segundo=0.064492、Sepluveda=0.051566。完整92站该行计算见`LAX_MAPPING_STEP_TRACE.csv`。

**方法判断：不是实现bug，不能为命中LAX把cutoff改小或强塞RS-N权重。** 该案例证明“距离较近／沿网可达＋权重截断”不保证保留一个已知设施服务关系；它不证明整个tract的正确权重应为RS-N=1，也不提供可替换四站份额的数据。保留两套方法作为tract级proxy，但不得用这一tract的结果声称已经预测机场供电。如果未来研究专门评价机场，应另用显式设施服务关系与适合该设施的观测量；本轮不扩展此模块。

该tract人口为0，因此它自身不影响当前population-weighted汇总，但并非没有机场负荷，也不意味着设施联系缺口无关紧要。不能用人口指标稳定为机场服务预测背书。对全域社区结果是否存在同类局部归因敏感性，使用§10既定运行的双mapping评价回答。

### 9.2 RS-K—COLORADO：几何边可恢复；唯一供电依赖尚不能证实

本次没有重新运行topology builder。直接读取七月`topology_interactive_validation_expanded.html`中保存的16顶点路径，并回查原`TransmissionLine_CEC.shp`。HTML是经纬度线性画布、坐标保留两位小数；逆变换仅用于定位原顶点，不把显示坐标当精确GIS。14个内部路径顶点与原始线顶点误差均小于0.53 m；用对应的原始坐标、原站坐标及七月graph key的0.1 m舍入重算该**已保存路径**，长度为**1695.3750278381 m**，与现有边CSV完全相同。

| CEC原行／GlobalID | 原属性与关系 | 七月处理对应 |
|---|---|---|
| 5322 / `c715473b-419b-4796-9c85-8473db220913` | SCE、66kV、Operational；长1028.0928 m；一端距COLORADO5.5371 m | 该端落在150 m primary snap内 |
| 5320 / `936c49b4-89d5-4caa-bb15-b07b30fc750c` | SCE、66kV、Operational；长763.7489 m；一端距RS-K16.6128 m | 该端落在150 m primary snap内 |
| 上述两段的共同端点 | 原始坐标完全相同；不是空间交叉处推定连接 | 保留同属性线节点连接 |
| 5323 / `bf065e64-51b2-44aa-9b56-d68850605ad6` | 端点与5322内部顶点10相同；距COLORADO39.0879 m | protected-junction cluster可将该共享顶点锚到COLORADO |
| 5321 / `5d453a56-7eff-4009-937b-b20d91e17f95` | 端点与5320内部顶点5相同；距RS-K99.709 m | 同一cluster处理可将共享顶点锚到RS-K |

这解释了为什么最后路径不是两条原线全长简单相加：站旁的共享junction及末端被锚定到站坐标，保留路径跳过已经合并的站旁尾段。原`force_snap_endpoints_to_substations()`、`snap_protected_junction_clusters_to_substations()`及`compute_direct_links()`分别负责端点／共享节点锚定和无中间站路径提取；不是后来新增的M2连接。对应原始线属性与WKT、逐顶点对应见`COLORADO_CEC_LOCAL_LINE_TRACE.csv`、`COLORADO_RAW_VERTEX_CORRESPONDENCE.csv`。

另一项重要事实：July站表给RS-K记录**MAX_VOLT=230、MIN_VOLT=66**，COLORADO为66/66。因而不能以“RS-K是230kV站”断言66kV线不可能在该站址关联，也不能以LADWP/SCE owner不同直接证明端点连接错误。原CEC线的Source为Google & BING & ESRI，属性为公开制图记录，仍非接线单线图或运行开关记录。

新SCE记录提供的Colorado69/16、69/4与La Cienega220/66 named-system归属、约32 m站址对应，支持同一站址／相关电压设施的身份联系，但没有说明每一条66kV线路的运行端点、跨utility接口、站内母线隔离或备用供电方式。**“有一条到RS-K站址的几何线路”与“Colorado属于La Cienega系统”不是必然互斥。** 原模型把站址聚合成一个节点、并把保留邻接视为可传递的源路径，因此额外作出了“RS-K整个节点退出后Colorado无其他源路径”的强假设；现有公开数据没有验证这个唯一性。

**分类与修改决定：** 已恢复这条边的直接几何和代码处理依据，不能归类为“已确认错误连边”；尚未完全解决的是资产／母线层级和唯一供电依赖。现在**不删除RS-K—COLORADO、不新增Colorado—La Cienega、不改变source gate**。早期历史probe CSV的Git树条目尚在，但本地对应LFS对象未取得；不能假称找回了所有中间audit。本次路径依据来自投稿版实际保留HTML、原CEC和边CSV，已足以定位该边的组成，不需为此重建网络。

若最终结果显示这一特定唯一路径贡献很大，应明确把该部分解释为抽象网络条件下的传播，不能升级成已证实的现实Colorado停电机制。没有新直接依据时，不为保住或改变结果而剪边。

## 10. 加入最终实验清单的两项必需输出（复用原定运行）

这里仅补齐既定final science的输出要求，不重新冻结策略／crew／样本量，也不启动运行。现有branch尚未冻结的最终实验矩阵仍由既有设计决策决定。**这两项不增加physical realizations，不增加scheduler或GA运行，也不另开MC。**

### F1：同一92站轨迹，两套mapping并列评价

每个既定`realization × strategy × 原定scenario`保留同一event-time grid上的92站raw functionality `f_i(t)`和gate后effective state `e_i(t)`。将**同一个e**分别送入`JULY_BASELINE_92`和`JULY_UTILITY_CONSTRAINED_92`，不重新排序、不重新优化priority、不更换物理样本、source、crew或工时。

必须并列输出：population T80、累计负担（明确原指标分母）、hospital burden、Q1–Q4绝对负担、signed/absolute gap、人口加权Gini、逐tract负担变化及improved/near-zero/worsened/unresolved人口。策略差及mapping差都按realization配对；平均效应分类与逐次分类分开；±1 h仍是实用阈值，不是显著性阈值。fully unresolved仍为NA；两套mapping采用各自明示的represented mass，不能将未表示部分当失败或恢复。

完成判据是能回答“总体差异是否保留、幅度改变多少、哪些tract／群体归因敏感”，不是要求utility-constrained结果更好或与baseline一致。该实验是固定决策下的evaluation sensitivity，不是mapping改变后重新制定policy的比较。

### F2：同一过程，分解自身功能损失与gate增加损失

在原92站识别域、原全功能参照为1的条件下，逐站逐event保存：

- 自身功能损失 `L_self,i(t) = 1 − f_i(t)`。
- gate增加的损失 `L_gate,i(t) = f_i(t) − e_i(t)`。
- 总损失 `L_total,i(t) = 1 − e_i(t) = L_self,i(t) + L_gate,i(t)`。

**不能把所有L_gate都叫“其他站切断源路径的损失”。** July gate同时使用0.5 functionality threshold；应随同保存原功能阈值标记`F_i(t)`与源连通标记`C_i(t)`，使`e_i=f_i F_i C_i`，并在需要解释机制时区分：自身低于阈值所截去的残余`f_i(1−F_i)`，以及已过阈值但无可用源路径的`f_i F_i(1−C_i)`。这些是对原gate输出的记账，不改变gate算法；未知状态不纳入零值分解。

对两套固定W分别报告`W L_self`、`W L_gate`及二者的事件积分，并验证相加等于同口径总缺额。原定run的排程和状态只计算一次，保存这些量即可完成两套映射和分解；不需要增加“gate OFF”科学运行。T80等非线性指标不做加法分解。

保留RS-K状态、COLORADO自身状态及其源连通标记，以辨认“Colorado自身仍可用而失去源路径”的时段与空间贡献；这只是模型内机制记账，不把所有gate损失因果归给某一站。最终检查：社区负担主要来自自身损伤还是gate放大、两套mapping是否改变这种判断、COLORADO这类未完全确认依赖是否主导局部结论。

### 最终决定

两处关系目前均**没有足够依据要求具体production代码或边修改**。LAX需要收紧设施级解释；COLORADO的几何边得到支持，唯一运行依赖仍未验证。保留原92站／318边与两套mapping进行上述既定结果输出，允许结果显示局部敏感或gate主导，不因结果方向临时改权重、剪边或另开MC。本轮仅增加本报告的追溯与实验清单、必要小表及离线追溯脚本；未改论文、生产模型或实验样本。

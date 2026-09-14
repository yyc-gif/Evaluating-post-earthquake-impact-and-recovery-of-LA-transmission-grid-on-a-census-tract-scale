# Mapping architecture decision — 2026-09-14

本轮比较三个研究架构，使用上一轮已归档的官方关系和冻结06输入。没有新增网络调查，没有运行 source gate、dry build 或任何恢复计算。

## 1. OPTION A / B / C 静态比较

|方案|证据与可解释输出|主要限制|判定|
|---|---|---|---|
|A：strict SCE 817 tract 主分析|官方 tract–circuit–substation 候选关系；权重仍为假设；可研究有独立候选约束的 modeled distribution-service access|23 tract 无可用 R1 candidate；350 tract 候选只匹配一部分；不能省略已知未匹配站后称完整覆盖|**科学架构可行，当前实现不完整。先建立独立 service-access layer。**|
|B：2315 tract full-region proxy|明确为 `modeled source-connected infrastructure/service-access proxy`；utility/evidence tier 显式报告；SCE作为外部候选一致性子集|1062 tract 为 weak/unresolved tier；54个冻结失败不能靠改名当作真实停电；不能声称所有 tract 同等经验支持|**proxy-only 定位可行，不能使当前计算输入自动通过。适合作为分开的 secondary analysis。**|
|C：SCE distribution mapping + LADWP RS/role proxy + ambiguous proxy 合并|数字形式可以均为0–1，但设施层级和遗漏的下游失效机制不同|同一数值并不意味着相同 delivered service；混合聚合会让效应依赖 utility 构成与证据层级|**REJECT OPTION C 作为统一 LA-wide population service-recovery curve。** 可分域并列，不直接合并为同一 primary outcome。|

**最终选择 STRUCTURE 1：SCE evidence-supported restricted primary；full-region transparent proxy secondary。当前门槛为 `REBUILD-SERVICE-LAYER`，不是 GO-SCE，也不是 final dry build。**

这一选择有两项具体依据：SCE候选关系覆盖全部817 tract，规模足以支持有明确地理边界的研究；但373个 tract、1,635,415人具有至少一个未匹配官方候选，不能把“97%至少匹配一个”当完整服务层。没有证据表明SCE与R1一定无法耦合，因此现在也不应放弃独立证据而直接选择 STRUCTURE 2。

## 2. 固定对象、输入及度量含义

- Set A：310 IDs，不变。Set B：仅引用06的 `registered_compatible` 状态，未重新闭合。
- Set C：上一轮121个有据成员仍原样保留。本轮 strict SCE 实际涉及其中113个；119是所有研究 tract 的SCE成员总数，两者分母不同。
- `O_r`：strict SCE tract 与官方 circuit 相交所得 unique normalized official substation names；物理站名去重，不能把多个 circuit/bank 当成多份权重。
- `M_r`：`O_r` 中按08冻结crosswalk匹配到R1的唯一station IDs；`U_r=O_r\M_r` 按官方站名计数。全部113个实际matched站在06中 registered_compatible、component1。这里不以source可达性筛选候选，也未执行21-source gate。
- 人口为 tract人口，不是客户数或电力负荷；SOVI沿用08的NRI-derived `SOVI_SCORE`，不冒称新CDC SVI。
- hospital tract表示本地医院表中至少一个设施记录所在tract，包含不同医院类型；不是运行状态模型、床位供电份额或急救能力。
- PGA仅描述空间暴露。使用保留的primary `2pc50` hazard grid，在EPSG3310 tract polygon centroid按原 `IDW.idw_core`（ln(g)、power2、k8、11km）插值。2315个值有效；未抽样损伤。它不是新地震情景，也不是人口平均PGA或substation PGA。

官方证据入口仍为08归档的 [SCE Distribution Circuits](https://drpep.sce.com/arcgis_server/rest/services/Hosted/Distribution_circuits/FeatureServer/0)、[SCE Substations](https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Layer/FeatureServer/18) 及 CEC/SCE utility polygon；本轮未重新下载。system epoch仍为 `multi-epoch infrastructure proxy`，不将2026公开GIS回填成历史系统真值。

## 3. OPTION A：817 tract 覆盖、规模与代表性

|候选crosswalk覆盖|tract数|人口|SCE人口比例|hospital tracts / records|SOVI中位数 / 人口加权均值|
|---|---:|---:|---:|---:|---:|
|全部官方候选matched|444|1,936,737|54.22%|28 /31|75.58 /70.74|
|matched与unmatched并存|350|1,534,439|42.96%|19 /22|74.52 /68.71|
|全部官方候选unmatched|23|100,976|2.83%|0 /0|76.14 /68.91|
|至少一个matched（前两行）|794|3,471,176|97.17%|47 /53|75.32 /69.84|
|全部strict SCE|817|3,572,152|100%|47 /53|75.35 /69.82|

794/817=97.18% tract至少一个matched；**373/817=45.65% tract、45.78%人口仍有候选遗漏**。最后一个比例是“居住于有候选遗漏的tract的人口”，不是已知缺失供电份额。没有把全部客户归给matched站。

每tract官方unique candidate数分布：1/2/3/4/5/6/7站分别155/284/237/104/33/2/2个tract，均值2.498。matched数0/1/2/3/4/5分别23/269/314/172/32/7。unmatched数0/1/2/3分别444/289/76/8。逐tract的名字、ID、质量标记、数量均见 `SCE_MAPPING_COVERAGE.csv`。

|研究域|tract /人口|hospital tracts / records /911 records|SOVI中位数（Q25–Q75）|centroid PGA中位数（Q25–Q75），g|
|---|---|---|---|---|
|SCE|817 /3,572,152|47 /53 /28|75.35（52.64–88.39）|0.888（0.836–0.948）|
|LADWP|848 /2,954,842|30 /36 /20|79.43（50.24–91.94）|0.952（0.910–0.988）|
|other/ambiguous|650 /2,539,528|26 /27 /17|63.18（35.21–84.96）|0.916（0.875–0.970）|
|全研究区|2315 /9,066,522|103 /116 /65|74.14（47.25–89.21）|0.923（0.872–0.975）|

SCE占全区35.29% tract、39.40%人口，47/103个hospital tract。保留医院文件有121个唯一设施记录，其中116个落入这2315个tract；未将另外5条补入研究区。SCE的PGA范围0.740–1.087g，全区0.714–1.438g，说明restricted domain没有覆盖全区的最高hazard尾部。SCE候选113站的冻结05 PGA中位数0.878g（IQR0.824–0.932），全部310站为0.894g（0.840–0.938）；均是静态输入描述。

**规模足够支持SCE限定研究，不代表统计上代表整个LA。** 其utility、hazard尾部及SOVI构成有选择性。不能由样本量或医院数量保证论文可接受，也不能把SCE的发现外推为LA全域客户恢复。若只用444个完整crosswalk tract，还需明确这是更小的嵌套域，不能悄悄沿用817分母；本轮未采纳这种自动删域。

## 4. SCE-W1 / W2：只构建静态候选权重

对于 `L_rs`＝冻结06 legacy W，定义：

`W1_rs = 1/|M_r| if s∈M_r, else 0`，仅在 `|M_r|>0` 时有定义。

`m_r = sum_{s∈M_r} L_rs`；`W2_rs = L_rs/m_r if s∈M_r, else 0`，仅在 `m_r>0` 时有定义。

`|M_r|=0` 或 `m_r=0` 的相应行是 **UNRESOLVED/NA**，不是全零服务行。无nearest-fill，无source筛选，无epsilon补权，无重新应用cutoff。官方候选资格是独立依据，W2的归一化不是为了baseline或某策略表现。

W1表达“在已表示候选之间没有份额信息时的equal-share assumption”，不是唯一客观/真实客户比例；对350个partial rows，W1和W2都省略了已知unmatched candidates，仅作 **matched-subset design diagnostic**，尚未批准为最终mapping。每行保留遗漏数。

|静态方案|有定义tract /人口|无定义tract /人口|hospital tract /records覆盖|one-hot|
|---|---|---|---|---|
|legacy|817 /3,572,152|0 /0|47 /53|194/817=23.75%|
|W1|794 /3,471,176|23 /100,976|47 /53|269/794=33.88%|
|W2|689 /3,018,098|128 /554,054|39 /44|557/689=80.84%|

W2的128个无定义行包含23个没有R1候选，以及 **105个有候选、但所有候选legacy权重为0** 的tract（453,078人、8个hospital tract/9个医院记录）。候选证据本身已经存在，W2仍继承了旧mapping的零权重排除。因此W2不适合作为独立primary mapping。

W1的269个one-hot中，144个官方candidate原本就只有一个且matched；**125个其实有多个官方candidate，只因其他candidate unmatched而在matched子集中变成one-hot**。所以one-hot增减不能直接解释成真实服务集中或数据质量改善。

### 同一689 tract上的权重结构

为了避免分母混淆，以下三列均限制在W2有定义的689个tract、3,018,098人：

|结构指标|legacy|W1|W2|
|---|---:|---:|---:|
|one-hot数 /比例|149 /21.63%|228 /33.09%|557 /80.84%|
|人口加权 max row weight|0.8273|0.6110|0.9714|
|人口加权 effective count `1/sum(w²)`|1.5127|2.0108|1.0644|
|最大station人口dependency share|2.118%|3.041%|2.660%|
|top5 station share|8.592%|12.298%|11.168%|
|top15 station share|22.626%|29.899%|27.702%|
|冻结key15合计share|2.565%|6.263%|4.673%|

station share=`sum_r population_r*w_rs / sum_r population_r`。它是模型份额，不是实际客户数。W1虽然降低单个tract的平均最大权重，却可能提高全域station聚合集中度；两种集中度不是同一量。

共同689域中，legacy最大share站为BULLIS301489（2.118%）；W1为CUDAHY310167（3.041%）；W2为AMADOR304533（2.660%）。W1在全部794有效行上CUDAHY为3.331%；W2的有效域不同，不能直接把两者当同分母比较。CSV保留每行所有正权重JSON，可复算任意station/key15 share。

|L1结构差异|共同有效行|均值 /中位数 /P90|人口加权均值|确定性top1不同|最大权重集合无交集|
|---|---:|---|---:|---:|---:|
|legacy–W1|794|1.1257 /1.0186 /2.0000|1.1317|459|245|
|legacy–W2|689|0.5513 /0.2602 /1.7725|0.5514|140|140|
|W1–W2|689|0.7151 /1.0000 /1.3333|0.7253|277|0|

L1范围0–2。W1等权使所有matched candidate都并列最大；表中确定性top1按station ID排序。因此W1/W2的277个“top1不同”主要是tie表示，不能解释成277个明确服务首选变化；它们的maximizer sets始终有交集。

**推荐W1作为primary proxy weighting principle，W2只作受限结构敏感性对照。** 原因是W1不继承旧IDW的相对距离偏好及零权重排除，更符合“已知membership、未知shares”的信息集；不是因为哪个方案更像旧结果或覆盖率更漂亮。当前matched-only W1须等service layer完整性处理后才能用于模型。未计算任何T50/T80/AUC、策略差值或恢复负担。

## 5. 142个contradicted tract的结构分类

这里分析“为什么官方candidate未在legacy top3出现”的结构证据，**不是声称已经鉴定真实接线错误的因果来源**。交叉flags可重叠；为给出可加总的表，预先采用D→C→B→A→E的优先级：只有亚米相交→名称坐标冲突→unmatched数量严格超过matched→有matched但未进top3→其他。majority按候选数，不按未知客户份额。epoch风险适用于全部关系，不能无证据归为某个tract的已确认成因。

|主分类|tract数|人口|SOVI中位数 /人口加权均值|含义|
|---|---:|---:|---|---|
|A matched候选存在但不在legacy top3|102|444,668|77.87 /71.20|有可操作的官方候选重构路径|
|B majority candidates未匹配R1|26|116,638|80.82 /71.02|含23个全部unmatched、3个matched少于unmatched|
|C 名称/坐标crosswalk冲突|14|53,926|54.16 /60.06|MESA、TROPHY既有冲突影响候选表示；未修改crosswalk|
|D 只有亚米相交的几何候选异常|0|0|—|没有这一已检测异常；不等于所有geometry都已验证|
|E 其他|0|0|—|按上述完整规则无需额外类别|

独立非互斥flag A为119/142、514,256人；B26、C14、D0。主分类A占71.83%，不是多数tract都缺任何R1候选。**旧candidate selection需重构，同时整个817域的service-node遗漏依然不能忽视。** 全域有候选但W2支持质量为0的是105个，与主分类A不同分母，不可互换。

## 6. 必须区分 network nodes 与 service-access nodes

strict SCE关系共涉及 **196个官方normalized service-station names**：113个有R1 crosswalk，83个没有。83个中79个有官方站点坐标记录，69个位于研究区几何内；剩余包含研究区外供区接口和缺官方点的名字。81个为unresolved name crosswalk，2个为MESA/TROPHY坐标冲突。**unmatched不证明该实体在R1物理上不存在**，但目前没有可审阅的一对一表示，不能在模型中视为已表示。

196是strict SCE candidate universe；上一轮203是整个研究区内官方D/A物理站、119是整个研究区matched SCE Set C，不能简单用203−119替代本轮83。

有未匹配候选的373个tract包括：23个完全缺表示（100,976人），350个部分缺表示（1,534,439人）。只删除前23个不能解决后350个的known omitted candidates。未匹配站名关联人口最多的若干项为 PASSONS19 tract/93,280人；MESA18/78,861；FRANCIS16/69,575；RAILROAD14/68,000；LAWNDALE14/65,284。这些是candidate exposure人口，跨站不可相加，不能称实际服务客户。

**决定：为保留817域的官方candidate support，需要独立service-access layer。** 下一步设计保持：

1. Network layer仍使用冻结R1 A/B；不把83个未匹配配电站自动加入transmission topology。
2. Service layer以196个official names及原bank/circuit IDs作为候选记录，保留类型、坐标、identity quality和研究区外状态。113个crosswalk提供identity attachment候选，仍须防止同物理站的network/service表示被重复损伤或重复修复。
3. 83个未匹配站单列upstream attachment状态。没有依据就unknown，不能按最近transmission line硬注册。也不能省略其服务份额并把权重悄悄移给其他站。
4. tract→service layer保持官方候选关系。W1的equal-share原理可用于最终已明确定义的候选域；本轮仅计算了要求的matched-R1 W1/W2，没有构建196列生产矩阵或实施任何新连接。

### 已有 `sys_name` 是有限且具体的衔接线索

无新增下载。官方circuit中83个未匹配service names均带有 `sys_name`，每个仅落入一个已记录system group。strict SCE共18个 `220/66 System` 标签，其中14个与R1名称或冻结CEC名称唯一对应，4个没有：Barre、Chino、Olinda、Padua。**71/83个未匹配service names有可核查的R1同名上游系统候选，另12个没有。**

例如Floraday、Downey和Passons属于官方`Center 220/66 System`，R1有CENTER300232；Monrovia属于`Rio Hondo 220/66 System`，R1有RIO HONDO305984。该字段直接支持系统组归属，**不证明具体接线端子、direct edge、容量或供电唯一性**。MESA/ALAMITOS的同名system候选也不消除既有坐标冲突。没有将这些system接口升级为source或加边。

下一次唯一值得实现的是：**official tract→service-node候选层及显式upstream attachment ledger**。先保留196个记录、113个identity候选、83个未闭合连接，按已有`sys_name`做限定接口审阅。不能直接把服务节点归给source可达的最近站。若接口始终无证据，就在后续单独决定restricted domain或显式upstream proxy，不能在本轮假装已经闭合。

## 7. OPTION B 的证据层级与54个失败标记

Tier是新定义的 **候选关系/角色证据层级**，不是官方评级，也不是旧W质量分数。固定规则不看source gate或恢复结果：

- High：strict SCE且全部官方候选有R1/B crosswalk（444）。该层也不验证份额。
- Moderate/proxy：strict SCE有matched和unmatched并存（350）；或strict LADWP的冻结legacy top1为已确认DS/RS角色（459）。后者只是物理角色支持的upstream/access proxy，绝不等同经验tract→DS关系。两种子类在CSV保持分开。
- Weak/unresolved：strict SCE无R1候选23；LADWP无已支持role的legacy top1 389；other/ambiguous650。不能因为mixed tract与某条SCE circuit相交就强行提升全tract tier。

|tier|tract数|人口|全区人口比例|SOVI中位数 /人口加权均值|hospital tracts|
|---|---:|---:|---:|---|---:|
|High candidate evidence|444|1,936,737|21.36%|75.58 /70.74|28|
|Moderate/proxy evidence|809|3,123,883|34.46%|79.19 /71.60|37|
|Weak/unresolved evidence|1062|4,005,902|44.18%|67.49 /63.82|38|

evidence tier的SOVI构成有系统性描述差异：weak人口加权均值比moderate低7.77点，比high低6.92点；不能说“缺证据只发生于高脆弱社区”。全区固定SOVI四分位切点47.255/74.140/89.210，对应weak层Q1人口占29.46%，high15.94%、moderate18.70%。这是coverage selection的描述，不是因果或恢复公平性结论。

54个冻结baseline failures在新tier中：high2/11,475人、moderate1/4,124人、weak51/204,827人。原08的3/22/29证据分类完整保留：high2与moderate1均来自此前“候选关系resolved”的3个；weak包含22个mapping uncertain及29个无公开证据。

每行标记 `retain_flag_model_boundary_or_mapping_gap_not_observed_outage`，而不是数学修复。即使采用B，也不能把54个pre-event=0带入曲线解释成震后停电；应先定义其推断边界/缺失处理及报告分母，**不是只改文字就允许恢复计算**。本轮没有排除、重新分配或激活source。

## 8. LADWP：可量化proxy footprint，真实服务coverage仍未知

2 confirmed DS与15 confirmed RS全部沿用08角色证据和06节点状态，不追全市feeder。strict LADWP848 tract内：

|已确认角色集合|冻结W有任一正权重关系：tract/人口|冻结W top1：tract/人口|centroid最近距离中位数 /P90|可由独立证据确定的服务区人口|
|---|---|---|---|---|
|DS2|78 /249,818|70 /222,399|10.69 /22.23 km|**未知**|
|RS15|551 /1,945,503|389 /1,367,045|3.90 /6.82 km|**未知**|

表内前两列是原proxy的结构覆盖，不是官方service coverage。所有15 RS在冻结component1，但不能凭同一component把全部848 tract声称为RS服务区。距离不设任意catchment半径；附近有站不证明供电关系。

DS站点本身落入strict LADWP的1个tract/2,976人口；RS站点落入8个strict tract/23,582人口；其余站点位于mixed等tract。点落在tract内也不等于该tract由该站服务。已有材料提供的 **独立tract→confirmed DS分配记录数为0**，这表示映射未知，不是DS不供电或零人口受服务。

LADWP evidence-supported subset目前只能叫“有确认DS设施角色的站点集合”，不能凭78个旧W关系形成经验服务subset。其余区域最多支持 `upstream community-supply interface proxy`，RS不得命名为 `tract-serving substation`。FiT+已知缺station key，不进行外推。

## 9. 可正式写进论文的方法与主张架构

**STRUCTURE 1（选择）：**

- Primary：strict SCE evidence-supported candidate domain。候选归属来自官方distribution circuits；equal shares是显式模型假设。主要结果应称“在官方候选约束下的 modeled distribution-service access”，不称actual delivered electricity。必须先补齐service-layer表示/限定残余推断域，再运行恢复计算。
- Secondary：全域统一定义的infrastructure-access proxy。保留utility和evidence tiers，单独分析其条件性比较；SCE官方关系提供外部candidate一致性检查。不能把来自两层物理接口的输出合成主结果。
- 物理层级边界：generation/transmission availability、RS upstream access、distribution-station access和customer delivery分别定义。相同0–1量纲不足以证明可交换或可聚合。

若同一secondary proxy定义被一致应用于所有utility，可以报告明确命名的LA-wide **proxy index**，并分utility展示；它不是将SCE强证据服务结果与LADWP弱proxy拼成实际恢复曲线。当前baseline和服务域问题仍需单独闭合。

可用的方法表述：

> The primary inference domain comprises census tracts assigned unambiguously to SCE in the archived utility polygons. Intersections with published SCE distribution circuits identify candidate service substations. Candidate membership is distinguished from unknown customer-load allocation; equal candidate shares are an explicit modeling assumption. Network infrastructure and distribution-service interfaces are represented separately, and unresolved upstream attachments are retained rather than filled by proximity or source reachability. Regional infrastructure-access proxy results are reported separately and are not pooled with distribution-interface results as delivered electricity recovery.

这是下一版方法架构，不是宣称上述service layer已实施。若后续有限接口工作证明SCE layer无法合理耦合，才考虑STRUCTURE 2 / GO-PROXY并下调全篇主张；目前71个未匹配站有官方system-group衔接线索，尚无理由提前认定无路可走。

## 10. GO / NO-GO及最终直接回答

**当前：REBUILD-SERVICE-LAYER。** 对817完整域不发GO-SCE：45.78%人口处于有候选遗漏的tract，而且W1的125个one-hot是matched-subset省略造成。也不发GO-PROXY：没有证明SCE独立关系无法耦合，放弃它会损失本研究最强的mapping证据。

下一步完成独立service records与attachment ledger后，只有在候选缺口已显式处理、同物理站避免重复建模、source边界含义一致、所有保留tract的分母和服务层级明确，才允许申请final static/dry QA。未知连接不可被“可达”替代。

1. A可行但需service layer；B是可辩护的secondary/proxy-only备选，不等于当前输入已可跑；C统一实际服务聚合拒绝。
2. **794/817** 有至少一个matched official candidate；均至少一个registered B候选。
3. **23** 只有unmatched候选；**350**有matched+unmatched；总共373个tract的官方支持集需要补表示。
4. 142中主分类A102、B26、C14，主要是legacy candidate选择与官方候选不一致；不是全部缺R1，也不是已证明全部真实接线错误。
5. **W1优先**，份额无知时更透明；W2继承零权重排除，128行无定义且有效行80.84% one-hot，保留为对照。
6. 为保留817完整官方candidate集合，**必须建立独立service-access layer**；不修改310 transmission inventory。
7. LADWP支持DS/RS设施角色和明确命名的upstream proxy，不能恢复citywide经验tract服务分配。
8. 不允许将SCE distribution-access与LADWP upstream proxy合成同一primary service curve；可并列，或另设统一定义的secondary proxy index。
9. **STRUCTURE 1**，实施状态为conditional architecture / service layer pending。
10. 下一次唯一实现：**196个官方service-node候选记录及其tract关系、113个identity候选和83个显式upstream attachment状态**；W1是待表示完整后采用的primary原则。
11. 继续禁止source gate、final dry build、topology/source变更、damage/repair/dispatch、recovery/MC/GA、32×4、29 crews；不得为旧结果选择权重。

## 11. 四个交付文件及复算定义

- `SCE_MAPPING_COVERAGE.csv`：817行，官方unique/matched/unmatched数、名字与crosswalk详情、医院/PGA/SOVI、contradiction主分类和重叠flags。`candidate_match_details_json`保留每个官方站名的sys_name及同名R1系统候选，`upstream_attachment_implemented=False`。
- `SCE_WEIGHT_DESIGN_COMPARISON.csv`：817行，legacy/W1/W2稀疏正权重JSON、有效状态、top1及并列集合、one-hot/effective count、L1。无定义的权重字段空白，不是zero row。
- `EVIDENCE_TIER_COVERAGE.csv`：2315行，人口/SOVI固定四分组、医院/PGA、tier及独立理由、原54失败分类、DS/RS静态proxy footprint；`source_gate_run`和`legacy_W_modified`均False。

输入定位：08的四个CSV提供官方relation/utility/role/失败证据；06 `R1_310_CLOSURE_DATA.npz` 的 `station_ids/tract_ids/W` 提供legacy矩阵；06 `STATION_CONNECTION_DECISIONS.csv` 提供B状态和冻结CEC名称；05 `R1_310_STATIONS_QA.csv:key15` 定义固定比较名单，`R1_310_INPUT_READINESS.csv:PGA_2pc50_g`提供已有站点PGA。`Data/hospital_with_tract_expanded.csv:GEOID/OSHPD_ID/is_911_receiving`用于医院记录；`Data/Tracts_Within_Expanded_Area.csv:wkt_geom`用于静态centroid。

复算顺序：按NPZ的tract IDs对齐08表→strict SCE筛选→relation按tract+normalized name去重→取得M/U和registered B计数→按§4公式构建两份独立静态数组（无定义行NaN）→按人口加权汇总；公共域对照仅取W2有效的689行。top1按`(-weight, station ID)`排序，最大值并列容差1e-12。L1=`sum(abs(u-v))`；one-hot按正权重数严格等于1；effective count=`1/sum(w²)`。没有将任何静态数组写回旧输入。

R1 sorted IDs SHA256仍为 `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5`。

06 NPZ SHA256仍为 `7f44b95426ce92c7343d373906efd894fe995347bb0433eba3effc79636e00d0`。

primary PGA grid `Data/MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv` SHA256：`e9a7fe19d39c67708dfe1915a4878fe4a01aa5d6e8a49b5b0b5126c412ec6bef`；插值源码 `IDW.py` SHA256：`fe45f3dfa260a2af0540837671d3eba7f79a2b728072097d67e4682d4c6018e4`。既有数据年份并未因本轮计算更新。

本轮证据等级：已执行静态矩阵/覆盖分析，未执行任何恢复模型；数值完整性验证不等于设施接线、客户份额或模型物理真实性已验证。

独立读回验证已通过：全部817个candidate集合与W1/W2逐行公式、689共同域集中度、2315个tier规则、54个冻结失败标记、人口/医院对账及全部所读冻结文件hash均一致。原310 IDs与21-source定义未改。CSV的NA/空白表示方案无定义；布尔列按True/False解析，不能把非空字符串当布尔真值。

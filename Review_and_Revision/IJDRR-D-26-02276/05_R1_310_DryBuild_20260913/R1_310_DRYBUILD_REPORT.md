# R1 310-station topology + dependency dry build

**结论：CONDITIONAL PASS；恢复模拟继续 STOP。** R1 的310站能通过现有线路几何形成设施级网络，不存在大量无法注册或被迫长距离注册的站；但“310/310注册”掩盖了局部电压／线路接入问题。尤其是 AIRCHEM 注册到不匹配电压的图节点、4个无source站承接18个tract的全部依赖，以及一个道路入口不能返回基地。这些问题必须在下一次局部接入核查与dry build中关闭，不能直接进入32×4。

本轮没有运行damage/repair sampling、crew dispatch、restoration、MC、GA或任何策略／社区恢复比较。**未修改R1 eligibility、任何原始源码、旧92/318或旧W；没有新加source、人工补边或调整snap阈值。** 1/6/12/36 h保持冻结的未校准on-site action duration假设，本轮未使用它们。旧恢复结论没有被转移到310站模型。

## 1. 冻结输入和真实执行链

父提交 `87d9b6c287eb3537e5b893e395eb348d8678818b`；工作分支 `revision/r1-310-dry-build`。使用上一轮 [R1名单](../04_Provenance_Decision_20260913/STATION_SELECTION_COMPARISON.csv) 的 `new_R1_selected=True`，没有重新选站：310唯一ID，共同83、新增227；key15保留15/15，既定source proxies保留14/14。没有发现需要更改R1实现的数据处理错误。

| 冻结对象 | SHA-256 |
|---|---|
| 310 ID，字符串升序、换行分隔、末尾换行、UTF-8 | `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| 本次站点输入序列化快照 | `7e170d725742d3ea6b5d49c44e7ed2f568765b043e75309cf83f25cc704e3589` |
| 上轮selection comparison CSV | `5a69f390bdf3e105436fbd1c864b55e138059952d099101fd4a72572a793bbc6` |
| 固定4260条上游 `../01_Source_Data/CA_substations_MERGED.csv` | `9036e1dbf192e853ff2fa30c615086f7f95f208bf1e314413c6aac8900ac90eb` |

实际执行：冻结310 ID → 从4260 inventory取原始坐标、电压与owner → 原始 `Data/TransmissionLine_CEC.shp` → 3310投影、站点bbox外扩50 km筛选相交线路、explode → endpoint primary/secondary snapping → protected junction cluster snapping → 75 m endpoint merge → 10 m through-line split／既有projection connector逻辑 → attribute-scoped线路MultiGraph → 250 m内最近图节点注册 → 每站Dijkstra／intermediate blocking → 新设施图 → 新310维W → 输入QA。

没有将旧318条边输入这条构图链。旧edge CSV仅在新物理图完成后载入用于逐边分类。旧W只用于结构对照；新W从310站重新计算。只在新driver内逐源保存Dijkstra结果，避免同时保存310套全图路径；调用原始direct-link函数，未改变其最短路／去重规则。

执行证据：[r1_drybuild.py](r1_drybuild.py)，`inputs/build/qa/inspect_geometry`；原逻辑 [Topology_and_Weight.py](../../../Topology_and_Weight.py#L2028) `build_topology_wrapper`、L2162 `calculate_connectivity`、L2331 `compute_direct_links`；[topology_outputs.py](../../../topology_outputs.py#L17) `build_W_matrix/apply_min_weight_threshold`。原源码、旧站表／edges／W、tract/source文件及线路sidecars的运行前后SHA断言全部通过。完整hash、参数、日志、软件版本和小规模几何记录存于 `R1_310_BUILD_DATA.npz:metadata_json`。

交付包含所需6个核心文件；另加三项必要复现材料：driver、实际W及内嵌audit的NPZ、逐条318旧边原因CSV。没有额外恢复结果、ranking表或装饰图。

## 2. Station registration：末端距离很小，不等于线路关系已验证

**310/310注册，0未注册；没有station共用同一个图节点。** 308站在250 m内存在多个候选图节点，通常是同一线路折点；这不等于存在多个可用变电站接入点。CAMERON 307274有两个完全等距的attribute-scoped候选节点；现有KDTree顺序决定选中66/69 kV scope，需在局部接入核查中明确tie处理，不能把顺序选择视为电气证据。

| 距离或处理 | 227 new-only | 83 retained |
|---|---:|---:|
| 最终station→graph距离中位数，m | 0.0395 | 0.0390 |
| 最终距离P95，m | 0.0594 | 0.0573 |
| 最终距离最大值，m | 124.218（AIRCHEM） | 15.223 |
| 原始线路最近距离中位数，m | 2.980 | 6.455 |
| 原始线路最近距离P95，m | 15.349 | 42.358 |
| 原始线路最近距离最大值，m | 53.852 | 132.028 |
| 使用endpoint secondary的站数 | 12 | 16 |
| 至少一处endpoint原位置移动>150 m的站数 | 65 | 32 |
| 至少一处endpoint原位置移动>250 m的站数 | 33 | 15 |

最终注册距离 >150 m、150–250 m、>250 m均为0；**这不能与线路端点移动混用**。原pipeline允许150 m primary、375 m secondary／protected cluster，另有300 m以上更严格的margin/ratio guard；没有本轮放宽阈值。最初端点primary接受495次、secondary54次、secondary拒绝4次。后续protected处理可在站坐标形成图节点，因此近零最终距离部分是算法构造的结果。共有97站出现>150 m端点移动，48站>250 m，最大371.989 m（MCNEIL 308793）；必须作为显式不确定接入记录保留，不能宣传成厘米级定位精度。

new-only没有普遍更远的原始线路距离，也没有更高的长端点移动比例；其最大最终注册距离来自单个AIRCHEM。该结果为描述性全样本比较，未进行没有必要的显著性检验。

全部310站的坐标、注册node、primary/secondary/protected次数、原始线路距离、候选数、owner／voltage flags在 [R1_310_STATIONS_QA.csv](R1_310_STATIONS_QA.csv)。28个secondary站可直接筛选 `endpoint_secondary_count>0`；原始3946条端点记录在NPZ的 `endpoint_audit`。`registration_method`描述线路处理来源；实际最终注册函数始终是250 m内最近图节点，并没有另一个电压保护的fallback算法。

### 必须处理的局部接入问题

| station | 记录／图节点证据 | 当前判定 |
|---|---|---|
| 308336 AIRCHEM | 站点MAX/MIN=66；原始66 kV线路距53.852 m；实际最近图节点距124.218 m，属于220/230 kV | 确认的输入兼容性冲突；final registration只看几何，不能将其当作已验证的66 kV供电接入。需查66 kV线路接入位置及站记录，不得直接提高threshold |
| 303265 UNKNOWN303265 | MAX=230且inferred；图节点66/69；原始66线路距7.502 m；最近230线路约2.57 km | 电压字段／设施角色需核实；它承接81,681人口权重、21个tract的全部依赖，是高价值局部问题 |
| 301479 RENO | inventory120 kV；图66/69 | 元数据冲突；不能仅靠距离作决定 |
| 304137 HALLDALE | inventory138；图115及66/69；附近原始LADWP115和SCE66线路 | 旧retained站也有问题，不能将retained自动当真值 |
| 304338 TIDELANDS；305021 UNKNOWN305021 | inventory230且inferred；图66/69 | 需要证据决定电压／接入关系 |
| 303487 UNKNOWN303487；306152 OLIVE；306489 SYLMAR EAST | 站owner LADWP，注册节点观测到的线路owner为SCE系；电压有匹配 | owner差异是review flag，不直接证明错误；可能涉及接口／ownership记录。SYLMAR EAST是key15和既定source，未擅自改变角色 |

6个voltage mismatch、3个owner mismatch是独立检查，不把“SCE 66→SCE 230电压差”再次算owner差。最终nearest registration没有执行这些guards；guard只在部分线路处理环节生效。[Topology_and_Weight.py](../../../Topology_and_Weight.py#L1487) `_substation_voltage_families`、L1506 voltage guard、L1531 owner grouping；CSV保留原始MAX/MIN和MAX_INFER，未用结果修正它们。

## 3. 新graph与旧边变化

| 构图结果 | 数量／处理 |
|---|---|
| through-line split前后线路parts | 1,973 → 2,082；97条被split、108 cut points、1个既有规则生成的projection connector |
| 物理MultiGraph | 68,060 nodes；69,653 edges |
| minimum-weight collapse后物理graph | 68,060 nodes；69,145 edges；508条平行边表示被折叠 |
| 设施图 | 310 nodes；**1,061 undirected direct edges** |
| 设施组件／孤站 | 4个，大小306/2/1/1；2个isolated stations |
| self loops／重复direct rows | 0／0 |
| articulation stations／bridges | 36／35；ID列表保存在NPZ，未解释为实际电网可靠度 |
| owner／voltage保护 | protected cluster compatibility blocked29，snap guard blocked28；2,149 shared coordinate被attribute scope隔开 |

split诊断日志计数为5条compatibility blocked；函数级计数还有31次station-voltage拒绝和3次endpoint owner/voltage拒绝。这些发生在不同候选循环，**不可相加成35或更多“被删除电气边”**。逐类原因在 `metadata_json.guard_counts`。沿用原源码4处线路属性override（3处LA BREA、1处Barren Ridge）；本轮没有新增，也未把继承override当作新的独立验证。

direct link是两站在选定最短物理路径上没有内部已注册站／相容projection anchor；parallel paths不作为独立设施边保留，MultiGraph平行边取minimum weight。一个最短路被阻挡后，函数不搜索另一条绕开中间站的更长路径。因此1,061不是实际线路回路数，也不是全部可替代电气路径数。站点protected node允许多个电压／owner线路在站点相接，仍是抽象接口假设；没有功率、容量或潮流验证。

| old318原因分类，穷尽且互斥 | 数量 |
|---|---:|
| 新图仍为direct edge | 115 |
| 因R1排除端点站，旧边不适用 | 56 |
| 新最短物理路径被new-only intermediate station阻挡，存在设施链 | 145 |
| 重新处理后由retained intermediate station阻挡 | 2 |
| 两端仍eligible但物理图彻底断开／未注册／其他未解释消失 | 0 |

新direct links中946条不属于old318。**145条中，143条可逐段对应“同一新物理路径上的注册站序列”，可明确称几何上拆分；另外2条涉及projection anchor，须单独保留限定。** 这2条为300105–305984和300105–307564，均涉及310294，其projection在路径上，但注册点不在该路径节点序列中；存在经310294的设施链，不等于已经证明与原路径逐段完全相同。详见 `exact_registered_path_chain`、`projection_internal_ids`、`facility_chain`，不要把145全部表述为电气上确认的合理拆分。

另外2条retained blocking：301156–308494经300429；303344–309703经302923。全部318条的原因和新物理路径WKT在 [R1_310_OLD_EDGE_QA.csv](R1_310_OLD_EDGE_QA.csv)。不能由新图倒推旧长边必然错误，变化还包括重新snapping／endpoint processing。

## 4. Source结构和几何抽查

| component | station count | source count | source IDs／无source成员 |
|---|---:|---:|---|
| 1 | 306 | 14 | 300829、301541、304450、305984、306489、307039、307373、307693、308540、308581、309553、309569、309703、310199 |
| 2 | 2 | 0 | SERFGEN 303547；NAVY MOLE 307683 |
| 3 | 1 | 0 | RINGMILL 306980 |
| 4 | 1 | 0 | UNKNOWN309598 |

14/14 source均注册；没有大型source-less组件，也没有一个source单独支撑极小组件。**这4个station组件与物理线路图中含站组件一致**，不是direct-link导出阶段新制造的孤站。但仍不能把它们理解为真实独立供电系统。

4个无source站获得18个tract的全部W依赖，涉及人口78,811：component2为3个tract/8,101人；RINGMILL为2/10,049；UNKNOWN309598为13/60,661。这里是静态人口权重，不是停电人口或恢复结果。其source不可达在没有damage sampling时就已存在，不能让后续模拟把这一输入边界问题误表现为灾后恢复负担。

局部几何检查：SERFGEN/NAVY MOLE线路组件距source组件最近图节点gap14.834 m；RINGMILL187.334 m；UNKNOWN30959842.952 m。**这些是节点间最近gap，不是已发现的漏接线路，也不是补边许可。** UNKNOWN309598附近230 kV干线与66 kV支线不能因靠近而自动连接。

new-only名称flag仅为：301215 PALOGEN、301318 HILGEN、302865 ICEGEN、303277 FEDERALGEN、303364 SIGGEN、303473 THUMSGEN、303547 SERFGEN、303622 CARBOGEN。没有升级成source。REDONDO1 308844另保留generation/interface角色核实事项；本轮无容量、在役发电或net-import证据可证明其应加入source set。source completeness仍是模型边界，14/14保留不是完整性验证。

实际完成32个重点站的原始近邻线路／metadata检查，包含全部key15、largest new dependency站、最大snap站和全部source-less站；13条旧边的几何路径检查包含固定seed20260913抽样5条、最大blocker数4条及key15端点4条。记录见NPZ `station_geometry_spot_checks/old_edge_geometry_spot_checks`。例如ALAMITOS307039–310179经过9个new-only intermediate stations，注册站就在重建几何路径上；这些站离原始线路约0.86–10.42 m，未出现记录的voltage mismatch。涉及CENTER、LIGHTPIPE和RIO HONDO的抽查也有逐路径记录。

![Network and local geometry QA](R1_310_NETWORK_QA.png)

地图中direct links沿实际路径绘制，不用两站直线代替；绿色为三条被拆分的旧端点对在新图上的路径。肉眼检查没有发现凭空跨区绘制的直线捷径。最长边GOODRICH303371–SYLMAR EAST306489约58.934 km、端点直距40.386 km，是沿原有北部线路走廊的路径，且属于保留旧边；不是证明电气连通合理的依据。AIRCHEM的错电压节点选择和MCNEIL约372 m端点移动在局部图中可见，已列问题，未隐藏。

## 5. 新W：数值完整，但更集中，且暴露局部无source依赖

采用冻结公式：EPSG:3310 tract几何centroid → Euclidean nearest access station → `access_distance + physical-network shortest distance` → IDW exponent2 → 首次归一化 → 删除权重<0.03 → 再归一化。不是单纯Euclidean IDW，也没有加入utility boundary。cutoff规则、最低距离0.001 km均不变。当前实际冻结tract文件与旧mapping包含**2,315 tracts**，不是稿件约2,291；本轮没有删tract来接近稿件数字。

W **2,315×310**；总人口9,066,522；全部row sum≈1，最大误差4.44e−16。negative/NaN/Inf、zero rows、raw fallback和cutoff fallback均为0；所有access stations已注册。cutoff前702,903个nonzero，后6,030；可达候选数1–306，中位306；最终每tract非零站1–8，中位2。各tract的数值检查、候选数、距离和浓度均保存在 [R1_310_DEPENDENCY_QA.csv](R1_310_DEPENDENCY_QA.csv)，实际W与cutoff前W保存在NPZ。

| 浓度／结构 | 旧92 W | 新310 W |
|---|---:|---:|
| top1权重中位数 | 0.7824 | 0.8424 |
| top1权重平均值 | 0.7627 | 0.8044 |
| top3累计权重平均值 | 0.9489 | 0.9736 |
| effective station count中位数，1/Σw² | 1.5711 | 1.3733 |
| 非零站数中位数 | 3 | 2 |
| 单站weight=1的tract数 | 234 | 433 |
| max weight≥0.95的tract数 | 332 | 505 |
| old key15总人口加权dependency share | 19.8485% | 7.7164% |
| common83总人口加权dependency share | 92.9028% | 33.7952% |

1,588/2,315个tract的top1改变（68.60%，承接69.80%总人口）；其中1,431个原top1仍属于common83。这不是仅由9个排除站解释的变化。547个tract非零站数增加，1,196个减少，其余572不变；因此不能说“增加227站使大部分tract分散到更多站”。最近access距离中位1.714 km、P95 5.049 km、最大9.488 km；最终权重加权network距离中位0.450 km、P95 1.517 km，最大保留network距离10.669 km。最近access的优势与cutoff共同形成强局部集中。

**没有全区域单站支配的数值病态hub**：最大站人口权重share为2.8004%。但单站支配tract增至433个，且其中存在无source／电压待核站；这意味着数学完整性通过，物理解释尚未全部通过。不能仅因row sum=1便批准pilot。旧key15虽全部保留，其权重总量明显变化；例如CENTER约239,771→21,164、RIO HONDO309,500→6,916、LIGHTPIPE220,897→22,522。所有common83的逐站变化在station QA中；这些是结构权重转移，不能当作策略／恢复贡献变化。

### Stations receiving the largest modeled tract-dependency share under the rebuilt mapping

以下仅列new-only top20。人口权重分配量为Σ population×W，不是实际客户数、utility service territory或“critical substations”。

| ID | name | 人口权重分配量 | 总人口权重share |
|---|---|---:|---:|
|304217|STATION S (VAN NUYS)|253,902|2.8004%|
|306012|STATION P (MARKET)|211,889|2.3370%|
|300589|STATION 54|190,357|2.0996%|
|306152|OLIVE|85,004|0.9376%|
|303487|UNKNOWN303487|81,945|0.9038%|
|303265|UNKNOWN303265|81,681|0.9009%|
|306926|BJ|71,740|0.7913%|
|310458|UNKNOWN310458|70,189|0.7742%|
|308716|GARFIELD|67,733|0.7471%|
|304857|ALHAMBRA|66,152|0.7296%|
|302381|FAIRFAX|65,962|0.7275%|
|301489|BULLIS|63,935|0.7052%|
|300393|CALDEN|63,537|0.7008%|
|309116|FERNWOOD|61,253|0.6756%|
|305781|UNKNOWN305781|60,932|0.6720%|
|309598|UNKNOWN309598|60,661|0.6691%|
|302401|RAMONA|60,354|0.6657%|
|303995|CITRUS|55,314|0.6101%|
|306794|SOUTHGATE|55,008|0.6067%|
|303858|SS3144|54,985|0.6065%|

## 6. Downstream input readiness与9个old-only

**Hazard／fragility字段可构建，travel还不能直接用于完整dispatch。** [R1_310_INPUT_READINESS.csv](R1_310_INPUT_READINESS.csv)逐站保留字段与检查结果。

- 确定性PGA input interpolation：使用 [IDW.py](../../../IDW.py#L29) 的现有4个hazard grids及L147 `idw_core`，11 km、k=8、power2、ln(g)插值后转g；Northridge、SanFernando、LongBeach、2pc50均310/310得到有限正PGA。只是输入覆盖检查，没有生成任何damage state或新scenario结果。网格hash和邻点数均保存。
- Fragility：沿用父目录 `02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py` L164 `assign_fragility`；low255、medium53、high2；active anchored参数及旧unanchored列均有有限正mu/beta，310/310完整。**152站MAX_INFER=Y**，是上游推断电压，不是本轮补值。没有额外missing-voltage fallback；字段完整不等于每站电压／anchoring已获得实证验证。原函数全文及SHA、310条原始站输入快照内嵌NPZ，便于Git上的审阅。
- Road：只读 `Data/la_drive.graphml`，174,483节点、460,875有向边；所有边有非负travel_time/length/speed_kph。采用与OSMnx未投影图nearest_nodes相同的haversine选择；仅检查从原11个基地的有向可达性，未计算310×310 travel matrix。310/310可从至少一个基地到达；**WESTHILL305751所选road node123535245不能返回任一基地，其strong component仅1节点**。这不是repair dispatch结果，而是入口选择／道路方向性问题。
- Road snap中位83.30 m、P95 357.40 m、最大1,406.12 m（NAVY MOLE）。>500 m的5站：SHELLWATT300950、HILGEN301318、UNKNOWN302923、HAYNES307373、NAVY MOLE307683。500 m只是本轮显式审查flag，未用来更换node或排除站；厂区入口、access road覆盖仍需核实。
- Population/hospital/topology features：新W可生成310维population dependency；医院输入121条、103个独立hospital-containing tracts，可生成dependency-weighted hospital-tract coverage及非零链接数。不是医院数量／床位容量／医院功能。本轮仅保存这些输入分数及degree、unweighted closeness、source flag，没有rule priority sequence、GA fitness evaluation或GA优化。来源：[hospital_with_tract_expanded.csv](../../../Data/hospital_with_tract_expanded.csv)、新W；driver `qa`。

8个STATUS=NOT AVAILABLE站全部仍为 **status still unknown**：SAN FERNANDO301636、WINDSOR HILLS301745、THERMAS305780、LA MIRADA306369、STANHILL306444、UNKNOWN306768、UNKNOWN307832、MOBILOIL308806。保留的MERGED、CA_substations、LA_County_SUBSTATION表没有提供更可靠的active/inactive状态；CEC2022/OpenBASIN记录含这些站，但没有STATUS字段。**SAN FERNANDO在CEC2022存在66 kV/SCE记录，仍不能由“地图中存在”升级为confirmed active。** 当前没有confirmed active或confirmed inactive的新增证据，8站保持R1 exclusion。OLINDA306279虽上游为IN SERVICE，仍因研究区外／非source而排除。逐项来源保存在NPZ `old_only_status_review`，不进行额外sensitivity。

## 7. 决策与下一步门槛

这不是FAIL：310站与线路inventory并未发生整体不相容；主要组件包含306站与全部14source，W无数值损坏，旧边绝大部分变化有路径解释，hazard字段不缺失。也不是PASS：若立即运行恢复，局部接入／无source边界／road方向问题会被传播为看似科学的恢复结果。

**下一轮唯一工作包：关闭“设施接入”问题后重新dry build。** 保持310-ID集合与当前输入冻结，以同一局部证据表解决：(a) AIRCHEM等6个电压冲突、3个owner flags和CAMERON等距scope；(b) 4个无source站的实际线路／角色／系统边界，重点UNKNOWN309598；(c) 310294 projection与2条旧端点对路径语义；(d) WESTHILL及长road snaps的可出入道路入口。允许的处理是有来源的元数据／几何修正，或明确且可审阅的模型边界；不允许为了source可达或可dispatch而补线、升source、删eligible station或任意延长snap。

若资料仍不足，无source组件必须明确保留为未解决的输入边界，不可默默计入可解释的灾后服务恢复。任何修正都保存本轮before数据，在另一个目录重做topology/W/input QA并给出变化原因；此时仍不运行32×4。门槛关闭、dry build正式PASS后，才可准备新task维度、道路矩阵、rule sequences、新310维GA sequences与repair-duration sensitivity design，然后申请进入310版32×4；29 crews更晚。

执行复现入口为 `python -B r1_drybuild.py --build --qa --inspect`，需要既有Python地理环境、Git LFS原始Data、父目录上游inventory／fragility脚本及CEC GDB。driver会拒绝覆盖已存在的临时checkpoint；独立复现应使用新临时目录。`--qa/--inspect`只复用本轮新checkpoint做输入计算和地图，不会重跑topology或任何恢复逻辑。NPZ包含W、W_before_cutoff、station_ids、tract_ids、population和metadata_json；不是pickle，不需要运行模型即可读取。父目录依赖不应误以为都在本项目Git根目录内；小站点输入、fragility源和status检查证据已内嵌NPZ供远端审阅。

### 最后12项答案

1. **实际注册：310/310。** 最终最大snap124.218 m；继承端点移动另外记录，最大371.989 m。
2. **新edge count：1,061**，沿原线路重建，未复用318作输入。
3. **components：4**，大小306/2/1/1。
4. **每component sources：14/0/0/0**；完整source IDs见上表。
5. **无大型source-less组件**；4个无source站影响18个tract的静态dependency，不能忽略。
6. **旧318中143条可逐段确认被新增注册中间站拆分；另2条projection blocking需限定**；115保留、56端点排除、2由retained站阻挡。
7. **W数值完整**：2,315×310，归一、零坏值、零fallback。
8. **无全区域支配hub；有更强局部集中**：433个one-hot tracts，含未解决的无source／电压冲突输入。不能称已完成物理验证。
9. **Hazard/fragility字段310/310可形成；travel尚未完整**：WESTHILL无返回路径及5处>500 m入口需核查；152站电压为上游inferred。
10. **CONDITIONAL PASS，恢复STOP不解除。**
11. **唯一下一工作包：证据驱动的局部设施接入／系统边界修正，然后再次dry build。**
12. **本轮不允许准备或运行310版32×4的计算任务**；只有局部门槛关闭并正式PASS，才按用户规定顺序准备新输入与pilot。旧结果保留为冻结旧模型结果。

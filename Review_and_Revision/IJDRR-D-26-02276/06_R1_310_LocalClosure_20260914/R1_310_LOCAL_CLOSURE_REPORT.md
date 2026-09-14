# R1-310 local closure — FAIL / STOP remains

本轮把局部接入规则和未解决问题变得可审阅，但**没有取得进入恢复计算的合格输入**。统一电压规则得到306/310个兼容注册；4站保持未解决。正常 source gate 下，54个 tract 的无震害服务值为0，涉及220,426人口。这是 baseline 输入失败，不能解释为地震损失，也不能通过重新归一化掩盖。

完成范围：一次完成的修订 dry build、无震害单时点 source gate、统一道路接入 QA、310294 的局部几何/接口检查。**没有运行 damage/repair sampling、dispatch、GA、MC、32×4、29/114 crews、恢复或社区结果分析。** 没有删站、添加任意线路、放宽250m电网注册半径，或根据恢复结果改变规则。旧92模型、05目录和原始代码/输出均冻结。

目录日期采用2026-09-14 UTC；本地执行日期为2026-09-13 PDT。基线父提交：`0a9e763cde7be7be7fc22c7e8656399a66e425f6`；工作分支：`revision/r1-310-local-closure`。

## 1. 本轮输入、规则和实现边界

310 IDs直接复用05的冻结记录；有序ID列表（每ID后一个换行）的SHA-256保持：
`d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5`。

| 环节 | 实际执行与证据 |
|---|---|
| 原线路重新构建 | `local_closure.py:151 build` 调用根目录 `Topology_and_Weight.py:2028 build_topology_wrapper`；从 `Data/TransmissionLine_CEC.shp` 及310站开始；05的1061边仅作比较 |
| 注册 | `local_closure.py:60 register`；复用 `Topology_and_Weight.py:1487 _substation_voltage_families` 与 `:1891 _node_attribute_signature` |
| direct links / projection | 根目录 `Topology_and_Weight.py:2331 compute_direct_links`；原算法未修改 |
| dependency | 根目录 `topology_outputs.py:17 build_W_matrix`、`:108 apply_min_weight_threshold`；p=2、cutoff=0.03不变 |
| baseline | `local_closure.py:137 baseline_gate`，AST单独提取根目录 `C257H_Project_Main.py:994 apply_source_gate_to_substation_series`；310站raw=1，threshold=0.5，明确传入24个proposed sources；不导入/执行主模型 |
| road | `local_closure.py:233 road_access`；原 `Data/la_drive.graphml`、原11个基地；只做节点/SCC可达性，没有310×310 routing |
| 局部核查 | `local_closure.py:290 finish`；读取本轮构建检查点，不执行恢复模块 |

完成的构建之前有一次导出失败：新增driver读取CEC plant表时，`set_index` 默认移除了后续需要的 `CECPlantID` 列；修正为 `drop=False` 后用完全相同的科学规则重试。它是新QA驱动的导出错误，不是原模型错误，不涉及参数选择。不能将本轮描述成“只有一次程序执行尝试”。

原模块没有改动；全部差异限于本目录。三个原始模块、线路各sidecar、旧W/边/源文件及05目录逐文件哈希均记录在 `R1_310_CLOSURE_DATA.npz:metadata_json` 并在构建后检查。

## 2. 全310站一致的电网注册规则

在250m内枚举节点；先要求站电压family与该节点**实际attribute scope**有交集。显式scope节点不借用同坐标其他scope的电压。多个兼容节点依次按距离（1e-7m数值舍入）、显式scope优先、稳定节点键选择；反转候选遍历顺序的检查对全部310站通过。没有兼容节点就保留unresolved，不使用不兼容fallback。Owner只作review flag。

这是“具有兼容电压scope的几何接入代理”，不是已验证的接线图。45个所选节点含多个电压family，沿用原物理图的设施/接口表示；未据此声称实际变压器、母线或ownership interface已验证。

**统一metadata证据优先级**：仅在原 `MAX_INFER=Y`、HIFLD_ID精确匹配CEC2022、CEC记录 `Source=CEC` 且 `Max_Voltage` 正值非缺失时，以记录值取代推断MAX。不是以最近线路电压反推站电压。CEC“记录值”也不等于现场实测。

本地依据：同级源数据目录
`../01_Source_Data/California Electric Substations (2022)/data/v101/*.gdb`，
layer `CA_Substations_Final`，字段 `HIFLD_ID/Name/Source/Max_Voltage`。
全部310站对应的原字段值在 `STATION_CONNECTION_DECISIONS.csv`；原始证据行也嵌入NPZ，
规范化证据SHA-256：
`b51acfc6002c725045c9c9fc04ddc7715ef7205ebef5c17b7aee24cba88a382d`。
这项外部GDB是复跑所需源数据，未把整个GDB复制进本交付目录。

只有5站数值改变，均230→66kV：

| ID | 原名 / CEC名 | 处理 |
|---|---|---|
| 303487 | UNKNOWN303487 / Station 67 | 采用CEC记录66；owner mismatch仍保留 |
| 304129 | UNKNOWN304129 / Airway | 采用CEC记录66 |
| 304338 | TIDELANDS | 采用CEC记录66 |
| 307512 | GRAYSON | 采用CEC记录66 |
| 308325 | VENICE | 采用CEC记录66 |

152站原带 `MAX_INFER=Y`；其中106站现在有上述CEC记录支持（101个数值相同、5个改值），46站仍仅有推断电压。原标记保留，没有把推断记录静默升级成实测。

注册结果和全部变化：

| 站 | 05注册 → 本轮决定 | 原因 |
|---|---|---|
| 308336 AIRCHEM | 220/230 scope、124.22m → 66/69 scope、130.44m | 统一兼容优先规则得到；66kV本身仍为推断证据 |
| 301479 RENO | 已注册 → unresolved | 120kV在250m内没有兼容scope；不能把附近66/69当作120 |
| 303265 UNKNOWN303265 | 已注册 → unresolved | 230 inferred；CEC MAX缺失；没有兼容scope |
| 304137 HALLDALE | 已注册 → unresolved | 138kV不等于附近115或66/69；没有有据的metadata更正 |
| 305021 UNKNOWN305021 | 已注册 → unresolved | 230 inferred；附近Sawtelle hydro点不证明本station的电压/接线 |

因此是**1站换到另一个节点、4站撤回不可信注册，共5项注册决定变化**，不是5站换到新节点。其余305站节点身份不变。

303487、306152 OLIVE、306489 SYLMAR EAST三项owner mismatch保留为review flag；39个已注册站owner缺失/不确定。全表owner_review另有2个未注册站也属于unknown，因此总unknown=41，不能和4个电压未解决项相加。CAMERON 307274原同坐标两个scope中，66/69为兼容项；确定性选择不再依赖遍历顺序。

## 3. 有限source完整性检查：24是本轮proposed proxy set，尚非获准的最终系统边界

这次没有把旧14个当作完整清单。系统性检查全部310站与官方CEC LA County plant inventory的空间候选（1km只用于发现），并形成明确的设施身份crosswalk。新增proxy要求：经人工核对的同设施身份、≤250m共址、CEC非retired且有正generation capacity、兼容电网注册。阈值是审查规则，不是已校准的电气接线距离。

官方数据：[CEC California Power Plants说明](https://catalog.data.gov/dataset/california-power-plants)、
[实际FeatureServer](https://services3.arcgis.com/bWPjFyq029ChCGur/arcgis/rest/services/Power_Plant/FeatureServer/0)。
查询 `County = 'Los Angeles'`，保存309条记录、全部字段、坐标及layer metadata于
`SOURCE_EVIDENCE_SNAPSHOT.json`；layer更新时间2026-06-12。
原快照SHA-256：
`a4ccee1a5590fda92c3aaaa6699d7037536042952491828fb92f6fd012b7892a`。

**匹配到发电设施，不等于确认它向该图节点净注入，也不证明blackstart、震后可用性、capacity adequacy或实际供电。** 本轮24个源是14个保留假设加10个有设施记录支持的generation proxies；非24个已验证真实电源。所有新源都在原主component，**没有一个用于填补四个旧source-less站点**。14与24在这个全功能连通图中的可达component相同；新增源没有掩盖baseline失败。

| 新增proposed source | CEC ID / 实际设施 | 距离m |
|---|---|---:|
| 300232 CENTER | G9222 Center Peaker | 132.20 |
| 301318 HILGEN | E0127 Puente Hills Energy Recovery | 28.66 |
| 302376 BREW | G1072 Irwindale Brew Yard | 56.95 |
| 302865 ICEGEN | G0084 Carson Cogeneration | 51.05 |
| 303473 THUMSGEN | G0925 THUMS | 35.49 |
| 306001 SAN DIMAS POWER | H0437 San Dimas Hydro Recovery | 26.48 |
| 306365 ARCOGEN | G0035 Watson Cogeneration | 144.26 |
| 306450 VERNON | G0894 Malburg Power Plant | 56.56 |
| 306473 MWD VENICE | H0541 Venice | 37.28 |
| 307512 GRAYSON | G0236 Grayson | 130.46 |

HILGEN另有[运营方设施说明](https://www.lacsd.org/services/solid-waste/energy-recovery-and-fueling-facilities/landfill-gas-to-energy-facilities/puente-hills-landfill-gas-to-energy-facility)支持实际generation/export角色；设计50MW与当前约23MW净输出不是同一量，本轮没有容量计算。

用户指定的其他generation候选：

| 候选 | 实际匹配/证据 | 当前决定 |
|---|---|---|
| PALOGEN 301215 | E0130 Palos Verdes Gas To Energy；CEC retired，2011年退役 | rejected current generation candidate |
| FEDERALGEN 303277 | G0203 NP Cogen；CEC retired，2001年退役 | rejected |
| SIGGEN 303364 | G0673 Norwalk/Wheelabrator；CEC retired，2018年退役 | rejected |
| SERFGEN 303547 | E0112 Southeast Resource Recovery；2024-04-01 retired；另见官方电气停运证据 | rejected contemporary source；2022历史角色另记 |
| CARBOGEN 303622 | C0002 Los Angeles Refinery–Calciner；当前retired/0MW | 不支持当前源；不以附近厂退役推断station本身停运 |
| REDONDO 1 308844 | G0490 AES Redondo Beach retired；官方证实2024-01-01机组移出运行 | rejected contemporary source；历史角色另记 |

REDONDO依据：[Water Board Order R4-2025-0184](https://www.waterboards.ca.gov/losangeles/board_decisions/adopted_orders/docs/0536_R4-2025-0184_WDR.pdf)，PDF p2 paragraph10。不能将2026状态回填成2022状态。

旧14源保留为已声明proxy，而非重新验证完毕。例如HARBORGEN 304450最近的retired Calciner点**不是已确认的身份匹配**，不能误读CSV最近点为源证据；其当代电气源角色仍待证实。ALAMITOS最近点是battery，也不能替代站点发电身份。CSV的 `plant_match_basis`、`generation_decision` 和 `import_decision` 将这些证据层级分开。

### 可复现boundary-interface候选规则

以固定2315 tract polygon union作研究区边界；找物理线路跨边界的位置。从注册站沿物理最短路径到一个跨界点，途中不经过其他已注册站，取最近的合格跨界路径。只产生**boundary候选**，不把centrality或“消除孤岛”作为依据，不自动判定进口方向或外部电源可用。

得到48个候选：8个本来就是旧source，40个仅为新boundary候选；**没有因此新增import source**。原6个import proxies中5个满足此first-interface规则，MESA 301541在310站表示下不是first boundary interface，但仍作为历史模型假设保留并标识。完整名单、跨界坐标和路径在 `SOURCE_ROLE_DECISIONS.csv`。

城市tract union有非凸边界/空隙，线路可能出界后重入；候选最远路径约44km，跨界本身不证明外部馈入。当前2010s/2022设施与线路记录、2026 plant状态并非一致的电气系统快照。**研究系统年份和外部energization假设还需要明确锁定；不能通过选择年份或升级候选让孤岛消失。**

## 4. 四个旧source-less站点：有据界定，尚未关闭服务边界

| 站 / component | 实际证据与分类 | 本轮处理 |
|---|---|---|
| SERFGEN 303547 | 当前Case C。CEC退役；官方FY25文件明确记录SCE断开66kV站和线路。2022时期确有发电角色，不能与当前混用 | 不添源/边；保留站及旧几何，标operating-epoch冲突 |
| NAVY MOLE 307683 | 与SERFGEN构成2站component；未找到独立可证实的当前外部供电或generation role | Case C；不能仅因依赖SERRF旧线路而假定有源 |
| RINGMILL 306980 | 66kV孤立站；附近主图约187m不证明存在电气tie | Case C；不跨空白补边 |
| UNKNOWN309598 / CEC Montrose | 66kV stub靠近230kV scope；约43m几何近邻不证明变压器或接口 | Case C；不把近邻当作接线 |

SERRF关键官方依据：[2026-04-03 City of Long Beach FY25 accomplishment record](https://www.longbeach.gov/globalassets/city-manager/media-library/documents/memos-to-the-mayor-tabbed-file-list-folders/2026/april-3--2026---citywide-accomplishment-dashboard-and-webpage---fy-25)，**PDF第28页，印刷页24/69，item1500**。下载原件并渲染核对：2024年11月decommissioning之后，SCE “de-energized the 66kV high-voltage substation and transmission lines”。PDF SHA-256：
`93039e5347b243f018dd111901a59ecbc7766c4dd734e76e2ece67dd807b90b2`。
[2022年SERRF会议记录](https://longbeach.legistar.com/View.ashx?GUID=A2822F48-AF5E-41DC-830F-6DF6DEF6C3CB&ID=11785590&M=F)支持其历史发电角色，不能用于证明当前仍通电。

Case C在本轮**不是**“删掉这些站/tract后继续”。它们留在310资产清单及诊断W中，整个W禁止送入恢复模型。若未来采用“只有已注册且baseline source-reachable的service stations可作dependency候选”，必须将其作为全2315 tract统一的新service-boundary规则，说明被排除资产与真实配电接入的关系，再完整重建W并复验baseline；本轮没有执行这种重分配，更没有只修18个tract。

## 5. 重新构建的topology与projection语义

| 项目 | 05 | 本轮 |
|---|---:|---:|
| eligible facilities | 310 | 310，ID完全相同 |
| registered facilities | 310 | 306 |
| facility direct edges | 1,061 | 1,040 |
| components | 306 / 2 / 1 / 1 | 302 / 2 / 1 / 1 / 1 / 1 / 1 / 1 |
| source counts | 14 / 0 / 0 / 0 | 24 / 0 / 0 / 0 / 0 / 0 / 0 / 0 |

新物理图68,061节点、69,145条collapsed simple edges。facility graph中的4个未注册站仍作为节点保留；components 3–6依次为301479、303265、304137、305021，components7/8为306980、309598。Component2仍为303547+307683。

相对05增加12条、移除33条direct edges；完整pair列表见NPZ `metadata_json.added_edges/removed_edges`，新边逐条见 `R1_310_EDGES.csv`。变更来自统一metadata/注册规则及相应重新预处理，原projection算法没改。**另发现9条direct path穿过HALLDALE的坐标，却不再经过其facility节点**：已在edge CSV的 `unresolved_site_coordinates_on_path` 和NPZ逐对标记。这种“未注册资产被物理路径越过”的语义不适合直接进入资产损伤/恢复模型，进一步支持STOP。

### 310294及两条旧路径

310294距66/69kV线路1.784553m；原预处理生成同长度几何connector。
registered node为 `(185606.8,-435384.4)`，
projection anchor为 `(185607.9,-435383.1)`。

两条物理最短路径实际注册站序列：

- 300105 → 307232 → 303715 → 305984
- 300105 → 307232 → 303715 → 307564

两者均经过310294的**projection anchor**，均**不经过310294的registered node**。facility表示则在303715之后插入310294。原 `compute_direct_links` 的docstring及内部逻辑明确同时阻断registered node和projection anchor；因此**不是代码背离现有算法定义的已确认bug**，而是一个影响电气含义的虚拟设施接口假设。若论文说只按实际registered-node sequence阻断，就与实现不一致。

只对310294的10个现有facility邻居做局部语义对照：撤掉它的anchor blocker会放出19个direct-link pairs、局部删除0个；全部19对在NPZ `projection_review`，**没有采纳到1040边网络，也不是全网projection sensitivity**。300105的两条旧长边即便忽略310294，仍有307232和303715作为中间站，不能简单恢复成direct links。

结论：算法行为已解释；尚无独立接线证据证明这条1.8m几何spur应当表现为串联facility。未重写最短路径算法，未宣称物理语义已经验证。实际“projection修正”造成的边变更数为0。

## 6. Directed-road access：WESTHILL关闭；长snap明确分型

统一规则：以原11基地所在directed strongly connected components为合格node集合（173,863节点）；对全310站，在固定500m内选最近合格节点，距离舍入后以node ID稳定tie-break；必须能与**同一个**基地往返。500m继承05长snap审查界限，是保守QA半径，不是经验校准的设施入口距离。没有改变道路方向、增加道路或计算完整travel matrix。

305站通过此几何node规则，5站没有半径内合格node。WESTHILL：
旧123535245、354.84m，是大小1的sink SCC；新11177952316、425.54m，可与原11基地往返，半径内共有5个合格候选。**1个实际换node，另5项是撤回旧长snap，不是改到更远的node。**

已对以下5站和WESTHILL逐个查看本目录QA地图：

| 站 | 最近合格node m | 最近现有道路几何 m | 几何判断 / 决定 |
|---|---:|---:|---|
| SHELLWATT 300950 | 838.45 | 78.47 | East Sepulveda Blvd很近；主要有简化图vertex间距问题，不能叫“缺路”；现有node规则下仍unresolved |
| HILGEN 301318 | 527.76 | 525.94 | Crossroads Pkwy South在设施北侧；landfill/发电设施内部接入未验证 |
| UNKNOWN302923 / Chevron Central | 782.15 | 781.42 | 工业设施内部与周边道路有明显间隔；缺少可证实入口/内部路线 |
| HAYNES 307373 | 545.18 | 427.53 | 道路几何在500m内但vertex更远；入口和内部接入未验证 |
| NAVY MOLE 307683 | 1,406.12 | 1,355.41 | Navy Way与站坐标之间的港区路网表示不完整；没有证实可通行connector |

“最近道路几何”来自局部原road inventory，不自动证明它的方向、出入口或车辆可达性；已接受305个node也只是几何代理，均未声称验证了真实facility gate。`ROAD_ACCESS_DECISIONS.csv` 保存完整before/after、候选数、往返基地ID及逐站review。

统一existing-node规则已经明确；5项接入证据未闭合。对SHELLWATT/HAYNES有价值的下一步是统一、方向保持的existing-road-edge projection/入口检查，而不是任意增大node半径。其他3项需要真实入口/内部道路证据。这些均不是本轮补造道路的理由。

## 7. W完整性与硬性无震害检查

冻结formulation仍然从EPSG:3310 tract几何centroid选最近站作access，距离为access几何距离+物理网络最短路；所有有限候选做IDW²，先归一、cutoff0.03、再归一。source set不参与候选选择。

| 检查 | 本轮实际结果 |
|---|---:|
| W dimensions | 2,315 × 310 |
| 非零数：cutoff前 / 后 | 682,879 / 6,042 |
| 最大row-sum误差 | 3.33e-16 |
| negative / NaN / Inf / zero rows | 均0 |
| cutoff全零fallback | 0 |
| unregistered access finite-self override | 36 tract |
| one-hot tract | 433 → 439 |
| 与05的W不同的行（L1>1e-12） | 613 |
| 最大row L1变化 | 0.695353 |
| baseline S最低值 | 0 |
| S < 1−1e−10 | 54 tract，220,426 population |
| 其余baseline S | 2,261 tract均≈1 |

**零fallback不等于映射有效。** 冻结 `build_W_matrix` 对target==access强制保留有限距离；36个tract选到未注册站后得到one-hot，而不是触发“all inf”的fallback分支。本轮明确标记该分支，没有修改旧公式或用归一化隐藏失联。

54个失败tract的S均为0：

| 原因 / access或top1站 | tract数 | population |
|---|---:|---:|
| 原source-less：RINGMILL 306980 | 2 | 10,049 |
| 原source-less：NAVY MOLE 307683 / SERFGEN component | 3 | 8,101 |
| 原source-less：Montrose 309598 | 13 | 60,661 |
| 新暴露的未注册access：303265 | 21 | 81,681 |
| 新暴露的未注册access：HALLDALE 304137 | 5 | 20,052 |
| 新暴露的未注册access：305021 | 10 | 39,882 |
| 合计 | 54 | 220,426 |

原18tract/78,811人口的问题仍在；增加的36tract/141,615人口来自严格注册后暴露的无兼容接入。RENO未注册但当前W没有人口dependency。每个受影响的GEOID、人口、S值和原因均在 `R1_310_DEPENDENCY_QA.csv`，筛选 `baseline_incomplete=True`；该表不是恢复结果。

原433个one-hot tract中：25个关联当前unresolved registration，15个关联其他source-less component，169个关联原 `MAX_INFER=Y` station。169中89现在有CEC记录支持、80仍是inferred provisional。各集合可能重叠，不能相加；均有逐tract列可核对。NAVY MOLE component的3个失败tract不是one-hot，因此原source-less总18与one-hot子集15不矛盾。

当前获得最大modeled population-dependency share的前5站：
304217 STATION S=253,431.59；306012 STATION P=212,638.19；
308991 STATION T=191,244.82；300589 STATION54=190,356.73；
303099 STATION D=171,112.91。它们是 `Σ population × W`，不是供电客户数、实际负荷或关键性判定；全310值在station CSV。本轮没有据这些值调整选站/接入规则。

## 8. 交付、可复查边界与下一步

核心CSV全部保留310 IDs或全部2315 tracts；本目录另保留实际W的压缩NPZ、官方plant快照和可重建driver，避免只交付不可复查的汇总。NPZ还保留component完整成员/源名单、所有新增/移除边、局部projection19对、HALLDALE9条路径、输入哈希。没有额外恢复结果或装饰图。

交付一致性检查实际通过：从交付edge CSV独立重建components，按其source可达性重算单时点W乘积，与导出baseline逐行一致；核对310有序ID hash、310/2315行序、CSV/NPZ值、非负/有限/归一、24源及全部54个失败tract；23个冻结原文件/05文件哈希未变，另核对road graph、source-gate module及本轮driver/官方plant快照哈希。运行环境为Python3.12.3、NumPy1.26.4、pandas2.2.2、NetworkX3.3。**交付一致性通过，不改变科学输入门槛FAIL。**

复现入口（仅在独立检查点路径/干净复现环境）：
`python -B local_closure.py --build`，
`--road`，
`--finish`。
需要原repo数据、05冻结NPZ及CEC2022 GDB；driver会拒绝覆盖已有本轮build检查点。Windows长路径用扩展路径前缀。地图只画线路/道路几何，不能单独验证电气接线或工业场区入口。

**当前唯一值得进入的下一项工作是关闭“服务接入边界”，仍不是计算新pilot**：先固定可辩护的系统年份与baseline供电边界；取得4个无兼容scope站和4个旧source-less站的电压/接线/服务接口证据，或明确提出全域一致的service-station资格定义。不能将重分配W当成证明这些tract实际由其他站供电。完成这项定义后才有必要再做局部输入dry check；同时按已定位原因补道路入口/edge access。无需全网电力潮流、全站百科搜索或新增恢复数字。

## 9. 最后12项直接答案

1. **registration rule是什么？** 250m内电压family兼容优先，实际attribute scope检查，距离/显式scope/稳定节点键择优；无兼容就unresolved；owner只flag，inferred电压保留证据等级。
2. **多少station改变registered node？** 1站实际换node（AIRCHEM），4站变unresolved，共5项注册决定变化。
3. **剩余voltage/owner flags？** 4个无兼容scope；3个已注册owner mismatch；39个已注册owner未知；46站电压仍仅有inferred依据。45个所选节点为多电压family接口，不能误称独立接线验证通过。
4. **source set是多少，为什么？** 本轮proposed24=保留14假设+10有generation设施记录支持的proxy；48个boundary候选未自动升源。最终系统年份/外部供电定义尚未批准，不能称24个已验证源。
5. **原4个source-less站如何处理？** 当前证据下均Case C；SERFGEN另有退役/断电证据，NAVY MOLE当前供电未知，RINGMILL/Montrose缺少可信接口。保留资产与诊断权重、停止下游，未补边/补源。
6. **baseline全部≈1吗？** 否。54 tract为0、220,426人口；其余2,261≈1。
7. **projection是bug吗？** 不是已确认的实现错误；是原代码明确使用的virtual interface假设，实际串联电气角色仍未验证。未改算法；局部撤掉anchor会放出19对，不采纳。
8. **WESTHILL和5个long snaps？** WESTHILL统一规则修正至11177952316；5个长snap明确flag，SHELLWATT/HAYNES存在vertex-spacing因素，其他3个需要入口/内部道路证据。
9. **topology变化？** 310 facilities、306注册、1040边；components302/2/1/1/1/1/1/1，source counts24/0/0/0/0/0/0/0；比05加12/减33边。
10. **W变化？** 仍2315×310、数值归一完整；613行变化，one-hot439；36个unregistered-access self overrides明确暴露。不是可批准的恢复输入。
11. **PASS / CONDITIONAL PASS / FAIL？** **FAIL**。剩余问题直接污染baseline服务与资产接入，超出metadata limitation，不能给conditional pass。
12. **允许310站32×4输入准备了吗？** **不允许。STOP保持。** 先完成有限站点/系统年份/service-boundary证据与统一接入定义，再dry check；不启动任务集、GA序列或恢复计算。

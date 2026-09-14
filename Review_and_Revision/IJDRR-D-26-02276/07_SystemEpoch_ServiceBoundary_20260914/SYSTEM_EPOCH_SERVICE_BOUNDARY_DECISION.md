# SYSTEM EPOCH / SERVICE BOUNDARY DECISION

**结论：UNRESOLVED。继续STOP；本轮不批准重新dry build或任何恢复计算。**

最重要的新发现不是baseline数值，而是保留线路主要来自2016年及以前的要素记录，不能因外层文件日期或CEC变电站包标题而称其为2022/2026运行网络。另一方面，独立资料支持SERRF在2022发电、HALLDALE的138kV记录、Ringmill的66/4kV配电角色，以及Montrose的34.5kV冗余线路；这些证据反对“把几何孤岛当作真实无电区域”，但尚未给出可批准的tract服务边界。

```text
MODELED_SYSTEM_EPOCH = multi-epoch infrastructure proxy
CORE_NETWORK_RECORD_WINDOW = predominantly mid-2010s:
    retained line feature records through 2016
    R1 station source/validation records from 2015–2019
    CEC station crosswalk package labelled July 2022
APPROVED_SINGLE_OPERATING_YEAR = NOT_ESTABLISHED
REFERENCE_YEAR_FOR_SOURCE_EVIDENCE_LEDGER = 2022
SOURCE_PROXY_SET_REFERENCE2022_PROVISIONAL = 25 IDs, review ledger only
APPROVED_SOURCE_PROXY_SET = NOT_ESTABLISHED
APPROVED_SERVICE_ACCESS_SET_C = NOT_ESTABLISHED
```

2022仅作为本轮历史source证据表的统一参照，因为它是保留CEC站点包唯一明确的provider版本年份；**它不是被选定为真实电网运行年，也不授权source activation**。不能将这个区别压缩成“模型已经改为2022”。source ledger保存可用证据，正式source boundary仍未获准。

本轮只读取冻结的06输入/QA、源数据metadata和有限目标设施资料，计算静态覆盖范围及SVI组成。没有重建graph、运行source gate、修改W、重新归一化、damage/repair sampling、MC、dispatch、GA、恢复、road优化或projection研究。旧310 IDs及06全部文件保持原样。父提交为 `9121e530814d791f4a403ea0f1f16902a483e506`。

## 1. 简短epoch证据表

位置以Git根目录为基准；`../01_Source_Data`与`../00_Project_Deliverables`是已保留的同级项目材料。

| 数据 | 实际保留证据 | 能够支持 / 不能支持 |
|---|---|---|
| R1 substation inventory | `../01_Source_Data/CA_substations_MERGED.csv` 的310个冻结ID：SOURCEDATE为2015年277站、2016年10站、2018年10站、2019年13站；最早2015-06-04、最晚2019-01-28；VAL_DATE同样截至2019。字段为毫秒时间戳 | 支持mid-2010s来源加后续校验；校验日期不是投运日期，也不是全系统状态快照 |
| CEC station crosswalk | `California Electric Substations (2022)/metadata/metadata1.xml`：caldate=July,2022；purpose为汇编CEC/HIFLD。原metadata有2021同步日期、2022包装日期 | 是2022发布的汇编，不证明其中每个站2022在役，更不自动把R1原HIFLD STATUS更新为2022 |
| Transmission inventory | `Data/TransmissionLine_CEC.shp`：6839条保留原线路；6822条Last_Edi_1为2016年，17条为1899-12-30占位值；Creator_Da有效范围2008–2016，最大2016-03-10，Last_Edi_1最大2016-09-06 | 核心几何最接近截至2016的资料。字段是编辑记录，不是线路实际投运/退役日志 |
| Line外层metadata | `Data/TransmissionLine_CEC.shp.xml`：ModDate/SyncDate=20231221，CreaDate=20240607，甚至保留feature-count=0的旧模板字段 | 这些不是当前6839条线路全部更新到2023/2024的证据；不能用文件/包装日期覆盖要素provenance |
| Sources/generation | 原 `Data/source_nodes_core_expanded.csv` 无operating-year字段；首次保留Git为2026-05-20的df1fc85上传。06官方CEC plant snapshot为2026-06-12状态，含StartDate但不是历史状态序列 | 旧14源隐含的是历史generation/import角色集合，不能恢复一个共同运行年。2026表不是2022 source inventory |
| Road | `Data/la_drive.graphml` graph.created_date=2025-04-16 21:53:18、created_with=OSMnx2.0.2 | 2025提取的道路代理；不是2016/2022同步道路状态。本轮未研究接入或routing |
| Tracts / population | 固定 `Data/Tracts_Within_Expanded_Area.csv`：2315 GEOID、9,066,522人口；具体TIGER/ACS release在保留派生字段中未恢复。GEOID能与NRI的2021-TIGER标识体系join，不等于几何版本已确认 | 不从housing文件的2022标签推断population年份；该population也不等于CDC2022 E_TOTPOP（仅21行相等）或NRI POPULATION（仅7行相等） |
| Vulnerability | 原服务权重用 `Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv:SOVI_SCORE`，对应NRI March2023 derivative；本地 `0b36f72c_NRI_metadata_March2023.txt` L2/8/9/37/88明确版本及CDC来源。另一独立输入 `Data/California.csv` 是稿件引用的CDC2022 | 本轮覆盖组成只用固定NRI-derived SOVI_SCORE，不混成CDC2022新指标。NRI底层CDC具体vintage在本轮证据中未进一步锁定 |
| Hospital | `Data/hospital_with_tract_expanded.csv` 的FACILITY_STATUS_DATE含2025记录及UCI HEALTH-LAKEWOOD的2026-03-07 | 单设施状态日期不是统一snapshot；不能不核对就说全部医院代表2022或2025-11-21 |
| Manuscript | 实际提交候选文本 `../00_Project_Deliverables/Audit_IJDRR_20260912_01/text/b81bdd6c_Manuscript_IJDRR.txt`：数据段L147、references约L709起；CEC/HIFLD/TIGER/ACS多为n.d.，标注2025-11-21 retrieved；CDC标2022 | **未声明单一system operating epoch**。retrieval date不等于运行年；历史地震scenario年也不是设施状态年 |

在限定本轮材料的查找后，没有找到足以证明“全部线路/站点同步到2022”的change log，也没有依据声称2026全系统。Population年份补核的ACS API请求没有返回可解析数据；没有凭近似数值猜年份，继续使用其冻结数值并记录vintage gap。

**A–D直接判断：** 核心资产最接近mid-2010s资料，但并非精确2016运行系统；transmission与substation可支持大致历史代理，不能支持同一已验证operating snapshot；旧14源无统一年份provenance；用2026退役状态否定2022-era发电角色确实产生epoch mismatch。多年代数据本身不使比较研究无意义，但限制了特定年份LA实际客户供电、当代政策推荐和完整公用事业系统的解释。

## 2. Source重新判定：保留历史证据，不把ledger当作已批准配置

`SOURCE_PROXY_EPOCH_DECISIONS.csv` 有66个唯一站点：旧14、新10、SERRF与REDONDO两个已提出的epoch案例，加上其余40个06 boundary候选。没有重新搜索全部310站。每行都有category、证据、reference year、06 membership、provisional membership和明确的 `activate_in_model=False`。

### 旧14源

| 站 | 2022参照下的证据/定位 | 本轮分类 |
|---|---|---|
| RINALDI 307693；SYLMAR EAST306489、WEST310199 | LADWP2022规划描述Barren Ridge–Rinaldi及Sylmar HVDC东/西设施；支持区域输入角色，但不是本裁剪图的容量/精确接线验证 | external import proxy，provisional |
| GOULD300829、MESA301541、RIO HONDO305984 | SCE历史资料支持实际高电压站及区域供电角色，未证明当前study-area裁剪边界上均为独立energized入口；MESA不满足06的first-interface筛选 | inherited assumption |
| ALAMITOS307039、EL SEGUNDO309703、HAYNES307373、LONG BEACH308540、SCATTERGOOD309553、VALLEY309569、STATION Q/HARBOR308581 | 实际发电设施身份有支持，CEC current记录的起始日期均早于2023；2022在役是可辩护的暂定判断，非完整历史发电档案或已验证注入点 | generation proxy，provisional |
| HARBORGEN304450 | CEC实际存在G0246 Harbor Cogeneration；06最近的retired Calciner C0002不是其身份确认。该station对应具体terminal仍未独立落实 | inherited assumption；没有因附近Calciner退役而拒绝 |

[2022 LADWP SLTRP，printed p2-47](https://www.ladwp.com/sites/default/files/2023-08/2022%20LADWP%20Power%20Strategic%20Long-Term%20Resource%20Plan_0.pdf)提供前一组区域接口依据；[SCE历史LCR资料Figure I-2，p7](https://www.sce.com/sites/default/files/inline-files/TrackI_SCELCRProcurementPlanPursuanttoD1302015.pdf)支持Gould/Mesa/Rio Hondo的系统位置，不证明外部source availability。旧6个import标签原本也不是“6个独立真实电源”的验证。

### 10个新增generation proxies逐项保留的证据

| Station | CEC identity | reference2022判断 |
|---|---|---|
| 300232 CENTER | G9222 Center Peaker | 暂定active，注入点未验证 |
| 301318 HILGEN | E0127 Puente Hills Energy Recovery | 暂定active；运营方描述历史发电，CEC记录StartDate不应等同整个场址首次投运日期 |
| 302376 BREW | G1072 Irwindale Brew Yard | 暂定active，注入点未验证 |
| 302865 ICEGEN | G0084 Carson Cogeneration | 暂定active，注入点未验证 |
| 303473 THUMSGEN | G0925 THUMS | 暂定active，注入点未验证 |
| 306001 SAN DIMAS POWER | H0437 San Dimas Hydro Recovery | 暂定active，注入点未验证 |
| 306365 ARCOGEN | G0035 Watson Cogeneration | 暂定active，注入点未验证 |
| 306450 VERNON | G0894 Malburg | 暂定active，注入点未验证 |
| 306473 MWD VENICE | H0541 Venice | 暂定active，注入点未验证 |
| 307512 GRAYSON | G0236 Grayson | 暂定active；site role不等于某一年代具体机组/容量全部相同 |

这些判断使用已保存的CEC官方2026记录中StartDate早于2023、非retired状态和06同设施crosswalk；**从这些信息推断2022具有连续运行可能性，不是找到了2022独立snapshot**。没有用2026容量回填2022，也没有新调colocation阈值。原始证据在06的 `SOURCE_EVIDENCE_SNAPSHOT.json`；[官方服务](https://services3.arcgis.com/bWPjFyq029ChCGur/arcgis/rest/services/Power_Plant/FeatureServer/0)。

### SERRF、REDONDO及epoch纠正

[Long Beach 2022-06-01 SERRF会议记录，PDF p4/printed p3](https://longbeach.legistar.com/View.ashx?GUID=A2822F48-AF5E-41DC-830F-6DF6DEF6C3CB&ID=11785590&M=F)明确讨论当时售电、2018年SCE合同到期后转入day-ahead market，以及延续运营的安排。SCE2019 Form1又列出SERRFGEN-LONG BEACH 66/12kV站。因此**2022的SERFGEN generation proxy有实质支持，06的2026-retirement拒绝理由不能跨时期沿用**。该项加入待审2022 ledger；没有激活源或声称3个tract已得到正确service mapping。

REDONDO在2024退役不否定其2022发电。仍不升为本轮provisional source：06的点位共址距离305.5m超过原新增proxy的250m筛选，且本轮没有新增station-terminal证据；不为了增加source而调整阈值。[Water Board2025 order，p2 paragraph10](https://www.waterboards.ca.gov/losangeles/board_decisions/adopted_orders/docs/0536_R4-2025-0184_WDR.pdf)支持2024-01-01退役界点。

待审清单25站=06的24+SERFGEN。类别为18 generation proxies、3 external import proxies、4 inherited assumptions。排序ID列表SHA-256（UTF-8，每ID换行含末尾换行）：
`2eb7c12b5cd30400a910f05f78ea4dad81969d6259fbe8f87bac280a767a4da8`。
这固定的是**审阅对象**，不是获准的模型source boundary。正式 `SOURCE_PROXY_SET_EPOCH_X` 仍不能诚实冻结为已解决。

### External-energization boundary：可定义规则，但目前未实例化为获准集合

可审阅且独立于恢复结果的候选规则如下：

1. 采用固定study-area polygon的**外边界**；内部空隙、线路短暂出界再进入，不直接视为外部供电系统。
2. 线路必须在目标operating-reference有存在/在役依据，并有可追踪的实际外部延伸；确定该corridor在域内的first electrically represented interface。
3. 使用已有source系统层级：高压输入corridor的220/230kV或更高voltage family，而非把所有低压边界穿越升为import。该选择必须先声明，不按baseline或centrality选站。
4. 明确假设外部网络在情景中energized；这是边界条件，不是已验证的净输入或容量充足。
5. 对不满足规则的旧import标记与新候选作同一处理，不能给旧6个永久豁免。

06的48条候选记录没有全部通过这套检验，尤其其polygon-union crossing含内部边界/重入可能，也没有逐候选目标年份、外部corridor状态和系统层级审阅结果。**本轮不将48个全部升级、不实例化新源集、不为了补孤岛选入口。** 按用户Part2的停止门槛，source boundary尚未闭合；以下coverage是概念方案评估，不是获准模型变更。

## 3. 只针对54个失败tract的六组证据判断

| 优先级/目标 | tract / population | 本轮独立证据及判断 | 处理 |
|---|---:|---|---|
| 1 UNKNOWN303265 | 21 / 81,681 | HIFLD SOURCE=OpenStreetMap，2015，230 inferred；CEC2022 exact-ID仍为Unknown、MAX缺失。有限identity/别名查找未取得可靠66kV站点证据 | 保持unresolved。不能从附近66/69线路反推站电压 |
| 2 Montrose309598 | 13 / 60,661 | CEC给出Montrose身份；GWP2022官方文件明确34.5kV Bel Aire–Montrose线路，并说明预防性停线没有客户失电、该线路承担冗余。它不是已证明的66kV独立供电孤岛 | 需局部subtransmission/服务接口资料。**34.5是已证实的线路电压，不自动等于station MAX**；不直接改MAX或补34.5/66/230虚构接线 |
| 3 UNKNOWN305021 | 10 / 39,882 | 230 inferred、CEC exact-ID Unknown/MAX缺失。Sawtelle hydro的存在不证明station identity。SCE文件中的Sawtelle-Santa Monica 66/16记录也没有与此ID的坐标/terminal crosswalk | 保持unresolved，不能用同名不同性质的设施填值 |
| 4 HALLDALE304137 | 5 / 20,052 | 独立LADWP/Leidos研究明确HALLDALE-C bus26260=138kV，支持原值，不支持直接替换成115 | 保持138记录；线路/接口表示需解决。06已标记的9条facility-bypass paths也不能靠排除5tract宣称关闭 |
| 5 RINGMILL306980 | 2 / 10,049 | SCE2019申报为Ringmill-Paramount，DU、66/4kV：确有配电站角色，非仅无名几何点 | 更可能是当前上游/配电表示缺失，而非已证实真孤岛；未找到足以补边的上游接线或精确tract服务区 |
| 6 SERFGEN/NAVY MOLE | 3 / 8,101 | SERRF2022发电及SERRFGEN66/12设施有证据；2024/2026退役不能否定2022 | source历史问题得到澄清，但provisional source尚未批准，且3个tract不等于已核实的SERRF/NAVY MOLE客户；未计为RESOLVED |

**关键primary sources和页码：**

- [GWP2022 Wildfire信息回应，PDF p6、printed p3](https://efiling.energysafety.ca.gov/eFiling/Getfile.aspx?fileid=52627&shareable=true)：34.5kV Bel Aire–Montrose及停线不丢失customer load。p7及后续表进一步说明冗余性质。已下载、渲染并读图，SHA `ef8cce3c657fc719b9999680bcf218b58f8ad361d633349e855358357a188798`。**并不能据此把13个IDW tract认作GWP实际服务区**。
- [SCE2019 Form1](https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/energy-division/documents/electric-costs/ferc-form-1s/sce-2019q4-ff1.pdf)：PDF p517/printed426.18 row1为Ringmill；p518/printed426.19 row2为Sawtelle、row7为SERRFGEN。已下载、渲染核对，SHA `14b3cd39dab48ee4b0e0c83baa226ab8c6bbb702fbd9e75104f7fa93b414a4be`。配电角色不等于取得feeder–tract映射。
- [CEC TN233302内LADWP/Leidos2014研究](https://efiling.energy.ca.gov/GetDocument.aspx?DocumentContentId=65793&tn=233302)：PDF p149/printed3-4/Table3.3，HALLDALE-C138kV。已渲染核对，SHA `cbba7d4b2b83b00b31423dc577553252bc4f91380a3e75d143ab42ca1c5221e6`。原HIFLD指向的 `10yta_2012_5.pdf` 本轮返回404；用该独立primary记录核查，没有伪称恢复了原引用文件。
- SERRF2022会议原PDF SHA `28102822b752c295dc61e339802a316462505e6a52d1255b7fe7cc1149219166`；历史发电role不等于精确station injection证明。

RENO仅附带记录：同一SCE2019文件PDF p516/printed426.17 row34有RENO-INDUSTRY 66/4记录，值得后续以确切facility crosswalk核对现120kV；本轮没有继续调查、改值或分配资源。其当前population dependency仍为0。

没有足够证据作本轮station MAX/registration输入更正。补充的独立事实已经进入decision CSV；没有将线路电压/相似名字直接写回站点MAX。R1 eligibility保持310，不删除目标站。

## 4. Set A / B / C必须分开

| 集合 | 科学含义 | 本轮可报告数量/状态 |
|---|---|---|
| A Eligible Infrastructure Inventory | 按R1公开字段和地理规则选出的资产记录；不自动说明电气接入或客户服务角色 | **310，冻结**；ID hash仍为 `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| B Electrically Representable Network | 具有可接受的registration或有据的局部接口，并明确哪些电路/设施功能被表示 | **306是当前几何兼容候选数，不是306个已独立验证的B成员**；4个明确registration unresolved，Montrose表示又被独立资料挑战；本轮不伪造一个“最终B=305/306”的已验证数 |
| C Modeled Service-Access Domain | B中有根据作为社区access proxy的功能节点；baseline可达只是必要条件之一，还需明确其是服务入口/step-down/面向下游的接口，或提供可审阅的服务代理假设 | **最终数量NOT_ESTABLISHED，不等于0。** 当前24-source下302可达节点仅为数学候选上界，不能自动命名为Set C |

为什么不能令C=B∩source-reachable就宣布关闭：CEC2022 layer的说明明确包含transmission substations、部分distribution substations、step-up/down、纯line interconnection及tap位置；统一TYPE=SUBSTATION并不区分这些功能。一个厂用/升压/线路tap设施与一个社区配电入口不是同一类access proxy。源可达性不提供独立的功能角色或feeder证据。

可辩护的C定义方向是：**有记录支持的面向下游服务接口，加上明确披露的未建模配电段**；对纯发电/厂用/线路tap不得仅凭最近距离承接社区。该原则独立于S=1目标，但当前字段不能给出一个可靠的全域C-ID名单。也没有依据把最近站失效或不被表示当作重新指派邻站的规则。

这不是要求全310站百科审计或重建AC/DC潮流；当前失败的闭合不能靠假装已经区分了设施功能完成。多年代代理可以作为条件比较研究的基础，但source假设、B中的接口表示和C的角色定义必须一致且可审阅。

## 5. 54个tract的正式分类与两个方案

**当前正式分类：**

| 分类 | tracts | population |
|---|---:|---:|
| RESOLVED | 0 | 0 |
| OUTSIDE MODELED SERVICE DOMAIN（正式采用） | 0 | 0 |
| REQUIRES NEW SERVICE MAPPING EVIDENCE | **54** | **220,426** |

这里的0个RESOLVED不是说没有科学进展。SERRF历史source疑问已有支持，Montrose/Ringmill的电气角色已获得独立证据；但它们尚不足以批准全局source boundary和这些tract的service inference。**3个tract/8,101人口的历史source问题有望解决，不等于3个tract已通过新baseline，更不等于这些居民已经被证实由SERRF供电。**

54行CSV保留原GEOID、人口、冻结baseline、NRI-derived SVI、centroid、目标设施组、证据与所需下一项数据。每行正式decision均为C类；`restricted_option_treatment`另列方案1下会如何排除，`restricted_option_adopted=False`，两种定义不混用。本轮没有新W或新S输出。

### Option 1 — Restricted inference domain（概念可行，尚未批准）

不改变任何W行权重；仅在最终source/C定义成立后，将无法表示的tract从推断域排除，保留其人口/GEOID，S=0不解释为停电。目前54个问题tract给出的**覆盖方案核算**：

| 指标 | 原全域 | 若排除54个 | 被排除 |
|---|---:|---:|---:|
| tracts | 2,315 | **2,261** | **54，2.3326%** |
| population | 9,066,522 | **8,846,096** | **220,426，2.4312%** |
| SOVI_SCORE中位数 | 74.14 | 74.55 | **49.97** |
| SOVI_SCORE Q25–Q75 | 47.25–89.21 | 47.94–89.34 | **17.99–66.53** |
| population-weighted SOVI_SCORE | 67.98 | 68.45 | **49.03** |

SVI使用原 `SOVI_SCORE` 的0–100尺度，2315/2315有效；不混用CDC2022，不生成新equity指标或恢复差异。TRACTFIPS以数值转整数后zfill11与GEOID一对一join。人口加权均值为Σ(P×SVI)/ΣP；quartiles为固定来源、各组tract分布的25/50/75分位。

排除区域集中于西北San Fernando Valley、北Glendale/山麓、West LA/Stone Canyon附近，及较小的Harbor–Torrance、Paramount、Long Beach港区组；地图按**模型access目标分组，不是utility territory地图**。排除组SVI明显偏低，意味着选择不是随机的，会改变样本组成和可推广范围。全体均值只移动约0.47不能消除这种地域/群体偏差。

保留97.57%人口在数量上足以支撑有规模的区域案例研究；但**数量足够不等于2261个tract的C角色和接口已经验证**。不能在source定义未批准、HALLDALE已知bypass语义未界定时，仅删54行就宣布其余推断全部可信。未来若采用此方案，论文必须明示覆盖域及选择偏差，不能仍声称覆盖全部2315。

### Option 2 — Evidence-based remapping

目前没有得到能对这54个tract执行该方案的独立feeder/service-area crosswalk。GWP官方文件证明电路/冗余性质，SCE Form1证明设施电压和功能；两者都没有提供这54个GEOID的供电依赖权重。行政/utility territory可用于候选约束，不能直接证明哪个feeder或substation服务这些tract。

因此目前Option1比“最近可达站替换”更可辩护，但仍只能是待批准的restricted-domain方案；Option2暂不具备执行依据。没有以source reachability为唯一理由重分W，没有为保留更多人口选择方案。

## 6. 本轮decision、下一步及复查

**本轮结束有限搜索。** 不继续追303265/305021的无依据别名，不扩大到全310调查，也不以新模拟代替证据。

再次dry build的最低前置条件是一个具体、可审阅的**边界定义包**：明确接受multi-epoch条件案例还是取得一个目标年份的核心网络快照；对external-energization规则给出实际入选/排除列表；给出C的设施功能定义与ID列表；对六组tract明确采用证据修复还是正式restricted inference。Montrose的34.5kV冗余接口和HALLDALE138kV表示应据现有独立证据处理，不能扩大snap或按近邻补边。没有这些定义，重复dry build只会再次得到已知的数学结果。

这一前置工作不要求full power flow、新算法或全县feeder普查。限定研究域仍是可保留的低复杂度路线，但需要把“资产清单、可表示电路、社区推断入口”真正分开，而不是只删除baseline失败行。

**执行证据层级：** 本轮完成文件/要素字段读取、primary文件核查、静态人口/SVI覆盖计算和决策表；未修改模型输入、未运行source gate或dry build，未执行恢复/MC/GA。覆盖核算只读取06静态baseline flags和原人口/SVI，不读策略恢复结果。地图只显示待审排除域。

输入hash供远端复查：

- 06 `R1_310_CLOSURE_DATA.npz`：`7f44b95426ce92c7343d373906efd894fe995347bb0433eba3effc79636e00d0`
- 06 `R1_310_DEPENDENCY_QA.csv`：`c574c7217ef603dcad2a9aaea355122e8a35afa3759e3b297b3a98ba25e2db43`
- 原 `LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv`：`117e19f0937aa2a2a0a75a8051883e59ed33146ed5da244bd89819976454a482`
- 原 `Tracts_Within_Expanded_Area.csv`：`b81268b48d77758f9d23fac4335c06024059a711f3c1453be2d0b9ecd1aa3a9e`

只交付本报告、54行targeted decisions、66行source ledger，以及一张覆盖域地图。CSV与冻结输入按ID核对；源清单25个ID的hash固定。没有新增大批manifest或模拟结果。

## 最后10项直接答案

1. **最合理system epoch？** `multi-epoch infrastructure proxy`。核心记录偏mid-2010s；2022包和2026plant状态不足以证明对应年份完整运行系统。
2. **final/provisional source set？** 正式集合未批准；待审reference2022清单25=06的24+SERFGEN，所有activate_in_model=False。2022是ledger参照，不是已验证的network epoch。
3. **54个tract分类？** 正式resolved0、正式outside0、requires evidence54；SERRF相关3个仅历史source疑点获得支持，未冒充service域已关闭。
4. **220,426人口？** 全部仍属待决推断范围；方案1会明确排除这220,426人，不重分W、不称其停电人口。
5. **改R1 eligibility？** **NO**。310 IDs不变；没有以本轮失败删除设施。
6. **A/B/C数目？** A=310；B现有306几何候选/4注册未解决，最终可辩护B尚未认证；C最终数量未定，302可达节点不等于302个合格社区入口。
7. **形成清楚的service inference domain了吗？** 尚未。分集合原则与restricted-domain方案已明确，但实际source/C membership缺乏足够关闭依据。
8. **baseline问题能靠证据而非归一化解决吗？** SERRF历史源问题有实质证据，Montrose/HALLDALE/Ringmill也获得方向明确的证据；目前没有证据解决全部54个tract的service关系，未做数学修补。
9. **限定域后覆盖是否足够支持论文？** 数量上仍有2261tract/884.61万人，可保留条件案例研究路线；不能据97.57%人口覆盖宣称代表性、服务映射或LA-specific政策解释已通过。
10. **现在值得再dry build吗？** **NO**。先完成明确的source boundary与C名单/角色定义及目标接口处理；现在重复计算不会解决它们。

**UNRESOLVED — 继续STOP，不运行恢复模型，也不批准重新dry build。**

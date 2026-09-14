# Utility-specific Set C decision — 2026-09-14

**决定：restricted/proxy mapping redesign；不进入 final dry build。** 本轮首次取得了与官方 SCE distribution architecture 直接关联的独立候选服务关系。可以冻结 Set C 的功能定义及有据成员，但不能据此宣称已恢复全市 tract→substation 经验映射。54 个失败 tract 中，3 个取得更强的候选变电站证据；这不是新的 baseline 通过结果。LADWP 部分的公开材料仍不足以确定全市 tract 服务归属，停止继续泛搜。

`MODELED_SYSTEM_EPOCH = multi-epoch infrastructure proxy`。2026 年下载的 SCE planning GIS 不回填为 2016、2022 或任何单一历史系统真值。

## 1. 实际完成与证据层级

执行了官方 GIS 原始响应下载、polygon/line 相交、设施名称与坐标 crosswalk、冻结 W 的静态 top-1/top-3 比较、54 个 tract 的证据分类，以及 CSV/ID/人口/hash 校验。没有改 R1 eligibility、registration、topology、W 或 source gate；没有执行 dry build、baseline 重算、恢复模型、MC、GA 或任何工班情景。

Set A 仍为 310。Set B 沿用 06 的未闭合状态，仅作为 crosswalk 属性报告，未重新验证。以下 Set C 不以 source-reachability 或让 baseline=1 为筛选条件；例如 NAVY MOLE 有官方 circuit 服务角色证据，仍保留其冻结的 component 2 / source-unreachable 标记。

父提交：`ef68dc5907b5bc1e705d4ab0a0600c1f85fb3325`。本轮仅新增 08 目录。这里的“old W”均指 **06 R1-310 local closure W**，不是旧 92-node W，也不是恢复结果。

## 2. 官方来源、下载和可复算记录

|资料|本轮使用的官方入口|实际支持范围|
|---|---|---|
|CEC utility polygons|[Electric Load Serving Entities layer 0](https://services3.arcgis.com/bWPjFyq029ChCGur/ArcGIS/rest/services/ElectricLoadServingEntities_IOU_POU/FeatureServer/0)|SCE、LADWP、其他 utility polygon；不是 feeder ground truth|
|SCE Distribution Circuits|[FeatureServer/0](https://drpep.sce.com/arcgis_server/rest/services/Hosted/Distribution_circuits/FeatureServer/0)|circuit_id、circuit_no、circuit_type、circt_nam、circuit_voltage、substation_voltage、sub_name、sys_name、geometry|
|SCE Service Territory|[ICA_Layer/17](https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Layer/FeatureServer/17)|与 CEC 交叉检查，不强行消除 polygon 差异|
|SCE Substations|[ICA_Layer/18](https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Layer/FeatureServer/18)|官方站名、坐标、bank ID、电压、D/A/S 类型|
|SCE 日期表|[ICA_Tables/0](https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Tables/FeatureServer/0)|`extract_name=ICA; fgdb_date=08-15-2026`；不保证每条 circuit geometry 都在该日更新|
|LADWP service exceptions|[Guide to Electric Service](https://www.ladwp.com/sites/default/files/2024-03/Guide%20to%20Electric%20Service%203.12.24.pdf)，PDF p28|官方服务规划地图；已目视检查；没有将示意图手工伪精确数字化|
|LADWP 系统角色|[2024 Power Infrastructure Plan](https://www.ladwp.com/sites/default/files/2024-09/2024_Power%20Infrastructure%20Plan%20Final_Web.pdf)，PDF p2、p5|RS→34.5 kV→DS→distribution architecture；123 DS、50 pole-top、22 RS 的系统描述|
|LADWP 设施记录|[LA City Clerk CUPA register](https://cityclerk.lacity.org/onlinedocs/2021/21-0943_misc_6_08-19-21.pdf)|2019 设施记录，2021 保留文件；本轮仅定向查角色、地址|
|FiT+ 局部线路|[LADWP FiT+ program](https://www.ladwp.com/commercial-services/programs-and-rebates-commercial/feed-tariff-plus-fit-pilot-program)、[2025-08 GIS ZIP](https://www.ladwp.com/sites/default/files/2025-08/FiTPlus%20Maps%20202508.zip)|局部 program geometry，不是全市 feeder map|
|FiT+ 适用范围|[program guidelines](https://www.ladwp.com/sites/default/files/2025-07/Guidelines%20-%20FiT%2B%20Pilot%20Program.pdf)，PDF p16 / printed p12 §3.5|近似 eligible service addresses；不能外推到 pilot 区域外|
|MWD 角色|[MWD Energy Sustainability Plan](https://www.mwdh2o.com/media/16848/mwd_esp_report-1630_vol_1.pdf)，PDF p45 / printed p25 §3.2|CRA 与自有水务设施用电；其宽域 LSE overlay 不直接代表普通社区独占零售供区|

下载日期 2026-09-14 UTC，最早 SCE schema 请求记录为 `2026-09-14T06:23:25.862980+00:00`。固定下载 bbox 为 `[-118.668176,33.696923,-117.677706,34.337306]`，之后只按实际 circuit 的未匹配站名追加查官方站点记录。1970 个 bbox circuit IDs 中 1499 个实际与研究区 tract 相交。官方 substation 下载包含 328 条 bbox bank records，另按站名追加 24 条。未进行全州线路泛搜。

`OFFICIAL_SERVICE_EVIDENCE.zip` 保存 56 次请求的原始响应及 query URL、参数、UTC 时间、SHA256，合计 112 个 raw 文件；包含 layer schema、官方 PDF/ZIP、原始 geometry、`RAW_RESPONSE_HASHES.json`、`ANALYSIS_SUMMARY.json`。`reproduce/` 包含三个静态分析脚本和 `validate.py`。解包后按 README 调整根目录，顺序执行 analyze→relations→build_deliverables；验证脚本只读最终文件与冻结输入。该证据包是五个核心文件之外唯一附加交付。

证据 ZIP SHA256：`8450c804063ba2af5fb2677332b27786fcbd250e36e1784695488293f295ba53`。

## 3. Utility domain 定义及结果

使用整个 tract polygon，不用 centroid 或 City of Los Angeles 市界代替 utility。SCE 类要求 CEC-SCE 与 SCE 官方 polygon 均完整覆盖，且没有 LADWP/其他社区零售 utility overlap；LADWP 类要求 CEC-LADWP 完整覆盖且无 SCE/其他 overlap。其余全部 `other / ambiguous`。1 m² 是几何数值容差，不是人口分配阈值。保存各 polygon 面积比例，不将面积比例当人口比例。

polygon 采用服务器 GeoJSON 的 shell/hole 分组，逐 polygon make_valid，再 union multipart；不扩大边界、不 buffer。重复 Vernon 记录只 union 一次。MWD overlay 单独保留 `MWD_LSE_overlay_fraction`，基于水务自供角色不用于普通社区零售的排他判定；这是一项明确功能解释，不是抹去该图层。

LADWP p28 列明 San Fernando、Beverly Hills、West Hollywood、Veterans Administration、Marina del Rey、Universal Studios 由 SCE 服务。这些例外不能由城市名称规则覆盖。本轮用 CEC/SCE polygon 检查并保留冲突；官方示意地图不能消除所有边界几何误差。

|UTILITY_DOMAIN|tract 数|人口|SOVI 中位数|人口加权 SOVI|
|---|---:|---:|---:|---:|
|SCE|817|3,572,152|75.35|69.82|
|LADWP|848|2,954,842|79.43|71.45|
|other / ambiguous|650|2,539,528|63.18|61.36|
|总计|2315|9,066,522|||

650 个 ambiguous 不等于无服务；包括 mixed tract、polygon overlap、边界差异、其他 utility。不能将它们强制并入 SCE/LADWP。`dominant_CEC_domain` 只是面积最大类的描述字段，绝不是唯一 utility assignment。

|54 个冻结失败 tract|tract 数|人口|SOVI 中位数|人口加权 SOVI|
|---|---:|---:|---:|---:|
|SCE|3|15,599|91.70|73.92|
|LADWP|23|90,079|51.32|45.60|
|other / ambiguous|28|114,748|48.94|48.34|
|总计|54|220,426|||

作为定位辅助，失败 tract 的 dominant CEC 类为 LADWP 40 /147,496 人，SCE 8 /39,868 人，other 6 /33,062 人；不可与上表严格归属互换。

SOVI 使用本地 `Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv:SOVI_SCORE`，NRI-derived 0–100 指标，并非新增 CDC SVI。TRACTFIPS 数值转整数、补齐 11 位，与冻结 tract ID 一对一对接；2315 个有效值。这里只报告证据覆盖构成，没有做恢复公平性分析。

## 4. SCE 独立关系及 crosswalk

按 tract polygon 与官方 circuit geometry 相交建立关系，无相交就标记，不 nearest-fill。多个 circuit/多个 substation 全保留。没有按长度、距离、人口或 old W 产生任何权重。

得到 **7375 条唯一 tract–circuit 关系、1295 个 tract、1499 个 circuit、223 个 normalized substation 名称、2921 条 tract–physical-substation-name 关系**。其中 817 个严格 SCE tract 全部有 circuit 相交，共 5190 条关系；另有 447 个 ambiguous、31 个严格 LADWP tract 与 SCE 线路相交，不能因此把整个 tract 改成 SCE。

相交关系均有正长度，无仅点接触；6 条小于 1 m，保留并在 `intersection_length_m_QA_not_weight` 中标记，不据此赋权或剔除。线路经过 tract 仍不保证其中每位客户由该 circuit 服务。

名称规则：去掉末尾电压标签、统一大小写/标点；只有官方 unsuffixed base name 存在时才合并 circuit A/B bank 后缀。同名同坐标 bank 合并为物理站名，同时保留全部官方 objectid/subst_id/type/voltage。R1 名称或冻结 CEC-2022 名称精确匹配后，再以坐标作交叉证据；250 m 沿用局部 registration QA 尺度，不进行最近距离强配。没有新增手工 alias。

全部查询站名中：123 个 exact normalized name + coordinate match；THUMSGEN 1 个 exact name 但无官方站点坐标，单列低证据质量；3 个 exact name coordinate conflicts；183 个 unmatched。这个分母包括无研究区 circuit 的查询站点，不能拿来当研究区匹配率。

坐标冲突保持 unresolved：ALAMITOS–307039 284.58 m；MESA–301541 531.52 m；TROPHY–308289 271.86 m。不能用名称或较近距离强行关闭。raw geometry、match quality、候选 ID 均可查。

实际研究区内有 265 条官方 bank records，对应 218 个物理站名/site，其中 203 个属于 `D -- Distribution` 或 `A -- District Pole Top`。其中 119 个可匹配 R1 且具有研究区 circuit evidence，形成 **SCE Set C =119**。这不是说另外 84 站不存在，也不是承认 R1 完整覆盖 SCE 配电站。

Crosswalk 文件 `record_type=tract_circuit_relation` 保留全部独立关系；`record_type=substation_registry` 保留完整匹配/未匹配名单。`official_unmatched_candidate_count` 保留未进 R1 的候选，不能把已匹配的子集误当唯一供电站。

## 5. 冻结 W 的独立候选一致性检查

仅主报严格 SCE 的 817 tract。top-3 是正权重前三站，相同权重按 station ID 稳定排序；不是重新计算 W。

- exact support：top-1 在官方 circuit-derived R1 candidate 集内。
- partial support：不是 exact，但 top-3 至少一个在 candidate 集内。
- contradicted：有官方 circuit evidence，但 top-3 无 candidate 命中。
- no official circuit evidence：没有相交 circuit。

“contradicted”是本轮公开候选集中的不一致，**不是已证明历史线路接错**：公开层完整性、epoch 差异及未匹配站名仍有影响。exact 也只支持候选归属，不验证 IDW 权重。

|类别|tract 数|比例|人口|SOVI 中位数|人口加权 SOVI|
|---|---:|---:|---:|---:|---:|
|exact support|549|67.20%|2,394,058|74.58|69.63|
|partial support|126|15.42%|562,862|76.36|70.21|
|contradicted|142|17.38%|615,232|76.27|70.19|
|no official circuit evidence|0|0%|0|||

Top-3 候选有交集为 675/817=82.62%；不是“82.62% 的 W 权重已验证”。非失败 814 个 tract 为 exact549、partial126、contradicted139；3 个失败 SCE tract 全部 contradicted，人口15,599。非失败 contradicted 人口599,633，人口加权 SOVI70.09；失败 contradicted 人口加权 SOVI73.92。逐行 SOVI/失败标签见 tract CSV。

另有 **111 个 R1 站在严格 SCE tract 的 W 中取得正权重，却没有本轮 matched study SCE circuit relation**。不能直接称这些设施错误；它们也可能具有其他角色/年代证据。静态人口 dependency 最大者为 SIMPSON307634：43,222.46；DUCTILE304240：40,442.03；CLAREMONT301431：38,973.41；UNKNOWN310294：37,332.43；MONTIBELLO307254：31,650.46。这些是 sum(population×frozen W)，不是实际客户数或关键性排名。完整标记见 R1 crosswalk。

## 6. LADWP 角色与公开 mapping 的上限

仅定向检查 CEC-LADWP polygon 内 51 个 R1 设施，其中5个位于 SCE polygon overlap：300916、301156、302381、307239、309663。地理落在 LADWP polygon 不等于资产 operator=LADWP；Owner 原值保存在 CSV，未更改。

LADWP 普通社区 access interface 优先采用独立证据支持的 DS。RS 的上游供电角色不能自动转成普通 tract access；SS、plant、switchyard 亦不能因距离近进入 Set C。

|角色证据|设施数|Set C 处理|
|---|---:|---|
|DS：官方角色+地址支持|2|纳入 LADWP Set C|
|DS：身份/位置仍需局部核实|1|provisional，不纳入正式成员|
|RS：官方 named role 支持|15|不自动纳入社区 Set C|
|RS：provisional named crosswalk|1|不纳入|
|Switching Station|3|不纳入|
|Generation / plant interface|2|不纳入|
|generic transmission/subtransmission interface|3|不纳入|
|SCE distribution interface，地理位于 CEC-LADWP|4|按 SCE 官方角色账本处理|
|unknown|20|不自动分类|

DS 明细：300144（R1 STATION11 / CEC Station66）对应 DS66，CUPA PDF p235，12200 W San Vicente，官方 Census address geocode 距 R1 148.09 m；300589 对应 DS54，p244，1675 Hillhurst，32.41 m。301555 HARBOR / CEC Station119 对应 DS119，p253，220 N Henry Ford，373.07 m，保留 provisional。地址 geocoder 是街址位置，不是站场边界；超过局部核查尺度不证明设施不存在，但不提前确认。

15 个 supported RS 为 E、J、K、G、N、D、U、B、P、Rinaldi、F、Q、T、C、H；A 为 provisional。逐 ID 的官方页码/URL 见 `role_evidence` 和 `role_source_url`。Station67 未找到足以确认 DS 的官方角色记录，不凭名字升级。Ringmill 有冻结07中的 SCE2019 distribution-role 记录，但没有当前 DRPEP named circuit crosswalk，未纳入 Set C。

FiT+ ZIP 有 60,624 条 line features，只含 Voltage 及季节时段/multiplier 字段，**没有 circuit ID/name/substation key**。它与820个研究 tract、31个失败 tract 相交，可作为局部电压线路覆盖证据，不能据此完成 circuit→DS 关系，更不能外推全市。

结论：**Full tract-to-substation empirical mapping cannot be recovered from the public evidence obtained in this bounded review.** 这不是声称任何渠道都不存在数据；它说明当前证据不足，继续同类公开泛搜不能替代研究设计决策。

## 7. 54 个失败 tract：只作证据分类

|分类|tract 数|人口|含义|
|---|---:|---:|---|
|RESOLVED_BY_UTILITY_EVIDENCE|3|15,599|取得独立 candidate-service relation；未解决权重、客户分配或 baseline|
|VALID_SERVICE_CANDIDATE_BUT_MAPPING_UNCERTAIN|22|88,764|有 circuit/substation 候选，但 utility mixed/tract allocation 未闭合|
|NO_PUBLIC_SERVICE_MAPPING_EVIDENCE|29|116,063|缺 station-linked 公共服务映射；FiT+ line 不能代替|
|OUTSIDE_SUPPORTED_INFERENCE_DOMAIN|0|0|本轮未采纳排除方案|

3 个候选关系闭合明细：

|tract ID|人口|冻结 W top-1|官方 circuit-derived candidates|
|---|---:|---|---|
|06037553902|5925|RINGMILL306980|Lighthipe303169、Somerset306947|
|06037553801|4124|RINGMILL306980|Imperial306884、Lighthipe303169、Somerset306947；Ronnie PT 尚未匹配 R1|
|06037300200|5550|Montrose309598|Gould300829、La Canada303005|

上述已匹配候选均在冻结06中 registered、component1、source-reachable。这是旧输入属性查询，**不是本轮新 gate 验证**；不能把它写成“已恢复15,599人供电”。Ringmill 的历史配电角色与当前候选不一致不等于 Ringmill 假设施。

其余 mixed 证据包括 HALLDALE 区的 Neptune/Nola/La Fresa、UNKNOWN305021 相关 tract 的 Sawtelle、UNKNOWN303265 边界 tract 的 Chatsworth、Montrose 周边 La Canada/Gould，以及旧 NAVY MOLE 组的 Dike/Walteria。跨过部分 tract 的线路不能决定整个 mixed tract。54个 ID、原 top-1、全部 circuit IDs、matched/unmatched candidate、冻结 component 和证据类别均逐行保留。

不重分权重，不剔除54个 tract，也不把原 S=0 解释成观测停电。LADWP-dominant failures 占多数，停止逐站 provenance 泛搜。

## 8. Set C 与 source scenario 决定

`Set C = facilities with independent evidence of downstream community-service function within the relevant utility domain.`

**当前证据成员121 = SCE119 + LADWP2；另有1个 provisional LADWP DS。** SCE 的实现要求官方 D/A 配电角色、研究区 circuit relation、可接受 name/coordinate crosswalk；LADWP 的实现要求明确 DS 角色及设施身份支持。没有因 node 无 source 而移出 C，也没有为了覆盖某个失败 tract 而加入 C。该集合是有据候选设施子集，不是完整城市 service mapping，不等于310。

冻结 **`SOURCE_SCENARIO_REFERENCE` =21**，只作为 reference source-availability scenario；不另造 CORE 或更多套情景。本轮沿用07证据账本的 generation/import role，去除4个仅 inherited/unsupported 的旧25成员 GOULD300829、MESA301541、RIO HONDO305984、HARBORGEN304450。不是因连通性或 baseline 成败删加 source。

21节点 =18 generation-role proxies +3 external-import interfaces：

`300232,301318,302376,302865,303473,303547,306001,306365,306450,306473,306489,307039,307373,307512,307693,308540,308581,309553,309569,309703,310199`

generation 节点主要来自保留的 CEC2026 inventory（site start早于2023，历史连续性仍属推断）；SERRF303547单列2019设施+2022发电角色，作为显式 historical availability assumption；3个import采用LADWP2022区域接口角色。逐node保留 `source_evidence_period` /URL。发电厂存在不等于注入端子已验证，source scenario不包含容量或电力平衡证明。不能称 actual2022sources 或 validated LA source set。Gould可以是社区候选站而不作为source。

`source_scenario_activated=False` 全310行；没有用21节点计算新baseline。

## 9. 下一步唯一值得推进的工作

**先做 restricted/proxy mapping redesign 的书面定义与可用输入设计，不先 final dry build。** 分开：(a) SCE 的 circuit-derived 多候选关系与尚未知的权重；(b) LADWP 少量DS角色证据与全市 tract归属缺口；(c) mixed-utility tract 的推断范围。任何新的权重需要独立依据或显式假设，不允许按source可达性重分配；任何 restricted domain 必须报告coverage及选择偏差，不能把本轮候选覆盖率当恢复覆盖率。

如继续保留全2315 tract，只能把未有实证的部分明确称为假设性 proxy mapping，并设计相应主张边界；如希望实证 LA-specific tract service claim，需要额外 utility/feeder/service-area 证据。LADWP缺口不是再跑MC能够解决。此阶段不建议继续逐站百科式追查、调snap、增source、增edge、改310名单或扩大模拟。

最终直接回答：

1. utility 分布：817 SCE /848 LADWP /650 other-ambiguous。
2. 54失败：3 SCE /23 LADWP /28 other-ambiguous；dominant分类另列，不能互换。
3. SCE GIS与1295研究tract相交，包括全部817严格SCE tract。
4. 独立关系7375 tract–circuit /2921 tract–station-name。
5. SCE top-1 support549；额外top-3 support126；candidate不一致142。
6. SCE Set C119个R1设施。
7. LADWP confirmed/supported DS2、RS15；各另1 provisional。
8. 没有足够公开证据形成 LADWP citywide service mapping。
9. 3个失败tract的候选关系被独立证据resolve；0个baseline被重新计算或宣布通过。
10. Set C功能定义及121个有据成员可冻结；全市W不能据此直接建立。
11. reference source scenario21可作为明确多年代假设冻结，未激活。
12. 下一步 restricted/proxy mapping redesign；恢复模拟继续STOP。

## 10. 文件与核验入口

- `TRACT_UTILITY_DOMAIN.csv`：2315行，utility面积比例/ambiguity、人口/SOVI、官方candidate及冻结W支持分类。
- `SCE_CIRCUIT_SUBSTATION_CROSSWALK.csv`：7375 relation行加station registry；按record_type读取，避免把registry行当tract关系。
- `R1_SERVICE_ROLE_CROSSWALK.csv`：310行，角色/evidence period/URL、Set C、source scenario、冻结B状态、原Owner及静态dependency。
- `BASELINE_FAILURE_UTILITY_EVIDENCE.csv`：54行，四类证据、candidate注册/component属性；W_modified/new_baseline_computed/outside_inference_domain_adopted全False。
- ZIP `reproduce/analyze.py`：geofeatures、utility full-polygon规则、SVI join；`relations.py`：norm、official crosswalk、spatial join、support；`build_deliverables.py`：set_C_role_candidate、rs/ds角色账本、source条件、cat；`validate.py`：独立读回验证。

冻结输入：`../06_R1_310_LocalClosure_20260914/R1_310_CLOSURE_DATA.npz`、`STATION_CONNECTION_DECISIONS.csv`、`R1_310_DEPENDENCY_QA.csv`；角色沿用依据 `../07_SystemEpoch_ServiceBoundary_20260914/SOURCE_PROXY_EPOCH_DECISIONS.csv`；坐标/原Owner来自05 stations QA；tract geometry来自仓库 `Data/Tracts_Within_Expanded_Area.csv`。

R1 sorted IDs（newline终止）SHA256：`d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5`。

冻结06 NPZ SHA256：`7f44b95426ce92c7343d373906efd894fe995347bb0433eba3effc79636e00d0`。

reference21 sorted IDs SHA256：`c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3`。

验证通过：2315/310/54唯一ID及人口对账；7375唯一tract–circuit键；全部top-3与候选分类独立读回；121/21集合计数；全部未激活标记；56个原始请求response hash；冻结06文件未变。**可复算证明分析执行一致，不等于模型已验证。**

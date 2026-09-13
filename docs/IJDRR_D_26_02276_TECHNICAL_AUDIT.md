# IJDRR-D-26-02276 技術診斷與修訂決策
查核日期：2026-09-12（洛杉磯）。這是可公開的版本庫快照；原始審稿文件、稿件副本及完整本地查核包未納入公開 repository。

**判斷：幾者兼有，主因不是已證明整個模型算錯。** 現有結果足以支持「排程完成速度與模型人口服務恢復速度不同」「同一策略讓部分社區改善、另一些社區惡化」；文章尚未充分分析這些結果。可信度的主要缺口是 tract dependency／source-connectivity 與真實供電的對應支持，以及平均任務排程與隨機恢復之間的決策語義、不確定性傳遞。另確認少數實作／稿件不一致：修復時間抽樣的負值處理不同於稿件公式、Table 4 兩列 makespan 對調、Northridge 文字數值落後於現存輸出。這些問題需要更正，但不能由此推定所有策略結果失效。

本輪實際完成了本地文稿與審稿原文比對、程式追蹤、保留 CSV 重算、同 fitness 比較、有限幾何診斷，以及主情境四個**固定既有排程**的恢復重建。沒有執行全量 pipeline、重新優化 GA、修改核心模型、覆寫既有圖表或執行轉投。下文所有新分析均是模型條件結果；沒有建立真實客戶停電、醫院營運或因果效果的實證。

**1. 版本與資料流程：可確認與尚不確定的部分**

實際專案已移至 目前專案（本地來源檔）。初始 HEAD 為 8dfbc5e（2026-07-22）；程式及既有結果的 tracked worktree 乾淨。未追蹤的兩個檔案為 Reviewer.docx 與 IJDRR-D-26-02276_editor_review_transfer_record.md，本輪沒有改寫。原工作路徑中的 Network science 已改為 CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science。

| 材料 | 核對結果 | 證據／用途 |
|---|---|---|
| 7 月 20 日 PDF | 題名 From Substation Damage to Community Recovery…；Table 4 在印刷頁 34。不是已證實的上傳版。 | LA Grid Paper Revised_20260720.pdf（本地來源檔）；SHA-256 8511a2177d433f72252ecc54601da0a7fdd62a04b66d54e1e29742cfd6513076 |
| 修訂 Word | LA Grid Paper Revised.docx，內部修改時間 2026-07-22T06:42:36Z；不是最新候選。 | 修訂 Word（本地來源檔） |
| 最新、與提交題名相符的 Word | LA_Grid_Manuscript.docx，內部修改時間 2026-07-23T19:44:13Z；題名與 IJDRR 提交題名完全相符。**目前最可信的提交候選**，但缺收件證明／Editorial Manager 編譯 PDF。 | 7 月 23 日稿（本地來源檔）；SHA-256 3dc7de9e27bb0f676ca56554cd6fa1d8becfa77732066ecf4193405c24fcb1dd |
| Archive 的 Submission_Package | Manuscript_IJDRR.docx 內部修改時間仍為 7 月 20 日，題名也較舊；資料夾名不能證明是提交版。 | 封存稿（本地來源檔） |
| 本轮審稿材料 | Reviewer.docx 與本地決定／審稿紀錄相符；決定是 Reject with transfer offer。紀錄是作者提供信件內容的本地轉錄，未取得郵件原始標頭或系統檔。 | 原始文件只保留於作者本地，不納入公開 repository。 |
| 舊回覆材料 | 找到投稿前合作者評論／回覆，包含 Marta Gonzalez 的 7 月初評論；未將它們當成本輪審稿回覆。未找到名稱完全相同的 Response to Comments LA Grid.pdf。 | 搜尋清單與文件提取索引（完整本地查核包） |
| 程式與數值輸出 | 92 nodes／318 edges；Table 4 的四個指定策略可逐項核對；其他已確認的版本差異另列。沒有逐一重現全部情境與圖表。 | [重現說明](../REPRODUCIBILITY.md)；所有情境的指標及實際 makespan（完整本地查核包） |
| 最終圖 | Submission_Package 的 Figures 1–7 與 build/figures 現存檔案 SHA-256 全部相同。是現存檔案比對，非本輪重新產圖證明。 | 圖檔雜湊核對（完整本地查核包） |

DOCX 內部時間是版本線索，不是上傳證明。完整版本雜湊、內部時間與文字差異見 版本表（完整本地查核包）、Word 文字差異（完整本地查核包）。本地未找到更晚的實質修訂稿。

資料到圖表的實際鏈條：

1. CEC/HIFLD 來源點位、CEC 線路、tract 範圍 → **先選定 92 站清單** → 線路修整與物理幾何圖 → 92 節點簡化圖及 dependency W。92 站選擇的完整逐筆 lineage 目前缺失；不能直接寫成「原始幾千個電力節點經等值縮減成 92 個」。
2. IDW.py 將 PGA 場配到站點 → Substations_PGA_IDW_CEC_expanded.csv → Stage 1 損傷／修復抽樣 → Stage 2 結構指標／探索性 percolation。
3. Stage 3 無工班限制恢復 → Stage 4 七種規則排程 → Stage 5 三種 GA 排程 → 同一恢復函式、source gate、W → Stage 6 系統曲線／KPI。
4. Stage 7 用 GA-Balanced 主情境 tract 結果與人口／社會／建物特徵作聚類與 hotspot。它是後處理，沒有回饋到工班決策。
5. Project_Visualizer.py → make_manuscript_composites.py → build/figures；Submission_Package 保存圖檔。敏感度的資料另保存在 Data/sensitivity_summary_2pc50.csv 及 Sensitivity Output_clean。

參見 [pipeline 順序](../run_pipeline.py)、[PGA 配值](../IDW.py)、[最終圖組合](../make_manuscript_composites.py)。

**2. 問題判定表**

A＝表述或定位；B＝已有輸出可補分析；C＝需要新增模擬或驗證；D＝已確認的實作／邏輯／報表不一致；E＝證據不足。D 不代表一定要改變模型物理；表格中會指出是資料呈現錯誤還是實作語义不符。

| 審稿問題 | 稿件怎麼寫 | 程式／輸出證據 | 對結論的影響 | 判定與處理 |
|---|---|---|---|---|
| 92／318 從何而來、額外連通 | 幾何修整、最短路、排除中間站；承認非電力等值網路。 | 已選定 92 站；物理圖重建 66,640 vertices／68,116 segments；六條最長保留邊距離吻合且無內部註冊站。完整 92 站選入／剔除紀錄缺失。[拓撲程式 L2028](../Topology_and_Weight.py#L2028)；[拓撲診斷](audit_outputs/topology_diagnostic_summary.json) | 部分程式建構可重現；尚不能證明全體簡化邊都物理正確或完整。 | A/C/E：補 inventory crosswalk、來源狀態及邊抽查，不能用邊長 cutoff 代替連接證據。 |
| 跨電壓／供電區連結 | 有 voltage-aware snapping 的敘述；次級 snapping 描述為 150–300 m。 | 實際 secondary tolerance 375 m；owner／voltage family 做幾何相容性，但受保護站點可跨層相接；無 feeder territory W 限制。4 個 Proposed parts 保留。[拓撲程式 L78](../Topology_and_Weight.py#L78)；[拓撲程式 L1902](../Topology_and_Weight.py#L1902) | 不是完全無電壓防護；也不能把地理／owner guard 當變壓器及開關證明。 | A/C/E；D 僅用於 300／375 設定不符。Proposed 是否過時、是否改變服務尚未證實。 |
| IDW／tract 映射正確性 | p=2、cutoff=.03、刪除後重正規化，有 cutoff sensitivity。 | 距離是 centroid 到最近站的平面距離，加該站至候選站的物理圖最短距離；不是純地理距離或 feeder 路徑。W=2315×92、無重複 tract–station、每列和為1。[映射程式 L18](../topology_outputs.py#L18)；映射檢查（完整本地查核包） | 數值一致性成立；ground truth 正確性未建立。 | A/C/E：替代映射、邊界／設施抽查；比較 tract 負擔與群體差距。 |
| source gate 與真實供電 | 承認 connectivity proxy，但 power-service／outage 等用語仍易被讀成實際供電。 | raw ≥.5 的**所有節點**構成 active graph；連到有效 source 的 component 才通過；每次 gate 後再平均。無容量、潮流、功率平衡、電壓、線路上限或 load shedding。[主程式 L2164](../C257H_Project_Main.py#L2164) | 可比較特定假設下的結構可達性恢復，不能證明实际 MW、客戶通電或醫院運作。 | A/C/E：限定主張，另補有限物理 benchmark 或相應資料支持。 |
| MC 如何進排程／排名 | 平均修復時間形成代表性排程，另有 damage-conditioned CDF。 | 任務門檻是 mean≥1 h，非 >0；平均工時決定 crew completion。逐次 DS 進曲線，但逐次 sampled repair duration 不重新解碼工班排程；最終 T80 是平均曲線的 crossing。[主程式 L347](../C257H_Project_Main.py#L347)；[主程式 L3326](../C257H_Project_Main.py#L3326) | 有 MC 傳播，但尚非端到端隨機排程效果分布。 | A/C/E：明確 expected-workload 基準，增加 paired realization 評估。不是已證明「未做 MC」。 |
| crew completion 與功能恢復相接 | 稱工班完成修復任務，功能由 CDF 恢復。 | CDF 從到站時間起算；平均任務時間後 crew 離開，而本情境平均 raw functionality 此時約 .544。[主程式 L3467](../C257H_Project_Main.py#L3467)；離場功能診斷（完整本地查核包） | 任務完成與恢復完成不是同一個事件；需解釋並支持其物理含義。 | A/C/E：待澄清／校驗，不直接標 double counting 或 D。 |
| 修復時間抽樣分布 | 正值條件化的 truncated normal。 | rng.normal 後 np.maximum(samples,0)；CDF 才是正值條件化；主情境 92,000 樣本中194個 damaged 樣本時間為0。[主程式 L795](../C257H_Project_Main.py#L795)；[主程式 L2140](../C257H_Project_Main.py#L2140) | 公式與抽樣分布確實不同；影響大小還未用修正分支測試。 | D/C：明確選擇並統一分布，必要時小規模 paired 對照。 |
| GA 是否有效、為何 Hospital rule 較好 | fitness 為任務提早完成收益減 makespan；並非服務 AUC。 | 同 fitness：GA-Hosp .924922 > Hospital rule .922243；但 pop T80 49.80 >47.00。GA-Balanced 可被另一 GA 排程在自己的目標上超越。[相同目標比較](audit_outputs/same_fitness_comparison.csv) | 主差異是目標不一致；不能用 T80 排名直接判 GA 失敗，也不能聲稱收斂最優。 | A/B/C：保留為比較基準、補跨種子與規則 fitness，降低方法主角地位。 |
| GA 可重現性／參數 | 有參數與權重，收斂和重複證據不充分。 | 100×100、DEAP eaSimple、固定 scenario/policy seed；無 Hall of Fame／elitism，取最後代最佳；無保留收斂與多次種子結果。MC 分塊依 CPU 數。[主程式 L4175](../C257H_Project_Main.py#L4175) | 單次可再執行不等於解的穩定性；seed42不足以跨硬體重現 MC 樣本。 | A/C/E：保存 realization ID／獨立隨機流與 GA trace，分開兩類不確定性。 |
| SVI／公平性 | SVI-weighted curve、聚類及差異。 | 系統權重用 NRI Mar-23 的 SOVI_SCORE；聚類另用 CDC 表四主題平均；有效 CDC 資料2291／模型2315。四策略負擔已補算。[主程式 L3513](../C257H_Project_Main.py#L3513)；[主程式 L5536](../C257H_Project_Main.py#L5536) | 加權平均不等於群體差距；不同 SVI 定義不應混稱單一指標。 | A/B/C/E：固定來源／分組，報人口加權負擔、有方向差距、尾端與受益／惡化；跨情境不確定性仍待補。 |
| 歷史時間尺度比較 | 7/23 稿已明說 contextual scale check。 | 舊 LADWP 客戶 milestones 與現代多 utility tract proxy 分母不同；retained Northridge baseline14.10、logistics14.45–15.10，文字14.25、14.55–15.25。歷史 milestones 對照（完整本地查核包） | 只能有限合理性檢查；T80近似不代表前段／尾段或 tract 預測有效。 | A/B/D：更新數字，併列 T50／T90／T95，收斂驗證用語。 |
| 聚類、hotspot 與機制 | 11 個標準化特徵、PCA/k-means、綜合熱點。 | features 已含 T80、SVI、NRI；hotspot 是 T80／pre1970／NRI／SVI 的 percentile 組合。[主程式 L5700](../C257H_Project_Main.py#L5700)；[主程式 L5735](../C257H_Project_Main.py#L5735) | 群集有高 SVI／慢恢復部分是定義結果，不能當獨立因果證據。 | A/B：描述性結果移附錄，主文以策略的 paired tract 變化為主。 |
| Table 4 與 sensitivity | 指定四策略數字；crew rank rho 約 .23–1。 | 四策略數字吻合；Degree／Closeness makespan 對調；114crew T80只差.10h。敏感度使用固定既有 order。重算指標（完整本地查核包）；[資源條件排名](audit_outputs/crew_rankings.csv) | 原始結果有決策價值；單報 rank correlation 容易誤導。 | A/B/D；C 用於重新配置策略或 paired UQ，勿把已做敏感度列為未做。 |
| 方法整合是否新穎 | 以串接現有模組為框架贡献。 | 本地 Cheng2024、Xu2007、Jiang2025、Chen2025 已覆蓋多個相鄰核心問題，見第7節。 | 無法主張 LA tract、GA物流、人口／SVI／醫院整合本身首次。 | A/B/C：將新意落在可檢驗的社區結果與資源適用條件。 |

**3. 技術鏈條與八項問題的詳細判讀**

**3.1 網路與 tract dependency**

來源清單有 CA_substations_MERGED.csv 4,260筆、OPENBASIN 4,442筆、LA County 442筆、LA City 64筆；現行 working_area_substations_with_fragility.csv 為92筆。現有地理篩選獨立重算得到302站，其中73與現行92相同；19個現行站不在該簡單篩選中、229個篩選站未保留。這證明需要補充人工／補充 source proxy 的選擇歷程，**不是證明該19站選錯**。完整逐站 crosswalk 未找到。選取差異（完整本地查核包）；原始資料目錄（本地來源檔）。

物理幾何處理依序是：50 km bbox 選線、屬性修正、150 m primary／375 m secondary snapping（另有嚴格 margin／ratio 條件）、75 m 端點合併、10 m 內的站點投影切線、圖建立、站點250 m registration 上限、最短路及中間站阻擋。現行92站全部註冊，最大偏移87.98m、沒有兩站共用同一註冊 node。保留318邊的圖是一個 component。六條最長邊重建距離吻合、無內部註冊站；這只是一項六邊抽查，未驗證所有318邊與所有可能遺漏的替代路徑。[拓撲程式 L78](../Topology_and_Weight.py#L78)；[拓撲程式 L2162](../Topology_and_Weight.py#L2162)；[拓撲程式 L2331](../Topology_and_Weight.py#L2331)；六條最長邊抽查（完整本地查核包）。

程式確實防止部分跨電壓／owner 的不當幾何合併：66/69、220/230被分為 voltage family；部分 owner aliases 允許接合；站點上的跨電壓接合允許存在，未知屬性較寬鬆。沒有 circuit-level breaker／transformer 狀態。LA BREA 等屬性有手動覆寫，應列逐項來源。受檢圖中保留4個 Proposed、23個 Unknown 線段；這些原始狀態部分來自舊資料，不能推論現時一定尚未投運。有限檢查移除4個 Proposed parts 後，92站仍同一 component、六條抽查最短路不變；**這不能排除其餘邊、權重或受損後 redundancy 改變**。[拓撲程式 L112](../Topology_and_Weight.py#L112)；[拓撲程式 L1462](../Topology_and_Weight.py#L1462)；非 Operational 明細（完整本地查核包）；[移除 Proposed 的有限結果](audit_outputs/proposed_line_check.json)。

W 的精確順序：

- tract polygon 投影 EPSG:3310 後取幾何 centroid；不是人口加權 centroid，也不是先用 INTPTLAT／LON。
- 以平面距離找最近的接入站；到候選站的合成距離為「centroid 到接入站」加「物理線路圖上接入站到候選站的最短距離」。
- 對可達候選計算 d^-2，再做第一次 row normalization；小於.03的**正規化權重**刪除後再次正規化。不是用.03去切原始 d^-2。
- 全部刪除時取原最大權重站 one-hot。程式另有 missing/protected proxy 機制，現行輸出沒有零連結 tract。2315個tract的W無重複 pair、人口欄位同一tract無衝突。
- 系統人口加權先對每個tract取一次人口再正規化，未發現系統人口重複計算。規則排序卻可能把同一tract人口計入多個站的 priority，屬排序定義，不能與總人口加總混淆。

證據：[映射程式 L18](../topology_outputs.py#L18)、[映射程式 L108](../topology_outputs.py#L108)、[映射程式 L150](../topology_outputs.py#L150)、[主程式 L3513](../C257H_Project_Main.py#L3513)、mapping 數量／正規化檢查（完整本地查核包）。模型共2315 tracts、9,066,522居民；2291是CDC有效值的分析子集。研究區不能寫成完整LA County／LADWP或SCE整套供電系統。

在限定專案、來源與參考文件的搜尋範圍內，未找到可直接驗證W的 feeder–tract ground truth、utility customer outages 或獨立 substation–customer 對應。CEC owner、醫院點位、行政邊界及道路不能替代它們。最小補強可用：基準W、純平面 nearest-1、nearest-3 IDW三組固定映射；另在取得可用 utility territory 後加一個 boundary-restricted 版本。先保留同四個排程重算服務，分離映射效應；若政策排序實質變動，再重新產生受W影響的優先順序。以20–30個分層抽查位置起步，涵蓋 utility 邊界、最大dependency變動、高SVI、source proxy與長邊接入；這是診斷樣本，不是精度驗證的統計樣本。比較 tract B／T80、受益人口、有方向群體差距、尾端與策略差值，不能只比較全域T80。

**3.2 Source-connectivity proxy**

對每個實現 m、時間 t，實際鏈條為：

raw f_i,m(t) → 所有 raw≥0.5 的節點及其誘導圖 → 14個source proxy中當下active者 → source-containing components 的 gate g_i,m(t) → effective f_i,m(t)g_i,m(t) → W乘積成 tract service → 對 m 平均 → 系統人口／脆弱度加權與KPI。

source_nodes_core_expanded.csv共有38筆角色記錄，但真正 source 是8個 in-basin generation proxy 加6個 import interface proxy；24個 transit hub 不作 source。threshold不是只測source節點；中間路徑節點也須≥.5。[source角色表](../Data/source_nodes_core_expanded.csv)；[主程式 L2223](../C257H_Project_Main.py#L2223)。

逐程式追蹤確認：沒有容量、潮流、供需平衡、thermal limits、voltage constraint、load shedding；源頭也沒有獨立機組可用MW抽樣，線路沒有獨立地震損傷／修复過程。line length 是路徑距離，voltage class 用於 fragility／結構score，不等於施加電力物理限制。[主程式 L2164](../C257H_Project_Main.py#L2164)；[拓撲程式 L1902](../Topology_and_Weight.py#L1902)；[README 的模型範圍](../README.md#L10)。

因此可以比較「同一簡化依賴假設、固定震害場與資源條件下，不同序列如何改變模型服務可達性／缺損」；不能直接稱實際 delivered power、實際客戶停電小時、醫院可運作時間。Hospital-first只表示含醫院tract的優先程度，沒有備援發電、床位／服務需求、醫院設備與人力依賴。

限定主張能處理名稱與解釋過度；無法單憑改名處理決策排序的物理可信度。現有LA檔案有幾何、電壓與人口，缺reactance、ratings、source MW、bus load與switching資訊，不能據此直接跑可信的LA DC／AC潮流。有限benchmark可先用有電氣參數的公開小網路、或能取得資料的5–20站子系統，對照proxy與capacitated flow／DC load-shedding在不同負載與破壞狀態下的差異。公開小網路只能測proxy失效條件與排序穩定性，不能「驗證LA供電」。若保留具體LA政策效果主張，仍要相應本地資料支持，或將其限於假設下的案例探索。

**3.3 隨機損傷、代表性任務與恢復**

每scenario在給定PGA與fragility參數下，對站點抽1000個DS與修復時間；沒有額外抽空間相關 ground-motion residual、fragility epistemic parameters或道路損傷。規則與GA恢復讀同一scenario damage records，因而已有 common samples 的基礎。程式沒有把不同策略各自獨立抽的震害誤當政策效應。[主程式 L728](../C257H_Project_Main.py#L728)；[主程式 L1242](../C257H_Project_Main.py#L1242)；[主程式 L2611](../C257H_Project_Main.py#L2611)。

任務是 mean repair≥1 h。下表直接由保存的 repair_task_threshold_audit.csv 得到；「預期未受損但被排入」為被選任務站的 Σ(1−P_damage)，不是每次都同樣這些站未受損。

| scenario | 代表性任務數 | 全網每次預期受損站數 | 被排任務中预期未受損數 |
|---|---:|---:|---:|
| 2pc50 | 92 | 91.673 | .327 |
| Northridge | 76 | 68.570 | 14.596 |
| LongBeach | 61 | 61.229 | 9.639 |
| SanFernando | 33 | 44.136 | 6.792 |

[原始任務審核](../Stage%203%20Output_expanded/repair_task_threshold_audit.csv)；本輪重算（完整本地查核包）。

所以「可能受損等於此次實際需修」是代表性排程的局限，但主情境幾乎全部站都受損；弱情境影響可能更大。未達1h門檻的站不佔工班、從t=0起依其DS恢復，不是被剔除為完全不受損。若代表性工作量被當成已知實際任務清單，就要修正敘述／決策層。

實際damage-to-function設定為DS0–4初始raw功能[1,.50,.09,.04,.03]；DS1–4的normal工時(μ,σ)，單位h，依序是(1,.5)、(6,3)、(12,4)、(36,12)。程式將這些解釋為檢查、切換、隔離或臨時配置的service-restoration actions，不能直接當成HAZUS設備更換／完全重建時間。註解提到DS2包含travel/inspection，而排程另加道路旅行；實際校準是否重複包含travel仍需參數來源釐清，尚不直接判D。來源：[初始功能及修復參數](../C257H_Project_Main.py#L286)。

現有排程用 scenario mean duration，沒有偷用每次未來實現工時作oracle派工；它也沒有模擬根據已觀察DS／進度調整計畫。CDF从arrival=start起算，排程finish=arrival+mean repair；沒有「先延遲完整一次修復，再重新開始完整CDF」的明確double counting。但crew離開時功能未恢復完成：主情境每站依其DS機率加權的raw functionality，平均.544、範圍.480–.655。這需要選定語義：工班只是完成某一階段，後续可自動恢復，還是應佔用直到修复達標？前者需作業／時間資料，後者需一致的任務完成規則。不能用排程 makespan 直接稱全網電力恢復時間。[主程式 L3398](../C257H_Project_Main.py#L3398)；[主程式 L3433](../C257H_Project_Main.py#L3433)；[主程式 L3467](../C257H_Project_Main.py#L3467)；離場raw功能（完整本地查核包）。

平均次序核對：**先每次gate，再平均**，這一點做對了；但 T80(E[S]) 不等於 E[T80(S)]。现有主要輸出是前者，未保存每次各策略的完整KPI，不能从一條平均曲線補出策略差值CI。B積分是線性，固定排程下可以從平均曲線得到平均B；T80及尾端排名則不能這樣交換。[主程式 L2333](../C257H_Project_Main.py#L2333)；[主程式 L2388](../C257H_Project_Main.py#L2388)。

原始MC records在目前工作樹缺失；git舊檔是LFS pointer，本地物件未找到。本輪以原函式、seed42及worker分塊測試重建；32 workers 的92站平均DS和平均工時與保留結果吻合至浮點精度。再用該DS矩陣重播四個固定排程，8條人口／SVI曲線各9601點均與保留曲線吻合，最大誤差<9×10^-16。這是強的**有限重現證據**，仍不是找回原始檔bytes或完整UQ。[worker比對](audit_outputs/sample_reconstruction_check.csv)；[逐點曲線核對](audit_outputs/full_curve_reproduction_check.csv)；有限重播腳本（完整本地查核包）。

最小端到端方案应先固定決策資訊時點，例如震後初步DS已知、repair duration分布已知、未來工時未知；以同一physical realization對四策略採用相同需求／時間樣本。任務集合由該次需作業狀態決定，工班時鐘用實現duration，排序不得窺看其值；對oracle另標基準。再用明確支持的completion-to-function規則驅動同一source gate與W。每次保存T80、B、群體差距、尾端及策略差值；paired bootstrap只在physical realizations層抽樣。GA種子獨立嵌套，不能把GA重複當地震樣本數。

**3.4 GA與醫院規則的目標**

程式是任務排列編碼；解碼逐一派給目前最早空閒工班，而非逐候選尋找最早到達的crew。時間由靜態base-to-task／task-to-task矩陣、mean repair組成；没有utility轄區、專業工種、震後道路阻斷约束。工班來源是空間proxy；57crew不等於現實總可用專業能力。[主程式 L3326](../C257H_Project_Main.py#L3326)；[主程式 L4196](../C257H_Project_Main.py#L4196)；[道路矩陣建立](../build_travel_matrices_osm.py)。

GA參數：population100、generations100、ordered crossover .8、outer mutation .2、inversion mutation內另以.2觸發、tournament size3；98個隨機初始化，另加1個按task value遞減、1個按task time遞增的啟發式排列；CRC32 scenario/policy派生seed；eaSimple固定代數，無其他early stop、elitism或Hall of Fame，最後取final generation最佳。沒有保留多seed／收斂曲線可證明穩定。[主程式 L4036](../C257H_Project_Main.py#L4036)；[主程式 L4175](../C257H_Project_Main.py#L4175)。

服務components先按当前任务集合min–max：population=ΣP_rW_ri；hospital=ΣI(hospital tract)W_ri；SVI=Σ[P_rSVI_r／Σ(P·SVI)]W_ri。另混合20%結構score（.7 source-role／.2 voltage／.1 line數的設定，line cap12）。Balanced=(1,3,1,.5)、HospFirst=(1,20,1,.1)、Efficiency=(1,1,1,2)；服務部分按population/hospital/SVI權重和正規化。HospFirst的20不是20倍實際醫院供電：最後hospital normalized component的總係數=.8×20/22≈.7273。[主程式 L3878](../C257H_Project_Main.py#L3878)；[主程式 L3920](../C257H_Project_Main.py#L3920)；[主程式 L3943](../C257H_Project_Main.py#L3943)；[主程式 L4100](../C257H_Project_Main.py#L4100)。

實際fitness為 F=Σv_i(504−C_i)_+／(504Σv_i) − w_M C_max／504，504=480h evaluation horizon+24h buffer。它沒有在每個candidate中計算source-gated tract動態、T80或AUC。規則Hospital-first則先按有醫院tract的mapping連結數，再按未乘dependency的linked人口排序；與GA的dependency-weighted hospital coverage不是同一指標。兩者都不是醫院數／床位容量／運作率。[主程式 L3307](../C257H_Project_Main.py#L3307)；[主程式 L4148](../C257H_Project_Main.py#L4148)。

以相同保存task values、完成時間及504h horizon評估七規則＋三GA，完成4scenario×10schedule×3objective＝120次重算：

| 2pc50 排程 | 同一 HospFirst fitness，越大越好 | Population T80 h | Population AUC |
|---|---:|---:|---:|
| Hospital first | .922243 | 47.00 | .919260 |
| Impact population first | .923088 | 49.95 | .918646 |
| GA-HospitalFirst | .924922 | 49.80 | .916208 |

GA-HospitalFirst确实比Hospital rule更好地优化自己的保存目標，却服務指標較差，主因是目標不一致。全部12個scenario/objective組合中，對應GA都高於最佳規則，但多個組合可被另一GA策略的排程略為超越；2pc50 Balanced自身.875541，GA-Hosp按Balanced評價.877418。這表示有搜尋與初始化改善空間，不能證明全域最優。[120項fitness評估](audit_outputs/same_fitness_comparison.csv)；各目標優劣摘要（完整本地查核包）。

本轮不应為勝過Hospital rule調權重。建議先保留原GA為「不同任務價值目標」基準、加入簡單規則與跨GA相同fitness表，補seed和best-so-far trace；降低GA在主文的中心性。如果後續研究問題明確是最小化群體負擔或動態服務缺損，才新增對齊目標的策略，與原策略並列，不覆蓋旧結果。

**3.5 公平性：本輪已補做的實質結果**

SVI來源需整理成三條明確定義：系統曲線用 LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv 的 SOVI_SCORE，數值與NRI Mar-23表吻合（最大差<5×10^-9）；CDC California.csv 的 RPL_THEMES為另一个欄位；聚類SVIComposite又是四個theme percentile平均。FEMA在March2023已轉用CDC/ATSDR作SVI來源，因此不能因欄位叫SOVI就宣稱完全無關；但NRI derivative與現用CDC2022 RPL_THEMES不是同一組數值，確切底層版本仍需固定metadata。當前兩欄有效tract相關約.9468，不是1。[主程式 L109](../C257H_Project_Main.py#L109)；[主程式 L3513](../C257H_Project_Main.py#L3513)；[主程式 L5536](../C257H_Project_Main.py#L5536)；[FEMA March 2023 更新說明](https://content.govdelivery.com/accounts/USDHSFEMA/bulletins/352f5d2)。

本輪群體分析固定CDC RPL_THEMES quartiles（按tract分位分組，各組均值按人口加權）、同一480h horizon，排除24個負值sentinel tracts、16,979居民；分析母體2291 tracts／9,049,543居民。缺值沒有被當0。以 B_r=∫_0^480[1−S_r(t)]dt，單位為「模型服務缺損累積量，proxy h」，不是觀測停電小時。人口與脆弱度join（完整本地查核包）；[群體負擔與人口加權P90](audit_outputs/policy_group_burdens_CDC2022.csv)。

| 策略 | Q1低SVI，平均B | Q2 | Q3 | Q4高SVI，平均B | 有方向差距Q4−Q1 |
|---|---:|---:|---:|---:|---:|
| Hospital first | 41.122 | 38.546 | 37.913 | 37.603 | −3.519 |
| Population first | 41.862 | 39.442 | 38.084 | 36.987 | −4.875 |
| GA-HospitalFirst | 41.738 | 40.879 | 39.796 | 38.507 | −3.231 |
| GA-Efficiency | 44.094 | 43.203 | 41.847 | 40.809 | −3.285 |

高SVI組在這四策略下反而有較低模型負擔。不能事先寫成高SVI受損更多、策略縮小其不利差距；也不能只看絕對差值就稱公平改善。Population rule的Q4較Hospital rule少.616 proxy h，但全體平均負擔高.295 h；Hospital rule相對GA-Efficiency則四組平均負擔都較小。現有資料足以提出分配結果，無需預設公平必然犧牲效率。

全體2315tract、同一固定模型下，Hospital rule相對GA-Efficiency：

- 人口平均B降低3.709 proxy h；1776tract／6,905,607居民所在tract的B較低，539tract／2,160,915居民所在tract的B較高。
- 若採用較實質的1 proxy h門檻，改善1262tract／4,913,438居民，惡化378tract／1,475,653居民。
- 以每tract「平均服務曲線的T80」比較，1490tract／5,743,077居民較早，703tract／2,812,579居民較晚；其餘並列。T80時間格點為.05h。
- 均值改善未涵蓋所有尾端：Q1人口加權P90 B在Hospital rule為57.866，GA-Efficiency為57.698，前者略高。先報這些具体分位與變化，不堆疊不必要的inequality indices。

[受益／惡化計數](audit_outputs/beneficiaries_and_delays.csv)；所有tract的B變化含ID（完整本地查核包）；所有tract平均曲線T80（完整本地查核包）；T80受益／延後人口（完整本地查核包）。

「多少人」是这些tract内的居民數，不是逐個人已觀測受益，也不是實際用電客戶數。現在沒有逐次差值CI與映射替代檢查，所以均屬條件式發現。現有策略增加SVI importance，沒有顯式優化群體gap；應稱vulnerability-informed weighting，不能稱已證明equity-optimal policy。

**3.6 歷史比較、聚類與機制**

本地Cagnan2006引用的LADWP恢復里程碑是customer restored 50%/75%/90%/95%/100%對應7/11/19/26/168h。13.7h T80是75%至90%線性插值，非實測milestone。現存模型Northridge unconstrained T50=1.90、T75=11.80、T80=14.10、T90=35.60、T95=38.65h；所以只看T80近似會遮蔽早期過快、尾段過慢。地域由舊LADWP到現代部分LA都市區多utility、分母由customers到population proxy、資產年代與外部供電也不同。歷史各milestone並列（完整本地查核包）；Cagnan原文（本地來源檔）。

7月23稿discussion已說contextual scale check，這方向正確；全文摘要、結論中的outage duration、hospital power與政策保證仍需逐句降到proxy相應範圍。更新14.25→14.10、14.55–15.25→14.45–15.10；如果另有對應舊版輸出，应保留版本對照而非混用。沒有資料支持以這些milestones驗證tract prediction；修復參數對歷史資料是否經選擇／調整的完整記錄亦未找到，不能先宣布獨立驗證。

聚類input包括T80、InitSupply、dependency degree、impact、betweenness、HHI、pre1970、population density、NRI risk/building及SVIComposite；density/building採log處理。主情境GA-Balanced的T80已在輸入，群集「慢、高SVI、高風險」部分來自設計。hotspot則由T80、pre1970、NRI risk、SVI percentile加總，不是獨立觀測的空間因果證據。這些可保留為描述性typology與抽查抽樣框架，但若比較策略，应先固定群體／區域、再比較政策B／T80，不能每策略重新聚類後將群集變動當改善。[主程式 L5489](../C257H_Project_Main.py#L5489)；[主程式 L5700](../C257H_Project_Main.py#L5700)；[主程式 L5735](../C257H_Project_Main.py#L5735)；[cluster保留結果](../Stage%207%20Output_expanded/clusters_labels_final.csv)。

**3.7 哪些既有結果值得成為主線**

| 2pc50／57crew | Population T80 h | 原系統SVI-weighted T80 h | Schedule makespan h |
|---|---:|---:|---:|
| Hospital first | 47.00 | 46.15 | 61.884 |
| Impact population first | 49.95 | 48.15 | 61.507 |
| GA-HospitalFirst | 49.80 | 49.00 | 58.429 |
| GA-Efficiency | 59.10 | 59.10 | 54.632 |

指定四列核對無誤。GA-Efficiency較Hospital rule早7.25h完成排程，却晚12.10h达到population T80；GA-HospitalFirst早3.45h完成排程，但T80晚2.80h。Table4另兩列需更正：Degree-first實際makespan63.23、Closeness-first62.54，稿件寫反。全情境保留指標與schedule重算（完整本地查核包）；[規則排程](../Stage%204%20Output_expanded/Gantt_Data_Stage4.csv)。

這不是普遍不變的效率tradeoff。29crew下Hospital rule makespan99.21且T80=68.45，GA-Efficiency為102.57／86.95，Hospital在這兩指標同時較好；57crew才出現指定對比；86crew下GA-Eff makespan47.86較Hospital51.33早，而T80=43.25較42.25晚1h；114crew下皆近似並列且GA-Eff makespan反而略長。其他三地震情境可從 verified_system_metrics.csv比較，尚無跨情境paired physical-uncertainty證據支持某策略普遍優越。

跨地震情境的點估計並不維持主情境的普遍排序：

| 情境（57crew） | Hospital T80／makespan h | GA-HospitalFirst T80／makespan h | GA-Efficiency T80／makespan h |
|---|---:|---:|---:|
| Northridge | 14.45／35.697 | 14.50／35.463 | 14.70／35.463 |
| SanFernando | 6.20／31.751 | 6.10／31.751 | 6.05／31.751 |
| LongBeach | 11.95／26.570 | 11.90／26.057 | 11.95／26.057 |
| 2pc50 | 47.00／61.884 | 49.80／58.429 | 59.10／54.632 |

所以Hospital rule的主情境優势不能寫成全scenario優勢；SanFernando的GA-Eff較早達T80，LongBeach的GA-HospitalFirst在兩指標均較好，但弱情境T80差值僅.05–.25h，沒有paired uncertainty時不應宣稱實質顯著。見[四情境四策略原始指標對照](audit_outputs/cross_scenario_policy_comparison.csv)。

crew sensitivity的具体解釋：

| 工班 | 相對57crew的population T80 rank rho | 十策略T80最大−最小 h | 最快T80 |
|---:|---:|---:|---|
| 29 | .927 | 23.20 | Hospital rule 68.45；Population rule68.80 |
| 57 | 1.000 | 14.00 | Hospital rule47.00 |
| 86 | .791 | 2.80 | Hospital／Population rule42.25並列 |
| 114 | .234 | .10 | GA-Balanced42.15；多數42.20 |

資源稀缺時排序影響大；資源增多時接近無資源限制時間尺度，額外優化序列的絕對收益縮小。低rho不能單獨說模型不穩健，需同時報絕對差值、time resolution與uncertainty。29crew下Population rule的AUC亦高於Hospital rule，T80與整段積分又有差異。[逐策略crew結果](audit_outputs/crew_rankings.csv)。

已有repair-scale／IDW cutoff／gate .4–.6 sensitivity，不能列為從未做；但程式固定基準task order，crew變化只重解碼，沒有重新優化GA；IDW變化則用baseline station R(t)乘新W，未更新mapping-driven策略。它回答的是固定orders的條件穩健性。若改問不同資源／mapping下最佳政策如何改變，需重算受影響的排序與策略。[主程式 L4820](../C257H_Project_Main.py#L4820)；[主程式 L5007](../C257H_Project_Main.py#L5007)。

站點到tract差異可以做**線性帳目分解**：因B_r=ΣW_ri B_i，GA-Eff減Hospital的station effective-B差乘mapped人口可回算全體差。最大正向項包含CENTER(300232)約.620系統proxy h、STATION H HOLLYWOOD(303899).496、SAN FERNANDO(301636).420、DEL AMO(302187).403。全部station與tract IDs、排程起迄、W已保存供追蹤。這些是gate之後的effect accounting：upstream source／path changes已混在station effective curve，**不能把.620稱修CENTER的獨立因果收益**；若主文要因果歸因，須有限swap／source-path事件對照。站點帳目分解（完整本地查核包）；固定排程明細（完整本地查核包）；tract完整改變（完整本地查核包）。

對上述四個最大正向station項，保留排程的到站起始時間如下；Hospital rule較早派工與較低effective-B的方向一致，但完整效果仍同時受source/path gate影響：

| station ID／名稱 | Hospital arrival h | GA-Efficiency arrival h |
|---|---:|---:|
| 300232 CENTER | .237 | 25.780 |
| 303899 STATION H HOLLYWOOD | .273 | 23.352 |
| 301636 SAN FERNANDO | .363 | 23.515 |
| 302187 DEL AMO | .319 | 27.728 |

來源：完整本地查核包中的逐站既有排程、逐tract效果明細及station分解；這些資料共同使用，不能把此對照當獨立干預實驗。

**4. 最優先的三個實質問題與完成門檻**

| 優先問題 | 最小修訂 | 是否改核心模型 | 新資料／計算 | 什麼證據算處理完成 |
|---|---|---|---|---|
| 1. 社區服務推估的依據：92站、W與source proxy | 補逐站選擇crosswalk、線路狀態／手動覆寫證據；明示合成IDW距離與proxy範圍；做替代W與有限物理／設施對照。 | 起步可保留基準；只有證明錯接或需物理限制才改核心。改名稱不能替代支持。 | W變體只需92×2315×time矩陣後處理；邊／設施分層抽查；物理benchmark需額外電氣参数資料。 | 重要tract／群體差距與政策差值在可辯護映射／物理条件下的穩定與失效範圍可量化；不存在未說明的高影響錯接／source選取。若證據只能支持探索性proxy，全文相應縮限。 |
| 2. 任務完成、功能恢復與決策不確定性一致 | 明定情報時點與completion含義；統一修復抽樣分布；修復時間、crew釋放與功能演化接成一致事件；保存paired每次結果、分開GA seeds。 | 可能需改task／clock／恢復接口，不預設更換全部hazard或圖。若保留current stylization，需外部作業依據與限制基準定位。 | 先單scenario四策略100個paired realizations做pilot，再按區間穩定度擴展；可由3個crew條件形成1200個schedule evaluations。不是1200次完整地理管線。GA小型多seed另計。 | 每次任務／工班占用／功能定義一致，無未說明的無工班恢復；報策略差值CI、排名概率／近似並列，不以T80(mean)代mean(T80)。GA自目標改善與seed變動可查。 |
| 3. 把「誰受益、誰延後」變成主結果 | 保留同一SVI版本、分組、人口、480h horizon；主文報B、signed gap、尾端、paired tract改善／惡化及整體T80／makespan。 | 本輪已證明第一層分析不需改核心；只有欲提出equity-optimizing政策才新增目標。 | 四固定排程結果已完成；其他scenario／crew要補相同tract輸出或有限重播；最終CI依賴問題2、映射穩健依賴問題1。 | 可回答具体群體／人口數／負擔差／局部延後，且能指出結論在哪些資源、震害與映射條件成立。不能只用SVI-weighted T80作公平成功證據。 |

先處理1與2的定義與證據門檻，3的現有資料分析可以同步完成。不是先改GA讓它贏，也不是先增加MC次數。若上述pilot推翻目前較重要的政策差值，才擴大重跑與改寫主結論。

**5. 分階段修訂順序與計算規模**

| 階段 | 工作與依賴 | 計算規模／本輪狀態 |
|---|---|---|
| 投稿前必須：鎖版與錯誤更正 | 確認7/23候選與實際上傳材料；資料／程式／figure manifest；統一2315 vs2291、SVI欄位、300 vs375、Table4兩列、Northridge數字及repair分布。依賴此次對照表。 | 文稿／CSV校對；本輪定位與數值對照完成，尚未改稿。 |
| 投稿前必須：模型支持與UQ | 實施優先問題1、2的有限設計，先凍結task/completion定義再跑paired結果。未通過前不發布新政策排名。 | 先一scenario、四策略、100paired realizations；3資源條件共1200schedule evaluations的pilot。保存metrics，避免每次都留全體time cube；用精度／穩定度決定擴大，未估工期。 |
| 現有輸出即可補做 | 相同GAfitness120項、四策略社區負擔、beneficiaries、crew排名絕對差值、歷史多milestones、文獻對照。這些是已有資料後處理或本輪固定排程重建。 | 本輪已完成并交付CSV／圖；不是待執行空泛建議。四策略恢復重建用同1000DS、9601timepoints、92station，無GA搜尋。 |
| 投稿前必須：GA最低重現證據 | 保留原目標，至少在主情境對三policy作多seed pilot，規則與跨GA排程納入候選比較；保存每代best-so-far／mean及最終fitness。只對入選結果計算服務指標。 | 例10seeds×3policies×100pop×100gen，約30萬candidate evaluations；與physical MC分開，未在本輪執行。若刪減GA主張可相應縮小。 |
| 投稿前必須：文章重構 | 問題1、2結論固定後重寫摘要／結果／結論；Table1保留，標準演算法移附錄；以問題3組織社區發現。 | 文稿工作。先整理可保留主結論，避免目前就為未有CI的點估計寫政策保證。 |
| 有價值、非本輪必要 | 震後道路／交通變化、crew技能與跨utility協定、醫院備援與容量、完整LA AC模型、動態資訊更新、equity差距直接優化。 | 新資料和更大模型；只有擴大論文主張才成必要。它們不能取代前述較小但直接相關的驗證。 |

上述100realizations／10seeds是可檢查的起始pilot規模，不是已證明足够的樣本量。應以paired差值區間、尾端估計與近似並列的穩定度判定是否增加，而非預設100或1000一定足夠。

**6. 最多三個研究問題及主圖表**

| 研究問題 | 目前證據與缺口 | 核心圖表 |
|---|---|---|
| RQ1：在特定震害與資源條件下，較快完成全部排程，何時轉化為較快人口服務恢復、何時沒有？ | Table4／crew sensitivity已有直接證據；跨physical realizations區間待補。 | 主圖：makespan對population T80／平均B，按crew条件分面，加入paired uncertainty；Table4縮成最重要策略的精確比較。 |
| RQ2：相對明確基準策略，哪些tract／SVI群體負擔降低、多少居民所在tract改善、哪些群體或尾端延後？ | 本輪固定模型分析已回答第一層；外推依賴映射與UQ。 | 主圖：固定SVI組B＋signed gap；全tract ΔB／ΔT80地圖及受益／惡化人口表。 |
| RQ3：上述社區與政策差異對映射、source proxy及資源條件何時穩定、何時失效？ | 已有cutoff／gate／crew；替代W、有限物理benchmark與端到端uncertainty未完成。 | 主圖／表：效應差值矩陣與適用條件，不只列Spearman；少量station/path事件案例解釋差異。 |

現有Table1有用：保留並改為每項假設的來源、範圍與對哪個RQ重要。主文方法保留W定義、source gate、任務／完成事件、資訊時點、指標、對照策略；標準fragility抽樣、IDW推導、中央性公式、GA操作細節與完整參數移附錄。percolation／meshing若僅說結構脆弱而未解釋恢復決策，就作附錄描述；它們不是潮流冗餘或因果社區改善證據。critical stations只有在連到具體policy timing與tract變化時才適合主結果。聚類／hotspot以補充typology呈現。

本輪三面板診斷圖（完整本地查核包）直接呈現目標差異、SVI組負擔與局部勝負；它是revision診斷圖，還不是有完整不確定性與驗證的投稿定稿圖。

**7. 本地近鄰文獻與可成立的貢獻**

以下已讀原文的模型／方法與結果段落；不是只看題名或綜述。它們限制新穎性主張，也提供有限benchmark設計的參照。

| 本地研究 | 已做到、與本稿相近之處 | 本稿應避免的宣稱／可保留差異 |
|---|---|---|
| Cheng et al. 2024, Quantifying the Earthquake Risk…Los Angeles…Census Tract Level；DOI10.1109/ACCESS.2024.3408797 | 同LA、tract風險與社會／PV差異；LADWP提供bus／transformer／line與load資料，DC供電／load-shedding；地震damage與restoration情境。mapping也是近距離capacitated assignment並承認缺distribution資訊。 | 不能稱首次LA tract電力震害／社區差異；也不能把對方mapping說成feeder ground truth。可聚焦本稿可透明重現的修復序列、資源条件與paired受益／惡化分析。 |
| Xu et al. 2007, Optimizing scheduling of post-earthquake electric power restoration tasks；DOI10.1002/eqe.623 | LA utility restoration scheduling、stochastic durations、GA、task precedence／personnel／materials、customer outage目標，基於utility資訊。 | LA+GA+物流+不確定性不是新缺口。本稿GA目標更間接，不應以方法複雜度主張超越。 |
| Cagnan et al. 2006, Post-Earthquake Restoration Planning…；DOI10.1193/1.2222400 | 離散事件、恢復資源與歷史milestones；地區恢復差異。 | 歷史時間應完整對照；本稿貢獻須是社區決策結果及適用條件。 |
| Jiang et al. 2025, Uncertainty-aware Predict-Then-Optimize Framework…；DOI10.24963/ijcai.2025/1080 | repair-duration uncertainty預測、group coverage、equity-constrained sequencing與真實報修資料。 | 不能稱uncertainty/equity scheduling未被研究；其報修資料與地震傳輸網不同，不能直接借作本稿驗證。 |
| Chen et al. 2025, Toward Community-Centered Planning…；DOI10.1061/JMENEA.MEENG-6331 | 用demographics、SVI、公共設施調整power/water恢復，已有群體／關鍵服務導向。 | 整合人口、SVI與醫院不構成獨有貢獻；需量化誰改善、誰延後。 |
| Toplu-Tutay et al. 2024, Impact of power outages depends on who loses it；DOI10.1016/j.seps.2024.102036 | stochastic power-grid hardening、物理constraints與well-being loss／equity。 | 防災與震後排程不同，但公平不等於加權平均、且可和整體績效共同改善的議題已有基礎。 |

本地原文：Cheng 2024（本地來源檔）；Xu 2007（本地來源檔）；Cagnan 2006（本地來源檔）；Jiang 2025（本地來源檔）；Chen 2025（本地來源檔）；Toplu-Tutay 2024（本地來源檔）。

[Weaving equity into infrastructure resilience research](https://doi.org/10.1038/s44304-024-00022-x)提供分類與概念起點，不能單靠它宣布未有人做LA、equity或uncertainty scheduling。本輪尚未完成全面新穎性systematic review；現在可辯護的貢獻方向是：**在清楚限定的LA都市區proxy模型中，揭示資源條件如何改變排程完成、人口恢復與社區分配之間的關係，并量化受益／延後的空間分布與不確定性。** 其中前半已有結果，後半不確定性與映射／物理可信度仍需補。

**8. 投稿方向與完成／未完成清單**

本輪發現仍支持「**完成實質修訂後，PIDS作優先轉投方向**」這個暫定判斷。理由是已有可形成主線的災後資源決策與社區結果；目前不適合把稿件包裝成新的電力潮流模型、GA方法突破或已驗證的公平最優政策。PIDS也不會免除映射、proxy与不確定性的證據要求。這是研究定位判斷，不是已確認的轉投、送審或接受概率；本輪未操作ATS，也未重查邀請APC或期限。Results in Engineering可維持原備選，不因本輪結果另展開期刊清單。

如果有限物理／映射對照显示主要政策比較无法穩定、或task–recovery一致化改变核心結果，先依新證據重寫主張；換期刊不能代替這些處理。如果證據只足以支持方法示範，就收窄case-study政策含義，再決定期刊，而非承諾現有差值可以保留。

1. **完成：** 定位實際工作區、候選提交稿、原PDF、審稿文件、程式HEAD、關鍵輸出與figure雜湊。
2. **完成：** 八項程式鏈條、120項相同fitness評價、Table4指定四策略、crew敏感度、SVI／人口join、歷史milestones核對。
3. **完成：** 主情境四固定排程、1000重建DS的恢復重播，8條平均曲線逐點吻合；新增tract負擔、分組、尾端、受益／惡化人口、站點帳目分解與診斷圖。
4. **完成但有限：** 幾何圖重建、92站registration、六條最長邊抽查、刪除4個Proposed parts的component／六路徑檢查。未完成全部318邊／替代路徑的物理驗證。
5. **未找到：** 投稿系統收件版、完整92站選擇crosswalk、可直接驗證W的feeder／客戶對應、當前工作樹原始MC records、GA多seed／收斂輸出。
6. **尚未執行：** 端到端paired scheduling UQ、修復分布修正分支、completion物理校驗、替代W與有限電力benchmark、跨情境完整社區分配不確定性。本輪沒有把這些列為已完成。
7. **未修改：** 核心程式、原始資料、稿件與既有圖表；所有新腳本／CSV／PNG只在本audit目錄。

本輪證據索引：原始／文稿檔案索引（完整本地查核包）；[固定重播檢核](audit_outputs/full_curve_reproduction_check.csv)；審核資料與腳本manifest（完整本地查核包）。文件提取文字僅供定位，PDF Table4另已視覺核對。正式修稿時應從表列來源重新生成表格，避免手動抄寫與指標名稱對調。




## 公開快照的範圍

本目錄只納入聚合診斷結果，不含 `Reviewer.docx`、逐字審稿意見、投稿稿件副本、重建的 Monte Carlo 樣本或中間 NPZ。原始分析留在作者的本地查核包。提交時的 Git HEAD 為 `8dfbc5eff4a5eb74883015877caf922bf6163347`；核心程式及既有研究輸出未因本次查核而修改。

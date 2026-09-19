# 有限稳健性支持的条件性恢复决策研究：最终科学补强结果

2026-09-19。采用评估commit `5f998ed`的定位B；原Round26基准为`1d1015ff2d636bb36385267ce5a52df7ac28aefc`。所有旧结果、旧序列及旧报告保留。本报告取代其作为修订稿依据的策略比较结论，而不改写历史。

## 先回答科学问题

**纠正候选后，Round26的主要比较故事改变了。** Hospital-first不再是32次实现中人口负担的固定冠军。恢复的Balanced、HospFirst初始化候选，相对HF平均人口归一化负担分别减少0.295 h和0.166 h；95%配对bootstrap区间分别为[−0.404, −0.169]和[−0.257, −0.064] h。优势很小，不能渲染为大幅恢复改善。原“Balanced以更高社区负担换较短makespan/较低Gini”以及“HospFirst显著劣于HF”的论述必须删除。

**谁改善、谁被延迟：** 新Balanced在Q1–Q4平均负担均略低于HF，Q4减少0.438 h；新HospFirst的Q4减少0.413 h，但Q1增加0.117 h。因此，“三条GA使四组均恶化”已经不成立。Efficiency则仍使所有四组平均负担增加，Q4增加最多，为21.526 h。医院tract负担方面，Balanced/HospFirst与HF差异接近零；没有证据把hospital-dominant系数20解释为实证医院恢复优势。

**较低Gini/gap是否仍伴随恶化：只对Efficiency明确成立，不能泛指三条GA。** Efficiency基准Gini为0.1765，HF为0.2187，但平均人口负担高15.076 h；它缩小了Q4−Q1绝对差距，同时增加了Q1–Q4绝对负担。另一方面，新Balanced/HospFirst改善Q4的幅度大于改善Q1，反而使原本为负的Q4−Q1差距更负、绝对差距略扩大。由此可见，“改善较高脆弱度群体”和“使四分位负担更相等”在本模型中不是同一个判据。

**对假设的依赖：** A/B相对候选影响λ=0.5、1、2下，三策略相对HF的总体负担差异方向均不变；但Efficiency的Q4额外负担为22.558、21.526、20.377 h，自身signed Q4−Q1均值从+0.495变至−3.540 h。群体幅度及谁的负担较高，不能称完全mapping-invariant。DS4工时加倍后，Balanced/HospFirst相对HF仍是小幅改善；Efficiency额外人口负担升至26.245 h，比基准策略差异再增加11.169 h [9.303, 12.880]。重损工时改变的是比较代价的量级，而不只是共同的日历尺度。

**可以进入修订稿的主张：** 在明确D302/C57、参考source连通及官方candidate-based服务代理条件下，固定ex-ante恢复序列产生不同分配后果；系统完工、社区累计负担与群体相等程度不能互相替代；有限权重压力对照保留主要总体效应方向，但群体细节仍依赖假设；重损相对工时显著放大某些序列的社区代价。**必须撤回**GA最优、普遍HF优势、三GA均使四组恶化、公平优化/真实供电恢复、效率—公平最优边界等更强主张。

**决定：核心发现已足以支持定位B下的修订稿写作，但必须重写旧策略叙事。** 本任务没有发现需要再开一批模拟才能解释的具体科学逻辑失败。不自动运行C29/C114、额外工时情景、GA搜索或新mapping。

![科学补强结果概览](TARGETED_SCIENTIFIC_FINDINGS.png)

图中均为保存结果的统计。Balanced/HospFirst保留历史策略标签，但本次采用的是达到历史最高已记录fitness的**确定性初始化候选**，不是新GA搜索得到的改进。D面板只有四个政策点，不是Pareto边界。B面板为配对均值差及95%区间；接近零的两策略应结合下面数表阅读。

## 1. 实际执行与比较对象

完成64条纠正候选链与128条DS4×2链，复用HF/Efficiency原基准64条链；没有新增GA搜索，没有重新抽取损伤或工时。四策略始终使用相同realization ID的DS、对应工时向量、D302、C57、directed travel、graph、21-source情景、Architecture B及原W1。

唯一科学情景改变是DS4已保存duration×2；DS0–DS3不变，不改变残余功能、gate阈值0.5或任何序列。重新执行event scheduler及后续完整链，未将原trajectory简单乘二。两个A/B权重对照只在离线评价中实施，未与DS4情景交叉成factorial。

冻结序列及ex-ante fitness在第一次尝试前写入[输入manifest](STRENGTHENING_INPUT_MANIFEST.json)、[候选序列](FROZEN_CANDIDATE_SEQUENCES.csv)及[同目标评分](CANDIDATE_OBJECTIVE_COMPARISON.csv)。32个物理样本已被使用过，这是**既有评价集的纠正重评和成对假设对照**，不是新独立验证集；没有依据这些新社区结果再挑序列或调整目标。

实际完成科学链192条。调用尝试193次，其中第一次在scheduler输入类型验证处因`numpy.str_`而退出，尚未调度或产生科学输出；只将NPZ读取的ID显式转为原生`str`，值、顺序、科学输入不变。原manifest与错误记录保留于[修复记录](PREEXECUTION_HARNESS_REPAIR.json)和[执行日志](EXECUTION_JOURNAL.jsonl)，未把失败尝试隐藏成不存在。此后192条均完成，没有科学重复执行或调参重跑。

每条新链返回后立即保存任务事件、event times、raw/effective state、mask、service state、tract lower、上游/服务接口积分。任何后处理均读取这些保存对象；HF/Efficiency基准没有为补档而重跑。[计算来源](RESULTS_PROVENANCE.json)记录次数、hash不变与离线信息范围。主模型、scheduler、gate、exporter、service interface及科学输入均未改动。

## 2. GA候选纠正：改了选择，不改搜索目标

原`run_ga`返回最后一代最好候选；当前源码增加了独立best-so-far archive和显式HF incumbent比较。archive不进入population，不改变selection/replacement，亦不消耗RNG。未重跑30次GA。原Round26输出仍是最后代结果，不被重新标记为历代最优。

| 同一目标函数 | 原最后代canonical fitness | 本次采用fitness | HF incumbent fitness | 本次候选来源 |
|---|---:|---:|---:|---|
| Balanced | 0.780985337154 | 0.793690122004 | 0.792733835572 | 可重建的priority降序初始化 |
| HospFirst | 0.900607781997 | 0.916459946176 | 0.916319981609 | 可重建的priority降序初始化 |
| Efficiency | 0.368272354637 | 0.368272354637 | 0.338924957558 | 保留Round26 canonical，seed 47 |

两条初始化达到各自已记录历史最高分数（1e-12数值容差内）；这不是恢复了全部seed的未保存中间染色体，更不是找到了全局最优。Balanced/HospFirst的既有GA搜索没有提供超过这些确定性候选的已记录改进，不能把初始化的贡献归功于遗传演化。

两条恢复序列与HF相同rank的ID分别为195/302和224/302，均不是同一序列；Efficiency为1/302。Hash完整保存在候选CSV：Balanced以`51204d91…`开头，HospFirst以`8b29414d…`开头，Efficiency仍为`dd975231…`，HF仍为`0fe713a2…`。

仍使用原ex-ante ExpectedWork、C57和directed travel解码，Tmax=504 h、原policy-design coefficients、network-importance DROP。没有使用realized duration、社区负担或公平指标选择候选。保留目标为静态站点priority加权完工收益减makespan罚项；它不直接优化source-gated累计burden。`decode(E[duration])`也不等于`E[decode(duration)]`：crew释放、下一任务位置和最大完工时间都是非线性的。这说明surrogate与实际评价可能错位，不能据此宣称任何特定真实电网机制已经验证。

## 3. 指标、missing及统计对象

记R为每tract可识别A/B候选质量，L(t)为known available mass，P为人口。`B=∫(R−L)dt`，`N=B/R`；R=0则N为NA。event积分采用左端状态；每条链终点为任务完成且已表示服务状态稳定时。该点后已表示部分deficit为零，因此不同makespan对应的终点不是人为延长某策略负担。

- **人口加权tract N**：`Σ_{R>0}P N / Σ_{R>0}P`，分母3,520,382人。
- **人口×R一致的累计负担**：`ΣP B / ΣP R`，分母约3,426,254.42的人口×候选质量；等于resolved availability deficit面积。
- **T50/T80/T90**：`ΣP L(t)/ΣP R`首次达到阈值的event time，未从离线接口积分反推。
- **Q1–Q4**：复用固定NRI-derived SOVI quartiles；组内N按人口加权。Gini对R>0的N使用人口权重。
- **医院tract**：47个保留医院tract的N算术均值，不是医院运营能力或真实供电恢复。
- **12个完全不可识别tract、51,770人**：所有情景均`unresolved`，N及受益方向概率NA；不是near-zero或零负担。部分可识别tract仍纳入，解释为其已表示候选部分的条件负担。

所有区间以同一realization ID配对：32个单位、10,000次bootstrap，固定seed=20260919；同一重采样索引用于策略、情景及差异之差。没有把256条策略运行或tract数当独立物理样本。原Round26按strategy/metric使用seed offset；本次采用共同索引以保持情景间配对，因此复用结果的CI端点会有有限bootstrap差异，而点估计不变。特别是Efficiency旅行差异接近零的下端点，不用其是否刚跨零来制造结论。

±1 h是逐tract平均/单次配对效应分类的实用阈值，不是统计显著性阈值。人口百分比分母为全部817域人口3,572,152；另提供可识别人群分母。下文所有mean及CI均为条件模型内证据，不覆盖未检验的容量、实际配电损伤、crew资格或其它hazard模型假设。

## 4. 纠正基准：微小总体收益，而非旧版巨大代价

### 4.1 绝对均值

单位h，Gini除外。完整mean/SD/median/IQR见[指标分布](METRIC_DISTRIBUTIONS.csv)，逐次值见[逐实现策略指标](REALIZATION_STRATEGY_METRICS.csv)。

| 序列 | 人口加权N | 人口×R累计负担 | 人口T80 | 医院tract N | Gini | makespan | 总travel |
|---|---:|---:|---:|---:|---:|---:|---:|
| HF | 44.131 | 43.589 | 62.000 | 43.442 | 0.2187 | 165.552 | 121.161 |
| Balanced恢复候选 | 43.836 | 43.284 | 61.787 | 43.401 | 0.2184 | 165.505 | 120.830 |
| HospFirst恢复候选 | 43.965 | 43.414 | 61.803 | 43.419 | 0.2201 | 165.568 | 120.414 |
| Efficiency保留候选 | 59.207 | 58.852 | 73.790 | 55.686 | 0.1765 | 165.554 | 122.225 |

原Balanced/HospFirst的人口N为51.207、59.828 h，现在为43.836、43.965 h。改变来自候选选择纠正后的完整链复评，不是将fitness差换算成社区效果。与两种合法人口分母一致，总体结论相同。

### 4.2 相对HF的配对效应

数值为均值差[95%配对CI]；负burden/T80/logistics差代表该指标较低，不自动等于社会公平。

| 指标 | Balanced−HF | HospFirst−HF | Efficiency−HF |
|---|---:|---:|---:|
| 人口N(h) | −0.295 [−0.404, −0.169] | −0.166 [−0.257, −0.064] | +15.076 [13.959, 16.170] |
| 人口T80(h) | −0.214 [−0.756, 0.274] | −0.197 [−0.735, 0.204] | +11.790 [8.418, 15.369] |
| 医院tract N(h) | −0.041 [−0.145, 0.080] | −0.022 [−0.104, 0.066] | +12.244 [10.990, 13.471] |
| Q4 N(h) | −0.438 [−0.582, −0.277] | −0.413 [−0.549, −0.269] | +21.526 [20.355, 22.652] |
| Gini | −0.00031 [−0.00232, 0.00159] | +0.00143 [0.00009, 0.00276] | −0.04225 [−0.05327, −0.03157] |
| makespan(h) | −0.047 [−0.141, 0.047] | +0.016 [−0.073, 0.102] | +0.002 [−2.354, 2.508] |
| travel(h) | −0.331 [−1.148, 0.507] | −0.746 [−1.837, 0.386] | +1.064 [−0.004, 2.079] |

Balanced/HospFirst的平均人口改善分别约0.67%和0.38%，虽配对均值CI不含零，实际幅度仍小。T80、医院tract负担和makespan差异的区间覆盖零，不宣称实质医院优势或可靠物流节约。Efficiency并没有以可确认的平均makespan收益补偿其显著更高的社区负担。

人口N相对HF较低的实现比例为Balanced 90.625%、HospFirst 84.375%、Efficiency 0%。四策略中最低人口N的频率为HF 6.25%、Balanced 68.75%、HospFirst 25%、Efficiency 0%；不再是原Round26的HF 100%。然而makespan最低频率中Efficiency为53.125%，它的均值与HF仍接近——频率、幅度和均值区间不能混为一谈。[所有指标排名频率](METRIC_RANK_FREQUENCIES.csv)不构造总冠军。

### 4.3 谁承担代价

| 序列 | Q1 N | Q2 N | Q3 N | Q4 N | signed Q4−Q1 | 平均绝对gap |
|---|---:|---:|---:|---:|---:|---:|
| HF | 49.469 | 45.198 | 42.926 | 39.523 | −9.946 | 9.946 |
| Balanced | 49.326 | 44.975 | 42.567 | 39.085 | −10.241 | 10.241 |
| HospFirst | 49.585 | 45.152 | 42.633 | 39.111 | −10.475 | 10.475 |
| Efficiency | 62.437 | 56.619 | 57.019 | 61.049 | −1.388 | 2.666 |

Balanced对Q1–Q4的变化分别为−0.143、−0.223、−0.359、−0.438 h。HospFirst为+0.117、−0.046、−0.293、−0.413 h：Q1平均增加[0.039, 0.197] h，Q4平均减少[−0.549, −0.269] h。这是可量化的群体间分配改变，但不能归因于单一医院或SOVI系数，因为三policy系数组合并非单因素试验。

Efficiency的Q1–Q4分别增加12.968、11.421、14.093、21.526 h。因此更低Gini与更小绝对gap并不表示任何四分位平均改善。反过来，Balanced/HospFirst使较低基准负担的Q4进一步下降，绝对gap分别增加0.295、0.529 h；即使部分较高脆弱度群体受益，也不一定更接近群体相等。这是本文应讨论的决策张力，而不是把某个指标的下降直接命名为公平。

### 4.4 逐tract受益/延迟，不隐藏near-zero与未知

按每tract 32次平均配对N变化，以±1 h分类：

| 序列 | improved tract / 人口 | near-zero tract / 人口 | worsened tract / 人口 | unresolved |
|---|---|---|---|---|
| Balanced | 110 / 465,142（13.02%） | 686 / 3,015,785（84.42%） | 9 / 39,455（1.10%） | 12 / 51,770（1.45%） |
| HospFirst | 61 / 263,165（7.37%） | 741 / 3,245,315（90.85%） | 3 / 11,902（0.33%） | 同上 |
| Efficiency | 14 / 62,257（1.74%） | 128 / 597,887（16.74%） | 663 / 2,860,238（80.07%） | 同上 |

在此平均分类中，Balanced/HospFirst的worsened tract均在Q1；Q4分别有156,455与123,461人属于improved，占各自整个Q4人口16.74%和13.21%。Efficiency的Q4有838,825人属于worsened，占Q4人口89.77%。这是模型内的固定人口/tract分类，不是已验证真实居民的受益。

**不能把上表当作每次地震的人口比例。** 先逐次分类再取平均，Balanced的improved/worsened人口为15.02%/6.23%，HospFirst为7.75%/3.64%，Efficiency为13.31%/76.57%。Balanced单次worsened人口范围0.29%–51.85%；平均效应小幅改善并不保证每次实现多数局部tract均受益。[人口分类表](WINNER_LOSER_POPULATION.csv)分别标明两个统计对象；[逐tract配对表](TRACT_PAIRED_EFFECTS.csv)保留方向概率，unresolved始终NA。

证据层也不能混为一体。基准中S1 direct-only的Balanced/HospFirst相对HF为−0.298/−0.210 h，S2 attached-no-C为−0.343/−0.148 h；S3 partly-unresolved为+0.066/+0.133 h。原Balanced在S3改善的旧故事不再成立。这个分层是描述性诊断，不是随机分组因果证据。

## 5. 固定决策的A/B影响对照：总体方向稳定，群体细节有依赖

仅对混合A/B tract使用预声明公式：A权重乘`R/(A+λB)`，B权重乘`λR/(A+λB)`；C原样保留。所有非混合tract权重逐值不变；R、candidate集合、attachment、source和四条决策序列不变。原W1文件未修改，未按当时缺失状态重新分配权重。

旧HF/Efficiency用已证明可识别的接口积分重建；新Balanced/HospFirst使用直接保存积分。300829/303005始终合并，未任意分摊。λ=1重建与生产基准的积分最大差小于9×10⁻¹³ h。这里只评价积分burden、群体、Gini及分类；没有从积分恢复T80或时间轨迹。

| λ | 序列 | 相对HF人口N(h) | 相对HF Q4 N(h) | 该序列signed Q4−Q1均值(h) | 该序列Gini |
|---|---|---:|---:|---:|---:|
| 0.5 | Balanced | −0.300 | −0.460 | −10.563 | 0.2179 |
| 1 | Balanced | −0.295 | −0.438 | −10.241 | 0.2184 |
| 2 | Balanced | −0.291 | −0.415 | −9.853 | 0.2209 |
| 0.5 | HospFirst | −0.177 | −0.446 | −10.796 | 0.2196 |
| 1 | HospFirst | −0.166 | −0.413 | −10.475 | 0.2201 |
| 2 | HospFirst | −0.154 | −0.375 | −10.088 | 0.2227 |
| 0.5 | Efficiency | +15.134 | +22.558 | +0.495 | 0.1816 |
| 1 | Efficiency | +15.076 | +21.526 | −1.388 | 0.1765 |
| 2 | Efficiency | +15.053 | +20.377 | −3.540 | 0.1761 |

三策略的人口差异在两个端点的95%配对区间仍保持各自方向；幅度范围窄。群体却有值得保留的敏感性：相对λ=1，Efficiency在λ=0.5的Q4额外负担再增加1.032 h [0.952, 1.109]，在λ=2减少1.149 h [−1.235, −1.060]；其自身signed gap的点估计跨零。不能由总体稳健写成“不同脆弱度组相对位置也不受mapping假设影响”。

分类同样有边界：Balanced的平均improved人口比例从λ=0.5的14.05%变为λ=2的11.80%，worsened从1.62%至0.61%；HospFirst improved为7.55%至5.83%；Efficiency worsened为80.57%至78.89%。这些变化主要改变边界tract是否跨±1 h实用阈值，不是人口真实供电关系被重新验证。

0.5/2是设计压力情景，不是经验置信范围。此项支持的只是“相同决策下，对A/B相对候选影响的有限评价稳健性”。它不验证Class B真实接线、真实份额、配电站自身损伤可以忽略，也不回答按不同mapping重新优化会发生什么。

## 6. DS4相对工时：代价放大，不能说仅改变恢复时标

### 6.1 绝对水平

| 序列 | 人口N | 人口×R累计负担 | 人口T80 | 医院tract N | Q1 | Q2 | Q3 | Q4 | Gini | makespan | travel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HF | 77.025 | 76.178 | 109.194 | 76.410 | 85.339 | 79.004 | 75.281 | 69.403 | 0.2273 | 300.867 | 121.275 |
| Balanced | 76.789 | 75.934 | 108.661 | 76.439 | 85.306 | 78.843 | 74.959 | 68.997 | 0.2273 | 300.712 | 120.533 |
| HospFirst | 76.848 | 75.996 | 108.819 | 76.366 | 85.474 | 78.927 | 74.967 | 68.985 | 0.2280 | 300.791 | 120.719 |
| Efficiency | 103.270 | 102.750 | 125.417 | 96.752 | 108.696 | 98.312 | 99.327 | 107.233 | 0.1799 | 300.679 | 122.243 |

这不是新参数校准，不声称72 h更真实；是同样事先决策面对相对更长重损行动的压力对照。没有按新工时重新优化。

### 6.2 策略差异改变多少

“改变”严格为`(策略−HF)_DS4×2 − (策略−HF)_基准`，在同一32个realization上计算。下表的最后一列CI不是两独立样本CI相减。

| 指标 | 序列 | 基准策略差 | DS4×2策略差 | 策略差的改变[95%CI] |
|---|---|---:|---:|---:|
| 人口N(h) | Balanced | −0.295 | −0.236 | +0.059 [−0.022, 0.141] |
| 人口N(h) | HospFirst | −0.166 | −0.177 | −0.010 [−0.068, 0.049] |
| 人口N(h) | Efficiency | +15.076 | +26.245 | +11.169 [9.303, 12.880] |
| 医院tract N(h) | Balanced | −0.041 | +0.029 | +0.070 [−0.018, 0.157] |
| 医院tract N(h) | HospFirst | −0.022 | −0.045 | −0.022 [−0.081, 0.037] |
| 医院tract N(h) | Efficiency | +12.244 | +20.342 | +8.097 [6.199, 9.867] |
| Q4 N(h) | Balanced | −0.438 | −0.406 | +0.032 [−0.044, 0.112] |
| Q4 N(h) | HospFirst | −0.413 | −0.418 | −0.005 [−0.069, 0.065] |
| Q4 N(h) | Efficiency | +21.526 | +37.830 | +16.303 [14.317, 18.168] |
| makespan(h) | Balanced | −0.047 | −0.155 | −0.109 [−0.287, 0.073] |
| makespan(h) | HospFirst | +0.016 | −0.076 | −0.092 [−0.262, 0.075] |
| makespan(h) | Efficiency | +0.002 | −0.189 | −0.191 [−2.651, 2.435] |
| travel(h) | Balanced | −0.331 | −0.742 | −0.411 [−1.566, 0.735] |
| travel(h) | HospFirst | −0.746 | −0.556 | +0.191 [−1.411, 1.815] |
| travel(h) | Efficiency | +1.064 | +0.968 | −0.096 [−1.607, 1.457] |

DS4×2下Balanced/HospFirst的人口N相对HF的CI仍为负，分别[−0.358, −0.101]及[−0.276, −0.073] h；均值变化很小。人口优势不能同时扩写为明确医院或物流优势，这些差异的区间仍跨零。Efficiency的人口/医院/Q4额外负担明显放大，但其makespan与travel相对差异的变化并无清楚方向。这不是以更大系统物流收益换更大社区代价的证据。

Efficiency的较低Gini仍伴随所有组绝对恶化：相对HF，Q1/Q4增加23.356/37.830 h；Gini差−0.0474 [−0.0619, −0.0329]，绝对gap差−11.189 h [−13.762, −8.388]。而Balanced/HospFirst的绝对gap仍略扩大，分别+0.323、+0.493 h；不能把其Q4改善说成群体差距缩小。

按32次均值分类，Efficiency worsened人口从80.07%升至93.33%（763 tract、3,333,712人）；Balanced/HospFirst分别为1.56%和1.04%。**这不表示每次实现的worsened人口也同比上升：** Efficiency逐次分类后平均worsened比例为75.33%，基准为76.57%。谁在各次实现中受损、受损幅度与跨实现平均分类是不同统计量；不得把93.33%写成每次地震均有此比例居民被延迟。

最低人口N频率变为HF 15.625%、Balanced 56.25%、HospFirst 28.125%、Efficiency 0%。说明Balanced仍较常最低，但不是固定冠军；物流排名更不宜汇成一个总分。差异方向和幅度的这些变化是科学结果，不是软件失败。

## 7. 有证据的解释与不能编造的机制

本次保存的新任务事件表表明，对相同sequence，DS4加倍不仅延长最后完工：在两个恢复候选中，每次平均约300.47个任务，约220个任务的crew assignment改变，previous-task也约219–221个改变；平均arrival增加约32.14 h。这直接证明必须重新调度，不能简单缩放既有服务曲线。[配对物流机制表](PAIRED_LOGISTICS_MECHANISM.csv)仅比较确实保存了两情景事件的Balanced/HospFirst，未伪造HF/Efficiency原基准任务事件。

模型内积分accounting可进一步定位负担差异。Balanced基准人口优势−0.295 h中，接口310167与310204分别贡献−0.108及−0.094 h；HospFirst优势中310167贡献−0.116 h。Efficiency相对HF的额外负担中，310167、302187、301489分别贡献2.375、2.363、2.027 h；DS4×2下这三项增为4.166、4.008、3.464 h。[接口贡献表](INTERFACE_INTEGRATED_CONTRIBUTIONS.csv)也按Q组保存，并保留300829/303005合并项。

这些是固定attachment/W下的**积分贡献**，不是现实社区因果解释。HF/Efficiency原基准没有保存完整事件过程，不能把其所有接口差异归因于某个站的自身完工顺序，也不能编造医院地理、脆弱度或线路位置的因果故事。新事件存档提供了后续查证条件，但本报告没有将尚未分析的细部机制作成已证实结论。

### HF与HospFirst现在为什么不同

两条sequence不同，但224/302个站的rank相同；恢复候选的ex-ante surrogate比HF高约0.000140，社区评价也只有小幅总体差异。新结果不支持原“简单HF明显击败GA-HospFirst”的叙述，不能保留旧解释。医院tract负担差异接近零且区间跨零，权重20只是构造hospital-dominant benchmark的设计系数。

更有证据的目标错位实例现在是Efficiency：它自己的surrogate优于HF，但社区人口/医院/Q4负担明显更高，而平均makespan优势不明确。解释应指向静态完工收益与source-gated社区积分、expected-work解码与随机event调度的不同对象；不是GA软件失败，也不是“优化了公平但公平无用”。

## 8. 哪些主张保留、限定或删除

| 主张 | 处理 | 理由 |
|---|---|---|
| HF在32次中始终最低人口负担 | 删除 | 原比较使用退化最后代候选；纠正后HF最低频率仅6.25%（基准） |
| Balanced以更大社区代价换较短makespan/低Gini | 删除旧结论 | 恢复候选小幅降低人口负担，平均makespan/Gini与HF接近 |
| 三GA的Q1–Q4全部恶化 | 删除 | 新Balanced四组均改善；新HospFirst主要为Q1小增、Q3/Q4小减 |
| Efficiency较低Gini/绝对gap伴随较高绝对负担 | 保留，明确范围 | 两个工时情景及有限A/B影响对照支持；不是公平改进 |
| 固定序列改变负担分配，指标可能冲突 | 保留为主要发现 | 群体水平、逐tract分类及物流cost都有实际配对证据 |
| 恢复假设只控制总体时长、不影响策略代价 | 删除 | DS4×2使Efficiency人口差异再扩大11.169 h、Q4差异扩大16.303 h |
| mapping已真实验证或所有群体关系稳健 | 删除/限定 | 总体差异方向稳定，但群体幅度和Efficiency signed gap点估计依赖λ |
| GA已求得最优政策/公平—效率边界 | 删除 | 两候选来自初始化，未优化公平；四个点非最优边界 |
| C57或工时代表真实LA应急能力/经验修复时间 | 限定 | pooled resource及未校准on-site duration scenarios，非实证staffing |
| source-connected proxy等于真实供电 | 删除/限定 | 无容量、功率平衡、配电自身损伤验证；本轮通过范围限定回应 |

本报告不声称共同proxy会消除相对偏差，也不把两个有限对照说成覆盖全部模型不确定性。结论针对固定2pc50 PGA图下的DS/工时实现，非32个空间地震动联合抽样的地震事件。Class C质量始终未知，Class B自身配电损伤未建模。没有依据据此给出现实跨utility派工、actual power restoration或社会公平因果建议。

## 9. 可直接用于稿件的核心结论草稿

以下英文是Results/Discussion/Abstract的核心段落草稿，不是整篇稿件重写；引用数字来自本报告和配套数据。

### Results draft

After correcting candidate retention, the Balanced and hospital-dominant benchmark sequences were recovered from deterministic initializers that attained their respective highest recorded surrogate scores. No new genetic search or physical sampling was performed. Across the same 32 paired realizations, these sequences reduced population-weighted normalized tract burden relative to Hospital-first by 0.295 h (95% paired bootstrap CI: 0.169–0.404 h reduction) and 0.166 h (0.064–0.257 h reduction), respectively. These were modest improvements; differences in hospital-tract burden, population T80, and makespan were small and their paired intervals included zero. Balanced reduced mean burden in all four fixed NRI SOVI quartiles, whereas the hospital-dominant sequence reduced Q4 burden by 0.413 h while increasing Q1 burden by 0.117 h. Because Q4 had lower baseline burden than Q1, these changes slightly widened the absolute between-quartile gap.

The retained Efficiency sequence exhibited a different distributional pattern. Its mean burden Gini was lower than Hospital-first (0.1765 versus 0.2187), yet population-normalized burden was 15.076 h higher and Q4 burden was 21.526 h higher. All four quartiles experienced higher mean absolute burden. Under doubled stored DS4 durations, its excess population burden increased to 26.245 h, an additional paired contrast of 11.169 h (95% CI: 9.303–12.880 h), while excess Q4 burden increased to 37.830 h. The population effects of the two recovered initializer benchmarks remained small and favorable. These comparisons did not demonstrate a corresponding mean makespan advantage for Efficiency.

### Discussion draft

These results separate distributional consequences from an equity-optimization claim. Lower relative dispersion or a smaller absolute quartile gap did not necessarily indicate an improvement for any vulnerability group. Conversely, a reduction in burden for the higher-vulnerability quartile could widen the gap when that quartile already had lower modeled burden. Such observations support examining group-specific levels and tract-level paired effects alongside aggregate indicators, rather than interpreting a single inequality statistic as a welfare verdict. The benchmark policies changed multiple coefficients and were not designed as isolated interventions on hospital or vulnerability priority; their differences therefore should not be attributed to any single coefficient.

The evidence is conditional on a source-connected availability proxy and an official-candidate-based service representation. Varying the relative Class B influence from 0.5 to 2 while preserving candidate membership, Class C mass, resolved mass, and all decisions left the direction of population effects unchanged, but altered group-level magnitudes and the sign of the Efficiency sequence's mean Q4–Q1 gap. This is a limited fixed-decision evaluation stress test, not validation of actual service shares, named-system wiring, downstream damage, or delivered electricity. Doubling only DS4 durations showed that assumptions about relative severe-damage workload can amplify the community cost of a sequence even when its relative logistics performance changes little. The surrogate benchmark should accordingly be interpreted as a transparent planning heuristic rather than a community-burden optimum.

### Abstract/conclusion draft

We compare four fixed ex-ante restoration sequences under a conditional D302 network, pooled 57-crew resource scenario, and candidate-based strict-SCE service representation, using 32 paired damage and on-site-duration realizations. Correcting retention of previously evaluated optimization candidates removed the earlier appearance of a large Hospital-first advantage: two recovered initializer sequences offered modest population-burden reductions without a clear mean logistics advantage. A retained efficiency-oriented surrogate sequence produced lower burden inequality but higher absolute burden in every vulnerability quartile. Doubling severe-damage durations increased this sequence's excess population burden from 15.1 to 26.2 h, while a limited A/B influence-weight stress test preserved overall effect directions but altered group-level relationships. The findings show how restoration sequences redistribute modeled burden, and why lower inequality, faster system completion, and improvements for higher-vulnerability communities are distinct decision criteria. They do not establish optimal equitable policies or predict actual electricity restoration.

## 10. 数据及复核路径

- [FROZEN_CANDIDATE_SEQUENCES.csv](FROZEN_CANDIDATE_SEQUENCES.csv)：302-ID完整序列、来源、hash；[CANDIDATE_OBJECTIVE_COMPARISON.csv](CANDIDATE_OBJECTIVE_COMPARISON.csv)：原/恢复/HF/采用候选同目标评分。
- [REALIZATION_STRATEGY_METRICS.csv](REALIZATION_STRATEGY_METRICS.csv)：四个condition的逐实现指标。两个AB condition的T80、makespan等未由积分计算，保留NA；`corrected_baseline`对应λ=1。
- [PAIRED_EFFECTS.csv](PAIRED_EFFECTS.csv)：`strategy_minus_HF`、`condition_minus_baseline_within_strategy`、`change_in_strategy_minus_HF`、`candidate_correction_minus_R26`，含均值/中位数/方向频率/95%CI。
- [GROUP_ABSOLUTE_BURDEN.csv](GROUP_ABSOLUTE_BURDEN.csv)、[METRIC_DISTRIBUTIONS.csv](METRIC_DISTRIBUTIONS.csv)、[METRIC_RANK_FREQUENCIES.csv](METRIC_RANK_FREQUENCIES.csv)：群体/证据层及不确定性，不合成总排名。
- [TRACT_PAIRED_EFFECTS.csv](TRACT_PAIRED_EFFECTS.csv)、[WINNER_LOSER_POPULATION.csv](WINNER_LOSER_POPULATION.csv)：逐tract及全域/四分位的人口分类；区分均值分类和逐实现分类；unknown不入near-zero。
- [TARGETED_SCIENTIFIC_EVIDENCE.npz](TARGETED_SCIENTIFIC_EVIDENCE.npz)：逐实现/策略/tract的N与mass burden、R、population、固定Q、两工时向量和可识别上游积分。没有覆盖原Round26证据。
- [SCIENTIFIC_RUN_CHECKPOINTS.zip](SCIENTIFIC_RUN_CHECKPOINTS.zip)：192条新链逐条的`evidence.npz`和`task_events.csv`；[NEW_RUN_TASK_EVENTS.csv.gz](NEW_RUN_TASK_EVENTS.csv.gz)为紧凑合并事件表。
- [REVIEWER_RESPONSE_EVIDENCE_MATRIX.md](REVIEWER_RESPONSE_EVIDENCE_MATRIX.md)：逐条连接本次科学证据与范围限定回应。

全部新增数据保留在此目录；原报告、原manifest、原序列和原科学结果均未覆盖。唯一既有代码修改为GA输出archive/incumbent层；其旧版由原commit保留，新旧hash见本次manifest。后处理可重复运行，不需再次执行科学链。

**下一步是以此有边界的科学发现写Results、Discussion及审稿回应，不再默认启动更多模拟。**

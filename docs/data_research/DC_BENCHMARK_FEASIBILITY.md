# DC benchmark feasibility

## Determination

**Facility-only electrical adequacy benchmark feasible.** A full real Los Angeles DC benchmark is not feasible from the retained public files. The SCE GNA table provides 34 internally consistent 2026 voltage-level facility rows across 28 retained stations, sufficient to show that source reachability and documented planning adequacy are different concepts. It does not provide a coherent bus/branch network case.

The project must not combine the CEC 92-node abstraction, SCE GNA loads, isolated LADWP ratings, EIA generation, and generic reactance into a purported real LA model. A defensible DC load-shedding case requires, in one compatible case and operating vintage: bus topology and voltage, branch endpoints and status, branch reactance/base and ratings, bus active-power load, generator/import bounds, and slack/boundary treatment.

## Available access routes

- **Cheng et al. (2024):** the retained paper documents a utility-provided 432-bus/545-branch LADWP model with loads, generation, branch capacities, external injections, DC load flow and load shedding. The paper, NSF-PAR record and retained author/publication pages do not expose the input case, an anonymized subset, or a station/bus crosswalk. The targeted unsent request is in `CHENG_LADWP_DATA_REQUEST_DRAFT.md`.
- **CAISO:** transmission planning base cases require an approved WECC Base Case Data Request Package and a Regional Transmission NDA before CAISO access. Secure regional cases may contain compatible bus/branch data, but LADWP internal detail is not guaranteed.
- **WECC:** the public case list is a catalog, not model data. Restricted team-site/base-case access requires an account and executed confidentiality/base-case permissions.
- **FERC Form 715:** Parts 2–6 are treated as CEII. A requester must submit the CEII request and applicable NDA with a detailed statement of need. Exact years, respondents and native formats must be requested; approval and LADWP/SCE detail are not guaranteed.

## Minimum next acquisition

The highest-value request is the anonymized Cheng/LADWP case or a reduced validation subset preserving bus/branch structure, X, ratings, load, source bounds and reference-bus treatment. Failing that, request aggregate outputs for a specified comparison between binary reachability and constrained DC load shed. FERC/CAISO/WECC routes are valuable only if their released case contains enough LADWP/SCE detail and permits research use.

The supplied archive named `source_gate_electrical_adequacy_research_partial_20260926(1).zip` was not present in the repository, Downloads directory, or other searched project roots in this execution environment. Its absence is not interpreted as absence of the underlying data; the retained `External_Validation_Data` package and current official access pages were used instead.

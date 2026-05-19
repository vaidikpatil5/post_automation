"""
Persistent strategic worldview structures for worldview-first cognition.

Articles activate narrative priors — they are not treated as blank reasoning problems.
"""

from editorial_intelligence import build_article_text, cosine_scores, encode_texts

MATCH_TOP_K = 3
MATCH_MIN_SCORE = 0.30
KEYWORD_BOOST = 0.06

_prior_embeddings = None

NARRATIVE_PRIORS = [
    {
        "id": "distribution_replacing_product",
        "name": "Distribution Replacing Product",
        "description": "Competitive advantage shifts from product features to customer access and routing.",
        "core_pattern": "Product commoditization redirects value capture to customer routing and gatekeeping channels.",
        "core_mechanism": "Rising customer acquisition costs squeeze product margins, forcing builders to compete on features while channel gatekeepers capture the economic surplus.",
        "trigger_patterns": ["channel partnerships", "platform distribution", "go-to-market spend", "retail footprint"],
        "mechanism_patterns": ["acquisition costs", "commoditization", "routing layer", "value capture"],
        "expectation_violation": "Excellent product features fail to translate to market share or sustainable growth because customers default to pre-existing channel configurations.",
        "editorial_tension": "Startups continue to focus on engineering better product features while incumbents with established channels win customer access.",
        "example_implications": ["Startups must buy distribution earlier", "Incumbents with channels outlast better products"],
        "keywords": ["distribution", "gtm", "channel", "routing", "marketplace", "platform"],
        "example_posts": ["Distribution is the product when acquisition costs dominate unit economics."],
        "recommended_templates": ["competing_on_y_not_x", "value_controlling_y_not_x"]
    },
    {
        "id": "ai_compressing_junior_labor",
        "name": "AI Compressing Junior Labor",
        "description": "Automation targets repeatable cognitive work first, thinning junior roles before senior judgment layers.",
        "core_pattern": "AI copilots eliminate repetitive cognitive work, flattening traditional organizational pyramids.",
        "core_mechanism": "Copilots and agents absorb drafting, analysis, and support tasks — firms need fewer junior hires per senior output.",
        "trigger_patterns": ["copilot rollout", "hiring freeze", "layoffs", "automation tools", "headcount reduction"],
        "mechanism_patterns": ["labor displacement", "junior work", "leverage", "headcount compression"],
        "expectation_violation": "Increased productivity leads to organizational contraction and hiring freezes rather than hiring expansion.",
        "editorial_tension": "Companies produce more output with smaller teams, reducing the entry paths for junior talent to develop judgment.",
        "example_implications": ["Pyramid org shapes flatten", "Junior hiring becomes selective not scalable"],
        "keywords": ["copilot", "layoff", "hiring freeze", "junior", "automation", "headcount", "agent"],
        "example_posts": ["Copilots don't replace teams — they replace the bottom of the pyramid first."],
        "recommended_templates": ["more_for_y_less_for_x", "operational_complexity_lives_in_y"]
    },
    {
        "id": "infrastructure_becoming_moat",
        "name": "Infrastructure Becoming Moat",
        "description": "Durable advantage moves to reliability, scale, and embedded operational systems — not UI.",
        "core_pattern": "Defensibility moves from front-end features and UI design to operational infrastructure.",
        "core_mechanism": "When switching costs are operational (data pipes, compliance, uptime), infrastructure depth beats feature velocity.",
        "trigger_patterns": ["downtime", "sla", "compliance", "integration depth", "data gravity"],
        "mechanism_patterns": ["switching cost", "compliance", "reliability", "infrastructure"],
        "expectation_violation": "Simple, sleek user interfaces lose contracts to complex, legacy backends with high reliability.",
        "editorial_tension": "Startups spend on UI polish while customers pay for uptime and data gravity.",
        "example_implications": ["Feature parity stops mattering", "Reliability budgets become strategic"],
        "keywords": ["infrastructure", "reliability", "sla", "compliance", "integration", "uptime"],
        "example_posts": ["The moat is what breaks if you migrate — not what you see in the demo."],
        "recommended_templates": ["moat_moving_x_to_y", "strategic_over_technical_shift"]
    },
    {
        "id": "software_margin_compression",
        "name": "Software Margin Compression",
        "description": "Software economics compress as build costs fall, competition rises, and AI adds inference COGS.",
        "core_pattern": "The decline of high software gross margins due to AI coding tools and model inference costs.",
        "core_mechanism": "Lower build barriers and AI-assisted development increase supply; inference and support costs eat gross margin.",
        "trigger_patterns": ["pricing cuts", "open source", "ai coding", "seat compression", "freemium"],
        "mechanism_patterns": ["cogs inflation", "price compression", "unlimited supply", "monetization collapse"],
        "expectation_violation": "High-revenue software products struggle to maintain historical 80%+ gross margins.",
        "editorial_tension": "Shipping features is cheaper than ever, but monetizing them is harder due to structural COGS.",
        "example_implications": ["Seat-based pricing weakens", "Services attach to survive margins"],
        "keywords": ["margin", "pricing", "seat", "arr", "cogs", "inference", "open source"],
        "example_posts": ["When everyone can ship features, pricing power moves to distribution or workflow lock-in."],
        "recommended_templates": ["competing_on_y_not_x", "operational_complexity_lives_in_y"]
    },
    {
        "id": "logistics_as_competitive_advantage",
        "name": "Logistics as Competitive Advantage",
        "description": "Physical routing, fleet utilization, and fulfillment density become the bottleneck — not software UX.",
        "core_pattern": "Digital interfaces commoditize in logistics, shifting margins to physical utilization.",
        "core_mechanism": "Margin accrues to operators who control physical throughput and asset utilization, not dashboards alone.",
        "trigger_patterns": ["fleet", "fulfillment", "freight", "last mile", "warehouse", "trucking"],
        "mechanism_patterns": ["asset utilization", "physical density", "fleet routing", "throughput bottleneck"],
        "expectation_violation": "Sophisticated digital supply chain software fails to solve low physical asset utilization.",
        "editorial_tension": "Software players must integrate physical operations or face margin collapse.",
        "example_implications": ["Software layer commoditizes", "Asset utilization drives profit"],
        "keywords": ["logistics", "freight", "fulfillment", "fleet", "trucking", "supply chain"],
        "example_posts": ["In logistics tech, the algorithm is only as good as asset utilization."],
        "recommended_templates": ["value_controlling_y_not_x", "more_for_y_less_for_x"]
    },
    {
        "id": "operational_leverage_replacing_branding",
        "name": "Operational Leverage Replacing Branding",
        "description": "Winners optimize unit economics and process throughput — brand spend cannot fix broken operations.",
        "core_pattern": "Process automation and cost structure optimization replace brand equity as the primary defensive moat.",
        "core_mechanism": "When categories mature, efficiency and cost structure beat awareness campaigns.",
        "trigger_patterns": ["unit economics", "cost reduction", "process automation", "throughput"],
        "mechanism_patterns": ["margin expansion", "process efficiency", "cac compression", "structural leverage"],
        "expectation_violation": "Large advertising campaigns fail to sustain market share against low-cost, automated operations.",
        "editorial_tension": "Marketing spend acts as a temporary patch over broken, high-cost operational processes.",
        "example_implications": ["Brand-heavy players lose on price", "Ops excellence becomes positioning"],
        "keywords": ["unit economics", "cac", "throughput", "efficiency", "automation", "margin"],
        "example_posts": ["Brand is a tax you pay when operations don't compound."],
        "recommended_templates": ["competing_on_y_not_x", "moat_moving_x_to_y"]
    },
    {
        "id": "incumbents_benefiting_from_ai",
        "name": "Incumbents Benefiting from AI",
        "description": "AI adoption rewards installed base, data access, and distribution — not only startups.",
        "core_pattern": "Installed distribution channels and data access give legacy firms an advantage in AI adoption over startups.",
        "core_mechanism": "Incumbents embed AI into existing workflows and contracts; startups fight procurement and trust cycles.",
        "trigger_patterns": ["enterprise rollout", "incumbent partnership", "on-prem", "existing customer base"],
        "mechanism_patterns": ["distribution lock-in", "procurement barriers", "bundling", "enterprise trust"],
        "expectation_violation": "Startups with superior AI technology lose enterprise contracts to slow-moving incumbents.",
        "editorial_tension": "The speed of startup innovation is throttled by enterprise procurement cycles and security standards.",
        "example_implications": ["Startup disruption narrative weakens in regulated enterprise", "Bundling beats point solutions"],
        "keywords": ["incumbent", "enterprise", "legacy", "installed base", "procurement"],
        "example_posts": ["AI often increases switching costs for customers already on the incumbent stack."],
        "recommended_templates": ["strategic_over_technical_shift", "more_for_y_less_for_x"]
    },
    {
        "id": "ai_reducing_value_of_junior_work",
        "name": "AI Reducing Value of Junior Work",
        "description": "Tasks that trained junior talent become automated — firms must rethink talent pipelines.",
        "core_pattern": "The automation of entry-level tasks disrupts professional training pipelines.",
        "core_mechanism": "Training via grunt work collapses; judgment-heavy roles remain while entry paths shrink.",
        "trigger_patterns": ["intern programs cut", "junior roles", "ai assistant", "workflow automation"],
        "mechanism_patterns": ["training collapse", "judgment development", "junior displacement", "automation gap"],
        "expectation_violation": "Productivity gains from AI tools make it harder to hire and train the next generation of engineers or analysts.",
        "editorial_tension": "Short-term savings from junior automation create long-term talent shortages.",
        "example_implications": ["Talent pipelines break", "Senior leverage rises per head"],
        "keywords": ["junior", "intern", "entry-level", "copilot", "automation"],
        "example_posts": ["If juniors don't do the repetitive work, companies must train judgment another way."],
        "recommended_templates": ["operational_complexity_lives_in_y", "shift_not_x_but_y"]
    },
    {
        "id": "distribution_control_as_infrastructure",
        "name": "Distribution Control as Infrastructure",
        "description": "Owning the pipe to demand (retail, bonds, APIs, marketplaces) is strategic infrastructure.",
        "core_pattern": "Control over supply chain or capital routing channels acts as infrastructural gatekeeping.",
        "core_mechanism": "Firms vertically integrate distribution to lower cost of capital, CAC, or fulfillment access.",
        "trigger_patterns": ["acquisition", "marketplace", "bond platform", "retail channel", "api gateway"],
        "mechanism_patterns": ["vertical integration", "channel control", "liquidity access", "middleman compression"],
        "expectation_violation": "Better interest rates or cheaper products lose to channels that control direct customer routing.",
        "editorial_tension": "Financial or physical products become commodities; value shifts to who owns the transaction gateway.",
        "example_implications": ["Balance-sheet players buy distribution rails", "Intermediaries get disintermediated"],
        "keywords": ["distribution", "marketplace", "platform", "acquisition", "bond", "retail"],
        "example_posts": ["Owning distribution is how you price the product — not the other way around."],
        "recommended_templates": ["value_controlling_y_not_x", "moat_moving_x_to_y"]
    },
    {
        "id": "enterprise_ai_moving_on_prem",
        "name": "Enterprise AI Moving On-Prem",
        "description": "Regulated enterprises pull sensitive inference and data inside the firewall.",
        "core_pattern": "Sovereign cloud, data residency, and audit requirements pull AI models inside corporate firewalls.",
        "core_mechanism": "Data residency, audit, and cost control push hybrid/on-prem deployments over pure SaaS APIs.",
        "trigger_patterns": ["on-prem", "private cloud", "data residency", "sovereign ai", "vpc"],
        "mechanism_patterns": ["data security", "cost containment", "private inference", "audit trail"],
        "expectation_violation": "Public cloud AI API usage drops as enterprise spends capital on private model infrastructure.",
        "editorial_tension": "Startup-friendly API platforms are locked out of high-paying enterprise contracts.",
        "example_implications": ["Cloud API growth slows in regulated verticals", "Hardware/local inference rises"],
        "keywords": ["on-prem", "private", "sovereign", "vpc", "enterprise", "regulated"],
        "example_posts": ["Enterprise AI spend shifts to where data already lives — not where demos run fastest."],
        "recommended_templates": ["moat_moving_x_to_y", "more_for_y_less_for_x"]
    },
    {
        "id": "ai_agents_shifting_value_to_orchestration",
        "name": "AI Agents Shifting Value to Orchestration",
        "description": "Agent reliability depends on workflows, tool routing, and failure recovery — not raw model IQ.",
        "core_pattern": "Agentic reliability depends on orchestration frameworks and sandboxed environments, not raw model capability.",
        "core_mechanism": "Autonomous tasks need state, retries, and guardrails; orchestration layers capture value.",
        "trigger_patterns": ["agent", "workflow", "tool use", "orchestration", "failure recovery", "sandbox"],
        "mechanism_patterns": ["state management", "reliability tools", "orchestration layer", "retry engineering"],
        "expectation_violation": "High benchmark scores fail to translate to reliable agents in messy production environments.",
        "editorial_tension": "Companies optimize model parameters when they should be optimizing execution environment stability.",
        "example_implications": ["Middleware and ops tooling rise", "Model benchmarks matter less than reliability"],
        "keywords": ["agent", "orchestration", "workflow", "tool", "sandbox", "reliability"],
        "example_posts": ["Agents need persistent workflows and failure recovery — orchestration becomes the product."],
        "recommended_templates": ["moat_moving_x_to_y", "operational_complexity_lives_in_y"]
    },
    {
        "id": "retail_investors_becoming_capital_source",
        "name": "Retail Investors Becoming Capital Source",
        "description": "Retail channels supply liquidity and lower cost of capital for issuers and lenders.",
        "core_pattern": "Direct-to-retail investment platforms bypass institutional brokers.",
        "core_mechanism": "Bond platforms and retail apps let firms bypass traditional institutional distribution.",
        "trigger_patterns": ["retail bond", "yield", "marketplace", "investor platform", "d2c finance"],
        "mechanism_patterns": ["middleman disintermediation", "capital pooling", "yield distribution", "cost of capital"],
        "expectation_violation": "Traditional investment banks lose underwriting fees to direct-to-consumer financial platforms.",
        "editorial_tension": "Institutional gatekeepers are disintermediated by yield-seeking individual investors.",
        "example_implications": ["Lenders integrate retail pipes", "Institutional middlemen compress"],
        "keywords": ["retail", "bond", "yield", "investor", "marketplace", "d2c"],
        "example_posts": ["Retail yield seekers become a funding channel — not just a customer segment."],
        "recommended_templates": ["value_controlling_y_not_x", "shift_not_x_but_y"]
    },
    {
        "id": "vertical_integration_increasing",
        "name": "Vertical Integration Increasing",
        "description": "Firms own more of the stack to capture margin and control quality.",
        "core_pattern": "Platform operators buy adjacent supply chain layers to eliminate middleman margins.",
        "core_mechanism": "When intermediaries extract rent, integrators buy or build adjacent layers to own the margin pool.",
        "trigger_patterns": ["acquisition", "full-stack", "in-house", "own the stack", "vertical"],
        "mechanism_patterns": ["margin internalization", "vendor consolidation", "middleman removal", "stack control"],
        "expectation_violation": "Specialized 'best-of-breed' software suites lose contracts to integrated, all-in-one bundles.",
        "editorial_tension": "Partner networks dissolve as category leaders expand upstream and downstream.",
        "example_implications": ["Partners become competitors", "Margin pool internalized"],
        "keywords": ["vertical", "integration", "acquisition", "full-stack", "in-house"],
        "example_posts": ["When the middle layer taxes you, you acquire it."],
        "recommended_templates": ["value_controlling_y_not_x", "competing_on_y_not_x"]
    },
    {
        "id": "measurement_replacing_intuition",
        "name": "Measurement Replacing Intuition",
        "description": "Decisions shift to instrumented metrics, experimentation, and observability.",
        "core_pattern": "Data instrumentation and continuous experimentation replace executive intuition.",
        "core_mechanism": "Operators with data pipelines out-execute intuition-led competitors in mature channels.",
        "trigger_patterns": ["analytics", "experimentation", "observability", "attribution", "metrics"],
        "mechanism_patterns": ["continuous attribution", "data automation", "telemetry", "metric signals"],
        "expectation_violation": "High-concept branding ideas underperform simple, instrumented, data-optimized micro-campaigns.",
        "editorial_tension": "Creative authority shifts to telemetry and automated attribution pipelines.",
        "example_implications": ["HiPPO decisions lose", "Instrumentation becomes product requirement"],
        "keywords": ["metrics", "analytics", "experiment", "attribution", "observability"],
        "example_posts": ["If you can't measure the loop, you can't scale the loop."],
        "recommended_templates": ["competing_on_y_not_x", "operational_complexity_lives_in_y"]
    },
    {
        "id": "execution_reliability_becoming_moat",
        "name": "Execution Reliability Becoming Moat",
        "description": "Consistent delivery and failure handling beat roadmap ambition.",
        "core_pattern": "High-reliability SLA execution beats feature velocity in production tech.",
        "core_mechanism": "In agentic and infra-heavy products, trust comes from predictable execution under load.",
        "trigger_patterns": ["sla", "incident", "latency", "retry", "reliability", "uptime"],
        "mechanism_patterns": ["sla protection", "fault tolerance", "predictable execution", "downtime cost"],
        "expectation_violation": "Startups with faster development cycles lose enterprise clients to slower, more reliable platforms.",
        "editorial_tension": "The marketing team sells feature velocity while the customer renews for uptime and support SLAs.",
        "example_implications": ["Roadmap velocity secondary", "Incident history drives churn"],
        "keywords": ["reliability", "sla", "latency", "incident", "uptime", "retry"],
        "example_posts": ["In agents, the moat is surviving production — not winning benchmarks."],
        "recommended_templates": ["moat_moving_x_to_y", "strategic_over_technical_shift"]
    },
    {
        "id": "capital_distribution_becoming_strategic",
        "name": "Capital Distribution Becoming Strategic",
        "description": "Who controls capital routing (debt, equity access, yield products) shapes market power.",
        "core_pattern": "Strategic advantage belongs to the channel controllers of capital, not the end services.",
        "core_mechanism": "Platforms that aggregate capital sources compress spreads and displace traditional brokers.",
        "trigger_patterns": ["lending", "debt platform", "capital markets", "syndication", "yield"],
        "mechanism_patterns": ["capital routing", "fee pool compression", "origination automation", "distribution advantage"],
        "expectation_violation": "Superior loan terms or interest rates fail against platforms that embed credit directly into workflow UI.",
        "editorial_tension": "The capital asset commoditizes; the interface that routes the capital captures the premium.",
        "example_implications": ["Balance-sheet + distribution wins", "Brokers lose fee pools"],
        "keywords": ["capital", "debt", "lending", "syndication", "yield", "bond"],
        "example_posts": ["The strategic asset is who routes the capital — not who built the UI."],
        "recommended_templates": ["value_controlling_y_not_x", "shift_not_x_but_y"]
    },
    {
        "id": "apis_commoditizing_products",
        "name": "APIs Commoditizing Application Layers",
        "description": "Shared APIs and models collapse application differentiation; value moves up or down stack.",
        "core_pattern": "Cheap APIs dissolve application-layer differentiation.",
        "core_mechanism": "When core capability is API-accessible, wrappers lose pricing power to workflow and data moats.",
        "trigger_patterns": ["api", "wrapper", "commodity", "openai", "model api", "plugin"],
        "mechanism_patterns": ["margin erosion", "feature commoditization", "repetition costs", "low build barrier"],
        "expectation_violation": "Capital-backed application wrappers collapse in value as competitors replicate them in days.",
        "editorial_tension": "Startups focus on building software features that can be absorbed as a minor API update by platforms.",
        "example_implications": ["Thin apps die", "Workflow and data moats survive"],
        "keywords": ["api", "wrapper", "commodity", "plugin", "integration"],
        "example_posts": ["If your product is only an API call, you're a feature waiting for absorption."],
        "recommended_templates": ["competing_on_y_not_x", "moat_moving_x_to_y"]
    },
    {
        "id": "ai_turning_services_into_features",
        "name": "AI Turning Services Into Features",
        "description": "Professional services and agencies compress into productized AI features inside software.",
        "core_pattern": "Professional services and consulting are absorbed as automated features inside software products.",
        "core_mechanism": "High-margin services get automated into seats; services firms must build proprietary tools or perish.",
        "trigger_patterns": ["copilot", "automated", "services", "agency", "productized"],
        "mechanism_patterns": ["seat-based transition", "service automation", "billable hour compression", "template integration"],
        "expectation_violation": "Traditional agencies see client churn despite delivering high-quality human work.",
        "editorial_tension": "Agencies must become software vendors or see their core services commoditized.",
        "example_implications": ["Services margins compress", "Software vendors eat agency work"],
        "keywords": ["services", "agency", "consulting", "automated", "copilot"],
        "example_posts": ["Every services workflow with a template becomes a feature — then a default."],
        "recommended_templates": ["shift_not_x_but_y", "more_for_y_less_for_x"]
    },
    {
        "id": "cloud_to_local_compute_shift",
        "name": "Cloud to Local Compute Shift",
        "description": "Inference economics and privacy push compute to edge, on-device, and local clusters.",
        "core_pattern": "Edge compute and on-device models replace expensive cloud API calls.",
        "core_mechanism": "When API costs scale linearly with usage, local inference becomes rational to preserve unit economics.",
        "trigger_patterns": ["on-device", "edge", "local inference", "gpu", "latency", "cost per token"],
        "mechanism_patterns": ["cost repatriation", "edge efficiency", "token expense reduction", "compute localism"],
        "expectation_violation": "High usage of centralized AI APIs leads to software migration to local models to preserve unit economics.",
        "editorial_tension": "Cloud AI platforms face churn as developers realize small local models are sufficient for core tasks.",
        "example_implications": ["Hybrid architectures grow", "Pure API bills trigger repatriation"],
        "keywords": ["edge", "on-device", "local", "inference", "gpu", "token cost"],
        "example_posts": ["At enough volume, inference stops being a cloud bill — it becomes a capex decision."],
        "recommended_templates": ["shift_not_x_but_y", "operational_complexity_lives_in_y"]
    },
    {
        "id": "compliance_becoming_defensive_moat",
        "name": "Compliance Becoming Defensive Moat",
        "description": "Regulatory burden favors incumbents who can absorb compliance cost.",
        "core_pattern": "Regulatory burdens favor large, established vendors who can absorb compliance costs.",
        "core_mechanism": "Certification, audit trails, and policy controls become buying criteria, penalizing startup velocity.",
        "trigger_patterns": ["compliance", "regulation", "audit", "soc2", "gdpr", "kyc"],
        "mechanism_patterns": ["procurement friction", "legal moat", "audit tax", "regulatory compliance"],
        "expectation_violation": "Fast, innovative products lose deals to legacy software that has compliance certifications.",
        "editorial_tension": "Regulatory friction behaves as a government-enforced moat for incumbents.",
        "example_implications": ["Startup velocity penalized in regulated buyers", "Compliance teams grow"],
        "keywords": ["compliance", "regulation", "audit", "soc", "kyc", "gdpr"],
        "example_posts": ["In regulated markets, compliance is the product — everything else is demo."],
        "recommended_templates": ["moat_moving_x_to_y", "more_for_y_less_for_x"]
    },
    {
        "id": "inference_costs_collapsing",
        "name": "Inference Costs Collapsing",
        "description": "Model efficiency and competition drive per-token costs down — changing unit economics.",
        "core_pattern": "The rapid decrease in model API pricing shifts focus from hardware to application architecture.",
        "core_mechanism": "Cheaper inference shifts who can afford agents, moving constraints from model access to workflow design.",
        "trigger_patterns": ["price cut", "efficient model", "flash", "distillation", "cheaper inference"],
        "mechanism_patterns": ["token deflation", "orchestration expansion", "cost structural shift", "volume economics"],
        "expectation_violation": "Lower token prices fail to lower total project budgets due to high orchestration and testing overhead.",
        "editorial_tension": "Model companies compete on price while application builders capture the efficiency gains.",
        "example_implications": ["High-volume use cases unlock", "Margin moves to orchestration not tokens"],
        "keywords": ["inference", "token", "pricing", "efficient", "flash", "cost"],
        "example_posts": ["When inference gets cheap, the constraint becomes workflow design — not model access."],
        "recommended_templates": ["operational_complexity_lives_in_y", "shift_not_x_but_y"]
    },
    {
        "id": "platform_dependency_risk",
        "name": "Platform Dependency Risk",
        "description": "Building on dominant platforms creates rent extraction and policy risk.",
        "core_pattern": "Building on third-party platforms subjects companies to rent extraction and policy risk.",
        "core_mechanism": "API policy changes, take rates, and ranking algorithms can destroy distribution overnight.",
        "trigger_patterns": ["app store", "platform policy", "api terms", "take rate", "algorithm change"],
        "mechanism_patterns": ["policy risk", "revenue concentration", "take rate extraction", "distribution eviction"],
        "expectation_violation": "High-growth startups are shut down due to minor policy adjustments by core platform providers.",
        "editorial_tension": "Platform distribution provides immediate scale but introduces existential survival risk.",
        "example_implications": ["Multi-platform strategies rise", "Direct channels regain priority"],
        "keywords": ["platform", "policy", "app store", "api terms", "take rate"],
        "example_posts": ["Platform distribution is rented — not owned."],
        "recommended_templates": ["moat_moving_x_to_y", "strategic_over_technical_shift"]
    },
    {
        "id": "concentration_dynamics",
        "name": "Market Concentration Dynamics",
        "description": "Winner-take-most effects strengthen as scale, data, and network effects compound.",
        "core_pattern": "Strong network and scale effects consolidate mature markets around a single leader.",
        "core_mechanism": "Category leaders capture disproportionate economics; #2 players fight for margins.",
        "trigger_patterns": ["market share", "dominant", "oligopoly", "consolidation", "merger"],
        "mechanism_patterns": ["oligopoly consolidation", "scale lock-in", "margin starvation", "network consolidation"],
        "expectation_violation": "A highly competitive market with dozens of funded startups consolidates into an oligopoly.",
        "editorial_tension": "Venture capital funding continues to flow to runner-up platforms despite poor economics.",
        "example_implications": ["Mid-tier players get squeezed", "M&A accelerates"],
        "keywords": ["concentration", "dominant", "oligopoly", "merger", "market share"],
        "example_posts": ["In mature categories, the middle gets hollowed out — leaders and niches survive."],
        "recommended_templates": ["market_behaves_like_y_not_x", "value_controlling_y_not_x"]
    },
    {
        "id": "pricing_power_erosion",
        "name": "Pricing Power Erosion",
        "description": "Competition and transparency erode ability to raise prices without adding lock-in.",
        "core_pattern": "Transparent market pricing forces software seat-based models to discount or compress.",
        "core_mechanism": "Customers benchmark instantly; pricing moves to usage-based structures or heavy bundling.",
        "trigger_patterns": ["price cut", "discount", "usage-based", "commoditization"],
        "mechanism_patterns": ["contract compression", "procurement squeezing", "bundle discounting", "commoditization pressure"],
        "expectation_violation": "Adding product features fails to stop contract sizes from shrinking during renewal cycles.",
        "editorial_tension": "Sales teams push value narratives while procurement teams treat software as a commodity.",
        "example_implications": ["Seat expansion stalls", "Bundling increases to hide margin"],
        "keywords": ["pricing", "discount", "usage-based", "commodity", "arr"],
        "example_posts": ["When comparison is one click away, pricing power needs a mechanism — not a brand."],
        "recommended_templates": ["competing_on_y_not_x", "market_behaves_like_y_not_x"]
    },
    {
        "id": "data_gravity_moat",
        "name": "Data Gravity Moat",
        "description": "Accumulated proprietary data makes migration costly and improves model/product performance.",
        "core_pattern": "Proprietary databases and user interaction logs create high switching barriers.",
        "core_mechanism": "Workflow data, transaction history, and feedback loops compound — new entrants start cold.",
        "trigger_patterns": ["data pipeline", "proprietary data", "training data", "feedback loop", "migration"],
        "mechanism_patterns": ["data compounding", "switching friction", "data feedback loop", "cold-start block"],
        "expectation_violation": "Competitors with modern technology stacks fail to displace older, clunkier platforms containing historical databases.",
        "editorial_tension": "The value is not in writing code, but in holding the historical operational records.",
        "example_implications": ["Data network effects strengthen incumbents", "Cold-start problem for challengers"],
        "keywords": ["data", "flywheel", "proprietary", "migration", "feedback"],
        "example_posts": ["The product is the accumulated data path — not today's feature list."],
        "recommended_templates": ["moat_moving_x_to_y", "value_controlling_y_not_x"]
    },
    {
        "id": "automation_economics_shift",
        "name": "Automation Economics Shift",
        "description": "Automation ROI is judged on payback period and error cost — not innovation narrative.",
        "core_pattern": "Corporate automation spending shifts from experimental trials to strict labor substitution metrics.",
        "core_mechanism": "Buyers fund automation that replaces measurable labor cost with predictable software spend.",
        "trigger_patterns": ["roi", "payback", "automation", "cost savings", "labor replacement"],
        "mechanism_patterns": ["headcount reduction", "cost amortization", "labor substitution", "payback metrics"],
        "expectation_violation": "Sophisticated AI pilot programs are cancelled because they cannot prove headcount cost reduction.",
        "editorial_tension": "Tech startups market creativity and intelligence, but enterprises buy headcount displacement.",
        "example_implications": ["Pilot-heavy AI fails budget scrutiny", "Ops-led buyers win"],
        "keywords": ["roi", "automation", "payback", "headcount", "cost savings"],
        "example_posts": ["Automation sells when the invoice replaces a salary line — not when it wins a hackathon."],
        "recommended_templates": ["market_behaves_like_y_not_x", "shift_not_x_but_y"]
    },
    {
        "id": "search_disintermediation",
        "name": "Search and Discovery Disintermediation",
        "description": "AI-mediated answers reduce traffic to publishers and standalone apps.",
        "core_pattern": "Answer engines bypass traditional click-through traffic to websites.",
        "core_mechanism": "Discovery shifts to answer engines; SEO and link economies weaken as users get answers in-app.",
        "trigger_patterns": ["search", "ai overview", "traffic drop", "publisher", "discovery"],
        "mechanism_patterns": ["zero-click search", "ad revenue starvation", "citation extraction", "discovery bypass"],
        "expectation_violation": "Website content ranks highly in AI search results but fails to generate site traffic.",
        "editorial_tension": "Content creators provide the data to train search models that ultimately make their websites obsolete.",
        "example_implications": ["Content monetization breaks", "Brands fight for citation not clicks"],
        "keywords": ["search", "traffic", "publisher", "seo", "discovery", "overview"],
        "example_posts": ["If the answer is in the interface, the website becomes a data supplier."],
        "recommended_templates": ["value_controlling_y_not_x", "strategic_over_technical_shift"]
    },
    {
        "id": "hardware_supply_bottleneck",
        "name": "Hardware Supply Bottleneck",
        "description": "GPU and chip supply constraints shape who can ship AI products at scale.",
        "core_pattern": "GPU and silicon constraints dictate application roadmap timelines.",
        "core_mechanism": "Capacity allocation favors hyperscalers and large contracts; startups face queue risks.",
        "trigger_patterns": ["gpu shortage", "nvidia", "chip", "capacity", "supply constraint"],
        "mechanism_patterns": ["compute rationing", "silicon dependency", "capacity queue", "infrastructure delay"],
        "expectation_violation": "Finished software applications sit undeployed due to server instance queues.",
        "editorial_tension": "Software engineering velocity is throttled by hardware fabrication and silicon supply chains.",
        "example_implications": ["Inference capacity becomes strategic asset", "Hardware partnerships decide winners"],
        "keywords": ["gpu", "nvidia", "chip", "capacity", "supply", "hardware"],
        "example_posts": ["In AI infra, the roadmap is often a supply chain document."],
        "recommended_templates": ["more_for_y_less_for_x", "strategic_over_technical_shift"]
    },
    {
        "id": "fintech_vertical_integration",
        "name": "Fintech Vertical Integration",
        "description": "Fintechs move from point solutions to full-stack lending, payments, and distribution.",
        "core_pattern": "Financial technology platforms shift from front-end tools to balance-sheet ownership.",
        "core_mechanism": "Owning origination, balance sheet, and distribution improves unit economics over SaaS fees.",
        "trigger_patterns": ["neobank", "lending", "acquisition", "payments", "embedded finance"],
        "mechanism_patterns": ["balance sheet utilization", "lending spread", "origination control", "fintech bundling"],
        "expectation_violation": "Neobanks with high user growth struggle to survive without internalizing balance-sheet lending.",
        "editorial_tension": "The front-end banking features are giveaways to distribute higher-margin debt products.",
        "example_implications": ["Point solutions consolidate", "Margin captured across stack"],
        "keywords": ["fintech", "lending", "payments", "embedded", "neobank"],
        "example_posts": ["Fintech margin lives in the stack — not the feature."],
        "recommended_templates": ["value_controlling_y_not_x", "competing_on_y_not_x"]
    },
    {
        "id": "labor_market_bifurcation",
        "name": "Labor Market Bifurcation",
        "description": "Demand polarizes toward elite judgment roles and commodity execution — middle thins.",
        "core_pattern": "Employment markets polarize between elite judgment roles and commoditized automation tasks.",
        "core_mechanism": "AI and outsourcing compress mid-skill work; hiring concentrates at the absolute extremes.",
        "trigger_patterns": ["layoff", "hiring", "salary", "skills", "talent war"],
        "mechanism_patterns": ["middle skill hollow-out", "wage bifurcation", "specialist premium", "repetition displacement"],
        "expectation_violation": "High overall tech employment numbers mask the hollowed-out middle of entry-to-mid career roles.",
        "editorial_tension": "Universities train students for standard mid-level roles that are disappearing.",
        "example_implications": ["Middle management layers cut", "Senior specialists premium rises"],
        "keywords": ["layoff", "hiring", "talent", "skills", "wage", "headcount"],
        "example_posts": ["The labor market is splitting: judgment at a premium, repetition at a discount."],
        "recommended_templates": ["shift_not_x_but_y", "more_for_y_less_for_x"]
    },
    {
        "id": "india_startup_unit_economics",
        "name": "India Startup Unit Economics Reality",
        "description": "Indian startups face growth-at-cost dynamics with thin margins and capital efficiency pressure.",
        "core_pattern": "High revenue growth in emerging tech markets masking operational losses and unsustainable CAC.",
        "core_mechanism": "High growth with weak profit signals customer subsidies rather than scale economics.",
        "trigger_patterns": ["crore", "profit slumps", "revenue growth", "india", "burn", "unit economics"],
        "mechanism_patterns": ["cac subsidy", "collection leakage", "thin margins", "capital recovery"],
        "expectation_violation": "Startup unicorns with massive transaction volume face bankruptcy during market downturns.",
        "editorial_tension": "Founders chase raw transaction metrics when public markets prioritize real cash flows.",
        "example_implications": ["Growth narrative meets margin reality", "Public markets punish profitless scale"],
        "keywords": ["india", "crore", "profit", "revenue", "burn", "inc42", "yourstory"],
        "example_posts": ["In Indian tech, revenue growth without margin expansion is a warning — not a trophy."],
        "recommended_templates": ["market_behaves_like_y_not_x", "competing_on_y_not_x"]
    },
    {
        "id": "agentic_ux_replacing_chat",
        "name": "Agentic UX Replacing Chat",
        "description": "Interfaces shift from chat boxes to task completion, background agents, and proactive systems.",
        "core_pattern": "Interfaces move from conversational text fields to task automation and background execution.",
        "core_mechanism": "Users pay for outcomes and workflow resolution, turning conversational chat logs into friction.",
        "trigger_patterns": ["agent", "background task", "proactive", "chatbot", "task completion"],
        "mechanism_patterns": ["action automation", "outcome pricing", "silent task execution", "conversational friction"],
        "expectation_violation": "Chat bots with high user engagement show low commercial renewal value compared to silent, background scripts.",
        "editorial_tension": "Startups build complex conversational UIs while users simply want their workflows resolved.",
        "example_implications": ["Chat UI becomes legacy", "Outcome-based pricing emerges"],
        "keywords": ["agent", "chatbot", "proactive", "task", "automation", "workflow"],
        "example_posts": ["Chat was the demo — agents are the interface."],
        "recommended_templates": ["moat_moving_x_to_y", "shift_not_x_but_y"]
    },
    {
        "id": "open_source_model_commoditization",
        "name": "Open Source Model Commoditization",
        "description": "Open weights collapse differentiation at the model layer; value moves to data and ops.",
        "core_pattern": "Free open-weights models eliminate closed API pricing leverage.",
        "core_mechanism": "Open weights collapse closed API margins; application value shifts to hosting, tooling, and data.",
        "trigger_patterns": ["open source", "open weights", "llama", "self-host", "fine-tune"],
        "mechanism_patterns": ["weight commoditization", "self-hosting economics", "tooling moats", "zero-cost license"],
        "expectation_violation": "Closed model providers cut prices drastically as developers shift to self-hosted alternatives.",
        "editorial_tension": "proprietary model tech requires billions in capital, yet competes with free, community-optimized alternatives.",
        "example_implications": ["Model vendors compete on price", "Differentiation shifts to applications"],
        "keywords": ["open source", "open weights", "llama", "self-host", "fine-tune"],
        "example_posts": ["When the model is free, the moat is everything wrapped around it."],
        "recommended_templates": ["competing_on_y_not_x", "value_controlling_y_not_x"]
    }
]


def build_prior_embed_text(prior):
    return " ".join([
        prior["name"],
        prior["description"],
        prior["core_pattern"],
        prior["core_mechanism"],
        prior["expectation_violation"],
        prior["editorial_tension"],
        " ".join(prior["keywords"]),
        " ".join(prior["trigger_patterns"]),
    ]).strip()


def _keyword_boost(prior, article_text):
    lowered = article_text.lower()
    hits = sum(1 for kw in prior["keywords"] if kw.lower() in lowered)
    return min(0.18, hits * KEYWORD_BOOST)


def _get_prior_embeddings():
    global _prior_embeddings
    if _prior_embeddings is None:
        texts = [build_prior_embed_text(p) for p in NARRATIVE_PRIORS]
        _prior_embeddings = encode_texts(texts)
    return _prior_embeddings


def get_narrative_prior_by_id(prior_id):
    for prior in NARRATIVE_PRIORS:
        if prior["id"] == prior_id:
            return prior
    return None


def match_narrative_priors(article, top_k=MATCH_TOP_K, min_score=MATCH_MIN_SCORE):
    """
    Primary cognition layer: which strategic narratives does this article activate?
    """
    article_text = build_article_text(article)
    if not article_text.strip():
        return {
            "matched_narratives": [],
            "confidence": 0.0,
            "supporting_mechanisms": [],
            "expectation_violations": [],
            "editorial_tension": [],
            "recommended_templates": [],
            "primary_narrative_id": "",
        }

    article_embedding = encode_texts([article_text])
    prior_embeddings = _get_prior_embeddings()
    similarities = cosine_scores(article_embedding, prior_embeddings)[0]

    ranked = []
    for idx, prior in enumerate(NARRATIVE_PRIORS):
        semantic = float(similarities[idx])
        score = semantic + _keyword_boost(prior, article_text)
        if score >= min_score:
            ranked.append({
                "id": prior["id"],
                "name": prior["name"],
                "score": round(score, 4),
                "semantic_score": round(semantic, 4),
                "core_pattern": prior["core_pattern"],
                "core_mechanism": prior["core_mechanism"],
                "expectation_violation": prior["expectation_violation"],
                "editorial_tension": prior["editorial_tension"],
                "example_implications": prior["example_implications"][:3],
                "example_posts": prior["example_posts"][:2],
                "recommended_templates": prior["recommended_templates"],
            })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    matched = ranked[:top_k]

    primary = matched[0] if matched else {}
    confidence = primary.get("score", 0.0) if primary else 0.0

    supporting = []
    violations = []
    tensions = []
    templates = []

    for item in matched:
        prior = get_narrative_prior_by_id(item["id"])
        if prior:
            supporting.append(prior["core_mechanism"])
            violations.append(prior["expectation_violation"])
            tensions.append(prior["editorial_tension"])
            templates.extend(prior["recommended_templates"])

    return {
        "matched_narratives": matched,
        "confidence": confidence,
        "supporting_mechanisms": supporting[:3],
        "expectation_violations": violations[:3],
        "editorial_tension": tensions[:3],
        "recommended_templates": list(set(templates)),
        "primary_narrative_id": primary.get("id", "") if primary else "",
    }


def format_matched_narratives_for_prompt(narrative_match):
    if not narrative_match.get("matched_narratives"):
        return "No strong narrative prior match — stay conservative and mechanism-grounded."

    lines = ["ACTIVATED NARRATIVE PRIORS (use as lenses, do not invent new worldviews):"]
    for item in narrative_match["matched_narratives"]:
        lines.append(
            f"- {item['name']} (confidence {item['score']:.2f}): {item['core_mechanism']}"
        )
        if item.get("example_implications"):
            lines.append(f"  Typical implications: {'; '.join(item['example_implications'][:2])}")
    return "\n".join(lines)

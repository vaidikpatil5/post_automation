"""
Strategic editorial synthesis structures.

Rather than generating insights from scratch, the system activates these
reusable structures to compress facts into mechanism-grounded strategic insights.
"""

EDITORIAL_TEMPLATES = [
    {
        "id": "shift_not_x_but_y",
        "template_name": "The interesting shift isn't X. It's Y.",
        "core_structure": "The interesting shift isn't {not_x}. It's {but_y}.",
        "editorial_pattern": "Focuses on looking past the obvious headline (X) to identify the true structural driver or consequence (Y).",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["State the headline/expectation (X) simply.", "Deliver the mechanical driver (Y) directly without fluff."],
        "style_rules": ["Underscored, sober tone.", "No emotional excitement."],
        "avoid": ["revolution", "game changer", "paradigm shift"],
        "example_outputs": [
            "The interesting shift isn't that AI models are getting cheaper. It's that enterprises are paying more for orchestration and data pipes to keep those models from hallucinating in production."
        ],
    },
    {
        "id": "competing_on_y_not_x",
        "template_name": "Companies are no longer competing on X. They're competing on Y.",
        "core_structure": "Companies are no longer competing on {not_x}. They're competing on {but_y}.",
        "editorial_pattern": "Emphasizes the commoditization of the front-end or core technology (X) and the shift of competition to execution, supply chains, or data assets (Y).",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Contrast technical product features with operational distribution or access."],
        "style_rules": ["Focus on commercial reality over engineering hype."],
        "avoid": ["the future of", "next generation"],
        "example_outputs": [
            "Startups are no longer competing on model capabilities. They're competing on workflow integration and custom data flywheels that cannot be replicated by API providers."
        ],
    },
    {
        "id": "moat_moving_x_to_y",
        "template_name": "The moat is moving from X to Y.",
        "core_structure": "The moat is moving from {not_x} to {but_y}.",
        "editorial_pattern": "Highlights a transition in defensibility away from transient features or algorithms (X) to structural locks (Y) like workflows, data gravity, or integration depth.",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Contrast visual or easily built components with deep operational switching costs."],
        "style_rules": ["Highly analytical.", "Clear causal links."],
        "avoid": ["ultimate", "revolutionary"],
        "example_outputs": [
            "The moat is moving from the front-end chat interface to the persistence layer that manages state and error recovery across long-running autonomous workflows."
        ],
    },
    {
        "id": "value_controlling_y_not_x",
        "template_name": "The real value isn't in X. It's in controlling Y.",
        "core_structure": "The real value isn't in {not_x}. It's in controlling {but_y}.",
        "editorial_pattern": "Addresses value capture across the supply chain, showing that the core product (X) is getting squeezed, while downstream routing or gatekeepers (Y) extract the margin.",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Explain the bottleneck dynamics that allow Y to capture the economic margin."],
        "style_rules": ["Focus on unit economics and pricing power."],
        "avoid": ["disrupting everything", "inevitable dominance"],
        "example_outputs": [
            "The real value isn't in producing raw tokens. It's in controlling the routing layer that chooses when to call a model and when to fetch from a cached database."
        ],
    },
    {
        "id": "more_for_y_less_for_x",
        "template_name": "This matters less for X and more for Y.",
        "core_structure": "This matters less for {not_x} and more for {but_y}.",
        "editorial_pattern": "Redirects public focus away from downstream hype (X) and points to the infrastructure, pick-and-shovel providers, or specific operational categories that capture the true windfall (Y).",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Pivot from consumer hype to business-to-business/operational infrastructure."],
        "style_rules": ["Pragmatic.", "Understated."],
        "avoid": ["democratization", "limitless potential"],
        "example_outputs": [
            "This development matters less for consumer search applications and more for on-prem enterprise data indexing tools that handle custom file formats under compliance guidelines."
        ],
    },
    {
        "id": "strategic_over_technical_shift",
        "template_name": "The technical shift of X is obvious. The strategic shift is Y.",
        "core_structure": "The technical shift of {not_x} is obvious. The strategic shift is {but_y}.",
        "editorial_pattern": "Differentiates between the visible product updates (X) and the underlying shifts in corporate power, market structures, or capital allocation (Y).",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["De-emphasize the technical details in favor of commercial incentives."],
        "style_rules": ["Business-first.", "Causal."],
        "avoid": ["exponential growth", "changing the world"],
        "example_outputs": [
            "The technical shift of open source models matching closed weights is obvious. The strategic shift is model providers changing their business models to services and dedicated hardware hosting."
        ],
    },
    {
        "id": "operational_complexity_lives_in_y",
        "template_name": "As X commoditizes, operational complexity shifts to Y.",
        "core_structure": "As {not_x} commoditizes, operational complexity shifts to {but_y}.",
        "editorial_pattern": "Shows that easing one bottleneck (X) simply transfers the complexity, friction, and cost to another layer of the workflow (Y).",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Identify what becomes cheap (X) and where the friction is displaced (Y)."],
        "style_rules": ["Low emotion.", "Workflow-centered."],
        "avoid": ["paradigm shift", "ultimate future"],
        "example_outputs": [
            "As model APIs commoditize, operational complexity shifts to parsing dirty data inputs and managing reliable database writes under peak loads."
        ],
    },
    {
        "id": "market_behaves_like_y_not_x",
        "template_name": "The market appears X-driven, but increasingly behaves like Y.",
        "core_structure": "The market appears {not_x}-driven, but increasingly behaves like {but_y}.",
        "editorial_pattern": "Critiques superficial market analysis (X) and reveals the underlying economic forces, unit economics, or incentive alignment (Y) that actually run the sector.",
        "mechanism_slot": "but_y",
        "expectation_violation_slot": "not_x",
        "strategic_implication_slot": "but_y",
        "compression_rules": ["Contrast PR narratives with real operational/financial performance."],
        "style_rules": ["Restrained.", "Skeptical."],
        "avoid": ["revolutionizing", "unstoppable momentum"],
        "example_outputs": [
            "The market appears to be venture-scale product-driven, but increasingly behaves like a low-margin services industry that requires custom customization for every enterprise client."
        ],
    }
]


def get_template_by_id(template_id):
    for t in EDITORIAL_TEMPLATES:
        if t["id"] == template_id:
            return t
    return EDITORIAL_TEMPLATES[0]  # default fallback

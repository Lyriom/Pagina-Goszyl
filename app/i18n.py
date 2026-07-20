"""Copy and URL helpers for the Spanish and English public site."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

Locale = Literal["es", "en"]
PageName = Literal["home", "about", "contact"]

ROUTES: dict[Locale, dict[PageName, str]] = {
    "es": {"home": "/", "about": "/acerca", "contact": "/contacto"},
    "en": {"home": "/en", "about": "/en/about", "contact": "/en/contact"},
}

OG_LOCALES: dict[Locale, str] = {"es": "es_ES", "en": "en_US"}


ENGLISH: dict[str, str] = {
    # Metadata
    "meta.organization_description": "Digital product, automation, and artificial intelligence consulting for companies that want to grow through technology.",
    "meta.home_title": "Gozsyl | Digital products, AI, and automation",
    "meta.home_description": "Digital product, automation, and artificial intelligence consulting for companies that want to grow through technology.",
    "meta.about_title": "About Gozsyl",
    "meta.about_description": "Meet Gozsyl and discover how we combine product strategy, design, and engineering to build useful digital systems.",
    "meta.contact_title": "Contact Gozsyl",
    "meta.contact_description": "Tell Gozsyl about the process, product, or digital experience you want to build or improve.",
    "meta.og_alt": "Gozsyl — digital products, AI, and automation",

    # Shared layout
    "base.skip_link": "Skip to content",
    "base.home_aria": "Gozsyl, go to homepage",
    "base.tagline": "Digital systems",
    "base.nav_label": "Main navigation",
    "base.services": "Services",
    "base.featured_project": "Featured project",
    "base.process": "Process",
    "base.about": "About us",
    "base.theme_toggle": "Switch color theme",
    "base.talk": "Let’s talk",
    "base.menu_toggle": "Open or close menu",
    "base.tell_project": "Tell us about your project",
    "base.language_selector": "Language selector",
    "base.switch_to_english": "Switch language to English",
    "base.switch_to_spanish": "Switch language to Spanish",
    "base.footer_copy": "We design digital products, automation, and data systems that turn complex challenges and processes into clear, useful tools.",
    "base.explore": "Explore",
    "base.contact": "Contact",
    "base.contact_intro": "Tell us what you’d like to improve and we’ll respond with a clear next step.",
    "base.open_contact": "Open contact form",
    "base.analytics_preferences": "Analytics preferences",
    "base.rights": "All rights reserved.",
    "base.footer_tagline": "Product, design, and technology with purpose.",
    "base.privacy_title": "Your privacy comes first",
    "base.privacy_copy": "We only enable site analytics with your permission. Essential features are always available.",
    "base.analytics_allow": "Allow analytics",
    "base.essential_only": "Essential only",

    # Home hero and visual
    "home.eyebrow": "Digital products · Automation · AI",
    "home.hero_before": "We turn complex processes into",
    "home.hero_gradient": "digital products that work.",
    "home.hero_description": "We design and build automation, web platforms, applied artificial intelligence, and data systems for teams that need to move forward with clarity, speed, and control.",
    "home.hero_cta": "Tell us about your challenge",
    "home.hero_secondary": "View featured project",
    "home.strategy": "Strategy",
    "home.design": "Design",
    "home.development": "Development",
    "home.operations": "Operations",
    "home.system_design": "System in design",
    "home.value_flow": "Value flow",
    "home.signal_result": "From signal to outcome",
    "home.input": "Input",
    "home.logic": "Logic",
    "home.outcome": "Outcome",
    "home.decisions": "Decisions",
    "home.clear_objectives": "Clear objectives",
    "home.delivery": "Delivery",
    "home.visible_progress": "Visible progress",

    # Featured work
    "home.selected_work": "Selected work",
    "home.work_title": "The work speaks for itself.",
    "home.work_intro": "We design end-to-end experiences, from strategy and interface design to the logic that keeps them running.",
    "home.project_badge": "Featured project",
    "home.ecommerce": "E-commerce",
    "home.aurexir_title": "Men’s fragrance retail, transformed into a premium digital experience.",
    "home.aurexir_description": "A bilingual platform for discovering and purchasing designer and niche fragrances. It brings together a catalog, search, filters, fragrance profiles, a shopping cart, accounts, and direct-purchase options in one responsive experience.",
    "home.catalog": "Catalog",
    "home.products": "products",
    "home.discovery": "Discovery",
    "home.categories": "categories",
    "home.content": "Content",
    "home.languages": "languages",
    "home.visit_aurexir": "Visit aurexir.com",
    "home.aurexir_aria": "Open the Aurexir website in a new tab",
    "home.aurexir_alt": "Aurexir homepage, a digital men’s fragrance store",

    # Services
    "home.capabilities": "Capabilities",
    "home.capabilities_title": "Useful technology for real business challenges.",
    "home.capabilities_intro": "We combine strategy, user experience, and engineering to build solutions teams understand, adopt, and can grow with.",
    "home.service_1_title": "Automation and applied AI",
    "home.service_1_description": "We reduce repetitive work and response times through workflows, assistants, and integrations connected to real operations.",
    "home.service_1_item_1": "AI agents and assistants",
    "home.service_1_item_2": "Workflows and API integrations",
    "home.service_1_item_3": "Operations automation",
    "home.service_2_title": "Digital products and web platforms",
    "home.service_2_description": "We create business websites, e-commerce platforms, portals, and internal tools with fast, clear, and accessible experiences.",
    "home.service_2_item_1": "Product strategy and UX/UI",
    "home.service_2_item_2": "Full-stack web development",
    "home.service_2_item_3": "Technical SEO and analytics",
    "home.service_3_title": "Data and integrations",
    "home.service_3_description": "We connect scattered tools and sources so data arrives complete, on time, and in a format people can act on.",
    "home.service_3_item_1": "APIs and integration architecture",
    "home.service_3_item_2": "Data pipelines and data quality",
    "home.service_3_item_3": "Dashboards and actionable metrics",

    # Delivery and process
    "home.delivery_eyebrow": "How we deliver",
    "home.delivery_title": "Less uncertainty. More clarity in every decision.",
    "home.delivery_intro": "Technology matters, but how it is built determines whether it creates value or becomes another burden for the team.",
    "home.delivery_1_title": "Clear scope and objectives",
    "home.delivery_1_description": "We align on which problem to solve, for whom, and how we’ll know the solution is useful.",
    "home.delivery_2_title": "Visible, frequent delivery",
    "home.delivery_2_description": "We validate real progress with your team to spot risks and opportunities early.",
    "home.delivery_3_title": "Ownership and autonomy",
    "home.delivery_3_description": "We deliver readable code and documentation so the knowledge stays with you.",
    "home.delivery_4_title": "Security by design",
    "home.delivery_4_description": "Privacy, access, observability, and maintenance are built into the product from day one.",
    "home.process_eyebrow": "Our process",
    "home.process_title": "From a conversation to a system that can grow.",
    "home.process_intro": "Each stage reduces uncertainty and delivers a concrete outcome to guide the next step.",
    "home.process_1_title": "Discover",
    "home.process_1_description": "We understand the context, people, data, and constraints before proposing a solution.",
    "home.process_2_title": "Design",
    "home.process_2_description": "We turn insights into a clear experience, architecture, and delivery plan.",
    "home.process_3_title": "Build",
    "home.process_3_description": "We build in short cycles, test what matters, and share real progress.",
    "home.process_4_title": "Improve",
    "home.process_4_description": "We observe usage, remove friction, and evolve the system based on new evidence.",

    # Gozsyl and CTA
    "home.about_eyebrow": "About Gozsyl",
    "home.about_title": "A technical partner with a product and business mindset.",
    "home.about_description": "We help teams modernize operations, launch digital products, and turn scattered data into useful decisions.",
    "home.about_cta": "Get to know Gozsyl",
    "home.one_conversation": "One conversation",
    "home.pair_1_title": "Strategy and execution",
    "home.pair_1_description": "Business and technical decisions move forward together.",
    "home.pair_2_title": "Design and engineering",
    "home.pair_2_description": "We care equally about the visible experience and the system behind it.",
    "home.pair_3_title": "Delivery and continuity",
    "home.pair_3_description": "We document, support, and leave behind a foundation ready to evolve.",
    "home.cta_eyebrow": "Next step",
    "home.cta_title": "What process, product, or experience do you want to improve?",
    "home.cta_description": "Tell us the context. We’ll reply with useful questions and a clear next step.",
    "home.cta_button": "Contact Gozsyl",

    # About page
    "about.eyebrow": "About Gozsyl",
    "about.hero_before": "We think about the business. We design the experience.",
    "about.hero_gradient": "We build the system.",
    "about.hero_description": "We work with teams looking to modernize operations, launch a digital product, or make better use of their data.",
    "about.thinking": "Thinking",
    "about.product_strategy": "Product strategy",
    "about.creation": "Creation",
    "about.design_engineering": "Design and engineering",
    "about.continuity": "Continuity",
    "about.operations_improvement": "Operations and continuous improvement",
    "about.approach": "Our approach",
    "about.approach_title": "The right solution starts before the code.",
    "about.approach_p1": "Before choosing a tool, we seek to understand the problem, the people who experience it, and the real conditions in which the solution must work. This prevents us from building more than necessary and helps focus investment where it creates value.",
    "about.approach_p2": "We bring product, design, and development into one conversation. This ensures experience decisions account for technical implications and architecture decisions stay focused on the outcome the business needs.",
    "about.approach_p3": "Our work doesn’t end at launch. We leave behind a clear, documented foundation designed to learn from real-world use and evolve with the team.",
    "about.principles": "Principles",
    "about.principles_title": "What you can expect when working with us.",
    "about.principle_1_title": "Clarity over complexity",
    "about.principle_1_description": "We explain decisions, risks, and alternatives in plain language. Technology should make work clearer, not more opaque.",
    "about.principle_2_title": "Visible collaboration",
    "about.principle_2_description": "We share progress and validate assumptions frequently. Your team takes part in the decisions that shape the product.",
    "about.principle_3_title": "Sustainable outcomes",
    "about.principle_3_description": "We design for operations, maintenance, and continuous improvement. The goal is not only to launch, but to leave you with a system that remains useful.",
    "about.principle_4_title": "Client ownership",
    "about.principle_4_description": "The code, documentation, and knowledge stay with you. We aim to create autonomy, not dependency.",
    "about.real_work": "Real work",
    "about.real_work_title": "Brand and commerce brought together in one digital experience.",
    "about.real_work_description": "Aurexir brings together experience design, a bilingual catalog, search, filters, a shopping cart, and assisted checkout in a responsive product created for a men’s fragrance retailer.",
    "about.view_project": "View the featured project",
    "about.aurexir_label": "Digital men’s fragrance store",
    "about.cta_eyebrow": "Let’s talk",
    "about.cta_title": "Do you have a challenge that deserves a better solution?",
    "about.cta_description": "Tell us the context and we’ll build the next step with you.",
    "about.cta_button": "Contact Gozsyl",

    # Contact page and delivery states
    "contact.eyebrow": "Contact",
    "contact.title": "Tell us what you want to build or improve.",
    "contact.description": "Share the context, the current challenge, and the outcome you need. Your message will be delivered directly to the Gozsyl team.",
    "contact.response_title": "What happens next",
    "contact.response_1": "We review your message and business context.",
    "contact.response_2": "We reply with useful questions and a clear next step.",
    "contact.response_3": "Your details are used only to respond to this request.",
    "contact.required_note": "Fields marked with * are required.",
    "contact.name": "Name",
    "contact.name_placeholder": "Your name",
    "contact.email": "Work email",
    "contact.email_placeholder": "you@company.com",
    "contact.company": "Company (optional)",
    "contact.company_placeholder": "Company name",
    "contact.message": "What would you like to build or improve?",
    "contact.message_placeholder": "Tell us about the context, the current problem, and the outcome you need.",
    "contact.consent": "I agree that Gozsyl may use this information only to respond to my request.",
    "contact.submit": "Send message",
    "contact.success_title": "Message sent",
    "contact.success": "Thank you. Your message was delivered to the Gozsyl team.",
    "contact.validation_error": "Please review the fields and try again.",
    "contact.csrf_error": "The form expired. Refresh the page and try again.",
    "contact.rate_error": "Too many attempts. Please wait a few minutes before trying again.",
    "contact.delivery_error": "We couldn’t deliver your message right now. Please try again later.",

    # Error pages
    "error.not_found_title": "Page not found",
    "error.not_found_message": "The page you’re looking for doesn’t exist, has moved, or is no longer available.",
    "error.restricted_title": "Restricted access",
    "error.restricted_message": "You don’t have permission to view this page.",
    "error.generic_title": "We couldn’t complete the request",
    "error.generic_message": "Try again or contact us if the problem continues.",
    "error.back_home": "Back to homepage",
    "error.contact": "Contact Gozsyl",

    # Plain-text email
    "email.subject": "[Gozsyl] New website message",
    "email.intro": "A new message was submitted through the Gozsyl website.",
    "email.name": "Name",
    "email.email": "Email",
    "email.company": "Company",
    "email.language": "Site language",
    "email.message": "Message",
}


def normalize_locale(locale: str) -> Locale:
    return "en" if locale == "en" else "es"


def locale_from_path(path: str) -> Locale:
    return "en" if path == "/en" or path.startswith("/en/") else "es"


def translate(locale: Locale, key: str, spanish: str) -> str:
    if locale == "es":
        return spanish
    try:
        return ENGLISH[key]
    except KeyError as exc:  # Fail loudly instead of leaking Spanish into English pages.
        raise RuntimeError(f"Missing English translation: {key}") from exc


def translator(locale: Locale) -> Callable[[str, str], str]:
    return lambda key, spanish: translate(locale, key, spanish)


def localized_context(locale: Locale, page: PageName | None = None) -> dict[str, object]:
    other_locale: Locale = "en" if locale == "es" else "es"
    language_urls = {
        "es": ROUTES["es"][page] if page else ROUTES["es"]["home"],
        "en": ROUTES["en"][page] if page else ROUTES["en"]["home"],
    }
    return {
        "locale": locale,
        "t": translator(locale),
        "urls": ROUTES[locale],
        "language_urls": language_urls,
        "other_locale": other_locale,
        "og_locale": OG_LOCALES[locale],
        "og_locale_alternate": OG_LOCALES[other_locale],
    }

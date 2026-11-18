"""Heuristic extractor: gazetteer plus regex, zero cost, no API key (FR-2.4)."""
import re

from src.extract.base import Claim, Entity, keep

# ponytail: hand-made gazetteer, about 150 terms. Upgrade path: LLM extractor behind the same interface.
GAZETTEER = {
    "company": """OpenAI, Anthropic, Google, DeepMind, Microsoft, Meta, Apple, Amazon, Nvidia, AMD, Intel, TSMC,
        Samsung, Tesla, xAI, Mistral, Hugging Face, IBM, Oracle, Salesforce, Baidu, Alibaba, Tencent, Huawei,
        ByteDance, Pfizer, Moderna, Novavax, BioNTech, AstraZeneca, Johnson & Johnson, Merck, Eli Lilly,
        Novo Nordisk, Roche, Novartis, Sanofi, GSK, Gilead, Regeneron, Vertex, CATL, BYD, Panasonic,
        LG Energy Solution, QuantumScape, Northvolt, Rivian, Siemens, GE Vernova, Westinghouse, NuScale,
        Oklo, TerraPower, Commonwealth Fusion Systems, Helion, Exxon, Chevron, Shell, BP, Saudi Aramco,
        Palantir, Perplexity, Cohere, Databricks, Snowflake, Arm, Qualcomm, Broadcom, SpaceX, Boeing""",
    "technology": """large language model, machine learning, deep learning, reinforcement learning, transformer,
        diffusion model, neural network, computer vision, generative AI, AI agent, agentic AI, retrieval-augmented
        generation, quantum computing, federated learning, knowledge graph, mixture of experts, fine-tuning,
        solid-state battery, sodium-ion battery, lithium-ion battery, lithium-sulfur battery, perovskite,
        solar panel, solar power, wind power, nuclear fusion, small modular reactor, hydrogen fuel cell,
        green hydrogen, carbon capture, geothermal, grid storage, heat pump, mRNA, CRISPR, gene therapy,
        gene editing, cell therapy, CAR-T, monoclonal antibody, immunotherapy, genome sequencing, nanoparticle,
        semiconductor, robotics, humanoid robot, autonomous vehicle, edge computing, blockchain, LLM, chatbot,
        coding agent, AI coding, AI chip, GPU, data center, deepfake, watermarking, qubit, quantum battery,
        quantum computer, nuclear reactor, nuclear power, solar farm, rooftop solar, power grid, electric vehicle,
        EV battery, drone, satellite, brain-computer interface, digital twin, synthetic data, open-weight model""",
    "disease": """measles, COVID-19, influenza, bird flu, H5N1, mpox, Ebola, Marburg, dengue, malaria,
        tuberculosis, cholera, polio, HIV, RSV, Alzheimer's, Parkinson's, cancer, diabetes, obesity,
        hepatitis, leukemia, acute myeloid leukemia, lymphoma, Lyme disease, Zika, Nipah, chikungunya, West Nile, pertussis, whooping cough, sepsis,
        antimicrobial resistance, long COVID, heart disease, stroke, dementia, autism, asthma""",
    "product": """ChatGPT, GPT-4, GPT-5, Claude, Gemini, Llama, Grok, Copilot, DeepSeek, Qwen, Sora, Midjourney,
        Stable Diffusion, Cursor, Kiro, iPhone, Vision Pro, Cybertruck, Model Y, Powerwall, Starlink,
        Ozempic, Wegovy, Mounjaro, Zepbound, Paxlovid, Lecanemab, Keytruda""",
}

# Generic words that the regex rules below may catch but that are not entities.
STOP = {"The", "This", "We", "Our", "A", "An", "New", "How", "Why", "What", "Show HN", "Ask HN", "Tell HN", "Launch HN", "Towards",
        "Toward", "Beyond", "When", "Can", "Is", "Are", "Do", "Does", "Rethinking", "Learning", "Understanding",
        "Breaking", "Exclusive", "Update", "Watch", "Live", "Opinion", "Analysis", "Report", "Study"}

COMPANY_RE = re.compile(r"\b((?:[A-Z][\w&.-]*\s){0,3}[A-Z][\w&.-]*)\s(?:Inc|Corp|Corporation|Ltd|LLC|Labs|Technologies|"
                        r"Therapeutics|Pharmaceuticals|Biosciences|Robotics|Energy|Systems)\b\.?")
PERSON_RE = re.compile(r"\b(?:Dr\.|CEO|Senator|Sen\.|Secretary|President|Professor|Prof\.|founder)\s+"
                       r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b")
DISEASE_RE = re.compile(r"\b([A-Z]?[a-z]*(?:itis|osis|virus|syndrome|fever))\b")
# Coined names: CamelCase (DeepSeek, TurnBench) or caps plus digits (GPT-6.2, H100).
COINED_RE = re.compile(r"\b(?:[A-Z][a-z]+[A-Z][A-Za-z]*|[A-Z]{2,}[A-Za-z]*-?\d[\w.]*\d|[A-Z]{2,}-?\d+)\b")
# Defined acronyms: "Agent Trust Infrastructure (ATI)".
ACRONYM_RE = re.compile(r"\b((?:[A-Z][\w-]+\s){1,5}[A-Z][\w-]+)\s\(([A-Z][A-Za-z]*[A-Z])\)")
# arXiv style "Name: subtitle", Name being a coined word such as DeepSeek-R1 or MoE-Lite.
METHOD_RE = re.compile(r"^([A-Z][A-Za-z0-9]*(?:[-][A-Za-z0-9]+)*(?:\s[A-Z0-9][A-Za-z0-9-]*)?):\s")

VERBS = [  # (regex, label), checked between the two entity mentions
    (r"acquir|buy|bought|merg", "acquires"), (r"partner|team(s|ed)? up|collaborat|alliance", "partners_with"),
    (r"launch|releas|unveil|introduc|announc", "launches"), (r"invest|fund|back", "invests_in"),
    (r"treat|cure|vaccin|against|target", "treats"), (r"cause|link|tied to|associated", "linked_to"),
    (r"use|using|power|built on|based on|with", "uses"), (r"beat|outperform|rival|vs\.?|versus|compet", "competes_with"),
]

_TERMS = []
for typ, blob in GAZETTEER.items():
    for term in (t.strip() for t in blob.split(",")):
        if term:
            flags = 0 if (term.isupper() or len(term) <= 4) else re.I
            _TERMS.append((re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", flags), term, typ))

SENT_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")


def mentions(sentence, first=False):
    """Return [(start, Entity)] found in one sentence."""
    found = {}
    for rx, term, typ in _TERMS:
        if m := rx.search(sentence):
            found.setdefault(term.lower(), (m.start(), Entity(term, typ)))
    for rx, typ in ((COMPANY_RE, "company"), (PERSON_RE, "person"), (DISEASE_RE, "disease")):
        for m in rx.finditer(sentence):
            name = m.group(0).rstrip(".") if typ == "company" else m.group(1)
            if name not in STOP and len(name) > 3:
                found.setdefault(name.lower(), (m.start(), Entity(name, typ)))
    for m in COINED_RE.finditer(sentence):
        if m.group(0) not in STOP and m.group(0) not in ("HN", "AI"):
            found.setdefault(m.group(0).lower(), (m.start(), Entity(m.group(0), "product")))
    for m in ACRONYM_RE.finditer(sentence):
        found.setdefault(m.group(1).lower(), (m.start(), Entity(m.group(1), "technology")))
    if first and (m := METHOD_RE.match(sentence)) and m.group(1) not in STOP and any(c.isupper() for c in m.group(1)[1:]):
        found.setdefault(m.group(1).lower(), (0, Entity(m.group(1), "technology")))
    return sorted(found.values(), key=lambda x: x[0])


class HeuristicExtractor:
    def extract(self, text):
        claims = []
        for i, sm in enumerate(SENT_RE.finditer(text or "")):
            s = sm.group(0).strip()
            if len(s) < 8:
                continue
            ms = mentions(s, first=(i == 0))
            for _, e in ms:
                claims.append(Claim(e, e, "mentioned_in", f"{e.name} is mentioned in this document", s))
            for (p1, a), (p2, b) in zip(ms, ms[1:]):  # adjacent pairs keep the relation local
                between = s[p1:p2 + 1].lower()
                label = next((lab for rx, lab in VERBS if re.search(rx, between)), "co_mentioned")
                claims.append(Claim(a, b, label, f"{a.name} {label.replace('_', ' ')} {b.name}", s))
        return keep(claims, text or "")

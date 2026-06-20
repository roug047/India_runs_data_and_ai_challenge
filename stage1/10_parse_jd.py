"""
stage1/10_parse_jd.py
Parse the Senior AI Engineer JD into a structured config the whole pipeline keys off.

DESIGN (Architecture V6, zero-API):
  - The JD is parsed into a hand-authored JD_CONFIG_FALLBACK derived line-by-line from
    the organizers' job_description.docx (the source of truth — NOT the derived .md).
  - This is DETERMINISTIC and correct even with no model. That's the default path.
  - An optional local-LLM path (Qwen GGUF via llama-cpp) can refine/extend the config;
    its JSON is MERGED OVER the fallback so we never lose a required key. OFF by default.

Every requirement strength, disqualifier, and the ideal-candidate summary below is
traceable to a specific sentence in the JD. Comments cite the source phrase.

Run:  python stage1/10_parse_jd.py
      python stage1/10_parse_jd.py --use-llm   # optional refinement (needs the GGUF)
Output: artifacts/jd_config.json, artifacts/jd_text.txt
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import read_docx_text   # noqa: E402


# ---------------------------------------------------------------------------
# DETERMINISTIC JD CONFIG — authored from job_description.docx, sentence by sentence.
# ---------------------------------------------------------------------------
JD_CONFIG_FALLBACK = {
    # "5-9 years ... This is a range, not a requirement ... seriously consider candidates
    #  outside the band if other signals are strong."
    "min_yoe": 5,
    "max_yoe": 9,
    "yoe_soft": True,
    # "ideal candidate ... 6-8 years total, of which 4-5 are in applied ML/AI roles"
    "yoe_ideal_low": 6,
    "yoe_ideal_high": 8,

    # "Pune/Noida ... Candidates in Hyderabad, Pune, Mumbai, Delhi NCR welcome.
    #  Outside India: case-by-case, but we don't sponsor work visas."
    "preferred_locs": ["pune", "noida", "hyderabad", "mumbai", "delhi", "ncr",
                        "delhi ncr", "gurgaon", "gurugram"],
    "acceptable_countries": ["india"],
    "outside_india_visa_sponsorship": False,   # "we don't sponsor work visas"

    # "We'd love sub-30-day notice. We can buy out up to 30 days. 30+ day notice candidates
    #  are still in scope but the bar gets higher."
    "notice_ideal_days": 30,
    "notice_soft_max_days": 30,
    "notice_in_scope_max_days": 180,           # schema caps notice at 180

    "production_required": True,               # research-without-production => hard reject

    # --- "Things you absolutely need" (hard requirements) ---
    # name -> strength in [0,1]. Each maps to a JD bullet.
    "hard_requirements": {
        # "Production experience with embeddings-based retrieval systems ... deployed to
        #  real users ... embedding drift, index refresh, retrieval-quality regression."
        "embeddings_retrieval": 1.00,
        # "Production experience with vector databases or hybrid search infrastructure —
        #  Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS."
        "vector_search_infra": 1.00,
        # "Hands-on experience designing evaluation frameworks for ranking systems —
        #  NDCG, MRR, MAP, offline-to-online correlation, A/B test interpretation."
        "ranking_evaluation": 0.95,
        # "Strong Python. Yes really, we care about code quality."
        "python_production": 0.85,
    },

    # --- "Things we'd like you to have but won't reject you for" (soft requirements) ---
    "soft_requirements": {
        "llm_finetuning": 0.65,            # "LoRA, QLoRA, PEFT"
        "learning_to_rank": 0.70,          # "XGBoost-based or neural"
        "hr_tech_experience": 0.55,        # "HR-tech, recruiting tech, or marketplace"
        "distributed_systems": 0.50,       # "distributed systems or large-scale inference"
        "open_source": 0.55,               # "Open-source contributions in the AI/ML space"
        "hybrid_retrieval": 0.80,          # ideal: "strong opinions ... hybrid vs dense"
    },

    # --- "Things we explicitly do NOT want" + the disqualifiers block ---
    # Names map 1:1 to flags computed in Stage 2.
    "disqualifiers": [
        # "pure research environments ... without any production deployment — we will not
        #  move forward. We are explicit about this." (MOST emphatic)
        "pure_research_no_prod",
        # "'AI experience' consists primarily of recent (under 12 months) LangChain to call
        #  OpenAI ... unless ... substantial pre-LLM-era ML production experience."
        "langchain_only_under_12mo",
        # "senior engineer who hasn't written production code in the last 18 months ...
        #  moved into 'architecture' or 'tech lead' roles."
        "no_code_18mo",
        # "only worked at consulting firms (TCS, Infosys, Wipro, Accenture, Cognizant,
        #  Capgemini, etc.) in their entire career."
        "pure_consulting_career",
        # "primary expertise is computer vision, speech, or robotics without significant
        #  NLP/IR exposure."
        "cv_speech_robotics_only",
        # "work has been entirely on closed-source proprietary systems for 5+ years without
        #  external validation (papers, talks, open-source)."
        "closed_source_no_validation",
        # "Title-chasers ... switching companies every 1.5 years." (soft-negative; penalize)
        "title_chaser",
    ],

    # Behavioral down-weighting is explicitly requested by the JD hackathon note:
    # "a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter
    #  response rate is ... not actually available. Down-weight them appropriately."
    "behavioral_signals_matter": True,

    # Consulting firms named explicitly in the JD (used by Stage 2 consulting features).
    "consulting_firms": ["tcs", "tata consultancy", "infosys", "wipro", "accenture",
                         "cognizant", "capgemini", "mphasis", "tech mahindra", "hexaware",
                         "ltimindtree", "mindtree", "hcl", "l&t infotech", "persistent",
                         "igate", "syntel", "birlasoft"],

    # The ideal-candidate paragraph, near-verbatim — used to build the "ideal" embedding
    # AND as the reference text for shipper-vs-researcher judgment.
    "ideal_profile_summary": (
        "Senior AI engineer with about 6 to 8 years total experience, of which 4 to 5 are "
        "in applied ML/AI roles at product companies rather than pure services. Has shipped "
        "at least one end-to-end ranking, search, or recommendation system to real users at "
        "meaningful scale. Has production experience with embeddings-based retrieval and with "
        "vector search or hybrid search infrastructure, and has designed evaluation frameworks "
        "for ranking systems using NDCG, MRR, and MAP with offline-to-online correlation. Holds "
        "strong, defensible opinions about retrieval (hybrid vs dense), evaluation (offline vs "
        "online), and LLM integration (when to fine-tune vs prompt), grounded in systems they "
        "actually built. Writes strong production Python and tilts toward shipper over researcher. "
        "Located in or willing to relocate to Noida or Pune, and active in the job market."
    ),

    # One-line statement of the trap, for documentation / reasoning grounding.
    "anti_pattern_summary": (
        "Not a fit: candidates whose skills section lists many AI keywords but whose career "
        "history and title do not show building production retrieval/ranking/recsys systems; "
        "e.g. a Marketing Manager with a perfect AI skill list. Keyword presence is a trap."
    ),

    "_source": "hand-authored from job_description.docx (deterministic fallback)",
    "_jd_role": "Senior AI Engineer — Founding Team, Redrob AI",
}


def parse_jd_with_llm(jd_text: str, base: dict) -> dict:
    """
    OPTIONAL: refine the config with a local Qwen GGUF. Merged OVER the fallback so all
    required keys survive. Returns base unchanged if the model/lib is unavailable.
    """
    model_path = config.REPO_ROOT / "models" / "qwen2.5-7b-instruct-q4_k_m.gguf"
    if not model_path.exists():
        print(f"  [llm] model not found at {model_path} — keeping deterministic config.")
        return base
    try:
        from llama_cpp import Llama
    except ImportError:
        print("  [llm] llama-cpp-python not installed — keeping deterministic config.")
        return base

    llm = Llama(model_path=str(model_path), n_ctx=8192, n_gpu_layers=-1, verbose=False)
    prompt = (
        "Extract structured fields from this job description. Return ONLY JSON with keys: "
        "hard_requirements (obj name->0..1), soft_requirements (obj name->0..1), "
        "disqualifiers (list of strings), ideal_profile_summary (string). Capture IMPLICIT "
        "signals (e.g. 'shipped to real users' => production required).\n\nJD:\n"
        + jd_text + "\n\nJSON:"
    )
    out = llm(prompt, max_tokens=1500, temperature=0.0)["choices"][0]["text"]
    try:
        parsed = json.loads(out[out.index("{"): out.rindex("}") + 1])
        merged = {**base, **{k: v for k, v in parsed.items() if v}}
        # never let the model drop required scaffolding
        for k in ("min_yoe", "max_yoe", "disqualifiers", "consulting_firms",
                  "ideal_profile_summary"):
            merged.setdefault(k, base[k])
        print("  [llm] merged LLM refinements over deterministic base.")
        return merged
    except Exception as e:
        print(f"  [llm] parse failed ({e}) — keeping deterministic config.")
        return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-llm", action="store_true",
                    help="Optionally refine with local Qwen GGUF (off by default).")
    args = ap.parse_args()
    config.ensure_artifacts()

    # Source of truth = organizers' docx. Fall back to .md only if docx absent.
    if config.JD_DOCX.exists():
        jd_text = read_docx_text(config.JD_DOCX)
        src = "job_description.docx (organizers)"
    elif config.JD_MD.exists():
        jd_text = config.JD_MD.read_text(encoding="utf-8")
        src = "job_description.md (fallback)"
    else:
        print("FATAL: no job description found (docx or md).")
        return 1

    config.JD_TEXT_CACHE.write_text(jd_text, encoding="utf-8")
    print(f"JD source: {src}  ({len(jd_text)} chars) -> {config.JD_TEXT_CACHE}")

    cfg = dict(JD_CONFIG_FALLBACK)
    if args.use_llm:
        cfg = parse_jd_with_llm(jd_text, cfg)
    else:
        print("  Using deterministic JD config (no LLM). Fully reproducible.")

    config.JD_CONFIG_JSON.write_text(json.dumps(cfg, indent=2))
    print("-" * 60)
    print(f"hard requirements:  {list(cfg['hard_requirements'])}")
    print(f"soft requirements:  {list(cfg['soft_requirements'])}")
    print(f"disqualifiers ({len(cfg['disqualifiers'])}): {cfg['disqualifiers']}")
    print(f"yoe band: {cfg['min_yoe']}-{cfg['max_yoe']} (ideal {cfg['yoe_ideal_low']}-{cfg['yoe_ideal_high']})")
    print(f"jd_config -> {config.JD_CONFIG_JSON}")
    print("STAGE 1.10 (parse JD): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

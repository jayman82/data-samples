# AWS Well-Architected Core Knowledge Base Plan

## 1. What to Include (Authoritative Sources)
Prioritize evergreen, first-party guidance and pattern libraries:

- **AWS Well-Architected Framework** (all six pillars + pillar pages).
- **Prescriptive Guidance** (Landing Zones, migration playbooks, service selection guides).
- **Security Reference Architecture (SRA)** (canonical multi-account security blueprint).
- **AWS Architecture Center & Solutions Library** (reference architectures + deployable solutions).
- **AWS Architecture Blog** (tagged Well-Architected / architecture best practices; use summaries, not full copies).
- (Optional) Recent GenAI posts that map WA practices to LLM/Bedrock patterns.

> **Rule of thumb:** store your curated notes/summaries + structured metadata + citations and link to the source; do not bulk copy full text.

---

## 2. Locator (Discovery Workflow)
- **Seed list:** hand-maintained YAML of canonical entry points (docs home pages, pillar pages, SRA, Solutions Library).  
- **Feed & delta:** poll Architecture Blog tags weekly; de-dupe by canonical URL.  
- **Inclusion filters:** keep HTML/PDF pages with stable URLs; ignore marketing/news unless they encode durable practices.

---

## 3. Curation Pipeline (Human-in-the-loop)
**Stages:** discover → fetch → extract → summarize → tag → approve → publish

- **Extract:** title, summary (200–400 words), key takeaways, pillar(s), lens (if relevant), services, patterns, diagrams (links only), and citations.
- **Summarize:** produce *two* levels—(a) executive brief (5–7 bullets), (b) deep dive (markdown sections).
- **Tagging taxonomy:**
  - `pillar` (Operational Excellence, Security, Reliability, Performance Efficiency, Cost, Sustainability)
  - `domain` (networking, identity, observability, data, serverless, genAI, etc.)
  - `pattern` (landing-zone, multi-account, zero-trust, backup, blue/green, IaC, cost-allocation)
  - `service` (Control Tower, IAM, Organizations, VPC, GuardDuty, KMS, etc.)
  - `reference_type` (framework, prescriptive-guide, solution, blog, whitepaper)
- **Approval:** DynamoDB table or Git PR gates for curator sign-off.
- **Refresh:** weekly EventBridge run; re-visit sources for drift and re-summarize if major updates.

---

## 4. Storage Formats (Built for RAG)
- **S3 “Curated” KB (for Bedrock KB):** Markdown/HTML files, one per curated artifact.  
- **Search index (OpenSearch):** compact JSONL with fields for hybrid search + filters (pillar, domain, service, pattern, year, source_url) and an embedding.  

**Example JSONL Record:**
```json
{
  "id": "sra-v4-overview",
  "title": "AWS Security Reference Architecture (v4) — Overview",
  "summary_exec": [
    "Canonical multi-account security blueprint",
    "Defines Security Tooling/Log Archive accounts",
    "Integrates GuardDuty, Security Hub, CT, KMS..."
  ],
  "key_takeaways": [
    "Use Organizations + SCP guardrails",
    "Centralize log archiving; account baselines",
    "Align controls to WA Security pillar"
  ],
  "pillar": ["Security"],
  "domain": ["identity", "logging", "governance"],
  "service": ["Organizations","Control Tower","KMS","GuardDuty","Security Hub"],
  "reference_type": "prescriptive-guidance",
  "source_url": "https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/welcome.html",
  "last_checked": "2025-08-16",
  "embedding": "<vector>"
}
```

---

## 5. Retrieval Strategy (Chatbot)
1. **Bedrock KB first** on curated Markdown → returns grounded passages with citations.  
2. If the question needs facets/filters, query OpenSearch with taxonomy filters and re-ask the LLM with both sources.  
3. Always render provenance (title → AWS link), and show the practice level (framework vs prescriptive vs solution).

---

## 6. Minimal Build Plan (1–2 Sprints)
**Sprint A (KB foundation):**
- Create seed YAML of sources; implement discovery/fetcher (Lambda or container).
- Build extractor → summarizer (LLM), with guardrails to avoid long verbatim copies.
- Design taxonomy; write to `s3://kb/curated/<slug>.md` and `s3://kb/search/index.jsonl`.
- Spin up Bedrock Knowledge Base on curated prefix; smoke test Q&A.

**Sprint B (quality & scale):**
- Add OpenSearch serverless vector collection; load JSONL for hybrid search.
- Wire a curator UI (React) to approve/edit summaries.
- Add freshness checks (ETag/Last-Modified) + weekly deltas and Slack alerts.

---

## 7. Starter Pack (Must-have Pages to Curate First)
- WA Framework home & pillar intros (one summary per pillar).
- Landing Zone (Control Tower + considerations).
- Security Reference Architecture (overview + account layout + logging).
- Solutions Library index (map common patterns to deployable solutions).
- Representative Architecture Blog posts tagged *Well-Architected* or *best practices*.

---

## 8. Acceptance Criteria ("Done Means")
- Query “cost allocation for multi-account” returns WA Cost-Optimization page + Prescriptive Guidance + Solutions pattern, each with pillar tags, services, and links.  
- Query “What’s a landing zone?” → concise definition, control-plane services, link to Control Tower guidance.  
- Query “Show me an SRA-aligned log strategy” → summary + link to SRA’s Log Archive guidance.

---


// Hand-written page content that is not a measurement. Measurements live in src/data/site-data.json only.

/** Fill these in: shown in the landing page footer. Empty strings render as "to be added". */
export const TEAM = {
  TEAM_NAME: "",
  MEMBERS: [] as string[],
  COLLEGE: "",
  MENTOR: "",
};

/**
 * Context facts for "The problem". Source: the Phase 13 project brief (not from NIYAM's data); the owner should
 * confirm the wording and dates against the official notifications before publishing.
 */
export const CONTEXT = {
  nbc: "The National Building Code of India 2016 has been replaced by the advisory NBCS 2026 (notified 30 April 2026).",
  singapore: "Singapore makes digital (BIM) submission for building approval mandatory from 1 October 2026.",
  ids: "buildingSMART published IDS 1.0, an open standard for machine-checkable information requirements.",
};

export const REPO_DOCS = [
  { label: "Evaluation method and metrics", path: "docs/evaluation.md" },
  { label: "Rule specs and what they cannot express", path: "docs/spec-backlog.md" },
  { label: "Real IFC models: what the audit could check", path: "docs/real-models.md" },
  { label: "What a model must contain (modelling profile)", path: "docs/modelling-profile.md" },
  { label: "Reviewer guide", path: "docs/review/REVIEWER_GUIDE.md" },
  { label: "Web app notes", path: "docs/frontend.md" },
];

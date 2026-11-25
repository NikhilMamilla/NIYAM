// Hand-written page content that is not a measurement. Measurements live in src/data/site-data.json only.

/** Shown in the landing page footer. */
export const TEAM = {
  TEAM_NAME: "Abhyudaya",
  MEMBERS: ["Nikhil Mamilla", "Yagna Sri Hasa", "G Nikhitha", "D Sahithi", "G Sahithi"],
  COLLEGE: "B V Raju Institute of Technology (BVRIT), Narsapur, Telangana",
  MENTOR: "Dr. Lanke Pallavi",
  MENTOR_ROLE: "Associate Professor & Associate HoD",
};

/** The competition this prototype is entered in. */
export const COMPETITION = {
  NAME: "DBI 2026 Student Competition (CDCPIndia / buildingSMART India)",
  THEME: "AI, Automation and Digital Workflows",
  SECONDARY_THEME: "Integrated BIM and Information Management",
  FINALS: "17 Dec 2026, IIT Bombay",
};

/**
 * Context facts for "The problem". Each is checked in docs/sources.md (sources and access dates); change the two
 * together.
 */
export const CONTEXT = {
  nbc: "India: BIS withdrew the National Building Code 2016 with effect from 30 April 2026 and replaced it with the advisory National Building Construction Standards 2026 (SP 7:2026).",
  singapore: "Singapore: from 1 October 2026, building plan submissions through CORENET X are mandatory for new projects of 5,000 m² gross floor area and above.",
  ids: "buildingSMART: IDS 1.0, published as a final standard in June 2024, is an open standard for machine-checkable information requirements.",
};

/** Files the footer offers for download. They are copied into public/downloads/ by scripts/sync-downloads.mjs. */
export type Doc = { label: string; file: string; about: string };
export const DOC_GROUPS: { title: string; blurb: string; docs: Doc[] }[] = [
  {
    title: "Start here",
    blurb: "What NIYAM is, where it stands, and how to run it.",
    docs: [
      { label: "Project overview", file: "README.pdf", about: "What NIYAM is, how it works, where it stands today, and how to run it." },
      { label: "Project status and known issues", file: "STATUS.pdf", about: "What is final, what is still open, and the commands to reproduce the tests and the re-score." },
      { label: "Web app notes", file: "frontend.pdf", about: "The stack, the 3D view, the design system, and the checks to repeat in your own browser." },
    ],
  },
  {
    title: "Method and results",
    blurb: "How rules are made, scored and tested.",
    docs: [
      { label: "Evaluation: method and metrics", file: "evaluation.pdf", about: "How compilation is scored on held-out buildings the gate never sees, and what the first real run showed." },
      { label: "Rule specs and what they cannot express", file: "spec-backlog.pdf", about: "Which sentences became machine checks, and why the rest do not fit a single-element template." },
      { label: "Rule specs and the generator", file: "specgen.pdf", about: "How one small spec file becomes an IDS file or a Python check, and the five templates." },
      { label: "Real IFC models", file: "real-models.pdf", about: "Two real building models run through the audit, and the data they lack." },
    ],
  },
  {
    title: "How checks run",
    blurb: "The gate, the audit engine and the data a model needs.",
    docs: [
      { label: "The geometric gate and its sandbox", file: "geometric-gate.pdf", about: "How computed-value checks run safely, and what the sandbox does not enforce." },
      { label: "Audit engine and exports", file: "audit.pdf", about: "How a model is audited, and what the JSON, HTML and BCF outputs contain." },
      { label: "What a model must contain", file: "modelling-profile.pdf", about: "The data an IFC model needs before NIYAM can check it." },
      { label: "Synthetic sample buildings", file: "samples.pdf", about: "The generated test models behind the samples and what each one shows." },
    ],
  },
  {
    title: "Technical notes",
    blurb: "Verified findings behind the design choices.",
    docs: [
      { label: "Can IDS express numeric limits?", file: "notes-ids-expressiveness.pdf", about: "A tested note on which numeric lower bounds IDS 1.0 can and cannot state." },
      { label: "Geometric tier spike", file: "notes-geometric-spike.pdf", about: "Which sentences compare a value that has to be computed from geometry." },
      { label: "ifctester notes", file: "notes-ifctester.pdf", about: "Verified notes on building and running IDS files with ifctester." },
      { label: "Corpus candidates", file: "corpus-candidates.pdf", about: "Keyword-scored candidate clauses from the bye-laws, kept for human review." },
    ],
  },
  {
    title: "Review, data and licence",
    blurb: "For reviewers, and the files the tools use.",
    docs: [
      { label: "Reviewer guide", file: "REVIEWER_GUIDE.pdf", about: "How a domain expert reviews the draft rules and returns decisions." },
      { label: "Review sheet for rule reviewers", file: "review-sheet.csv", about: "Every draft rule with the sentence, the check and blank decision columns." },
      { label: "Data readiness file (IDS 1.0)", file: "niyam-data-readiness.ids", about: "Open it against your model to see what data to add before auditing." },
      { label: "A real gate rejection", file: "gate-rejection.json", about: "One candidate rule the gate refused, with the reason." },
      { label: "Licence (MIT)", file: "LICENSE", about: "Free to use, copy and change, with the licence notice kept; three copied UI components keep their own terms." },
      { label: "Third-party notices", file: "THIRD_PARTY_NOTICES.pdf", about: "Every shipped package, font, component and data file, with its licence and source." },
      { label: "Sources for the regulatory facts", file: "sources.pdf", about: "The pages behind each date and rule on this site, with access dates." },
    ],
  },
];


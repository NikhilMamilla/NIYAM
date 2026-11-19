// Plain-language glossary tooltips for the few technical words the UI cannot avoid.
import { useId, useState, type ReactNode } from "react";

export const GLOSSARY = {
  IFC: "Industry Foundation Classes: the open file format (ISO 16739) for building models, exported by tools such as Revit, ArchiCAD and SketchUp. NIYAM reads IFC4.",
  IDS: "Information Delivery Specification 1.0: a buildingSMART standard for saying which data a model must contain, as an XML file any IDS checker can run.",
  BCF: "BIM Collaboration Format 2.1: a standard file of issues (with the element and a viewpoint) that design tools can import.",
  gate: "The verifier gate: a rule drafted by an AI model is only kept if it is valid, loads, applies to test buildings, passes the test building that follows the rule and fails the one that breaks it.",
  unchecked: "Unchecked: the rule applies to this element, but the model lacks the data needed to decide (for example a door without a width). It is never counted as a pass.",
} as const;

export type GlossaryKey = keyof typeof GLOSSARY;

/** A word with a definition that appears on hover and on keyboard focus (Escape hides it). */
export function Term({ k, children }: { k: GlossaryKey; children?: ReactNode }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  return (
    <button type="button" className="term" aria-describedby={id} onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
            onKeyDown={(e) => e.key === "Escape" && setOpen(false)}>
      {children ?? k}
      <span role="tooltip" id={id} className="term-tip" hidden={!open}>{GLOSSARY[k]}</span>
    </button>
  );
}

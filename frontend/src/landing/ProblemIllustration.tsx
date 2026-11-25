// Building section illustration showing regulatory checks
export function ProblemIllustration() {
  return (
    <figure className="problem-figure">
      <img 
        src="/screens/building-section-checks.webp" 
        alt="Building section showing regulatory checks: height limit ≤ 7.5m, room size ≥ 9.0m², setback 3.0m, exit width ≥ 1.0m, and building width 12.0m"
        className="problem-img"
        loading="lazy"
      />
      <figcaption>Illustration: the kind of limits a plan check compares (height, room size, setback, exit width). Not a real building.</figcaption>
    </figure>
  );
}

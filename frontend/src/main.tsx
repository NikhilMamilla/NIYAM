import { StrictMode, Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import Landing from "./landing/Landing";
import { Link, useRoute } from "./router";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/landing.css";

// The dashboard (three.js, web-ifc) is a separate chunk: the landing page never loads WebGL code.
const Dashboard = lazy(() => import("./App"));

function NotFound({ path }: { path: string }) {
  return (
    <main className="not-found sheet">
      <h1>Nothing is drawn at {path}</h1>
      <p className="lede">This address is not part of NIYAM.</p>
      <div className="btn-row"><Link to="/" className="btn primary">Go to the start</Link><Link to="/app" className="btn">Open the app</Link></div>
    </main>
  );
}

function Root() {
  const route = useRoute();
  if (route.page === "landing") return <Landing />;
  if (route.page === "app") {
    return (
      <Suspense fallback={<p className="route-loading" role="status">Opening the app…</p>}>
        <Dashboard initialSample={route.sample} />
      </Suspense>
    );
  }
  return <NotFound path={route.path} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);

import { StrictMode, Suspense, lazy } from "react";
import Button from "./Button";
import { createRoot } from "react-dom/client";
import Landing from "./landing/Landing";
import { Link, useRoute } from "./router";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/landing.css";
import "./styles/loader.css";

// The dashboard (three.js, web-ifc) is a separate chunk: the landing page never loads WebGL code.
// The loader stays on screen for at least 700 ms, so it reads as a loader and never as a flicker.
const Dashboard = lazy(() => Promise.all([import("./App"), new Promise((done) => setTimeout(done, 700))]).then(([m]) => m));

function NotFound({ path }: { path: string }) {
  return (
    <main className="not-found sheet">
      <h1>Nothing is drawn at {path}</h1>
      <p className="lede">This address is not part of NIYAM.</p>
      <div className="btn-row"><Button as={Link} to="/" primary>Go to the start</Button><Button as={Link} to="/app">Open the app</Button></div>
    </main>
  );
}

/** Shown while the dashboard's chunk downloads. */
function RouteLoader() {
  return (
    <div className="route-loader" role="status" aria-label="Loading">
      <span /><span /><span />
    </div>
  );
}

function Root() {
  const route = useRoute();
  if (route.page === "landing") return <Landing />;
  if (route.page === "app") {
    return (
      <Suspense fallback={<RouteLoader />}>
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

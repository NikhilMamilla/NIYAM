// A tiny History API router: "/" is the landing page, "/app" the dashboard. Back/forward and deep links work;
// the Vite dev server and `vite preview` fall back to index.html for both paths.
import { useEffect, useState, type AnchorHTMLAttributes, type MouseEvent } from "react";

export type Route = { page: "landing" } | { page: "app"; sample: string | null } | { page: "not-found"; path: string };

/** Parse a location into a route (pure, unit-tested). */
export function routeOf(pathname: string, search = ""): Route {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/") return { page: "landing" };
  if (path === "/app") {
    const sample = new URLSearchParams(search).get("sample");
    return { page: "app", sample: sample && /^[a-z0-9_]+$/.test(sample) ? sample : null };
  }
  return { page: "not-found", path };
}

const listeners = new Set<() => void>();

export function navigate(to: string, opts: { replace?: boolean } = {}) {
  if (to === window.location.pathname + window.location.search) return;
  if (opts.replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  for (const l of listeners) l();
  if (!to.includes("#")) window.scrollTo({ top: 0 });
}

export function useRoute(): Route {
  const read = () => routeOf(window.location.pathname, window.location.search);
  const [route, setRoute] = useState<Route>(read);
  useEffect(() => {
    const update = () => setRoute(read());
    listeners.add(update);
    window.addEventListener("popstate", update);
    return () => {
      listeners.delete(update);
      window.removeEventListener("popstate", update);
    };
  }, []);
  return route;
}

/** An in-app link: a real <a href> (copyable, middle-clickable) that navigates without a reload. */
export function Link({ to, onClick, ...rest }: AnchorHTMLAttributes<HTMLAnchorElement> & { to: string }) {
  const handle = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    navigate(to);
  };
  return <a href={to} onClick={handle} {...rest} />;
}

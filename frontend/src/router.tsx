// A tiny History API router: "/" is the landing page, "/app" the dashboard. Back/forward and deep links work;
// the Vite dev server and `vite preview` fall back to index.html for both paths.
import { useEffect, useState, type AnchorHTMLAttributes, type MouseEvent } from "react";

export type Route = { page: "landing" } | { page: "app"; sample: string | null } | { page: "not-found"; path: string };

// The site's base path: "" locally, "/NIYAM" on GitHub Pages. Routes are written without it.
const BASE = import.meta.env.BASE_URL.replace(/\/+$/, "");
export const href = (to: string) => BASE + to;
/** A file in public/, under the base path. */
export const asset = (path: string) => BASE + path;

/** Parse a location into a route (pure, unit-tested). */
export function routeOf(pathname: string, search = "", base = BASE): Route {
  if (base && (pathname === base || pathname.startsWith(`${base}/`))) pathname = pathname.slice(base.length);
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
  const url = href(to);
  if (url === window.location.pathname + window.location.search) return;
  if (opts.replace) window.history.replaceState(null, "", url);
  else window.history.pushState(null, "", url);
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
  return <a href={href(to)} onClick={handle} {...rest} />;
}

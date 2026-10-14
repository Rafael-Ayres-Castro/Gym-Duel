// Hash router (#/login, #/home, ...): no server config needed and refresh keeps the screen.
// Each route declares whether it needs a logged user and how to mount itself.

let routes = {};
let fallback = null;
let current = null; // { name, cleanup }

export function defineRoutes(map, defaultRoute) {
  routes = map;
  fallback = defaultRoute;
}

export function go(name) {
  if (currentRouteName() === name) resolve();
  else window.location.hash = `#/${name}`;
}

export function currentRouteName() {
  return window.location.hash.replace(/^#\//, '') || null;
}

/** Re-mount the current screen (e.g. after a check-in changes the data). */
export function reload() { resolve(); }

async function resolve() {
  const name = currentRouteName();
  const route = routes[name];
  if (!route) return go(fallback(name));

  const redirect = route.guard?.();
  if (redirect && redirect !== name) return go(redirect);

  if (current?.cleanup) current.cleanup();
  current = { name, cleanup: await route.mount() };
}

export function startRouter() {
  window.addEventListener('hashchange', resolve);
  resolve();
}

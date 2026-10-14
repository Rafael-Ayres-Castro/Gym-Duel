// localStorage can throw (private mode, blocked storage); the app must keep working without it.

export function readItem(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

export function writeItem(key, value) {
  try {
    if (value == null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch { /* storage unavailable: the value just won't persist */ }
}

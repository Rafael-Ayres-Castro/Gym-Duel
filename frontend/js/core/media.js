// Breakpoint shared with the CSS (min-width: 960px = desktop layout with sidebar and modal).
const desktopQuery = window.matchMedia('(min-width: 960px)');

export const isDesktop = () => desktopQuery.matches;

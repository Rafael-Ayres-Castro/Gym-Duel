// Navigation entries shared by the mobile bottom bar and the desktop sidebar.
// `short` is the label on the bottom bar; entries with `soon` are disabled and show "EM BREVE";
// `badge` is the key of GET /api/badges shown as a pink counter.
export const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: 'home' },
  { id: 'history', label: 'Histórico', icon: 'history' },
  { id: 'challenges', label: 'Desafios', icon: 'swords', soon: 'Desafios chegam na próxima etapa.' },
  { id: 'rewards', label: 'Prêmios', icon: 'trophy', badge: 'rewards' },
  { id: 'goals', label: 'Metas e regras', short: 'Metas', icon: 'target' },
];

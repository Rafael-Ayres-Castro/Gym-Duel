// Navigation entries shared by the mobile bottom bar and the desktop sidebar.
// Entries with `soon` are disabled in the MVP and show the "EM BREVE" badge.
export const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: 'home' },
  { id: 'history', label: 'Histórico', icon: 'history' },
  { id: 'rules', label: 'Regras', icon: 'book' },
  { id: 'rewards', label: 'Prêmios', icon: 'trophy', soon: 'Prêmios chega na próxima fase.' },
  { id: 'profile', label: 'Perfil', icon: 'user', soon: 'Perfil chega na próxima fase.' },
];

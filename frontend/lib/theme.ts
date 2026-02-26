export const theme = {
  brand: {
    gradient: "from-[#667eea] to-[#764ba2]",
    primary: "#667eea",
    secondary: "#764ba2",
    gradientCss: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  },

  status: {
    success: { bg: "bg-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500", border: "border-l-emerald-500", hex: "#10b981" },
    failed: { bg: "bg-red-100", text: "text-red-700", dot: "bg-red-500", border: "border-l-red-500", hex: "#ef4444" },
    warning: { bg: "bg-amber-100", text: "text-amber-700", dot: "bg-amber-500", border: "border-l-amber-500", hex: "#f59e0b" },
    info: { bg: "bg-blue-100", text: "text-blue-700", dot: "bg-blue-500", border: "border-l-blue-500", hex: "#3b82f6" },
    noChanges: { bg: "bg-purple-100", text: "text-purple-700", dot: "bg-purple-500", border: "border-l-purple-500", hex: "#8b5cf6" },
    idle: { bg: "bg-gray-100", text: "text-gray-600", dot: "bg-gray-400", border: "border-l-gray-400", hex: "#9ca3af" },
    queued: { bg: "bg-yellow-100", text: "text-yellow-700", dot: "bg-yellow-500", border: "border-l-yellow-500", hex: "#eab308" },
    running: { bg: "bg-blue-100", text: "text-blue-700", dot: "bg-blue-500", border: "border-l-blue-500", hex: "#3b82f6" },
  },

  health: {
    healthy: { bg: "bg-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500", hex: "#10b981" },
    warning: { bg: "bg-amber-100", text: "text-amber-700", dot: "bg-amber-500", hex: "#f59e0b" },
    failing: { bg: "bg-red-100", text: "text-red-700", dot: "bg-red-500", hex: "#ef4444" },
    unknown: { bg: "bg-gray-100", text: "text-gray-500", dot: "bg-gray-400", hex: "#9ca3af" },
  },

  extractors: {
    simplegameguide: { bg: "bg-blue-100", text: "text-blue-700" },
    mosttechs: { bg: "bg-orange-100", text: "text-orange-700" },
    wsop: { bg: "bg-green-100", text: "text-green-700" },
    crazyashwin: { bg: "bg-pink-100", text: "text-pink-700" },
    techyhigher: { bg: "bg-cyan-100", text: "text-cyan-700" },
    gamesbie: { bg: "bg-violet-100", text: "text-violet-700" },
    coinscrazy: { bg: "bg-yellow-100", text: "text-yellow-700" },
    default: { bg: "bg-gray-100", text: "text-gray-700" },
  },

  charts: {
    success: "#10b981",
    failed: "#ef4444",
    noChanges: "#8b5cf6",
    links: "#667eea",
    sites: ["#667eea", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"],
  },

  nav: {
    bg: "bg-slate-900",
    activeItem: "bg-white/10",
    hoverItem: "bg-white/5",
    text: "text-slate-300",
    activeText: "text-white",
  },
} as const;

export function getStatusStyle(status: string) {
  return theme.status[status as keyof typeof theme.status] || theme.status.idle;
}

export function getHealthStyle(health: string) {
  return theme.health[health as keyof typeof theme.health] || theme.health.unknown;
}

export function getExtractorStyle(extractor: string) {
  return theme.extractors[extractor as keyof typeof theme.extractors] || theme.extractors.default;
}

/* ============================================================
   Renders the shared top nav + bottom nav into every app page.
   Usage: <body data-page="home"> ... <div id="app-nav"></div>
   ============================================================ */

const NAV_ITEMS = [
  { key: "home", label: "Home", icon: "🏠", href: "home.html" },
  { key: "reels", label: "Reels", icon: "🎥", href: "reels.html" },
  { key: "tea", label: "Tea", icon: "☕", href: "tea.html" },
  { key: "communities", label: "Communities", icon: "👥", href: "communities.html" },
  { key: "rooms", label: "Rooms", icon: "💬", href: "rooms.html" },
  { key: "matching", label: "Matching", icon: "❤️", href: "matching.html" },
  { key: "events", label: "Campus Life", icon: "🎉", href: "campus-life.html" },
  { key: "messages", label: "Messages", icon: "✉️", href: "messages.html" },
  { key: "ai", label: "AI Studio", icon: "🤖", href: "ai-studio.html" },
];

const BOTTOM_NAV_ITEMS = [
  { key: "home", label: "Home", icon: "🏠", href: "home.html" },
  { key: "reels", label: "Reels", icon: "🎥", href: "reels.html" },
  { key: "tea", label: "Discover", icon: "🧭", href: "tea.html" },
  { key: "__fab", label: "", icon: "+", href: "home.html?compose=1" },
  { key: "communities", label: "Campus", icon: "🏫", href: "communities.html" },
  { key: "messages", label: "Chat", icon: "✉️", href: "messages.html" },
];

function renderNav() {
  const activeKey = document.body.dataset.page;
  const user = Auth.getUser();
  const isAdmin = user && (user.role === "admin" || user.role === "moderator");

  const topnav = document.createElement("div");
  topnav.className = "topnav";
  topnav.innerHTML = `
    <a href="home.html" class="brand"><span class="gradient-text">Campus</span>🎓</a>
    <div class="links desktop-only">
      ${NAV_ITEMS.map(item => `<a class="nav-link ${item.key === activeKey ? "active" : ""}" href="${item.href}">${item.icon} ${item.label}</a>`).join("")}
      ${isAdmin ? `<a class="nav-link ${activeKey === "admin" ? "active" : ""}" href="admin.html">🛡️ Admin</a>` : ""}
    </div>
    <div class="links">
      <a class="nav-link" href="profile.html">👤 ${user ? escapeHtml(user.username) : ""}</a>
      <button class="btn btn-ghost btn-sm" onclick="Auth.logout()">Logout</button>
    </div>
  `;
  document.body.prepend(topnav);

  const bottomnav = document.createElement("div");
  bottomnav.className = "bottomnav";
  bottomnav.innerHTML = BOTTOM_NAV_ITEMS.map(item => {
    if (item.key === "__fab") {
      return `<a href="${item.href}"><div class="fab">${item.icon}</div></a>`;
    }
    return `<a href="${item.href}" class="${item.key === activeKey ? "active" : ""}"><span>${item.icon}</span>${item.label}</a>`;
  }).join("");
  document.body.appendChild(bottomnav);
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.nav !== "false") {
    Auth.requireLogin();
    renderNav();
  }
});

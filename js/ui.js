// ui.js - shared page pieces: the public nav + footer (home page) and the
// app shell (sidebar + top bar) used by dashboard, scan and results.
//
// Home page:   renderNav("home"); renderFooter();
// App pages:   renderAppShell("dashboard" | "scan" | "results");

// ---------- small helpers ----------

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const svg = (paths, size = 20, width = 1.8) =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;

const ICONS = {
    figure:   svg(`<circle cx="12" cy="5" r="2.2"/><path d="M12 8v7M8 11l4-1 4 1M12 15l-3 6M12 15l3 6"/>`, 18),
    home:     svg(`<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-5h4v5"/>`),
    camera:   svg(`<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>`),
    chart:    svg(`<path d="M4 19V5M4 19h16M8 15l3-4 3 2 4-6"/>`),
    chevron:  svg(`<path d="m6 9 6 6 6-6"/>`, 16, 2),
    logout:   svg(`<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h11"/>`, 18),
    menu:     svg(`<path d="M4 7h16M4 12h16M4 17h16"/>`, 22, 2),
};

const brand = (href = "index.html") =>
    `<a href="${href}" class="brand"><span class="brand-mark">${ICONS.figure}</span>Mobility Tracker</a>`;

// who is logged in (login.js saves this after a successful login)
export function currentUser() {
    try { return localStorage.getItem("username"); } catch { return null; }
}

export function logout() {
    try {
        localStorage.removeItem("username");
        localStorage.removeItem("lastResult");
    } catch { /* storage blocked - nothing to clear */ }
    window.location.href = "login.html";
}

// "amanda@mobility.com" -> "amanda"
export function displayName(user = currentUser()) {
    if (!user) return "";
    const name = user.split("@")[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
}

// "amanda@mobility.com" -> "A"
function initials(user) {
    return (displayName(user).charAt(0) || "?").toUpperCase();
}

// ---------- public site: nav + footer ----------

export function renderNav(active = "home") {
    const el = document.getElementById("nav");
    if (!el) return;
    const user = currentUser();

    const actions = user
        ? `<a href="dashboard.html" class="btn btn-sm">Go to dashboard</a>`
        : `<a href="login.html" class="btn btn-sm btn-secondary">Log in</a>
           <a href="signup.html" class="btn btn-sm btn-accent">Sign up</a>`;

    el.className = "site-nav";
    el.innerHTML = `
        <div class="site-nav-inner">
            ${brand()}
            <button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false">${ICONS.menu}</button>
            <nav class="site-links" aria-label="Main">
                <a class="site-link" href="index.html#how">How it works</a>
                <a class="site-link" href="index.html#measure">What we measure</a>
                <a class="site-link" href="index.html#privacy">Privacy</a>
                <a class="site-link" href="index.html#faq">FAQ</a>
            </nav>
            <div class="site-actions">${actions}</div>
        </div>`;

    // mobile: the menu button opens/closes the links
    const toggle = el.querySelector(".nav-toggle");
    toggle.addEventListener("click", () => {
        const open = el.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
    });
    // close the mobile menu after tapping a link
    el.querySelectorAll(".site-link").forEach((a) =>
        a.addEventListener("click", () => {
            el.classList.remove("open");
            toggle.setAttribute("aria-expanded", "false");
        }));
}

export function renderFooter() {
    const el = document.getElementById("footer");
    if (!el) return;
    el.className = "site-footer";
    el.innerHTML = `
        <div class="footer-inner">
            <div class="footer-brand">
                ${brand()}
                <p>Camera-based mobility checks you can do at home. For general awareness only, not a medical device.</p>
            </div>
            <div class="footer-cols">
                <div>
                    <h4>Product</h4>
                    <a href="index.html#how">How it works</a>
                    <a href="index.html#measure">What we measure</a>
                    <a href="index.html#faq">FAQ</a>
                </div>
                <div>
                    <h4>Account</h4>
                    <a href="login.html">Log in</a>
                    <a href="signup.html">Sign up</a>
                    <a href="dashboard.html">Dashboard</a>
                </div>
            </div>
        </div>
        <div class="footer-legal">
            &copy; ${new Date().getFullYear()} Mobility Tracker &middot; Capstone project.
            Measurements are webcam estimates and cannot diagnose anything.
        </div>`;
}

// ---------- app pages: sidebar + top bar ----------

const APP_PAGES = {
    dashboard: { title: "Dashboard", href: "dashboard.html", icon: ICONS.home },
    scan:      { title: "New scan",  href: "scan.html",      icon: ICONS.camera },
    results:   { title: "Results",   href: "results.html",   icon: ICONS.chart },
};

export function renderAppShell(active = "dashboard") {
    const user = currentUser();

    // app pages are for logged-in users only
    if (!user) {
        window.location.replace("login.html");
        return;
    }

    // ----- sidebar -----
    const sidebar = document.getElementById("sidebar");
    if (sidebar) {
        const links = Object.entries(APP_PAGES).map(([key, p]) => `
            <a href="${p.href}" class="side-link ${key === active ? "active" : ""}" ${key === active ? 'aria-current="page"' : ""}>
                <span class="icon">${p.icon}</span>${p.title}
            </a>`).join("");

        sidebar.innerHTML = `
            <div class="side-brand">${brand("dashboard.html")}</div>
            <nav class="side-nav" aria-label="App">${links}</nav>
            <div class="side-tip">
                <strong>Scan tip</strong>
                <p>Use the same spot, lighting and clothing each time so your scans are easy to compare.</p>
            </div>`;
    }

    // ----- top bar -----
    const topbar = document.getElementById("topbar");
    if (topbar) {
        const showScanBtn = active !== "scan";
        topbar.innerHTML = `
            <span class="top-brand">${brand("dashboard.html")}</span>
            <h1 class="top-title">${APP_PAGES[active]?.title ?? ""}</h1>
            <div class="top-actions">
                ${showScanBtn ? `<a href="scan.html" class="btn btn-sm btn-accent top-scan">New scan</a>` : ""}
                <div class="dropdown">
                    <button class="dropdown-btn user-btn" type="button" aria-haspopup="true" aria-expanded="false">
                        <span class="avatar">${esc(initials(user))}</span>
                        <span class="user-name">${esc(displayName(user))}</span>
                        <span class="icon">${ICONS.chevron}</span>
                    </button>
                    <div class="menu right" hidden>
                        <div class="menu-item" style="cursor:default">
                            <span class="menu-text">
                                <span class="menu-label">${esc(displayName(user))}</span>
                                <span class="menu-desc">${esc(user)}</span>
                            </span>
                        </div>
                        <div class="menu-divider"></div>
                        <a href="dashboard.html" class="menu-item"><span class="icon">${ICONS.home}</span><span class="menu-label">Dashboard</span></a>
                        <a href="scan.html" class="menu-item"><span class="icon">${ICONS.camera}</span><span class="menu-label">New scan</span></a>
                        <div class="menu-divider"></div>
                        <button type="button" class="menu-item danger" data-logout>
                            <span class="icon">${ICONS.logout}</span><span class="menu-label">Log out</span>
                        </button>
                    </div>
                </div>
            </div>`;

        // user menu: open/close on click, close when clicking elsewhere or pressing Esc
        const btn = topbar.querySelector(".user-btn");
        const menu = topbar.querySelector(".menu");
        const setOpen = (open) => {
            menu.hidden = !open;
            btn.setAttribute("aria-expanded", String(open));
        };
        btn.addEventListener("click", (e) => { e.stopPropagation(); setOpen(menu.hidden); });
        document.addEventListener("click", (e) => { if (!menu.contains(e.target)) setOpen(false); });
        document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
        topbar.querySelector("[data-logout]").addEventListener("click", logout);
    }
}
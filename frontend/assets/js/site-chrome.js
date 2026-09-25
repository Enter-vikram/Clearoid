(function () {
  function isAuthPage() {
    var pathname = window.location.pathname || "";
    return pathname === "/pages/signin.html";
  }

  function getUser() {
    try {
      var raw = localStorage.getItem("clearoid_user");
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      return parsed && parsed.loggedIn ? parsed : null;
    } catch (e) {
      return null;
    }
  }

  function navLinksHtml(isLoggedIn, pathname) {
    var links = [
      { href: "/index.html", label: "Home" },
      { href: "/pages/upload.html", label: "Upload" },
      { href: "/pages/history.html", label: "History" },
      { href: "/pages/export.html", label: "Export" }
    ];

    if (isLoggedIn) {
      links.splice(1, 0, { href: "/pages/dashboard.html", label: "Dashboard" });
    }

    var html = links.map(function (link) {
      var active = pathname === link.href ? " text-white" : " text-white/90 hover:text-white";
      return '<a href="' + link.href + '" class="' + active + ' transition">' + link.label + "</a>";
    }).join("");

    if (isLoggedIn) {
      html += '<button id="logoutBtn" class="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-gray-200 transition">Logout</button>';
    } else if (pathname !== "/pages/signin.html") {
      html += '<a href="/pages/signin.html" class="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-gray-200 transition">Sign in</a>';
    }

    return html;
  }

  function renderNav() {
    if (isAuthPage()) return;
    var navContainer = document.querySelector("header .flex.items-center.gap-6");
    if (!navContainer) return;

    var pathname = window.location.pathname;
    var user = getUser();
    navContainer.innerHTML = navLinksHtml(!!user, pathname);

    var logout = document.getElementById("logoutBtn");
    if (logout) {
      logout.addEventListener("click", function () {
        localStorage.removeItem("clearoid_user");
        window.location.href = "/index.html";
      });
    }
  }

  function footerHtml() {
    var isDark = document.body.getAttribute("data-theme") !== "light";
    var headingClass = isDark ? "text-white" : "text-slate-900";
    var hoverClass = isDark ? "hover:text-white" : "hover:text-slate-900";
    var borderClass = isDark ? "border-gray-800" : "border-slate-200";
    
    return (
      '<div class="max-w-7xl mx-auto px-6 lg:px-8">' +
      '<div class="grid grid-cols-1 gap-10 mb-10 md:grid-cols-3">' +
      "<div>" +
      '<h3 class="' + headingClass + ' font-bold text-lg tracking-wider mb-6 uppercase">Product</h3>' +
      '<ul class="space-y-4 text-base">' +
      '<li><a href="/index.html" class="' + hoverClass + ' transition">Home</a></li>' +
      '<li><a href="/pages/dashboard.html" class="' + hoverClass + ' transition">Dashboard</a></li>' +
      '<li><a href="/pages/upload.html" class="' + hoverClass + ' transition">Upload</a></li>' +
      '<li><a href="/pages/history.html" class="' + hoverClass + ' transition">History</a></li>' +
      '<li><a href="/pages/export.html" class="' + hoverClass + ' transition">Export</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      '<h3 class="' + headingClass + ' font-bold text-lg tracking-wider mb-6 uppercase">Company</h3>' +
      '<ul class="space-y-4 text-base">' +
      '<li><a href="/pages/about.html" class="' + hoverClass + ' transition">About Clearoid</a></li>' +
      '<li><a href="/pages/contact.html" class="' + hoverClass + ' transition">Contact Us</a></li>' +
      '<li><a href="/pages/feedback.html" class="' + hoverClass + ' transition">Feedback</a></li>' +
      '<li><a href="/pages/privacy.html" class="' + hoverClass + ' transition">Privacy Policy</a></li>' +
      '<li><a href="/pages/terms.html" class="' + hoverClass + ' transition">Terms of Service</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      '<h3 class="' + headingClass + ' font-bold text-lg tracking-wider mb-6 uppercase">Social</h3>' +
      '<ul class="space-y-4 text-base">' +
      '<li><a href="https://github.com/yourusername/clearoid" target="_blank" rel="noreferrer" class="' + hoverClass + ' transition">GitHub</a></li>' +
      '<li><a href="https://linkedin.com/in/yourprofile" target="_blank" rel="noreferrer" class="' + hoverClass + ' transition">LinkedIn</a></li>' +
      '<li><a href="https://x.com/yourusername" target="_blank" rel="noreferrer" class="' + hoverClass + ' transition">X</a></li>' +
      '<li><a href="mailto:clearoid.ai@gmail.com" class="' + hoverClass + ' transition">Email</a></li>' +
      '<li><a href="https://clearoid.vercel.app" target="_blank" rel="noreferrer" class="' + hoverClass + ' transition">Share</a></li>' +
      "</ul>" +
      "</div>" +
      "</div>" +
      '<div class="' + borderClass + ' border-t pt-6 flex flex-col md:flex-row justify-between items-center text-sm gap-6">' +
      "<p>&copy; 2026 Clearoid</p>" +
      "<p>Version 1.0</p>" +
      "</div>" +
      "</div>"
    );
  }

  function appFooterHtml() {
    var isDark = document.body.getAttribute("data-theme") !== "light";
    var hoverClass = isDark ? "hover:text-white" : "hover:text-slate-900";
    
    return (
      '<div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">' +
      '<div class="flex flex-wrap items-center gap-4 text-sm">' +
      '<a href="/index.html" class="transition ' + hoverClass + '">Home</a>' +
      '<a href="/pages/history.html" class="transition ' + hoverClass + '">History</a>' +
      '<a href="/pages/export.html" class="transition ' + hoverClass + '">Export</a>' +
      '<a href="/pages/help.html" class="transition ' + hoverClass + '">Help</a>' +
      "</div>" +
      '<div class="flex flex-wrap items-center gap-4 text-sm">' +
      "<span>&copy; 2026 Clearoid</span>" +
      "<span>Version 1.0</span>" +
      "</div>" +
      "</div>"
    );
  }

  function renderFooter() {
    if (isAuthPage()) return;
    var footer = document.querySelector("footer");
    if (!footer) return;
    var isDark = document.body.getAttribute("data-theme") !== "light";
    var bgClass = isDark ? "bg-black" : "bg-white";
    var textClass = isDark ? "text-gray-400" : "text-slate-700";
    footer.className = bgClass + " " + textClass + " pt-12 pb-10";
    footer.innerHTML = footerHtml();
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderNav();
    renderFooter();
  });
  
  // Expose renderFooter globally for theme switching
  window.renderFooter = renderFooter;
})();

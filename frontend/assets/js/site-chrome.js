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
      { href: "/pages/export.html", label: "Export" },
    ];
    if (isLoggedIn) {
      links.splice(1, 0, { href: "/pages/dashboard.html", label: "Dashboard" });
    }

    var html = links
      .map(function (link) {
        var active = pathname === link.href ? " text-white" : " text-white hover:text-gray-300";
        return (
          '<a href="' + link.href + '" class="' + active + ' transition">' + link.label + "</a>"
        );
      })
      .join("");

    if (isLoggedIn) {
      html +=
        '<button id="logoutBtn" class="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-gray-200 transition">Logout</button>';
    } else if (pathname !== "/pages/signin.html") {
      html +=
        '<a href="/pages/signin.html" class="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-gray-200 transition">Sign in</a>';
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
    return (
      '<div class="max-w-7xl mx-auto px-6 lg:px-8">' +
      '<div class="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">' +
      "<div>" +
      '<h3 class="text-white font-bold text-lg tracking-wider mb-5 uppercase">PRODUCT</h3>' +
      '<ul class="space-y-3 text-base">' +
      '<li><a href="/index.html" class="hover:text-white transition">Home</a></li>' +
      '<li><a href="/pages/dashboard.html" class="hover:text-white transition">Dashboard</a></li>' +
      '<li><a href="/pages/upload.html" class="hover:text-white transition">Upload</a></li>' +
      '<li><a href="/pages/history.html" class="hover:text-white transition">History</a></li>' +
      '<li><a href="/pages/export.html" class="hover:text-white transition">Export</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      '<h3 class="text-white font-bold text-lg tracking-wider mb-5 uppercase">COMPANY</h3>' +
      '<ul class="space-y-3 text-base">' +
      '<li><a href="/pages/about.html" class="hover:text-white transition">About Clearoid</a></li>' +
      '<li><a href="/pages/contact.html" class="hover:text-white transition">Contact Us</a></li>' +
      '<li><a href="/pages/feedback.html" class="hover:text-white transition">Feedback</a></li>' +
      '<li><a href="/pages/privacy.html" class="hover:text-white transition">Privacy Policy</a></li>' +
      '<li><a href="/pages/terms.html" class="hover:text-white transition">Terms of Service</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      '<h3 class="text-white font-bold text-lg tracking-wider mb-5 uppercase">SOCIAL</h3>' +
      '<ul class="space-y-3 text-base">' +
      '<li><a href="https://github.com/yourusername/clearoid" target="_blank" class="hover:text-white transition">GitHub</a></li>' +
      '<li><a href="https://linkedin.com/in/yourprofile" target="_blank" class="hover:text-white transition">LinkedIn</a></li>' +
      '<li><a href="https://x.com/yourusername" target="_blank" class="hover:text-white transition">X</a></li>' +
      '<li><a href="mailto:clearoid.ai@gmail.com" class="hover:text-white transition">Email</a></li>' +
      '<li><a href="https://clearoid.vercel.app" target="_blank" class="hover:text-white transition">Share</a></li>' +
      "</ul>" +
      "</div>" +
      "</div>" +
      '<div class="border-t border-gray-800 pt-6 flex flex-col md:flex-row justify-between items-center text-sm gap-6">' +
      "<p>© 2026 Clearoid</p>" +
      "<p>Version 1.0</p>" +
      "</div>" +
      "</div>"
    );
  }

  function renderFooter() {
    if (isAuthPage()) return;
    var footer = document.querySelector("footer");
    if (!footer) return;
    footer.className = "bg-black text-gray-400 pt-12 pb-10";
    footer.innerHTML = footerHtml();
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderNav();
    renderFooter();
  });
})();

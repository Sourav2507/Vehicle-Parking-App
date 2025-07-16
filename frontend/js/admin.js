new Vue({
  el: "#admin-navbar",
  delimiters: ["${", "}"],
  data: {
    logo: "/static/images/logo_2.png",
    navLinks: [
      { label: "Dashboard", url: "/admin/dashboard", iconClass: "bi bi-house-door" },
      { label: "Parking Slots", url: "/admin/manage-slots", iconClass: "bi bi-calendar-event" },
      { label: "Users", url: "/admin/manage-users", iconClass: "bi bi-people" },
      { label: "Bookings", url: "/admin/bookings", iconClass: "bi bi-clock-history" },
      { label: "Reports", url: "/admin/reports", iconClass: "bi bi-bar-chart" },
      { label: "Queries", url: "/admin/queries", iconClass: "bi bi-question-circle" },
      { label: "Logout", url: "/logout", iconClass: "bi bi-box-arrow-right" }
    ]
  }
});

new Vue({
  el: "#dashboard_app",
  delimiters: ["${", "}"],
  data: {
    loading: true,
    cards: [],
    recentActivities: [],
    revenueData: [],
    bookingsByMonth: [],
    bookingsByLot: {}, // renamed for clarity
    bookingStatus: {},
    revenueStatus: {},
    navLinks: [
      {
        label: "Dashboard",
        url: "/admin/dashboard",
        iconClass: "bi bi-speedometer2",
      },
      { label: "Users", url: "/admin/users", iconClass: "bi bi-people" },
      {
        label: "Bookings",
        url: "/admin/bookings",
        iconClass: "bi bi-calendar-check",
      },
      {
        label: "Revenue",
        url: "/admin/revenue",
        iconClass: "bi bi-currency-rupee",
      },
    ],
    logo: "/static/images/logo_2.png",
  },
  mounted() {
    fetch("/admin/dashboard_data")
      .then((res) => res.json())
      .then((data) => {
        this.cards = data.cards.map((card) => {
          const iconMap = {
            "Total Users": "bi bi-people",
            "Total Bookings": "bi bi-calendar-check",
            "Active Parking Lots": "bi bi-pin-map",
            "Total Revenue": "bi bi-currency-rupee",
          };
          return {
            ...card,
            iconClass: iconMap[card.label] || "bi bi-info-circle",
          };
        });
        this.recentActivities = data.activities || [];
        this.revenueData = data.revenue || Array(12).fill(0);
        this.bookingsByMonth = data.bookings_over_time || Array(12).fill(0);
        this.bookingsByLot = data.bookings_by_slot || {}; // lot name
        this.bookingStatus = data.booking_status || {};
        this.revenueStatus = data.revenue_status || {};

        this.loading = false;
        this.$nextTick(() => {
          this.drawRevenueChart();
          this.drawBookingsOverTimeChart();
          this.drawBookingsByLotChart(); // updated method name
          this.drawBookingStatusChart();
          this.drawRevenueStatusChart();
        });
      })
      .catch((err) => {
        alert("Failed to load dashboard: " + err.message);
        this.loading = false;
      });
  },
  methods: {
    drawRevenueChart() {
      const ctx = document.getElementById("annualRevenueChart");
      if (!ctx) return;

      new Chart(ctx, {
        type: "line",
        data: {
          labels: [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
          ],
          datasets: [
            {
              label: "Revenue (₹)",
              data: this.revenueData,
              borderColor: "#0d6efd",
              backgroundColor: "rgba(13,110,253,0.1)",
              fill: true,
              tension: 0,
              pointRadius: 4,
              pointHoverRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });
    },
    drawBookingsOverTimeChart() {
      const ctx = document.getElementById("bookingsOverTimeChart");
      if (!ctx) return;

      new Chart(ctx, {
        type: "line",
        data: {
          labels: [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
          ],
          datasets: [
            {
              label: "Bookings",
              data: this.bookingsByMonth,
              borderColor: "#198754",
              backgroundColor: "rgba(25,135,84,0.1)",
              fill: true,
              tension: 0,
              pointRadius: 4,
              pointHoverRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });
    },
    drawBookingsByLotChart() {
      const ctx = document.getElementById("bookingsBySlotChart"); // ID stays same
      if (!ctx || !this.bookingsByLot) return;

      const labels = Object.keys(this.bookingsByLot);
      const counts = Object.values(this.bookingsByLot);

      new Chart(ctx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: counts,
              backgroundColor: [
                "#0d6efd", "#6610f2", "#6f42c1",
                "#198754", "#fd7e14", "#dc3545", "#20c997",
              ],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const label = context.label || "";
                  const value = context.raw || 0;
                  return `${label}: ${value} bookings`;
                },
              },
            },
          },
        },
      });
    },
    drawBookingStatusChart() {
      const ctx = document.getElementById("bookingStatusChart");
      if (!ctx) return;

      const labels = Object.keys(this.bookingStatus);
      const data = Object.values(this.bookingStatus);

      new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Bookings",
              data,
              backgroundColor: "#0d6efd",
              borderRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: false },
          },
          scales: {
            x: {
              title: { display: true, text: "Status" },
            },
            y: {
              beginAtZero: true,
              title: { display: true, text: "Count" },
            },
          },
        },
      });
    },
    drawRevenueStatusChart() {
      const ctx = document.getElementById("revenueStatusChart");
      if (!ctx || !this.revenueStatus) return;

      const labels = Object.keys(this.revenueStatus);
      const values = Object.values(this.revenueStatus);

      new Chart(ctx, {
        type: "pie",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: ["#198754", "#ffc107"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });
    },
  },
});

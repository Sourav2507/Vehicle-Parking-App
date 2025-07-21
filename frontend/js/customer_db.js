new Vue({
  el: "#app",
  delimiters: ["${", "}"],
  data: {
    user: {},
    bookings: [],
    payments: [],
    notifications: [],
    loading: true,
    booking_status: {},
    payment_status: {},
    total_expenditure: 0,
    monthly_bookings: [],
  },
  mounted() {
    fetch("/user/dashboard_data")
      .then((res) => res.json())
      .then((data) => {
        this.user = data.user;
        this.bookings = data.bookings || [];
        this.payments = data.payments || [];
        this.notifications = data.notifications || [];
        this.booking_status = data.booking_status || {};
        this.payment_status = data.payment_status || {};
        this.total_expenditure = data.total_expenditure || 0;
        this.monthly_bookings =
          Array.isArray(data.monthly_bookings) &&
          data.monthly_bookings.length === 12
            ? data.monthly_bookings
            : Array(12).fill(0);

        this.loading = false;
        this.$nextTick(() => {
          this.drawCharts();
        });
      })
      .catch((err) => {
        alert("Failed to load dashboard: " + err.message);
        this.loading = false;
        this.booking_status = {};
        this.payment_status = {};
        this.total_expenditure = 0;
        this.monthly_bookings = Array(12).fill(0);

        this.$nextTick(() => {
          this.drawCharts();
        });
      });
  },
  methods: {
    drawCharts() {
      this.drawBookingChart();
      this.drawPaymentChart();
      this.drawMonthlyBookingChart();
    },
    drawBookingChart() {
      const ctx = document.getElementById("bookingStatusChart");
      if (!ctx) return;

      const actualLabels = [
        "Requested",
        "Accepted",
        "Confirmed",
        "Occupied",
        "Cancelled",
        "Rejected",
        "Accomplished",
      ];

      const actualCounts = actualLabels.map(
        (label) => this.booking_status[label] || 0
      );

      const labels = ["", ...actualLabels, ""];
      const counts = [null, ...actualCounts, null];

      new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Bookings",
              data: counts,
              borderColor: "#0d6efd",
              backgroundColor: "#0d6efd44",
              fill: true,
              tension: 0,
              pointRadius: 5,
              pointHoverRadius: 7,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: false },
            legend: { display: false },
          },
          scales: {
            x: {
              ticks: {
                callback: (val, index) =>
                  labels[index] === "" ? "" : labels[index],
              },
            },
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    },
    drawPaymentChart() {
      const ctx = document.getElementById("paymentStatusChart");
      if (!ctx) return;

      const paid = this.payment_status["paid"] || 0;
      const unpaid =
        (this.payment_status["unpaid"] || 0) +
        (this.payment_status["expired"] || 0);

      new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: [
            `Unpaid (₹${unpaid.toLocaleString()})`,
            `Paid (₹${paid.toLocaleString()})`,
          ],
          datasets: [
            {
              data: [unpaid, paid],
              backgroundColor: ["#dc3545", "#198754"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: false },
            legend: { position: "bottom" },
          },
        },
      });
    },
    drawMonthlyBookingChart() {
      const ctx = document.getElementById("monthlyBookingsChart");
      if (!ctx) return;

      const months = [
        "",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "",
      ];

      const counts = [null, ...this.monthly_bookings, null];

      new Chart(ctx, {
        type: "line",
        data: {
          labels: months,
          datasets: [
            {
              label: "Bookings",
              data: counts,
              fill: true,
              backgroundColor: "rgba(13, 110, 253, 0.2)",
              borderColor: "#0d6efd",
              tension: 0,
              pointRadius: 5,
              pointHoverRadius: 7,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: false },
            legend: { display: false },
          },
          scales: {
            x: {
              ticks: {
                callback: (val, index) =>
                  months[index] === "" ? "" : months[index],
              },
            },
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    },
    statusClass(status) {
      switch (status.toLowerCase()) {
        case "rejected":
          return "text-danger";
        case "accomplished":
          return "text-success";
        case "cancelled":
          return "text-muted";
        case "requested":
          return "text-primary";
        case "occupied":
          return "text-warning";
        default:
          return "text-secondary";
      }
    },
  },
});

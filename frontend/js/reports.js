new Vue({
  el: "#admin-reports-app",
  delimiters: ["${", "}"],
  mounted() {
    this.initCharts();
  },
  methods: {
    initCharts() {
      // Bookings Over Time (Line Chart)
      new Chart(document.getElementById("bookingsOverTimeChart"), {
        type: "line",
        data: {
          labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
          datasets: [{
            label: "Bookings",
            data: [20, 35, 40, 50, 60, 45, 70],
            borderColor: "#007bff",
            backgroundColor: "rgba(0, 123, 255, 0.1)",
            fill: true,
            tension: 0
          }]
        },
        options: { responsive: true }
      });

      // Bookings by Slot (Bar Chart)
      new Chart(document.getElementById("bookingsBySlotChart"), {
        type: "bar",
        data: {
          labels: ["Lot A", "Lot B", "Garage C", "Zone D"],
          datasets: [{
            label: "Bookings",
            data: [80, 55, 60, 30],
            backgroundColor: "#28a745"
          }]
        },
        options: { responsive: true }
      });

      // Booking Status Pie Chart
      new Chart(document.getElementById("statusDistributionChart"), {
        type: "pie",
        data: {
          labels: ["Requested", "Accepted", "Confirmed", "Cancelled", "Occupied", "Released"],
          datasets: [{
            data: [10, 15, 30, 5, 20, 10],
            backgroundColor: ["#ffc107", "#17a2b8", "#28a745", "#dc3545", "#6f42c1", "#20c997"]
          }]
        },
        options: { responsive: true }
      });

      // Revenue Status Pie Chart
      new Chart(document.getElementById("revenueStatusChart"), {
        type: "pie",
        data: {
          labels: ["Received", "Pending"],
          datasets: [{
            data: [8000, 2000],
            backgroundColor: ["#28a745", "#ffc107"]
          }]
        },
        options: { responsive: true }
      });

      // Annual Revenue Line Chart
      new Chart(document.getElementById("annualRevenueChart"), {
        type: "line",
        data: {
          labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
          datasets: [{
            label: "Revenue ($)",
            data: [1000, 1200, 1300, 1500, 1700, 1600, 1800, 2000],
            borderColor: "#6610f2",
            backgroundColor: "rgba(102, 16, 242, 0.1)",
            fill: true,
            tension: 0
          }]
        },
        options: { responsive: true }
      });
    }
  }
});

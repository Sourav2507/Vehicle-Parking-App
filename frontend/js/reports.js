new Vue({
  el: "#admin-reports-app",
  delimiters: ["${", "}"],
  data: {
    trend: [],
    lots_analytics: [],
    lots_table: [],
    status_table: [],
    users_table: [],
    loading: true,
  },
  methods: {
    exportCSV(dataArray, columns, filename) {
      // columns: [{header: "Col Name", key: "data_key"}, ...]
      let csv =
        columns.map((col) => `"${col.header}"`).join(",") +
        "\n" +
        dataArray
          .map((row) =>
            columns
              .map(
                (col) =>
                  `"${(row[col.key] !== undefined ? row[col.key] : "")
                    .toString()
                    .replace(/"/g, '""')}"`
              )
              .join(",")
          )
          .join("\n");

      // Create and trigger download
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    exportTrendCSV() {
      this.exportCSV(
        this.trend,
        [
          { header: "Month and Year", key: "month_and_year" },
          { header: "Bookings", key: "bookings" },
          { header: "Accomplishment Rate", key: "accomplishment_rate" },
          { header: "Revenue Generated", key: "revenue" },
          { header: "Top Parking Spot", key: "top_parking_spot" },
        ],
        "monthly_bookings_trend.csv"
      );
    },

    exportLotsAnalyticsCSV() {
      this.exportCSV(
        this.lots_analytics,
        [
          { header: "Name", key: "name" },
          { header: "Capacity", key: "capacity" },
          { header: "Location", key: "location" },
          { header: "Bookings (till now)", key: "bookings_total" },
          { header: "Accomplishment Rate", key: "accomplishment_rate" },
          { header: "Cancellation Rate", key: "cancellation_rate" },
        ],
        "bookings_analytics.csv"
      );
    },

    exportLotsTableCSV() {
      this.exportCSV(
        this.lots_table,
        [
          { header: "Parking Lot", key: "lot" },
          { header: "Capacity", key: "capacity" },
          { header: "Price/Hour", key: "price" },
          { header: "Total Revenue", key: "total_revenue" },
        ],
        "parking_lots.csv"
      );
    },

    exportStatusTableCSV() {
      this.exportCSV(
        this.status_table,
        [
          { header: "Parking Lot", key: "lot" },
          { header: "Capacity", key: "capacity" },
          { header: "Occupied", key: "occupied" },
        ],
        "current_parking_lot_status.csv"
      );
    },

    exportUsersTableCSV() {
      this.exportCSV(
        this.users_table,
        [
          { header: "Name", key: "name" },
          { header: "Email Id", key: "email" },
          { header: "Address", key: "address" },
          { header: "Bookings Availed", key: "bookings_availed" },
          { header: "Bookings Accomplished", key: "bookings_accomplished" },
          { header: "Booking Cancelled", key: "bookings_cancelled" },
          { header: "Revenue Spent", key: "revenue_spent" },
          { header: "Revenue Unpaid", key: "revenue_unpaid" },
        ],
        "users_analytics.csv"
      );
    },
    downloadEntireReport() {
    const fullReport = {
      trend: this.trend,
      lots_analytics: this.lots_analytics,
      lots_table: this.lots_table,
      status_table: this.status_table,
      users_table: this.users_table
    };

    fetch("/admin/generate_report_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fullReport)
    })
    .then(res => res.json())
    .then(data => {
      setTimeout(() => {
        window.location = "/admin/fetch_report_pdf";
      }, 5000);
    });
  }
  },
  mounted() {
    console.log("Mounted Successfully !");
    fetch("/admin/reports_data")
      .then((res) => res.json())
      .then((data) => {
        this.trend = data.trend;
        this.lots_analytics = data.lots_analytics;
        this.lots_table = data.lots_table;
        this.status_table = data.status_table;
        this.users_table = data.users_table;
        this.loading = false;
      });
  },
});

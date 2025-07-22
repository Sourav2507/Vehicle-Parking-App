new Vue({
  el: "#bookingApp",
  delimiters: ["${", "}"],
  data: {
    activeTab: "upcoming",
    upcoming: [],
    past: [],
    cancelled: [],
    loading: true,
    error: null,
  },
  mounted() {
    fetch("/user/my_bookings", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          this.upcoming = data.upcoming.reverse();
          this.past = data.past.reverse();
          this.cancelled = data.cancelled.reverse();
        } else {
          this.error = data.message;
        }
        this.loading = false;
      })
      .catch((err) => {
        this.error = "Error fetching bookings.";
        this.loading = false;
      });
  },
  computed: {
    filteredBookings() {
      if (this.activeTab === "upcoming") return this.upcoming;
      if (this.activeTab === "past") return this.past;
      return this.cancelled;
    },
  },
  methods: {
    formatDate(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleDateString() + " " + date.toLocaleTimeString();
    },
    formatTime(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleTimeString();
    },
    isWithinBookingTime(booking) {
      const now = new Date();
      const start = new Date(booking.start_time);
      const end = new Date(booking.end_time);
      return now >= start && now <= end;
    },
    cancelBooking(booking) {
      if (!confirm(`Are you sure you want to cancel Booking #${booking.id}?`))
        return;

      fetch(`/user/cancel_existing_booking/${booking.id}`, {
        method: "POST",
        credentials: "include",
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            const list = this.upcoming;
            const index = list.findIndex((b) => b.id === booking.id);
            if (index !== -1) list.splice(index, 1);
          } else {
            alert(data.message || "Failed to cancel booking.");
          }
        });
    },
    payForBooking(booking) {
      window.location.href = "/user/payments";
    },
    occupySpot(booking) {
      if (!this.isWithinBookingTime(booking)) {
        alert("It's not the right time to occupy the spot.");
        return;
      }

      fetch(`/user/occupy_spot/${booking.id}`, {
        method: "POST",
        credentials: "include",
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Spot occupied successfully!");
            booking.status = "Occupied";
          } else {
            alert(data.message || "Failed to occupy spot.");
          }
        })
        .catch((err) => {
          console.error(err);
          alert("Error occupying spot.");
        });
    },
    releaseSpot(booking) {
      fetch(`/user/release_spot/${booking.id}`, {
        method: "POST",
        credentials: "include",
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Spot released successfully!");
            window.location.reload(); // 🔁 Reload to move from Upcoming → Past
          } else {
            alert(data.message || "Failed to release spot.");
          }
        })
        .catch((err) => {
          console.error(err);
          alert("Error releasing spot.");
        });
    },
  },
});

new Vue({
  el: "#admin-bookings-app",
  delimiters: ["${", "}"],
  data: {
    bookings: [],
    visibleStatuses: [
      "Requested", "Accepted", "Confirmed", "Rejected",
      "Cancelled", "Occupied", "Accomplished"
    ],
    allStatuses: [
      "Requested", "Accepted", "Confirmed", "Rejected",
      "Cancelled", "Occupied", "Accomplished"
    ],
    statusIcons: {
      "Requested": "bi bi-hourglass-split",
      "Accepted": "bi bi-person-check-fill",
      "Confirmed": "bi bi-cash-stack",
      "Rejected": "bi bi-x-octagon-fill",
      "Cancelled": "bi bi-slash-circle-fill",
      "Occupied": "bi bi-car-front-fill",
      "Accomplished": "bi bi-check2-circle"
    }
  },
  computed: {
    groupedBookings() {
      const grouped = {};
      this.allStatuses.forEach(status => {
        grouped[status] = this.bookings.filter(b => b.status === status);
      });
      return grouped;
    }
  },
  mounted() {
    this.fetchBookings();
  },
  methods: {
    fetchBookings() {
      fetch("/admin/bookings_data")
        .then(res => res.json())
        .then(data => {
          this.bookings = data;
        })
        .catch(err => console.error("Error fetching bookings:", err));
    },
    acceptBooking(booking) {
      if (!confirm(`Accept booking #${booking.id}?`)) return;
      fetch(`/admin/accept_booking/${booking.id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            booking.status = "Accepted";
            alert("Booking accepted.");
          } else alert(data.message || "Failed.");
        });
    },
    rejectBooking(booking) {
      if (!confirm(`Reject booking #${booking.id}?`)) return;
      fetch(`/admin/reject_booking/${booking.id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            booking.status = "Rejected";
            alert("Booking rejected.");
          } else alert(data.message || "Failed.");
        });
    },
    confirmBooking(booking) {
      if (!confirm(`Mark booking #${booking.id} as paid and confirmed?`)) return;
      fetch(`/admin/confirm_booking/${booking.id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            booking.status = "Confirmed";
            alert("Booking marked as confirmed & paid.");
          } else alert(data.message || "Failed.");
        });
    }
  }
});

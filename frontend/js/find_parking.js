new Vue({
  el: "#find_parking_app",
  delimiters: ["${", "}"],
  data: {
    parkingLots: [],
    searchQuery: "",
    minNow: new Date().toISOString().slice(0, 16),
  },
  methods: {
    goToBookings() {
      window.location.href = "/user/bookings";
    },
    goToPayments() {
      window.location.href = "/user/payments";
    },
    bookspot(lot) {
      if (!lot.selectedStartTime || !lot.selectedEndTime) {
        alert("Please select both start and end times.");
        return;
      }

      const now = new Date();
      const start = new Date(lot.selectedStartTime);
      const end = new Date(lot.selectedEndTime);

      if (start <= now) {
        alert("Start time must be in the future.");
        return;
      }

      if (end <= start) {
        alert("End time must be after the start time.");
        return;
      }

      const diffHours = (end - start) / (1000 * 60 * 60);
      if (diffHours < 1) {
        alert("Minimum booking duration is 1 hour.");
        return;
      }

      const payload = {
        lot_id: lot.id,
        start_time: lot.selectedStartTime,
        end_time: lot.selectedEndTime,
      };

      fetch("/user/book_spot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Booking confirmed!");
            lot.available -= 1;
            lot.requested = true;
            lot.status = "Requested";
            lot.start_time = lot.selectedStartTime;
            lot.end_time = lot.selectedEndTime;
          } else {
            alert(data.message || "Booking failed.");
          }
        })
        .catch((err) => {
          console.error("Error booking:", err);
          alert("Something went wrong.");
        });
    },

    cancelBooking(lot) {
      if (!confirm(`Cancel your booking at "${lot.name}"?`)) return;

      fetch("/user/cancel_booking", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ lot_id: lot.id }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Booking canceled.");
            lot.available += 1;
            lot.requested = false;
            lot.status = null;
            lot.start_time = null;
            lot.end_time = null;
            lot.selectedStartTime = "";
            lot.selectedEndTime = "";
          } else {
            alert(data.message || "Cancellation failed.");
          }
        })
        .catch((err) => {
          console.error("Error cancelling booking:", err);
          alert("Something went wrong.");
        });
    },

    calculatePrice(lot) {
      const start = new Date(lot.selectedStartTime);
      const end = new Date(lot.selectedEndTime);
      const hours = Math.ceil((end - start) / (1000 * 60 * 60));
      return hours * lot.price;
    },
  },

  computed: {
    filteredLots() {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return this.parkingLots;
      return this.parkingLots.filter(
        (lot) =>
          lot.address.toLowerCase().includes(query) ||
          lot.name.toLowerCase().includes(query)
      );
    },
  },

  mounted() {
    fetch("/user/find_parking_data")
      .then((res) => res.json())
      .then((data) => {
        this.parkingLots = data.map((lot) => ({
          ...lot,
          available: Number(lot.capacity) - Number(lot.occupied),
          requested: lot.requested || false,
          status: lot.status || null,
          selectedStartTime: "",
          selectedEndTime: "",
          start_time: lot.start_time || null,
          end_time: lot.end_time || null,
        }));
      })
      .catch((err) => console.error("Error loading parking data:", err));
  },
});

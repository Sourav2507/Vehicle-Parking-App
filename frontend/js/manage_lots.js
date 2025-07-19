new Vue({
  el: "#manage-lots-app",
  delimiters: ["${", "}"],
  data: {
    lots: [],
    showAddForm: false,
    newLot: { name: "", address: "", capacity: null, price: null },
    selectedLotId: null,
    selectedLotBookings: [],
  },
  mounted() {
    this.fetchLots();
  },
  methods: {
    fetchLots() {
      fetch("/admin/manage-lots/data")
        .then((res) => res.json())
        .then((data) => {
          this.lots = data;
        })
        .catch(() => alert("Failed to load parking lots."));
    },
    toggleActive(lot) {
      const newActiveStatus = !lot.active;

      if (!newActiveStatus && lot.occupied > 0) {
        alert(
          `Lot #00${lot.id} cannot be marked unavailable. ${lot.occupied} slot(s) are currently occupied.`
        );
        return;
      }

      fetch(`/admin/manage-lots/toggle-active/${lot.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: newActiveStatus }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            lot.active = data.active;
            alert(
              `Lot #00${lot.id} is now ${
                lot.active ? "available" : "unavailable"
              }`
            );
          } else {
            alert("Failed to update lot status: " + data.error);
          }
        })
        .catch(() => alert("Error updating lot status."));
    },
    addLot() {
      if (
        !this.newLot.name.trim() ||
        !this.newLot.address.trim() ||
        !this.newLot.capacity ||
        !this.newLot.price
      ) {
        return alert("Please fill in all fields.");
      }

      fetch("/admin/manage-lots/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.newLot),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Parking lot added successfully.");
            this.cancelAdd();
            this.fetchLots();
          } else {
            alert("Failed to add lot: " + data.error);
          }
        })
        .catch(() => alert("Error adding parking lot."));
    },
    cancelAdd() {
      this.showAddForm = false;
      this.resetNewLot();
    },
    resetNewLot() {
      this.newLot = {
        name: "",
        address: "",
        capacity: null,
        price: null,
      };
    },
    getBookingsForLot(lotId) {
      this.selectedLotId = lotId;
      fetch(`/admin/manage-lots/bookings/${lotId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            this.selectedLotBookings = data.bookings;
          } else {
            alert("Failed to load bookings: " + data.error);
          }
        })
        .catch(() => alert("Error fetching booking data."));
    },
  },
});

new Vue({
  el: "#manage-slots-app",
  delimiters: ["${", "}"],
  data: {
    slots: [],
    showAddForm: false,
    newSlot: {
      name: "",
      address: "",
      capacity: null,
      price: null,
    },
  },
  mounted() {
    this.fetchSlots();
  },
  methods: {
    fetchSlots() {
      fetch("/admin/manage-slots/data")
        .then((res) => res.json())
        .then((data) => {
          this.slots = data;
        })
        .catch(() => alert("Failed to load slots."));
    },
    toggleActive(slot) {
      const newActiveStatus = !slot.active;
      fetch(`/admin/manage-slots/toggle-active/${slot.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: newActiveStatus }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            slot.active = data.active;
            alert(`Slot #00${slot.id} is now ${slot.active ? "available" : "unavailable"}`);
          } else {
            alert("Failed to update slot status: " + data.error);
          }
        })
        .catch(() => alert("Error updating slot status."));
    },
    addSlot() {
      if (
        !this.newSlot.name.trim() ||
        !this.newSlot.address.trim() ||
        !this.newSlot.capacity ||
        !this.newSlot.price
      ) {
        return alert("Please fill in all fields.");
      }

      fetch("/admin/manage-slots/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.newSlot),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            alert("Slot added successfully.");
            this.cancelAdd();
            this.fetchSlots();
          } else {
            alert("Failed to add slot: " + data.error);
          }
        })
        .catch(() => alert("Error adding slot."));
    },
    cancelAdd() {
      this.showAddForm = false;
      this.resetNewSlot();
    },
    resetNewSlot() {
      this.newSlot = {
        name: "",
        address: "",
        capacity: null,
        price: null,
      };
    },
  },
});

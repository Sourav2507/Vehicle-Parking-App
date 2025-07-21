new Vue({
  el: "#paymentsApp",
  delimiters: ["${", "}"],
  data: {
    paymentHistory: [],
    unpaidBookings: []
  },
  mounted() {
    this.fetchPayments();
  },
  methods: {
    fetchPayments() {
      fetch("/user/payments-data")
        .then(res => res.json())
        .then(data => {
          this.paymentHistory = data.history.reverse() || [];
          this.unpaidBookings = data.unpaid.reverse() || [];
        })
        .catch(err => {
          console.error("Error loading payment data:", err);
          alert("Failed to load payment data.");
        });
    },
    payNow(paymentId) {
      if (!confirm("Proceed to mark this booking as paid?")) return;

      fetch(`/user/pay/${paymentId}`, {
        method: "POST"
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("Payment successful!");
            this.fetchPayments();
          } else {
            alert("Payment failed: " + (data.message || ""));
          }
        })
        .catch(err => {
          alert("Error processing payment.");
          console.error(err);
        });
    }
  }
});

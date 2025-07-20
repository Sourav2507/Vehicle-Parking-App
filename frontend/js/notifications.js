new Vue({
  el: "#notificationsApp",
  delimiters: ["${", "}"], // ✅ Using ${ } now
  data: {
    notifications: [],
  },
  mounted() {
    this.fetchNotifications();
  },
  methods: {
    fetchNotifications() {
      fetch("/user/notifications/data")
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            this.notifications = data.notifications;
          } else {
            console.error(data.message || "Failed to load notifications.");
          }
        })
        .catch((err) => {
          console.error("Error fetching notifications:", err);
        });
    },
  },
});

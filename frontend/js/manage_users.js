new Vue({
  el: "#manage-users-app",
  delimiters: ["${", "}"],
  data: {
    users: [],
    loading: true
  },
  mounted() {
    this.fetchUsers();
  },
  methods: {
    fetchUsers() {
      fetch("/admin/users_data")
        .then(res => {
          if (!res.ok) throw new Error("Failed to fetch users");
          return res.json();
        })
        .then(data => {
          this.users = data;
          this.loading = false;
        })
        .catch(err => {
          alert(err.message);
          this.loading = false;
        });
    },
    deleteUser(id) {
      if (!confirm(`Are you sure you want to delete user #${id}?`)) return;

      fetch(`/admin/delete_user/${id}`, { method: "DELETE" })
        .then(res => {
          if (!res.ok) throw new Error("Failed to delete user");
          return res.json();
        })
        .then(data => {
          if (data.success) {
            alert("User deleted successfully.");
            this.users = this.users.filter(u => u.id !== id);
          } else {
            alert("Failed to delete user.");
          }
        })
        .catch(() => alert("Error deleting user."));
    },
    toggleActive(user) {
      fetch(`/admin/toggle_user_active/${user.id}`, { method: "POST" })
        .then(res => {
          if (!res.ok) throw new Error("Failed to toggle user status");
          return res.json();
        })
        .then(data => {
          if (data.success) {
            user.active = data.active;
            alert(`User is now ${user.active ? "Active" : "Blocked"}.`);
          } else {
            alert("Failed to toggle user status.");
          }
        })
        .catch(() => alert("Error toggling user status."));
    }
  }
});

new Vue({
  el: "#queries_app",
  delimiters: ["${", "}"],
  data: {
    queries: [],
    loading: true
  },
  mounted() {
    console.log("App mounted")
    fetch("/admin/queries_data")
      .then(res => res.json())
      .then(data => {
        this.queries = data.map(q => ({ ...q, replyText: "" }));
        this.loading = false;
      })
      .catch(err => {
        alert("Failed to load queries: " + err.message);
        this.loading = false;
      });
  },
  methods: {
    sendReply(query) {
      const reply = query.replyText.trim();
      if (!reply) return alert("Reply cannot be empty.");

      fetch(`/admin/reply_query/${query.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reply })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("Reply sent as notification.");
            query.replyText = "";
          } else {
            alert("Failed to send reply.");
          }
        })
        .catch(() => alert("Error sending reply."));
    }
  }
});

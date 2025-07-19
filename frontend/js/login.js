const app = new Vue({
  el: "#app",
  delimiters: ["${", "}"],  // <-- Required because you're using ${ } in HTML
  data: {
    form: {
      username: "",
      password: "",
    },
    errorMessage: "",
  },
  methods: {
    handleLogin: function () {
      if (!this.form.username || !this.form.password) {
        this.errorMessage = "Username and Password are required.";
        return;
      }

      this.errorMessage = "";

      fetch("/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(this.form),
      })
        .then((response) =>
          response.json().then((data) => {
            if (!response.ok) {
              throw new Error(data.message || "Login failed.");
            }
            return data;
          })
        )
        .then((data) => {
          window.location.href = data.redirect;
        })
        .catch((error) => {
          this.errorMessage = error.message;
        });
    },
  },
});

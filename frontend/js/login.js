const app = new Vue({
  el: '#app',
  delimiters: ['${', '}'],
  data: {
    form: {
      username: '',
      password: ''
    },
    errorMessage: ''
  },
  methods: {
    handleLogin: function () {
      if (!this.form.username || !this.form.password) {
        this.errorMessage = "Username and Password are required.";
        return;
      }

      this.errorMessage = "";

      fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.form)
      })
        .then(response => {
          if (response.ok) {
            return response.json();
          } else {
            return response.json().then(data => {
              throw new Error(data.message || "Invalid login.");
            });
          }
        })
        .then(data => {
          window.location.href = data.redirect;
        })
        .catch(error => {
          console.error("Error:", error);
          this.errorMessage = error.message;
        });
    }
  }
});

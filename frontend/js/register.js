const app = new Vue({
  el: '#app',
  delimiters: ['${', '}'],
  data: {
    form: {
      username: '',
      password: '',
      confirm_password: '',
      fname: '',
      lname: '',
      email: '',
      ph_no: '',
      age: '',
      gender: '',
      reg_no: '',
      city: '',
      state: ''
    },
    errorMessage: '',
    successMessage: ''
  },
  methods: {
    handleRegister() {
      this.errorMessage = '';
      this.successMessage = '';

      if (this.form.password !== this.form.confirm_password) {
        this.errorMessage = "Passwords do not match!";
        return;
      }

      fetch('/register', {
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
            throw new Error(data.message || "Registration failed");
          });
        }
      })
      .then(data => {
        this.successMessage = data.message || "Registered successfully!";
        setTimeout(() => {
          window.location.href = "/login";
        }, 1500);
      })
      .catch(error => {
        this.errorMessage = error.message;
      });
    }
  }
});

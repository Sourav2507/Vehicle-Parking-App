const navbarApp = new Vue({
  el: '#navbar-vue',
  delimiters: ['${', '}'],
  data: {
    profileImage: ""
  },
  mounted() {
    fetch("/user/data")
      .then(res => res.json())
      .then(data => {
        this.profileImage = "/static/" + data.profile_image;
      })
      .catch(err => console.error("Error loading profile image:", err));
  },
  methods: {
    goHome() { window.location.href = "/user/dashboard"; },
    goFindParking() { window.location.href = "/user/find_parking"; },
    goBookings() { window.location.href = "/user/bookings"; },
    goPayments() { window.location.href = "/user/payments"; },
    goHelp() { window.location.href = "/user/help_and_support"; },
    goNotifications() { window.location.href = "/user/notifications"; },
    goProfile() { window.location.href = "/user/profile"; },
    goLogout() { window.location.href = "/logout"; }
  }
});

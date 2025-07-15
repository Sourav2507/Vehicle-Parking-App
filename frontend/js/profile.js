new Vue({
  el: "#profileApp",
  delimiters: ["${", "}"],
  data: {
    fname: "",
    lname: "",
    phone: "",
    age: "",
    gender: "",
    reg_no: "",
    address: "",
    email: "",
    role: "",
    profileImage: "",
    editMode: false,
  },
  mounted: function () {
    fetch("/user/data")
      .then((res) => res.json())
      .then((data) => {
        this.fname = data.fname;
        this.lname = data.lname;
        this.phone = data.phone;
        this.age = data.age;
        this.gender = data.gender;
        this.reg_no = data.reg_no;
        this.address = data.address;
        this.email = data.email;
        this.role = data.role;
        this.profileImage = data.profile_image;
      })
      .catch((err) => console.error("Error fetching profile:", err));
  },
  methods: {
    toggleEdit: function () {
      this.editMode = true;
    },
    saveChanges: function () {
      fetch("/user/data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fname: this.fname,
          lname: this.lname,
          phone: this.phone,
          age: this.age,
          reg_no: this.reg_no,
          address: this.address,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          alert(data.message || "Changes saved successfully.");
          this.editMode = false;
        })
        .catch((err) => {
          alert("Failed to save changes.");
          console.error(err);
        });
    },
    uploadImage: function (event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("image", file);

      fetch("/user/upload-image", {
        method: "POST",
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.image_url) {
            // Add timestamp to bust browser cache
            this.profileImage = data.image_url + "?t=" + Date.now();
          }

          // Show alert and then reload after user closes it
          setTimeout(() => {
            alert(data.message || "Image uploaded successfully.");
            location.reload(); // Refreshes the page so navbar and profile both update
          }, 100);
        })
        .catch((err) => {
          alert("Image upload failed.");
          console.error(err);
        });
    },
  },
});

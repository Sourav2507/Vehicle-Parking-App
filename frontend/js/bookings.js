const bokingapp = new Vue({
    el: "#bookingApp",
    delimiters: ['${', '}'],
    data: {
        activeTab: 'upcoming',
        upcoming: [],
        past: [],
        loading: true,
        error: null
    },
    mounted() {
        console.log('Started Fetching')
        fetch("/user/my_bookings")
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.upcoming = data.upcoming;
                    this.past = data.past;
                } else {
                    this.error = data.message;
                }
                this.loading = false;
            })
            .catch(err => {
                this.error = "Error fetching bookings.";
                this.loading = false;
            });
    },
    computed: {
        filteredBookings() {
            return this.activeTab === 'upcoming' ? this.upcoming : this.past;
        }
    },
    methods: {
        payForBooking(booking) {
            // Redirect to payment page
            window.location.href = "/user/payment";
        },
        formatDate(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleDateString() + " " + date.toLocaleTimeString();
        },
        formatTime(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleTimeString();
        },
        switchTab(tab) {
            this.activeTab = tab;
        }, cancelBooking(booking) {
            if (!confirm(`Are you sure you want to cancel Booking #${booking.id}? This action cannot be undone.`)) return;

            fetch(`/user/cancel_existing_booking/${booking.id}`, {
                method: "POST"
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Remove the booking from the correct list
                        const list = this.activeTab === 'upcoming' ? this.upcoming : this.past;
                        const index = list.findIndex(b => b.id === booking.id);
                        if (index !== -1) list.splice(index, 1);
                    } else {
                        alert(data.message || "Failed to delete booking.");
                    }
                })
                .catch(err => {
                    alert("Error deleting booking.");
                });
        }


    }
});

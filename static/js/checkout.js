document.addEventListener('DOMContentLoaded', () => {
    const payBtn = document.getElementById('pay-btn');
    const form = document.getElementById('checkout-form');
    const errorDiv = document.getElementById('payment-error');

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
        payBtn.textContent = 'PAY NOW';
        payBtn.disabled = false;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    payBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        
        // 1. Basic validation
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        payBtn.disabled = true;
        payBtn.textContent = 'PROCESSING...';
        errorDiv.style.display = 'none';

        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());

        try {
            // 2. Call Django to calculate totals & create Razorpay Order
            const response = await fetch(window.URL_CREATE_PAYMENT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                showError(data.error || 'Failed to initialize payment.');
                return;
            }

            // 3. Initialize Razorpay Checkout
            const options = {
                key: window.RAZORPAY_KEY, // Enter the Key ID generated from the Dashboard
                amount: data.amount, // Amount is in currency subunits. Default currency is INR. Hence, 50000 refers to 50000 paise
                currency: data.currency,
                name: "URBN Clothing",
                description: "Purchase Order " + data.order_number,
                image: "https://example.com/your_logo", // Replace with real logo if needed
                order_id: data.razorpay_order_id,
                handler: async function (response) {
                    // 4. On success, verify with our server!
                    payBtn.textContent = 'VERIFYING...';
                    
                    try {
                        const verifyResponse = await fetch(window.URL_PAYMENT_SUCCESS, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            body: JSON.stringify({
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_signature: response.razorpay_signature,
                                local_order_id: data.order_id
                            })
                        });

                        const verifyData = await verifyResponse.json();

                        if (verifyData.success) {
                            // Redirect to success page
                            const successUrl = window.URL_ORDER_CONFIRMATION.replace('ORDER_NO', data.order_number);
                            window.location.href = successUrl;
                        } else {
                            showError('Payment verification failed. Please contact support.');
                        }
                    } catch (err) {
                        showError('An error occurred during verification.');
                    }
                },
                prefill: {
                    name: data.customer_name,
                    email: data.customer_email,
                    contact: data.customer_phone
                },
                theme: {
                    color: "#000000"
                },
                modal: {
                    ondismiss: function() {
                        showError("Payment Cancelled.");
                    }
                }
            };

            const rzp = new Razorpay(options);
            
            rzp.on('payment.failed', function (response){
                showError("Payment Failed: " + response.error.description);
            });

            rzp.open();

        } catch (error) {
            showError("Network error. Please try again.");
        }
    });
});

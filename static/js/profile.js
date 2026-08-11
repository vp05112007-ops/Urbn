document.addEventListener('DOMContentLoaded', () => {
    // CSRF Token Setup
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    function getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        };
    }

    // Toast Notification System
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 3500);
    }

    // Sidebar Navigation with URL Params
    const navBtns = document.querySelectorAll('.nav-btn:not(.logout-btn)');
    const sections = document.querySelectorAll('.dashboard-section');

    function switchSection(targetId, updateUrl = true) {
        navBtns.forEach(b => b.classList.remove('active'));
        sections.forEach(s => s.classList.remove('active'));
        
        const activeBtn = Array.from(navBtns).find(b => b.getAttribute('data-target') === targetId);
        if (activeBtn) activeBtn.classList.add('active');
        
        const targetSection = document.getElementById(targetId);
        if (targetSection) targetSection.classList.add('active');

        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.set('section', targetId.replace('-section', ''));
            window.history.pushState({ section: targetId }, '', url);
        }
    }

    // Initialize from URL
    const urlParams = new URLSearchParams(window.location.search);
    const initialSection = urlParams.get('section');
    if (initialSection && document.getElementById(initialSection + '-section')) {
        switchSection(initialSection + '-section', false);
    }

    // Handle button clicks
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            switchSection(btn.getAttribute('data-target'));
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.section) {
            switchSection(e.state.section, false);
        } else {
            // Default to personal info if no state
            switchSection('personal-info-section', false);
        }
    });

    // 1. Personal Info Form
    const personalInfoForm = document.getElementById('personal-info-form');
    if (personalInfoForm) {
        personalInfoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = personalInfoForm.querySelector('button[type="submit"]');
            btn.textContent = 'Saving...';
            btn.disabled = true;

            const selectedCategories = [];
            document.querySelectorAll('input[name="preferred_categories"]:checked').forEach(cb => selectedCategories.push(cb.value));
            
            const clothingSizeEl = document.querySelector('input[name="clothing_size"]:checked');
            const preferredFitEl = document.querySelector('input[name="preferred_fit"]:checked');

            const data = {
                first_name: document.getElementById('id_first_name').value,
                last_name: document.getElementById('id_last_name').value,
                display_name: document.getElementById('id_display_name').value,
                date_of_birth: document.getElementById('id_date_of_birth').value,
                phone: document.getElementById('id_phone').value,
                country: document.getElementById('id_country').value,
                preferred_language: document.getElementById('id_preferred_language').value,
                clothing_size: clothingSizeEl ? clothingSizeEl.value : '',
                preferred_fit: preferredFitEl ? preferredFitEl.value : '',
                preferred_categories: selectedCategories
            };

            try {
                const res = await fetch('/api/profile/update/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(result.message);
                    const newName = data.display_name || (data.first_name ? `${data.first_name} ${data.last_name}` : '{{ user.username }}');
                    const sidebarH2 = document.querySelector('.sidebar-user-info h2');
                    if (sidebarH2) sidebarH2.textContent = newName;
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Save Changes';
                btn.disabled = false;
            }
        });
    }

    // 2. Change Password Form
    const changePasswordForm = document.getElementById('change-password-form');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = changePasswordForm.querySelector('button[type="submit"]');
            btn.textContent = 'Updating...';
            btn.disabled = true;

            const data = {
                current_password: document.getElementById('current_password').value,
                new_password: document.getElementById('new_password').value,
                confirm_password: document.getElementById('confirm_password').value
            };

            try {
                const res = await fetch('/api/profile/password/change/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(result.message);
                    changePasswordForm.reset();
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Change Password';
                btn.disabled = false;
            }
        });
    }

    // 3. Email Change OTP Flow
    const requestEmailForm = document.getElementById('request-email-form');
    const verifyEmailForm = document.getElementById('verify-email-form');
    const step1 = document.getElementById('email-change-step-1');
    const step2 = document.getElementById('email-change-step-2');
    let pendingEmail = '';

    if (requestEmailForm) {
        requestEmailForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = requestEmailForm.querySelector('button[type="submit"]');
            btn.textContent = 'Sending...';
            btn.disabled = true;

            pendingEmail = document.getElementById('new_email').value;

            try {
                const res = await fetch('/api/profile/email/request-change/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({ new_email: pendingEmail })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(result.message);
                    step1.style.display = 'none';
                    step2.style.display = 'block';
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Request Change';
                btn.disabled = false;
            }
        });
    }

    if (verifyEmailForm) {
        verifyEmailForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = verifyEmailForm.querySelector('button[type="submit"]');
            btn.textContent = 'Verifying...';
            btn.disabled = true;

            const otp = document.getElementById('email_otp').value;

            try {
                const res = await fetch('/api/profile/email/verify/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({ new_email: pendingEmail, otp: otp })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(result.message);
                    const currentEmailDisplay = document.getElementById('current-email-display');
                    if (currentEmailDisplay) currentEmailDisplay.textContent = pendingEmail;
                    const sidebarEmail = document.querySelector('.sidebar-user-info p');
                    if (sidebarEmail) sidebarEmail.textContent = pendingEmail;
                    step2.style.display = 'none';
                    step1.style.display = 'block';
                    requestEmailForm.reset();
                    verifyEmailForm.reset();
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Verify & Save';
                btn.disabled = false;
            }
        });
    }

    // 4. Addresses
    const modal = document.getElementById('address-modal');
    const btnAddAddress = document.getElementById('btn-add-address');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const addressForm = document.getElementById('address-form');
    
    if (btnAddAddress) {
        btnAddAddress.addEventListener('click', () => {
            modal.style.display = 'flex';
        });
    }

    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => {
            modal.style.display = 'none';
            addressForm.reset();
        });
    }

    if (addressForm) {
        addressForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = addressForm.querySelector('button[type="submit"]');
            btn.textContent = 'Saving...';
            btn.disabled = true;

            const data = {
                full_name: document.getElementById('addr_full_name').value,
                phone: document.getElementById('addr_phone').value,
                address_line_1: document.getElementById('addr_line_1').value,
                address_line_2: document.getElementById('addr_line_2').value,
                city: document.getElementById('addr_city').value,
                state: document.getElementById('addr_state').value,
                postal_code: document.getElementById('addr_postal').value,
                country: document.getElementById('addr_country').value,
                is_default: document.getElementById('addr_is_default').checked
            };

            try {
                const res = await fetch('/api/profile/address/add/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Address added successfully');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Save Address';
                btn.disabled = false;
            }
        });
    }

    document.querySelectorAll('.btn-delete-address').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to delete this address?')) return;
            const id = btn.getAttribute('data-id');
            try {
                const res = await fetch(`/api/profile/address/${id}/delete/`, {
                    method: 'POST',
                    headers: getHeaders()
                });
                const result = await res.json();
                if (result.success) {
                    showToast('Address deleted');
                    btn.closest('.address-card').remove();
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    });

    document.querySelectorAll('.btn-set-default').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            try {
                const res = await fetch(`/api/profile/address/${id}/set-default/`, {
                    method: 'POST',
                    headers: getHeaders()
                });
                const result = await res.json();
                if (result.success) {
                    showToast('Default address updated');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    });


    // 5. Profile Photo Upload
    const photoInput = document.getElementById('profile-photo-input');
    if (photoInput) {
        photoInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            // Validate size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                showToast('Image is too large (max 5MB)', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('profile_photo', file);
            
            try {
                const res = await fetch('/api/profile/photo/upload/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Profile photo updated');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    }

    const btnRemovePhoto = document.getElementById('btn-remove-photo');
    if (btnRemovePhoto) {
        btnRemovePhoto.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to remove your profile photo?')) return;
            
            try {
                const res = await fetch('/api/profile/photo/remove/', {
                    method: 'POST',
                    headers: getHeaders()
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Profile photo removed');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    }

    // 6. Two-Factor Authentication
    const btnEnable2FA = document.getElementById('btn-enable-2fa');
    const setup2FaModal = document.getElementById('setup-2fa-modal');
    const verifySetup2FaForm = document.getElementById('verify-setup-2fa-form');
    
    if (btnEnable2FA) {
        btnEnable2FA.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/security/2fa/request/', {
                    method: 'POST',
                    headers: getHeaders()
                });
                const result = await res.json();
                
                if (result.success) {
                    document.getElementById('qr-code-img').src = 'data:image/png;base64,' + result.qr_code;
                    document.getElementById('manual-secret').textContent = result.secret;
                    setup2FaModal.style.display = 'flex';
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    }
    
    if (verifySetup2FaForm) {
        verifySetup2FaForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = verifySetup2FaForm.querySelector('button[type="submit"]');
            btn.textContent = 'Verifying...';
            btn.disabled = true;
            
            const token = document.getElementById('setup_2fa_token').value;
            
            try {
                const res = await fetch('/api/security/2fa/verify/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({ token })
                });
                const result = await res.json();
                
                if (result.success) {
                    document.getElementById('setup-2fa-step-1').style.display = 'none';
                    document.getElementById('setup-2fa-step-2').style.display = 'block';
                    
                    const codesContainer = document.getElementById('recovery-codes-container');
                    codesContainer.innerHTML = result.recovery_codes.join('<br>');
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Verify & Enable';
                btn.disabled = false;
            }
        });
    }
    
    const btnDisable2FA = document.getElementById('btn-disable-2fa');
    const disable2FaModal = document.getElementById('disable-2fa-modal');
    const disable2FaForm = document.getElementById('disable-2fa-form');
    
    if (btnDisable2FA) {
        btnDisable2FA.addEventListener('click', () => {
            disable2FaModal.style.display = 'flex';
        });
    }
    
    if (disable2FaForm) {
        disable2FaForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = disable2FaForm.querySelector('button[type="submit"]');
            btn.textContent = 'Disabling...';
            btn.disabled = true;
            
            const password = document.getElementById('disable_2fa_password').value;
            
            try {
                const res = await fetch('/api/security/2fa/disable/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({ password })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('2FA Disabled successfully');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Disable 2FA';
                btn.disabled = false;
            }
        });
    }

    document.querySelectorAll('.btn-close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            setup2FaModal.style.display = 'none';
            disable2FaModal.style.display = 'none';
        });
    });

    // 7. Active Sessions Logout
    const btnLogoutAll = document.getElementById('btn-logout-all');
    if (btnLogoutAll) {
        btnLogoutAll.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to log out all other sessions?')) return;
            
            try {
                const res = await fetch('/api/security/session/logout-all/', {
                    method: 'POST',
                    headers: getHeaders()
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('All other sessions logged out');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    }
    
    document.querySelectorAll('.btn-logout-session').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to log out this session?')) return;
            
            const sessionKey = btn.getAttribute('data-key');
            try {
                const res = await fetch(`/api/security/session/logout/`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({ session_key: sessionKey })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Session logged out');
                    btn.closest('.session-item').remove();
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            }
        });
    });

    // 8. Security Notifications
    const securityNotificationsForm = document.getElementById('security-notifications-form');
    if (securityNotificationsForm) {
        securityNotificationsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = securityNotificationsForm.querySelector('button[type="submit"]');
            btn.textContent = 'Saving...';
            btn.disabled = true;
            
            const data = {
                new_login: securityNotificationsForm.querySelector('[name="new_login"]').checked,
                password_changed: securityNotificationsForm.querySelector('[name="password_changed"]').checked,
                email_changed: securityNotificationsForm.querySelector('[name="email_changed"]').checked,
                '2fa_changes': securityNotificationsForm.querySelector('[name="2fa_changes"]').checked,
                suspicious_login: securityNotificationsForm.querySelector('[name="suspicious_login"]').checked
            };
            
            try {
                const res = await fetch('/api/security/notifications/update/', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Preferences saved successfully');
                } else {
                    showToast(result.message, 'error');
                }
            } catch (err) {
                showToast('An error occurred.', 'error');
            } finally {
                btn.textContent = 'Save Preferences';
                btn.disabled = false;
            }
        });
    }

});

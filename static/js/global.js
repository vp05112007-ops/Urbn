document.addEventListener('DOMContentLoaded', () => {
    initSearchOverlay();
    setupMobileMenu();
    initScrollReveal();
    fetchCart();
    setupCartDrawerListeners();
    initPremiumNavbar();
});

function initPremiumNavbar() {
    const nav = document.querySelector('.global-nav');
    if (nav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 20) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        });
    }

    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-center a');
    navLinks.forEach(link => {
        const url = new URL(link.href, window.location.origin);
        if (url.pathname === currentPath && currentPath !== '/') {
            link.classList.add('active');
        } else if (currentPath === '/' && url.pathname === '/') {
            link.classList.add('active');
        }
    });
}

function initScrollReveal() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15
    };

    const revealCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    };

    const scrollObserver = new IntersectionObserver(revealCallback, observerOptions);
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    
    revealElements.forEach(el => {
        scrollObserver.observe(el);
    });
}

function initSearchOverlay() {
    const searchBtns = document.querySelectorAll('.trigger-search');
    const overlay = document.getElementById('search-overlay');
    const closeBtn = document.querySelector('.close-search');

    if (!overlay) return;

    searchBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            overlay.classList.add('active');
            const input = overlay.querySelector('.search-input');
            if (input) input.focus();
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            overlay.classList.remove('active');
        });
    }

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            overlay.classList.remove('active');
        }
    });
}

let currentCartState = { items: [], subtotal: 0, count: 0 };

async function fetchCart() {
    try {
        const response = await fetch('/api/cart/');
        if (response.ok) {
            currentCartState = await response.json();
            updateCartCountUI(currentCartState.count);
            renderCartDrawer(currentCartState);
        }
    } catch (e) {
        console.error("Failed to fetch cart", e);
    }
}

function updateCartCountUI(count) {
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(el => {
        el.textContent = count;
    });
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

async function addToCart(product) {
    try {
        const response = await fetch('/api/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(product)
        });
        
        if (response.ok) {
            currentCartState = await response.json();
            updateCartCountUI(currentCartState.count);
            
            // Animate Bag count slightly
            const bagIcons = document.querySelectorAll('.cart-count-wrapper');
            bagIcons.forEach(icon => {
                icon.style.transform = 'scale(1.1)';
                icon.style.transition = 'transform 0.2s';
                setTimeout(() => icon.style.transform = 'scale(1)', 250);
            });
            
            renderCartDrawer(currentCartState, product.id);
            openCartDrawer();
            showToast('✓ Added to Bag');
        } else {
            console.error("Add to cart failed");
        }
    } catch (e) {
        console.error(e);
    }
}

async function updateCartItem(itemId, quantity) {
    if (quantity < 1 || quantity > 9) return;
    try {
        const response = await fetch(`/api/cart/update/${itemId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ quantity })
        });
        if (response.ok) {
            currentCartState = await response.json();
            updateCartCountUI(currentCartState.count);
            renderCartDrawer(currentCartState);
        }
    } catch (e) {
        console.error(e);
    }
}

async function removeCartItem(itemId) {
    try {
        const response = await fetch(`/api/cart/remove/${itemId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        if (response.ok) {
            currentCartState = await response.json();
            updateCartCountUI(currentCartState.count);
            renderCartDrawer(currentCartState);
        }
    } catch (e) {
        console.error(e);
    }
}

function renderCartDrawer(state, highlightProductId = null) {
    const countEl = document.getElementById('cart-item-count-text');
    if (countEl) countEl.textContent = `${state.count} ITEMS`;
    
    const subtotalEl = document.getElementById('cart-subtotal-amount');
    if (subtotalEl) subtotalEl.textContent = `₹${parseFloat(state.subtotal).toLocaleString('en-IN')}`;
    
    const container = document.getElementById('cart-items-container');
    if (!container) return;
    
    if (state.items.length === 0) {
        container.innerHTML = `
            <div class="cart-empty-state">
                <h3>YOUR BAG IS EMPTY</h3>
                <p>Discover something new for your wardrobe.</p>
                <a href="/categories.html" class="btn-primary" style="display:inline-block; margin-top:24px; padding:12px 32px; text-decoration:none;">SHOP NOW</a>
            </div>
        `;
        return;
    }
    
    container.innerHTML = state.items.map(item => `
        <div class="cart-item ${item.product_id === highlightProductId ? 'highlight-new' : ''}">
            <div class="cart-item-img">
                <img src="${item.image || '/static/images/placeholder.png'}" alt="${item.name}">
            </div>
            <div class="cart-item-details">
                <h4 class="cart-item-title">${item.name}</h4>
                ${item.size || item.color || item.fit ? `<p class="cart-item-variant">${[item.color, item.size, item.fit].filter(Boolean).join(' | ')}</p>` : ''}
                ${item.custom_text ? `<p class="cart-item-custom">"${item.custom_text}" - ${item.placement}</p>` : ''}
                <div class="cart-item-price">₹${parseFloat(item.price).toLocaleString('en-IN')}</div>
                ${item.product_id === highlightProductId ? `<p style="color: #4caf50; font-size: 12px; margin-top: 4px; font-weight: 600;">Item is added</p>` : ''}
                
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button class="quantity-btn" aria-label="Decrease quantity" onclick="updateCartItem(${item.id}, ${item.quantity - 1})" style="visibility: ${item.quantity <= 1 ? 'hidden' : 'visible'};">-</button>
                        <div class="quantity-value">${item.quantity}</div>
                        <button class="quantity-btn" aria-label="Increase quantity" onclick="updateCartItem(${item.id}, ${item.quantity + 1})" ${item.quantity >= 9 ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>+</button>
                    </div>
                    <button class="remove-btn" aria-label="Remove item" onclick="removeCartItem(${item.id})">REMOVE</button>
                </div>
            </div>
        </div>
    `).join('');

    if (highlightProductId) {
        setTimeout(() => {
            const newItem = container.querySelector('.highlight-new');
            if (newItem) {
                newItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }, 150); // Slight delay to ensure DOM is updated and drawer is animating
    }
}

function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-backdrop');
    if (drawer && backdrop) {
        drawer.classList.add('active');
        backdrop.classList.add('active');
        document.body.classList.add('cart-sidebar-open');
        if (window.innerWidth <= 768) {
            document.body.classList.add('no-scroll');
        }
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-backdrop');
    if (drawer && backdrop) {
        drawer.classList.remove('active');
        backdrop.classList.remove('active');
        document.body.classList.remove('cart-sidebar-open');
        document.body.classList.remove('no-scroll');
    }
}

function showToast(message) {
    let toast = document.querySelector('.toast-notification');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast-notification';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function setupCartDrawerListeners() {
    // Override nav bag click
    const bagNavLinks = document.querySelectorAll('a[href*="cart"]');
    bagNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            openCartDrawer();
        });
    });
    
    // Set up drawer close listeners
    const closeBtn = document.getElementById('close-cart-btn');
    const contBtn = document.getElementById('continue-shopping-btn');
    const backdrop = document.getElementById('cart-backdrop');
    
    if (closeBtn) {
        closeBtn.setAttribute('aria-label', 'Close bag');
        closeBtn.addEventListener('click', closeCartDrawer);
    }
    if (contBtn) contBtn.addEventListener('click', closeCartDrawer);
    if (backdrop) backdrop.addEventListener('click', closeCartDrawer);
    
    // Also ESC key close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeCartDrawer();
    });
}

function toggleWishlist(productId, btnElement) {
    let wishlist = JSON.parse(localStorage.getItem('urbn_wishlist')) || [];
    const index = wishlist.indexOf(productId);
    
    if (index > -1) {
        wishlist.splice(index, 1);
        if (btnElement) btnElement.classList.remove('active');
    } else {
        wishlist.push(productId);
        if (btnElement) btnElement.classList.add('active');
    }
    
    localStorage.setItem('urbn_wishlist', JSON.stringify(wishlist));
}

function checkWishlistState() {
    let wishlist = JSON.parse(localStorage.getItem('urbn_wishlist')) || [];
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        const id = btn.getAttribute('data-id');
        if (wishlist.includes(id)) {
            btn.classList.add('active');
        }
    });
}

function setupMobileMenu() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navCenter = document.querySelector('.nav-center');
    
    if (toggle && navCenter) {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navCenter.classList.toggle('mobile-active');
            toggle.classList.toggle('active');
            
            if (navCenter.classList.contains('mobile-active')) {
                document.body.classList.add('no-scroll');
                // Change hamburger icon to X
                toggle.innerHTML = '&times;';
                toggle.style.fontSize = '32px';
            } else {
                document.body.classList.remove('no-scroll');
                // Change back to hamburger
                toggle.innerHTML = '&#9776;';
                toggle.style.fontSize = '24px';
            }
        });

        // Close when clicking a link
        const links = navCenter.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', () => {
                navCenter.classList.remove('mobile-active');
                toggle.classList.remove('active');
                document.body.classList.remove('no-scroll');
                toggle.innerHTML = '&#9776;';
                toggle.style.fontSize = '24px';
            });
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (navCenter.classList.contains('mobile-active') && !navCenter.contains(e.target) && e.target !== toggle) {
                navCenter.classList.remove('mobile-active');
                toggle.classList.remove('active');
                document.body.classList.remove('no-scroll');
                toggle.innerHTML = '&#9776;';
                toggle.style.fontSize = '24px';
            }
        });
    }
}


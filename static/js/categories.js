document.addEventListener('DOMContentLoaded', () => {
    
    // 1. DYNAMIC DATA
    let productsData = [];

    // State
    let currentSort = 'featured';
    let currentFilters = {
        category: 'All Categories',
        size: [],
        color: [],
        price: null // 'under-1000', '1000-2500', 'over-2500'
    };

    // DOM Elements
    const gridEl = document.getElementById('product-grid');
    const emptyStateEl = document.getElementById('empty-state');
    const countEl = document.getElementById('product-count-display');
    const activeFiltersContainer = document.getElementById('active-filters-container');

    // 2. RENDERING
    function renderSkeleton() {
        gridEl.innerHTML = Array(6).fill('').map(() => `
            <div class="skeleton-card">
                <div class="skeleton-img"></div>
                <div class="skeleton-text"></div>
                <div class="skeleton-text short"></div>
            </div>
        `).join('');
    }

    function renderProducts(products) {
        if (products.length === 0) {
            gridEl.style.display = 'none';
            emptyStateEl.style.display = 'block';
            countEl.textContent = '0';
            return;
        }

        gridEl.style.display = 'grid';
        emptyStateEl.style.display = 'none';
        countEl.textContent = products.length;

        gridEl.innerHTML = products.map(p => `
            <div class="product-card">
                ${p.badge ? `<div class="product-badges"><span class="badge">${p.badge}</span></div>` : ''}
                <div class="product-image-wrap">
                    <img src="${p.image}" alt="${p.name}" onerror="this.src='/static/images/placeholder.png';">
                    <div class="wishlist-btn" data-id="${p.id}">♡</div>
                    <button class="quick-add-btn" data-id="${p.id}">+ ADD TO BAG</button>
                </div>
                <div class="product-info">
                    <span class="product-category">${p.category}</span>
                    <span class="product-name">${p.name}</span>
                    <span class="product-price">₹${p.price.toLocaleString('en-IN')}</span>
                    ${p.colors.length > 0 ? `
                        <div class="product-colors">
                            ${p.colors.map(c => {
                                const hex = c === 'Black' ? '#000' : c === 'White' ? '#fff' : c === 'Gray' ? '#777' : c === 'Green' ? '#3c5233' : '#8c1c1c';
                                return `<div class="dot" style="background: ${hex}" title="${c}"></div>`;
                            }).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');

        attachProductListeners();
    }

    function renderActiveFilters() {
        activeFiltersContainer.innerHTML = '';
        
        let hasFilters = false;

        if (currentFilters.category !== 'All Categories') {
            hasFilters = true;
            activeFiltersContainer.innerHTML += `<div class="filter-chip">${currentFilters.category} <span data-type="category" data-val="${currentFilters.category}">×</span></div>`;
        }

        currentFilters.size.forEach(s => {
            hasFilters = true;
            activeFiltersContainer.innerHTML += `<div class="filter-chip">${s} <span data-type="size" data-val="${s}">×</span></div>`;
        });

        currentFilters.color.forEach(c => {
            hasFilters = true;
            activeFiltersContainer.innerHTML += `<div class="filter-chip">${c} <span data-type="color" data-val="${c}">×</span></div>`;
        });

        if (currentFilters.price) {
            hasFilters = true;
            let label = currentFilters.price === 'under-1000' ? 'Under ₹1,000' : currentFilters.price === '1000-2500' ? '₹1k - ₹2.5k' : 'Over ₹2,500';
            activeFiltersContainer.innerHTML += `<div class="filter-chip">${label} <span data-type="price" data-val="${currentFilters.price}">×</span></div>`;
        }
        
        // Add chip clear listeners
        document.querySelectorAll('.filter-chip span').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.dataset.type;
                const val = e.target.dataset.val;
                
                if (type === 'category') {
                    document.querySelector(`input[name="category"][value="All Categories"]`).click();
                } else if (type === 'size') {
                    document.querySelector(`input[name="size"][value="${val}"]`).click();
                } else if (type === 'color') {
                    document.querySelector(`input[name="color"][value="${val}"]`).click();
                } else if (type === 'price') {
                    const el = document.querySelector(`input[name="price"][value="${val}"]`);
                    el.checked = false;
                    applyFilters();
                }
            });
        });
    }

    // 3. FILTERING & SORTING
    function applyFilters() {
        // Read form state
        currentFilters.category = document.querySelector('input[name="category"]:checked')?.value || 'All Categories';
        
        currentFilters.size = Array.from(document.querySelectorAll('input[name="size"]:checked')).map(el => el.value);
        currentFilters.color = Array.from(document.querySelectorAll('input[name="color"]:checked')).map(el => el.value);
        
        const priceEl = document.querySelector('input[name="price"]:checked');
        currentFilters.price = priceEl ? priceEl.value : null;

        // Apply to data
        let filtered = productsData.filter(p => {
            if (currentFilters.category !== 'All Categories' && p.category !== currentFilters.category) return false;
            if (currentFilters.size.length > 0 && !currentFilters.size.some(s => p.sizes.includes(s))) return false;
            if (currentFilters.color.length > 0 && !currentFilters.color.some(c => p.colors.includes(c))) return false;
            
            if (currentFilters.price) {
                if (currentFilters.price === 'under-1000' && p.price >= 1000) return false;
                if (currentFilters.price === '1000-2500' && (p.price < 1000 || p.price > 2500)) return false;
                if (currentFilters.price === 'over-2500' && p.price <= 2500) return false;
            }
            return true;
        });

        // Sort
        if (currentSort === 'price-low') {
            filtered.sort((a, b) => a.price - b.price);
        } else if (currentSort === 'price-high') {
            filtered.sort((a, b) => b.price - a.price);
        } else if (currentSort === 'name') {
            filtered.sort((a, b) => a.name.localeCompare(b.name));
        } else if (currentSort === 'newest') {
            filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
        }
        // 'featured' maintains default array order

        renderActiveFilters();
        
        renderSkeleton();
        setTimeout(() => {
            renderProducts(filtered);
        }, 300); // Artificial delay for premium feel
    }

    // 4. EVENT LISTENERS
    
    // Filter Changes
    document.querySelectorAll('.filters-sidebar input').forEach(input => {
        input.addEventListener('change', applyFilters);
    });

    // Clear Filters
    document.getElementById('clear-filters-btn').addEventListener('click', () => {
        document.querySelector('input[name="category"][value="All Categories"]').checked = true;
        document.querySelectorAll('input[name="size"], input[name="color"]').forEach(el => el.checked = false);
        document.querySelectorAll('input[name="price"]').forEach(el => el.checked = false);
        applyFilters();
    });

    // Custom Sort Dropdown
    const sortDropdown = document.getElementById('custom-sort-dropdown');
    const sortValDisplay = document.getElementById('current-sort-val');
    
    if (sortDropdown) {
        sortDropdown.addEventListener('click', (e) => {
            sortDropdown.classList.toggle('active');
        });

        document.querySelectorAll('.sort-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                currentSort = opt.dataset.value;
                sortValDisplay.textContent = opt.textContent;
                
                // Update mobile sort radio if exists to keep sync
                const mobileRadio = document.querySelector(`input[name="mobile-sort"][value="${currentSort}"]`);
                if (mobileRadio) mobileRadio.checked = true;

                sortDropdown.classList.remove('active');
                applyFilters();
            });
        });

        document.addEventListener('click', (e) => {
            if (!sortDropdown.contains(e.target)) {
                sortDropdown.classList.remove('active');
            }
        });
    }

    // Filter Group Collapsible
    document.querySelectorAll('.filter-title').forEach(title => {
        title.addEventListener('click', () => {
            const group = title.parentElement;
            group.classList.toggle('collapsed');
        });
    });

    // Mobile specific
    const mobileFilterBtn = document.getElementById('mobile-filter-btn');
    const sidebar = document.getElementById('filters-sidebar');
    const closeSidebarBtn = document.querySelector('.close-sidebar-btn');
    
    if (mobileFilterBtn && sidebar) {
        mobileFilterBtn.addEventListener('click', () => {
            sidebar.classList.add('mobile-active');
            document.body.style.overflow = 'hidden';
        });
    }

    if (closeSidebarBtn && sidebar) {
        closeSidebarBtn.addEventListener('click', () => {
            sidebar.classList.remove('mobile-active');
            document.body.style.overflow = '';
        });
    }

    const mobileSortBtn = document.getElementById('mobile-sort-btn');
    const sortModal = document.getElementById('mobile-sort-modal');
    const closeSortModalBtn = document.querySelector('.close-modal-btn');

    if (mobileSortBtn && sortModal) {
        mobileSortBtn.addEventListener('click', () => {
            sortModal.classList.add('active');
        });
    }

    if (closeSortModalBtn && sortModal) {
        closeSortModalBtn.addEventListener('click', () => {
            sortModal.classList.remove('active');
        });
    }

    document.querySelectorAll('input[name="mobile-sort"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentSort = e.target.value;
            // update desktop label
            const dtOpt = document.querySelector(`.sort-option[data-value="${currentSort}"]`);
            if (dtOpt && sortValDisplay) {
                sortValDisplay.textContent = dtOpt.textContent;
            }
            sortModal.classList.remove('active');
            applyFilters();
        });
    });


    // Product Interactions
    function attachProductListeners() {
        // Quick Add
        document.querySelectorAll('.quick-add-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation(); // prevent card click
                const id = btn.dataset.id;
                const p = productsData.find(x => x.id === id);
                if (p) {
                    const cartItem = {
                        id: p.id,
                        name: p.name,
                        price: p.price,
                        image: p.image,
                        size: 'M', // default size if not selected
                        color: p.colors[0] || 'Black'
                    };
                    if (typeof addToCart === 'function') {
                        addToCart(cartItem);
                        const originalText = btn.textContent;
                        btn.textContent = '✓ ADDED TO BAG';
                        btn.style.background = '#4caf50';
                        btn.style.color = '#fff';
                        setTimeout(() => {
                            btn.textContent = originalText;
                            btn.style.background = '';
                            btn.style.color = '';
                        }, 1500);
                    }
                }
            });
        });

        // Wishlist
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof toggleWishlist === 'function') {
                    toggleWishlist(btn.dataset.id, btn);
                } else {
                    btn.classList.toggle('active');
                }
            });
        });

        // Card Click (routing)
        document.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Ignore if clicked on buttons
                if (e.target.classList.contains('quick-add-btn') || e.target.classList.contains('wishlist-btn')) return;
                
                // Currently no detail page exists in URBN, but we mock the action
                console.log("Navigate to product page");
                // window.location.href = `/product/${card.querySelector('.quick-add-btn').dataset.id}`;
            });
        });
    }

    // INITIALIZATION
    async function fetchAndRender() {
        try {
            renderSkeleton();
            const res = await fetch('/api/products/');
            if (res.ok) {
                const data = await res.json();
                productsData = data.products;
                applyFilters();
                if (typeof checkWishlistState === 'function') {
                    setTimeout(checkWishlistState, 100);
                }
            } else {
                const errText = await res.text();
                gridEl.style.display = 'none';
                emptyStateEl.style.display = 'block';
                emptyStateEl.innerHTML = `<h3>API ERROR (${res.status})</h3><p>${errText.substring(0, 100)}</p>`;
            }
        } catch(e) { 
            console.error("Failed to load products", e); 
            gridEl.style.display = 'none';
            emptyStateEl.style.display = 'block';
            emptyStateEl.innerHTML = `<h3>NETWORK ERROR</h3><p>${e.message}</p>`;
        }
    }
    fetchAndRender();
});

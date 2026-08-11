document.addEventListener('DOMContentLoaded', () => {
    // Initialize Wishlist State
    checkWishlistState();

    // Setup Add to Cart Listeners
    const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const card = e.target.closest('.product-card');
            const product = {
                id: card.dataset.id,
                name: card.dataset.name,
                price: parseFloat(card.dataset.price),
                image: card.dataset.image,
                size: 'M' // Default size for quick add
            };
            addToCart(product);
            
            // Visual feedback
            const originalText = btn.textContent;
            btn.textContent = 'ADDED';
            btn.style.background = '#4caf50';
            btn.style.color = '#fff';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.style.color = '';
            }, 1000);
        });
    });

    // Setup Wishlist Listeners
    const wishlistBtns = document.querySelectorAll('.wishlist-btn');
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            toggleWishlist(id, btn);
        });
    });
});

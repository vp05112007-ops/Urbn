document.addEventListener('DOMContentLoaded', () => {
    checkWishlistState();

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
                size: 'M'
            };
            addToCart(product);
            
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

    const wishlistBtns = document.querySelectorAll('.wishlist-btn');
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            toggleWishlist(id, btn);
        });
    });
});

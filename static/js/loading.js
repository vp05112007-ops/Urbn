document.addEventListener('DOMContentLoaded', () => {
    // Check if loading screen has been seen in this session
    if (sessionStorage.getItem('urbn_loading_seen')) {
        // Redirect immediately without showing anything
        window.location.replace('landing.html');
        return;
    }

    // Set flag so it's not seen again during this session
    sessionStorage.setItem('urbn_loading_seen', 'true');

    // Wait for the animation (2s) then fade out and redirect
    const loadingDuration = 2200; // 2s animation + slight buffer
    const fadeOutDuration = 500;

    setTimeout(() => {
        document.querySelector('.loading-container').classList.add('fade-out');
        
        setTimeout(() => {
            window.location.replace('landing.html');
        }, fadeOutDuration);
        
    }, loadingDuration);
});

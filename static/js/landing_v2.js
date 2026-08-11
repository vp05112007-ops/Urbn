document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById("hoodie-canvas");
    if (!canvas) return;
    const context = canvas.getContext("2d");

    const frameCount = 240;
    const images = [];
    let currentFrame = -1;
    let targetFrame = 0;
    let currentFrameFloat = 0;
    let ticking = false;

    const phases = [
        { element: document.getElementById('phase-1'), start: 0, end: 0.15 },
        { element: document.getElementById('phase-2'), start: 0.15, end: 0.30 },
        { element: document.getElementById('phase-3'), start: 0.30, end: 0.50 },
        { element: document.getElementById('phase-4'), start: 0.50, end: 0.65 },
        { element: document.getElementById('phase-5'), start: 0.65, end: 0.82 },
        { element: document.getElementById('phase-6'), start: 0.82, end: 1.01 } // 1.01 to catch exactly 1.0
    ];
    let currentActivePhase = -1;

    function drawFrame(index) {
        const img = images[index];

        if (!img || !img.complete || !img.naturalWidth) return;

        context.clearRect(0, 0, canvas.width, canvas.height);
        
        // Exact cover logic for full screen animation
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let scale = Math.max(
            viewportWidth / img.naturalWidth,
            viewportHeight / img.naturalHeight
        );

        // On mobile portrait screens, scale up to hide the black bottom half of the image
        // and make the 3D hoodie animation cover the entire screen area.
        if (viewportWidth < 768 && viewportHeight > viewportWidth) {
            scale *= 2.2; // Zoom in to make animation fill the screen
        }

        const drawWidth = img.naturalWidth * scale;
        const drawHeight = img.naturalHeight * scale;

        const offsetX = (viewportWidth - drawWidth) / 2;
        
        let offsetY = (viewportHeight - drawHeight) / 2;
        if (viewportWidth < 768 && viewportHeight > viewportWidth) {
            // Align to the top of the image so the texture covers the screen
            // The black bottom half will overflow and be hidden
            offsetY = 0;
        }

        // Scale by DPR before drawing since context is scaled
        context.drawImage(
            img,
            offsetX,
            offsetY,
            drawWidth,
            drawHeight
        );
    }

    // Preload all images
    async function preloadImages() {
        const promises = [];
        for (let i = 1; i <= frameCount; i++) {
            const img = new Image();
            img.decoding = "async";
            // Notice: Path adjusted for running from templates/landing.html
            img.src = `../enhance/frame_${i}.png`;
            images.push(img);
            
            const decodePromise = img.decode().catch(e => {
                // Ignore decode errors
            });
            promises.push(decodePromise);

            if (i === 1) {
                decodePromise.then(() => {
                    resizeCanvas();
                    drawFrame(0);
                });
            }
        }
        
        // Wait for all images to finish decoding in parallel
        await Promise.all(promises);
    }
    
    preloadImages();

    function render() {
        ticking = false;

        const vh = window.innerHeight;
        const scrollTop = window.scrollY;

        // SECTION 1: Hoodie Animation
        const heroSection = document.querySelector('.hero-animation-section');
        const storyContainer = document.getElementById('story-container');
        const hoodieCanvasContainer = document.getElementById('animation-stage');
        
        if (heroSection) {
            const heroRect = heroSection.getBoundingClientRect();
            // Total scrollable area inside the hero section
            const heroTotal = heroSection.offsetHeight - window.innerHeight;
            
            // Calculate progress strictly from hero section's position
            // The first 3/4ths (300vh out of 400vh total) is for frames
            let heroProgress = 0;
            if (heroTotal > 0) {
                heroProgress = Math.min(1, Math.max(0, -heroRect.top / heroTotal));
            }

            // Map the heroProgress (0 to 1) to the 240 frames
            // Since frames take up 300vh of the 400vh (which is 3/4), 
            // frameProgress hits 1.0 when heroProgress is ~0.75
            const frameProgress = Math.min(1, heroProgress * (4/3));

            // Fade out during the last 100vh (from 300vh to 400vh)
            if (-heroRect.top > 3 * vh) {
                storyContainer.style.opacity = 0;
                let fadeProgress = Math.min(1, (-heroRect.top - 3 * vh) / vh);
                hoodieCanvasContainer.style.opacity = 1 - fadeProgress;
            } else {
                storyContainer.style.opacity = 1;
                hoodieCanvasContainer.style.opacity = 1;
            }

            // Determine active text phase based on frameProgress
            let activePhaseIndex = -1;
            for (let i = 0; i < phases.length; i++) {
                if (frameProgress >= phases[i].start && frameProgress < phases[i].end) {
                    activePhaseIndex = i;
                    break;
                }
            }

            // Apply phase transitions
            if (activePhaseIndex !== currentActivePhase) {
                phases.forEach((p, index) => {
                    if (index === activePhaseIndex) {
                        p.element.classList.add('is-active');
                        p.element.classList.remove('is-leaving-up', 'is-leaving-down');
                    } else {
                        p.element.classList.remove('is-active');
                        if (index < activePhaseIndex) {
                            p.element.classList.add('is-leaving-up');
                            p.element.classList.remove('is-leaving-down');
                        } else {
                            p.element.classList.add('is-leaving-down');
                            p.element.classList.remove('is-leaving-up');
                        }
                    }
                });
                currentActivePhase = activePhaseIndex;
            }

            // Set target frame for smooth interpolation
            targetFrame = Math.min(
                frameCount - 1,
                Math.max(0, frameProgress * (frameCount - 1))
            );
        }

        // SECTION 2: Story Section
        const storySection = document.getElementById('story-section');
        if (storySection) {
            const rect = storySection.getBoundingClientRect();
            // Calculate progress relative to story section viewport
            const scrollableDistance = storySection.offsetHeight - window.innerHeight;
            let introProgress = 0;
            
            if (scrollableDistance > 0) {
                introProgress = Math.min(1, Math.max(0, -rect.top / scrollableDistance));
            }

            const hl1 = document.getElementById('hl-1');
            const hl2 = document.getElementById('hl-2');
            const hl3 = document.getElementById('hl-3');
            const hl4 = document.getElementById('hl-4');
            const hl5 = document.getElementById('hl-5');
            const img1 = document.getElementById('intro-img-1');
            const img2 = document.getElementById('intro-img-2');
            const img3 = document.getElementById('intro-img-3');
            const ctaHeadline = document.querySelector('.intro-cta-headline');
            const ctaDesc = document.querySelector('.intro-cta-desc');
            const introCtaBtn = document.querySelector('.intro-cta-btn');

            // Text morphing logic helper
            const updateHl = (element, start, end, progress) => {
                if (!element) return;
                const duration = end - start;
                if (progress >= start && progress < end) {
                    let localP = (progress - start) / duration;
                    // Fade in first 20%, fade out last 20%
                    let opacity = 1;
                    let y = 0;
                    if (localP < 0.2) {
                        opacity = localP / 0.2;
                        y = 15 * (1 - opacity);
                    } else if (localP > 0.8) {
                        opacity = (1 - localP) / 0.2;
                        y = -15 * (1 - opacity);
                    }
                    element.style.opacity = opacity;
                    element.style.transform = `translateY(${y}px)`;
                } else {
                    element.style.opacity = 0;
                }
            };

            // Image transition helper
            const updateImg = (img, appearStart, appearEnd, vanishStart, vanishEnd, baseScale, progress) => {
                if (!img) return;
                
                if (progress >= appearStart && progress < vanishStart) {
                    let pIn = Math.min(1, (progress - appearStart) / (appearEnd - appearStart));
                    img.style.opacity = pIn;
                    img.style.transform = `translateY(${(1 - pIn) * 60}px) scale(${baseScale + pIn * (1 - baseScale)})`;
                    img.style.filter = 'blur(0px)';
                } else if (progress >= vanishStart && progress <= vanishEnd) {
                    let pOut = Math.min(1, (progress - vanishStart) / (vanishEnd - vanishStart));
                    img.style.opacity = 1 - pOut;
                    img.style.transform = `translateY(${-pOut * 40}px) scale(${1 + pOut * 0.08})`;
                    img.style.filter = `blur(${pOut * 8}px)`;
                } else {
                    img.style.opacity = 0;
                }
            };

            // Apply timelines
            if (introProgress > 0 && introProgress <= 1) {
                // Headlines
                updateHl(hl1, 0.15, 0.35, introProgress);
                updateHl(hl2, 0.35, 0.55, introProgress);
                updateHl(hl3, 0.55, 0.72, introProgress);
                updateHl(hl4, 0.72, 0.86, introProgress);
                updateHl(hl5, 0.86, 1.20, introProgress);

                // Images
                updateImg(img1, 0.30, 0.40, 0.82, 0.90, 0.92, introProgress);
                updateImg(img2, 0.45, 0.55, 0.82, 0.90, 0.94, introProgress);
                updateImg(img3, 0.65, 0.75, 0.82, 0.90, 0.95, introProgress);

                // CTA
                let pCta = Math.min(1, Math.max(0, (introProgress - 0.86) / 0.14));
                if (ctaHeadline && ctaDesc && introCtaBtn) {
                    let headIn = Math.min(1, Math.max(0, pCta / 0.6));
                    let descIn = Math.min(1, Math.max(0, (pCta - 0.2) / 0.6));
                    let btnIn = Math.min(1, Math.max(0, (pCta - 0.4) / 0.6));

                    ctaHeadline.style.opacity = headIn;
                    ctaHeadline.style.transform = `translateX(${(1 - headIn) * 40}px)`;

                    ctaDesc.style.opacity = descIn;
                    ctaDesc.style.transform = `translateX(${(1 - descIn) * 30}px)`;

                    introCtaBtn.style.opacity = btnIn;
                    introCtaBtn.style.transform = `translateX(${(1 - btnIn) * 25}px)`;
                }
            } else {
                [hl1, hl2, hl3, hl4, img1, img2, img3, ctaHeadline, ctaDesc, introCtaBtn].forEach(el => {
                    if (el) el.style.opacity = 0;
                });
            }
        }
    }

    function requestRender() {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(render);
        }
    }

    function resizeCanvas() {
        if (canvas) {
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            
            canvas.style.width = `${window.innerWidth}px`;
            canvas.style.height = `${window.innerHeight}px`;
            
            context.scale(dpr, dpr);
            
            if (currentFrame >= 0) {
                drawFrame(currentFrame);
            }
        }
    }

    // Smooth animation loop for canvas frames
    function smoothLoop() {
        // Linear interpolation (lerp) for smooth frame transitions
        currentFrameFloat += (targetFrame - currentFrameFloat) * 0.1;
        
        const nextFrame = Math.min(frameCount - 1, Math.max(0, Math.round(currentFrameFloat)));
        if (nextFrame !== currentFrame) {
            currentFrame = nextFrame;
            drawFrame(currentFrame);
        }
        requestAnimationFrame(smoothLoop);
    }
    requestAnimationFrame(smoothLoop);

    window.addEventListener('scroll', requestRender, { passive: true });
    window.addEventListener('resize', () => {
        resizeCanvas();
        requestRender();
    });
    
    // Initial render call in case we load mid-scroll
    resizeCanvas();
    requestRender();
});

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        product: 'Hoodie',
        color: 'Black',
        size: 'M',
        fit: 'Oversized',
        text: '',
        placement: 'Front Center'
    };

    // Color Maps
    const colorMap = {
        'Black': '#111111',
        'White': '#f5f5f5',
        'Gray': '#555555',
        'Red': '#8b0000'
    };

    // Text Color Logic
    const textColorMap = {
        'Black': '#ffffff',
        'White': '#111111',
        'Gray': '#ffffff',
        'Red': '#ffffff'
    };

    // Product Images Base Path
    const imageBasePath = '/static/img/customizer/';
    
    // DOM Elements
    const productCanvas = document.getElementById('product-canvas');
    const productCtx = productCanvas ? productCanvas.getContext('2d', { willReadFrequently: true }) : null;
    const textCanvas = document.getElementById('custom-text-canvas');
    const textCtx = textCanvas ? textCanvas.getContext('2d', { willReadFrequently: true }) : null;
    let debounceTimer = null;
    const summaryContainer = document.getElementById('customization-summary');
    const textInput = document.querySelector('.text-input');

    const imageCache = {};
    let currentBaseImage = null;

    function loadBaseImage(product, callback) {
        const src = `${imageBasePath}${product.toLowerCase()}-White.webp`;
        if (imageCache[src]) {
            currentBaseImage = imageCache[src];
            callback();
        } else {
            const img = new Image();
            img.onload = () => {
                imageCache[src] = img;
                currentBaseImage = img;
                callback();
            };
            img.src = src;
        }
    }

    function getContainerDimensions() {
        const container = document.getElementById('product-image-container');
        return {
            width: container ? container.clientWidth : 0,
            height: container ? container.clientHeight : 0
        };
    }

    function calculateContain(imgWidth, imgHeight, containerWidth, containerHeight) {
        const targetWidth = containerWidth * 0.92;
        const targetHeight = containerHeight * 0.92;
        
        const scale = Math.min(targetWidth / imgWidth, targetHeight / imgHeight);
        
        const drawWidth = imgWidth * scale;
        const drawHeight = imgHeight * scale;
        
        const x = (containerWidth - drawWidth) / 2;
        const y = (containerHeight - drawHeight) / 2;
        
        return { scale, drawWidth, drawHeight, x, y };
    }

    function renderGarmentColor() {
        if (!productCanvas || !productCtx || !currentBaseImage) return;
        
        const container = getContainerDimensions();
        const cWidth = container.width;
        const cHeight = container.height;
        
        if (cWidth === 0 || cHeight === 0) return;
        
        if (productCanvas.width !== cWidth || productCanvas.height !== cHeight) {
            productCanvas.width = cWidth;
            productCanvas.height = cHeight;
        }
        
        const imgWidth = currentBaseImage.naturalWidth;
        const imgHeight = currentBaseImage.naturalHeight;
        const { drawWidth, drawHeight, x, y } = calculateContain(imgWidth, imgHeight, cWidth, cHeight);
        
        productCtx.clearRect(0, 0, cWidth, cHeight);
        
        // 1. Draw base white garment
        productCtx.globalCompositeOperation = 'source-over';
        productCtx.globalAlpha = 1.0;
        productCtx.drawImage(currentBaseImage, x, y, drawWidth, drawHeight);
        
        // 2. Recoloring
        if (state.color !== 'White') {
            // Multiply color
            productCtx.globalCompositeOperation = 'multiply';
            productCtx.fillStyle = colorMap[state.color];
            productCtx.fillRect(x, y, drawWidth, drawHeight);
            
            // Mask to garment alpha
            productCtx.globalCompositeOperation = 'destination-in';
            productCtx.drawImage(currentBaseImage, x, y, drawWidth, drawHeight);
            
            // Restore highlights using overlay
            productCtx.globalCompositeOperation = 'overlay';
            productCtx.globalAlpha = 0.55; 
            productCtx.drawImage(currentBaseImage, x, y, drawWidth, drawHeight);
        }
        
        // Reset composite
        productCtx.globalCompositeOperation = 'source-over';
        productCtx.globalAlpha = 1.0;
        
        if (textCanvas) requestRenderText();
    }

    // Attach Event Listeners
    function attachListeners(selector, stateKey) {
        const buttons = document.querySelectorAll(selector);
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state[stateKey] = btn.getAttribute('data-value');
                render();
            });
        });
    }

    attachListeners('.product-option', 'product');
    attachListeners('.color-btn', 'color');
    attachListeners('.size-option', 'size');
    attachListeners('.fit-option', 'fit');
    attachListeners('.placement-option', 'placement');

    if (textInput) {
        textInput.addEventListener('input', (e) => {
            state.text = e.target.value;
            render();
            if (textCanvas) requestRenderText();
        });
    }

    // Handle responsive resize
    if (textCanvas || productCanvas) {
        window.addEventListener('resize', () => {
            if (currentBaseImage) {
                renderGarmentColor();
            }
        });
    }

    // Render function updates the preview and summary
    function render() {
        // 1. Update Realistic Image
        let scaleSize = 1;
        if (state.size === 'S') scaleSize = 0.96;
        if (state.size === 'L') scaleSize = 1.04;
        if (state.size === 'XL') scaleSize = 1.08;

        let scaleFitX = 1;
        let scaleFitY = 1;
        if (state.fit === 'Oversized') {
            scaleFitX = 1.08;
            scaleFitY = 1.03;
        }

        // 2. Render Garment Color
        loadBaseImage(state.product, () => {
            renderGarmentColor();
        });
        
        // Apply transform to the canvas for realistic sizing/fit
        if (productCanvas) {
            productCanvas.style.transform = `scale(${scaleSize}) scaleX(${scaleFitX}) scaleY(${scaleFitY})`;
        }
        if (textCanvas) {
            textCanvas.style.transform = `scale(${scaleSize}) scaleX(${scaleFitX}) scaleY(${scaleFitY})`;
        }

        // 3. Update Summary
        summaryContainer.innerHTML = `
            <div class="summary-row">
                <span class="summary-label">Product</span>
                <span class="summary-value">${state.product}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Color</span>
                <span class="summary-value">${state.color}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Size</span>
                <span class="summary-value">${state.size}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Fit</span>
                <span class="summary-value">${state.fit}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Placement</span>
                <span class="summary-value">${state.placement}</span>
            </div>
            ${state.text ? `
            <div class="summary-row">
                <span class="summary-label">Print</span>
                <span class="summary-value">"${state.text}"</span>
            </div>` : ''}
        `;
    }

    function requestRenderText() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(renderTextCanvas, 50);
    }

    function renderTextCanvas() {
        if (!state.text || !currentBaseImage || currentBaseImage.naturalWidth === 0) {
            if (textCtx) textCtx.clearRect(0, 0, textCanvas.width, textCanvas.height);
            return;
        }

        const container = getContainerDimensions();
        const cWidth = container.width;
        const cHeight = container.height;
        
        if (cWidth === 0 || cHeight === 0) return;

        if (textCanvas.width !== cWidth || textCanvas.height !== cHeight) {
            textCanvas.width = cWidth;
            textCanvas.height = cHeight;
        }

        textCtx.clearRect(0, 0, cWidth, cHeight);

        const imgWidth = currentBaseImage.naturalWidth;
        const imgHeight = currentBaseImage.naturalHeight;
        const { drawWidth, drawHeight, x: imgX, y: imgY } = calculateContain(imgWidth, imgHeight, cWidth, cHeight);

        // 1. Draw text on a temporary offscreen canvas
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = cWidth;
        tempCanvas.height = cHeight;
        const tCtx = tempCanvas.getContext('2d', { willReadFrequently: true });

        tCtx.fillStyle = textColorMap[state.color];
        
        let fontSize = drawWidth * 0.09;
        let align = 'center';
        let textX = imgX + drawWidth * 0.5;
        let textY = imgY + drawHeight * 0.38;
        let rotation = 0;

        if (state.product === 'Hoodie') textY = imgY + drawHeight * 0.42;
        if (state.product === 'T-Shirt') textY = imgY + drawHeight * 0.36;
        if (state.product === 'Jacket') textY = imgY + drawHeight * 0.34;

        if (state.placement === 'Left Chest') {
            textX = imgX + drawWidth * 0.65;
            textY = imgY + drawHeight * 0.36;
            fontSize = drawWidth * 0.035;
            if (state.product === 'Hoodie') textY = imgY + drawHeight * 0.40;
        } else if (state.placement === 'Sleeve') {
            textX = imgX + drawWidth * 0.22;
            textY = imgY + drawHeight * 0.55;
            fontSize = drawWidth * 0.035;
            rotation = -65 * Math.PI / 180;
        } else if (state.placement === 'Back Center') {
            // Emulate back placement
        }

        tCtx.font = `800 ${fontSize}px "Inter", sans-serif`;
        tCtx.textAlign = align;
        tCtx.textBaseline = 'middle';

        tCtx.save();
        tCtx.translate(textX, textY);
        tCtx.rotate(rotation);
        tCtx.fillText(state.text.toUpperCase(), 0, 0);
        tCtx.restore();

        const textData = tCtx.getImageData(0, 0, cWidth, cHeight);

        // 2. Extract underlying garment pixel data
        const imgCanvas = document.createElement('canvas');
        imgCanvas.width = cWidth;
        imgCanvas.height = cHeight;
        const imgCtx = imgCanvas.getContext('2d', { willReadFrequently: true });
        imgCtx.drawImage(currentBaseImage, imgX, imgY, drawWidth, drawHeight);
        const imgData = imgCtx.getImageData(0, 0, cWidth, cHeight);

        // 3. Apply displacement and texture map
        const outData = textCtx.createImageData(cWidth, cHeight);
        
        let hasContent = false;
        
        for (let py = 0; py < cHeight; py++) {
            for (let px = 0; px < cWidth; px++) {
                const idx = (py * cWidth + px) * 4;
                if (textData.data[idx+3] > 0) {
                    hasContent = true;
                    // Calculate luminance of the garment pixel
                    const lum = (imgData.data[idx]*0.299 + imgData.data[idx+1]*0.587 + imgData.data[idx+2]*0.114);
                    
                    // Displace text pixel coordinates based on luminance
                    const displaceY = ((lum / 255) - 0.5) * (drawWidth * 0.012);
                    const displaceX = ((lum / 255) - 0.5) * (drawWidth * 0.005);
                    
                    const srcY = Math.min(cHeight-1, Math.max(0, Math.round(py + displaceY)));
                    const srcX = Math.min(cWidth-1, Math.max(0, Math.round(px + displaceX)));
                    const srcIdx = (srcY * cWidth + srcX) * 4;
                    
                    // Copy color from original text
                    outData.data[idx] = textData.data[srcIdx];
                    outData.data[idx+1] = textData.data[srcIdx+1];
                    outData.data[idx+2] = textData.data[srcIdx+2];
                    
                    // Modulate opacity based on garment shadows for realistic texture blending
                    const shadowBlend = 0.5 + 0.5 * (lum / 255);
                    let textOpacity = 0.95;
                    
                    if (state.placement === 'Back Center' && state.product === 'Jacket') {
                        textOpacity = 0.4;
                    }
                    
                    // Blend alpha channel
                    outData.data[idx+3] = textData.data[srcIdx+3] * shadowBlend * textOpacity;
                }
            }
        }
        
        if (hasContent) {
            textCtx.putImageData(outData, 0, 0);
        }

        // 4. Update CSS mix-blend-mode for the correct contrast
        textCanvas.className = 'custom-text-canvas';
        if (textColorMap[state.color] === '#111111') {
            textCanvas.classList.add('blend-dark');
        } else {
            textCanvas.classList.add('blend-light');
        }
    }


    // Initial render
    render();

    // Handle Add to Cart
    const addCustomBtn = document.querySelector('.add-custom-btn');
    if (addCustomBtn) {
        addCustomBtn.addEventListener('click', () => {
            const product = {
                id: 'custom-' + Date.now(),
                name: `Custom ${state.color} ${state.product}`,
                price: 3499,
                size: state.size,
                fit: state.fit,
                customText: state.text,
                placement: state.placement,
                image: 'custom-placeholder'
            };
            
            if (typeof addToCart === 'function') {
                addToCart(product);
            }
            
            const originalText = addCustomBtn.textContent;
            addCustomBtn.textContent = 'ADDED TO CART';
            addCustomBtn.style.background = '#4caf50';
            addCustomBtn.style.color = '#fff';
            setTimeout(() => {
                addCustomBtn.textContent = originalText;
                addCustomBtn.style.background = '';
                addCustomBtn.style.color = '';
            }, 1500);
        });
    }
});

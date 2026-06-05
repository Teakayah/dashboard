/**
 * Automatically wraps all `<canvas>` elements on the page in a `.chart-container`
 * and injects a "Full Screen" toggle button.
 *
 * This enables responsive, full-viewport chart viewing. When toggled, it applies
 * the `.chart-fullscreen` class to the container and blocks body scrolling.
 * It also triggers a global `resize` event to force Chart.js to redraw
 * according to the new container dimensions.
 */
(function() {
  function initFullscreen() {
    const canvases = document.querySelectorAll('canvas');
    canvases.forEach(canvas => {
      if (canvas.closest('.chart-container')) return;

      const container = document.createElement('div');
      container.className = 'chart-container';
      canvas.parentNode.insertBefore(container, canvas);
      container.appendChild(canvas);

      const btn = document.createElement('button');
      btn.className = 'fullscreen-btn';
      btn.textContent = '⛶';
      btn.title = 'Full Screen';
      btn.setAttribute('aria-label', 'Enter Full Screen');
      container.appendChild(btn);

      btn.addEventListener('click', () => {
        const isFull = container.classList.toggle('chart-fullscreen');
        btn.textContent = isFull ? '✕' : '⛶';
        btn.setAttribute('aria-label', isFull ? 'Exit Full Screen' : 'Enter Full Screen');
        
        // Trigger resize event for Chart.js
        window.dispatchEvent(new Event('resize'));
        
        if (isFull) {
          document.body.style.overflow = 'hidden';
        } else {
          document.body.style.overflow = '';
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFullscreen);
  } else {
    initFullscreen();
  }
})();

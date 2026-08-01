/**
 * Automatically wraps all <canvas> elements on the page with a container
 * and injects a "Full Screen" toggle button.
 *
 * This script is intended to be included globally. It relies on specific CSS
 * classes (`chart-container`, `chart-fullscreen`, `fullscreen-btn`) defined in
 * `theme.css` to handle the actual visual transitions and layout.
 */
(function() {
  /**
   * Scans the DOM for unwrapped <canvas> elements, wraps them in a
   * `.chart-container`, and appends a fullscreen toggle button.
   *
   * Binds click handlers that toggle the `.chart-fullscreen` class and dispatch
   * a global `resize` event to force Chart.js to re-render at the new dimensions.
   */
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

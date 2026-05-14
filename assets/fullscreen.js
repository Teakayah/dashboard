(function() {
  /**
   * Initializes fullscreen functionality for all Chart.js canvas elements on the page.
   * Wraps isolated canvases in a `.chart-container`, injects a toggle button, and handles the
   * fullscreen CSS state alongside forcing a Chart.js resize event.
   *
   * This ensures charts automatically resize and remain visible when entering/exiting fullscreen mode.
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

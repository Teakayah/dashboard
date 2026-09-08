(function() {
  /**
   * Initializes a fullscreen toggle for all unguarded <canvas> elements on the page.
   * Wraps standalone canvases in a container and injects a button that toggles a
   * 'chart-fullscreen' class. This provides an accessible, immersive viewing mode
   * for data visualizations like Chart.js, explicitly triggering window resize
   * events to force chart recalculations upon toggling.
   */
  function wrapCanvas(canvas) {
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
  }

  function initFullscreen() {
    document.querySelectorAll('canvas').forEach(wrapCanvas);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.addedNodes) {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeName === 'CANVAS') {
              wrapCanvas(node);
            } else if (node.querySelectorAll) {
              node.querySelectorAll('canvas').forEach(wrapCanvas);
            }
          });
        }
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFullscreen);
  } else {
    initFullscreen();
  }
})();

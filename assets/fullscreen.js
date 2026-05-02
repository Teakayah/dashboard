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
      btn.innerHTML = '⛶';
      btn.title = 'Full Screen';
      container.appendChild(btn);

      btn.addEventListener('click', () => {
        const isFull = container.classList.toggle('chart-fullscreen');
        btn.innerHTML = isFull ? '✕' : '⛶';
        
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

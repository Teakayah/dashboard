function showToast(message) {
    let toast = document.getElementById('toast-notification');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-notification';
        toast.setAttribute('role', 'alert');
        toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; background: #333; color: white; padding: 12px 24px; border-radius: 8px; font-size: 14px; z-index: 10000; box-shadow: 0 4px 6px rgba(0,0,0,0.1); opacity: 0; transition: opacity 0.3s;';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';

    if (toast.timeoutId) {
        clearTimeout(toast.timeoutId);
    }

    toast.timeoutId = setTimeout(() => {
        toast.style.opacity = '0';
    }, 4000);
}
window.showToast = showToast;

import { showToast } from './utils.js';

let queryHistory = JSON.parse(localStorage.getItem('dz_query_history') || '[]');

/**
 * Returns the current list of saved query strings.
 * @returns {Array<string>}
 */
export function getQueryHistory() {
    return queryHistory;
}

/**
 * Adds a successfully executed SQL query to the local storage history.
 * Maintains a maximum of 10 recent unique queries.
 *
 * @param {string} sql - The SQL query string to record.
 * @param {HTMLElement} container - The container element to render chips into.
 * @param {HTMLInputElement|HTMLTextAreaElement} sqlInput - The SQL input element.
 */
export function addToHistory(sql, container, sqlInput) {
    const trimmed = sql.trim();
    if (!trimmed) return;
    queryHistory = [trimmed, ...queryHistory.filter(q => q !== trimmed)].slice(0, 10);
    localStorage.setItem('dz_query_history', JSON.stringify(queryHistory));
    renderHistory(container, sqlInput);
}

/**
 * Renders the user's recent SQL queries as clickable chips in the UI.
 *
 * @param {HTMLElement} container - The DOM container for query chips.
 * @param {HTMLInputElement|HTMLTextAreaElement} sqlInput - The input element to populate on click.
 */
export function renderHistory(container, sqlInput) {
    if (!container) return;
    container.textContent = '';
    if (queryHistory.length === 0) return;

    const label = document.createElement('span');
    label.textContent = 'Recent:';
    label.style.fontSize = '0.7rem';
    label.style.color = 'var(--text-muted)';
    label.style.marginRight = '8px';
    container.appendChild(label);

    queryHistory.forEach(sql => {
        const chip = document.createElement('button');
        chip.className = 'history-chip';
        chip.style.fontFamily = 'inherit';
        chip.style.fontSize = 'inherit';
        chip.style.textAlign = 'left';
        chip.textContent = sql;
        chip.title = sql;
        chip.setAttribute('aria-label', `Load recent query: ${sql}`);

        chip.onclick = () => {
            if (sqlInput) {
                sqlInput.value = sql;
                sqlInput.dispatchEvent(new Event('input'));
                sqlInput.focus();
                showToast('Loaded query from history', 'success');
            }
        };

        container.appendChild(chip);
    });
}

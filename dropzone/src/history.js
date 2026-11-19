import { showToast } from './utils.js';

let queryHistory = JSON.parse(localStorage.getItem('dz_query_history') || '[]');

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

const SAVED_QUERIES_KEY = 'dz_saved_queries';

/**
 * Loads the list of user-saved SQL queries from localStorage.
 *
 * @returns {Array<{id: string, name: string, sql: string}>}
 */
function loadSavedQueries() {
    try {
        const parsed = JSON.parse(localStorage.getItem(SAVED_QUERIES_KEY) || '[]');
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

/**
 * Persists a named SQL query in localStorage and re-renders the saved queries list.
 *
 * @param {string} name - User-chosen label for the saved query.
 * @param {string} sql - SQL query text.
 * @param {HTMLElement} container - Container element for saved query chips.
 * @param {HTMLInputElement|HTMLTextAreaElement} sqlInput - SQL input element.
 * @returns {boolean} True if saved, false if invalid.
 */
export function saveQuery(name, sql, container, sqlInput) {
    const cleanName = name.trim();
    const cleanSql = sql.trim();
    if (!cleanName || !cleanSql) return false;

    const existing = loadSavedQueries().filter(q => q.name.toLowerCase() !== cleanName.toLowerCase());
    const entry = {
        id: 'sq_' + Date.now().toString(36),
        name: cleanName,
        sql: cleanSql
    };
    const updated = [entry, ...existing].slice(0, 25);
    localStorage.setItem(SAVED_QUERIES_KEY, JSON.stringify(updated));
    renderSavedQueries(container, sqlInput);
    showToast(`Saved query "${cleanName}"`, 'success');
    return true;
}

/**
 * Deletes a saved query by ID and re-renders the saved queries list.
 *
 * @param {string} id - Saved query identifier.
 * @param {HTMLElement} container - Container element for saved query chips.
 * @param {HTMLInputElement|HTMLTextAreaElement} sqlInput - SQL input element.
 */
export function deleteSavedQuery(id, container, sqlInput) {
    const updated = loadSavedQueries().filter(q => q.id !== id);
    localStorage.setItem(SAVED_QUERIES_KEY, JSON.stringify(updated));
    renderSavedQueries(container, sqlInput);
    showToast('Removed saved query', 'success');
}

/**
 * Renders saved SQL queries as accessible chips with a delete button.
 *
 * @param {HTMLElement} container - Container element for saved query chips.
 * @param {HTMLInputElement|HTMLTextAreaElement} sqlInput - SQL input element.
 */
export function renderSavedQueries(container, sqlInput) {
    if (!container) return;
    container.textContent = '';
    const saved = loadSavedQueries();
    if (saved.length === 0) {
        container.style.display = 'none';
        return;
    }
    container.style.display = 'flex';

    const label = document.createElement('span');
    label.textContent = 'Saved:';
    label.style.fontSize = '0.7rem';
    label.style.color = 'var(--text-muted)';
    label.style.marginRight = '4px';
    label.style.alignSelf = 'center';
    container.appendChild(label);

    saved.forEach(item => {
        const wrapper = document.createElement('span');
        wrapper.className = 'saved-query-item';

        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'history-chip saved-query-chip';
        chip.textContent = item.name;
        chip.title = item.sql;
        chip.setAttribute('aria-label', `Load saved query: ${item.name}`);
        chip.onclick = () => {
            if (sqlInput) {
                sqlInput.value = item.sql;
                sqlInput.dispatchEvent(new Event('input'));
                sqlInput.focus();
                showToast(`Loaded saved query "${item.name}"`, 'success');
            }
        };

        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'saved-query-delete';
        delBtn.textContent = '×';
        delBtn.setAttribute('aria-label', `Delete saved query: ${item.name}`);
        delBtn.title = `Delete "${item.name}"`;
        delBtn.onclick = () => deleteSavedQuery(item.id, container, sqlInput);

        wrapper.appendChild(chip);
        wrapper.appendChild(delBtn);
        container.appendChild(wrapper);
    });
}

/**
 * Escapes double quotes in identifiers (like table or column names)
 * to prevent SQL injection or syntax errors when constructing dynamic queries.
 *
 * @param {string} str - The identifier string to escape
 * @returns {string} The escaped identifier string
 */
export function escapeId(str) {
    return String(str).replace(/"/g, '""');
}

/**
 * Safely converts an Arrow table result into a plain array of JavaScript objects.
 * DuckDB-Wasm returns query results as Apache Arrow tables wrapped in Proxy objects.
 * Attempting to pass these proxies directly to UI components (like Grid.js) or standard
 * JSON serializers crashes due to unhandled ownKeys proxy traps. This function extracts
 * the rows and explicitly converts BigInt values to strings to prevent serialization errors.
 *
 * @param {import('@duckdb/duckdb-wasm').Table} result
 * @returns {Array<Object>}
 */
export function getRows(result) {
    if (!result || !result.schema) return [];

    let hasBigInt = false;
    const bigIntCols = [];
    for (const f of result.schema.fields) {
        if (f.type && (f.type.bitWidth === 64 || String(f.type).match(/Int64|Timestamp|Time64|Decimal/i))) {
            hasBigInt = true;
            bigIntCols.push(f.name);
        }
    }

    const numRows = result.numRows;

    // Performance optimization: Use Arrow's native .toArray() to extract objects first,
    // and eagerly convert the row Proxy into a plain JavaScript object using .toJSON().
    // This completely bypasses the heavy proxy getter trap overhead for every cell.
    const rawRows = result.toArray();
    const rows = new Array(numRows);

    if (hasBigInt) {
        const numBigIntCols = bigIntCols.length;
        for (let i = 0; i < numRows; i++) {
            const rawObj = rawRows[i];
            const rowObjPlain = typeof rawObj?.toJSON === 'function' ? rawObj.toJSON() : (typeof rawObj === 'object' && rawObj !== null ? {...rawObj} : rawObj);

            // Fast path: Only iterate the known BigInt columns instead of all fields.
            for (let j = 0; j < numBigIntCols; j++) {
                const field = bigIntCols[j];
                const val = rowObjPlain[field];
                if (typeof val === 'bigint') {
                    rowObjPlain[field] = val.toString();
                }
            }
            rows[i] = rowObjPlain;
        }
    } else {
        for (let i = 0; i < numRows; i++) {
            const rawObj = rawRows[i];
            rows[i] = typeof rawObj?.toJSON === 'function' ? rawObj.toJSON() : rawObj;
        }
    }
    return rows;
}

/**
 * Trigger a browser download for an object or data URL.
 *
 * @param {string} url - URL containing the download payload.
 * @param {string} filename - Suggested file name.
 */
export function triggerDownload(url, filename) {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
}

/**
 * Utility to clear and populate a <select> element.
 * @param {HTMLSelectElement} select - The select element to populate.
 * @param {Array<string|Object>} options - Array of values or column objects.
 * @param {string} [defaultMsg] - Optional default disabled option.
 */
export function populateSelect(select, options, defaultMsg) {
    const currentVal = select.value;
    select.textContent = '';

    if (defaultMsg) {
        select.add(new Option(defaultMsg, '', true, true));
    }

    options.forEach(item => {
        if (typeof item === 'object') {
            select.add(new Option(`${item.column_name} (${item.column_type})`, item.column_name));
        } else {
            select.add(new Option(item, item));
        }
    });

    if (!defaultMsg && options.some(opt => typeof opt === 'object' ? opt.column_name === currentVal : opt === currentVal)) {
        select.value = currentVal;
    }
}

/**
 * Displays a temporary, accessible error or informational toast notification
 * at the bottom right of the viewport. Automatically dismisses after 5 seconds.
 *
 * @param {string} msg - The message text to display.
 * @param {string} [type='error'] - The type of toast ('error' or 'success').
 */
export function showToast(msg, type = 'error') {
    const panel = document.createElement('div');
    panel.textContent = msg;
    panel.setAttribute('role', 'alert');
    panel.setAttribute('aria-live', 'assertive');
    const bgColor = type === 'success' ? '#10b981' : '#ef4444';
    panel.style.cssText = `position:fixed;bottom:20px;right:20px;background:${bgColor};color:#fff;padding:12px 20px;border-radius:8px;z-index:9999;box-shadow:0 4px 6px rgba(0,0,0,0.1);`;
    document.body.appendChild(panel);
    setTimeout(() => { panel.remove(); }, 5000);
}

/**
 * Inserts text at the current cursor position within an input or textarea element.
 *
 * @param {HTMLInputElement|HTMLTextAreaElement} myField - The target input field.
 * @param {string} myValue - The text to insert.
 */
export function insertAtCursor(myField, myValue) {
    if (myField.selectionStart !== undefined) {
        const startPos = myField.selectionStart;
        const endPos = myField.selectionEnd;
        myField.value = myField.value.substring(0, startPos)
            + myValue
            + myField.value.substring(endPos, myField.value.length);
        myField.selectionStart = startPos + myValue.length;
        myField.selectionEnd = startPos + myValue.length;
    } else {
        myField.value += myValue;
    }
    myField.focus();
    myField.dispatchEvent(new Event('input'));
    if (myField.id === 'sql-input') {
        let displayValue = myValue;
        if (displayValue.length > 30) {
            displayValue = displayValue.substring(0, 30) + '...';
        }
        showToast('Inserted ' + displayValue + ' into query editor', 'success');
    }
}

/**
 * Wraps an async function with loading overlay state management.
 *
 * @param {string} errorPrefix - Prefix for the error toast message.
 * @param {Function} asyncFn - The async function to execute.
 */
export function showEmptyState(containerEl, title, message, svgPath) {
    containerEl.textContent = '';
    const emptyDiv = document.createElement('div');
    emptyDiv.className = 'empty';
    emptyDiv.style.cssText = 'text-align: center; padding: 40px 20px;';

    const svgNs = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNs, 'svg');
    svg.setAttribute('aria-hidden', 'true');
    svg.style.cssText = 'width: 48px; height: 48px; margin: 0 auto 16px; opacity: 0.5; display: block;';
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('viewBox', '0 0 24 24');

    const path = document.createElementNS(svgNs, 'path');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('d', svgPath);
    svg.appendChild(path);
    emptyDiv.appendChild(svg);

    const h3 = document.createElement('h3');
    h3.style.cssText = 'font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 0 0 8px 0;';
    h3.textContent = title;
    emptyDiv.appendChild(h3);

    const p = document.createElement('p');
    p.style.cssText = 'font-size: 0.9rem; margin: 0; color: var(--text-muted);';
    p.textContent = message;
    emptyDiv.appendChild(p);

    containerEl.appendChild(emptyDiv);
}

export async function withLoading(errorPrefix, asyncFn) {
    const loadingOverlay = document.getElementById('loading');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    document.body.setAttribute('aria-busy', 'true');
    try {
        await asyncFn();
    } catch (err) {
        console.error(err);
        showToast(errorPrefix + ': ' + err.message);
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        document.body.removeAttribute('aria-busy');
    }
}

import { escapeId, getRows, triggerDownload, showToast } from './utils.js';

/**
 * Destroys all Chart.js instances inside a given container to prevent memory leaks.
 *
 * @param {HTMLElement} container - The DOM element containing canvas elements.
 */
export function destroyCharts(container) {
    if (!container || !window.Chart) return;
    const canvases = container.querySelectorAll('canvas');
    canvases.forEach(canvas => {
        const chart = window.Chart.getChart(canvas);
        if (chart) chart.destroy();
    });
}

/**
 * Initializes and renders a Chart.js instance onto a specific canvas element.
 * Automatically applies responsive defaults.
 *
 * @param {string} id - The ID of the target canvas element.
 * @param {string} type - The Chart.js chart type (e.g., 'line', 'bar', 'scatter').
 * @param {Object} data - The Chart.js data configuration object.
 * @param {Object} [options={}] - Additional Chart.js options to merge with defaults.
 */
export function renderChart(id, type, data, options = {}) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    if (window.Chart) {
        const existingChart = window.Chart.getChart(canvas);
        if (existingChart) existingChart.destroy();
    }
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: type !== 'bar' } },
            ...options
        }
    });
}

/**
 * Creates a DOM container for an instant chart preview and invokes a render function
 * to populate it. Automatically provides a header with a title and a download button.
 *
 * @param {string} title - The title displayed in the card header.
 * @param {Function} renderFn - A callback function invoked with the newly generated canvas ID.
 * @param {HTMLElement} [container] - Container element, defaults to #instant-previews.
 */
export function createPreviewCard(title, renderFn, container = document.getElementById('instant-previews')) {
    if (!container) return;
    const id = 'chart-' + Math.random().toString(36).substr(2, 9);
    const card = document.createElement('div');
    card.className = 'preview-card';
    card.style.position = 'relative';

    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    header.style.marginBottom = '10px';

    const h3 = document.createElement('h3');
    h3.textContent = title;
    h3.style.margin = '0';
    header.appendChild(h3);

    const downloadBtn = document.createElement('button');
    downloadBtn.textContent = '💾 PNG';
    downloadBtn.setAttribute('aria-label', `Download ${title} as PNG`);
    downloadBtn.title = `Download ${title} as PNG`;
    downloadBtn.style.padding = '2px 6px';
    downloadBtn.style.fontSize = '0.7rem';
    downloadBtn.onclick = () => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const url = canvas.toDataURL('image/png');
        triggerDownload(url, title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.png');
        showToast(`Downloaded ${title} as PNG`, 'success');
    };
    header.appendChild(downloadBtn);

    card.appendChild(header);

    const canvas = document.createElement('canvas');
    canvas.id = id;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', `Chart preview: ${title}`);
    card.appendChild(canvas);

    container.appendChild(card);
    renderFn(id);
}

/**
 * Automatically generates visualization previews for a given dataset table.
 * Analyzes the table schema to identify date, numeric, and text columns,
 * then runs heuristic SQL queries to detect and render:
 *  1. Time-series trends (if date + numeric columns exist)
 *  2. Highest correlation pairs (tests up to 10 pairs of numeric columns)
 *  3. Category distributions (if text + numeric columns exist)
 *
 * @param {string} tableName - The name of the DuckDB table to analyze.
 * @param {Object} conn - The active DuckDB connection.
 * @param {Function} getSchemaFn - Function taking tableName and returning schema result promise.
 * @param {HTMLElement} [previewsContainer] - Container for preview cards.
 */
export async function generateInstantCharts(tableName, conn, getSchemaFn, previewsContainer = document.getElementById('instant-previews')) {
    if (!conn || !tableName) return;
    const schemaResult = await getSchemaFn(tableName);
    const columns = getRows(schemaResult);
    const numericCols = columns.filter(c =>
        ['DOUBLE', 'FLOAT', 'BIGINT', 'INTEGER', 'DECIMAL', 'HUGEINT'].includes(c.column_type.split('(')[0].toUpperCase())
    ).map(c => c.column_name);

    const textCols = columns.filter(c =>
        ['VARCHAR', 'TEXT', 'DATE', 'TIMESTAMP'].includes(c.column_type.toUpperCase())
    ).map(c => c.column_name);

    const dateCols = columns.filter(c =>
        ['DATE', 'TIMESTAMP', 'TIME'].includes(c.column_type.toUpperCase()) ||
        c.column_name.toLowerCase().includes('date') ||
        c.column_name.toLowerCase().includes('year')
    ).map(c => c.column_name);

    if (numericCols.length === 0) return;

    // 1. Time-Series Trend detection
    if (dateCols.length > 0 && numericCols.length > 0) {
        const dCol = dateCols[0];
        const nCol = numericCols[0];
        createPreviewCard(`Trend: ${nCol} over ${dCol}`, async (canvasId) => {
            const result = await conn.query(`
                SELECT "${escapeId(dCol)}" as date, AVG("${escapeId(nCol)}") as val
                FROM "${escapeId(tableName)}"
                WHERE "${escapeId(dCol)}" IS NOT NULL AND "${escapeId(nCol)}" IS NOT NULL
                GROUP BY 1 ORDER BY 1 ASC LIMIT 100
            `);
            const rows = getRows(result);
            renderChart(canvasId, 'line', {
                labels: rows.map(r => r.date),
                datasets: [{
                    label: `Avg ${nCol}`,
                    data: rows.map(r => r.val),
                    borderColor: '#4bc0c0',
                    tension: 0.1,
                    fill: false
                }]
            });
        }, previewsContainer);
    }

    // 2. Correlation detection
    if (numericCols.length >= 2) {
        try {
            let bestPair = [numericCols[0], numericCols[1]];
            let maxCorr = 0;

            const colsToCheck = numericCols.slice(0, 5);
            const corrExprs = [];
            const pairs = [];
            for (let i = 0; i < colsToCheck.length; i++) {
                for (let j = i + 1; j < colsToCheck.length; j++) {
                    const c1 = colsToCheck[i];
                    const c2 = colsToCheck[j];
                    corrExprs.push(`corr("${escapeId(c1)}", "${escapeId(c2)}") as "c_${i}_${j}"`);
                    pairs.push({ c1, c2, alias: `c_${i}_${j}` });
                }
            }

            if (corrExprs.length > 0) {
                const corrQuery = `SELECT ${corrExprs.join(', ')} FROM "${escapeId(tableName)}"`;
                const corrResult = await conn.query(corrQuery);
                const row = getRows(corrResult)[0] || {};

                for (const pair of pairs) {
                    const corr = Math.abs(row[pair.alias] || 0);
                    if (corr > maxCorr) {
                        maxCorr = corr;
                        bestPair = [pair.c1, pair.c2];
                    }
                }
            }

            createPreviewCard(`Correlation: ${bestPair[0]} vs ${bestPair[1]}`, async (canvasId) => {
                const result = await conn.query(`SELECT "${escapeId(bestPair[0])}" as x, "${escapeId(bestPair[1])}" as y FROM "${escapeId(tableName)}" WHERE x IS NOT NULL AND y IS NOT NULL LIMIT 500`);
                const rows = getRows(result);
                renderChart(canvasId, 'scatter', {
                    datasets: [{
                        label: `${bestPair[0]} vs ${bestPair[1]}`,
                        data: rows.map(r => ({x: r.x, y: r.y})),
                        backgroundColor: '#1d4ed8'
                    }]
                }, {
                    scales: { x: { title: {display: true, text: bestPair[0]} }, y: { title: {display: true, text: bestPair[1]} } }
                });
            }, previewsContainer);
        } catch (e) {
            console.warn('Correlation check failed', e);
        }
    }

    // 3. Category Distribution
    if (textCols.length > 0 && numericCols.length > 0) {
        const tCol = textCols[0];
        const nCol = numericCols[0];
        createPreviewCard(`Distribution: ${nCol} by ${tCol}`, async (canvasId) => {
            const result = await conn.query(`
                SELECT "${escapeId(tCol)}" as label, AVG("${escapeId(nCol)}") as value
                FROM "${escapeId(tableName)}"
                GROUP BY 1 
                ORDER BY value DESC 
                LIMIT 10
            `);
            const rows = getRows(result);
            renderChart(canvasId, 'bar', {
                labels: rows.map(r => r.label),
                datasets: [{
                    label: `Average ${nCol}`,
                    data: rows.map(r => r.value),
                    backgroundColor: '#ff6384'
                }]
            });
        }, previewsContainer);
    }
}

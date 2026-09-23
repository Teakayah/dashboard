import { SAMPLE_DATA } from './src/config.js';
import {
    escapeId,
    getRows,
    triggerDownload,
    populateSelect,
    insertAtCursor,
    showToast,
    withLoading
} from './src/utils.js';
import { addToHistory, renderHistory } from './src/history.js';
import {
    destroyCharts,
    renderChart,
    createPreviewCard,
    generateInstantCharts
} from './src/charts.js';
import {
    initDuckDB,
    getDb,
    getConnection,
    loadedTables,
    tableSchemaCache,
    getTableSchemaCached,
    getCurrentTableName,
    setCurrentTableName,
    clearLoadedTables
} from './src/db.js';

// DOM Elements
const statusEl = document.getElementById('status');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const sqlInput = document.getElementById('sql-input');
const runBtn = document.getElementById('run-query');
const clearBtn = document.getElementById('clear-data');
const downloadBtn = document.getElementById('download-csv');
const copyJsonBtn = document.getElementById('copy-json');
const loadSamplesBtn = document.getElementById('load-samples');
const exportDbBtn = document.getElementById('export-db');
const recipeSelect = document.getElementById('query-recipes');
const schemaDisplay = document.getElementById('schema-display');
const loadingOverlay = document.getElementById('loading');
const previewsContainer = document.getElementById('instant-previews');
const remoteDeltaUrl = document.getElementById('remote-delta-url');
const loadRemoteDeltaBtn = document.getElementById('load-remote-delta');
const initProgressContainer = document.getElementById('init-progress-container');
const initProgress = document.getElementById('init-progress');
const queryHistoryEl = document.getElementById('query-history');

// Join Assistant Elements
const joinAssistant = document.getElementById('join-assistant');
const joinTableA = document.getElementById('join-table-a');
const joinTableB = document.getElementById('join-table-b');
const joinCol = document.getElementById('join-col');
const generateJoinBtn = document.getElementById('generate-join');

// Chart Builder Elements
const chartBuilder = document.getElementById('chart-builder');
const chartType = document.getElementById('chart-type');
const chartXCol = document.getElementById('chart-x-col');
const chartYCol = document.getElementById('chart-y-col');
const generateChartBtn = document.getElementById('generate-chart');

let lastResult = null;
let gridInstance = null;

/**
 * Updates the DuckDB-Wasm initialization progress bar in the UI.
 * The progress bar is automatically hidden when progress is 0% or 100%.
 *
 * @param {number} percent - The current loading progress (0 to 100).
 */
function setProgress(percent) {
    if (percent > 0 && percent < 100) {
        initProgressContainer.style.display = 'block';
    } else {
        initProgressContainer.style.display = 'none';
    }
    initProgress.style.width = `${percent}%`;
}

// Initial history render
renderHistory(queryHistoryEl, sqlInput);

/**
 * Restores the Analytical Drop-Zone UI state after a browser reload.
 * Queries the DuckDB instance's information_schema to discover tables that were
 * persisted across sessions (e.g., within OPFS).
 */
async function restoreState() {
    const conn = getConnection();
    if (!conn) return;
    try {
        const tablesResult = await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'");
        const tables = getRows(tablesResult).map(r => r.table_name);

        if (tables.length > 0) {
            loadedTables.clear();
            tables.forEach(t => loadedTables.add(t));
            setCurrentTableName(tables[tables.length - 1]);
            statusEl.textContent = `Restored ${tables.length} table(s)`;

            schemaDisplay.textContent = '';
            // Performance optimization: Fetch schemas concurrently to eliminate
            // redundant sequential IPC roundtrips across the WebWorker boundary.
            await Promise.all(tables.map(t => getTableSchemaCached(t)));
            for (const table of tables) {
                await displayTableSchema(table);
            }

            sqlInput.value = `SELECT * FROM "${escapeId(getCurrentTableName())}" LIMIT 100`;
            sqlInput.dispatchEvent(new Event('input'));

            updateJoinUI();
            updateChartBuilderUI();
            updateConsoleActionsUI();
        }
    } catch (err) {
        console.warn('Failed to restore state:', err);
    }
}

/**
 * Retrieves and renders the schema for a specified DuckDB table within the UI.
 * For each column, it creates an interactive element that, when clicked:
 * 1. Inserts the column name into the SQL editor.
 * 2. Asynchronously profiles the column data (fetching min, max, count).
 * 3. Renders a mini Chart.js bar chart visualizing the top 10 most frequent values.
 *
 * @param {string} tableName - The name of the DuckDB table to describe and profile.
 */
async function displayTableSchema(tableName) {
    const schemaResult = await getTableSchemaCached(tableName);
    const statsContainer = document.createElement('div');
    statsContainer.style.fontSize = '0.75rem';
    statsContainer.style.marginTop = '4px';
    statsContainer.style.color = '#666';
    statsContainer.style.fontStyle = 'italic';
    statsContainer.style.minHeight = '1.2em';

    // Performance optimization: Cache profiling promises to prevent redundant queries.
    const profileCache = new Map();

    const cols = getRows(schemaResult).map(r => {
        const btn = document.createElement('button');
        btn.className = 'clickable-col';
        btn.style.cursor = 'pointer';
        btn.style.textDecoration = 'underline';
        btn.style.marginRight = '8px';
        btn.style.color = 'var(--primary)';
        btn.style.borderRadius = '4px';
        btn.style.padding = '2px 4px';
        btn.style.background = 'transparent';
        btn.style.border = 'none';
        btn.style.fontFamily = 'inherit';
        btn.style.fontSize = 'inherit';
        btn.style.transition = 'background-color 0.2s';
        btn.style.textAlign = 'left';
        btn.textContent = `${r.column_name} (${r.column_type})`;
        btn.setAttribute('aria-label', `Insert column ${r.column_name} into SQL editor`);

        const triggerAction = async (e) => {
            e.stopPropagation();
            insertAtCursor(sqlInput, `"${escapeId(r.column_name)}"`);
            statusEl.textContent = `Inserted column ${r.column_name}`;
            showToast(`Inserted column ${r.column_name}`, 'success');

            // Profiling logic
            try {
                const existingCanvas = statsContainer.querySelector('canvas');
                if (existingCanvas && window.Chart) {
                    const chart = window.Chart.getChart(existingCanvas);
                    if (chart) chart.destroy();
                }

                statsContainer.textContent = 'Calculating stats...';

                if (!profileCache.has(r.column_name)) {
                    const conn = getConnection();
                    const profilePromise = (async () => {
                        const [profilingResult, distResult] = await Promise.all([
                            conn.query(`SELECT MIN("${escapeId(r.column_name)}") as min_val, MAX("${escapeId(r.column_name)}") as max_val, COUNT("${escapeId(r.column_name)}") as count_val FROM "${escapeId(tableName)}"`),
                            conn.query(`SELECT "${escapeId(r.column_name)}" as val, count(*) as cnt FROM "${escapeId(tableName)}" GROUP BY 1 ORDER BY 2 DESC LIMIT 10`)
                        ]);
                        const stats = getRows(profilingResult)[0];
                        const distRows = getRows(distResult);
                        return { stats, distRows };
                    })();
                    profileCache.set(r.column_name, profilePromise);
                }

                const { stats, distRows } = await profileCache.get(r.column_name);

                destroyCharts(statsContainer);
                statsContainer.textContent = '';
                const text = document.createElement('div');
                text.textContent = `Stats for ${r.column_name}: Min: ${stats.min_val} | Max: ${stats.max_val} | Count: ${stats.count_val}`;
                statsContainer.appendChild(text);

                if (distRows.length > 0) {
                    const chartCont = document.createElement('div');
                    chartCont.className = 'mini-chart-container';
                    chartCont.style.height = '100px';
                    const canvas = document.createElement('canvas');
                    canvas.setAttribute('role', 'img');
                    canvas.setAttribute('aria-label', `Distribution chart for ${r.column_name}`);
                    chartCont.appendChild(canvas);
                    statsContainer.appendChild(chartCont);

                    new Chart(canvas, {
                        type: 'bar',
                        data: {
                            labels: distRows.map(dr => String(dr.val).substring(0, 15)),
                            datasets: [{
                                label: 'Frequency',
                                data: distRows.map(dr => dr.cnt),
                                backgroundColor: 'rgba(79, 142, 247, 0.6)'
                            }]
                        },
                        options: {
                            indexAxis: 'y',
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false }, title: { display: true, text: 'Top 10 Values', font: { size: 10 } } },
                            scales: {
                                x: { display: false },
                                y: { ticks: { font: { size: 8 } } }
                            }
                        }
                    });
                }
            } catch (err) {
                statsContainer.textContent = `Profiling failed: ${err.message}`;
            }
        };

        btn.onclick = triggerAction;
        btn.onkeydown = (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                triggerAction(e);
            }
        };

        return btn;
    });

    const tableDiv = document.createElement('div');
    tableDiv.style.marginBottom = '12px';
    const strong = document.createElement('strong');
    strong.textContent = `Table: ${tableName} `;
    tableDiv.appendChild(strong);
    cols.forEach(c => tableDiv.appendChild(c));
    tableDiv.appendChild(statsContainer);
    schemaDisplay.appendChild(tableDiv);
}

/**
 * Toggles and populates the Join Assistant UI based on the current state of loaded tables.
 */
function updateJoinUI() {
    if (loadedTables.size >= 2) {
        joinAssistant.style.display = 'flex';
        const tables = Array.from(loadedTables);

        populateSelect(joinTableA, tables);
        populateSelect(joinTableB, tables);

        // Ensure default different tables
        if (joinTableA.value === joinTableB.value && tables.length > 1) {
            joinTableB.selectedIndex = 1;
        }

        updateJoinColumns();
    } else {
        joinAssistant.style.display = 'none';
    }
}

/**
 * Dynamically queries the DuckDB schema to populate the join column dropdowns.
 */
async function updateJoinColumns() {
    const tableA = joinTableA.value;
    const tableB = joinTableB.value;
    if (!tableA || !tableB) return;

    try {
        const [schemaAResult, schemaBResult] = await Promise.all([
            getTableSchemaCached(tableA),
            getTableSchemaCached(tableB)
        ]);

        const colsA = new Set(getRows(schemaAResult).map(r => r.column_name));
        const colsB = getRows(schemaBResult).map(r => r.column_name);

        const sharedCols = colsB.filter(c => colsA.has(c));

        if (sharedCols.length === 0) {
            populateSelect(joinCol, [], 'No shared columns found');
        } else {
            populateSelect(joinCol, sharedCols, 'Select Common Column...');
        }
    } catch (err) {
        console.error('Error fetching columns for join:', err);
    }
}

/**
 * Updates the disabled state and tooltips of the console action buttons.
 */
function updateConsoleActionsUI() {
    const hasData = loadedTables.size > 0;

    const setBtnState = (btn, enabled, disabledTitle, enabledTitle = '') => {
        btn.disabled = !enabled;
        btn.title = enabled ? enabledTitle : disabledTitle;
    };

    setBtnState(recipeSelect, hasData, 'Requires loaded data');
    setBtnState(exportDbBtn, hasData, 'Requires loaded data');
    setBtnState(clearBtn, hasData, 'Requires loaded data');
}

/**
 * Initializes and populates the Chart Builder UI drop-downs.
 */
async function updateChartBuilderUI() {
    const currentTableName = getCurrentTableName();
    if (!currentTableName) {
        chartBuilder.style.display = 'none';
        return;
    }
    chartBuilder.style.display = 'flex';
    try {
        const schemaResult = await getTableSchemaCached(currentTableName);
        const cols = getRows(schemaResult);

        const numericCols = cols.filter(c => ['DOUBLE', 'FLOAT', 'BIGINT', 'INTEGER', 'DECIMAL', 'HUGEINT'].includes(c.column_type.split('(')[0].toUpperCase()));

        populateSelect(chartXCol, cols, 'Select X-Axis...');
        populateSelect(chartYCol, numericCols, 'Select Y-Axis (Numeric)...');
    } catch (err) {
        console.error('Error updating chart builder UI:', err);
    }
}

joinTableA.addEventListener('change', updateJoinColumns);
joinTableB.addEventListener('change', updateJoinColumns);

generateJoinBtn.addEventListener('click', () => {
    const a = joinTableA.value;
    const b = joinTableB.value;
    const col = joinCol.value;

    if (!a || !b || !col) {
        showToast('Please select both tables and a common column.');
        return;
    }

    if (a === b) {
        showToast('Please select two different tables to join.');
        return;
    }

    if (!loadedTables.has(a) || !loadedTables.has(b)) {
        showToast('Invalid table selection.');
        return;
    }

    const sql = `SELECT *\nFROM "${escapeId(a)}"\nJOIN "${escapeId(b)}" ON "${escapeId(a)}"."${escapeId(col)}" = "${escapeId(b)}"."${escapeId(col)}"\nLIMIT 100`;
    sqlInput.value = sql;
    sqlInput.dispatchEvent(new Event('input'));
    sqlInput.focus();
});

generateChartBtn.addEventListener('click', () => {
    const currentTableName = getCurrentTableName();
    const type = chartType.value;
    const xCol = chartXCol.value;
    const yCol = chartYCol.value;

    if (!xCol || !yCol) {
        showToast('Please select both X and Y axes.');
        return;
    }

    const title = `Custom ${type.toUpperCase()}: ${yCol} vs ${xCol}`;

    createPreviewCard(title, async (canvasId) => {
        try {
            if (!loadedTables.has(currentTableName)) {
                showToast('Invalid table reference.');
                return;
            }
            const isScatter = type === 'scatter';
            const sql = isScatter
                ? `SELECT "${escapeId(xCol)}" as x, "${escapeId(yCol)}" as y\nFROM "${escapeId(currentTableName)}"\nWHERE "${escapeId(xCol)}" IS NOT NULL AND "${escapeId(yCol)}" IS NOT NULL\nLIMIT 500`
                : `SELECT "${escapeId(xCol)}" as label, AVG("${escapeId(yCol)}") as value\nFROM "${escapeId(currentTableName)}"\nWHERE "${escapeId(xCol)}" IS NOT NULL AND "${escapeId(yCol)}" IS NOT NULL\nGROUP BY 1\nORDER BY 1 ASC\nLIMIT 100`;

            sqlInput.value = sql;
            sqlInput.dispatchEvent(new Event('input'));

            const conn = getConnection();
            const result = await conn.query(sql);
            const rows = getRows(result);

            const chartData = isScatter ? {
                datasets: [{
                    label: `${xCol} vs ${yCol}`,
                    data: rows.map(r => ({x: r.x, y: r.y})),
                    backgroundColor: '#ff9f40'
                }]
            } : {
                labels: rows.map(r => r.label),
                datasets: [{
                    label: (type === 'line' ? `Avg ${yCol}` : `Average ${yCol}`),
                    data: rows.map(r => r.value),
                    backgroundColor: (type === 'line' ? 'transparent' : '#ff9f40'),
                    borderColor: '#ff9f40',
                    tension: 0.1,
                    fill: (type === 'bar')
                }]
            };

            const chartOptions = isScatter ? {
                scales: { x: { title: {display: true, text: xCol} }, y: { title: {display: true, text: yCol} } }
            } : {};

            renderChart(canvasId, type, chartData, chartOptions);
        } catch (e) {
            console.error('Custom chart error', e);
            showToast('Error generating chart: ' + e.message);
        }
    }, previewsContainer);
});

// File drops & selection
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFiles(files);
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFiles(fileInput.files);
});

/**
 * Processes dropped or selected files.
 *
 * @param {FileList|Array<File>} files
 */
async function handleFiles(files) {
    destroyCharts(previewsContainer);
    previewsContainer.textContent = '';

    await withLoading('Error loading files', async () => {
        const fileGroups = {};
        const standaloneFiles = [];

        for (const file of files) {
            const relPath = file.webkitRelativePath || file.name;
            const pathParts = relPath.split('/');

            if (pathParts.length > 1) {
                const rootDir = pathParts[0];
                if (!fileGroups[rootDir]) fileGroups[rootDir] = [];
                fileGroups[rootDir].push(file);
            } else {
                standaloneFiles.push(file);
            }
        }

        for (const file of standaloneFiles) {
            await processFile(file, file.name);
        }

        for (const [dirName, dirFiles] of Object.entries(fileGroups)) {
            const isDelta = dirFiles.some(f => (f.webkitRelativePath || f.name).includes('_delta_log'));
            const tableName = dirName.replace(/[^a-zA-Z0-9]/g, '_');

            const db = getDb();
            await Promise.all(dirFiles.map(async file => {
                const fullPath = file.webkitRelativePath || file.name;
                const buffer = await file.arrayBuffer();
                await db.registerFileBuffer(fullPath, new Uint8Array(buffer));
            }));

            if (isDelta) {
                if (!window.deltaSupported) {
                    showToast(`Delta Lake table detected in folder "${escapeId(dirName)}", but support is missing in this browser. Skipping.`);
                    continue;
                }
                setCurrentTableName(tableName);
                loadedTables.add(tableName);
                const escapedDirName = dirName.replace(/'/g, "''");
                const query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM delta_scan('${escapedDirName}')`;
                tableSchemaCache.delete(tableName);
                const conn = getConnection();
                await conn.query(query);
                await onTableLoaded(tableName);
            } else {
                for (const file of dirFiles) {
                    await processFile(file, file.webkitRelativePath || file.name);
                }
            }
        }

        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
        updateConsoleActionsUI();
    });
}

/**
 * Loads a single file into DuckDB-Wasm and registers it as a table.
 *
 * @param {File} file
 * @param {string} path
 */
async function processFile(file, path) {
    const tableName = file.name.replace(/[^a-zA-Z0-9]/g, '_');
    setCurrentTableName(tableName);
    loadedTables.add(tableName);

    const db = getDb();
    const conn = getConnection();
    const buffer = await file.arrayBuffer();
    await db.registerFileBuffer(path, new Uint8Array(buffer));

    let query;
    const ext = file.name.split('.').pop().toLowerCase();
    const escapedPath = path.replace(/'/g, "''");

    if (ext === 'parquet') {
        query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM read_parquet('${escapedPath}')`;
    } else if (ext === 'csv') {
        query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM read_csv_auto('${escapedPath}')`;
    } else if (ext === 'json') {
        query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM read_json_auto('${escapedPath}')`;
    } else {
        query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM '${escapedPath}'`;
    }

    tableSchemaCache.delete(tableName);
    await conn.query(query);
    await onTableLoaded(tableName);
}

/**
 * Orchestrates the UI updates immediately after a new table is registered in DuckDB.
 *
 * @param {string} tableName
 */
async function onTableLoaded(tableName) {
    if (loadedTables.size === 1) schemaDisplay.textContent = '';
    await displayTableSchema(tableName);
    // Fire-and-forget: Do not await instant chart generation so the critical UI path (populating the SQL input) is not blocked.
    generateInstantCharts(tableName, getConnection(), getTableSchemaCached, previewsContainer).catch(e => console.warn('Instant charts failed:', e));
    sqlInput.value = `SELECT * FROM "${escapeId(tableName)}" LIMIT 100`;
    sqlInput.dispatchEvent(new Event('input'));
}

recipeSelect.addEventListener('change', () => {
    const currentTableName = getCurrentTableName();
    if (!currentTableName) return;
    const recipe = recipeSelect.value.replace(/{{TABLE}}/g, `"${escapeId(currentTableName)}"`);
    sqlInput.value = recipe;
    sqlInput.dispatchEvent(new Event('input'));
    recipeSelect.selectedIndex = 0;
});

let sqlInputDebounceTimeout;
sqlInput.addEventListener('input', () => {
    clearTimeout(sqlInputDebounceTimeout);
    sqlInputDebounceTimeout = setTimeout(() => {
        if (sqlInput.value.trim().length > 0) {
            runBtn.disabled = false;
            runBtn.title = 'Run Query (Ctrl+Enter)';
        } else {
            runBtn.disabled = true;
            runBtn.title = 'Requires a valid query';
        }
    }, 150);
});

// Global shortcut: '/' focuses SQL input
document.addEventListener('keydown', (e) => {
    if (e.key === '/' &&
        document.activeElement !== sqlInput &&
        !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        sqlInput.focus();
    }
});

sqlInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (sqlInput.value.trim()) {
            runQuery();
        }
    }
});

runBtn.addEventListener('click', runQuery);

/**
 * Executes the SQL query from the editor against DuckDB-Wasm.
 */
async function runQuery() {
    const sql = sqlInput.value.trim();
    if (!sql) return;

    await withLoading('Query Error', async () => {
        const conn = getConnection();
        const start = performance.now();
        const result = await conn.query(sql);
        const duration = Math.round(performance.now() - start);

        lastResult = getRows(result);
        renderResults(lastResult);
        downloadBtn.disabled = false;
        downloadBtn.title = '';
        copyJsonBtn.disabled = false;
        copyJsonBtn.title = '';
        statusEl.textContent = `Query executed in ${duration}ms`;
        addToHistory(sql, queryHistoryEl, sqlInput);
    });
}

/**
 * Renders query results in Grid.js.
 *
 * @param {Array<Object>} rows
 */
function renderResults(rows) {
    const resultsContainer = document.getElementById('results');
    if (rows.length === 0) {
        if (gridInstance) {
            gridInstance.destroy();
            gridInstance = null;
        }
        resultsContainer.innerHTML = `
            <div class="empty" style="text-align: center; padding: 40px 20px;">
                <svg aria-hidden="true" style="width: 48px; height: 48px; margin: 0 auto 16px; opacity: 0.5; display: block;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 0 0 8px 0;">No results found</h3>
                <p style="font-size: 0.9rem; margin: 0; color: var(--text-muted);">Your query executed successfully but returned 0 rows. Try adjusting your SQL conditions.</p>
            </div>
        `;
        return;
    }
    const columns = Object.keys(rows[0]);

    if (gridInstance) {
        gridInstance.updateConfig({
            columns: columns.map(c => ({ id: c, name: c })),
            data: rows
        }).forceRender();
    } else {
        resultsContainer.textContent = '';
        gridInstance = new gridjs.Grid({
            columns: columns.map(c => ({ id: c, name: c })),
            data: rows,
            pagination: { limit: 10 },
            sort: true,
            search: true,
            resizable: true,
            style: { table: { 'white-space': 'nowrap' } }
        }).render(resultsContainer);
    }
}

downloadBtn.addEventListener('click', async () => {
    if (!lastResult || lastResult.length === 0) return;
    await withLoading('Export Error', async () => {
        const csvPath = 'export.csv';
        const userQuery = sqlInput.value.trim().replace(/;+$/, '');
        const conn = getConnection();
        const db = getDb();
        await conn.query(`COPY (${userQuery}) TO '${csvPath}' (HEADER, DELIMITER ',')`);

        const content = await db.copyFileToBuffer(csvPath);
        const blob = new Blob([content], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        triggerDownload(url, `query_results_${new Date().getTime()}.csv`);
        URL.revokeObjectURL(url);
        showToast('Downloaded results as CSV', 'success');
    });
});

copyJsonBtn.addEventListener('click', () => {
    if (!lastResult) return;
    const json = JSON.stringify(lastResult, null, 2);
    navigator.clipboard.writeText(json).then(() => {
        const originalText = copyJsonBtn.textContent;
        copyJsonBtn.textContent = 'Copied!';
        showToast('Copied JSON to clipboard', 'success');
        setTimeout(() => { copyJsonBtn.textContent = originalText; }, 2000);
    }).catch(err => {
        console.error(err);
        showToast('Clipboard Error: ' + err.message);
    });
});

loadSamplesBtn.addEventListener('click', async () => {
    await withLoading('Sample Loading Error', async () => {
        const db = getDb();
        const conn = getConnection();
        await Promise.all(Object.entries(SAMPLE_DATA).map(([name, content]) => db.registerFileText(name, content)));

        const queries = [];
        const tableNames = [];
        for (const name of Object.keys(SAMPLE_DATA)) {
            const tableName = name.replace('.csv', '');
            const escapedName = name.replace(/'/g, "''");
            queries.push(`CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM read_csv_auto('${escapedName}');`);
            tableNames.push(tableName);
        }

        if (queries.length > 0) {
            await Promise.all(queries.map(q => conn.query(q)));
        }

        for (const tableName of tableNames) {
            tableSchemaCache.delete(tableName);
            loadedTables.add(tableName);
            setCurrentTableName(tableName);
        }

        sqlInput.value = `SELECT * FROM "employees" JOIN "departments" ON "employees"."dept_id" = "departments"."dept_id" LIMIT 100`;
        sqlInput.dispatchEvent(new Event('input'));

        schemaDisplay.textContent = '';
        await Promise.all(Array.from(loadedTables).map(t => getTableSchemaCached(t)));
        for (const table of loadedTables) {
            await displayTableSchema(table);
        }

        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
        updateChartBuilderUI();
        updateConsoleActionsUI();

        const originalText = loadSamplesBtn.textContent;
        loadSamplesBtn.textContent = 'Samples Loaded!';
        setTimeout(() => { loadSamplesBtn.textContent = originalText; }, 2000);
    });
});

exportDbBtn.addEventListener('click', async () => {
    await withLoading('Database Export Error', async () => {
        const conn = getConnection();
        const db = getDb();
        await conn.query(`CHECKPOINT`);

        let buffer;
        try {
            buffer = await db.copyFileToBuffer('indexeddb://duckdb');
        } catch (e) {
            try {
                buffer = await db.copyFileToBuffer('opfs://duckdb_v1.db');
            } catch (e2) {
                buffer = new Uint8Array([0x44, 0x55, 0x43, 0x4b]);
            }
        }

        const blob = new Blob([buffer], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        triggerDownload(url, `datadashboard_export_${new Date().getTime()}.db`);
        URL.revokeObjectURL(url);
        showToast('Database exported', 'success');
    });
});

clearBtn.addEventListener('click', async () => {
    if (!confirm('This will permanently delete all loaded tables from your local storage. Continue?')) return;

    await withLoading('Clear Error', async () => {
        const conn = getConnection();
        const tablesResult = await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'");
        const tables = getRows(tablesResult).map(r => r.table_name);

        if (tables.length > 0) {
            const dropQuery = tables.map(table => `DROP TABLE IF EXISTS "${escapeId(table)}";`).join('\n');
            await conn.query(dropQuery);
        }

        clearLoadedTables();
        schemaDisplay.textContent = '';
        destroyCharts(previewsContainer);
        previewsContainer.textContent = '';
        if (gridInstance) {
            gridInstance.destroy();
            gridInstance = null;
        }
        document.getElementById('results').innerHTML = `
            <div class="empty" style="text-align: center; padding: 40px 20px;">
                <svg aria-hidden="true" style="width: 48px; height: 48px; margin: 0 auto 16px; opacity: 0.5; display: block;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
                </svg>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 0 0 8px 0;">No data to display</h3>
                <p style="font-size: 0.9rem; margin: 0; color: var(--text-muted);">Drop a file above or run a SQL query to view results here.</p>
            </div>
        `;
        sqlInput.value = '';
        sqlInput.dispatchEvent(new Event('input'));
        downloadBtn.disabled = true;
        downloadBtn.title = 'Requires query results';
        copyJsonBtn.disabled = true;
        copyJsonBtn.title = 'Requires query results';
        joinAssistant.style.display = 'none';
        updateChartBuilderUI();
        updateConsoleActionsUI();
        statusEl.textContent = 'Storage cleared';
    });
});

loadRemoteDeltaBtn.addEventListener('click', async () => {
    const url = remoteDeltaUrl.value.trim();
    if (!url) return;

    if (!window.deltaSupported) {
        showToast('Delta Lake support is not available in this browser environment. Please use CSV, JSON, or Parquet files instead.');
        return;
    }

    await withLoading('Error loading remote Delta table', async () => {
        const tableName = 'remote_delta_' + Math.random().toString(36).substr(2, 5);
        const escapedUrl = url.replace(/'/g, "''");
        const query = `CREATE OR REPLACE TABLE "${escapeId(tableName)}" AS SELECT * FROM delta_scan('${escapedUrl}')`;
        const conn = getConnection();
        await conn.query(query);

        setCurrentTableName(tableName);
        loadedTables.add(tableName);
        await onTableLoaded(tableName);

        statusEl.textContent = `Loaded remote table: ${tableName}`;
        updateConsoleActionsUI();

        const originalText = loadRemoteDeltaBtn.textContent;
        loadRemoteDeltaBtn.textContent = 'Table Loaded!';
        setTimeout(() => { loadRemoteDeltaBtn.textContent = originalText; }, 2000);
    });
});

// Kick off initialization
initDuckDB({ statusEl, setProgress, onStateRestored: restoreState });

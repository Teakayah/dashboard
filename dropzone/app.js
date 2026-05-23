import * as duckdb from './vendor/duckdb/duckdb-browser.mjs';

// DuckDB-Wasm manual bundle configuration.
const MANUAL_BUNDLES = {
    mvp: {
        mainModule: new URL('./vendor/duckdb/duckdb-mvp.wasm', import.meta.url).href,
        mainWorker: new URL('./vendor/duckdb/duckdb-browser-mvp.worker.js', import.meta.url).href,
    },
    eh: {
        mainModule: new URL('./vendor/duckdb/duckdb-eh.wasm', import.meta.url).href,
        mainWorker: new URL('./vendor/duckdb/duckdb-browser-eh.worker.js', import.meta.url).href,
    },
};

const INIT_TIMEOUT_MS = 30000;

let db = null;
let conn = null;
let lastResult = null;
let currentTableName = '';
let loadedTables = new Set();

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

loadRemoteDeltaBtn.addEventListener('click', async () => {
    const url = remoteDeltaUrl.value.trim();
    if (!url) return;

    if (!window.deltaSupported) {
        alert('Delta Lake support is not available in this browser environment. Please use CSV, JSON, or Parquet files instead.');
        return;
    }

    loadingOverlay.style.display = 'flex';
    try {
        const tableName = 'remote_delta_' + Math.random().toString(36).substr(2, 5);
        // httpfs is required for remote URLs, DuckDB-Wasm usually autoloads it, 
        // but we can ensure it's there if needed.

        const escapedUrl = url.replace(/'/g, "''");
        const query = `CREATE TABLE "${tableName}" AS SELECT * FROM delta_scan('${escapedUrl}')`;
        await conn.query(query);

        currentTableName = tableName;
        loadedTables.add(tableName);
        await onTableLoaded(tableName);

        statusEl.textContent = `Loaded remote table: ${tableName}`;

        const originalText = loadRemoteDeltaBtn.textContent;
        loadRemoteDeltaBtn.textContent = 'Table Loaded!';
        setTimeout(() => { loadRemoteDeltaBtn.textContent = originalText; }, 2000);
    } catch (err) {
        console.error(err);
        alert('Error loading remote Delta table: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

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
function getRows(result) {
    if (!result || !result.schema) return [];
    const fields = result.schema.fields.map(f => f.name);
    const rows = [];
    for (let i = 0; i < result.numRows; i++) {
        const rowProxy = result.get(i);
        const rowPlain = {};
        for (const field of fields) {
            const val = rowProxy[field];
            // Cast BigInts to strings for UI/JSON compatibility
            rowPlain[field] = typeof val === 'bigint' ? val.toString() : val;
        }
        rows.push(rowPlain);
    }
    return rows;
}

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

const SAMPLE_DATA = {
    'employees.csv': `id,name,dept_id,salary,join_date
1,Alice,101,85000,2022-01-15
2,Bob,102,72000,2022-03-20
3,Charlie,101,95000,2021-11-10
4,David,103,64000,2023-02-05
5,Eve,102,81000,2022-08-12`,
    'departments.csv': `dept_id,dept_name,location
101,Engineering,New York
102,Marketing,Toronto
103,Design,Vancouver
104,Sales,Montreal`
};

function showInitError(message) {
    statusEl.textContent = message + ' ';
    const btn = document.createElement('button');
    btn.textContent = 'Reload without service worker';
    btn.style.cssText = 'margin-left:8px;padding:2px 8px;cursor:pointer;font-size:inherit';
    btn.addEventListener('click', reloadWithoutSW);
    statusEl.appendChild(btn);
}

function reloadWithoutSW() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations()
            .then((regs) => Promise.all(regs.map((r) => r.unregister())))
            .then(() => location.reload());
    } else {
        location.reload();
    }
}

async function init() {
    let timedOut = false;
    const timeoutId = setTimeout(() => {
        timedOut = true;
        showInitError('Initialization timed out after 30 s.');
    }, INIT_TIMEOUT_MS);

    try {
        statusEl.textContent = 'Selecting bundle...';
        const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);

        statusEl.textContent = 'Initializing worker...';
        const worker = new Worker(bundle.mainWorker);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

        const accessMode = duckdb.DuckDBAccessMode?.READ_WRITE ?? 1;
        console.log('DuckDB accessMode:', accessMode);
        await db.open({ path: 'indexeddb://duckdb', accessMode });

        conn = await db.connect();

        statusEl.textContent = 'Loading extensions...';
        let deltaSupported = true;
        try {
            // DuckDB-Wasm v0.9.1 may not support the 'delta' extension on all platforms
            await conn.query('LOAD delta;');
        } catch (e) {
            console.warn('Delta extension not supported in this environment:', e.message);
            deltaSupported = false;
        }
        window.deltaSupported = deltaSupported;

        clearTimeout(timeoutId);
        if (!timedOut) {
            statusEl.textContent = 'DuckDB Ready';
        }
        console.log('DuckDB-Wasm initialized');

        // Restore loaded tables
        await restoreState();
    } catch (err) {
        clearTimeout(timeoutId);
        console.error(err);
        showInitError('Error: ' + err.message);
    }
}

async function restoreState() {
    try {
        const tablesResult = await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'");
        const tables = getRows(tablesResult).map(r => r.table_name);
        
        if (tables.length > 0) {
            loadedTables = new Set(tables);
            currentTableName = tables[tables.length - 1];
            statusEl.textContent = `Restored ${tables.length} table(s)`;
            
            schemaDisplay.textContent = '';
            for (const table of tables) {
                await displayTableSchema(table);
            }
            
            sqlInput.value = `SELECT * FROM "${currentTableName}" LIMIT 100`;
            sqlInput.dispatchEvent(new Event('input'));
            
            updateJoinUI();
            updateChartBuilderUI();
        }
    } catch (err) {
        console.warn('Failed to restore state:', err);
    }
}

async function displayTableSchema(tableName) {
    const schemaResult = await conn.query(`DESCRIBE "${tableName}"`);
    const statsContainer = document.createElement('div');
    statsContainer.style.fontSize = '0.75rem';
    statsContainer.style.marginTop = '4px';
    statsContainer.style.color = '#666';
    statsContainer.style.fontStyle = 'italic';
    statsContainer.style.minHeight = '1.2em';

    const cols = getRows(schemaResult).map(r => {
        const span = document.createElement('span');
        span.className = 'clickable-col';
        span.style.cursor = 'pointer';
        span.style.textDecoration = 'underline';
        span.style.marginRight = '8px';
        span.style.color = 'var(--primary)';
        span.style.borderRadius = '4px';
        span.style.padding = '2px 4px';
        span.textContent = `${r.column_name} (${r.column_type})`;
        span.tabIndex = 0;
        span.setAttribute('role', 'button');
        span.setAttribute('aria-label', `Insert column ${r.column_name} into SQL editor`);
        
        const triggerAction = async (e) => {
            e.stopPropagation();
            insertAtCursor(sqlInput, `"${r.column_name}"`);
            
            // Profiling logic
            try {
                statsContainer.textContent = 'Calculating stats...';
                const profilingResult = await conn.query(`SELECT MIN("${r.column_name}") as min_val, MAX("${r.column_name}") as max_val, COUNT("${r.column_name}") as count_val FROM "${tableName}"`);
                const stats = getRows(profilingResult)[0];
                statsContainer.textContent = `Stats for ${r.column_name}: Min: ${stats.min_val} | Max: ${stats.max_val} | Count: ${stats.count_val}`;
            } catch (err) {
                statsContainer.textContent = `Profiling failed: ${err.message}`;
            }
        };

        span.onclick = triggerAction;
        span.onkeydown = (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                triggerAction(e);
            }
        };

        return span;
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

function updateJoinUI() {
    if (loadedTables.size >= 2) {
        joinAssistant.style.display = 'flex';
        const tables = Array.from(loadedTables);
        
        const populateSelect = (select, options) => {
            const currentVal = select.value;
            select.textContent = '';
            options.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                select.appendChild(opt);
            });
            if (options.includes(currentVal)) select.value = currentVal;
        };

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

async function updateJoinColumns() {
    const tableA = joinTableA.value;
    const tableB = joinTableB.value;
    if (!tableA || !tableB) return;

    try {
        const schemaAResult = await conn.query(`DESCRIBE "${tableA}"`);
        const schemaBResult = await conn.query(`DESCRIBE "${tableB}"`);
        
        const colsA = new Set(getRows(schemaAResult).map(r => r.column_name));
        const colsB = getRows(schemaBResult).map(r => r.column_name);
        
        const sharedCols = colsB.filter(c => colsA.has(c));
        
        joinCol.textContent = '';
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.disabled = true;
        defaultOpt.selected = true;
        defaultOpt.textContent = 'Select Common Column...';
        joinCol.appendChild(defaultOpt);
        sharedCols.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            joinCol.appendChild(opt);
        });

        if (sharedCols.length === 0) {
            const opt = document.createElement('option');
            opt.textContent = 'No shared columns found';
            opt.disabled = true;
            joinCol.appendChild(opt);
        }
    } catch (err) {
        console.error('Error fetching columns for join:', err);
    }
}

async function updateChartBuilderUI() {
    if (!currentTableName) {
        chartBuilder.style.display = 'none';
        return;
    }
    chartBuilder.style.display = 'flex';
    try {
        const schemaResult = await conn.query(`DESCRIBE "${currentTableName}"`);
        const cols = getRows(schemaResult);
        
        const populateSelect = (select, cols, defaultMsg) => {
            select.textContent = '';
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.disabled = true;
            defaultOpt.selected = true;
            defaultOpt.textContent = defaultMsg;
            select.appendChild(defaultOpt);
            cols.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.column_name;
                opt.textContent = `${c.column_name} (${c.column_type})`;
                select.appendChild(opt);
            });
        };

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
        alert('Please select both tables and a common column.');
        return;
    }
    
    if (a === b) {
        alert('Please select two different tables to join.');
        return;
    }

    const sql = `SELECT *\nFROM "${a}"\nJOIN "${b}" ON "${a}"."${col}" = "${b}"."${col}"\nLIMIT 100`;
    sqlInput.value = sql;
    sqlInput.dispatchEvent(new Event('input'));
    sqlInput.focus();
});

generateChartBtn.addEventListener('click', () => {
    const type = chartType.value;
    const xCol = chartXCol.value;
    const yCol = chartYCol.value;
    
    if (!xCol || !yCol) {
        alert('Please select both X and Y axes.');
        return;
    }

    const title = `Custom ${type.toUpperCase()}: ${yCol} vs ${xCol}`;
    
    createPreviewCard(title, async (canvasId) => {
        try {
            let sql = '';
            if (type === 'scatter') {
                sql = `SELECT "${xCol}" as x, "${yCol}" as y\nFROM "${currentTableName}"\nWHERE "${xCol}" IS NOT NULL AND "${yCol}" IS NOT NULL\nLIMIT 500`;
            } else {
                sql = `SELECT "${xCol}" as label, AVG("${yCol}") as value\nFROM "${currentTableName}"\nWHERE "${xCol}" IS NOT NULL AND "${yCol}" IS NOT NULL\nGROUP BY 1\nORDER BY 1 ASC\nLIMIT 100`;
            }
            
            // Show the generated SQL to the user in the console
            sqlInput.value = sql;
            sqlInput.dispatchEvent(new Event('input'));
            
            const result = await conn.query(sql);
            const rows = getRows(result);
            
            let chartData = {};
            let chartOptions = {};
            
            if (type === 'scatter') {
                chartData = {
                    datasets: [{
                        label: `${xCol} vs ${yCol}`,
                        data: rows.map(r => ({x: r.x, y: r.y})),
                        backgroundColor: '#ff9f40'
                    }]
                };
                chartOptions = {
                    scales: { x: { title: {display: true, text: xCol} }, y: { title: {display: true, text: yCol} } }
                };
            } else {
                chartData = {
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
            }
            
            renderChart(canvasId, type, chartData, chartOptions);
        } catch (e) {
            console.error('Custom chart error', e);
            alert('Error generating chart: ' + e.message);
        }
    });
});

// Handle file drops
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

// Add keyboard support to trigger file dialog
dropZone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault(); // Prevent page scroll for space
        fileInput.click();
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFiles(fileInput.files);
});

/**
 * Processes dropped or selected files, grouping them to detect complex dataset structures like Delta Lake.
 *
 * Delta Lake datasets consist of a directory containing Parquet files and a `_delta_log` directory.
 * Standard HTML file inputs and Drag & Drop APIs flatten these into a list of files.
 * This function groups files by their root directory name. If a group contains a `_delta_log`,
 * it loads them as a unified Delta table; otherwise, it processes them as standalone files.
 *
 * @param {FileList|Array<File>} files - The files selected or dropped by the user.
 */
async function handleFiles(files) {
    loadingOverlay.style.display = 'flex';
    previewsContainer.textContent = '';
    
    try {
        // Group files by their relative path to detect Delta Lake tables
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

        // Process standalone files
        for (const file of standaloneFiles) {
            await processFile(file, file.name);
        }

        // Process directory groups (Potential Delta Lake or multi-part datasets)
        for (const [dirName, dirFiles] of Object.entries(fileGroups)) {
            const isDelta = dirFiles.some(f => (f.webkitRelativePath || f.name).includes('_delta_log'));
            const tableName = dirName.replace(/[^a-zA-Z0-9]/g, '_');
            
            for (const file of dirFiles) {
                const fullPath = file.webkitRelativePath || file.name;
                const buffer = await file.arrayBuffer();
                await db.registerFileBuffer(fullPath, new Uint8Array(buffer));
            }

            if (isDelta) {
                if (!window.deltaSupported) {
                    alert(`Delta Lake table detected in folder "${dirName}", but support is missing in this browser. Skipping.`);
                    continue;
                }
                currentTableName = tableName;
                loadedTables.add(tableName);
                const escapedDirName = dirName.replace(/'/g, "''");
                const query = `CREATE TABLE "${tableName}" AS SELECT * FROM delta_scan('${escapedDirName}')`;
                await conn.query(`DROP TABLE IF EXISTS "${tableName}"`);
                await conn.query(query);
                await onTableLoaded(tableName);
            } else {
                // If not delta, just treat as individual files (default behavior)
                for (const file of dirFiles) {
                    await processFile(file, file.webkitRelativePath || file.name);
                }
            }
        }

        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
    } catch (err) {
        console.error(err);
        alert('Error loading files: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Loads a single file into DuckDB-Wasm and registers it as a table.
 *
 * Automatically selects the appropriate DuckDB read function (`read_parquet`, `read_csv_auto`,
 * `read_json_auto`) based on the file extension to ensure optimal parsing and schema inference.
 *
 * @param {File} file - The file object to load.
 * @param {string} path - The internal path to register the file buffer under in DuckDB.
 */
async function processFile(file, path) {
    const tableName = file.name.replace(/[^a-zA-Z0-9]/g, '_');
    currentTableName = tableName;
    loadedTables.add(tableName);
    
    const buffer = await file.arrayBuffer();
    await db.registerFileBuffer(path, new Uint8Array(buffer));
    
    let query = '';
    const ext = file.name.split('.').pop().toLowerCase();
    const escapedPath = path.replace(/'/g, "''");
    
    if (ext === 'parquet') {
        query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_parquet('${escapedPath}')`;
    } else if (ext === 'csv') {
        query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_csv_auto('${escapedPath}')`;
    } else if (ext === 'json') {
        query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_json_auto('${escapedPath}')`;
    } else {
        query = `CREATE TABLE "${tableName}" AS SELECT * FROM '${escapedPath}'`;
    }
    
    await conn.query(`DROP TABLE IF EXISTS "${tableName}"`);
    await conn.query(query);
    await onTableLoaded(tableName);
}

async function onTableLoaded(tableName) {
    // Show schema
    if (loadedTables.size === 1) schemaDisplay.textContent = '';
    await displayTableSchema(tableName);
    
    // Generate Previews
    await generateInstantCharts(tableName);
    
    // Set default query
    sqlInput.value = `SELECT * FROM "${tableName}" LIMIT 100`;
    sqlInput.dispatchEvent(new Event('input'));
}

function insertAtCursor(myField, myValue) {
    if (document.selection) {
        myField.focus();
        const sel = document.selection.createRange();
        sel.text = myValue;
    } else if (myField.selectionStart || myField.selectionStart == '0') {
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
}

recipeSelect.addEventListener('change', () => {
    if (!currentTableName) return;
    const recipe = recipeSelect.value.replace(/{{TABLE}}/g, currentTableName);
    sqlInput.value = recipe;
    sqlInput.dispatchEvent(new Event('input'));
    recipeSelect.selectedIndex = 0;
});

/**
 * Automatically generates visualization previews for a given dataset table.
 * Analyzes the table schema to identify date, numeric, and text columns,
 * then runs heuristic SQL queries to detect and render:
 *  1. Time-series trends (if date + numeric columns exist)
 *  2. Highest correlation pairs (tests up to 10 pairs of numeric columns)
 *  3. Category distributions (if text + numeric columns exist)
 *
 * @param {string} tableName - The name of the DuckDB table to analyze
 */
async function generateInstantCharts(tableName) {
    const schemaResult = await conn.query(`DESCRIBE "${tableName}"`);
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
                SELECT "${dCol}" as date, AVG("${nCol}") as val 
                FROM "${tableName}"
                WHERE "${dCol}" IS NOT NULL AND "${nCol}" IS NOT NULL
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
        });
    }

    // 2. Correlation detection
    if (numericCols.length >= 2) {
        try {
            let bestPair = [numericCols[0], numericCols[1]];
            let maxCorr = 0;
            
            for (let i = 0; i < Math.min(numericCols.length, 5); i++) {
                for (let j = i + 1; j < Math.min(numericCols.length, 5); j++) {
                    const c1 = numericCols[i];
                    const c2 = numericCols[j];
                    const corrResult = await conn.query(`SELECT corr("${c1}", "${c2}") as c FROM "${tableName}"`);
                    const corr = Math.abs(getRows(corrResult)[0].c || 0);
                    if (corr > maxCorr) {
                        maxCorr = corr;
                        bestPair = [c1, c2];
                    }
                }
            }
            
            createPreviewCard(`Correlation: ${bestPair[0]} vs ${bestPair[1]}`, async (canvasId) => {
                const result = await conn.query(`SELECT "${bestPair[0]}" as x, "${bestPair[1]}" as y FROM "${tableName}" WHERE x IS NOT NULL AND y IS NOT NULL LIMIT 500`);
                const rows = getRows(result);
                renderChart(canvasId, 'scatter', {
                    datasets: [{
                        label: `${bestPair[0]} vs ${bestPair[1]}`,
                        data: rows.map(r => ({x: r.x, y: r.y})),
                        backgroundColor: '#4f8ef7'
                    }]
                }, {
                    scales: { x: { title: {display: true, text: bestPair[0]} }, y: { title: {display: true, text: bestPair[1]} } }
                });
            });
        } catch (e) { console.warn('Correlation check failed', e); }
    }

    // 3. Category Distribution
    if (textCols.length > 0 && numericCols.length > 0) {
        const tCol = textCols[0];
        const nCol = numericCols[0];
        createPreviewCard(`Distribution: ${nCol} by ${tCol}`, async (canvasId) => {
            const result = await conn.query(`
                SELECT "${tCol}" as label, AVG("${nCol}") as value 
                FROM "${tableName}"
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
        });
    }
}

function createPreviewCard(title, renderFn) {
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
    downloadBtn.style.padding = '2px 6px';
    downloadBtn.style.fontSize = '0.7rem';
    downloadBtn.onclick = () => {
        const canvas = document.getElementById(id);
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.png';
        a.click();
    };
    header.appendChild(downloadBtn);
    
    card.appendChild(header);
    
    const canvas = document.createElement('canvas');
    canvas.id = id;
    card.appendChild(canvas);
    
    previewsContainer.appendChild(card);
    renderFn(id);
}

function renderChart(id, type, data, options = {}) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
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

sqlInput.addEventListener('input', () => {
    if (sqlInput.value.trim().length > 0) {
        runBtn.disabled = false;
        runBtn.title = '';
    } else {
        runBtn.disabled = true;
        runBtn.title = 'Requires a valid query';
    }
});

runBtn.addEventListener('click', runQuery);

async function runQuery() {
    const sql = sqlInput.value.trim();
    if (!sql) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        const result = await conn.query(sql);
        lastResult = getRows(result);
        renderResults(lastResult);
        downloadBtn.disabled = false;
        downloadBtn.title = '';
        copyJsonBtn.disabled = false;
        copyJsonBtn.title = '';
    } catch (err) {
        console.error(err);
        alert('Query Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Renders the SQL query result table in the UI using Grid.js.
 * Transforms DuckDB-Wasm result formats into plain arrays of objects suitable for visualization.
 *
 * @param {Array<Object>} rows - The plain array of row objects
 */
function renderResults(rows) {
    if (rows.length === 0) {
        document.getElementById('results').textContent = 'No results';
        return;
    }
    const columns = Object.keys(rows[0]);
    const resultsContainer = document.getElementById('results');
    resultsContainer.textContent = '';
    
    new gridjs.Grid({
        columns: columns,
        data: rows.map(row => columns.map(col => row[col])),
        pagination: { limit: 10 },
        sort: true,
        search: true,
        resizable: true,
        style: { table: { 'white-space': 'nowrap' } }
    }).render(resultsContainer);
}

downloadBtn.addEventListener('click', async () => {
    if (!lastResult || lastResult.length === 0) return;
    loadingOverlay.style.display = 'flex';
    try {
        const csvPath = 'export.csv';
        await conn.query(`CREATE OR REPLACE TEMPORARY TABLE _export_tmp AS ${sqlInput.value.trim()}`);
        await conn.query(`COPY _export_tmp TO '${csvPath}' (HEADER, DELIMITER ',')`);
        
        const content = await db.copyFileToBuffer(csvPath);
        const blob = new Blob([content], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `query_results_${new Date().getTime()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error(err);
        alert('Export Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

copyJsonBtn.addEventListener('click', () => {
    if (!lastResult) return;
    const json = JSON.stringify(lastResult, null, 2);
    navigator.clipboard.writeText(json).then(() => {
        const originalText = copyJsonBtn.textContent;
        copyJsonBtn.textContent = 'Copied!';
        setTimeout(() => { copyJsonBtn.textContent = originalText; }, 2000);
    });
});

loadSamplesBtn.addEventListener('click', async () => {
    loadingOverlay.style.display = 'flex';
    try {
        for (const [name, content] of Object.entries(SAMPLE_DATA)) {
            const tableName = name.replace('.csv', '');
            await db.registerFileText(name, content);
            const escapedName = name.replace(/'/g, "''");
            await conn.query(`CREATE TABLE IF NOT EXISTS "${tableName}" AS SELECT * FROM read_csv_auto('${escapedName}')`);
            loadedTables.add(tableName);
            currentTableName = tableName;
        }
        
        // Populate the example SQL before the async schema render loop, so any
        // test (or user) waiting on schema-display to mention a table can rely on
        // sqlInput already being settled. Otherwise this write races with the
        // next user/test action and can clobber it.
        sqlInput.value = `SELECT * FROM "employees" JOIN "departments" ON "employees"."dept_id" = "departments"."dept_id" LIMIT 100`;
        sqlInput.dispatchEvent(new Event('input'));

        schemaDisplay.textContent = '';
        for (const table of loadedTables) {
            await displayTableSchema(table);
        }

        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
        updateChartBuilderUI();
        
        const originalText = loadSamplesBtn.textContent;
        loadSamplesBtn.textContent = 'Samples Loaded!';
        setTimeout(() => { loadSamplesBtn.textContent = originalText; }, 2000);
    } catch (err) {
        console.error(err);
        alert('Sample Loading Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

exportDbBtn.addEventListener('click', async () => {
    loadingOverlay.style.display = 'flex';
    try {
        // We can't directly download the indexeddb file from here, 
        // so we export to a temporary buffer and download.
        const exportPath = 'duckdb_export.db';
        await conn.query(`CHECKPOINT`); // Ensure all data is flushed
        
        // DuckDB-Wasm doesn't support 'EXPORT DATABASE' to a single file easily via SQL yet,
        // but we can copy the internal DB file if we know its name.
        // For indexeddb, it's safer to use the buffer if it was a file-backed DB.
        // Since we used indexeddb:// path, we'll try a SQL export approach.
        
        const buffer = await db.copyFileToBuffer('indexeddb://duckdb');
        const blob = new Blob([buffer], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `datadashboard_export_${new Date().getTime()}.db`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error(err);
        alert('Database Export Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

clearBtn.addEventListener('click', async () => {
    if (!confirm('This will permanently delete all loaded tables from your local storage. Continue?')) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        const tablesResult = await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'");
        const tables = getRows(tablesResult).map(r => r.table_name);
        
        for (const table of tables) {
            await conn.query(`DROP TABLE IF EXISTS "${table}"`);
        }
        
        loadedTables.clear();
        currentTableName = '';
        schemaDisplay.textContent = '';
        previewsContainer.textContent = '';
        document.getElementById('results').textContent = '';
        sqlInput.value = '';
        sqlInput.dispatchEvent(new Event('input'));
        downloadBtn.disabled = true;
        downloadBtn.title = 'Requires query results';
        copyJsonBtn.disabled = true;
        copyJsonBtn.title = 'Requires query results';
        joinAssistant.style.display = 'none';
        updateChartBuilderUI();
        statusEl.textContent = 'Storage cleared';
    } catch (err) {
        console.error(err);
        alert('Clear Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

init();

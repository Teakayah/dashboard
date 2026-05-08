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

async function init() {
    try {
        statusEl.textContent = 'Selecting bundle...';
        const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
        
        statusEl.textContent = 'Initializing worker...';
        const worker = new Worker(bundle.mainWorker);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
        await db.open({ path: 'indexeddb://duckdb', accessMode: duckdb.DuckDBAccessMode.READ_WRITE });

        conn = await db.connect();
        statusEl.textContent = 'DuckDB Ready';

        console.log('DuckDB-Wasm initialized');
        
        // Restore loaded tables
        await restoreState();
    } catch (err) {
        console.error(err);
        statusEl.textContent = 'Error: ' + err.message;
    }
}

async function restoreState() {
    try {
        const tablesResult = await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'");
        const tables = tablesResult.toArray().map(r => r.table_name);
        
        if (tables.length > 0) {
            loadedTables = new Set(tables);
            currentTableName = tables[tables.length - 1];
            statusEl.textContent = `Restored ${tables.length} table(s)`;
            
            schemaDisplay.textContent = '';
            for (const table of tables) {
                await displayTableSchema(table);
            }
            
            sqlInput.value = `SELECT * FROM "${currentTableName}" LIMIT 100`;
            runBtn.disabled = false;
            
            updateJoinUI();
            updateChartBuilderUI();
        }
    } catch (err) {
        console.warn('Failed to restore state:', err);
    }
}

async function displayTableSchema(tableName) {
    const schema = await conn.query(`DESCRIBE "${tableName}"`);
    const statsContainer = document.createElement('div');
    statsContainer.style.fontSize = '0.75rem';
    statsContainer.style.marginTop = '4px';
    statsContainer.style.color = '#666';
    statsContainer.style.fontStyle = 'italic';
    statsContainer.style.minHeight = '1.2em';

    const cols = schema.toArray().map(r => {
        const span = document.createElement('span');
        span.className = 'clickable-col';
        span.style.cursor = 'pointer';
        span.style.textDecoration = 'underline';
        span.style.marginRight = '8px';
        span.style.color = 'var(--primary)';
        span.textContent = `${r.column_name} (${r.column_type})`;
        
        span.onclick = async (e) => {
            e.stopPropagation();
            insertAtCursor(sqlInput, `"${r.column_name}"`);
            
            // Profiling logic
            try {
                statsContainer.textContent = 'Calculating stats...';
                const profilingResult = await conn.query(`SELECT MIN("${r.column_name}") as min_val, MAX("${r.column_name}") as max_val, COUNT("${r.column_name}") as count_val FROM "${tableName}"`);
                const stats = profilingResult.toArray()[0];
                statsContainer.textContent = `Stats for ${r.column_name}: Min: ${stats.min_val} | Max: ${stats.max_val} | Count: ${stats.count_val}`;
            } catch (err) {
                statsContainer.textContent = `Profiling failed: ${err.message}`;
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
        const schemaA = await conn.query(`DESCRIBE "${tableA}"`);
        const schemaB = await conn.query(`DESCRIBE "${tableB}"`);
        
        const colsA = new Set(schemaA.toArray().map(r => r.column_name));
        const colsB = schemaB.toArray().map(r => r.column_name);
        
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
        const schema = await conn.query(`DESCRIBE "${currentTableName}"`);
        const cols = schema.toArray();
        
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
            
            const data = await conn.query(sql);
            const rows = data.toArray();
            
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

async function handleFiles(files) {
    loadingOverlay.style.display = 'flex';
    previewsContainer.textContent = '';
    
    try {
        for (const file of files) {
            const tableName = file.name.replace(/[^a-zA-Z0-9]/g, '_');
            currentTableName = tableName;
            loadedTables.add(tableName);
            
            const buffer = await file.arrayBuffer();
            await db.registerFileBuffer(file.name, new Uint8Array(buffer));
            
            let query = '';
            const ext = file.name.split('.').pop().toLowerCase();
            const escapedFileName = file.name.replace(/'/g, "''");
            if (ext === 'parquet') {
                query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_parquet('${escapedFileName}')`;
            } else if (ext === 'csv') {
                query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_csv_auto('${escapedFileName}')`;
            } else if (ext === 'json') {
                query = `CREATE TABLE "${tableName}" AS SELECT * FROM read_json_auto('${escapedFileName}')`;
            } else {
                query = `CREATE TABLE "${tableName}" AS SELECT * FROM '${escapedFileName}'`;
            }
            
            await conn.query(`DROP TABLE IF EXISTS "${tableName}"`);
            await conn.query(query);
            
            // Show schema
            if (loadedTables.size === 1) schemaDisplay.textContent = '';
            await displayTableSchema(tableName);
            
            // Generate Previews
            await generateInstantCharts(tableName);
            
            // Set default query
            sqlInput.value = `SELECT * FROM "${tableName}" LIMIT 100`;
            runBtn.disabled = false;
        }
        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
    } catch (err) {
        console.error(err);
        alert('Error loading file: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
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
}

recipeSelect.addEventListener('change', () => {
    if (!currentTableName) return;
    const recipe = recipeSelect.value.replace(/{{TABLE}}/g, currentTableName);
    sqlInput.value = recipe;
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
    const schema = await conn.query(`DESCRIBE "${tableName}"`);
    const columns = schema.toArray();
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
            const data = await conn.query(`
                SELECT "${dCol}" as date, AVG("${nCol}") as val 
                FROM "${tableName}"
                WHERE "${dCol}" IS NOT NULL AND "${nCol}" IS NOT NULL
                GROUP BY 1 ORDER BY 1 ASC LIMIT 100
            `);
            const rows = data.toArray();
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
                    const corr = Math.abs(corrResult.toArray()[0].c || 0);
                    if (corr > maxCorr) {
                        maxCorr = corr;
                        bestPair = [c1, c2];
                    }
                }
            }
            
            createPreviewCard(`Correlation: ${bestPair[0]} vs ${bestPair[1]}`, async (canvasId) => {
                const data = await conn.query(`SELECT "${bestPair[0]}" as x, "${bestPair[1]}" as y FROM "${tableName}" WHERE x IS NOT NULL AND y IS NOT NULL LIMIT 500`);
                renderChart(canvasId, 'scatter', {
                    datasets: [{
                        label: `${bestPair[0]} vs ${bestPair[1]}`,
                        data: data.toArray().map(r => ({x: r.x, y: r.y})),
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
            const data = await conn.query(`
                SELECT "${tCol}" as label, AVG("${nCol}") as value 
                FROM "${tableName}"
                GROUP BY 1 
                ORDER BY value DESC 
                LIMIT 10
            `);
            const rows = data.toArray();
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

runBtn.addEventListener('click', runQuery);

async function runQuery() {
    const sql = sqlInput.value.trim();
    if (!sql) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        lastResult = await conn.query(sql);
        renderResults(lastResult);
        downloadBtn.disabled = false;
        copyJsonBtn.disabled = false;
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
 * @param {import('@duckdb/duckdb-wasm').Table} result - The Arrow table result from a DuckDB query
 */
function renderResults(result) {
    const fields = result.schema.fields.map(f => f.name);
    const data = result.toArray().map(row => {
        const obj = {};
        for (const key of fields) {
            const val = row[key];
            // Workaround: Grid.js and standard JSON serialization (JSON.stringify) crash on BigInt values.
            // We cast BigInts to strings here so that UI components can render them safely.
            obj[key] = typeof val === 'bigint' ? val.toString() : val;
        }
        return obj;
    });

    const resultsContainer = document.getElementById('results');
    resultsContainer.textContent = '';

    new gridjs.Grid({
        columns: fields,
        data: data.map(row => fields.map(col => row[col])),        pagination: { limit: 10 },
        sort: true,
        search: true,
        resizable: true,
        style: { table: { 'white-space': 'nowrap' } }
    }).render(resultsContainer);
}

downloadBtn.addEventListener('click', async () => {
    if (!lastResult) return;
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
    const fields = lastResult.schema.fields.map(f => f.name);
    const data = lastResult.toArray().map(row => {
        const obj = {};
        for (const key of fields) {
            const val = row[key];
            obj[key] = typeof val === 'bigint' ? val.toString() : val;
        }
        return obj;
    });
    const json = JSON.stringify(data, null, 2);
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
        }
        
        schemaDisplay.textContent = '';
        for (const table of loadedTables) {
            await displayTableSchema(table);
        }
        
        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
        updateChartBuilderUI();
        sqlInput.value = `SELECT * FROM "employees" JOIN "departments" ON "employees"."dept_id" = "departments"."dept_id" LIMIT 100`;
        runBtn.disabled = false;
        
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
        const tables = tablesResult.toArray().map(r => r.table_name);
        
        for (const table of tables) {
            await conn.query(`DROP TABLE IF EXISTS "${table}"`);
        }
        
        loadedTables.clear();
        currentTableName = '';
        schemaDisplay.textContent = '';
        previewsContainer.textContent = '';
        document.getElementById('results').textContent = '';
        sqlInput.value = '';
        runBtn.disabled = true;
        downloadBtn.disabled = true;
        copyJsonBtn.disabled = true;
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

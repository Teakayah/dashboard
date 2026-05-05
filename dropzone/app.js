import * as duckdb from './vendor/duckdb/duckdb-browser.mjs';

// DuckDB-Wasm manual bundle configuration.
const MANUAL_BUNDLES = {
    mvp: {
        mainModule: '/dropzone/vendor/duckdb/duckdb-mvp.wasm',
        mainWorker: '/dropzone/vendor/duckdb/duckdb-browser-mvp.worker.js',
    },
    eh: {
        mainModule: '/dropzone/vendor/duckdb/duckdb-eh.wasm',
        mainWorker: '/dropzone/vendor/duckdb/duckdb-browser-eh.worker.js',
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
        
        // Persistent Storage with IndexedDB
        statusEl.textContent = 'Opening persistent storage...';
        await db.open({
            path: 'indexeddb://duckdb',
        });

        conn = await db.connect();
        statusEl.textContent = 'DuckDB Ready';
        
        console.log('DuckDB-Wasm initialized with IndexedDB');
        
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
            
            sqlInput.value = `SELECT * FROM ${currentTableName} LIMIT 100`;
            runBtn.disabled = false;
            
            updateJoinUI();
        }
    } catch (err) {
        console.warn('Failed to restore state:', err);
    }
}

async function displayTableSchema(tableName) {
    const schema = await conn.query(`DESCRIBE ${tableName}`);
    const cols = schema.toArray().map(r => {
        const span = document.createElement('span');
        span.className = 'clickable-col';
        span.style.cursor = 'pointer';
        span.style.textDecoration = 'underline';
        span.style.marginRight = '8px';
        span.style.color = 'var(--primary)';
        span.textContent = `${r.column_name} (${r.column_type})`;
        span.onclick = (e) => {
            e.stopPropagation();
            insertAtCursor(sqlInput, `"${r.column_name}"`);
        };
        return span;
    });
    
    const tableDiv = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = `Table: ${tableName} `;
    tableDiv.appendChild(strong);
    cols.forEach(c => tableDiv.appendChild(c));
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
        const schemaA = await conn.query(`DESCRIBE ${tableA}`);
        const schemaB = await conn.query(`DESCRIBE ${tableB}`);
        
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

    const sql = `SELECT *\nFROM ${a}\nJOIN ${b} ON ${a}."${col}" = ${b}."${col}"\nLIMIT 100`;
    sqlInput.value = sql;
    sqlInput.focus();
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
            if (ext === 'parquet') {
                query = `CREATE TABLE ${tableName} AS SELECT * FROM read_parquet('${file.name}')`;
            } else if (ext === 'csv') {
                query = `CREATE TABLE ${tableName} AS SELECT * FROM read_csv_auto('${file.name}')`;
            } else if (ext === 'json') {
                query = `CREATE TABLE ${tableName} AS SELECT * FROM read_json_auto('${file.name}')`;
            } else {
                query = `CREATE TABLE ${tableName} AS SELECT * FROM '${file.name}'`;
            }
            
            await conn.query(`DROP TABLE IF EXISTS ${tableName}`);
            await conn.query(query);
            
            // Show schema
            if (loadedTables.size === 1) schemaDisplay.textContent = '';
            await displayTableSchema(tableName);
            
            // Generate Previews
            await generateInstantCharts(tableName);
            
            // Set default query
            sqlInput.value = `SELECT * FROM ${tableName} LIMIT 100`;
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

async function generateInstantCharts(tableName) {
    const schema = await conn.query(`DESCRIBE ${tableName}`);
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
                FROM ${tableName} 
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
                    const corrResult = await conn.query(`SELECT corr("${c1}", "${c2}") as c FROM ${tableName}`);
                    const corr = Math.abs(corrResult.toArray()[0].c || 0);
                    if (corr > maxCorr) {
                        maxCorr = corr;
                        bestPair = [c1, c2];
                    }
                }
            }
            
            createPreviewCard(`Correlation: ${bestPair[0]} vs ${bestPair[1]}`, async (canvasId) => {
                const data = await conn.query(`SELECT "${bestPair[0]}" as x, "${bestPair[1]}" as y FROM ${tableName} WHERE x IS NOT NULL AND y IS NOT NULL LIMIT 500`);
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
                FROM ${tableName} 
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
    
    const h3 = document.createElement('h3');
    h3.textContent = title;
    card.appendChild(h3);
    
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

function renderResults(result) {
    const data = result.toArray().map(row => {
        const obj = {};
        for (const key of Object.keys(row)) {
            const val = row[key];
            obj[key] = typeof val === 'bigint' ? val.toString() : val;
        }
        return obj;
    });
    
    const columns = result.schema.fields.map(f => f.name);
    const resultsContainer = document.getElementById('results');
    resultsContainer.textContent = '';
    
    new gridjs.Grid({
        columns: columns,
        data: data.map(row => columns.map(col => row[col])),
        pagination: { limit: 10 },
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
    const data = lastResult.toArray().map(row => {
        const obj = {};
        for (const key of Object.keys(row)) {
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
            await conn.query(`CREATE TABLE IF NOT EXISTS ${tableName} AS SELECT * FROM read_csv_auto('${name}')`);
            loadedTables.add(tableName);
        }
        
        schemaDisplay.textContent = '';
        for (const table of loadedTables) {
            await displayTableSchema(table);
        }
        
        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
        updateJoinUI();
        sqlInput.value = `SELECT * FROM employees JOIN departments ON employees.dept_id = departments.dept_id LIMIT 100`;
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
        statusEl.textContent = 'Storage cleared';
    } catch (err) {
        console.error(err);
        alert('Clear Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

init();

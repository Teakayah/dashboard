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
const loadedTables = new Set();

const statusEl = document.getElementById('status');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const sqlInput = document.getElementById('sql-input');
const runBtn = document.getElementById('run-query');
const downloadBtn = document.getElementById('download-csv');
const recipeSelect = document.getElementById('query-recipes');
const schemaDisplay = document.getElementById('schema-display');
const loadingOverlay = document.getElementById('loading');
const previewsContainer = document.getElementById('instant-previews');

async function init() {
    try {
        statusEl.textContent = 'Selecting bundle...';
        const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
        
        statusEl.textContent = 'Initializing worker...';
        const worker = new Worker(bundle.mainWorker);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
        
        conn = await db.connect();
        statusEl.textContent = 'DuckDB Ready';
        
        console.log('DuckDB-Wasm initialized');
    } catch (err) {
        console.error(err);
        statusEl.textContent = 'Error: ' + err.message;
    }
}

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
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFiles(fileInput.files);
});

async function handleFiles(files) {
    loadingOverlay.style.display = 'flex';
    previewsContainer.innerHTML = '';
    schemaDisplay.innerHTML = '';
    
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
            
            // Show schema with clickable columns
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
            strong.textContent = `${file.name} (table: ${tableName}): `;
            tableDiv.appendChild(strong);
            cols.forEach(c => tableDiv.appendChild(c));
            schemaDisplay.appendChild(tableDiv);
            
            // Generate Previews
            await generateInstantCharts(tableName);
            
            // Set default query
            sqlInput.value = `SELECT * FROM ${tableName} LIMIT 100`;
            runBtn.disabled = false;
        }
        statusEl.textContent = `Loaded ${loadedTables.size} table(s)`;
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

    if (numericCols.length === 0) return;

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

    if (textCols.length > 0 && numericCols.length > 0) {
        const tCol = textCols[0];
        const nCol = numericCols[0];
        createPreviewCard(`Avg ${nCol} by ${tCol}`, async (canvasId) => {
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
    resultsContainer.innerHTML = '';
    
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

init();

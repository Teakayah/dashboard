import * as duckdb from './vendor/duckdb/duckdb-browser.mjs';

// DuckDB-Wasm manual bundle configuration.
// Paths are relative to the site root.
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
let grid = null;

const statusEl = document.getElementById('status');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const sqlInput = document.getElementById('sql-input');
const runBtn = document.getElementById('run-query');
const schemaDisplay = document.getElementById('schema-display');
const loadingOverlay = document.getElementById('loading');

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
        runBtn.disabled = false;
        
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
    try {
        for (const file of files) {
            const tableName = file.name.replace(/[^a-zA-Z0-9]/g, '_');
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
                // Try guessing
                query = `CREATE TABLE ${tableName} AS SELECT * FROM '${file.name}'`;
            }
            
            await conn.query(`DROP TABLE IF EXISTS ${tableName}`);
            await conn.query(query);
            
            // Show schema
            const schema = await conn.query(`DESCRIBE ${tableName}`);
            const schemaRows = schema.toArray().map(r => `${r.column_name} (${r.column_type})`).join(', ');

            const schemaDiv = document.createElement('div');
            const fileNameStrong = document.createElement('strong');
            fileNameStrong.textContent = `${file.name}:`;
            schemaDiv.appendChild(fileNameStrong);
            schemaDiv.appendChild(document.createTextNode(` ${schemaRows}`));
            schemaDisplay.appendChild(schemaDiv);
            
            // Set default query if first file
            if (sqlInput.value === '') {
                sqlInput.value = `SELECT * FROM ${tableName} LIMIT 10`;
            }
        }
        statusEl.textContent = `Loaded ${files.length} file(s)`;
    } catch (err) {
        console.error(err);
        alert('Error loading file: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

runBtn.addEventListener('click', runQuery);

async function runQuery() {
    const sql = sqlInput.value.trim();
    if (!sql) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        const result = await conn.query(sql);
        renderResults(result);
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
            // Handle BigInt and other non-serializable types for Grid.js
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
        pagination: {
            limit: 10
        },
        sort: true,
        search: true,
        resizable: true,
        style: {
            table: {
                'white-space': 'nowrap'
            }
        }
    }).render(resultsContainer);
}

init();

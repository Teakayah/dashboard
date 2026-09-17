import * as duckdb from '../vendor/duckdb/duckdb-browser.mjs';
import { MANUAL_BUNDLES, INIT_TIMEOUT_MS } from './config.js';
import { escapeId, getRows } from './utils.js';

let db = null;
let conn = null;
let currentTableName = '';

export const loadedTables = new Set();
// Performance optimization: Caches the schema to prevent redundant IPC roundtrips
// to the DuckDB-Wasm worker during UI updates, instant chart generation, and join assistant rendering.
export const tableSchemaCache = new Map();

/**
 * Returns the active DuckDB instance.
 * @returns {duckdb.AsyncDuckDB|null}
 */
export function getDb() {
    return db;
}

/**
 * Returns the active DuckDB connection.
 * @returns {duckdb.AsyncDuckDBConnection|null}
 */
export function getConnection() {
    return conn;
}

/**
 * Returns the currently active table name.
 * @returns {string}
 */
export function getCurrentTableName() {
    return currentTableName;
}

/**
 * Sets the currently active table name.
 * @param {string} name
 */
export function setCurrentTableName(name) {
    currentTableName = name;
}

/**
 * Clears the set of loaded tables and the schema cache.
 */
export function clearLoadedTables() {
    loadedTables.clear();
    tableSchemaCache.clear();
    currentTableName = '';
}

/**
 * Retrieves the schema for a table, using a memory cache if available.
 * @param {string} tableName
 * @returns {Promise<any>}
 */
export async function getTableSchemaCached(tableName) {
    if (tableSchemaCache.has(tableName)) {
        return tableSchemaCache.get(tableName);
    }
    if (!conn) {
        throw new Error('Database connection not established');
    }
    const schemaPromise = conn.query(`DESCRIBE "${escapeId(tableName)}"`);
    tableSchemaCache.set(tableName, schemaPromise);
    return await schemaPromise;
}

/**
 * Displays a critical initialization error message to the user.
 * Appends a recovery button that allows the user to forcefully bypass
 * potentially stale Service Worker caches.
 *
 * @param {HTMLElement} statusEl - The status element to update.
 * @param {string} message - The error message to display.
 */
export function showInitError(statusEl, message) {
    if (!statusEl) return;
    statusEl.textContent = message + ' ';
    const btn = document.createElement('button');
    btn.textContent = 'Reload without service worker';
    btn.style.cssText = 'margin-left:8px;padding:2px 8px;cursor:pointer;font-size:inherit';
    btn.addEventListener('click', reloadWithoutSW);
    statusEl.appendChild(btn);
}

/**
 * Forcefully reloads the application while unregistering any active Service Workers.
 * This serves as an escape hatch when the DuckDB-Wasm initialization times out.
 */
export function reloadWithoutSW() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations()
            .then((regs) => Promise.all(regs.map((r) => r.unregister())))
            .then(() => location.reload());
    } else {
        location.reload();
    }
}

/**
 * Initializes the DuckDB-Wasm instance.
 *
 * @param {Object} options
 * @param {HTMLElement} [options.statusEl] - Status display element.
 * @param {Function} [options.setProgress] - Progress callback (0-100).
 * @param {Function} [options.onStateRestored] - Async callback after DB is ready to restore state.
 */
export async function initDuckDB({ statusEl, setProgress, onStateRestored } = {}) {
    let timedOut = false;
    const timeoutId = setTimeout(() => {
        if (!db) {
            timedOut = true;
            showInitError(statusEl, 'DuckDB initialization timed out. Service worker may be stale.');
        }
    }, INIT_TIMEOUT_MS);

    try {
        if (setProgress) setProgress(10);
        if (statusEl) statusEl.textContent = 'Selecting bundle...';
        const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);

        if (setProgress) setProgress(30);
        if (statusEl) statusEl.textContent = 'Instantiating DuckDB...';
        const worker = new Worker(bundle.mainWorker);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

        if (setProgress) setProgress(50);
        if (statusEl) statusEl.textContent = 'Opening database...';
        const accessMode = duckdb.DuckDBAccessMode?.READ_WRITE ?? 3;
        const opfsSupported = !!navigator.storage?.getDirectory;
        // We use a versioned name for OPFS to avoid conflicts with older incompatible files
        const dbPath = opfsSupported ? 'opfs://duckdb_v1.db' : null;

        try {
            await db.open({ path: dbPath, accessMode });
        } catch (err) {
            console.warn('Persistent db.open failed, falling back to in-memory:', err);
            await db.open({ path: null, accessMode });
        }

        if (setProgress) setProgress(70);
        if (statusEl) statusEl.textContent = 'Connecting...';
        conn = await db.connect();

        if (setProgress) setProgress(85);
        if (statusEl) statusEl.textContent = 'Loading extensions...';
        let deltaSupported = true;
        try {
            await conn.query('LOAD delta;');
        } catch (e) {
            console.warn('Delta extension not supported in this environment:', e.message);
            deltaSupported = false;
        }
        window.deltaSupported = deltaSupported;

        clearTimeout(timeoutId);
        if (setProgress) setProgress(100);
        if (!timedOut && statusEl) {
            statusEl.textContent = 'DuckDB Ready';
        }

        // Restore loaded tables if handler is provided
        if (onStateRestored) {
            await onStateRestored();
        }
    } catch (err) {
        clearTimeout(timeoutId);
        if (setProgress) setProgress(0);
        console.error(err);
        showInitError(statusEl, 'Error: ' + err.message);
    }
}

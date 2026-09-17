// DuckDB-Wasm manual bundle configuration.
export const MANUAL_BUNDLES = {
    mvp: {
        mainModule: new URL('../vendor/duckdb/duckdb-mvp.wasm', import.meta.url).href,
        mainWorker: new URL('../vendor/duckdb/duckdb-browser-mvp.worker.js', import.meta.url).href,
    },
    eh: {
        mainModule: new URL('../vendor/duckdb/duckdb-eh.wasm', import.meta.url).href,
        mainWorker: new URL('../vendor/duckdb/duckdb-browser-eh.worker.js', import.meta.url).href,
    },
};

export const INIT_TIMEOUT_MS = 30000;

export const SAMPLE_DATA = {
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

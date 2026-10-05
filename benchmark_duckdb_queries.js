import * as duckdb from './dropzone/vendor/duckdb/duckdb-node.mjs';

async function run() {
    const db = new duckdb.Database(':memory:');
    const conn = await db.connect();

    // Create a dummy table with some data
    await conn.query(`
        CREATE TABLE data (a INT, b INT, c INT, d INT, e INT, f INT);
        INSERT INTO data VALUES (1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12), (13, 14, 15, 16, 17, 18);
    `);

    // Sequential queries
    let start = performance.now();
    for(let i = 0; i < 100; i++) {
        await conn.query(`SELECT corr(a, b) as c_0_1 FROM data`);
        await conn.query(`SELECT corr(a, c) as c_0_2 FROM data`);
        await conn.query(`SELECT corr(b, c) as c_1_2 FROM data`);
    }
    console.log("Sequential:", performance.now() - start);

    // Combined query
    start = performance.now();
    for(let i = 0; i < 100; i++) {
        await conn.query(`SELECT corr(a, b) as c_0_1, corr(a, c) as c_0_2, corr(b, c) as c_1_2 FROM data`);
    }
    console.log("Combined:", performance.now() - start);
}
run();

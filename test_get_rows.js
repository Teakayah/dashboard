const result = {
    schema: { fields: [{name: 'id'}, {name: 'value'}] },
    numRows: 100000,
    get: (i) => {
        return {id: i, value: i * 2, extra: 'x'};
    }
}

function getRowsArray(result) {
    if (!result || !result.schema) return [];
    const fields = result.schema.fields.map(f => f.name);
    const numFields = fields.length;
    const numRows = result.numRows;

    const rows = new Array(numRows);
    for (let i = 0; i < numRows; i++) {
        const rowProxy = result.get(i);
        const rowPlain = {};
        for (let j = 0; j < numFields; j++) {
            const field = fields[j];
            const val = rowProxy[field];
            rowPlain[field] = typeof val === 'bigint' ? val.toString() : val;
        }
        rows[i] = rowPlain;
    }
    return rows;
}

function getRowsObject(result) {
    if (!result || !result.schema) return [];

    // Convert to Apache Arrow Array representation?
    // result.toArray() works on real tables in DuckDB!
    // But it gives us proxies again...

    const rows = result.toArray().map((row) => {
        const rowPlain = {};
        for (const [k, v] of Object.entries(row)) {
            rowPlain[k] = typeof v === 'bigint' ? v.toString() : v;
        }
        return rowPlain;
    });
    return rows;
}

console.time('getRowsArray');
getRowsArray(result);
console.timeEnd('getRowsArray');

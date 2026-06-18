const assert = require('assert');

function getRowsSlow(rawRows, numRows, fields) {
    const numFields = fields.length;
    const rows = new Array(numRows);
    for (let i = 0; i < numRows; i++) {
        const rowObj = rawRows[i];
        const rowPlain = {};
        for (let j = 0; j < numFields; j++) {
            const field = fields[j];
            const val = rowObj[field];
            rowPlain[field] = typeof val === 'bigint' ? val.toString() : val;
        }
        rows[i] = rowPlain;
    }
    return rows;
}

function getRowsFast(rawRows, numRows, fields, schemaFields) {
    // Determine which columns might contain BigInts
    const bigIntCols = new Set();
    for (const f of schemaFields) {
        const typeStr = String(f.type);
        if (f.type.bitWidth === 64 || typeStr.includes('Int64') || typeStr.includes('Timestamp') || typeStr.includes('Time64') || typeStr.includes('Decimal')) {
            bigIntCols.add(f.name);
        }
    }

    const numFields = fields.length;
    const rows = new Array(numRows);

    if (bigIntCols.size === 0) {
        // Fast path: no BigInts
        for (let i = 0; i < numRows; i++) {
            const rowObj = rawRows[i];
            const rowPlain = {};
            for (let j = 0; j < numFields; j++) {
                const field = fields[j];
                rowPlain[field] = rowObj[field];
            }
            rows[i] = rowPlain;
        }
    } else {
        // Only check BigInts for specific columns
        for (let i = 0; i < numRows; i++) {
            const rowObj = rawRows[i];
            const rowPlain = {};
            for (let j = 0; j < numFields; j++) {
                const field = fields[j];
                const val = rowObj[field];
                if (bigIntCols.has(field)) {
                    rowPlain[field] = typeof val === 'bigint' ? val.toString() : val;
                } else {
                    rowPlain[field] = val;
                }
            }
            rows[i] = rowPlain;
        }
    }
    return rows;
}

// Generate some fake data
const numRows = 100000;
const fields = ['a', 'b', 'c', 'd', 'e'];
const schemaFields = fields.map(f => ({ name: f, type: { toString: () => 'Int32' } }));
const rawRows = new Array(numRows);
for (let i = 0; i < numRows; i++) {
    rawRows[i] = { a: 1, b: "hello", c: 3.14, d: false, e: 100 };
}

console.time('slow');
getRowsSlow(rawRows, numRows, fields);
console.timeEnd('slow');

console.time('fast');
getRowsFast(rawRows, numRows, fields, schemaFields);
console.timeEnd('fast');

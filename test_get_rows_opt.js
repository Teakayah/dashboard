const result = {
    schema: { fields: [{name: 'id'}, {name: 'value'}] },
    numRows: 100000,
    get: (i) => {
        return {id: i, value: i * 2};
    }
};

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

function getRowsArrayOpt(result) {
    if (!result || !result.schema) return [];
    const fields = result.schema.fields.map(f => f.name);
    const numFields = fields.length;
    const numRows = result.numRows;

    // Use push or map?
    const rows = [];
    for (let i = 0; i < numRows; i++) {
        const rowProxy = result.get(i);
        // Maybe using Object.fromEntries is faster? No, probably not.
    }
    return rows;
}

console.time('getRowsArray');
getRowsArray(result);
console.timeEnd('getRowsArray');

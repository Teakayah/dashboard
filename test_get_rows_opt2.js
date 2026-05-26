const result = {
    schema: { fields: [{name: 'id'}, {name: 'value'}] },
    numRows: 100000,
    get: (i) => {
        return {id: i, value: i * 2, toJSON: () => ({id: i, value: i * 2})};
    },
    toArray: function() {
        let arr = [];
        for(let i=0; i<this.numRows; i++) arr.push(this.get(i));
        return arr;
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

    return result.toArray().map((rowProxy) => {
        return Object.fromEntries(
            Object.entries(rowProxy).map(([k, v]) => [k, typeof v === 'bigint' ? v.toString() : v])
        );
    });
}

console.time('getRowsArray');
getRowsArray(result);
console.timeEnd('getRowsArray');

console.time('getRowsArrayOpt');
getRowsArrayOpt(result);
console.timeEnd('getRowsArrayOpt');

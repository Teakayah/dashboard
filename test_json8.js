const fs = require('fs');

function checkSchema(schema) {
    if (!schema || !schema.fields) return false;
    for (let j = 0; j < schema.fields.length; j++) {
        // According to apache-arrow JS docs, typeId for Int/BigInt can be checked. Or we can just check if the type's bitWidth is 64.
        // But the safest DuckDB-Wasm way without importing arrow is just checking the type object
        const type = schema.fields[j].type;
        if (type && type.typeId === 2 /* Int */ && type.bitWidth === 64) {
            return true;
        }
        // BigInt could also be Int64, Uint64. Sometimes the type name contains "Int64".
        // Let's inspect what DuckDB-wasm returns for bigint in `type`.
    }
}

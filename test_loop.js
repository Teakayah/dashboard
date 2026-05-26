const numRows = 100000;
const rowsArray = new Array(numRows);
console.time('for loop');
for (let i = 0; i < numRows; i++) {
    rowsArray[i] = i;
}
console.timeEnd('for loop');

const rowsArray2 = [];
console.time('push loop');
for (let i = 0; i < numRows; i++) {
    rowsArray2.push(i);
}
console.timeEnd('push loop');

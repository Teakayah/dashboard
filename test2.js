async function doQuery(i) {
  console.log('started', i);
  await new Promise(r => setTimeout(r, 100));
  console.log('finished', i);
}

const previewPromises = [];
const tasks = [
    async () => { await doQuery(1); },
    async () => { await doQuery(2); },
    async () => { await doQuery(3); }
];

async function runSequential() {
    for (const task of tasks) {
        await task();
    }
}
runSequential();

async function doQuery(i) {
  console.log('started', i);
  await new Promise(r => setTimeout(r, 100));
  console.log('finished', i);
}

const previewPromises = [];
previewPromises.push((async () => {
    await doQuery(1);
})());
previewPromises.push((async () => {
    await doQuery(2);
})());
previewPromises.push((async () => {
    await doQuery(3);
})());

Promise.all(previewPromises);

// Heavy computation task implementation
console.log("Starting heavy computation...");
const start = Date.now();
let result = 0;
for (let i = 0; i < 1e7; i++) {
  result += Math.sqrt(i);
}
console.log(`Computation finished in ${Date.now() - start}ms. Result: ${result}`);

import * as readline from 'node:readline';
import * as fs from 'node:fs';

const createStockfish = await import(`../${process.argv[2] ?? 'sf17_1-79.js'}`);
let history = [],
  index = 0;

const sf = await createStockfish.default();
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: '',
  terminal: true,
});

rl.on('SIGINT', process.exit);

rl.on('line', line => {
  history.push(line);
  index = history.length;
  if (line.startsWith('load ')) sf.setNnueBuffer(fs.readFileSync(line.slice(5)), 0);
  else if (line.startsWith('big ')) sf.setNnueBuffer(fs.readFileSync(line.slice(4)), 0);
  else if (line.startsWith('small ')) sf.setNnueBuffer(fs.readFileSync(line.slice(6)), 1);
  else if (line === 'exit' || line === 'quit') process.exit();
  else sf.uci(line);
});

process.stdin.on('keypress', (_, key) => {
  if (key.name === 'up') {
    if (index < 1) return;
    rl.write(null, { ctrl: true, name: 'u' });
    rl.write(history[--index]);
  } else if (key.name === 'down') {
    if (index > history.length - 2) return;
    rl.write(null, { ctrl: true, name: 'u' });
    rl.write(history[++index]);
  }
});

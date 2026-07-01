import * as readline from 'node:readline';
import * as fs from 'node:fs/promises';
import * as crypto from 'node:crypto';
import * as path from 'node:path';

function checksumNnue(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex').slice(0, 12);
}

async function ensureNnue(filepath) {
  const filename = path.basename(filepath);
  const match = filename.match(/^nn-([0-9a-f]{12})\.nnue$/);

  try {
    const buf = await fs.readFile(filepath);
    if (!match || checksumNnue(buf) === match[1]) return buf;
    console.error(`${filepath}: checksum mismatch, re-downloading`);
  } catch {
    if (!match) throw new Error(`${filepath} not found`);
    console.error(`${filepath}: missing, downloading`);
  }

  const url = `https://tests.stockfishchess.org/api/nn/${filename}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`failed to download ${url}: ${res.status} ${res.statusText}`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (checksumNnue(buf) !== match[1]) throw new Error(`${url}: downloaded file failed checksum validation`);

  await fs.writeFile(filepath, buf);
  return buf;
}

const createStockfish = await import(`../${process.argv[2] ?? 'sf_18.js'}`);
let history = [],
  index = 0;

const sf = await createStockfish.default();

for (let index = 0; ; index++) {
  const nnueFilename = sf.getRecommendedNnue(index);
  if (!nnueFilename) break;
  sf.setNnueBuffer(await ensureNnue(nnueFilename), index);
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: '',
  terminal: true,
});

rl.on('SIGINT', process.exit);

rl.on('line', async line => {
  history.push(line);
  index = history.length;
  if (line.startsWith('load ')) sf.setNnueBuffer(await ensureNnue(line.slice(5)), 0);
  else if (line.startsWith('big ')) sf.setNnueBuffer(await ensureNnue(line.slice(4)), 0);
  else if (line.startsWith('small ')) sf.setNnueBuffer(await ensureNnue(line.slice(6)), 1);
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

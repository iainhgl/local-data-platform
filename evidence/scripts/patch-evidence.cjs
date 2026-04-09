/**
 * Patches @evidence-dev/universal-sql build-parquet.js to fix a deadlock
 * that occurs on linux/arm64 when DuckDB WASM blocking mode tries to read
 * local parquet files via read_parquet.
 *
 * Root cause: DuckDB WASM blocking mode seizes the Node.js event loop, so
 * async file I/O callbacks (needed by NODE_FS protocol) never fire → deadlock.
 *
 * Fix: replace the DuckDB WASM COPY merge with native DuckDB (@duckdb/node-api),
 * which uses worker threads and does not block the event loop.
 */
const fs = require('fs');
const path = require('path');

const universalSqlDir = path.join(__dirname, '..', 'node_modules', '@evidence-dev', 'universal-sql', 'src');
const buildParquetFile = path.join(universalSqlDir, 'build-parquet.js');

if (!fs.existsSync(buildParquetFile)) {
  console.log('[patch-evidence] node_modules not yet installed, skipping patch');
  process.exit(0);
}

let buildParquet = fs.readFileSync(buildParquetFile, 'utf8');

if (buildParquet.includes('// PATCHED: use native DuckDB')) {
  console.log('[patch-evidence] build-parquet.js already patched, skipping');
  process.exit(0);
}

// Restore import to original (remove registerFile if added by old patch)
buildParquet = buildParquet.replace(
  "import { emptyDbFs, initDB, query, registerFile } from './client-duckdb/node.js';",
  "import { emptyDbFs, initDB, query } from './client-duckdb/node.js';"
);

// Restore parquetFiles to use full paths (remove basename change from old patch)
buildParquet = buildParquet.replace(
  "const parquetFiles = tmpFilenames.map((filename) => `'${path.basename(filename)}'`);",
  "const parquetFiles = tmpFilenames.map((filename) => `'${filename.replaceAll('\\\\', '/')}'`);"
);

// Remove the old registerFile loop if present
buildParquet = buildParquet.replace(
  "\tfor (const tmpFile of tmpFilenames) {\n\t\tawait registerFile(path.basename(tmpFile), tmpFile);\n\t}\n\tawait query(copy);",
  "\tawait query(copy);"
);

// Now replace the DuckDB WASM merge block with native DuckDB.
// The block to replace uses initDB() + query(copy) for the COPY step.
// We need to match the exact surrounding context to avoid false replacements.
const wasmMergePattern = /(\tawait fs\.mkdir\(path\.dirname\(outputFilepath\), \{ recursive: true \}\);\n)\t await query\(copy\);/;
const nativeMerge = `$1\t// PATCHED: use native DuckDB to merge parquet — DuckDB WASM blocking mode
\t// deadlocks on arm64 because async file I/O callbacks cannot fire while the
\t// event loop is seized. Native DuckDB uses worker threads instead.
\tconst { DuckDBInstance } = await import('@duckdb/node-api');
\tconst _mergeDb = await DuckDBInstance.create(':memory:');
\tconst _mergeConn = await _mergeDb.connect();
\tawait _mergeConn.run(copy);
\t_mergeConn.disconnectSync();
\t_mergeDb.closeSync();`;

// Try the exact pattern first
let patched = buildParquet.replace(wasmMergePattern, nativeMerge);

if (patched === buildParquet) {
  // Fallback: simple string replace without regex
  const oldMerge = '\tawait fs.mkdir(path.dirname(outputFilepath), { recursive: true });\n\tawait query(copy);';
  const newMerge = `\tawait fs.mkdir(path.dirname(outputFilepath), { recursive: true });

\t// PATCHED: use native DuckDB to merge parquet — DuckDB WASM blocking mode
\t// deadlocks on arm64 because async file I/O callbacks cannot fire while the
\t// event loop is seized. Native DuckDB uses worker threads instead.
\tconst { DuckDBInstance } = await import('@duckdb/node-api');
\tconst _mergeDb = await DuckDBInstance.create(':memory:');
\tconst _mergeConn = await _mergeDb.connect();
\tawait _mergeConn.run(copy);
\t_mergeConn.disconnectSync();
\t_mergeDb.closeSync();`;

  patched = buildParquet.replace(oldMerge, newMerge);

  if (patched === buildParquet) {
    console.error('[patch-evidence] ERROR: Could not find merge block to patch in build-parquet.js');
    console.error('[patch-evidence] The Evidence package may have been updated. Manual patch required.');
    process.exit(1);
  }
}

fs.writeFileSync(buildParquetFile, patched);
console.log('[patch-evidence] Patched build-parquet.js — native DuckDB merge replaces DuckDB WASM COPY');
console.log('[patch-evidence] Done');

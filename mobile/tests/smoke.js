/**
 * Mobile smoke check — plain Node, zero new dependencies.
 *
 * Run from mobile/:  `node tests/smoke.js`  (or `npm run smoke`)
 *
 * What it verifies (all WITHOUT a device/emulator — screen interactions are
 * NOT tested and nothing here claims they are):
 *  1. The bundled KaTeX stylesheet (`src/components/katexCss.ts`, loaded via
 *     Node type-stripping) is present, full-size, and contains the layout rules
 *     KaTeX output needs (.mfrac/.vlist/.sqrt) plus @font-face (fonts resolve
 *     to nothing in the offline WebView by design — serif fallback).
 *  2. The installed `katex` version matches the version the CSS was bundled
 *     from (major.minor must match; patch drift needs a CSS regen check).
 *  3. Representative LaTeX renders with the EXACT options LatexView uses
 *     (throwOnError/displayMode/strict/trust:false): valid samples must render,
 *     invalid/unsupported samples must throw (that throw drives the app's
 *     monospace-fallback path — never a crash).
 *  4. Every runtime dependency in package.json resolves (catches partial installs).
 *
 * Exit 0 = pass; non-zero = first failure message.
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const mobileDir = path.join(__dirname, '..');

async function main() {
  // 1. Bundled stylesheet integrity.
  const { KATEX_CSS } = await import('../src/components/katexCss.ts');
  assert.equal(typeof KATEX_CSS, 'string', 'KATEX_CSS must be a string');
  assert.ok(KATEX_CSS.length > 20000, `KATEX_CSS suspiciously small: ${KATEX_CSS.length}`);
  for (const rule of ['.mfrac', '.vlist', '.sqrt', '@font-face', '.katex-display']) {
    assert.ok(KATEX_CSS.includes(rule), `KATEX_CSS missing ${rule}`);
  }
  console.log(`PASS katex-css (${KATEX_CSS.length} bytes, layout rules present)`);

  // 2. Installed katex matches the bundled CSS major.minor.
  const katexPkg = require('../node_modules/katex/package.json');
  const cssHeader = fs.readFileSync(
    path.join(mobileDir, 'src', 'components', 'katexCss.ts'), 'utf8',
  );
  const bundled = cssHeader.match(/katex@(\d+\.\d+\.\d+)/)?.[1];
  assert.ok(bundled, 'katexCss.ts header must state the bundled katex version');
  assert.equal(
    bundled.split('.').slice(0, 2).join('.'),
    katexPkg.version.split('.').slice(0, 2).join('.'),
    `CSS bundled from ${bundled} but installed katex is ${katexPkg.version} — regenerate katexCss.ts`,
  );
  console.log(`PASS katex-version (bundled ${bundled}, installed ${katexPkg.version})`);

  // 3. Render behaviour with LatexView's exact options.
  const katex = require('../node_modules/katex');
  const OPTS = { throwOnError: true, displayMode: true, strict: true, trust: false };
  const valid = [
    '\\frac{1}{2}+\\sqrt{16}',
    'x_{1}-x_{2}+x_{0}=0',
    '2\\cdot x+3\\times y',
    '\\sum_{j}L_{ij}\\frac{\\partial F_{j}}{\\partial x_{j}}',
  ];
  for (const latex of valid) {
    const html = katex.renderToString(latex, OPTS);
    assert.ok(html.includes('katex'), `no KaTeX output for ${latex}`);
    assert.ok(!/<script/i.test(html), `script tag in KaTeX output for ${latex}`);
  }
  console.log(`PASS katex-render-valid (${valid.length} samples)`);
  // Throwing inputs drive the app's monospace-fallback path (verified throws
  // with LatexView's exact options; ''/whitespace short-circuit before KaTeX).
  const invalid = ['\\unknowncmd{4}', '\\sqrt{', 'x^'];
  for (const latex of invalid) {
    // ''/whitespace: LatexView short-circuits to fallback before calling KaTeX.
    if (!latex.trim()) continue;
    assert.throws(() => katex.renderToString(latex, OPTS), `expected throw for ${latex}`);
  }
  console.log('PASS katex-render-invalid (fallback path triggers)');

  // 4. Runtime deps resolve.
  const pkg = require('../package.json');
  for (const dep of Object.keys(pkg.dependencies)) {
    require.resolve(dep, { paths: [mobileDir] });
  }
  console.log(`PASS deps-resolve (${Object.keys(pkg.dependencies).length} deps)`);
}

main().then(
  () => console.log('SMOKE OK'),
  (e) => {
    console.error(`SMOKE FAIL: ${e.message}`);
    process.exit(1);
  },
);

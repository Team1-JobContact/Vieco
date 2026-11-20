const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

test('company names and logo marks preserve the intended demo brands', () => {
    const dom = new JSDOM('', { url: 'https://vieco-frontend.onrender.com', runScripts: 'outside-only' });
    try {
        for (const file of ['src/services/auth-api.js', 'src/shared/layout.js']) {
            dom.window.eval(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'));
        }
        const V = dom.window.Vieco;
        for (const [name, brand, mark] of [
            ['Tập đoàn FPT', 'FPT', 'FPT'],
            ['Công ty Cổ phần Dịch vụ Di động Trực tuyến (MoMo)', 'MoMo', 'MOMO'],
            ['Công ty Cổ phần Sữa Việt Nam (Vinamilk)', 'Vinamilk', 'Vinamilk'],
            ['Công ty Cổ phần Xây dựng Coteccons', 'Coteccons', 'C'],
            ['Tổng Công ty Hàng không Việt Nam (Vietnam Airlines)', 'Vietnam Airlines', 'VA'],
            ['Hệ thống Nhà thuốc FPT Long Châu', 'FPT Long Châu', 'FPT'],
        ]) {
            assert.equal(V.brandName(name), brand);
            assert.equal(V.brand(name), brand.toUpperCase());
            assert.equal(V.brandMark(name), mark);
            assert.equal(V.logo(name).textContent, mark);
        }
        assert.equal(V.logo('<img src=x onerror=alert(1)>').querySelector('img'), null);
    } finally {
        dom.window.close();
    }
});

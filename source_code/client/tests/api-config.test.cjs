const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const source = fs.readFileSync(path.join(__dirname, '../src/services/auth-api.js'), 'utf8');

for (const origin of ['http://localhost:5500', 'http://127.0.0.1:5500', 'http://[::1]:5500', 'https://vieco-frontend.onrender.com']) {
    test('registration and login use the correct API from ' + origin, async () => {
        const dom = new JSDOM('', { url: origin, runScripts: 'outside-only' });
        try {
            const w = dom.window;
            const calls = [];
            w.fetch = async (url, options) => {
                calls.push({ url, method: options.method });
                return { ok: true, headers: { get: () => 'application/json' }, json: async () => ({}) };
            };
            w.eval(source);
            const base = origin === 'https://vieco-frontend.onrender.com'
                ? 'https://vieco.onrender.com/api/v1'
                : 'http://127.0.0.1:8000/api/v1';
            await w.ViecoAuthApi.registerUser({ email: 'test@example.com' });
            await w.ViecoAuthApi.loginUser({ email: 'test@example.com' });
            assert.deepEqual(calls, [
                { url: base + '/auth/register', method: 'POST' },
                { url: base + '/auth/login', method: 'POST' },
            ]);
        } finally {
            dom.window.close();
        }
    });
}

test('explicit API configuration still overrides defaults and trims trailing slashes', () => {
    const dom = new JSDOM('', { url: 'https://frontend.example.com', runScripts: 'outside-only' });
    try {
        const w = dom.window;
        w.eval(source);
        w.localStorage.setItem('vieco_api_base_url', 'https://stored.example.com/api/v1/');
        assert.equal(w.ViecoAuthApi.getApiBaseUrl(), 'https://stored.example.com/api/v1');
        w.VIECO_API_BASE_URL = 'https://configured.example.com/api/v1/';
        assert.equal(w.ViecoAuthApi.getApiBaseUrl(), 'https://configured.example.com/api/v1');
    } finally {
        dom.window.close();
    }
});

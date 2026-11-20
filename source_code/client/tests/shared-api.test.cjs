const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const script = fs.readFileSync(path.resolve(__dirname, '../src/services/auth-api.js'), 'utf8');

test('shared frontend sends API requests to the server users actually opened', () => {
    for (const origin of ['https://vieco.example', 'http://192.168.1.20:8000']) {
        const dom = new JSDOM('', {url: origin + '/pages/login.html', runScripts: 'outside-only'});
        dom.window.eval(script);
        assert.equal(dom.window.ViecoAuthApi.getApiBaseUrl(), origin + '/api/v1');
        dom.window.close();
    }
});

test('local frontend development keeps the separate backend and explicit overrides', () => {
    const dom = new JSDOM('', {url: 'http://localhost:5500', runScripts: 'outside-only'});
    dom.window.eval(script);
    assert.equal(dom.window.ViecoAuthApi.getApiBaseUrl(), 'http://127.0.0.1:8000/api/v1');
    dom.window.localStorage.setItem('vieco_api_base_url', 'https://api.example/api/v1/');
    assert.equal(dom.window.ViecoAuthApi.getApiBaseUrl(), 'https://api.example/api/v1');
    dom.window.VIECO_API_BASE_URL = 'https://override.example/api/v1/';
    assert.equal(dom.window.ViecoAuthApi.getApiBaseUrl(), 'https://override.example/api/v1');
    dom.window.close();
});

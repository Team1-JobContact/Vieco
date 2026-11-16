const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(root, name), 'utf8');
const tick = () => new Promise(resolve => setTimeout(resolve, 15));

function setup(markup = '<main id="app"></main>', handlers = {}) {
    const dom = new JSDOM(markup, { url: 'http://localhost/pages/admin.html', runScripts: 'outside-only', pretendToBeVisual: true });
    const w = dom.window;
    w.eval(source('src/services/auth-api.js'));
    w.ViecoAuthApi.getApiBaseUrl = () => '/api/v1';
    const calls = [];
    w.fetch = async (url, request) => {
        calls.push({ url, request });
        const key = Object.keys(handlers).find(key => url.includes(key));
        const result = key ? await handlers[key](url, request) : { items: [], total: 0, total_pages: 0 };
        return { ok: true, status: 200, json: async () => result };
    };
    w.eval(source('src/shared/layout.js'));
    return { dom, w, calls };
}

test('network failure keeps session and allows current-user retry', async () => {
    const { dom, w } = setup();
    let requests = 0;
    w.ViecoAuthApi.getAuthToken = () => 'session-token';
    w.ViecoAuthApi.clearAuthSession = () => assert.fail('Network failure must keep credentials');
    w.ViecoAuthApi.fetchCurrentUser = async () => {
        if (++requests === 1) throw new Error('Mất kết nối');
        return { role: 'ADMIN', full_name: 'Admin' };
    };
    await assert.rejects(w.Vieco.currentUser(), /Mất kết nối/);
    assert.equal((await w.Vieco.currentUser()).role, 'ADMIN');
    dom.window.close();
});

test('modal traps focus, restores opener and closes once', () => {
    const { dom, w } = setup('<button id="opener">Mở</button>');
    const opener = w.document.getElementById('opener');
    opener.focus();
    let closed = 0;
    const close = w.Vieco.modal(w.Vieco.h('div', {}, w.Vieco.h('input', {}), w.Vieco.h('button', { text: 'Lưu' })), { onClose: () => closed++ });
    const items = w.document.querySelectorAll('.v-modal button, .v-modal input');
    items[items.length - 1].focus();
    w.document.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    assert.equal(w.document.activeElement, items[0]);
    w.document.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    close();
    assert.equal(closed, 1);
    assert.equal(w.document.activeElement, opener);
    dom.window.close();
});

test('save button prevents concurrent requests and unlocks after success', async () => {
    let resolveSave;
    const { dom, w, calls } = setup(undefined, {
        '/saved-jobs/1': () => new Promise(resolve => { resolveSave = resolve; }),
        '/saved-jobs': () => ({ items: [] }),
    });
    w.ViecoAuthApi.getAuthToken = () => 'session-token';
    w.ViecoAuthApi.fetchCurrentUser = async () => ({ role: 'CANDIDATE' });
    const button = w.Vieco.saveButton({ id: 1 });
    w.document.body.appendChild(button);
    await tick();
    button.click(); button.click();
    await tick();
    assert.equal(calls.filter(call => call.url.endsWith('/saved-jobs/1')).length, 1);
    assert.equal(button.disabled, true);
    resolveSave({ saved: true });
    await tick();
    assert.equal(button.disabled, false);
    assert.equal(button.getAttribute('aria-pressed'), 'true');
    dom.window.close();
});

test('admin users render as text and lock through the API after confirmation', async () => {
    const user = { id: 7, full_name: '<img src=x>', email: 'person@example.com', role: 'CANDIDATE', status: 'ACTIVE' };
    const { dom, w, calls } = setup(undefined, { '/admin/users': () => ({ items: [user], total: 1, page: 1, total_pages: 1 }) });
    w.Vieco.confirm = async () => true;
    w.eval(source('src/features/admin/admin-management.js'));
    w.ViecoAdminManagement.users(w.document.getElementById('app'));
    await tick();
    assert.equal(w.document.querySelectorAll('#app img').length, 0);
    const lock = [...w.document.querySelectorAll('button')].find(button => button.textContent === 'Khóa');
    lock.click();
    await tick();
    const request = calls.find(call => call.url.endsWith('/admin/users/7/status'));
    assert.equal(request.request.method, 'PATCH');
    assert.equal(JSON.parse(request.request.body).status, 'LOCKED');
    dom.window.close();
});

test('admin category editor sends existing identity and visibility', async () => {
    const { dom, w, calls } = setup(undefined, { '/admin/categories': () => ({ industries: [{ id: 3, name: 'CNTT', slug: 'cntt', is_active: true }], skills: [], provinces: [] }) });
    w.eval(source('src/features/admin/admin-management.js'));
    w.ViecoAdminManagement.categories(w.document.getElementById('app'));
    await tick();
    [...w.document.querySelectorAll('button')].find(button => button.textContent === 'Sửa / ẩn').click();
    w.document.querySelector('.v-modal input[type="checkbox"]').checked = false;
    w.document.querySelector('.v-modal form').dispatchEvent(new w.Event('submit', { bubbles: true, cancelable: true }));
    await tick();
    const call = calls.find(call => call.request.method === 'PATCH');
    assert.equal(call.url, '/api/v1/admin/categories/industries/3');
    assert.equal(JSON.parse(call.request.body).is_active, false);
    dom.window.close();
});

test('published content is rendered as text', async () => {
    const { dom, w } = setup(undefined, { '/pages/': () => ({ title: 'Điều khoản', content: '<script>alert(1)</script>' }) });
    w.eval(source('src/features/admin/content-ui.js'));
    await tick();
    assert.equal(w.document.querySelectorAll('#app script').length, 0);
    assert.match(w.document.getElementById('app').textContent, /<script>/);
    dom.window.close();
});

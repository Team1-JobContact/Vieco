const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(root,name),'utf8');
const tick = () => new Promise(resolve => setTimeout(resolve, 10));

function stubApi(w, handlers) {
    const calls = [];
    w.fetch = async (url, request) => {
        const path = url.replace('/api/v1', '');
        calls.push(path);
        const key = Object.keys(handlers).find(prefix => path.startsWith(prefix));
        const data = key ? handlers[key](path, request) : {items: [], total: 0, page: 1, total_pages: 0};
        return {ok: true, status: 200, json: async () => data};
    };
    w.eval(source('src/services/auth-api.js'));
    w.ViecoAuthApi.getApiBaseUrl = () => '/api/v1';
    w.eval(source('src/shared/layout.js'));
    return calls;
}
const unsafeJob = {id: 1, title: '<img src=x onerror=alert(1)>', company_name: 'Company', skills: []};

test('home renders trending jobs and companies from the API as text', async () => {
    const dom = new JSDOM(source('index.html'), {url: 'http://localhost/', runScripts: 'outside-only', pretendToBeVisual: true});
    const w = dom.window;
    const calls = stubApi(w, {
        '/categories': () => ({industries: [{id: 7, name: 'CNTT'}], provinces: [], skills: []}),
        '/jobs': () => ({items: [unsafeJob], total: 1, page: 1, total_pages: 1}),
        '/companies': () => ({items: [{id: 3, name: 'Company', open_jobs: 2}], total: 1, page: 1, total_pages: 1})
    });
    w.eval(source('src/features/jobs/home-ui.js'));
    await tick(); await tick();
    assert.equal(w.document.querySelectorAll('#jobs-container article').length, 1);
    assert.equal(w.document.querySelectorAll('#jobs-container img').length, 0);
    assert.equal(w.document.querySelector('#jobs-container h3 a').textContent, unsafeJob.title);
    assert.match(w.document.querySelector('#jobs-container h3 a').getAttribute('href'), /pages\/job\.html\?id=1$/);
    assert.equal(w.document.querySelectorAll('#home-companies article').length, 1);
    assert.ok(w.document.querySelector('header.v-header') && w.document.querySelector('footer.v-footer'));
    w.document.querySelectorAll('#jobs-filter button')[1].click();
    await tick();
    assert.ok(calls.some(path => path.startsWith('/jobs?') && path.includes('industry_id=7')));
    dom.window.close();
});

test('jobs page searches, filters and paginates through the API', async () => {
    const dom = new JSDOM(source('pages/jobs.html'), {url: 'http://localhost/pages/jobs.html?q=Python', runScripts: 'outside-only', pretendToBeVisual: true});
    const w = dom.window;
    w.scrollTo = () => {};
    const calls = stubApi(w, {
        '/categories': () => ({industries: [], provinces: [], skills: []}),
        '/jobs': path => ({items: [unsafeJob], total: 25, page: Number(new URLSearchParams(path.split('?')[1]).get('page')), total_pages: 3})
    });
    w.eval(source('src/features/jobs/jobs-ui.js'));
    await tick(); await tick();
    assert.ok(calls.some(path => path.startsWith('/jobs?') && path.includes('q=Python') && path.includes('page=1')));
    assert.equal(w.document.getElementById('jobs-total').textContent, '25');
    assert.equal(w.document.querySelectorAll('#jobs-container article').length, 1);
    assert.equal(w.document.querySelectorAll('#jobs-container img').length, 0);
    w.document.querySelector('#jobs-pagination button[aria-label="Trang 2"]').click();
    await tick();
    assert.ok(calls.at(-1).includes('page=2') && calls.at(-1).includes('q=Python'));
    assert.match(w.location.search, /page=2/);
    dom.window.close();
});

test('reset password validates before sending, strips URL secret and reports success only on success',async()=>{
    const dom=new JSDOM(source('pages/account.html'),{url:'http://localhost/pages/account.html?action=reset-password&token=secret-token',runScripts:'outside-only'});
    const w=dom.window;
    let calls=0,cleared=false,fail=true;
    w.eval(source('src/services/auth-api.js'));
    w.ViecoAuthApi.clearAuthSession=()=>{cleared=true;};
    w.ViecoAccountApi={submit:async(action,payload)=>{
        calls++;
        assert.equal(action,'reset-password');
        assert.equal(payload.token,'secret-token');
        if(fail)throw new Error('SMTP unavailable');
        return {message:'Changed'};
    }};
    w.eval(source('src/features/auth/account-ui.js'));
    await tick();
    assert.equal(w.location.search.includes('secret-token'),false);
    const form=w.document.getElementById('account-form');
    form.elements.password.value='short';
    form.dispatchEvent(new w.Event('submit',{cancelable:true}));
    await tick();
    assert.equal(calls,0);
    form.elements.password.value='NewPass123';
    form.dispatchEvent(new w.Event('submit',{cancelable:true}));
    await tick();
    assert.equal(form.hidden,false);
    assert.equal(cleared,false);
    assert.equal(w.document.getElementById('account-message').textContent,'SMTP unavailable');
    fail=false;
    form.dispatchEvent(new w.Event('submit',{cancelable:true}));
    await tick();
    assert.equal(cleared,true);
    assert.equal(form.hidden,true);
    dom.window.close();
});

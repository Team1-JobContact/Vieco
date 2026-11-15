const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(root,name),'utf8');
const tick = () => new Promise(resolve => setTimeout(resolve, 10));

test('public jobs are loaded, searched and rendered as text with real details', async () => {
    const dom = new JSDOM(source('index.html'), {url:'http://localhost/',runScripts:'outside-only'});
    const w=dom.window;
    w.fetch=async () => ({ok:true,json:async () => ({})});
    w.ViecoAuthApi={getApiBaseUrl:()=>'/api/v1',getAuthToken:()=>null};
    const calls=[];
    w.ViecoJobsApi={
        list: async (query,page) => {calls.push([query,page]);return {items:[{id:1,title:'<img src=x onerror=alert(1)>',company_name:'Company'}],page,total_pages:2};},
        get: async id => ({description:'Real description',requirements:'Requirements'})
    };
    w.eval(source('src/features/jobs/home-ui.js'));
    await tick();
    assert.equal(w.document.querySelectorAll('#jobs-container article').length,1);
    assert.equal(w.document.querySelectorAll('#jobs-container img').length,0);
    w.document.querySelector('#jobs-container button').click();
    await tick();
    assert.match(w.document.querySelector('#jobs-container').textContent,/Real description/);
    w.document.getElementById('keyword-input').value='Python';
    w.handleSearch();
    await tick();
    assert.deepEqual(calls.at(-1),['Python',1]);
    w.document.querySelector('#jobs-pagination button:last-child').click();
    await tick();
    assert.deepEqual(calls.at(-1),['Python',2]);
    w.ViecoJobsApi.list=async()=>{throw new Error('API unavailable');};
    w.handleSearch();
    await tick();
    assert.equal(w.document.getElementById('jobs-container').textContent,'API unavailable');
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

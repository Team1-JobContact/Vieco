const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'pages/employer.html'), 'utf8');
const apiSource = fs.readFileSync(path.join(root, 'assets/js/employer-api.js'), 'utf8');
const uiSource = fs.readFileSync(path.join(root, 'assets/js/employer-ui.js'), 'utf8');
const companyRecord = { id: 4, name: 'Vieco', industry_id: 1, province_id: 2, size: '51-200',
    address: 'Hà Nội', website: null, description: null, status: 'APPROVED', member_role: 'OWNER' };
const jobRecord = { id: 42, company_id: 4, title: 'Backend Python', industry_id: 1, province_id: 2,
    work_address: 'Hà Nội', employment_type: 'FULL_TIME', experience_level: 'FROM_1_TO_3', positions: 2,
    salary_min: 0, salary_max: 20000000, salary_currency: 'VND', deadline: '2099-01-01',
    description: 'Phát triển API', requirements: 'Có kiến thức Python', benefits: 'Đào tạo', status: 'DRAFT' };
const tick = () => new Promise(resolve => setImmediate(resolve));

async function setup(t, options = {}) {
    const dom = new JSDOM(html, { url: 'http://localhost/pages/employer.html' + (options.url || ''), runScripts: 'outside-only' });
    t.after(() => dom.window.close());
    const w = dom.window, calls = [];
    let currentCompany = options.company === undefined ? { ...companyRecord } : options.company;
    let submitFailures = options.submitFailures || 0;
    w.confirm = () => true;
    w.ViecoAuthApi = { getAuthToken: () => 'test-token', getApiBaseUrl: () => 'http://test/api/v1',
        fetchCurrentUser: async () => ({ full_name: 'Nhà tuyển dụng', role: options.role || 'EMPLOYER' }),
        clearAuthSession() {}, logoutUser: async () => ({}) };
    w.fetch = async (url, request) => {
        const endpoint = url.replace('http://test/api/v1', '');
        const body = request.body && JSON.parse(request.body);
        calls.push({ endpoint, method: request.method, body });
        let code = 200, data;
        if (options.respond) {
            const override = await options.respond(endpoint, request.method, body);
            if (override) return { ok: override.code < 400, status: override.code, json: async () => override.data };
        }
        if (endpoint === '/categories') data = { industries: [{ id: 1, name: 'Công nghệ' }], provinces: [{ id: 2, name: 'Hà Nội' }] };
        else if (endpoint === '/employer/company') {
            if (request.method !== 'GET') currentCompany = { ...companyRecord, status: currentCompany ? currentCompany.status : 'PENDING', ...body };
            if (currentCompany) data = currentCompany;
            else { code = 404; data = { detail: 'Chưa có hồ sơ' }; }
        } else if (endpoint === '/employer/company/resubmit') data = currentCompany = { ...currentCompany, status: 'PENDING', reject_reason: null };
        else if (endpoint === '/employer/jobs/42' && request.method === 'GET') data = { ...jobRecord, ...options.job };
        else if (endpoint === '/employer/jobs' || endpoint === '/employer/jobs/42') data = { ...jobRecord, ...body };
        else if (endpoint === '/employer/jobs/42/submit') {
            if (submitFailures-- > 0) { code = 500; data = { detail: 'Thử lại' }; }
            else data = { ...jobRecord, status: 'PENDING' };
        } else { code = 404; data = { detail: 'Not Found' }; }
        return { ok: code < 400, status: code, json: async () => JSON.parse(JSON.stringify(data)) };
    };
    w.eval(apiSource);
    w.eval(uiSource);
    for (let i = 0; i < 5; i++) await tick();
    function fill(id, data) {
        const form = w.document.getElementById(id);
        for (const [key, value] of Object.entries(data)) {
            const input = form.elements.namedItem(key);
            if (input) { input.value = value == null ? '' : String(value); input.dispatchEvent(new w.Event('input', { bubbles: true })); }
        }
    }
    async function submit(id, buttonId) {
        const form = w.document.getElementById(id);
        form.dispatchEvent(new w.SubmitEvent('submit', { bubbles: true, cancelable: true, submitter: w.document.getElementById(buttonId) }));
        for (let i = 0; i < 5; i++) await tick();
    }
    return { w, calls, fill, submit, $: id => w.document.getElementById(id) };
}

test('only employers can open forms, role is verified by /auth/me', async t => {
    const { $, calls } = await setup(t, { role: 'CANDIDATE' });
    assert.equal($('workspace').hidden, true);
    assert.equal(calls.length, 0);
    assert.match($('page-message').textContent, /Nhà tuyển dụng/);
});

test('new company form saves actual API record and displays PENDING', async t => {
    const { $, fill, submit, calls } = await setup(t, { company: null });
    assert.equal($('company-fields').disabled, false);
    fill('company-form', companyRecord);
    await submit('company-form', 'save-company');
    assert.equal(calls.filter(c => c.endpoint === '/employer/company' && c.method === 'POST').length, 1);
    assert.equal($('company-status').textContent, 'Chờ duyệt');
    assert.equal($('job-fields').disabled, true);
});

test('company error fields and server failures keep unsaved input', async t => {
    const { $, fill, submit } = await setup(t, { respond: (p, method) => p === '/employer/company' && method === 'PATCH'
        ? { code: 422, data: { detail: [{ loc: ['body', 'name'], msg: 'Value error, Tên chưa hợp lệ' }] } } : null });
    fill('company-form', { name: 'Tên giữ nguyên' });
    await submit('company-form', 'save-company');
    assert.equal($('company-name').value, 'Tên giữ nguyên');
    assert.equal($('company-name').getAttribute('aria-invalid'), 'true');
    assert.match($('company-name-error').textContent, /Tên chưa hợp lệ/);
    assert.equal($('company-fields').disabled, false);
});

test('rejected company shows reason and saves edits before resubmitting', async t => {
    const { $, calls } = await setup(t, { company: { ...companyRecord, status: 'REJECTED', reject_reason: '<img src=x onerror=alert(1)>' } });
    assert.match($('company-rejection').textContent, /<img/);
    assert.equal($('company-rejection').querySelector('img'), null);
    assert.equal($('job-fields').disabled, true);
    $('resubmit-company').click();
    for (let i = 0; i < 5; i++) await tick();
    assert.deepEqual(calls.filter(c => c.method !== 'GET').map(c => [c.method, c.endpoint]), [
        ['PATCH', '/employer/company'], ['POST', '/employer/company/resubmit']
    ]);
    assert.equal($('company-status').textContent, 'Chờ duyệt');
});

test('company MEMBER cannot edit or resubmit', async t => {
    const { $ } = await setup(t, { company: { ...companyRecord, member_role: 'MEMBER', status: 'REJECTED' } });
    assert.equal($('company-fields').disabled, true);
    assert.equal($('company-permission').hidden, false);
});

test('editing loads all old job values including zero salary and rejection reason', async t => {
    const { $, w } = await setup(t, { url: '?job_id=42#job', job: { status: 'REJECTED', reject_reason: 'Cần bổ sung mô tả' } });
    assert.equal($('job-fields').disabled, false);
    assert.equal($('job-title').value, jobRecord.title);
    assert.equal($('job-salary-min').value, '0');
    assert.equal($('job-experience').value, 'FROM_1_TO_3');
    assert.match($('job-rejection').textContent, /Cần bổ sung/);
    assert.equal(w.document.querySelector('[aria-current="page"]').id, 'job-tab');
});

test('pending job and foreign company job cannot be edited', async t => {
    const pending = await setup(t, { url: '?job_id=42#job', job: { status: 'PENDING' } });
    assert.equal(pending.$('job-fields').disabled, true);
    const foreign = await setup(t, { url: '?job_id=42#job', job: { company_id: 99 } });
    assert.equal(foreign.$('job-fields').disabled, true);
    assert.match(foreign.$('job-message').textContent, /không thuộc/);
});

test('draft save only needs title, duplicate submissions are blocked while busy', async t => {
    const { $, fill, submit, calls } = await setup(t, { url: '#job' });
    fill('job-form', { title: 'Tin nháp mới' });
    const first = submit('job-form', 'save-draft');
    const second = submit('job-form', 'save-draft');
    await Promise.all([first, second]);
    assert.equal(calls.filter(c => c.endpoint === '/employer/jobs' && c.method === 'POST').length, 1);
    assert.equal($('job-status').textContent, 'Nháp');
    assert.equal($('job-fields').disabled, false);
});

test('submit validates required fields without issuing a write', async t => {
    const { $, fill, submit, calls } = await setup(t, { url: '#job' });
    fill('job-form', { title: 'Tin chưa đủ thông tin' });
    await submit('job-form', 'submit-job');
    assert.equal(calls.some(c => c.method !== 'GET'), false);
    assert.equal($('job-description').getAttribute('aria-invalid'), 'true');
});

test('retry after submit failure PATCHes saved ID instead of creating another job', async t => {
    const { $, w, fill, submit, calls } = await setup(t, { url: '#job', submitFailures: 1 });
    fill('job-form', jobRecord);
    await submit('job-form', 'submit-job');
    assert.match($('job-message').textContent, /Đã lưu nội dung tin nhưng chưa gửi duyệt/);
    assert.equal(w.location.search, '?job_id=42');
    await submit('job-form', 'submit-job');
    assert.equal(calls.filter(c => c.endpoint === '/employer/jobs' && c.method === 'POST').length, 1);
    assert.equal(calls.filter(c => c.endpoint === '/employer/jobs/42' && c.method === 'PATCH').length, 1);
    assert.equal($('job-status').textContent, 'Chờ duyệt');
    assert.equal($('job-fields').disabled, true);
});

test('missing PB-014 endpoint keeps input and does not claim successful save', async t => {
    const { $, fill, submit } = await setup(t, { url: '#job', respond: p => p === '/employer/jobs' ? { code: 404, data: { detail: 'Not Found' } } : null });
    fill('job-form', { title: 'Dữ liệu chưa lưu' });
    await submit('job-form', 'save-draft');
    assert.equal($('job-title').value, 'Dữ liệu chưa lưu');
    assert.equal($('job-status').textContent, 'Chưa lưu');
    assert.match($('job-message').textContent, /Chưa thể/);
});

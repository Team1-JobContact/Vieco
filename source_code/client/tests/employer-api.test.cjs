const { test } = require('node:test');
const assert = require('node:assert/strict');
const Api = require('../assets/js/employer-api.js');

const company = { name: ' Công ty Vieco ', industry_id: '1', province_id: '2', size: '51-200',
    address: ' 1 Nguyễn Trãi ', website: 'https://vieco.vn', description: '' };
const job = { title: 'Backend Python', province_id: '2', work_address: 'Hà Nội', description: 'Phát triển API',
    requirements: 'Python', employment_type: 'FULL_TIME', deadline: '2027-01-01' };

test('company validation trims values, converts IDs and leaves optional text null', () => {
    const r = Api.validateCompany(company);
    assert.equal(r.valid, true);
    assert.equal(r.payload.name, 'Công ty Vieco');
    assert.equal(r.payload.industry_id, 1);
    assert.equal(r.payload.description, null);
    assert.equal(r.payload.address, '1 Nguyễn Trãi');
    assert.equal('status' in r.payload, false);
});

test('company validation rejects required fields, invalid IDs, size and website', () => {
    const r = Api.validateCompany({ ...company, name: ' ', industry_id: '1.2', province_id: '-1', size: 'invalid', website: 'javascript:alert(1)' });
    assert.equal(r.valid, false);
    for (const field of ['name', 'industry_id', 'province_id', 'size', 'website']) assert.ok(r.errors[field]);
});

test('draft only needs title; submit requires full fields and a real date', () => {
    assert.equal(Api.validateJob({ title: 'Nháp' }, false, '2026-11-13').valid, true);
    const r = Api.validateJob({ title: 'Nháp' }, true, '2026-11-13');
    for (const field of ['description', 'requirements', 'province_id', 'work_address', 'employment_type', 'deadline']) assert.ok(r.errors[field]);
    assert.equal(Api.validateJob(job, true, '2026-11-13').valid, true);
    assert.ok(Api.validateJob({ ...job, deadline: '2027-02-30' }, true, '2026-11-13').errors.deadline);
});

test('salary, positions, enum and date errors are reported at their fields', () => {
    const r = Api.validateJob({ ...job, salary_min: '200', salary_max: '100', positions: '0',
        experience_level: 'FAKE', employment_type: 'FAKE', deadline: '2026-11-12' }, true, '2026-11-13');
    for (const field of ['salary_max', 'positions', 'experience_level', 'employment_type', 'deadline']) assert.ok(r.errors[field]);
    assert.ok(Api.validateJob({ ...job, salary_min: '9007199254740993' }, false).errors.salary_min);
    assert.equal(Api.validateJob({ ...job, salary_min: '0', salary_max: '0' }, true, '2026-11-13').payload.salary_min, 0);
});

test('deadline accepts today and business date follows Vietnam at the UTC boundary', () => {
    assert.equal(Api.validateJob({ ...job, deadline: '2026-11-13' }, true, '2026-11-13').valid, true);
    assert.equal(Api.localDate(new Date('2026-11-12T18:00:00Z')), '2026-11-13');
});

test('employer error parser does not turn all conflicts into duplicate email errors', () => {
    const conflict = Api.parseError(409, { detail: 'Chỉ gửi duyệt tin nháp' });
    assert.equal(conflict.message, 'Chỉ gửi duyệt tin nháp');
    assert.deepEqual(conflict.fieldErrors, {});
    const validation = Api.parseError(422, { detail: [{ loc: ['body', 'title'], msg: 'Value error, Tiêu đề quá dài' }] });
    assert.equal(validation.fieldErrors.title, 'Tiêu đề quá dài');
    assert.equal(Api.parseError(403, {}).message, 'Bạn không có quyền thực hiện thao tác này.');
});

test('client uses bearer token and expected methods without allowing body-controlled IDs', async () => {
    const calls = [];
    const client = Api.createClient({ baseUrl: 'http://test/api/v1/', token: 'test-token', fetch: async (url, options) => {
        calls.push({ url, ...options });
        return { ok: true, status: 200, json: async () => ({ id: 7 }) };
    } });
    await client.saveCompany(false, { name: 'A' });
    await client.saveCompany(true, { name: 'B' });
    await client.job(7);
    await client.saveJob(null, { title: 'A' });
    await client.saveJob(7, { title: 'B' });
    await client.submitJob(7);
    assert.deepEqual(calls.map(c => [c.method, c.url.replace('http://test/api/v1', '')]), [
        ['POST', '/employer/company'], ['PATCH', '/employer/company'], ['GET', '/employer/jobs/7'],
        ['POST', '/jobs'], ['PATCH', '/jobs/7'], ['POST', '/jobs/7/submit']
    ]);
    assert.ok(calls.every(c => c.headers.Authorization === 'Bearer test-token'));
});

test('HTTP and network failures never report save success', async () => {
    const client = Api.createClient({ baseUrl: 'http://test', token: 't', fetch: async () => ({
        ok: false, status: 404, json: async () => ({ detail: 'Not Found' })
    }) });
    await assert.rejects(client.saveJob(null, { title: 'A' }), e => e.status === 404);
    const offline = Api.createClient({ baseUrl: 'http://test', token: 't', fetch: async () => { throw new TypeError('Failed to fetch'); } });
    await assert.rejects(offline.company(), /Không thể kết nối/);
});

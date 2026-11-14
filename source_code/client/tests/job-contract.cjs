// Emit requests from the real PB-015 client for the FastAPI integration test.
const fs = require('node:fs');
const Api = require('../assets/js/employer-api.js');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const validation = Api.validateJob(input.fields, Boolean(input.submitValidation));
if (!validation.valid) throw new Error(JSON.stringify(validation.errors));
const requests = [];
const client = Api.createClient({ baseUrl: 'http://integration/api/v1', token: 'test', fetch: async (url, options) => {
    requests.push({ path: new URL(url).pathname, method: options.method,
        body: options.body ? JSON.parse(options.body) : undefined });
    return { ok: true, status: 200, json: async () => ({}) };
} });
(async () => {
    if (input.jobId) await client.job(input.jobId);
    await client.saveJob(input.jobId || null, validation.payload);
    if (input.jobId && input.submit) await client.submitJob(input.jobId);
    process.stdout.write(JSON.stringify(requests));
})().catch(error => { process.stderr.write(error.message); process.exitCode = 1; });

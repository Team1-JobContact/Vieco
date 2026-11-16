const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(root, name), 'utf8');

test('closed jobs can extend with Vietnam date; removed jobs expose no reopen or extend', async () => {
    const dom = new JSDOM('<main id="app"></main>', {
        url: 'http://localhost/pages/employer-jobs.html', runScripts: 'outside-only', pretendToBeVisual: true,
    });
    try {
        const w = dom.window;
        w.eval(source('src/services/auth-api.js'));
        w.eval(source('src/services/employer-api.js'));
        w.eval(source('src/shared/layout.js'));
        w.Vieco.requireRole = async () => ({ role: 'EMPLOYER' });
        w.ViecoEmployerApi.localDate = () => '2026-11-17';
        w.Vieco.api = async endpoint => endpoint === '/employer/company'
            ? { id: 1, name: 'Test company', status: 'APPROVED', member_role: 'OWNER' }
            : { items: [
                { id: 1, title: 'Closed job', status: 'CLOSED', deadline: '2026-11-16' },
                { id: 2, title: 'Removed job', status: 'CLOSED', removed_at: '2026-11-16T10:00:00Z' },
            ], page: 1, total_pages: 1 };
        w.eval(source('src/features/employer/employer-jobs-ui.js'));
        await new Promise(resolve => setTimeout(resolve, 20));
        const rows = [...w.document.querySelectorAll('article.v-row')];
        assert.equal(rows.length, 2);
        assert.ok(rows[0].textContent.includes('Gia hạn'));
        assert.ok(rows[0].textContent.includes('Mở lại'));
        assert.ok(!rows[1].textContent.includes('Gia hạn'));
        assert.ok(!rows[1].textContent.includes('Mở lại'));
        [...rows[0].querySelectorAll('button')].find(button => button.textContent === 'Gia hạn').click();
        assert.equal(w.document.querySelector('input[type=date]').min, '2026-11-17');
    } finally {
        dom.window.close();
    }
});

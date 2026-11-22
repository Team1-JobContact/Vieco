/* Mẫu CV Thanh lịch, Hiện đại, Tối giản: dựng trang A4 từ dữ liệu, chia trang và xuất PDF ngay trên trình duyệt.
   Dữ liệu người dùng chỉ được chèn bằng textContent. Ảnh trang do html2canvas vẽ, tệp PDF được ghép trực tiếp. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;

    var PAGE_W = 794, PAGE_H = 1123;          // A4 ở 96 dpi
    var PAGE_TOP = 56, PAGE_BOTTOM = 48;      // lề trên của trang 2 trở đi, lề dưới mọi trang
    var PERSONAL = ["full_name", "title", "birthday", "phone", "email", "address", "link"];
    var ENTRY = ["title", "subtitle", "start", "end", "description"];
    var SECTIONS = ["experience", "education", "projects", "activities"];
    var LISTS = ["skills", "languages", "certificates", "interests"];
    var LIMITS = { experience: 15, education: 10, projects: 10, activities: 10, skills: 40, languages: 10, certificates: 20, interests: 15 };

    var TEMPLATES = {
        elegant: { name: "Thanh lịch", note: "Rõ ràng, tinh tế và chuyên nghiệp", color: "#214e53" },
        modern: { name: "Hiện đại", note: "Nổi bật năng lực, tạo dấu ấn riêng", color: "#1a5276" },
        minimal: { name: "Tối giản", note: "Tập trung vào những điều quan trọng", color: "#876b40" }
    };
    var BASE_LABELS = {
        summary: "Giới thiệu", experience: "Kinh nghiệm làm việc", education: "Học vấn", projects: "Dự án", activities: "Hoạt động",
        skills: "Kỹ năng", languages: "Ngoại ngữ", certificates: "Chứng chỉ & giải thưởng", interests: "Sở thích", contact: "Liên hệ"
    };
    var LABELS = {
        elegant: BASE_LABELS,
        modern: Object.assign({}, BASE_LABELS, { summary: "Về tôi", experience: "Kinh nghiệm", certificates: "Chứng chỉ" }),
        minimal: Object.assign({}, BASE_LABELS, { summary: "Tóm tắt chuyên môn", experience: "Kinh nghiệm" })
    };
    var CONTACT = [["birthday", "Ngày sinh"], ["phone", "Điện thoại"], ["email", "Email"], ["address", "Địa chỉ"], ["link", "Website"]];

    // ---------- Dữ liệu ----------
    function text(value) { return typeof value === "string" ? value.normalize("NFC") : ""; }
    function empty() {
        var data = { version: 1, template: "elegant", photo: null, personal: {}, summary: "" };
        PERSONAL.forEach(function (key) { data.personal[key] = ""; });
        SECTIONS.concat(LISTS).forEach(function (key) { data[key] = []; });
        return data;
    }
    /** Đưa dữ liệu bất kỳ (bản nháp, máy chủ, AI) về đúng cấu trúc trình tạo CV. */
    function normalize(raw) {
        raw = raw && typeof raw === "object" ? raw : {};
        var data = empty();
        if (TEMPLATES[raw.template]) data.template = raw.template;
        if (/^data:image\/(jpeg|png|webp);base64,/.test(text(raw.photo))) data.photo = raw.photo;
        var personal = raw.personal && typeof raw.personal === "object" ? raw.personal : {};
        PERSONAL.forEach(function (key) { data.personal[key] = text(personal[key]); });
        data.summary = text(raw.summary);
        SECTIONS.forEach(function (key) {
            data[key] = (Array.isArray(raw[key]) ? raw[key] : []).filter(function (item) { return item && typeof item === "object"; })
                .slice(0, LIMITS[key]).map(function (item) {
                    var entry = {};
                    ENTRY.forEach(function (field) { entry[field] = text(item[field]); });
                    return entry;
                });
        });
        LISTS.forEach(function (key) {
            data[key] = (Array.isArray(raw[key]) ? raw[key] : []).map(text).map(function (s) { return s.trim(); }).filter(Boolean);
        });
        return data;
    }
    function hasEntry(entry) { return ENTRY.some(function (field) { return entry[field].trim(); }); }
    function hasContent(data) {
        return PERSONAL.some(function (key) { return data.personal[key].trim(); }) || Boolean(data.summary.trim()) ||
            SECTIONS.some(function (key) { return data[key].some(hasEntry); }) || LISTS.some(function (key) { return data[key].length; });
    }

    // ---------- Dựng trang ----------
    function keep(node, withNext) {
        node.setAttribute("data-keep", "");
        if (withNext) node.setAttribute("data-keep-next", "");
        return node;
    }
    function line(tag, cls, value) { return value ? h(tag, { class: cls, text: value }) : null; }
    function period(entry) { return [entry.start.trim(), entry.end.trim()].filter(Boolean).join(" – "); }
    function sectionTitle(label, number) {
        return keep(h("h2", { class: "cv-section-title" }, number ? h("span", { class: "cv-num", text: number }) : null, label), true);
    }
    function paragraphs(value) {
        return value.split(/\r?\n/).map(function (s) { return s.trim(); }).filter(Boolean).map(function (s) { return keep(h("p", { class: "cv-text", text: s })); });
    }
    function entryBlock(entry, dateFirst) {
        var bullets = V.lines(entry.description);
        var when = period(entry);
        var titles = h("div", { class: "cv-entry-titles" }, line("p", "cv-entry-title", entry.title.trim()), line("p", "cv-entry-sub", entry.subtitle.trim()));
        var date = h("p", { class: "cv-entry-date", text: when });
        var head = keep(h("div", { class: "cv-entry-head" }, dateFirst ? [date, titles] : [titles, when ? date : null]), bullets.length > 0);
        return h("div", { class: "cv-entry" }, head,
            bullets.length ? h("ul", { class: "cv-bullets" }, bullets.map(function (item) { return keep(h("li", { text: item })); })) : null);
    }
    function entries(data, key) { return data[key].filter(hasEntry); }
    function listItems(items) { return h("ul", { class: "cv-list" }, items.map(function (item) { return keep(h("li", { text: item })); })); }

    /** Phần đầu CV: họ tên, vị trí; withDetails: kèm thông tin liên hệ và ảnh (mẫu Hiện đại để chúng ở cột trái). */
    function head(data, options, withDetails) {
        var name = data.personal.full_name.trim(), role = data.personal.title.trim();
        var contacts = CONTACT.filter(function (c) { return data.personal[c[0]].trim(); });
        return keep(h("header", { class: "cv-head" },
            h("div", { class: "cv-head-main" },
                h("p", { class: "cv-name" + (name ? "" : " is-placeholder"), text: name || (options.placeholder ? "Họ và tên" : "") }),
                (role || options.placeholder) && h("p", { class: "cv-role" + (role ? "" : " is-placeholder"), text: role || "Vị trí ứng tuyển" }),
                withDetails && contacts.length ? h("ul", { class: "cv-contact" }, contacts.map(function (c) {
                    return h("li", {}, h("span", { class: "cv-contact-key", text: c[1] }), h("span", { text: data.personal[c[0]].trim() }));
                })) : null),
            withDetails && data.photo ? h("img", { class: "cv-photo", src: data.photo, alt: "Ảnh " + (name || "ứng viên") }) : null));
    }
    function emptyHint(data, options) {
        if (!options.placeholder || hasContent(data)) return null;
        return h("p", { class: "cv-hint", text: "Nhập thông tin vào biểu mẫu, CV của bạn sẽ hiện ra ở đây." });
    }

    /** Thanh lịch: một cột, thanh màu trên cùng, ảnh bên phải phần đầu. */
    function elegant(data, options) {
        var L = LABELS.elegant, body = h("div", { class: "cv-flow", "data-flow": "" });
        body.appendChild(head(data, options, true));
        body.appendChild(emptyHint(data, options) || h("div", { class: "cv-rule" }));
        if (data.summary.trim()) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.summary), paragraphs(data.summary)));
        SECTIONS.forEach(function (key) {
            var items = entries(data, key);
            if (items.length) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key]), items.map(function (e) { return entryBlock(e); })));
        });
        if (data.skills.length) {
            body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.skills),
                keep(h("div", { class: "cv-tags" }, data.skills.map(function (s) { return h("span", { class: "cv-tag", text: s }); })))));
        }
        ["languages", "certificates", "interests"].forEach(function (key) {
            if (data[key].length) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key]), listItems(data[key])));
        });
        return [h("div", { class: "cv-topbar", "aria-hidden": "true" }), body];
    }

    /** Hiện đại: cột trái màu xanh (ảnh, liên hệ, kỹ năng), cột phải là kinh nghiệm và học vấn. */
    function modern(data, options) {
        var L = LABELS.modern, name = data.personal.full_name.trim();
        var side = h("aside", { class: "cv-side cv-flow", "data-flow": "" },
            data.photo ? keep(h("img", { class: "cv-photo", src: data.photo, alt: "Ảnh " + (name || "ứng viên") })) : null);
        var contacts = CONTACT.filter(function (c) { return data.personal[c[0]].trim(); });
        if (contacts.length) {
            side.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.contact), h("ul", { class: "cv-list cv-contact-list" }, contacts.map(function (c) {
                return keep(h("li", {}, h("span", { class: "cv-contact-key", text: c[1] }), h("span", { class: "cv-contact-value", text: data.personal[c[0]].trim() })));
            }))));
        }
        LISTS.forEach(function (key) {
            if (data[key].length) side.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key]), listItems(data[key])));
        });
        var main = h("div", { class: "cv-main cv-flow", "data-flow": "" }, head(data, options, false), emptyHint(data, options));
        if (data.summary.trim()) main.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.summary), paragraphs(data.summary)));
        SECTIONS.forEach(function (key) {
            var items = entries(data, key);
            if (items.length) main.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key]), items.map(function (e) { return entryBlock(e, true); })));
        });
        return [h("div", { class: "cv-side-bg", "aria-hidden": "true" }), h("div", { class: "cv-columns" }, side, main)];
    }

    /** Tối giản: chữ đánh số 01, 02..., thời gian nằm cột trái của từng mục. */
    function minimal(data, options) {
        var L = LABELS.minimal, body = h("div", { class: "cv-flow", "data-flow": "" }), n = 0;
        function number() { n += 1; return (n < 10 ? "0" : "") + n; }
        body.appendChild(head(data, options, true));
        body.appendChild(emptyHint(data, options) || h("div", { class: "cv-rule" }));
        if (data.summary.trim()) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.summary, number()), paragraphs(data.summary)));
        SECTIONS.forEach(function (key) {
            var items = entries(data, key);
            if (items.length) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key], number()), items.map(function (e) { return entryBlock(e, true); })));
        });
        ["skills", "languages", "interests"].forEach(function (key) {
            if (data[key].length) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L[key], number()), keep(h("p", { class: "cv-text cv-inline", text: data[key].join("  ·  ") }))));
        });
        if (data.certificates.length) body.appendChild(h("section", { class: "cv-section" }, sectionTitle(L.certificates, number()), listItems(data.certificates)));
        return [body];
    }

    var RENDERERS = { elegant: elegant, modern: modern, minimal: minimal };

    /** Trang CV khổ A4 (chưa chia trang). options.placeholder: hiện chữ gợi ý khi chưa nhập. */
    function render(data, options) {
        var template = TEMPLATES[data.template] ? data.template : "elegant";
        return h("article", { class: "cv-sheet cv-" + template, lang: "vi" }, RENDERERS[template](data, options || {}));
    }

    // ---------- Chia trang ----------
    function offsetIn(sheet, node) {
        var top = 0;
        while (node && node !== sheet) { top += node.offsetTop; node = node.offsetParent; }
        return node === sheet ? top : NaN;
    }
    function flowOf(node) { return node.closest("[data-flow]"); }
    /** Chèn khoảng trống để không khối nào bị cắt ngang giữa hai trang; trả về số trang. Trang phải đang hiển thị. */
    function paginate(sheet) {
        Array.prototype.forEach.call(sheet.querySelectorAll(".cv-spacer, .cv-page-break"), function (node) { node.remove(); });
        sheet.style.height = "";
        sheet.style.minHeight = PAGE_H + "px";
        var blocks = Array.prototype.slice.call(sheet.querySelectorAll("[data-keep]"));
        var contentBottom = 0;
        for (var i = 0; i < blocks.length; i++) {
            var block = blocks[i], top = offsetIn(sheet, block);
            if (isNaN(top)) continue;
            var last = i;   // khối "dính" với khối kế tiếp (tiêu đề mục, dòng đầu của một kinh nghiệm)
            while (blocks[last].hasAttribute("data-keep-next") && last + 1 < blocks.length && flowOf(blocks[last + 1]) === flowOf(block)) last++;
            var bottom = offsetIn(sheet, blocks[last]) + blocks[last].offsetHeight;
            var page = Math.floor(top / PAGE_H);
            var start = page * PAGE_H + (page > 0 ? PAGE_TOP : 0);
            var shift = 0;
            if (top < start) shift = start - top;
            else if (bottom > (page + 1) * PAGE_H - PAGE_BOTTOM && bottom - top <= PAGE_H - PAGE_TOP - PAGE_BOTTOM) shift = (page + 1) * PAGE_H + PAGE_TOP - top;
            if (shift > 0) {
                var spacer = h("div", { class: "cv-spacer", "aria-hidden": "true" });
                spacer.style.height = shift + "px";
                block.parentNode.insertBefore(spacer, block);
                var moved = offsetIn(sheet, block) - top;   // bù phần lề bị gộp/tách khi chèn khoảng trống
                if (moved !== shift) spacer.style.height = Math.max(0, 2 * shift - moved) + "px";
            }
            contentBottom = Math.max(contentBottom, offsetIn(sheet, block) + block.offsetHeight);
        }
        // Tính theo khối nội dung cuối cùng, để lề dưới của khung không sinh thêm trang trắng.
        var pages = Math.max(1, Math.ceil(contentBottom / PAGE_H));
        sheet.style.minHeight = "";
        sheet.style.height = pages * PAGE_H + "px";
        return pages;
    }
    /** Vạch chia trang chỉ hiển thị ở bản xem trước. */
    function markPages(sheet, pages) {
        for (var i = 1; i < pages; i++) {
            var mark = h("div", { class: "cv-page-break", "aria-hidden": "true" }, h("span", { text: "Trang " + (i + 1) }));
            mark.style.top = i * PAGE_H + "px";
            sheet.appendChild(mark);
        }
    }

    // ---------- Xuất PDF ----------
    var exportHost = null;
    function host() {
        if (!exportHost || !exportHost.isConnected) {
            exportHost = h("div", { class: "cv-export-host", "aria-hidden": "true" });
            document.body.appendChild(exportHost);
        }
        return exportHost;
    }
    function imagesReady(node) {
        return Promise.all(Array.prototype.map.call(node.querySelectorAll("img"), function (img) {
            if (img.complete && img.naturalWidth) return Promise.resolve();
            return new Promise(function (resolve) { img.onload = img.onerror = function () { resolve(); }; });
        }));
    }
    function jpeg(canvas) {
        return new Promise(function (resolve, reject) {
            canvas.toBlob(function (blob) {
                if (!blob) return reject(new Error("Không tạo được ảnh trang CV, vui lòng thử lại."));
                blob.arrayBuffer().then(function (buffer) { resolve(new Uint8Array(buffer)); }, reject);
            }, "image/jpeg", 0.92);
        });
    }
    function pdfString(value) {
        var hex = "FEFF";
        for (var i = 0; i < value.length; i++) hex += ("000" + value.charCodeAt(i).toString(16).toUpperCase()).slice(-4);
        return "<" + hex + ">";
    }
    function pdfDate() {
        var d = new Date();
        function two(n) { return (n < 10 ? "0" : "") + n; }
        return "D:" + d.getFullYear() + two(d.getMonth() + 1) + two(d.getDate()) + two(d.getHours()) + two(d.getMinutes()) + two(d.getSeconds());
    }
    /** PDF tối thiểu: mỗi trang A4 là một ảnh JPEG phủ kín trang. */
    function buildPdf(pages, title) {
        var encoder = new TextEncoder(), parts = [], offsets = [], size = 0;
        var W = "595.28", H = "841.89";
        function add(chunk) {
            if (typeof chunk === "string") chunk = encoder.encode(chunk);
            parts.push(chunk);
            size += chunk.length;
        }
        function object(id, pieces) {
            offsets[id] = size;
            add(id + " 0 obj\n");
            pieces.forEach(add);
            add("\nendobj\n");
        }
        add(new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x34, 0x0a, 0x25, 0xe2, 0xe3, 0xcf, 0xd3, 0x0a]));
        object(1, ["<< /Type /Catalog /Pages 2 0 R >>"]);
        object(2, ["<< /Type /Pages /Kids [" + pages.map(function (_, i) { return (4 + 3 * i) + " 0 R"; }).join(" ") + "] /Count " + pages.length + " >>"]);
        object(3, ["<< /Title " + pdfString(title || "CV") + " /Producer (Vieco) /CreationDate (" + pdfDate() + ") >>"]);
        pages.forEach(function (page, i) {
            var id = 4 + 3 * i, content = "q\n" + W + " 0 0 " + H + " 0 0 cm\n/Im0 Do\nQ\n";
            object(id, ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + W + " " + H + "] /Resources << /XObject << /Im0 " + (id + 1) + " 0 R >> >> /Contents " + (id + 2) + " 0 R >>"]);
            object(id + 1, ["<< /Type /XObject /Subtype /Image /Width " + page.width + " /Height " + page.height +
                " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + page.bytes.length + " >>\nstream\n", page.bytes, "\nendstream"]);
            object(id + 2, ["<< /Length " + content.length + " >>\nstream\n" + content + "endstream"]);
        });
        var count = 4 + 3 * pages.length, xref = size, table = "xref\n0 " + count + "\n0000000000 65535 f \n";
        for (var id = 1; id < count; id++) table += ("000000000" + offsets[id]).slice(-10) + " 00000 n \n";
        add(table + "trailer\n<< /Size " + count + " /Root 1 0 R /Info 3 0 R >>\nstartxref\n" + xref + "\n%%EOF\n");
        return new Blob(parts, { type: "application/pdf" });
    }
    /** Tạo tệp PDF (Blob) đúng như bản xem trước, mỗi trang A4 một ảnh nét gấp đôi. */
    async function exportPdf(data, title) {
        if (typeof window.html2canvas !== "function") throw new Error("Chưa tải được công cụ xuất PDF, hãy tải lại trang và thử lại.");
        if (document.fonts && document.fonts.ready) await document.fonts.ready;
        var box = V.clear(host()), sheet = render(data, {});
        box.appendChild(sheet);
        try {
            await imagesReady(sheet);
            var count = paginate(sheet), pages = [];
            for (var i = 0; i < count; i++) {
                var canvas = await window.html2canvas(sheet, {
                    scale: 2, backgroundColor: "#ffffff", logging: false, useCORS: false,
                    x: 0, y: i * PAGE_H, width: PAGE_W, height: PAGE_H, scrollX: 0, scrollY: 0,
                    windowWidth: Math.max(document.documentElement.clientWidth, PAGE_W), windowHeight: Math.max(window.innerHeight, count * PAGE_H),
                    onclone: function (doc) {
                        var clone = doc.querySelector(".cv-export-host");
                        if (clone) clone.style.opacity = "1";
                    }
                });
                pages.push({ bytes: await jpeg(canvas), width: canvas.width, height: canvas.height });
                canvas.width = canvas.height = 0;   // giải phóng bộ nhớ trên điện thoại
            }
            return buildPdf(pages, title);
        } finally {
            V.clear(box);
        }
    }

    window.ViecoCv = {
        PAGE_W: PAGE_W, PAGE_H: PAGE_H, TEMPLATES: TEMPLATES, SECTIONS: SECTIONS, LISTS: LISTS, PERSONAL: PERSONAL, LIMITS: LIMITS,
        empty: empty, normalize: normalize, hasContent: hasContent, render: render, paginate: paginate, markPages: markPages, exportPdf: exportPdf
    };
}());

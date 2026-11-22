/* Bong bóng chat "Trợ lý Vieco" ở góc dưới bên phải: hỏi đáp AI về việc làm, công ty và cách dùng website.
   - Chỉ hiện khi máy chủ đã bật AI (GET /chat/status). Khách cũng dùng được, máy chủ giới hạn lượt hỏi.
   - Lịch sử lưu trong trình duyệt (localStorage) theo từng tài khoản, giữ khi chuyển trang; máy chủ không lưu.
   - Câu trả lời được dựng bằng DOM/textContent (không dùng innerHTML); chỉ nhận liên kết tới trang Vieco hoặc http(s). */
(function () {
    "use strict";

    var V = window.Vieco;
    if (!V || document.getElementById("v-chat")) return;
    var h = V.h;

    var STORE_KEY = "vieco.chat.v1";
    var OPEN_KEY = "vieco.chat.open";
    var STATUS_KEY = "vieco.chat.enabled";
    var MAX_STORED = 40;
    var SEND_LAST = 20;
    var MAX_CHARS = 1000;
    var REPLY_LIMIT = 6000;
    var KEEP_DAYS = 7;
    var SUGGESTIONS = ["Tìm việc IT ở TP.HCM", "Làm sao để ứng tuyển?", "Cách tạo CV trên Vieco", "Đăng tin tuyển dụng thế nào?"];

    // ---------- Lưu trữ trình duyệt (có thể bị chặn ở chế độ riêng tư) ----------
    function read(area, key) {
        try { return window[area].getItem(key); } catch (_) { return null; }
    }
    function write(area, key, value) {
        try {
            if (value === null) window[area].removeItem(key);
            else window[area].setItem(key, value);
        } catch (_) { /* bỏ qua: trình duyệt không cho lưu */ }
    }

    var state = { owner: "guest", messages: [], pending: false, error: null, open: false };
    var els = {};

    function load(owner) {
        state.owner = owner;
        var saved = null;
        try { saved = JSON.parse(read("localStorage", STORE_KEY) || "null"); } catch (_) { saved = null; }
        var fresh = saved && saved.owner === owner && Date.now() - (saved.updated || 0) < KEEP_DAYS * 864e5;
        state.messages = fresh && Array.isArray(saved.messages) ? saved.messages.filter(function (m) {
            return m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string" && m.content;
        }) : [];
        if (!fresh && saved) write("localStorage", STORE_KEY, null);  // lịch sử của tài khoản khác hoặc đã quá hạn
    }
    function save() {
        state.messages = state.messages.slice(-MAX_STORED);
        write("localStorage", STORE_KEY, state.messages.length
            ? JSON.stringify({ owner: state.owner, updated: Date.now(), messages: state.messages }) : null);
    }

    // ---------- Hiển thị câu trả lời ----------
    function safeLink(href) {
        if (/^https?:\/\/[^\s]+$/i.test(href)) return { url: href, external: true };
        var path = href.replace(/^\.?\//, "");
        if (/^(index\.html|pages\/[a-z0-9-]+\.html)([?#][^\s]*)?$/i.test(path)) return { url: V.url(path), external: false };
        return null;
    }
    function inline(text) {
        var nodes = [], pattern = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)/g, last = 0, match;
        while ((match = pattern.exec(text))) {
            if (match.index > last) nodes.push(text.slice(last, match.index));
            if (match[1] !== undefined) nodes.push(h("strong", { text: match[1] }));
            else {
                var link = safeLink(match[3]);
                nodes.push(!link ? match[2] : h("a", {
                    href: link.url, text: match[2], target: link.external ? "_blank" : null,
                    rel: link.external ? "noopener noreferrer" : null, onclick: onLinkClick
                }));
            }
            last = pattern.lastIndex;
        }
        if (last < text.length) nodes.push(text.slice(last));
        return nodes;
    }
    function rich(text) {
        var box = h("div", { class: "v-chat-rich" }), list = null, listType = "", para = null;
        text.replace(/\r/g, "").split("\n").forEach(function (raw) {
            var line = raw.replace(/^#{1,6}\s+/, "");
            var item = /^\s*([-*•]|\d+[.)])\s+(.*)$/.exec(line);
            if (item) {
                var type = /\d/.test(item[1]) ? "ol" : "ul";
                if (!list || listType !== type) { list = h(type, {}); listType = type; box.appendChild(list); }
                list.appendChild(h("li", {}, inline(item[2])));
                para = null;
                return;
            }
            list = null;
            if (!line.trim()) { para = null; return; }
            if (para) { para.appendChild(h("br", {})); inline(line).forEach(function (n) { para.appendChild(n.nodeType ? n : document.createTextNode(n)); }); }
            else { para = h("p", {}, inline(line)); box.appendChild(para); }
        });
        return box;
    }
    function bubble(message) {
        var mine = message.role === "user";
        return h("div", { class: "v-chat-msg " + (mine ? "is-user" : "is-bot") },
            h("span", { class: "v-sr-only", text: mine ? "Bạn: " : "Trợ lý: " }),
            mine ? h("p", { class: "v-chat-text", text: message.content }) : rich(message.content));
    }

    function onLinkClick() {
        // Trên điện thoại khung chat phủ kín màn hình: thu nhỏ để trang mới hiện ra.
        if (window.matchMedia && window.matchMedia("(max-width: 640px)").matches) write("sessionStorage", OPEN_KEY, null);
    }

    function scrollDown() { els.log.scrollTop = els.log.scrollHeight; }

    function renderLog() {
        V.clear(els.log);
        els.log.appendChild(h("div", { class: "v-chat-msg is-bot" }, rich(
            "Xin chào! Mình là **trợ lý AI của Vieco**. Mình có thể tìm việc đang tuyển, giới thiệu công ty và hướng dẫn bạn dùng website. Bạn cần giúp gì?")));
        if (!state.messages.length) {
            els.log.appendChild(h("div", { class: "v-chat-suggest", role: "group", "aria-label": "Gợi ý câu hỏi" },
                SUGGESTIONS.map(function (text) {
                    return h("button", { type: "button", class: "v-chat-chip", text: text, onclick: function () { send(text); } });
                })));
        }
        state.messages.forEach(function (message) { els.log.appendChild(bubble(message)); });
        renderStatus();
    }
    function renderStatus() {
        [els.typing, els.errorBox].forEach(function (node) { if (node && node.parentNode) node.parentNode.removeChild(node); });
        els.typing = els.errorBox = null;
        if (state.pending) {
            els.typing = h("div", { class: "v-chat-msg is-bot v-chat-typing", role: "status", "aria-label": "Trợ lý đang trả lời" },
                h("span", {}), h("span", {}), h("span", {}));
            els.log.appendChild(els.typing);
        } else if (state.error) {
            els.errorBox = h("div", { class: "v-chat-msg is-error", role: "alert" },
                h("p", { class: "v-chat-text", text: state.error }),
                h("button", { type: "button", class: "v-chat-retry", text: "Thử lại", onclick: retry }));
            els.log.appendChild(els.errorBox);
        }
        els.send.disabled = state.pending;
        els.reset.disabled = state.pending || !state.messages.length;
        scrollDown();
    }

    // ---------- Gửi câu hỏi ----------
    function pageInfo() {
        var path = window.location.pathname, at = path.indexOf("/pages/");
        return ((document.title || "") + " — " + (at >= 0 ? path.slice(at + 1) : "index.html") + window.location.search).slice(0, 200);
    }
    function payload() {
        return state.messages.slice(-SEND_LAST).map(function (m) {
            return { role: m.role, content: m.role === "assistant" ? m.content.slice(0, REPLY_LIMIT) : m.content };
        });
    }
    async function ask() {
        state.pending = true;
        state.error = null;
        renderStatus();
        try {
            var data = await V.api("/chat", { method: "POST", body: { messages: payload(), page: pageInfo() }, timeout: 60000 });
            state.messages.push({ role: "assistant", content: data.reply });
            save();
            state.pending = false;
            els.log.appendChild(bubble(state.messages[state.messages.length - 1]));
        } catch (error) {
            state.pending = false;
            state.error = error.message || "Có lỗi xảy ra, vui lòng thử lại";
        }
        renderStatus();
    }
    function send(text) {
        text = String(text || "").trim();
        if (!text || state.pending) return;
        if (text.length > MAX_CHARS) { state.error = "Mỗi câu hỏi tối đa " + MAX_CHARS + " ký tự"; renderStatus(); return; }
        var suggest = els.log.querySelector(".v-chat-suggest");
        if (suggest) suggest.remove();
        state.messages.push({ role: "user", content: text });
        save();
        els.log.appendChild(bubble(state.messages[state.messages.length - 1]));
        els.input.value = "";
        resize();
        ask();
    }
    function retry() {
        var last = state.messages[state.messages.length - 1];
        if (last && last.role === "user") ask();
    }

    async function reset() {
        if (!state.messages.length || state.pending) return;
        if (!(await V.confirm("Bắt đầu cuộc trò chuyện mới?", "Toàn bộ tin nhắn hiện tại sẽ bị xóa khỏi trình duyệt này.", "Xóa và bắt đầu lại", true))) return;
        state.messages = [];
        state.error = null;
        save();
        renderLog();
        els.input.focus();
    }

    // ---------- Mở / đóng ----------
    function setOpen(open, focus) {
        state.open = open;
        els.panel.hidden = !open;
        els.root.classList.toggle("is-open", open);
        els.launcher.setAttribute("aria-expanded", String(open));
        els.launcher.setAttribute("aria-label", open ? "Thu nhỏ trợ lý Vieco" : "Mở trợ lý Vieco");
        write("sessionStorage", OPEN_KEY, open ? "1" : null);
        if (open) {
            scrollDown();
            if (focus && !(window.matchMedia && window.matchMedia("(pointer: coarse)").matches)) els.input.focus();
        } else if (focus) {
            els.launcher.focus();
        }
    }

    function resize() {
        els.input.style.height = "auto";
        els.input.style.height = Math.min(els.input.scrollHeight, 120) + "px";
        var left = MAX_CHARS - els.input.value.length;
        els.count.textContent = left <= 200 ? "Còn " + left + " ký tự" : "";
    }

    function build() {
        els.log = h("div", { class: "v-chat-log", role: "log", "aria-live": "polite", "aria-label": "Tin nhắn" });
        els.input = h("textarea", {
            class: "v-chat-input", rows: "1", maxlength: String(MAX_CHARS), placeholder: "Nhập câu hỏi của bạn…",
            "aria-label": "Câu hỏi cho trợ lý", oninput: resize,
            onkeydown: function (event) {
                if (event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
                    event.preventDefault();
                    send(els.input.value);
                }
            }
        });
        els.send = h("button", { type: "submit", class: "v-chat-send", "aria-label": "Gửi" }, V.icon("send"));
        els.count = h("span", { class: "v-chat-count", "aria-live": "polite" });
        els.reset = h("button", { type: "button", class: "v-chat-tool", "aria-label": "Cuộc trò chuyện mới", title: "Cuộc trò chuyện mới", onclick: reset }, V.icon("refresh"));
        els.panel = h("section", { id: "v-chat-panel", class: "v-chat-panel", role: "dialog", "aria-label": "Trợ lý Vieco", hidden: true,
            onkeydown: function (event) { if (event.key === "Escape") setOpen(false, true); } },
            h("header", { class: "v-chat-head" },
                h("span", { class: "v-chat-mark", "aria-hidden": "true" }, V.icon("spark")),
                h("div", { class: "v-chat-title" }, h("h2", { text: "Trợ lý Vieco" }), h("p", { text: "Hỏi đáp việc làm và cách dùng Vieco" })),
                els.reset,
                h("button", { type: "button", class: "v-chat-tool", "aria-label": "Thu nhỏ", title: "Thu nhỏ", onclick: function () { setOpen(false, true); } }, V.icon("close"))),
            els.log,
            h("form", { class: "v-chat-form", onsubmit: function (event) { event.preventDefault(); send(els.input.value); } },
                h("div", { class: "v-chat-field" }, els.input, els.send),
                h("p", { class: "v-chat-note" }, h("span", { text: "AI có thể nhầm lẫn. Không nhập mật khẩu hay thông tin cá nhân nhạy cảm." }), els.count)));
        els.launcher = h("button", { type: "button", class: "v-chat-launcher", "aria-controls": "v-chat-panel", "aria-expanded": "false",
            "aria-label": "Mở trợ lý Vieco", title: "Hỏi trợ lý Vieco", onclick: function () { setOpen(!state.open, true); } },
            h("span", { class: "v-chat-launcher-open" }, V.icon("chat")), h("span", { class: "v-chat-launcher-close" }, V.icon("close")),
            h("span", { class: "v-chat-badge", "aria-hidden": "true", text: "AI" }));
        els.root = h("div", { id: "v-chat", class: "v-chat" }, els.panel, els.launcher);
        document.body.appendChild(els.root);
    }

    async function enabled() {
        if (read("sessionStorage", STATUS_KEY) === "1") return true;
        try {
            var status = await V.api("/chat/status", { auth: false, timeout: 8000 });
            if (status && status.enabled) write("sessionStorage", STATUS_KEY, "1");
            return Boolean(status && status.enabled);
        } catch (_) {
            return false;
        }
    }

    async function init() {
        if (!(await enabled())) return;
        var user = null;
        try { user = await V.currentUser(); } catch (_) { user = null; }
        load(user && user.id ? "u:" + user.id : "guest");
        build();
        renderLog();
        resize();
        if (read("sessionStorage", OPEN_KEY) === "1") setOpen(true, false);
    }

    init();
}());

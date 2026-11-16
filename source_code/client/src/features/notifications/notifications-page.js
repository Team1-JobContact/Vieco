/* Trang thông báo cho mọi vai trò đã đăng nhập. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    V.currentUser().then(function (user) {
        if (!user) return V.goLogin();
        var box = h("div", {});
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" }, h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }), h("span", { "aria-current": "page", text: "Thông báo" })),
            h("p", { class: "v-eyebrow", text: V.roleLabel(user.role) }),
            h("h1", { class: "v-h1", text: "Thông báo của bạn" }),
            h("p", { class: "v-lead", text: "Cập nhật về đơn ứng tuyển, tin tuyển dụng và hồ sơ công ty." }))));
        app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap", style: "max-width:1000px" }, box)));
        window.ViecoNotifications.mount(box);
    });
}());

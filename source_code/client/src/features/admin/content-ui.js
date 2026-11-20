(function () {
    "use strict";
    var V = window.Vieco, app = document.getElementById("app");
    var slug = new URLSearchParams(window.location.search).get("slug") || "gioi-thieu";
    V.api("/pages/" + encodeURIComponent(slug), { auth: false }).then(function (page) {
        document.title = page.title + " | Vieco";
        V.clear(app).appendChild(V.h("article", {}, V.h("h1", { class: "v-h1", text: page.title }),
            V.h("div", { class: "v-lead", style: "white-space:pre-wrap", text: page.content })));
    }).catch(function (error) { V.note(app, error.message, "error"); });
}());

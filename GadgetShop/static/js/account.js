// Личный кабинет: профиль (GET/PATCH /api/me/) и заказы (GET /api/orders/)
(function () {
    "use strict";

    const GS = window.GadgetShop || {};
    const csrf = GS.getCsrfToken ? GS.getCsrfToken : function () { return ""; };
    const notify = GS.showNotification ? GS.showNotification : function (m) { alert(m); };

    let ordersCache = {};

    const PROFILE_FIELDS = [
        "username", "email", "full_name", "phone", "address",
        "favorite_category_name", "delivery_city", "postal_code",
    ];

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || "—";
    }

    // ---------- Профиль ----------
    function loadProfile() {
        fetch("/api/me/", { headers: { Accept: "application/json" }, credentials: "same-origin" })
            .then(function (r) {
                if (!r.ok) {
                    GS.handleAuthError && GS.handleAuthError(r.status);
                    throw new Error("status " + r.status);
                }
                return r.json();
            })
            .then(function (data) {
                PROFILE_FIELDS.forEach(function (f) { setText("v-" + f, data[f]); });
                const badge = document.getElementById("role-badge");
                if (badge) {
                    badge.textContent = data.role_display || data.role;
                    badge.className = "badge " + (data.role === "ADMIN" ? "bg-danger"
                        : data.role === "MANAGER" ? "bg-warning text-dark" : "bg-primary");
                }
                // Заполнить форму редактирования
                const form = document.getElementById("profile-form");
                if (form) {
                    form.full_name.value = data.full_name || "";
                    form.phone.value = data.phone || "";
                    form.address.value = data.address || "";
                    form.delivery_city.value = data.delivery_city || "";
                    form.postal_code.value = data.postal_code || "";
                    if (form.favorite_category)
                        form.favorite_category.value = data.favorite_category || "";
                }
                document.getElementById("profile-view").style.display = "";
                document.getElementById("edit-btn").style.display = "";
            })
            .catch(function () {
                const box = document.getElementById("profile-loading");
                if (box) box.innerHTML = '<div class="alert alert-danger">Не удалось загрузить профиль.</div>';
            });
    }

    function saveProfile(event) {
        event.preventDefault();
        const form = event.target;
        const payload = {
            full_name: form.full_name.value,
            phone: form.phone.value,
            address: form.address.value,
            delivery_city: form.delivery_city.value,
            postal_code: form.postal_code.value,
            favorite_category: form.favorite_category && form.favorite_category.value
                ? parseInt(form.favorite_category.value, 10) : null,
        };

        fetch("/api/me/", {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
            credentials: "same-origin",
            body: JSON.stringify(payload),
        })
            .then(function (r) {
                if (!r.ok) {
                    if (!(GS.handleAuthError && GS.handleAuthError(r.status)))
                        notify("Не удалось сохранить профиль.", "danger");
                    throw new Error("status " + r.status);
                }
                return r.json();
            })
            .then(function () {
                notify("Профиль обновлён.", "success");
                toggleEdit(false);
                loadProfile();
            })
            .catch(function () {});
    }

    function toggleEdit(editing) {
        document.getElementById("profile-form").style.display = editing ? "" : "none";
        document.getElementById("profile-view").style.display = editing ? "none" : "";
        document.getElementById("edit-btn").style.display = editing ? "none" : "";
    }

    // ---------- Заказы ----------
    function loadOrders() {
        const box = document.getElementById("orders-box");
        box.innerHTML = GS.spinnerHtml ? GS.spinnerHtml("Загрузка заказов...") : "Загрузка...";

        fetch("/api/orders/", { headers: { Accept: "application/json" }, credentials: "same-origin" })
            .then(function (r) {
                if (!r.ok) {
                    GS.handleAuthError && GS.handleAuthError(r.status);
                    throw new Error("status " + r.status);
                }
                return r.json();
            })
            .then(function (data) {
                const orders = Array.isArray(data) ? data : data.results || [];
                if (!orders.length) {
                    box.innerHTML = '<p class="text-muted mb-0">У вас пока нет заказов.</p>';
                    return;
                }
                ordersCache = {};
                let rows = "";
                orders.forEach(function (o) {
                    ordersCache[o.id] = o;
                    rows +=
                        "<tr><td>#" + o.id + "</td>" +
                        "<td>" + (o.created_at || "").slice(0, 10) + "</td>" +
                        "<td>" + o.total + " руб.</td>" +
                        '<td><span class="badge bg-secondary">' + (o.status_display || o.status) + "</span></td>" +
                        '<td><button class="btn btn-outline-primary btn-sm js-order-detail" data-id="' + o.id + '">Подробнее</button></td></tr>";
                });
                box.innerHTML =
                    '<div class="table-responsive"><table class="table table-sm align-middle">' +
                    "<thead><tr><th>№</th><th>Дата</th><th>Сумма</th><th>Статус</th><th></th></tr></thead>" +
                    "<tbody>" + rows + "</tbody></table></div>";
            })
            .catch(function () {
                box.innerHTML = '<div class="alert alert-danger">Не удалось загрузить заказы.</div>';
            });
    }

    function showOrderDetail(id) {
        const o = ordersCache[id];
        if (!o) return;
        let items = (o.items || []).map(function (it) {
            return "<tr><td>" + it.product_name + "</td><td>" + it.quantity +
                "</td><td>" + it.price + "</td><td>" + it.item_cost + "</td></tr>";
        }).join("");
        document.getElementById("order-detail-body").innerHTML =
            "<p><strong>Заказ #" + o.id + "</strong> от " + (o.created_at || "").slice(0, 10) + "</p>" +
            "<p>Адрес: " + (o.address || "—") + "</p>" +
            '<table class="table table-sm"><thead><tr><th>Товар</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr></thead><tbody>' +
            items + "</tbody></table>" +
            "<p class='text-end fw-bold'>Итого: " + o.total + " руб.</p>";
        const modal = new bootstrap.Modal(document.getElementById("orderModal"));
        modal.show();
    }

    // ---------- Инициализация ----------
    document.addEventListener("DOMContentLoaded", function () {
        if (!document.getElementById("profile-form")) return;
        loadProfile();
        loadOrders();

        document.getElementById("edit-btn").addEventListener("click", function () { toggleEdit(true); });
        document.getElementById("cancel-edit").addEventListener("click", function () { toggleEdit(false); });
        document.getElementById("profile-form").addEventListener("submit", saveProfile);

        document.getElementById("orders-box").addEventListener("click", function (e) {
            const btn = e.target.closest(".js-order-detail");
            if (btn) showOrderDetail(parseInt(btn.dataset.id, 10));
        });
    });
})();

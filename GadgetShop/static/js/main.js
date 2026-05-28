// GadgetShop — взаимодействие с REST API (Задание 6)
(function () {
    "use strict";

    // ---------- CSRF ----------
    function getCookie(name) {
        const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
        return match ? decodeURIComponent(match.pop()) : "";
    }

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return getCookie("csrftoken") || (meta ? meta.getAttribute("content") : "");
    }

    // ---------- Уведомления (Bootstrap Toast/Alert) ----------
    function ensureToastContainer() {
        let container = document.getElementById("gs-toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "gs-toast-container";
            document.body.appendChild(container);
        }
        return container;
    }

    function showNotification(message, type) {
        const container = ensureToastContainer();
        const alert = document.createElement("div");
        alert.className =
            "alert alert-" + (type || "success") + " alert-dismissible fade show shadow-sm";
        alert.setAttribute("role", "alert");
        alert.innerHTML =
            message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>';
        container.appendChild(alert);
        setTimeout(function () {
            alert.classList.remove("show");
            setTimeout(function () {
                alert.remove();
            }, 200);
        }, 3500);
    }

    // ---------- Спиннер ----------
    function spinnerHtml(text) {
        return (
            '<div class="d-flex justify-content-center align-items-center py-5 w-100">' +
            '<div class="spinner-border text-primary me-2" role="status">' +
            '<span class="visually-hidden">Загрузка...</span></div>' +
            "<span class=\"text-muted\">" + (text || "Загрузка товаров...") + "</span>" +
            "</div>"
        );
    }

    // ---------- Обновление счётчика корзины ----------
    function updateCartBadge(count) {
        const badge = document.getElementById("cart-count");
        if (!badge) return;
        badge.textContent = count;
        badge.style.display = count > 0 ? "" : "none";
    }

    // ---------- Рендер карточки товара ----------
    function renderProductCard(p) {
        const photo = p.photo
            ? '<img src="' + p.photo + '" class="card-img-top product-thumb" alt="' + p.name + '">'
            : '<div class="product-thumb-placeholder">📦</div>';

        const button = p.in_stock
            ? '<button class="btn btn-gs btn-sm js-add-to-cart" data-product-id="' +
              p.id + '">В корзину</button>'
            : '<button class="btn btn-secondary btn-sm" disabled>Нет в наличии</button>';

        return (
            '<div class="col-sm-6 col-md-4 col-lg-3 mb-4">' +
            '<div class="card h-100 product-card">' +
            photo +
            '<div class="card-body d-flex flex-column">' +
            '<span class="badge bg-light text-dark align-self-start mb-2">' + (p.category_name || "") + "</span>" +
            '<h6 class="card-title">' + p.name + "</h6>" +
            '<p class="text-muted small mb-2">' + (p.manufacter_name || "") + "</p>" +
            '<div class="price-tag mb-3 mt-auto">' + p.price + " руб.</div>" +
            '<div class="d-flex gap-2">' +
            '<a href="' + p.detail_url + '" class="btn btn-outline-primary btn-sm flex-grow-1">Подробнее</a>' +
            button +
            "</div>" +
            "</div></div></div>"
        );
    }

    // ---------- Задание 6.1: загрузка товаров из API ----------
    function loadProductsFromAPI(container) {
        const limit = parseInt(container.dataset.limit || "8", 10);
        container.innerHTML = spinnerHtml();

        fetch("/api/products/", {
            headers: { Accept: "application/json" },
            credentials: "same-origin",
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Сервер вернул статус " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                const products = Array.isArray(data) ? data : data.results || [];
                if (!products.length) {
                    container.innerHTML =
                        '<div class="col-12"><div class="alert alert-info">Товары не найдены.</div></div>';
                    return;
                }
                container.innerHTML = products
                    .slice(0, limit)
                    .map(renderProductCard)
                    .join("");
            })
            .catch(function (error) {
                // Задание 6.5: обработка ошибок
                container.innerHTML =
                    '<div class="col-12"><div class="alert alert-danger">' +
                    "Не удалось загрузить товары. " + error.message +
                    "</div></div>";
            });
    }

    // ---------- Задание 6.2: добавление в корзину ----------
    function addToCart(productId, button) {
        const originalHtml = button ? button.innerHTML : "";
        if (button) {
            button.disabled = true;
            button.innerHTML =
                '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        }

        fetch("/api/cart/add/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            credentials: "same-origin",
            body: JSON.stringify({ product_id: productId }),
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, status: response.status, data: data };
                });
            })
            .then(function (result) {
                if (!result.ok) {
                    if (result.status === 401 || result.status === 403) {
                        showNotification(
                            'Войдите в аккаунт, чтобы добавлять товары в корзину.',
                            "warning"
                        );
                    } else {
                        showNotification(
                            result.data.error || "Не удалось добавить товар.",
                            "danger"
                        );
                    }
                    return;
                }
                updateCartBadge(result.data.cart_count);
                showNotification(result.data.message || "Товар добавлен в корзину", "success");
            })
            .catch(function () {
                showNotification("Ошибка соединения с сервером.", "danger");
            })
            .finally(function () {
                if (button) {
                    button.disabled = false;
                    button.innerHTML = originalHtml;
                }
            });
    }

    // ---------- Инициализация ----------
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-api-products]").forEach(loadProductsFromAPI);

        document.addEventListener("click", function (event) {
            const button = event.target.closest(".js-add-to-cart");
            if (!button) return;
            event.preventDefault();
            addToCart(button.dataset.productId, button);
        });
    });
})();

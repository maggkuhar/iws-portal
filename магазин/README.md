# Блок: Магазин

Blueprint: `shop`

## Маршруты
- `/shop` — каталог товаров
- `/shop/<slug>` — карточка товара
- `/cart` — корзина
- `/cart/add` (POST) — добавить в корзину
- `/cart/remove` (POST) — удалить из корзины
- `/checkout` (GET/POST) — оформление заказа
- `/publishing` — издательство
- `/publishing/<slug>` — книга издательства

## Шаблоны
- `shop.html`, `product.html`, `cart.html`, `checkout.html`
- `publishing.html`, `publishing_book.html`

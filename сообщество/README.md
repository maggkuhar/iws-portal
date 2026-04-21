# Блок: Сообщество

Blueprint: `community`

## Маршруты
- `/community` — лента постов
- `/community/post` (POST) — создать пост
- `/members` — участники
- `/profile/<user_id>` — профиль участника
- `/profile/<user_id>/follow` (POST) — подписаться/отписаться
- `/post/<post_id>/like` (POST) — лайк поста
- `/groups` — группы
- `/groups/<group_id>` — группа
- `/groups/<group_id>/join` (POST) — вступить/выйти
- `/messages` — список диалогов
- `/messages/<to_id>` — диалог

## Шаблоны
- `community.html`, `members.html`, `profile.html`
- `groups.html`, `group_detail.html`, `messages.html`, `dialog.html`

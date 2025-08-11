# bot/handlers.py
import html
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from bot import sheets
from bot.config import settings

router = Router(name=__name__)

GEO_FLAGS = {
    "AR": "🇦🇷", "AU": "🇦🇺", "BD": "🇧🇩", "BF": "🇧🇫", "BJ": "🇧🇯",
    "BR": "🇧🇷", "CA": "🇨🇦", "CH": "🇨🇭", "CI": "🇨🇮", "CL": "🇨🇱",
    "CM": "🇨🇲", "CO": "🇨🇴", "CZ": "🇨🇿", "DE": "🇩🇪", "ES": "🇪🇸",
    "FR": "🇫🇷", "HU": "🇭🇺", "IN": "🇮🇳", "IT": "🇮🇹", "KE": "🇰🇪",
    "KZ": "🇰🇿", "LT": "🇱🇹", "LV": "🇱🇻", "MA": "🇲🇦", "MM": "🇲🇲",
    "MX": "🇲🇽", "NG": "🇳🇬", "NL": "🇳🇱", "NP": "🇳🇵", "NZ": "🇳🇿",
    "PH": "🇵🇭", "PK": "🇵🇰", "PL": "🇵🇱", "PT": "🇵🇹", "SA": "🇸🇦",
    "UAE": "🇦🇪", "QA": "🇶🇦", "BH": "🇧🇭", "KW": "🇰🇼", "SK": "🇸🇰",
    "SN": "🇸🇳", "SO": "🇸🇴", "TR": "🇹🇷", "UK": "🇬🇧", "UZ": "🇺🇿",
    "ZM": "🇿🇲",
}

MAX_MSG = 4000  # предел для текста (чуть меньше 4096 для запаса)

# ---------- Хелперы ----------
def _get(o, name, default: str = "-"):
    """Безопасно получаем поле из dict или объекта; пустые значения -> default."""
    try:
        if isinstance(o, dict):
            val = o.get(name, None)
        else:
            val = getattr(o, name, None)
    except Exception:
        val = None
    return default if val in (None, "") else val

def _esc(v) -> str:
    return html.escape(str(v))

# ---------- Клавиатуры ----------
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все офферы", callback_data="all_offers")],
        [InlineKeyboardButton(text="🌍 GEO", callback_data="geo_menu")],
        [InlineKeyboardButton(text="🏆 Топ недели", callback_data="top_offers")],
        [InlineKeyboardButton(text="🔄 Обновить кэш", callback_data="update_cache")]
    ])

def geos_keyboard(geos: list[str]) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for geo in geos:
        flag = GEO_FLAGS.get(geo.upper(), "🏳️")
        row.append(InlineKeyboardButton(text=f"{flag} {geo}", callback_data=f"geo:{geo}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def pager_kb(kind: str, page: int, total: int, extra: str | None = None) -> InlineKeyboardMarkup:
    """
    kind: 'all' | 'geo'
    extra: для geo — сам GEO (например 'BR')
    """
    buttons: list[InlineKeyboardButton] = []
    prev_page = page - 1 if page > 1 else total
    next_page = page + 1 if page < total else 1

    if kind == "all":
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"all_offers:{prev_page}"))
        buttons.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="noop"))
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"all_offers:{next_page}"))
    else:  # geo
        geo = extra or ""
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"geo_pg:{geo}:{prev_page}"))
        buttons.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="noop"))
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"geo_pg:{geo}:{next_page}"))

    rows = [buttons, [InlineKeyboardButton(text="🏠 Меню", callback_data="home")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- Рендер оффера и разбиение на страницы ----------
def render_offer_block(o) -> str:
    geo_val = str(_get(o, "geo", ""))  # пустая строка, чтобы флаг корректно дефолтился
    flag = GEO_FLAGS.get(geo_val.upper(), "🏳️")

    return (
        f"<b>{_esc(_get(o, 'name'))}</b>\n"
        f"🌍 <b>GEO:</b> {flag} {_esc(geo_val)}\n"
        f"📲 <b>Трафик:</b> {_esc(_get(o, 'traffic'))}\n"
        f"💰 <b>Оплата:</b> {_esc(_get(o, 'payout'))}\n"
        f"🔝 <b>Капа/статус:</b> {_esc(_get(o, 'capa_status'))}\n"
        f"📊 <b>Cap/Day:</b> {_esc(_get(o, 'cap_day'))}\n"
        f"💹 <b>EPC/CR:</b> {_esc(_get(o, 'epc'))}\n"
        f"📉 <b>Crash rate:</b> {_esc(_get(o, 'crash_rate'))}\n"
        f"💳 <b>Mindep:</b> {_esc(_get(o, 'mindep'))}\n"
        f"📦 <b>Base:</b> {_esc(_get(o, 'base'))}\n"
        f"💵 <b>Профит:</b> {_esc(_get(o, 'profit'))}\n"
        f"🎯 <b>KPI:</b> {_esc(_get(o, 'kpi'))}\n"
        f"📝 <b>Описание:</b> {_esc(_get(o, 'description'))}\n"
        f"⚡ <b>Статус:</b> {_esc(_get(o, 'status'))}\n"
        f"👨‍💼 <b>Менеджер:</b> {_esc(_get(o, 'manager'))}\n"
        f"🕒 <b>Добавлено:</b> {_esc(_get(o, 'date_added'))}\n\n"
    )

def paginate_offers(offers: list, title: str) -> list[str]:
    """
    Делит длинный вывод на страницы, чтобы каждая была <= MAX_MSG символов.
    """
    pages: list[str] = []
    current = f"{title}\n\n"
    for o in offers:
        block = render_offer_block(o)
        if len(current) + len(block) > MAX_MSG:
            pages.append(current.rstrip())
            current = f"{title}\n\n{block}"
        else:
            current += block
    if current.strip():
        pages.append(current.rstrip())
    return pages or [f"{title}\n\n(пусто)"]

# ---------- Хэндлеры ----------
@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    await msg.answer("👋 Добро пожаловать!\n\n", reply_markup=main_menu())

@router.callback_query(F.data == "home")
async def back_home(cb: CallbackQuery):
    await cb.message.edit_text("Главное меню:", reply_markup=main_menu())
    await cb.answer()

@router.callback_query(F.data == "geo_menu")
async def geo_menu(cb: CallbackQuery):
    geos = await sheets.geos()
    if not geos:
        await cb.message.edit_text("Нет доступных стран.", reply_markup=main_menu())
        await cb.answer()
        return
    await cb.message.edit_text(
        "<b>Выберите страну (GEO):</b>",
        reply_markup=geos_keyboard(geos),
        parse_mode="HTML"
    )
    await cb.answer()

@router.callback_query(F.data.startswith("geo:"))
async def geo_click(cb: CallbackQuery):
    geo = cb.data.split(":", 1)[1]
    offers = await sheets.offers_by_geo(geo)
    if not offers:
        await cb.message.edit_text(
            f"Нет офферов для {GEO_FLAGS.get(geo.upper(),'🏳️')} {html.escape(geo)}.",
            reply_markup=main_menu()
        )
        await cb.answer()
        return

    flag = GEO_FLAGS.get(geo.upper(), "🏳️")
    title = f"<b>Офферы для {flag} {html.escape(geo)}</b>"
    pages = paginate_offers(offers, title)
    kb = pager_kb("geo", page=1, total=len(pages), extra=geo)
    await cb.message.edit_text(pages[0], parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("geo_pg:"))
async def geo_page(cb: CallbackQuery):
    # callback_data формат: geo_pg:{geo}:{page}
    try:
        _, geo, page_str = cb.data.split(":", 2)
        page = int(page_str)
    except Exception:
        await cb.answer()
        return

    offers = await sheets.offers_by_geo(geo)
    if not offers:
        await cb.message.edit_text(
            f"Нет офферов для {GEO_FLAGS.get(geo.upper(),'🏳️')} {html.escape(geo)}.",
            reply_markup=main_menu()
        )
        await cb.answer()
        return

    flag = GEO_FLAGS.get(geo.upper(), "🏳️")
    title = f"<b>Офферы для {flag} {html.escape(geo)}</b>"
    pages = paginate_offers(offers, title)
    total = len(pages)
    if page < 1 or page > total:
        page = 1

    kb = pager_kb("geo", page=page, total=total, extra=geo)
    await cb.message.edit_text(pages[page - 1], parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "all_offers")
async def all_offers(cb: CallbackQuery):
    offers = await sheets.get_offers()
    if not offers:
        await cb.message.edit_text("Список офферов пуст.", reply_markup=main_menu())
        await cb.answer()
        return

    pages = paginate_offers(offers, "<b>Все офферы</b>")
    kb = pager_kb("all", page=1, total=len(pages))
    await cb.message.edit_text(pages[0], parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("all_offers:"))
async def all_offers_page(cb: CallbackQuery):
    # callback_data формат: all_offers:{page}
    try:
        _, page_str = cb.data.split(":", 1)
        page = int(page_str)
    except Exception:
        await cb.answer()
        return

    offers = await sheets.get_offers()
    if not offers:
        await cb.message.edit_text("Список офферов пуст.", reply_markup=main_menu())
        await cb.answer()
        return

    pages = paginate_offers(offers, "<b>Все офферы</b>")
    total = len(pages)
    if page < 1 or page > total:
        page = 1

    kb = pager_kb("all", page=page, total=total)
    await cb.message.edit_text(pages[page - 1], parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "top_offers")
async def top_offers(cb: CallbackQuery):
    top = await sheets.top_offers()
    if not top:
        await cb.message.edit_text("Топ офферов пока пуст.", reply_markup=main_menu())
        await cb.answer()
        return

    pages = paginate_offers(top, "<b>🏆 Топ офферы недели</b>")
    kb = pager_kb("all", page=1, total=len(pages))  # пагинация, как у all
    await cb.message.edit_text(pages[0], parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "update_cache")
async def update_cache(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        await cb.message.edit_text("Нет доступа.", reply_markup=main_menu())
        await cb.answer()
        return
    await sheets.get_offers(force=True)
    await cb.message.edit_text("🔄 Кэш обновлён!", reply_markup=main_menu())
    await cb.answer()

# --- доступ: /myid, /allow, /deny, /partners ---
@router.message(F.text == "/myid")
async def my_id(msg: Message):
    await msg.answer(f"Ваш ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")

@router.message(F.text.regexp(r"^/allow\s+\d+$"))
async def allow_user(msg: Message):
    # только админ
    if msg.from_user.id not in settings.admin_ids:
        await msg.answer("Нет доступа.")
        return
    uid = int(msg.text.split()[1])
    added = await sheets.add_partner(uid)  # должна быть функция в sheets.py
    if added:
        await msg.answer(f"✅ Доступ выдан: <code>{uid}</code>", parse_mode="HTML")
    else:
        await msg.answer(f"ℹ️ Уже в списке: <code>{uid}</code>", parse_mode="HTML")

@router.message(F.text.regexp(r"^/deny\s+\d+$"))
async def deny_user(msg: Message):
    # только админ
    if msg.from_user.id not in settings.admin_ids:
        await msg.answer("Нет доступа.")
        return
    uid = int(msg.text.split()[1])
    removed = await sheets.remove_partner(uid)  # должна быть функция в sheets.py
    if removed:
        await msg.answer(f"🗑️ Удалён: <code>{uid}</code>", parse_mode="HTML")
    else:
        await msg.answer(f"🙅 Не найден: <code>{uid}</code>", parse_mode="HTML")

@router.message(F.text == "/partners")
async def list_partners(msg: Message):
    # только админ
    if msg.from_user.id not in settings.admin_ids:
        await msg.answer("Нет доступа.")
        return
    ids = sorted(await sheets.partner_ids())  # должна быть функция в sheets.py
    if not ids:
        await msg.answer("Список партнёров пуст.")
        return
    text = "👥 Партнёры (доступ):\n" + "\n".join(f"• <code>{i}</code>" for i in ids)
    await msg.answer(text, parse_mode="HTML")

# bot/sheets.py
from __future__ import annotations

import os
import json
import time
from typing import List, Iterable, Any, Set
from dataclasses import dataclass

import gspread_asyncio
from google.oauth2.service_account import Credentials

from bot.config import settings


# --------- Модель ---------
@dataclass
class Offer:
    name: str
    geo: str
    traffic: str
    payout: str
    cap_day: str
    capa_status: str
    profit: str
    kpi: str
    epc: str
    description: str
    status: str
    manager: str
    date_added: str


# --------- Creds: ENV или файл ---------
def get_creds() -> Credentials:
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    raw = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if raw:
        # Railway: берём JSON из переменной окружения
        return Credentials.from_service_account_info(json.loads(raw), scopes=scopes)

    # Локально: читаем файл (если у тебя файл лежит в bot/, укажи это в .env)
    path = getattr(settings, "google_service_file", "credentials.json")
    return Credentials.from_service_account_file(path, scopes=scopes)


def get_agcm():
    return gspread_asyncio.AsyncioGspreadClientManager(get_creds)


# --------- Кэш офферов ---------
_cache: List[Offer] = []
_cache_ts: float | None = None

def _cache_expired() -> bool:
    if _cache_ts is None:
        return True
    ttl = int(getattr(settings, "refresh_sec", 300) or 300)
    return (time.monotonic() - _cache_ts) > ttl


# --------- Парс строки ---------
def _offer_from_row(row: Iterable[Any]) -> Offer:
    r = ["" if v is None else str(v) for v in row]
    r += [""] * (14 - len(r))  # подстраховка по длине
    return Offer(
        name=r[1], geo=r[2], traffic=r[3], payout=r[4],
        cap_day=r[5], capa_status=r[6], profit=r[7], kpi=r[8],
        epc=r[9], description=r[10], status=r[11], manager=r[12], date_added=r[13],
    )


# --------- Загрузка из Google Sheets ---------
async def _query() -> List[Offer]:
    # 1) имя листа из ENV, если задано; 2) иначе твой хардкод; 3) иначе первый лист
    worksheet_name = os.environ.get("SHEETS_WORKSHEET") or "Update on cap for August Viktoria TopRange"

    agcm = get_agcm()
    client = await agcm.authorize()
    sh = await client.open_by_key(settings.sheets_id)

    ws = None
    if worksheet_name:
        try:
            ws = await sh.worksheet(worksheet_name)
        except Exception:
            # если такого листа нет — возьмём первый
            ws = await sh.get_worksheet(0)
    else:
        ws = await sh.get_worksheet(0)

    rows = await ws.get_all_values()
    offers: List[Offer] = []
    for row in rows[1:]:  # пропускаем заголовок
        if not row or not any(str(c).strip() for c in row):
            continue
        offers.append(_offer_from_row(row))
    return offers


# --------- Публичные функции (офферы) ---------
async def get_offers(force: bool = False) -> List[Offer]:
    global _cache, _cache_ts
    if force or _cache_expired():
        _cache = await _query()
        _cache_ts = time.monotonic()
    return _cache

async def geos() -> List[str]:
    offers = await get_offers()
    return sorted({(o.geo or "").strip() for o in offers if (o.geo or "").strip()})

async def offers_by_geo(geo: str) -> List[Offer]:
    g = (geo or "").strip()
    return [o for o in await get_offers() if (o.geo or "").strip() == g]

async def top_offers() -> List[Offer]:
    return [o for o in await get_offers() if "топ" in (o.status or "").lower()]


# ===================== Доступ (партнёры) =====================

# Название листа со списком ID (можно переопределить переменной окружения)
_PARTNERS_WS = os.environ.get("PARTNERS_WORKSHEET", "partners")

# Кэш партнёров
_p_cache: Set[int] = set()
_p_ts: float | None = None

def _p_cache_expired() -> bool:
    global _p_ts
    if _p_ts is None:
        return True
    # кэшируем список партнёров на 60 секунд
    return (time.monotonic() - _p_ts) > 60


async def _partners_ws():
    """Открыть лист с партнёрами. Если нет — создать с заголовком user_id."""
    agcm = get_agcm()
    client = await agcm.authorize()
    sh = await client.open_by_key(settings.sheets_id)
    try:
        ws = await sh.worksheet(_PARTNERS_WS)
    except Exception:
        # создаём лист и ставим заголовок
        ws = await sh.add_worksheet(title=_PARTNERS_WS, rows=100, cols=1)
        await ws.update("A1", [["user_id"]])
    return ws


async def partner_ids() -> Set[int]:
    """Считать id партнёров из листа (с кэшем)."""
    global _p_cache, _p_ts
    if not _p_cache_expired():
        return _p_cache

    try:
        ws = await _partners_ws()
        values = await ws.get_all_values()
    except Exception:
        return set()

    ids: Set[int] = set()
    for row in values[1:]:
        if not row or not row[0].strip():
            continue
        try:
            ids.add(int(row[0].strip()))
        except ValueError:
            continue

    _p_cache = ids
    _p_ts = time.monotonic()
    return ids


async def add_partner(user_id: int) -> bool:
    """Добавить user_id. True — добавили, False — уже был."""
    ids = await partner_ids()
    if user_id in ids:
        return False
    ws = await _partners_ws()
    await ws.append_row([str(user_id)])
    # сбрасываем кэш
    global _p_cache, _p_ts
    _p_cache = set()
    _p_ts = None
    return True


async def remove_partner(user_id: int) -> bool:
    """Удалить user_id. True — удалили, False — не найден."""
    ws = await _partners_ws()
    values = await ws.get_all_values()
    row_idx = None
    for i, row in enumerate(values[1:], start=2):  # начинаем со 2-й строки
        if row and row[0].strip() == str(user_id):
            row_idx = i
            break
    if row_idx is None:
        return False
    await ws.delete_rows(row_idx)
    # сбрасываем кэш
    global _p_cache, _p_ts
    _p_cache = set()
    _p_ts = None
    return True

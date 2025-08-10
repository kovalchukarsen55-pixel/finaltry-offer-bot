import gspread_asyncio
from google.oauth2.service_account import Credentials
from typing import List
from dataclasses import dataclass

from bot.config import settings

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

def get_creds():
    return Credentials.from_service_account_file(
        settings.google_service_file,
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )

def get_agcm():
    return gspread_asyncio.AsyncioGspreadClientManager(get_creds)

_cache: List[Offer] = []

async def _query():
    agcm = get_agcm()
    client = await agcm.authorize()  
    sh = await client.open_by_key(settings.sheets_id)
    ws = await sh.worksheet("Update on cap for August Viktoria TopRange")  
    rows = await ws.get_all_values()
    offers = []
    for row in rows[1:]:
        if not any(row): continue
        row += [""] * (14 - len(row))
        offer = Offer(
            name=row[1], geo=row[2], traffic=row[3], payout=row[4],
            cap_day=row[5], capa_status=row[6], profit=row[7], kpi=row[8],
            epc=row[9], description=row[10], status=row[11], manager=row[12], date_added=row[13],
        )
        offers.append(offer)
    return offers


async def get_offers(force=False) -> List[Offer]:
    global _cache
    if not _cache or force:
        _cache = await _query()
    return _cache

async def geos():
    offers = await get_offers()
    return sorted(set(o.geo for o in offers if o.geo))

async def offers_by_geo(geo: str):
    offers = await get_offers()
    return [o for o in offers if o.geo == geo]

async def top_offers():
    offers = await get_offers()
    return [o for o in offers if "топ" in o.status.lower()]

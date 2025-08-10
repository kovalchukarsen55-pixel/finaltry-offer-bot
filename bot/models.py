from dataclasses import dataclass


@dataclass(slots=True)
class Offer:
    name: str
    geo: str          # 🇧🇷
    traffic: str      # Facebook, Google …
    payout: str       # "$29" / "20 EUR"
    kpi: str | None   # "Да"/"Нет" или пусто
    epc: str | None   # "1.3$" / "-"
    top: bool         # помечено ли как топ недели
    creatives: list[str]  # ссылки

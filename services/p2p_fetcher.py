import aiohttp
from typing import Dict, List, Optional

class P2PFetcher:
    """Helper for fetching P2P orders from various exchanges."""
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    async def _post_json(self, url: str, payload: Dict) -> Dict:
        async with self.session.post(url, json=payload) as r:
            return await r.json()

    async def fetch_binance_orders(
        self, asset: str = "USDT", fiat: str = "UAH", rows: int = 1
    ) -> Optional[Dict[str, float]]:
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        buy_payload = {"asset": asset, "fiat": fiat, "tradeType": "SELL", "page": 1, "rows": rows}
        sell_payload = {"asset": asset, "fiat": fiat, "tradeType": "BUY", "page": 1, "rows": rows}
        buy_resp = await self._post_json(url, buy_payload)
        sell_resp = await self._post_json(url, sell_payload)
        try:
            buy_adv = buy_resp.get("data", [])[0]["adv"]
            sell_adv = sell_resp.get("data", [])[0]["adv"]
        except Exception:
            return None
        return {
            "buy": float(buy_adv.get("price", 0)),
            "sell": float(sell_adv.get("price", 0)),
            "volume": float(buy_adv.get("tradableQuantity", 0)),
            "url": f"https://p2p.binance.com/en/adDetail?advNo={buy_adv.get('advNo')}",
        }

    async def fetch_bybit_orders(
        self, asset: str = "USDT", fiat: str = "RUB", rows: int = 1
    ) -> Optional[Dict[str, float]]:
        url = "https://api2.bybit.com/fiat/otc/item/online"
        buy_payload = {"tokenId": asset, "currencyId": fiat, "payment": [], "side": 1, "size": rows, "page": 1}
        sell_payload = {"tokenId": asset, "currencyId": fiat, "payment": [], "side": 2, "size": rows, "page": 1}
        buy_resp = await self._post_json(url, buy_payload)
        sell_resp = await self._post_json(url, sell_payload)
        try:
            buy_adv = buy_resp.get("result", {}).get("items", [])[0]
            sell_adv = sell_resp.get("result", {}).get("items", [])[0]
        except Exception:
            return None
        return {
            "buy": float(buy_adv.get("price", 0)),
            "sell": float(sell_adv.get("price", 0)),
            "volume": float(buy_adv.get("stock", 0)),
            "url": f"https://www.bybit.com/fiat/trade/otc/detail?id={buy_adv.get('id')}",
        }

    async def fetch_orders(self) -> List[Dict]:
        orders: List[Dict] = []
        binance = await self.fetch_binance_orders()
        if binance:
            orders.append({**binance, "symbol": "USDT", "price": binance["buy"], "sell_price": binance["sell"]})
        bybit = await self.fetch_bybit_orders()
        if bybit:
            orders.append({**bybit, "symbol": "USDT", "price": bybit["buy"], "sell_price": bybit["sell"]})
        return orders

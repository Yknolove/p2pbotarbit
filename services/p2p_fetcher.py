"""
P2P exchange fetcher for the ArbitPro bot.

This helper class encapsulates the logic for retrieving best buy and sell
orders from supported P2P trading platforms like Binance and Bybit.  It
matches the original implementation from the upstream repository and
provides a unified ``fetch_orders`` method for higher‑level components such
as the aggregator.
"""

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
        """Return best buy/sell order info from Binance P2P."""

        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

        buy_payload = {
            "asset": asset,
            "fiat": fiat,
            "tradeType": "SELL",  # others sell, we buy
            "page": 1,
            "rows": rows,
        }

        sell_payload = {
            "asset": asset,
            "fiat": fiat,
            "tradeType": "BUY",  # others buy, we sell
            "page": 1,
            "rows": rows,
        }

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
        """Return best buy/sell order info from Bybit P2P."""

        url = "https://api2.bybit.com/fiat/otc/item/online"

        buy_payload = {
            "tokenId": asset,
            "currencyId": fiat,
            "payment": [],
            "side": 1,  # we buy crypto
            "size": rows,
            "page": 1,
        }

        sell_payload = {
            "tokenId": asset,
            "currencyId": fiat,
            "payment": [],
            "side": 2,  # we sell crypto
            "size": rows,
            "page": 1,
        }

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

    async def fetch_bitget_orders(
        self,
        asset: str = "USDT",
        fiat: str = "UAH",
        rows: int = 1,
    ) -> Optional[Dict[str, float]]:
        """
        Return best buy/sell order info from Bitget P2P.

        Bitget's public API does not currently expose an unauthenticated endpoint
        for querying real‑time P2P advertisement prices.  Accessing the P2P
        orderbook requires authenticated REST requests with a valid API key and
        timestamp parameters (see the Bitget API documentation).  Without
        credentials, this method returns ``None`` and therefore Bitget orders
        are not considered in the arbitrage calculations.  To integrate Bitget
        support, provide API credentials and implement the necessary request
        signatures.

        Args:
            asset: Trading asset symbol, e.g. "USDT".
            fiat: Fiat currency code, e.g. "UAH".
            rows: Number of rows to fetch (not used in this stub).

        Returns:
            A dictionary with keys ``buy``, ``sell``, ``volume`` and ``url`` or
            ``None`` if Bitget P2P data could not be retrieved.
        """
        # NOTE: The Bitget API for P2P requires authentication.  To implement
        # support, supply API credentials and build a signed request to
        # /api/p2p/v1/merchant/advList or another appropriate endpoint.  See
        # https://bitgetlimited.github.io/apidoc/en/spot/ for details.
        return None

    async def fetch_orders(self) -> List[Dict]:
        """Gather P2P orders from supported exchanges."""

        orders: List[Dict] = []

        binance = await self.fetch_binance_orders()
        if binance:
            orders.append({
                **binance,
                "symbol": "USDT",
                "price": binance["buy"],
                "sell_price": binance["sell"],
            })

        bybit = await self.fetch_bybit_orders()
        if bybit:
            orders.append({
                **bybit,
                "symbol": "USDT",
                "price": bybit["buy"],
                "sell_price": bybit["sell"],
            })

        # Fetch from Bitget (will be None until implemented)
        bitget = await self.fetch_bitget_orders()
        if bitget:
            orders.append({
                **bitget,
                "symbol": "USDT",
                "price": bitget["buy"],
                "sell_price": bitget["sell"],
            })

        return orders
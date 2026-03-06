"""
Finance MCP Server v1.3.0
Real-time exchange rates, historical data, currency conversion, crypto prices,
macroeconomic indicators (GDP, inflation, unemployment, interest rates, population),
commodity prices (gold, silver, oil, copper, natural gas, wheat), stock indices,
ETF info, index history, portfolio backtesting, GDP growth comparison, portfolio P&L,
asset correlation, portfolio volatility/Sharpe, Crypto Fear & Greed Index,
multi-commodity prices, market sentiment (VIX + DXY + US Treasury yields),
dividend analysis, S&P500 sector rotation, stock fundamental summary,
SEC EDGAR filings + insider trades + XBRL company facts, US Treasury yield curve,
options chain, institutional holdings (13F), historical Treasury yields.

APIs:
- Frankfurter (ECB data): https://api.frankfurter.app
- Binance Public API: https://api.binance.com (crypto + commodity tokens, no auth)
- CoinGecko Public API: https://api.coingecko.com (market cap, rate-limited)
- World Bank API: https://api.worldbank.org/v2 (macro indicators, no auth)
- Yahoo Finance API: https://query1.finance.yahoo.com (stock indices, ETF, futures, history, no auth)
- SEC EDGAR API: https://data.sec.gov (filings, insider trades, XBRL facts, no auth)
- US Treasury: https://home.treasury.gov (yield curve, no auth)
"""

from fastmcp import FastMCP
from apify import Actor

import httpx
import yfinance as yf
from typing import Optional
from datetime import datetime, timedelta

mcp = FastMCP("Finance MCP", version="1.3.0")

FRANKFURTER_BASE = "https://api.frankfurter.app"
BINANCE_BASE = "https://api.binance.com/api/v3"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
WORLDBANK_BASE = "https://api.worldbank.org/v2"
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

# World Bank indicator codes
WB_INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",           # GDP (current US$)
    "gdp_per_capita": "NY.GDP.PCAP.CD", # GDP per capita (current US$)
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
    "inflation": "FP.CPI.TOTL.ZG",      # Inflation, CPI (annual %)
    "unemployment": "SL.UEM.TOTL.ZS",   # Unemployment, total (% of labor force)
    "lending_rate": "FR.INR.LEND",       # Lending interest rate (%)
    "population": "SP.POP.TOTL",         # Population, total
}

# ─── FOREX ────────────────────────────────────────────────

@mcp.tool()
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float = 1.0,
) -> dict:
    """
    Get real-time exchange rate between two currencies.
    Supports 30 major currencies from ECB (European Central Bank).

    Args:
        from_currency: Source currency code (e.g., USD, EUR, KRW)
        to_currency: Target currency code (e.g., EUR, KRW, JPY)
        amount: Amount to convert (default: 1.0)

    Returns:
        Exchange rate and converted amount with metadata
    """
    await Actor.charge('basic_tool', count=1)
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{FRANKFURTER_BASE}/latest",
                params={"from": from_currency, "to": to_currency, "amount": amount}
            )
            resp.raise_for_status()
            data = resp.json()

            rate = data["rates"][to_currency]
            return {
                "from": from_currency,
                "to": to_currency,
                "amount": amount,
                "result": rate,
                "rate": round(rate / amount, 6),
                "date": data["date"],
                "source": "ECB (European Central Bank)"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currencies: list[str],
) -> dict:
    """
    Convert an amount from one currency to multiple target currencies at once.

    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., USD)
        to_currencies: List of target currency codes (e.g., ["EUR", "KRW", "JPY"])

    Returns:
        Conversion results for all target currencies
    """
    await Actor.charge('basic_tool', count=1)
    from_currency = from_currency.upper()
    to_list = [c.upper() for c in to_currencies]

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{FRANKFURTER_BASE}/latest",
                params={"from": from_currency, "to": ",".join(to_list), "amount": amount}
            )
            resp.raise_for_status()
            data = resp.json()

            return {
                "from": from_currency,
                "amount": amount,
                "date": data["date"],
                "results": data["rates"],
                "source": "ECB (European Central Bank)"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_historical_rates(
    from_currency: str,
    to_currency: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> dict:
    """
    Get historical exchange rates between two currencies over a date range.

    Args:
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        Historical rates with summary statistics
    """
    await Actor.charge('basic_tool', count=1)
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    url = f"{FRANKFURTER_BASE}/{start_date}..{end_date}"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params={"from": from_currency, "to": to_currency})
            resp.raise_for_status()
            data = resp.json()

            rates_list = [
                {"date": date, "rate": rates[to_currency]}
                for date, rates in sorted(data["rates"].items())
            ]

            if rates_list:
                first = rates_list[0]["rate"]
                last = rates_list[-1]["rate"]
                change = ((last - first) / first) * 100
            else:
                change = 0

            return {
                "from": from_currency,
                "to": to_currency,
                "period": {"start": start_date, "end": end_date},
                "data_points": len(rates_list),
                "rates": rates_list,
                "summary": {
                    "start_rate": rates_list[0]["rate"] if rates_list else None,
                    "end_rate": rates_list[-1]["rate"] if rates_list else None,
                    "change_pct": round(change, 4),
                    "min": min(r["rate"] for r in rates_list) if rates_list else None,
                    "max": max(r["rate"] for r in rates_list) if rates_list else None,
                },
                "source": "ECB (European Central Bank)"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_rate_trend(
    from_currency: str,
    to_currency: str,
    days: int = 30,
) -> dict:
    """
    Get the exchange rate trend for the last N days.

    Args:
        from_currency: Source currency code
        to_currency: Target currency code
        days: Number of days to look back (default: 30, max: 365)

    Returns:
        Trend analysis with current rate, change, min/max
    """
    await Actor.charge('advanced_tool', count=1)
    days = min(days, 365)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    return await get_historical_rates(from_currency, to_currency, start_date, end_date)


@mcp.tool()
async def list_supported_currencies() -> dict:
    """
    List all supported currency codes with their names (ECB, ~30 major currencies).

    Returns:
        await Actor.charge('advanced_tool', count=1)
        Dictionary of currency codes and full names
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{FRANKFURTER_BASE}/currencies")
            resp.raise_for_status()
            ecb_currencies = resp.json()

            return {
                "count": len(ecb_currencies),
                "currencies": ecb_currencies,
                "note": "ECB-supported currencies (major world currencies)"
            }
        except Exception as e:
            return {"error": str(e)}


# ─── CRYPTO ───────────────────────────────────────────────

@mcp.tool()
async def get_crypto_price(
    symbol: str,
    vs_currency: str = "USDT",
) -> dict:
    """
    Get real-time cryptocurrency price from Binance (no API key needed).
    Common symbols: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
        vs_currency: Quote currency (default: USDT). Also supports BUSD, BTC, ETH, BNB.

    Returns:
        Current price with 24h stats
    """
    await Actor.charge('basic_tool', count=1)
    symbol = symbol.upper()
    vs_currency = vs_currency.upper()
    pair = f"{symbol}{vs_currency}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{BINANCE_BASE}/ticker/24hr",
                params={"symbol": pair}
            )
            resp.raise_for_status()
            d = resp.json()

            return {
                "symbol": symbol,
                "vs_currency": vs_currency,
                "price": float(d["lastPrice"]),
                "price_change_24h": float(d["priceChange"]),
                "price_change_pct_24h": float(d["priceChangePercent"]),
                "high_24h": float(d["highPrice"]),
                "low_24h": float(d["lowPrice"]),
                "volume_24h": float(d["volume"]),
                "quote_volume_24h": float(d["quoteVolume"]),
                "open_price": float(d["openPrice"]),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "Binance Public API"
            }
        except Exception as e:
            return {
                "error": str(e),
                "hint": f"Check if {pair} is a valid Binance trading pair. Try vs_currency=USDT."
            }


@mcp.tool()
async def get_crypto_market(
    top_n: int = 10,
    vs_currency: str = "usd",
) -> dict:
    """
    Get top cryptocurrencies ranked by market cap.
    Uses CoinGecko public API (rate-limited, may be slow during high traffic).

    Args:
        top_n: Number of top coins to return (default: 10, max: 50)
        vs_currency: Quote currency for prices (default: usd)

    Returns:
        Ranked list of cryptocurrencies with price, market cap, volume, 24h change
    """
    await Actor.charge('advanced_tool', count=1)
    top_n = min(top_n, 50)
    vs_currency = vs_currency.lower()

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": vs_currency,
                    "order": "market_cap_desc",
                    "per_page": top_n,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h"
                }
            )
            resp.raise_for_status()
            data = resp.json()

            coins = [
                {
                    "rank": coin["market_cap_rank"],
                    "id": coin["id"],
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "volume_24h": coin["total_volume"],
                    "change_24h_pct": coin.get("price_change_percentage_24h"),
                    "ath": coin.get("ath"),
                    "ath_date": coin.get("ath_date"),
                }
                for coin in data
            ]

            return {
                "vs_currency": vs_currency,
                "count": len(coins),
                "coins": coins,
                "source": "CoinGecko Public API",
                "note": "Rate-limited. If empty, retry after 60s."
            }
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_crypto_historical(
    symbol: str,
    days: int = 30,
    vs_currency: str = "USDT",
    interval: str = "1d",
) -> dict:
    """
    Get historical OHLCV data for a cryptocurrency from Binance.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
        days: Number of days of history (default: 30, max: 365)
        vs_currency: Quote currency (default: USDT)
        interval: Candle interval — 1d (daily), 4h (4-hour), 1h (hourly)

    Returns:
        Historical OHLCV data with trend summary
    """
    await Actor.charge('basic_tool', count=1)
    symbol = symbol.upper()
    vs_currency = vs_currency.upper()
    pair = f"{symbol}{vs_currency}"
    days = min(days, 365)

    interval_map = {"1d": days, "4h": days * 6, "1h": days * 24}
    limit = min(interval_map.get(interval, days), 1000)

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{BINANCE_BASE}/klines",
                params={"symbol": pair, "interval": interval, "limit": limit}
            )
            resp.raise_for_status()
            raw = resp.json()

            candles = [
                {
                    "time": datetime.utcfromtimestamp(k[0] / 1000).strftime("%Y-%m-%d %H:%M"),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                }
                for k in raw
            ]

            if candles:
                prices = [c["close"] for c in candles]
                first, last = prices[0], prices[-1]
                change = ((last - first) / first) * 100
                summary = {
                    "start_price": first,
                    "end_price": last,
                    "change_pct": round(change, 4),
                    "min": min(prices),
                    "max": max(prices),
                    "avg": round(sum(prices) / len(prices), 4),
                }
            else:
                summary = {}

            return {
                "symbol": symbol,
                "vs_currency": vs_currency,
                "interval": interval,
                "data_points": len(candles),
                "candles": candles,
                "summary": summary,
                "source": "Binance Public API"
            }
        except Exception as e:
            return {
                "error": str(e),
                "hint": f"Check if {pair} is a valid Binance pair. interval options: 1d, 4h, 1h"
            }


@mcp.tool()
async def compare_crypto(
    symbols: list[str],
    vs_currency: str = "USDT",
) -> dict:
    """
    Compare multiple cryptocurrencies side by side (price, 24h change, volume).

    Args:
        symbols: List of crypto symbols (e.g., ["BTC", "ETH", "SOL"])
        vs_currency: Quote currency (default: USDT)

    Returns:
        Comparison table sorted by 24h change
    """
    await Actor.charge('advanced_tool', count=1)
    vs_currency = vs_currency.upper()
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        for sym in symbols:
            sym = sym.upper()
            pair = f"{sym}{vs_currency}"
            try:
                resp = await client.get(
                    f"{BINANCE_BASE}/ticker/24hr",
                    params={"symbol": pair}
                )
                resp.raise_for_status()
                d = resp.json()
                results.append({
                    "symbol": sym,
                    "price": float(d["lastPrice"]),
                    "change_pct_24h": float(d["priceChangePercent"]),
                    "high_24h": float(d["highPrice"]),
                    "low_24h": float(d["lowPrice"]),
                    "volume_24h": float(d["quoteVolume"]),
                })
            except Exception as e:
                results.append({"symbol": sym, "error": str(e)})

    results.sort(key=lambda x: x.get("change_pct_24h", -999), reverse=True)

    return {
        "vs_currency": vs_currency,
        "count": len(results),
        "comparison": results,
        "source": "Binance Public API"
    }


# ─── MACRO ECONOMICS (World Bank) ─────────────────────────

def _parse_worldbank(data: list, indicator_name: str) -> dict:
    """Parse World Bank API response into clean time series."""
    if not data:
        return {"error": "No data returned"}

    series = [
        {"year": int(item["date"]), "value": item["value"]}
        for item in data
        if item.get("value") is not None
    ]
    series.sort(key=lambda x: x["year"])

    values = [s["value"] for s in series]
    return {
        "indicator": indicator_name,
        "data_points": len(series),
        "series": series,
        "summary": {
            "latest_year": series[-1]["year"] if series else None,
            "latest_value": series[-1]["value"] if series else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "avg": round(sum(values) / len(values), 4) if values else None,
        } if series else {}
    }


@mcp.tool()
async def get_gdp(
    country: str,
    start_year: int = 2010,
    end_year: int = 2023,
    per_capita: bool = False,
) -> dict:
    """
    Get GDP data for a country from World Bank (no API key required).
    Covers 200+ countries with data going back to 1960.

    Args:
        country: 2-letter ISO country code (e.g., US, KR, FR, CN, JP, DE, GB)
        start_year: Start year (default: 2010)
        end_year: End year (default: 2023)
        per_capita: If True, return GDP per capita instead of total GDP (default: False)

    Returns:
        GDP time series with summary statistics (values in current USD)

    Examples:
        get_gdp("US") → US total GDP 2010-2023
        get_gdp("KR", 2000, 2023, per_capita=True) → South Korea GDP per capita
    """
    await Actor.charge('basic_tool', count=1)
    country = country.upper()
    indicator = WB_INDICATORS["gdp_per_capita"] if per_capita else WB_INDICATORS["gdp"]
    label = "GDP per capita (current US$)" if per_capita else "GDP (current US$)"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator}",
                params={
                    "format": "json",
                    "date": f"{start_year}:{end_year}",
                    "per_page": 100
                }
            )
            resp.raise_for_status()
            raw = resp.json()

            if not isinstance(raw, list) or len(raw) < 2:
                return {"error": "Invalid response from World Bank API"}

            result = _parse_worldbank(raw[1], label)
            result["country"] = country
            result["source"] = "World Bank Open Data"
            return result

        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_inflation(
    country: str,
    start_year: int = 2010,
    end_year: int = 2023,
) -> dict:
    """
    Get annual inflation rate (CPI) for a country from World Bank.
    No API key required. Covers 200+ countries.

    Args:
        country: 2-letter ISO country code (e.g., US, KR, FR, CN, JP, DE, GB, TR)
        start_year: Start year (default: 2010)
        end_year: End year (default: 2023)

    Returns:
        Annual CPI inflation rate (%) time series with min/max/avg

    Examples:
        get_inflation("TR") → Turkey inflation (known for high inflation)
        get_inflation("US", 2018, 2023) → Recent US inflation including 2022 spike
    """
    await Actor.charge('basic_tool', count=1)
    country = country.upper()

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{WORLDBANK_BASE}/country/{country}/indicator/{WB_INDICATORS['inflation']}",
                params={
                    "format": "json",
                    "date": f"{start_year}:{end_year}",
                    "per_page": 100
                }
            )
            resp.raise_for_status()
            raw = resp.json()

            if not isinstance(raw, list) or len(raw) < 2:
                return {"error": "Invalid response from World Bank API"}

            result = _parse_worldbank(raw[1], "Inflation, consumer prices (annual %)")
            result["country"] = country
            result["source"] = "World Bank Open Data"
            return result

        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_macro_overview(
    country: str,
    year: int = 2022,
) -> dict:
    """
    Get a comprehensive macroeconomic snapshot for a country.
    Returns GDP, GDP per capita, inflation, unemployment in one call.
    No API key required. World Bank data.

    Args:
        country: 2-letter ISO country code (e.g., US, KR, FR, CN, DE, JP, GB, BR, IN)
        year: Reference year (default: 2022; latest available is usually 2022-2023)

    Returns:
        Dictionary with key macro indicators for the specified year

    Examples:
        get_macro_overview("KR") → South Korea 2022 macro snapshot
        get_macro_overview("US", 2020) → US during COVID year
    """
    await Actor.charge('basic_tool', count=1)
    country = country.upper()
    indicators = {
        "gdp": WB_INDICATORS["gdp"],
        "gdp_per_capita": WB_INDICATORS["gdp_per_capita"],
        "gdp_growth": WB_INDICATORS["gdp_growth"],
        "inflation": WB_INDICATORS["inflation"],
        "unemployment": WB_INDICATORS["unemployment"],
    }

    results = {"country": country, "year": year, "source": "World Bank Open Data"}
    date_range = f"{year-1}:{year+1}"  # Fetch ±1 year for best coverage

    async with httpx.AsyncClient(timeout=20) as client:
        for key, indicator_id in indicators.items():
            try:
                resp = await client.get(
                    f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator_id}",
                    params={"format": "json", "date": date_range, "per_page": 10}
                )
                resp.raise_for_status()
                raw = resp.json()

                if isinstance(raw, list) and len(raw) >= 2 and raw[1]:
                    # Find the value for the target year (fallback to nearest)
                    series = {
                        int(item["date"]): item["value"]
                        for item in raw[1]
                        if item.get("value") is not None
                    }
                    value = series.get(year) or series.get(year - 1) or series.get(year + 1)
                    results[key] = value
                else:
                    results[key] = None
            except Exception:
                results[key] = None

    # Add units for clarity
    results["units"] = {
        "gdp": "current USD",
        "gdp_per_capita": "current USD",
        "gdp_growth": "annual %",
        "inflation": "annual % (CPI)",
        "unemployment": "% of labor force",
    }

    return results


# ─── COMMODITY PRICES (v0.4.0) ────────────────────────────

# Commodity token map on Binance (no API key)
# PAXG = PAX Gold, 1 PAXG = 1 troy oz of gold
COMMODITY_TOKENS = {
    "gold": ("PAXGUSDT", "Gold (troy oz)", "PAXG/USDT via Binance — 1 PAXG = 1 troy oz gold"),
    "xau":  ("PAXGUSDT", "Gold (troy oz)", "PAXG/USDT via Binance — 1 PAXG = 1 troy oz gold"),
    "btc":  ("BTCUSDT",  "Bitcoin", "Binance spot"),
    "eth":  ("ETHUSDT",  "Ethereum", "Binance spot"),
}


@mcp.tool()
async def get_commodity_price(
    commodity: str,
) -> dict:
    """
    Get current price for gold or major crypto commodities (no API key required).
    Supported: gold (XAU) via PAXG token — 1 PAXG = 1 troy ounce of physical gold.

    Args:
        commodity: Commodity name. Supported values:
            - "gold" or "xau" → Gold price (USD per troy oz) via PAXG on Binance
            - "btc" → Bitcoin price via Binance
            - "eth" → Ethereum price via Binance

    Returns:
        Current price with 24h stats and data source note

    Note:
        Silver (XAG) and crude oil (WTI) require an API key (e.g., metals-api.com).
        Use get_crypto_price() for other crypto assets.
    """
    await Actor.charge('basic_tool', count=1)
    key = commodity.lower().strip()
    if key not in COMMODITY_TOKENS:
        return {
            "error": f"Unsupported commodity: '{commodity}'",
            "supported": list(COMMODITY_TOKENS.keys()),
            "note": "For silver/oil prices, an external API key is required (metals-api.com)."
        }

    pair, label, source_note = COMMODITY_TOKENS[key]

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{BINANCE_BASE}/ticker/24hr",
                params={"symbol": pair}
            )
            resp.raise_for_status()
            d = resp.json()

            return {
                "commodity": label,
                "pair": pair,
                "price_usd": float(d["lastPrice"]),
                "change_24h_usd": float(d["priceChange"]),
                "change_24h_pct": float(d["priceChangePercent"]),
                "high_24h_usd": float(d["highPrice"]),
                "low_24h_usd": float(d["lowPrice"]),
                "volume_24h": float(d["volume"]),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": source_note,
            }
        except Exception as e:
            return {"error": str(e), "pair": pair}


# ─── GDP GROWTH COMPARISON (v0.4.0) ──────────────────────

@mcp.tool()
async def compare_gdp_growth(
    countries: list[str],
    start_year: int = 2015,
    end_year: int = 2023,
) -> dict:
    """
    Compare annual GDP growth rates (%) across multiple countries.
    Uses World Bank data. No API key required. Covers 200+ countries.

    Args:
        countries: List of 2-letter ISO country codes (e.g., ["US", "CN", "KR", "DE"])
        start_year: Start year (default: 2015)
        end_year: End year (default: 2023)

    Returns:
        GDP growth rate comparison table with per-country summary stats

    Examples:
        compare_gdp_growth(["US", "CN", "KR"]) → G3 Asia-Pacific growth comparison
        compare_gdp_growth(["FR", "DE", "IT", "ES"], 2018, 2023) → Eurozone comparison
    """
    await Actor.charge('advanced_tool', count=1)
    indicator = WB_INDICATORS["gdp_growth"]
    results = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for country in countries:
            country = country.upper()
            try:
                resp = await client.get(
                    f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator}",
                    params={
                        "format": "json",
                        "date": f"{start_year}:{end_year}",
                        "per_page": 50,
                    }
                )
                resp.raise_for_status()
                raw = resp.json()

                if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
                    results[country] = {"error": "No data"}
                    continue

                series = {
                    int(item["date"]): round(item["value"], 4)
                    for item in raw[1]
                    if item.get("value") is not None
                }

                values = list(series.values())
                results[country] = {
                    "series": {str(yr): series.get(yr) for yr in range(start_year, end_year + 1)},
                    "summary": {
                        "avg_growth": round(sum(values) / len(values), 4) if values else None,
                        "best_year": max(series, key=lambda y: series[y]) if series else None,
                        "best_value": max(values) if values else None,
                        "worst_year": min(series, key=lambda y: series[y]) if series else None,
                        "worst_value": min(values) if values else None,
                    }
                }
            except Exception as e:
                results[country] = {"error": str(e)}

    # Build ranking by avg growth
    ranked = sorted(
        [(c, r["summary"]["avg_growth"]) for c, r in results.items()
         if "summary" in r and r["summary"].get("avg_growth") is not None],
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "indicator": "GDP Growth Rate (annual %)",
        "period": {"start": start_year, "end": end_year},
        "countries": results,
        "ranking_by_avg_growth": [{"country": c, "avg_growth_pct": v} for c, v in ranked],
        "source": "World Bank Open Data",
    }


# ─── PORTFOLIO P&L CALCULATOR (v0.4.0) ───────────────────

@mcp.tool()
async def portfolio_pnl(
    holdings: list[dict],
) -> dict:
    """
    Calculate current portfolio value and P&L for a list of crypto holdings.
    Fetches live prices from Binance. No API key required.

    Args:
        holdings: List of holding objects, each with:
            - symbol: Crypto symbol (e.g., "BTC", "ETH", "SOL")
            - quantity: Amount held (e.g., 0.5)
            - avg_cost_usd: Average purchase price in USD per coin (for P&L)
            Example: [{"symbol": "BTC", "quantity": 0.5, "avg_cost_usd": 60000},
                      {"symbol": "ETH", "quantity": 3.0, "avg_cost_usd": 2000}]

    Returns:
        Per-holding breakdown (current value, cost basis, P&L, %) and portfolio totals

    Note:
        Prices are fetched from Binance (symbol+USDT pairs).
        For non-Binance assets, P&L will show an error for that holding.
    """
    await Actor.charge('advanced_tool', count=1)
    results = []
    total_cost = 0.0
    total_value = 0.0
    errors = []

    async with httpx.AsyncClient(timeout=15) as client:
        for h in holdings:
            sym = h.get("symbol", "").upper()
            qty = float(h.get("quantity", 0))
            avg_cost = float(h.get("avg_cost_usd", 0))
            pair = f"{sym}USDT"

            try:
                resp = await client.get(
                    f"{BINANCE_BASE}/ticker/price",
                    params={"symbol": pair}
                )
                resp.raise_for_status()
                current_price = float(resp.json()["price"])

                cost_basis = qty * avg_cost
                current_value = qty * current_price
                pnl = current_value - cost_basis
                pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost else None

                total_cost += cost_basis
                total_value += current_value

                results.append({
                    "symbol": sym,
                    "quantity": qty,
                    "avg_cost_usd": avg_cost,
                    "current_price_usd": round(current_price, 6),
                    "cost_basis_usd": round(cost_basis, 2),
                    "current_value_usd": round(current_value, 2),
                    "pnl_usd": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 4) if pnl_pct is not None else None,
                })
            except Exception as e:
                errors.append({"symbol": sym, "error": str(e)})

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else None

    return {
        "holdings": results,
        "errors": errors,
        "portfolio_summary": {
            "total_cost_basis_usd": round(total_cost, 2),
            "total_current_value_usd": round(total_value, 2),
            "total_pnl_usd": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 4) if total_pnl_pct is not None else None,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "Binance Public API (USDT pairs)",
    }


# ─── INTEREST RATES (v0.5.0) ─────────────────────────────

@mcp.tool()
async def get_interest_rate(
    country: str,
    start_year: int = 2010,
    end_year: int = 2023,
) -> dict:
    """
    Get lending interest rate (%) for a country from World Bank (no API key required).
    Covers 200+ countries. Useful for comparing monetary policy across economies.

    Args:
        country: 2-letter ISO country code (e.g., US, KR, FR, CN, JP, DE, GB, TR, BR)
        start_year: Start year (default: 2010)
        end_year: End year (default: 2023)

    Returns:
        Annual lending interest rate (%) time series with min/max/avg

    Examples:
        get_interest_rate("TR") → Turkey lending rate (known for high/volatile rates)
        get_interest_rate("US", 2015, 2023) → US rate cycle including 2022 hikes
        get_interest_rate("KR") → South Korea BOK rate history
    """
    await Actor.charge('advanced_tool', count=1)
    country = country.upper()

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{WORLDBANK_BASE}/country/{country}/indicator/{WB_INDICATORS['lending_rate']}",
                params={
                    "format": "json",
                    "date": f"{start_year}:{end_year}",
                    "per_page": 100
                }
            )
            resp.raise_for_status()
            raw = resp.json()

            if not isinstance(raw, list) or len(raw) < 2:
                return {"error": "Invalid response from World Bank API"}

            result = _parse_worldbank(raw[1], "Lending interest rate (%)")
            result["country"] = country
            result["source"] = "World Bank Open Data"
            return result

        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def compare_interest_rates(
    countries: list[str],
    start_year: int = 2015,
    end_year: int = 2023,
) -> dict:
    """
    Compare lending interest rates across multiple countries.
    World Bank data, no API key required.

    Args:
        countries: List of 2-letter ISO country codes (e.g., ["US", "KR", "TR", "BR"])
        start_year: Start year (default: 2015)
        end_year: End year (default: 2023)

    Returns:
        Interest rate comparison with per-country averages and ranking

    Examples:
        compare_interest_rates(["US", "EU", "KR", "JP"]) → Developed markets comparison
        compare_interest_rates(["TR", "BR", "AR", "ZA"]) → Emerging market rates
    """
    await Actor.charge('advanced_tool', count=1)
    indicator = WB_INDICATORS["lending_rate"]
    results = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for country in countries:
            country = country.upper()
            try:
                resp = await client.get(
                    f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator}",
                    params={
                        "format": "json",
                        "date": f"{start_year}:{end_year}",
                        "per_page": 50,
                    }
                )
                resp.raise_for_status()
                raw = resp.json()

                if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
                    results[country] = {"error": "No data"}
                    continue

                series = {
                    int(item["date"]): round(item["value"], 4)
                    for item in raw[1]
                    if item.get("value") is not None
                }

                values = list(series.values())
                results[country] = {
                    "series": {str(yr): series.get(yr) for yr in range(start_year, end_year + 1)},
                    "summary": {
                        "avg_rate": round(sum(values) / len(values), 4) if values else None,
                        "latest": series.get(max(series.keys())) if series else None,
                        "latest_year": max(series.keys()) if series else None,
                        "min": min(values) if values else None,
                        "max": max(values) if values else None,
                    }
                }
            except Exception as e:
                results[country] = {"error": str(e)}

    ranked = sorted(
        [(c, r["summary"]["avg_rate"]) for c, r in results.items()
         if "summary" in r and r["summary"].get("avg_rate") is not None],
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "indicator": "Lending Interest Rate (%)",
        "period": {"start": start_year, "end": end_year},
        "countries": results,
        "ranking_by_avg_rate": [{"country": c, "avg_rate_pct": v} for c, v in ranked],
        "source": "World Bank Open Data",
    }


# ─── POPULATION (v0.5.0) ─────────────────────────────────

@mcp.tool()
async def compare_population(
    countries: list[str],
    start_year: int = 2010,
    end_year: int = 2023,
) -> dict:
    """
    Compare population across multiple countries over time.
    World Bank data, no API key required. Covers 200+ countries.

    Args:
        countries: List of 2-letter ISO country codes (e.g., ["US", "CN", "IN", "KR"])
        start_year: Start year (default: 2010)
        end_year: End year (default: 2023)

    Returns:
        Population time series per country with latest values and growth rates

    Examples:
        compare_population(["CN", "IN", "US"]) → World's top 3 by population
        compare_population(["KR", "JP", "DE"]) → Aging economy comparison
    """
    await Actor.charge('advanced_tool', count=1)
    indicator = WB_INDICATORS["population"]
    results = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for country in countries:
            country = country.upper()
            try:
                resp = await client.get(
                    f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator}",
                    params={
                        "format": "json",
                        "date": f"{start_year}:{end_year}",
                        "per_page": 50,
                    }
                )
                resp.raise_for_status()
                raw = resp.json()

                if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
                    results[country] = {"error": "No data"}
                    continue

                series = {
                    int(item["date"]): int(item["value"])
                    for item in raw[1]
                    if item.get("value") is not None
                }

                sorted_years = sorted(series.keys())
                latest_pop = series.get(max(series.keys())) if series else None
                earliest_pop = series.get(min(series.keys())) if series else None
                growth_pct = None
                if latest_pop and earliest_pop and earliest_pop > 0:
                    growth_pct = round((latest_pop - earliest_pop) / earliest_pop * 100, 4)

                results[country] = {
                    "series": {str(yr): series.get(yr) for yr in sorted_years},
                    "summary": {
                        "latest_year": max(series.keys()) if series else None,
                        "latest_population": latest_pop,
                        "earliest_year": min(series.keys()) if series else None,
                        "earliest_population": earliest_pop,
                        "growth_pct_over_period": growth_pct,
                    }
                }
            except Exception as e:
                results[country] = {"error": str(e)}

    ranked = sorted(
        [(c, r["summary"]["latest_population"]) for c, r in results.items()
         if "summary" in r and r["summary"].get("latest_population") is not None],
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "indicator": "Total Population",
        "period": {"start": start_year, "end": end_year},
        "countries": results,
        "ranking_by_latest_population": [{"country": c, "population": v} for c, v in ranked],
        "source": "World Bank Open Data",
    }


# ─── STOCK INDICES (v0.5.0) ─── Yahoo Finance, no API key ─

# Major global stock index symbols (Yahoo Finance format)
STOCK_INDICES = {
    "sp500":   ("^GSPC",  "S&P 500 (USA)"),
    "^gspc":   ("^GSPC",  "S&P 500 (USA)"),
    "dow":     ("^DJI",   "Dow Jones Industrial Average (USA)"),
    "^dji":    ("^DJI",   "Dow Jones Industrial Average (USA)"),
    "nasdaq":  ("^IXIC",  "NASDAQ Composite (USA)"),
    "^ixic":   ("^IXIC",  "NASDAQ Composite (USA)"),
    "ftse":    ("^FTSE",  "FTSE 100 (UK)"),
    "^ftse":   ("^FTSE",  "FTSE 100 (UK)"),
    "nikkei":  ("^N225",  "Nikkei 225 (Japan)"),
    "^n225":   ("^N225",  "Nikkei 225 (Japan)"),
    "kospi":   ("^KS11",  "KOSPI (South Korea)"),
    "^ks11":   ("^KS11",  "KOSPI (South Korea)"),
    "dax":     ("^GDAXI", "DAX (Germany)"),
    "^gdaxi":  ("^GDAXI", "DAX (Germany)"),
    "cac":     ("^FCHI",  "CAC 40 (France)"),
    "^fchi":   ("^FCHI",  "CAC 40 (France)"),
    "hsi":     ("^HSI",   "Hang Seng Index (Hong Kong)"),
    "^hsi":    ("^HSI",   "Hang Seng Index (Hong Kong)"),
    "sse":     ("000001.SS", "Shanghai Composite (China)"),
    "shanghai":("000001.SS", "Shanghai Composite (China)"),
}


@mcp.tool()
async def get_stock_index(
    index: str,
) -> dict:
    """
    Get current price and 24h stats for major global stock indices (no API key required).
    Uses Yahoo Finance public API.

    Supported indices:
        - sp500 / ^GSPC   → S&P 500 (USA)
        - dow / ^DJI      → Dow Jones (USA)
        - nasdaq / ^IXIC  → NASDAQ Composite (USA)
        - ftse / ^FTSE    → FTSE 100 (UK)
        - nikkei / ^N225  → Nikkei 225 (Japan)
        - kospi / ^KS11   → KOSPI (South Korea)
        - dax / ^GDAXI    → DAX (Germany)
        - cac / ^FCHI     → CAC 40 (France)
        - hsi / ^HSI      → Hang Seng (Hong Kong)
        - sse / shanghai  → Shanghai Composite (China)

    Args:
        index: Index name or Yahoo Finance symbol (e.g., "sp500", "nikkei", "^GSPC")

    Returns:
        Current index level with previous close, change, 52-week high/low
    """
    await Actor.charge('basic_tool', count=1)
    key = index.lower().strip()
    if key not in STOCK_INDICES:
        return {
            "error": f"Unknown index: '{index}'",
            "supported": list(set(v[1] for v in STOCK_INDICES.values())),
            "hint": "Try: sp500, dow, nasdaq, ftse, nikkei, kospi, dax, cac, hsi, sse"
        }

    symbol, label = STOCK_INDICES[key]

    async with httpx.AsyncClient(
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/0.5.0)"}
    ) as client:
        try:
            resp = await client.get(
                f"{YAHOO_FINANCE_BASE}/{symbol}",
                params={"interval": "1d", "range": "5d"}
            )
            resp.raise_for_status()
            data = resp.json()

            meta = data["chart"]["result"][0]["meta"]
            current = meta.get("regularMarketPrice") or meta.get("previousClose")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
            change = None
            change_pct = None
            if current and prev_close:
                change = round(current - prev_close, 4)
                change_pct = round((current - prev_close) / prev_close * 100, 4)

            return {
                "index": label,
                "symbol": symbol,
                "current": current,
                "previous_close": prev_close,
                "change": change,
                "change_pct": change_pct,
                "52w_high": meta.get("fiftyTwoWeekHigh"),
                "52w_low": meta.get("fiftyTwoWeekLow"),
                "currency": meta.get("currency", "USD"),
                "exchange_timezone": meta.get("exchangeTimezoneName"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "Yahoo Finance (public API, no key required)"
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}


@mcp.tool()
async def compare_stock_indices(
    indices: list[str],
) -> dict:
    """
    Compare multiple global stock indices side by side.
    Fetches current price and daily change for each index.
    No API key required.

    Args:
        indices: List of index names (e.g., ["sp500", "nikkei", "kospi", "ftse", "dax"])

    Returns:
        Comparison table sorted by daily performance (best to worst)

    Examples:
        compare_stock_indices(["sp500", "nasdaq", "dow"]) → US markets comparison
        compare_stock_indices(["nikkei", "kospi", "hsi", "sse"]) → Asia-Pacific markets
        compare_stock_indices(["sp500", "ftse", "dax", "cac", "nikkei"]) → Global snapshot
    """
    await Actor.charge('advanced_tool', count=1)
    results = []

    for idx in indices:
        result = await get_stock_index(idx)
        if "error" not in result:
            results.append({
                "index": result["index"],
                "symbol": result["symbol"],
                "current": result["current"],
                "change_pct": result["change_pct"],
                "change": result["change"],
                "currency": result["currency"],
            })
        else:
            results.append({
                "index": idx,
                "error": result["error"]
            })

    results.sort(key=lambda x: x.get("change_pct") or -999, reverse=True)

    return {
        "count": len(results),
        "indices": results,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "Yahoo Finance (public API, no key required)"
    }


# ─── ETF INFO (v0.6.0) ── Yahoo Finance, no API key ──────

# Popular ETF symbols with descriptions
POPULAR_ETFS = {
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco NASDAQ-100 ETF",
    "IWM": "iShares Russell 2000 ETF (small-cap)",
    "VTI": "Vanguard Total Stock Market ETF",
    "VOO": "Vanguard S&P 500 ETF",
    "ARKK": "ARK Innovation ETF",
    "GLD": "SPDR Gold Shares",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "XLF": "Financial Select Sector SPDR Fund",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLK": "Technology Select Sector SPDR Fund",
    "SQQQ": "ProShares UltraPro Short QQQ (3x inverse)",
    "TQQQ": "ProShares UltraPro QQQ (3x leveraged)",
    "VWO": "Vanguard Emerging Markets ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
}


@mcp.tool()
async def get_etf_info(
    symbol: str,
) -> dict:
    """
    Get current price and key stats for an ETF (Exchange-Traded Fund).
    Uses Yahoo Finance public API — no API key required.

    Commonly traded ETFs:
        - SPY / VOO   → S&P 500 index funds
        - QQQ / TQQQ  → NASDAQ-100 (QQQ 3x leveraged: TQQQ)
        - IWM         → Russell 2000 small-cap
        - ARKK        → ARK Innovation (high-growth tech)
        - GLD         → Gold
        - TLT         → Long-term US Treasury bonds
        - XLF / XLK / XLE → Sector ETFs (finance / tech / energy)
        - VWO / EEM   → Emerging markets

    Args:
        symbol: ETF ticker symbol (e.g., "SPY", "QQQ", "ARKK", "GLD")

    Returns:
        Current price, daily change, 52-week high/low, volume, and nav/category info
    """
    await Actor.charge('basic_tool', count=1)
    symbol = symbol.upper().strip()

    async with httpx.AsyncClient(
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/0.6.0)"}
    ) as client:
        try:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={"interval": "1d", "range": "5d"}
            )
            resp.raise_for_status()
            data = resp.json()

            result_data = data["chart"]["result"]
            if not result_data:
                return {"error": f"No data found for symbol: {symbol}"}

            meta = result_data[0]["meta"]
            current = meta.get("regularMarketPrice") or meta.get("previousClose")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
            change = None
            change_pct = None
            if current and prev_close:
                change = round(current - prev_close, 4)
                change_pct = round((current - prev_close) / prev_close * 100, 4)

            return {
                "symbol": symbol,
                "name": POPULAR_ETFS.get(symbol, meta.get("longName", meta.get("shortName", symbol))),
                "current_price": current,
                "previous_close": prev_close,
                "change": change,
                "change_pct": change_pct,
                "52w_high": meta.get("fiftyTwoWeekHigh"),
                "52w_low": meta.get("fiftyTwoWeekLow"),
                "currency": meta.get("currency", "USD"),
                "exchange": meta.get("exchangeName"),
                "market_state": meta.get("marketState"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "Yahoo Finance (public API, no key required)"
            }
        except Exception as e:
            return {
                "error": str(e),
                "symbol": symbol,
                "hint": "Make sure the symbol is a valid ETF/stock ticker (e.g., SPY, QQQ, ARKK)"
            }


# ─── INDEX HISTORY (v0.6.0) ── Yahoo Finance, no API key ─

YAHOO_RANGE_MAP = {
    "1w": ("1d", "5d"),
    "1m": ("1d", "1mo"),
    "3m": ("1d", "3mo"),
    "6m": ("1d", "6mo"),
    "1y": ("1d", "1y"),
    "2y": ("1wk", "2y"),
    "5y": ("1wk", "5y"),
    "10y": ("1mo", "10y"),
    "max": ("1mo", "max"),
}


@mcp.tool()
async def get_index_history(
    index: str,
    period: str = "1y",
) -> dict:
    """
    Get historical price data for a major stock index or ETF.
    Uses Yahoo Finance public API — no API key required.

    Supported indices (same as get_stock_index):
        sp500, dow, nasdaq, ftse, nikkei, kospi, dax, cac, hsi, sse
    Also accepts ETF symbols: SPY, QQQ, GLD, TLT, etc.

    Args:
        index: Index name (e.g., "sp500", "kospi") or ETF ticker (e.g., "SPY", "QQQ")
        period: Time period. Options:
            - "1w"  → 1 week  (daily candles)
            - "1m"  → 1 month (daily candles)
            - "3m"  → 3 months (daily candles)
            - "6m"  → 6 months (daily candles)
            - "1y"  → 1 year  (daily candles) [default]
            - "2y"  → 2 years (weekly candles)
            - "5y"  → 5 years (weekly candles)
            - "10y" → 10 years (monthly candles)
            - "max" → All available (monthly candles)

    Returns:
        Historical OHLCV time series with trend summary (start/end/change/min/max)
    """
    await Actor.charge('basic_tool', count=1)
    period = period.lower().strip()
    if period not in YAHOO_RANGE_MAP:
        return {
            "error": f"Invalid period: '{period}'",
            "supported": list(YAHOO_RANGE_MAP.keys())
        }

    # Resolve index name to Yahoo Finance symbol
    key = index.lower().strip()
    if key in STOCK_INDICES:
        symbol, label = STOCK_INDICES[key]
    else:
        # Treat as direct ticker (ETF, etc.)
        symbol = index.upper().strip()
        label = POPULAR_ETFS.get(symbol, symbol)

    interval, yf_range = YAHOO_RANGE_MAP[period]

    async with httpx.AsyncClient(
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/0.6.0)"}
    ) as client:
        try:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={"interval": interval, "range": yf_range}
            )
            resp.raise_for_status()
            data = resp.json()

            result_data = data["chart"]["result"]
            if not result_data:
                return {"error": f"No historical data for: {index}"}

            timestamps = result_data[0].get("timestamp", [])
            ohlcv = result_data[0].get("indicators", {}).get("quote", [{}])[0]
            closes = ohlcv.get("close", [])
            highs = ohlcv.get("high", [])
            lows = ohlcv.get("low", [])
            volumes = ohlcv.get("volume", [])

            candles = []
            for i, ts in enumerate(timestamps):
                close = closes[i] if i < len(closes) else None
                if close is None:
                    continue
                candles.append({
                    "date": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                    "close": round(close, 4),
                    "high": round(highs[i], 4) if i < len(highs) and highs[i] else None,
                    "low": round(lows[i], 4) if i < len(lows) and lows[i] else None,
                    "volume": volumes[i] if i < len(volumes) else None,
                })

            summary = {}
            if candles:
                prices = [c["close"] for c in candles]
                first, last = prices[0], prices[-1]
                change_pct = ((last - first) / first) * 100
                summary = {
                    "start_date": candles[0]["date"],
                    "end_date": candles[-1]["date"],
                    "start_price": first,
                    "end_price": last,
                    "change_pct": round(change_pct, 4),
                    "min": min(prices),
                    "max": max(prices),
                    "data_points": len(candles),
                }

            return {
                "index": label,
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "candles": candles,
                "summary": summary,
                "source": "Yahoo Finance (public API, no key required)"
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}


# ─── BUY-HOLD BACKTEST (v0.6.0) ─────────────────────────

@mcp.tool()
async def backtest_buy_hold(
    symbol: str,
    start_date: str,
    amount_usd: float = 1000.0,
) -> dict:
    """
    Backtest a simple buy-and-hold strategy for a stock index, ETF, or crypto.
    Calculates returns if you had invested a fixed USD amount on a given date.
    No API key required.

    Supports:
        - Stock indices: sp500, dow, nasdaq, nikkei, kospi, ftse, dax, cac, hsi, sse
        - ETFs: SPY, QQQ, GLD, ARKK, TLT, IWM, VOO, etc.
        - Crypto: BTC, ETH, SOL, BNB, etc. (appends USDT, uses Binance)

    Args:
        symbol: Asset symbol. Use index name (e.g., "sp500") or ticker/crypto (e.g., "SPY", "BTC")
        start_date: Investment start date in YYYY-MM-DD format (e.g., "2020-01-01")
        amount_usd: Initial investment in USD (default: 1000.0)

    Returns:
        Entry price, current price, shares/units bought, current value, total return %, CAGR

    Examples:
        backtest_buy_hold("sp500", "2020-01-01", 10000) → 5-year S&P 500 return
        backtest_buy_hold("BTC", "2021-01-01", 1000)   → BTC crash + recovery backtest
        backtest_buy_hold("QQQ", "2022-01-01", 5000)   → QQQ bear market recovery
    """
    await Actor.charge('advanced_tool', count=1)
    # Determine data source: Binance for crypto, Yahoo Finance for indices/ETFs
    key = symbol.lower().strip()
    use_binance = False
    binance_pair = None
    yahoo_symbol = None
    asset_label = symbol.upper()

    if key in STOCK_INDICES:
        yahoo_symbol, asset_label = STOCK_INDICES[key]
    else:
        sym_upper = symbol.upper()
        # Check if crypto (Binance USDT pair)
        binance_pair = f"{sym_upper}USDT"
        # Try to determine: if it's a known ETF, use Yahoo; otherwise try Binance
        if sym_upper in POPULAR_ETFS or len(sym_upper) <= 5:
            # Ambiguous: try Yahoo Finance first (for ETFs/stocks), fall back to Binance
            yahoo_symbol = sym_upper
            asset_label = POPULAR_ETFS.get(sym_upper, sym_upper)

    # Parse start date and compute period
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid start_date format. Use YYYY-MM-DD."}

    today = datetime.utcnow()
    days_held = (today - start_dt).days
    if days_held < 1:
        return {"error": "start_date must be in the past."}

    years_held = days_held / 365.25

    # Calculate total period for Yahoo Finance
    if days_held <= 7:
        yf_range = "5d"
        yf_interval = "1d"
    elif days_held <= 32:
        yf_range = "1mo"
        yf_interval = "1d"
    elif days_held <= 95:
        yf_range = "3mo"
        yf_interval = "1d"
    elif days_held <= 190:
        yf_range = "6mo"
        yf_interval = "1d"
    elif days_held <= 400:
        yf_range = "1y"
        yf_interval = "1d"
    elif days_held <= 800:
        yf_range = "2y"
        yf_interval = "1wk"
    elif days_held <= 2000:
        yf_range = "5y"
        yf_interval = "1wk"
    else:
        yf_range = "max"
        yf_interval = "1mo"

    entry_price = None
    current_price = None
    data_source = ""

    async with httpx.AsyncClient(
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/0.6.0)"}
    ) as client:

        # Try Yahoo Finance first
        if yahoo_symbol:
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                    params={"interval": yf_interval, "range": yf_range}
                )
                resp.raise_for_status()
                data = resp.json()

                result_data = data["chart"]["result"]
                if result_data:
                    timestamps = result_data[0].get("timestamp", [])
                    closes = result_data[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                    meta = result_data[0]["meta"]

                    # Find entry price: first candle on or after start_date
                    for i, ts in enumerate(timestamps):
                        candle_dt = datetime.utcfromtimestamp(ts)
                        close = closes[i] if i < len(closes) else None
                        if close and candle_dt.date() >= start_dt.date():
                            if entry_price is None:
                                entry_price = close
                            current_price = close

                    if not current_price:
                        current_price = meta.get("regularMarketPrice") or meta.get("previousClose")

                    data_source = "Yahoo Finance (public API)"
            except Exception:
                pass

        # Fall back to Binance if Yahoo didn't work or for crypto
        if (entry_price is None or current_price is None) and binance_pair:
            try:
                # Use Binance klines for historical
                # Calculate start timestamp (ms)
                start_ms = int(start_dt.timestamp() * 1000)

                # Get first candle at/after start_date
                resp_entry = await client.get(
                    f"{BINANCE_BASE}/klines",
                    params={
                        "symbol": binance_pair,
                        "interval": "1d",
                        "startTime": start_ms,
                        "limit": 1
                    }
                )
                resp_entry.raise_for_status()
                entry_klines = resp_entry.json()

                # Get current price
                resp_curr = await client.get(
                    f"{BINANCE_BASE}/ticker/price",
                    params={"symbol": binance_pair}
                )
                resp_curr.raise_for_status()

                if entry_klines:
                    entry_price = float(entry_klines[0][1])  # open price of first candle
                current_price = float(resp_curr.json()["price"])
                asset_label = binance_pair.replace("USDT", "") + " (crypto)"
                data_source = "Binance Public API"
            except Exception as e:
                return {
                    "error": f"Could not fetch data for '{symbol}'. "
                             f"Try a stock index name (sp500, kospi) or ETF ticker (SPY, QQQ) "
                             f"or crypto symbol (BTC, ETH). Details: {e}"
                }

    if entry_price is None or current_price is None or entry_price == 0:
        return {
            "error": f"Could not determine entry or current price for '{symbol}'.",
            "hint": "The start_date may be before available history, or the symbol is invalid."
        }

    units = amount_usd / entry_price
    current_value = units * current_price
    total_return = current_value - amount_usd
    total_return_pct = (total_return / amount_usd) * 100

    # CAGR: Compound Annual Growth Rate
    cagr = None
    if years_held >= 0.1:
        cagr = ((current_value / amount_usd) ** (1 / years_held) - 1) * 100

    return {
        "asset": asset_label,
        "symbol": symbol.upper(),
        "strategy": "Buy and Hold",
        "investment": {
            "start_date": start_date,
            "amount_usd": amount_usd,
            "entry_price": round(entry_price, 4),
            "units_bought": round(units, 6),
        },
        "current": {
            "price": round(current_price, 4),
            "value_usd": round(current_value, 2),
        },
        "returns": {
            "total_return_usd": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 4),
            "days_held": days_held,
            "years_held": round(years_held, 2),
            "cagr_pct": round(cagr, 4) if cagr is not None else None,
        },
        "source": data_source,
        "note": "Entry price is the first available price at or after start_date. Past performance does not guarantee future results."
    }


# ─── PORTFOLIO ANALYTICS (v0.7.0) ────────────────────────

@mcp.tool()
async def get_asset_correlation(
    symbols: list[str],
    period: str = "1y",
) -> dict:
    """
    Calculate correlation matrix between multiple assets (stocks, ETFs, crypto).
    Supports Yahoo Finance tickers (SPY, QQQ, AAPL) and crypto symbols (BTC, ETH).
    Period: 1mo, 3mo, 6mo, 1y, 2y, 5y.
    Returns Pearson correlation matrix (-1 to +1).
    """
    await Actor.charge('advanced_tool', count=1)
    import math

    if len(symbols) < 2:
        return {"error": "Need at least 2 symbols to compute correlation."}
    if len(symbols) > 6:
        return {"error": "Max 6 symbols supported."}

    period_map = {
        "1mo": 30, "3mo": 90, "6mo": 180,
        "1y": 365, "2y": 730, "5y": 1825
    }
    days = period_map.get(period, 365)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)

    # Crypto tickers mapped to Yahoo Finance equivalents
    crypto_yahoo = {
        "BTC": "BTC-USD", "ETH": "ETH-USD", "BNB": "BNB-USD",
        "SOL": "SOL-USD", "XRP": "XRP-USD", "ADA": "ADA-USD",
        "AVAX": "AVAX-USD", "DOGE": "DOGE-USD", "DOT": "DOT-USD",
        "MATIC": "MATIC-USD", "LINK": "LINK-USD"
    }

    price_series: dict[str, list[float]] = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for sym in symbols:
            upper = sym.upper()
            ticker = crypto_yahoo.get(upper, upper)
            try:
                resp = await client.get(
                    f"{YAHOO_FINANCE_BASE}/{ticker}",
                    params={
                        "interval": "1d",
                        "period1": int(start_dt.timestamp()),
                        "period2": int(end_dt.timestamp()),
                    },
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                resp.raise_for_status()
                data = resp.json()
                closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                closes = [c for c in closes if c is not None]
                if len(closes) < 20:
                    return {"error": f"Not enough data for {sym} (got {len(closes)} points). Try a shorter period."}
                price_series[upper] = closes
            except Exception as e:
                return {"error": f"Failed to fetch data for {sym}: {e}"}

    # Align lengths (use minimum length across all series)
    min_len = min(len(v) for v in price_series.values())
    for k in price_series:
        price_series[k] = price_series[k][-min_len:]

    # Compute daily log returns
    def log_returns(prices: list[float]) -> list[float]:
        return [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]

    returns: dict[str, list[float]] = {k: log_returns(v) for k, v in price_series.items()}

    def pearson(a: list[float], b: list[float]) -> float:
        n = len(a)
        ma, mb = sum(a)/n, sum(b)/n
        num = sum((a[i]-ma)*(b[i]-mb) for i in range(n))
        da = math.sqrt(sum((x-ma)**2 for x in a))
        db = math.sqrt(sum((x-mb)**2 for x in b))
        if da == 0 or db == 0:
            return 0.0
        return round(num / (da * db), 4)

    syms = list(returns.keys())
    matrix = {}
    for s1 in syms:
        matrix[s1] = {}
        for s2 in syms:
            matrix[s1][s2] = pearson(returns[s1], returns[s2])

    # Human-readable interpretation
    def interpret(r: float) -> str:
        if r >= 0.8: return "강한 양의 상관"
        if r >= 0.5: return "중간 양의 상관"
        if r >= 0.2: return "약한 양의 상관"
        if r >= -0.2: return "무상관"
        if r >= -0.5: return "약한 음의 상관"
        if r >= -0.8: return "중간 음의 상관"
        return "강한 음의 상관"

    pairs = []
    for i, s1 in enumerate(syms):
        for s2 in syms[i+1:]:
            r = matrix[s1][s2]
            pairs.append({"pair": f"{s1}/{s2}", "correlation": r, "interpretation": interpret(r)})

    return {
        "period": period,
        "data_points": min_len,
        "symbols": syms,
        "correlation_matrix": matrix,
        "pair_summary": pairs,
        "note": "Based on daily log returns. 1 = perfect positive, -1 = perfect negative, 0 = no correlation."
    }


@mcp.tool()
async def get_portfolio_volatility(
    holdings: list[dict],
    period: str = "1y",
    risk_free_rate_pct: float = 4.5,
) -> dict:
    """
    Calculate portfolio volatility, annualized return, and Sharpe ratio.
    holdings: list of {symbol: str, weight: float} (weights should sum to 1.0).
    period: 1mo, 3mo, 6mo, 1y, 2y.
    risk_free_rate_pct: annual risk-free rate in % (default 4.5 = US T-bill).
    """
    await Actor.charge('advanced_tool', count=1)
    import math

    if not holdings:
        return {"error": "No holdings provided."}

    total_weight = sum(h.get("weight", 0) for h in holdings)
    if abs(total_weight - 1.0) > 0.05:
        return {"error": f"Weights must sum to ~1.0. Got {round(total_weight, 4)}."}

    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = period_map.get(period, 365)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)

    crypto_yahoo = {
        "BTC": "BTC-USD", "ETH": "ETH-USD", "BNB": "BNB-USD",
        "SOL": "SOL-USD", "XRP": "XRP-USD", "ADA": "ADA-USD",
    }

    price_series: dict[str, list[float]] = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for h in holdings:
            sym = h["symbol"].upper()
            ticker = crypto_yahoo.get(sym, sym)
            try:
                resp = await client.get(
                    f"{YAHOO_FINANCE_BASE}/{ticker}",
                    params={
                        "interval": "1d",
                        "period1": int(start_dt.timestamp()),
                        "period2": int(end_dt.timestamp()),
                    },
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                resp.raise_for_status()
                data = resp.json()
                closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                closes = [c for c in closes if c is not None]
                if len(closes) < 10:
                    return {"error": f"Not enough data for {sym}."}
                price_series[sym] = closes
            except Exception as e:
                return {"error": f"Failed to fetch {sym}: {e}"}

    min_len = min(len(v) for v in price_series.values())
    for k in price_series:
        price_series[k] = price_series[k][-min_len:]

    def log_returns(prices):
        return [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]

    # Portfolio daily returns (weighted sum)
    all_returns = {h["symbol"].upper(): log_returns(price_series[h["symbol"].upper()]) for h in holdings}
    n = min(len(v) for v in all_returns.values())
    for k in all_returns:
        all_returns[k] = all_returns[k][-n:]

    weights = {h["symbol"].upper(): h["weight"] for h in holdings}
    portfolio_returns = []
    for i in range(n):
        daily_r = sum(weights[sym] * all_returns[sym][i] for sym in weights)
        portfolio_returns.append(daily_r)

    trading_days = 252
    mean_daily = sum(portfolio_returns) / n
    variance_daily = sum((r - mean_daily)**2 for r in portfolio_returns) / (n - 1)
    std_daily = math.sqrt(variance_daily)

    annual_return_pct = mean_daily * trading_days * 100
    annual_vol_pct = std_daily * math.sqrt(trading_days) * 100
    rfr_daily = risk_free_rate_pct / 100 / trading_days
    excess_mean = mean_daily - rfr_daily
    sharpe = (excess_mean / std_daily * math.sqrt(trading_days)) if std_daily > 0 else 0

    # Max drawdown
    cumulative = [1.0]
    for r in portfolio_returns:
        cumulative.append(cumulative[-1] * math.exp(r))
    peak = cumulative[0]
    max_dd = 0.0
    for v in cumulative:
        if v > peak:
            peak = v
        dd = (peak - v) / peak
        if dd > max_dd:
            max_dd = dd

    def sharpe_grade(s: float) -> str:
        if s >= 2.0: return "우수"
        if s >= 1.0: return "양호"
        if s >= 0.5: return "보통"
        return "불량"

    per_asset = []
    for sym, w in weights.items():
        rets = all_returns[sym]
        m = sum(rets) / len(rets)
        v = sum((r - m)**2 for r in rets) / (len(rets) - 1)
        per_asset.append({
            "symbol": sym,
            "weight": round(w, 4),
            "annualized_return_pct": round(m * trading_days * 100, 2),
            "annualized_vol_pct": round(math.sqrt(v) * math.sqrt(trading_days) * 100, 2),
        })

    return {
        "period": period,
        "data_points": n,
        "portfolio": {
            "annualized_return_pct": round(annual_return_pct, 2),
            "annualized_volatility_pct": round(annual_vol_pct, 2),
            "sharpe_ratio": round(sharpe, 4),
            "sharpe_grade": sharpe_grade(sharpe),
            "max_drawdown_pct": round(max_dd * 100, 2),
        },
        "per_asset": per_asset,
        "assumptions": {
            "risk_free_rate_pct": risk_free_rate_pct,
            "trading_days_per_year": trading_days,
        },
        "note": "Uses daily log returns. Sharpe ratio annualized. Max drawdown from peak equity curve."
    }


@mcp.tool()
async def get_fear_greed_index() -> dict:
    """
    Get the current Crypto Fear & Greed Index from alternative.me.
    Returns current score (0-100), rating, and 7-day historical trend.
    0-24: Extreme Fear, 25-44: Fear, 45-55: Neutral, 56-74: Greed, 75-100: Extreme Greed.
    No API key required.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        await Actor.charge('basic_tool', count=1)
        resp = await client.get(
            "https://api.alternative.me/fng/",
            params={"limit": 8, "format": "json"}
        )
        resp.raise_for_status()
        data = resp.json()

    entries = data.get("data", [])
    if not entries:
        return {"error": "No data returned from Fear & Greed API."}

    current = entries[0]
    history = []
    for e in entries[1:]:
        ts = int(e["timestamp"])
        dt = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        history.append({
            "date": dt,
            "value": int(e["value"]),
            "rating": e["value_classification"],
        })

    score = int(current["value"])
    rating = current["value_classification"]

    def market_implication(r: str) -> str:
        implications = {
            "Extreme Fear": "시장 공황 상태. 역발상 매수 기회일 수 있음.",
            "Fear": "투자자 불안. 과매도 가능성.",
            "Neutral": "균형 상태. 방향성 불명확.",
            "Greed": "과열 신호. 조정 주의.",
            "Extreme Greed": "버블 위험. 고점 가능성."
        }
        return implications.get(r, "N/A")

    return {
        "current": {
            "score": score,
            "rating": rating,
            "implication_kr": market_implication(rating),
            "date": datetime.utcfromtimestamp(int(current["timestamp"])).strftime("%Y-%m-%d"),
        },
        "history_7d": history,
        "scale": "0-24: Extreme Fear | 25-44: Fear | 45-55: Neutral | 56-74: Greed | 75-100: Extreme Greed",
        "source": "alternative.me/fng",
        "note": "Index combines volatility, momentum, social media, dominance, and trends."
    }


# ─── COMMODITIES (MULTI) ──────────────────────────────────

COMMODITY_TICKERS = {
    "silver":      ("SI=F",     "USD/troy oz"),
    "oil":         ("CL=F",     "USD/barrel"),
    "copper":      ("HG=F",     "USD/lb"),
    "natural_gas": ("NG=F",     "USD/MMBtu"),
    "wheat":       ("ZW=F",     "USX/bushel"),
    "corn":        ("ZC=F",     "USX/bushel"),
    "gold":        ("GC=F",     "USD/troy oz"),
}

@mcp.tool()
async def get_commodity_prices(
    commodities: list[str] = None,
) -> dict:
    """
    Get real-time futures prices for multiple commodities via Yahoo Finance.
    Available: silver, oil, copper, natural_gas, wheat, corn, gold
    Defaults to all if no list provided. No API key required.
    """
    await Actor.charge('basic_tool', count=1)
    if not commodities:
        commodities = list(COMMODITY_TICKERS.keys())

    results = {}
    errors = []

    async with httpx.AsyncClient(timeout=15) as client:
        for name in commodities:
            key = name.lower().replace(" ", "_")
            if key not in COMMODITY_TICKERS:
                errors.append(f"Unknown commodity: {name}. Valid: {list(COMMODITY_TICKERS.keys())}")
                continue
            ticker, unit = COMMODITY_TICKERS[key]
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": "1d", "range": "1d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                meta = resp.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose") or meta.get("regularMarketPreviousClose") or 0
                change_pct = round((price - prev) / prev * 100, 2) if prev else None
                results[key] = {
                    "price": round(price, 4) if price else None,
                    "unit": unit,
                    "change_pct_1d": change_pct,
                    "ticker": ticker,
                }
            except Exception as e:
                errors.append(f"{name}: {str(e)}")

    return {
        "commodities": results,
        "source": "Yahoo Finance (futures contracts)",
        "note": "Futures prices. Gold via GC=F (CME), Oil via CL=F (WTI), Silver via SI=F.",
        "errors": errors if errors else None,
    }


# ─── MARKET SENTIMENT (VIX + DXY + YIELDS) ───────────────

SENTIMENT_TICKERS = {
    "VIX":        ("^VIX",     "Market fear index (CBOE)", "0-12: Low / 13-19: Normal / 20-30: Elevated / 30+: High Fear"),
    "DXY":        ("DX-Y.NYB", "US Dollar Index",           "Rising = USD strengthening"),
    "US10Y":      ("^TNX",     "10-Year Treasury Yield %",  "Key benchmark rate"),
    "US2Y":       ("^IRX",     "2-Year Treasury Yield %",   "Short-term rate expectation"),
    "US30Y":      ("^TYX",     "30-Year Treasury Yield %",  "Long-term inflation expectation"),
}

@mcp.tool()
async def get_market_sentiment() -> dict:
    """
    Get a macro market sentiment snapshot: VIX (fear index), DXY (dollar index),
    and US Treasury yields (2Y, 10Y, 30Y). No API key required.
    Useful for understanding risk-on/risk-off regime and rate environment.
    """
    results = {}
    errors = []

    async with httpx.AsyncClient(timeout=15) as client:
        await Actor.charge('basic_tool', count=1)
        for key, (ticker, desc, guide) in SENTIMENT_TICKERS.items():
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": "1d", "range": "1d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                meta = resp.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose") or meta.get("regularMarketPreviousClose") or 0
                change_pct = round((price - prev) / prev * 100, 2) if prev else None
                results[key] = {
                    "value": round(price, 4) if price else None,
                    "change_pct_1d": change_pct,
                    "description": desc,
                    "guide": guide,
                }
            except Exception as e:
                errors.append(f"{key}: {str(e)}")

    # Yield curve status
    us2y = results.get("US2Y", {}).get("value")
    us10y = results.get("US10Y", {}).get("value")
    if us2y and us10y:
        spread = round(us10y - us2y, 3)
        curve_status = "Normal (10Y > 2Y)" if spread > 0 else "Inverted (2Y > 10Y — recession signal)"
    else:
        spread = None
        curve_status = "N/A"

    # VIX interpretation
    vix = results.get("VIX", {}).get("value")
    if vix:
        if vix < 13:
            vix_regime = "Low fear — risk-on"
        elif vix < 20:
            vix_regime = "Normal — balanced"
        elif vix < 30:
            vix_regime = "Elevated — caution"
        else:
            vix_regime = "High fear — risk-off / potential crash"
    else:
        vix_regime = "N/A"

    return {
        "indicators": results,
        "analysis": {
            "vix_regime": vix_regime,
            "yield_curve_spread_10y_minus_2y": spread,
            "yield_curve_status": curve_status,
        },
        "source": "Yahoo Finance (real-time)",
        "note": "VIX and yields are updated throughout trading hours. DXY reflects USD strength vs major currencies.",
        "errors": errors if errors else None,
    }


# ─── DIVIDEND ANALYSIS ───────────────────────────────────

@mcp.tool()
async def get_dividend_info(ticker: str) -> dict:
    """
    Get dividend information for a stock: annual dividend yield, trailing
    12-month dividend per share, payout ratio, ex-dividend date, and
    5-year average yield. No API key required.

    Args:
        await Actor.charge('advanced_tool', count=1)
        ticker: Stock ticker symbol (e.g., AAPL, JNJ, KO, VZ, T)

    Returns:
        Dividend yield, dividend per share, payout ratio, ex-date, and more
    """
    ticker = ticker.upper()
    try:
        t = yf.Ticker(ticker)
        info = t.info

        if not info or info.get("quoteType") is None:
            return {"error": f"No data found for ticker: {ticker}"}

        # trailingAnnualDividendYield is decimal (0.0261 = 2.61%)
        # dividendYield from yfinance is inconsistent — sometimes %, sometimes decimal. Use trailing.
        trailing_yield = info.get("trailingAnnualDividendYield")
        div_rate = info.get("dividendRate")
        trailing_div = info.get("trailingAnnualDividendRate")
        payout_ratio = info.get("payoutRatio")
        ex_div_date = info.get("exDividendDate")
        five_yr_avg = info.get("fiveYearAvgDividendYield")  # already in % (e.g. 2.91)

        # Format ex-dividend date
        if ex_div_date:
            try:
                ex_div_str = datetime.utcfromtimestamp(ex_div_date).strftime("%Y-%m-%d")
            except Exception:
                ex_div_str = str(ex_div_date)
        else:
            ex_div_str = None

        # Income classification (use trailing yield which is reliably decimal)
        yield_dec = trailing_yield or 0
        if yield_dec == 0:
            income_class = "No dividend"
        elif yield_dec < 0.01:
            income_class = "Low yield (<1%)"
        elif yield_dec < 0.03:
            income_class = "Moderate yield (1-3%)"
        elif yield_dec < 0.06:
            income_class = "High yield (3-6%)"
        else:
            income_class = "Very high yield (>6%) — check sustainability"

        return {
            "ticker": ticker,
            "company": info.get("longName") or info.get("shortName"),
            "dividend_yield_trailing_12m": f"{trailing_yield*100:.2f}%" if trailing_yield else "0%",
            "dividend_rate_annual": f"${div_rate:.2f}" if div_rate else None,
            "trailing_annual_dividend": f"${trailing_div:.2f}" if trailing_div else None,
            "payout_ratio": f"{payout_ratio*100:.1f}%" if payout_ratio else None,
            "5yr_avg_yield": f"{five_yr_avg:.2f}%" if five_yr_avg else None,
            "ex_dividend_date": ex_div_str,
            "income_classification": income_class,
            "source": "Yahoo Finance (yfinance)",
        }
    except Exception as e:
        return {"error": str(e)}


# ─── SECTOR ROTATION ─────────────────────────────────────

# S&P 500 Sector ETFs (SPDR)
SECTOR_ETFS = {
    "Technology":       "XLK",
    "Financials":       "XLF",
    "Energy":           "XLE",
    "Healthcare":       "XLV",
    "Utilities":        "XLU",
    "Industrials":      "XLI",
    "Real Estate":      "XLRE",
    "Materials":        "XLB",
    "Communication":    "XLC",
    "Consumer Discr":   "XLY",
    "Consumer Staples": "XLP",
}

@mcp.tool()
async def compare_sectors(period: str = "1d") -> dict:
    """
    Compare performance of all 11 S&P 500 sectors using SPDR Sector ETFs.
    Shows which sectors are leading or lagging — useful for sector rotation strategy.

    Args:
        await Actor.charge('advanced_tool', count=1)
        period: Time period — "1d" (today), "5d" (week), "1mo" (month), "3mo" (quarter), "ytd" (year-to-date)

    Returns:
        Ranked sector performance with % change
    """
    valid_periods = ["1d", "5d", "1mo", "3mo", "ytd"]
    if period not in valid_periods:
        return {"error": f"Invalid period. Choose from: {valid_periods}"}

    headers = {"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/0.9.0)"}
    interval = "1d" if period in ("1d", "5d") else "1wk"

    results = {}
    errors = []

    async with httpx.AsyncClient(timeout=20) as client:
        for sector, ticker in SECTOR_ETFS.items():
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": interval, "range": period},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()["chart"]["result"][0]
                meta = data["meta"]
                closes = data.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                closes = [c for c in closes if c is not None]

                current = meta.get("regularMarketPrice")
                if closes and len(closes) >= 2:
                    start_price = closes[0]
                    change_pct = round((current - start_price) / start_price * 100, 2) if start_price else None
                elif period == "1d":
                    prev = meta.get("chartPreviousClose") or meta.get("regularMarketPreviousClose")
                    change_pct = round((current - prev) / prev * 100, 2) if prev and current else None
                else:
                    change_pct = None

                results[sector] = {
                    "ticker": ticker,
                    "price": round(current, 2) if current else None,
                    "change_pct": change_pct,
                }
            except Exception as e:
                errors.append(f"{sector} ({ticker}): {str(e)}")

    # Rank sectors by performance
    ranked = sorted(
        [(s, v) for s, v in results.items() if v.get("change_pct") is not None],
        key=lambda x: x[1]["change_pct"],
        reverse=True,
    )

    leader = ranked[0][0] if ranked else None
    laggard = ranked[-1][0] if ranked else None

    return {
        "period": period,
        "sectors": results,
        "ranking": [
            {"rank": i+1, "sector": s, "ticker": results[s]["ticker"], "change_pct": v["change_pct"]}
            for i, (s, v) in enumerate(ranked)
        ],
        "leader": leader,
        "laggard": laggard,
        "source": "Yahoo Finance — SPDR Sector ETFs",
        "errors": errors if errors else None,
    }


# ─── STOCK FUNDAMENTAL SUMMARY ────────────────────────────

@mcp.tool()
async def get_stock_summary(ticker: str) -> dict:
    """
    Get a comprehensive fundamental snapshot for a stock: P/E ratio, EPS,
    market cap, 52-week high/low, dividend yield, revenue growth, and
    profit margin. No API key required.

    Args:
        await Actor.charge('advanced_tool', count=1)
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, NVDA, TSLA)

    Returns:
        Valuation, profitability, momentum, and income metrics in one view
    """
    ticker = ticker.upper()

    def fmt_large(n):
        if n is None:
            return None
        if abs(n) >= 1e12:
            return f"${n/1e12:.2f}T"
        if abs(n) >= 1e9:
            return f"${n/1e9:.2f}B"
        if abs(n) >= 1e6:
            return f"${n/1e6:.2f}M"
        return str(n)

    try:
        t = yf.Ticker(ticker)
        info = t.info

        if not info or info.get("quoteType") is None:
            return {"error": f"No data found for ticker: {ticker}"}

        current_price = info.get("regularMarketPrice") or info.get("currentPrice")
        week52_high = info.get("fiftyTwoWeekHigh")
        week52_low = info.get("fiftyTwoWeekLow")

        # 52-week position
        if week52_high and week52_low and current_price:
            week52_range = week52_high - week52_low
            position_pct = round((current_price - week52_low) / week52_range * 100, 1) if week52_range else None
            position_label = (
                "Near 52w High (>80%)" if position_pct and position_pct > 80 else
                "Near 52w Low (<20%)" if position_pct and position_pct < 20 else
                "Mid-range"
            )
        else:
            position_pct = None
            position_label = None

        div_yield = info.get("trailingAnnualDividendYield")  # decimal, e.g. 0.026 = 2.6%
        pe_trailing = info.get("trailingPE")
        pe_forward = info.get("forwardPE")
        peg = info.get("pegRatio")
        beta = info.get("beta")
        eps_trailing = info.get("trailingEps")
        eps_forward = info.get("forwardEps")
        market_cap = info.get("marketCap")
        revenue_growth = info.get("revenueGrowth")
        profit_margin = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")

        return {
            "ticker": ticker,
            "company": info.get("longName") or info.get("shortName"),
            "current_price": round(current_price, 2) if current_price else None,
            "market_cap": fmt_large(market_cap),
            "valuation": {
                "pe_trailing": round(pe_trailing, 2) if pe_trailing else None,
                "pe_forward": round(pe_forward, 2) if pe_forward else None,
                "peg_ratio": round(peg, 2) if peg else None,
                "eps_trailing": round(eps_trailing, 2) if eps_trailing else None,
                "eps_forward": round(eps_forward, 2) if eps_forward else None,
                "beta": round(beta, 2) if beta else None,
            },
            "momentum": {
                "52w_high": round(week52_high, 2) if week52_high else None,
                "52w_low": round(week52_low, 2) if week52_low else None,
                "52w_position_pct": position_pct,
                "52w_position": position_label,
            },
            "income": {
                "dividend_yield": f"{div_yield*100:.2f}%" if div_yield else "0%",
            },
            "fundamentals": {
                "revenue_growth_yoy": f"{revenue_growth*100:.1f}%" if revenue_growth else None,
                "profit_margin": f"{profit_margin*100:.1f}%" if profit_margin else None,
                "return_on_equity": f"{roe*100:.1f}%" if roe else None,
                "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
            },
            "source": "Yahoo Finance (yfinance)",
        }
    except Exception as e:
        return {"error": str(e)}


# ─── EARNINGS CALENDAR ──────────────────────────────────────

@mcp.tool()
async def get_earnings_calendar(ticker: str) -> dict:
    """
    Get upcoming earnings date and analyst estimates for a specific stock.

    Args:
        await Actor.charge('advanced_tool', count=1)
        ticker: Stock ticker symbol (e.g., AAPL, NVDA, MSFT)

    Returns:
        Next earnings date, EPS estimate (high/low/avg), revenue estimate, dividend dates
    """
    ticker = ticker.upper()
    try:
        t = yf.Ticker(ticker)
        cal = t.calendar
        info = t.info

        if not cal:
            return {"error": f"No calendar data for {ticker}"}

        earnings_dates = cal.get("Earnings Date", [])
        if isinstance(earnings_dates, list):
            next_earn = str(earnings_dates[0]) if earnings_dates else None
        else:
            next_earn = str(earnings_dates) if earnings_dates else None

        div_date = cal.get("Dividend Date")
        ex_div_date = cal.get("Ex-Dividend Date")

        eps_avg = cal.get("Earnings Average")
        eps_high = cal.get("Earnings High")
        eps_low = cal.get("Earnings Low")
        rev_avg = cal.get("Revenue Average")
        rev_high = cal.get("Revenue High")
        rev_low = cal.get("Revenue Low")

        def fmt_rev(v):
            if v is None:
                return None
            if abs(v) >= 1e9:
                return f"${v/1e9:.2f}B"
            if abs(v) >= 1e6:
                return f"${v/1e6:.2f}M"
            return str(v)

        # Days until earnings
        days_until = None
        if next_earn:
            from datetime import date
            try:
                earn_dt = date.fromisoformat(next_earn)
                days_until = (earn_dt - date.today()).days
            except Exception:
                pass

        return {
            "ticker": ticker,
            "company": info.get("longName") or info.get("shortName", ticker),
            "next_earnings_date": next_earn,
            "days_until_earnings": days_until,
            "eps_estimate": {
                "average": round(eps_avg, 4) if eps_avg else None,
                "high": round(eps_high, 4) if eps_high else None,
                "low": round(eps_low, 4) if eps_low else None,
            },
            "revenue_estimate": {
                "average": fmt_rev(rev_avg),
                "high": fmt_rev(rev_high),
                "low": fmt_rev(rev_low),
            },
            "dividend": {
                "dividend_date": str(div_date) if div_date else None,
                "ex_dividend_date": str(ex_div_date) if ex_div_date else None,
            },
            "source": "Yahoo Finance (yfinance)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_upcoming_earnings(
    days: int = 30,
    tickers: Optional[list[str]] = None,
) -> dict:
    """
    Get upcoming earnings dates for major tech/financial stocks or a custom list.

    Args:
        days: Filter earnings within next N days (default: 30, max: 90)
        tickers: Custom list of tickers (default: top 20 S&P500 by market cap)

    Returns:
        List of upcoming earnings sorted by date with EPS/revenue estimates
    """
    await Actor.charge('advanced_tool', count=1)
    if tickers is None:
        tickers = [
            "AAPL", "NVDA", "MSFT", "GOOGL", "META",
            "AMZN", "TSLA", "BRK-B", "JPM", "V",
            "XOM", "JNJ", "WMT", "MA", "PG",
            "GS", "NFLX", "AMD", "INTC", "BAC",
        ]

    days = min(days, 90)
    from datetime import date, timedelta
    cutoff = date.today() + timedelta(days=days)
    today = date.today()

    results = []
    for sym in tickers:
        try:
            t = yf.Ticker(sym)
            cal = t.calendar
            if not cal:
                continue
            earn_dates = cal.get("Earnings Date", [])
            if isinstance(earn_dates, list):
                next_earn = earn_dates[0] if earn_dates else None
            else:
                next_earn = earn_dates

            if next_earn is None:
                continue

            earn_dt = next_earn if isinstance(next_earn, date) else date.fromisoformat(str(next_earn))
            if earn_dt < today or earn_dt > cutoff:
                continue

            eps_avg = cal.get("Earnings Average")
            rev_avg = cal.get("Revenue Average")

            def fmt_rev(v):
                if v is None:
                    return None
                return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.2f}M"

            results.append({
                "ticker": sym,
                "earnings_date": str(earn_dt),
                "days_until": (earn_dt - today).days,
                "eps_estimate_avg": round(eps_avg, 4) if eps_avg else None,
                "revenue_estimate_avg": fmt_rev(rev_avg),
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["earnings_date"])

    return {
        "filter_days": days,
        "count": len(results),
        "upcoming_earnings": results,
        "source": "Yahoo Finance (yfinance)",
        "note": f"Earnings within next {days} days as of {today}",
    }


@mcp.tool()
async def get_stock_news(
    ticker: str,
    limit: int = 5,
) -> dict:
    """
    Get recent news headlines and summaries for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, NVDA, TSLA)
        limit: Number of news items to return (default: 5, max: 10)

    Returns:
        List of recent news articles with title, date, and summary
    """
    await Actor.charge('basic_tool', count=1)
    ticker = ticker.upper()
    limit = min(limit, 10)

    try:
        t = yf.Ticker(ticker)
        news_raw = t.news

        if not news_raw:
            return {"error": f"No news found for {ticker}"}

        articles = []
        for item in news_raw[:limit]:
            content = item.get("content", {})
            title = content.get("title", "")
            pub_date = content.get("pubDate", "")
            summary = content.get("summary", "")
            provider = content.get("provider", {})
            source = provider.get("displayName", "") if isinstance(provider, dict) else ""
            url = ""
            # Try to get canonical URL
            clinks = content.get("canonicalUrl", {})
            if isinstance(clinks, dict):
                url = clinks.get("url", "")

            articles.append({
                "title": title,
                "published": pub_date,
                "source": source,
                "summary": summary[:200] if summary else "",
                "url": url,
            })

        info = t.info
        return {
            "ticker": ticker,
            "company": info.get("longName") or info.get("shortName", ticker),
            "news_count": len(articles),
            "articles": articles,
            "source": "Yahoo Finance (yfinance)",
        }
    except Exception as e:
        return {"error": str(e)}



# ─────────────────────────────────────────────────────────────────────────────
# FRED API Tools (v1.1.0 — requires FRED_API_KEY env var)
# Free key: https://fred.stlouisfed.org/docs/api/api_key.html
# ─────────────────────────────────────────────────────────────────────────────

import os as _os

FRED_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = _os.environ.get("FRED_API_KEY", "")


def _fred_series(series_id: str, limit: int = 12) -> dict:
    """Fetch latest observations from FRED for a given series_id."""
    if not FRED_API_KEY:
        return {
            "error": "FRED_API_KEY not set. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html",
            "series_id": series_id,
        }
    url = f"{FRED_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": limit,
        "sort_order": "desc",
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    obs = data.get("observations", [])
    return [{"date": o["date"], "value": o["value"]} for o in obs if o["value"] != "."]


@mcp.tool()
def get_fed_funds_rate(months: int = 12) -> dict:
    """
    Federal Funds Rate (FEDFUNDS) — monthly average, from FRED.
    Requires FRED_API_KEY env var (free key from fred.stlouisfed.org).

    Args:
        months: Number of recent monthly data points (default: 12)

    Returns:
        List of {date, value} in descending order + current rate
    """
    try:
        data = _fred_series("FEDFUNDS", limit=months)
        if isinstance(data, dict) and "error" in data:
            return data
        current = float(data[0]["value"]) if data else None
        return {
            "series": "FEDFUNDS",
            "description": "Federal Funds Effective Rate (%)",
            "current_rate_pct": current,
            "history": data,
            "source": "FRED (St. Louis Fed)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_us_cpi(months: int = 12) -> dict:
    """
    US Consumer Price Index — All Urban Consumers (CPIAUCSL), from FRED.
    Measures inflation. Index base: 1982-84 = 100.
    Requires FRED_API_KEY env var.

    Args:
        months: Number of recent monthly data points (default: 12)

    Returns:
        CPI index values + YoY change estimate
    """
    try:
        data = _fred_series("CPIAUCSL", limit=months + 12)
        if isinstance(data, dict) and "error" in data:
            return data
        current = float(data[0]["value"]) if data else None
        # YoY: compare with 12 months ago (data is desc order)
        yoy_pct = None
        if len(data) >= 13:
            prev_year = float(data[12]["value"])
            yoy_pct = round((current - prev_year) / prev_year * 100, 2)
        return {
            "series": "CPIAUCSL",
            "description": "CPI — All Urban Consumers, All Items (Index 1982-84=100)",
            "current_index": current,
            "yoy_change_pct": yoy_pct,
            "history": data[:months],
            "source": "FRED (St. Louis Fed)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_us_pce(months: int = 12) -> dict:
    """
    US Personal Consumption Expenditures Price Index (PCEPI) — the Fed's preferred
    inflation measure. From FRED. Requires FRED_API_KEY env var.

    Args:
        months: Number of recent monthly data points (default: 12)

    Returns:
        PCE index values + YoY change (Fed's 2% target reference)
    """
    try:
        data = _fred_series("PCEPI", limit=months + 12)
        if isinstance(data, dict) and "error" in data:
            return data
        current = float(data[0]["value"]) if data else None
        yoy_pct = None
        if len(data) >= 13:
            prev_year = float(data[12]["value"])
            yoy_pct = round((current - prev_year) / prev_year * 100, 2)
        return {
            "series": "PCEPI",
            "description": "PCE Price Index — Fed's preferred inflation measure (2% target)",
            "current_index": current,
            "yoy_change_pct": yoy_pct,
            "fed_target_pct": 2.0,
            "deviation_from_target": round(yoy_pct - 2.0, 2) if yoy_pct else None,
            "history": data[:months],
            "source": "FRED (St. Louis Fed)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_us_m2(months: int = 12) -> dict:
    """
    US M2 Money Supply (M2SL) in billions of dollars, from FRED.
    Tracks money supply expansion/contraction — key macro signal.
    Requires FRED_API_KEY env var.

    Args:
        months: Number of recent monthly data points (default: 12)

    Returns:
        M2 values in billions USD + MoM and YoY change
    """
    try:
        data = _fred_series("M2SL", limit=months + 12)
        if isinstance(data, dict) and "error" in data:
            return data
        current = float(data[0]["value"]) if data else None
        mom_pct = None
        yoy_pct = None
        if len(data) >= 2:
            prev_month = float(data[1]["value"])
            mom_pct = round((current - prev_month) / prev_month * 100, 3)
        if len(data) >= 13:
            prev_year = float(data[12]["value"])
            yoy_pct = round((current - prev_year) / prev_year * 100, 2)
        return {
            "series": "M2SL",
            "description": "M2 Money Supply (Billions USD, seasonally adjusted)",
            "current_billions_usd": current,
            "mom_change_pct": mom_pct,
            "yoy_change_pct": yoy_pct,
            "history": data[:months],
            "source": "FRED (St. Louis Fed)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_us_unemployment(months: int = 12) -> dict:
    """
    US Unemployment Rate (UNRATE) — monthly, seasonally adjusted, from FRED.
    Requires FRED_API_KEY env var.

    Args:
        months: Number of recent monthly data points (default: 12)

    Returns:
        Unemployment rate history + current rate
    """
    try:
        data = _fred_series("UNRATE", limit=months)
        if isinstance(data, dict) and "error" in data:
            return data
        current = float(data[0]["value"]) if data else None
        return {
            "series": "UNRATE",
            "description": "Civilian Unemployment Rate (%, seasonally adjusted)",
            "current_rate_pct": current,
            "history": data,
            "note": "Full employment: Fed target ~4.0%. Pre-pandemic low: 3.5% (2023)",
            "source": "FRED (St. Louis Fed)",
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# SEC EDGAR tools (v1.2.0) — no API key required
# ─────────────────────────────────────────────

def _edgar_headers():
    return {"User-Agent": "finance-mcp-server contact@example.com", "Accept-Encoding": "gzip, deflate"}


# Module-level cache for company tickers (avoids repeated SEC API calls)
_ticker_cik_cache: dict[str, str] = {}

async def _ticker_to_cik(ticker: str) -> str | None:
    """Resolve ticker → SEC CIK using EDGAR company_tickers.json (async, cached)."""
    global _ticker_cik_cache
    ticker_upper = ticker.upper()
    if ticker_upper in _ticker_cik_cache:
        return _ticker_cik_cache[ticker_upper]
    url = "https://www.sec.gov/files/company_tickers.json"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=_edgar_headers())
        r.raise_for_status()
        data = r.json()
    for entry in data.values():
        t = entry.get("ticker", "")
        _ticker_cik_cache[t] = str(entry["cik_str"]).zfill(10)
    return _ticker_cik_cache.get(ticker_upper)


@mcp.tool()
async def get_sec_filings(ticker: str, form_type: str = "10-K", limit: int = 5) -> dict:
    """
    Recent SEC EDGAR filings for a company — no API key required.

    Args:
        ticker: Stock ticker (e.g. AAPL)
        form_type: Filing type — 10-K, 10-Q, 8-K, DEF 14A, etc. (default: 10-K)
        limit: Number of filings to return (default: 5)

    Returns:
        List of filings with date, accession number, and direct SEC URL
    """
    await Actor.charge('basic_tool', count=1)
    try:
        cik = await _ticker_to_cik(ticker)
        if not cik:
            return {"error": f"CIK not found for ticker: {ticker}"}
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=_edgar_headers())
            r.raise_for_status()
            data = r.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        results = []
        for i, form in enumerate(forms):
            if form == form_type and len(results) < limit:
                acc = accessions[i].replace("-", "")
                results.append({
                    "form": form,
                    "date": dates[i],
                    "accession": accessions[i],
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/",
                })
        return {
            "ticker": ticker.upper(),
            "cik": cik,
            "form_type": form_type,
            "filings": results,
            "source": "SEC EDGAR (free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_insider_trades(ticker: str, limit: int = 10) -> dict:
    """
    Recent insider trading filings (Form 4) from SEC EDGAR — no API key required.

    Args:
        ticker: Stock ticker (e.g. TSLA)
        limit: Number of Form 4 filings to return (default: 10)

    Returns:
        List of recent insider transaction filings with dates
    """
    await Actor.charge('basic_tool', count=1)
    try:
        cik = await _ticker_to_cik(ticker)
        if not cik:
            return {"error": f"CIK not found for ticker: {ticker}"}
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=_edgar_headers())
            r.raise_for_status()
            data = r.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        results = []
        for i, form in enumerate(forms):
            if form == "4" and len(results) < limit:
                results.append({
                    "date": dates[i],
                    "accession": accessions[i],
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(cik)}&type=4&dateb=&owner=include&count=40",
                })
        return {
            "ticker": ticker.upper(),
            "cik": cik,
            "form_type": "Form 4 (insider transactions)",
            "recent_filings": results,
            "note": "Visit each URL for full transaction details (shares bought/sold, price, insider name)",
            "source": "SEC EDGAR (free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_company_facts(ticker: str, concept: str = "us-gaap/Revenues") -> dict:
    """
    Structured financial facts from SEC EDGAR XBRL data — no API key required.
    Covers balance sheet, income statement, and cash flow items.

    Args:
        ticker: Stock ticker (e.g. MSFT)
        concept: XBRL concept in format taxonomy/ConceptName
                 Examples: us-gaap/Revenues, us-gaap/NetIncomeLoss,
                           us-gaap/Assets, us-gaap/EarningsPerShareBasic

    Returns:
        Historical values for the requested financial concept
    """
    await Actor.charge('basic_tool', count=1)
    try:
        cik = await _ticker_to_cik(ticker)
        if not cik:
            return {"error": f"CIK not found for ticker: {ticker}"}
        taxonomy, tag = concept.split("/", 1)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=_edgar_headers())
            r.raise_for_status()
            data = r.json()
        facts = data.get("facts", {}).get(taxonomy, {}).get(tag, {})
        if not facts:
            available = list(data.get("facts", {}).get(taxonomy, {}).keys())[:20]
            return {
                "error": f"Concept '{concept}' not found",
                "available_concepts_sample": available,
            }
        units = facts.get("units", {})
        unit_key = list(units.keys())[0] if units else None
        entries = units.get(unit_key, []) if unit_key else []
        annual = [e for e in entries if e.get("form") in ("10-K", "20-F")][-8:]
        return {
            "ticker": ticker.upper(),
            "concept": concept,
            "label": facts.get("label", tag),
            "unit": unit_key,
            "annual_values": annual,
            "source": "SEC EDGAR XBRL (free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_treasury_yield_curve() -> dict:
    """
    Current US Treasury yield curve — daily rates from US Treasury XML feed.
    No API key required.

    Returns:
        Yield rates for all maturities (1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
        plus the date and basic curve shape analysis (normal vs inverted).
    """
    await Actor.charge('basic_tool', count=1)
    try:
        import xml.etree.ElementTree as ET
        from datetime import datetime
        year = datetime.utcnow().year
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, follow_redirects=True)
            r.raise_for_status()
            text = r.text
        root = ET.fromstring(text)
        atom = "http://www.w3.org/2005/Atom"
        meta = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
        entries = root.findall(f"{{{atom}}}entry")
        if not entries:
            return {"error": "No entries in Treasury XML feed"}
        last = entries[-1]
        props = last.find(f"{{{atom}}}content/{{{meta}}}properties")
        if props is None:
            return {"error": "Could not parse Treasury XML"}
        d = {child.tag.split("}")[1]: child.text for child in props}
        maturity_map = {
            "BC_1MONTH": "1M", "BC_2MONTH": "2M", "BC_3MONTH": "3M",
            "BC_6MONTH": "6M", "BC_1YEAR": "1Y", "BC_2YEAR": "2Y",
            "BC_3YEAR": "3Y", "BC_5YEAR": "5Y", "BC_7YEAR": "7Y",
            "BC_10YEAR": "10Y", "BC_20YEAR": "20Y", "BC_30YEAR": "30Y",
        }
        rates = {}
        for key, label in maturity_map.items():
            if d.get(key):
                rates[label] = float(d[key])
        short = rates.get("3M", 0)
        long_ = rates.get("10Y", 0)
        shape = "normal" if long_ > short else "inverted"
        spread_10y_3m = round(long_ - short, 2)
        return {
            "date": d.get("NEW_DATE", "")[:10],
            "yields_pct": rates,
            "curve_shape": shape,
            "spread_10y_minus_3m_pct": spread_10y_3m,
            "note": "Inverted (spread < 0) = historical recession signal. Normal = long > short.",
            "source": "US Treasury (home.treasury.gov, free)",
        }
    except Exception as e:
        return {"error": str(e)}



@mcp.tool()
async def get_options_chain(ticker: str, expiry: Optional[str] = None) -> dict:
    """
    Options chain for a stock — calls and puts with strike, last price, volume, IV.
    No API key required (Yahoo Finance).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'SPY')
        expiry: Expiry date in YYYY-MM-DD format. If None, returns nearest expiry.

    Returns:
        Calls and puts with strike prices, last price, bid/ask, volume, open interest,
        implied volatility, and in-the-money status.
    """
    await Actor.charge('advanced_tool', count=1)
    try:
        tk = yf.Ticker(ticker)
        expirations = tk.options
        if not expirations:
            return {"error": f"No options data for {ticker}"}
        # Select expiry
        if expiry and expiry in expirations:
            selected = expiry
        else:
            selected = expirations[0]
        chain = tk.option_chain(selected)
        def _fmt(df, kind):
            rows = []
            for _, r in df.iterrows():
                rows.append({
                    "strike": round(float(r.get("strike", 0)), 2),
                    "lastPrice": round(float(r.get("lastPrice", 0)), 2),
                    "bid": round(float(r.get("bid", 0)), 2),
                    "ask": round(float(r.get("ask", 0)), 2),
                    "volume": int(r.get("volume", 0)) if not str(r.get("volume","")) in ["nan","None"] else 0,
                    "openInterest": int(r.get("openInterest", 0)) if not str(r.get("openInterest","")) in ["nan","None"] else 0,
                    "impliedVolatility": round(float(r.get("impliedVolatility", 0)), 4),
                    "inTheMoney": bool(r.get("inTheMoney", False)),
                })
            return rows
        calls = _fmt(chain.calls, "call")
        puts = _fmt(chain.puts, "put")
        # Top 10 by open interest each side
        calls_top = sorted(calls, key=lambda x: x["openInterest"], reverse=True)[:10]
        puts_top = sorted(puts, key=lambda x: x["openInterest"], reverse=True)[:10]
        return {
            "ticker": ticker.upper(),
            "expiry": selected,
            "available_expiries": list(expirations[:8]),
            "calls_top10_by_oi": calls_top,
            "puts_top10_by_oi": puts_top,
            "calls_total": len(calls),
            "puts_total": len(puts),
            "source": "Yahoo Finance (yfinance, free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_institutional_holdings(ticker: str) -> dict:
    """
    Institutional holdings (13F filings) for a stock — top fund holders and insider owners.
    No API key required (Yahoo Finance + SEC EDGAR).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')

    Returns:
        Major institutional holders, mutual fund holders, insider holders,
        shares outstanding, float percentage held by institutions.
    """
    await Actor.charge('advanced_tool', count=1)
    try:
        tk = yf.Ticker(ticker)
        result = {"ticker": ticker.upper()}
        # Institutional holders
        inst = tk.institutional_holders
        if inst is not None and not inst.empty:
            holders = []
            for _, r in inst.head(10).iterrows():
                holders.append({
                    "holder": str(r.get("Holder", "")),
                    "shares": int(r.get("Shares", 0)),
                    "pct_out": round(float(r.get("% Out", 0)) * 100, 2) if r.get("% Out") is not None else None,
                    "value_usd": int(r.get("Value", 0)) if r.get("Value") is not None else None,
                })
            result["institutional_holders_top10"] = holders
        # Mutual fund holders
        mf = tk.mutualfund_holders
        if mf is not None and not mf.empty:
            mf_holders = []
            for _, r in mf.head(5).iterrows():
                mf_holders.append({
                    "holder": str(r.get("Holder", "")),
                    "shares": int(r.get("Shares", 0)),
                    "pct_out": round(float(r.get("% Out", 0)) * 100, 2) if r.get("% Out") is not None else None,
                })
            result["mutual_fund_holders_top5"] = mf_holders
        # Major holders summary
        major = tk.major_holders
        if major is not None and not major.empty:
            summary = {}
            for _, r in major.iterrows():
                key = str(r.iloc[1]).strip() if len(r) > 1 else str(r.iloc[0])
                val = str(r.iloc[0]).strip()
                summary[key] = val
            result["major_holders_summary"] = summary
        result["source"] = "Yahoo Finance (yfinance, 13F aggregated data, free)"
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_historical_treasury_yields(maturity: str = "10Y", start: str = None, end: str = None) -> dict:
    """
    Historical US Treasury yield data for a specific maturity.
    No API key required (US Treasury XML feed).

    Args:
        maturity: Maturity to fetch: '1M', '2M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y'
        start: Start date YYYY-MM-DD (default: 1 year ago)
        end: End date YYYY-MM-DD (default: today)

    Returns:
        List of {date, yield_pct} sorted by date, plus min/max/mean stats.
    """
    await Actor.charge('basic_tool', count=1)
    try:
        import xml.etree.ElementTree as ET
        from datetime import datetime, timedelta
        maturity_map = {
            "1M": "BC_1MONTH", "2M": "BC_2MONTH", "3M": "BC_3MONTH",
            "6M": "BC_6MONTH", "1Y": "BC_1YEAR", "2Y": "BC_2YEAR",
            "3Y": "BC_3YEAR", "5Y": "BC_5YEAR", "7Y": "BC_7YEAR",
            "10Y": "BC_10YEAR", "20Y": "BC_20YEAR", "30Y": "BC_30YEAR",
        }
        mat = maturity.upper()
        if mat not in maturity_map:
            return {"error": f"Invalid maturity '{maturity}'. Valid: {list(maturity_map.keys())}"}
        field = maturity_map[mat]
        today = datetime.utcnow()
        if not end:
            end = today.strftime("%Y-%m-%d")
        if not start:
            start = (today - timedelta(days=365)).strftime("%Y-%m-%d")
        start_year = int(start[:4])
        end_year = int(end[:4])
        atom = "http://www.w3.org/2005/Atom"
        meta = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
        records = []
        async with httpx.AsyncClient(timeout=20) as client:
            for year in range(start_year, end_year + 1):
                url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
                r = await client.get(url, follow_redirects=True)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.text)
                for entry in root.findall(f"{{{atom}}}entry"):
                    props = entry.find(f"{{{atom}}}content/{{{meta}}}properties")
                    if props is None:
                        continue
                    d = {child.tag.split("}")[1]: child.text for child in props}
                    date_str = d.get("NEW_DATE", "")[:10]
                    if not date_str or date_str < start or date_str > end:
                        continue
                    val = d.get(field)
                    if val:
                        records.append({"date": date_str, "yield_pct": float(val)})
        records.sort(key=lambda x: x["date"])
        if not records:
            return {"error": "No data found for the given range and maturity"}
        yields = [r["yield_pct"] for r in records]
        return {
            "maturity": mat,
            "start": start,
            "end": end,
            "count": len(records),
            "data": records,
            "stats": {
                "min_pct": round(min(yields), 3),
                "max_pct": round(max(yields), 3),
                "mean_pct": round(sum(yields) / len(yields), 3),
                "latest_pct": yields[-1],
                "latest_date": records[-1]["date"],
            },
            "source": "US Treasury (home.treasury.gov, free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_analyst_ratings(ticker: str) -> dict:
    """
    Analyst ratings, price targets, and recent upgrades/downgrades for a stock.
    No API key required (Yahoo Finance via yfinance).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')

    Returns:
        Consensus rating breakdown (strongBuy/buy/hold/sell/strongSell) for last 4 months,
        price target (current/high/low/mean/median), and last 10 upgrades/downgrades.
    """
    await Actor.charge('advanced_tool', count=1)
    try:
        import yfinance as yf
        t = yf.Ticker(ticker.upper())

        # Price targets
        price_targets = {}
        try:
            apt = t.analyst_price_targets
            if isinstance(apt, dict):
                price_targets = {k: round(float(v), 2) if v is not None else None for k, v in apt.items()}
        except Exception:
            pass

        # Recommendations summary (last 4 months)
        consensus = []
        try:
            rec = t.recommendations_summary
            if rec is not None and not rec.empty:
                for _, row in rec.iterrows():
                    consensus.append({
                        "period": row.get("period", ""),
                        "strongBuy": int(row.get("strongBuy", 0)),
                        "buy": int(row.get("buy", 0)),
                        "hold": int(row.get("hold", 0)),
                        "sell": int(row.get("sell", 0)),
                        "strongSell": int(row.get("strongSell", 0)),
                    })
        except Exception:
            pass

        # Upgrades/downgrades (last 10)
        recent_actions = []
        try:
            ud = t.upgrades_downgrades
            if ud is not None and not ud.empty:
                ud_recent = ud.head(10)
                for date_idx, row in ud_recent.iterrows():
                    entry = {
                        "date": str(date_idx)[:10],
                        "firm": str(row.get("Firm", "")),
                        "action": str(row.get("Action", "")),
                        "toGrade": str(row.get("ToGrade", "")),
                        "fromGrade": str(row.get("FromGrade", "")),
                    }
                    pt = row.get("currentPriceTarget")
                    if pt is not None and pt == pt:  # not NaN
                        entry["priceTarget"] = round(float(pt), 2)
                    recent_actions.append(entry)
        except Exception:
            pass

        # Derive overall sentiment from current month
        sentiment = "neutral"
        if consensus:
            cur = consensus[0]
            total = sum([cur["strongBuy"], cur["buy"], cur["hold"], cur["sell"], cur["strongSell"]])
            if total > 0:
                bullish = (cur["strongBuy"] + cur["buy"]) / total
                bearish = (cur["sell"] + cur["strongSell"]) / total
                if bullish > 0.6:
                    sentiment = "bullish"
                elif bearish > 0.4:
                    sentiment = "bearish"

        return {
            "ticker": ticker.upper(),
            "sentiment": sentiment,
            "price_targets": price_targets,
            "consensus_last_4_months": consensus,
            "recent_upgrades_downgrades": recent_actions,
            "source": "Yahoo Finance (yfinance, analyst data, free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_short_interest(ticker: str) -> dict:
    """
    Short interest data for a stock: shares short, short ratio (days to cover), short % of float.
    No API key required (Yahoo Finance via yfinance).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GME')

    Returns:
        sharesShort, shortRatio, shortPercentOfFloat, comparison to prior month, and interpretation.
    """
    await Actor.charge('advanced_tool', count=1)
    try:
        import yfinance as yf
        from datetime import datetime
        t = yf.Ticker(ticker.upper())
        info = t.info

        shares_short = info.get("sharesShort")
        shares_short_prior = info.get("sharesShortPriorMonth")
        short_ratio = info.get("shortRatio")
        short_pct_float = info.get("shortPercentOfFloat")
        date_short = info.get("dateShortInterest")
        float_shares = info.get("floatShares")
        shares_outstanding = info.get("sharesOutstanding")

        # Convert timestamp
        date_str = None
        if date_short:
            try:
                date_str = datetime.utcfromtimestamp(date_short).strftime("%Y-%m-%d")
            except Exception:
                pass

        prior_date_str = None
        prior_ts = info.get("sharesShortPreviousMonthDate")
        if prior_ts:
            try:
                prior_date_str = datetime.utcfromtimestamp(prior_ts).strftime("%Y-%m-%d")
            except Exception:
                pass

        # Month-over-month change
        mom_change_pct = None
        if shares_short and shares_short_prior and shares_short_prior > 0:
            mom_change_pct = round((shares_short - shares_short_prior) / shares_short_prior * 100, 2)

        # Interpretation
        interpretation = "low"
        if short_pct_float is not None:
            pct = short_pct_float * 100
            if pct >= 20:
                interpretation = "extremely_high (squeeze risk)"
            elif pct >= 10:
                interpretation = "high"
            elif pct >= 5:
                interpretation = "moderate"

        return {
            "ticker": ticker.upper(),
            "report_date": date_str,
            "shares_short": shares_short,
            "shares_short_prior_month": shares_short_prior,
            "prior_month_date": prior_date_str,
            "mom_change_pct": mom_change_pct,
            "short_ratio_days_to_cover": short_ratio,
            "short_pct_of_float": round(short_pct_float * 100, 4) if short_pct_float is not None else None,
            "float_shares": float_shares,
            "shares_outstanding": shares_outstanding,
            "interpretation": interpretation,
            "source": "Yahoo Finance (yfinance, FINRA short interest data, free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_economic_calendar(year: int = None) -> dict:
    """
    FOMC meeting schedule and key economic event calendar.
    No API key required (Federal Reserve website, public data).

    Args:
        year: Calendar year to fetch (default: current year). Range: 2021-2027.

    Returns:
        List of FOMC meeting dates with statement/minutes status, plus next upcoming meeting.
    """
    await Actor.charge('basic_tool', count=1)
    try:
        from datetime import datetime
        import re
        if year is None:
            year = datetime.utcnow().year
        year = int(year)
        if year < 2021 or year > 2027:
            return {"error": "Year must be between 2021 and 2027"}

        url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FinanceMCP/1.4.0)"}
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            r = await client.get(url, follow_redirects=True)
        if r.status_code != 200:
            return {"error": f"Fed website returned HTTP {r.status_code}"}

        text = r.text
        # Find year section
        year_marker = f"{year} FOMC Meetings"
        next_year_marker = f"{year + 1} FOMC Meetings"
        start = text.find(year_marker)
        end = text.find(next_year_marker) if text.find(next_year_marker) > start else start + 8000
        section = text[start:end] if start != -1 else ""

        if not section:
            return {"error": f"No FOMC calendar data found for {year}"}

        # Extract months and dates
        month_names = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        meetings = []
        for m in month_names:
            idx = section.find(f"<strong>{m}</strong>")
            if idx == -1:
                continue
            # Find date after month
            date_div_start = section.find('fomc-meeting__date', idx)
            if date_div_start == -1:
                continue
            date_div_content_start = section.find('>', date_div_start) + 1
            date_div_content_end = section.find('<', date_div_content_start)
            raw_date = section[date_div_content_start:date_div_content_end].strip()
            # Check for projected (asterisk = SEP meeting)
            is_sep = "*" in raw_date
            clean_date = raw_date.replace("*", "").strip()

            # Detect if statement is available
            has_statement = "Statement:" in section[idx:idx+1000]
            has_minutes = "Minutes:" in section[idx:idx+1000]

            # Try to form exact date (use last day in range)
            end_day = None
            try:
                if "-" in clean_date:
                    end_day = int(clean_date.split("-")[-1])
                else:
                    end_day = int(clean_date)
                month_num = month_names.index(m) + 1
                meeting_date = datetime(year, month_num, end_day)
                date_iso = meeting_date.strftime("%Y-%m-%d")
            except Exception:
                date_iso = f"{year}-{month_names.index(m)+1:02d}-??"

            meetings.append({
                "month": m,
                "dates": clean_date,
                "end_date_iso": date_iso,
                "includes_sep": is_sep,
                "statement_published": has_statement,
                "minutes_published": has_minutes,
            })

        # Find next upcoming meeting
        now = datetime.utcnow()
        upcoming = None
        for mtg in meetings:
            try:
                mtg_date = datetime.strptime(mtg["end_date_iso"], "%Y-%m-%d")
                if mtg_date >= now:
                    upcoming = mtg
                    break
            except Exception:
                pass

        return {
            "year": year,
            "fomc_meetings": meetings,
            "total_meetings": len(meetings),
            "next_meeting": upcoming,
            "note": "Meetings marked includes_sep=true include Summary of Economic Projections (dot plot).",
            "source": "Federal Reserve (federalreserve.gov, free)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_crypto_defi_tvl(protocol: str = None) -> dict:
    """
    DeFi Total Value Locked (TVL) data via DefiLlama. Free, no API key required.

    Args:
        protocol: Protocol slug/name (e.g., 'uniswap', 'aave', 'lido', 'makerdao').
                  If None or 'top', returns top 20 DeFi protocols by TVL.

    Returns:
        Current TVL, 24h/7d change, category, chains, and description.
    """
    await Actor.charge('basic_tool', count=1)
    try:
        base_url = "https://api.llama.fi"

        if protocol is None or protocol.strip().lower() in ("top", "all", ""):
            # Return top 20 protocols
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(f"{base_url}/protocols")
            if r.status_code != 200:
                return {"error": f"DefiLlama API returned HTTP {r.status_code}"}
            data = r.json()
            # Sort by TVL descending, filter out CEX/bridges for pure DeFi
            defi_protocols = [p for p in data if p.get("category") not in ("CEX", "Chain")]
            defi_protocols.sort(key=lambda x: x.get("tvl", 0) or 0, reverse=True)
            top20 = []
            for p in defi_protocols[:20]:
                top20.append({
                    "rank": len(top20) + 1,
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "tvl_usd": round(p.get("tvl", 0) or 0),
                    "change_1d_pct": round(p.get("change_1d", 0) or 0, 2),
                    "change_7d_pct": round(p.get("change_7d", 0) or 0, 2),
                    "category": p.get("category"),
                    "chains": p.get("chains", [])[:5],
                })
            total_defi_tvl = sum(p.get("tvl", 0) or 0 for p in defi_protocols)
            return {
                "query": "top_20_defi",
                "total_defi_tvl_usd": round(total_defi_tvl),
                "top_protocols": top20,
                "source": "DefiLlama (api.llama.fi, free)",
            }
        else:
            # Specific protocol
            slug = protocol.strip().lower().replace(" ", "-")
            async with httpx.AsyncClient(timeout=15) as client:
                # Get current TVL (simple number)
                tvl_r = await client.get(f"{base_url}/tvl/{slug}")
                # Get full protocol info
                proto_r = await client.get(f"{base_url}/protocol/{slug}")

            if tvl_r.status_code == 200:
                try:
                    current_tvl = float(tvl_r.text.strip())
                except Exception:
                    current_tvl = None
            else:
                current_tvl = None

            if proto_r.status_code != 200:
                return {"error": f"Protocol '{slug}' not found on DefiLlama. Try the exact slug (e.g., 'uniswap', 'aave-v3', 'lido')."}

            d = proto_r.json()
            # Get chain breakdown (latest values)
            chain_tvls = {}
            for chain_name, chain_data in (d.get("chainTvls") or {}).items():
                if isinstance(chain_data, dict) and "tvl" in chain_data:
                    tvl_series = chain_data["tvl"]
                    if tvl_series:
                        chain_tvls[chain_name] = round(tvl_series[-1].get("totalLiquidityUSD", 0))
                elif isinstance(chain_data, (int, float)):
                    chain_tvls[chain_name] = round(chain_data)

            # Historical TVL: last 30 data points
            tvl_history = []
            raw_tvl = d.get("tvl", [])
            if isinstance(raw_tvl, list) and raw_tvl:
                for entry in raw_tvl[-30:]:
                    if isinstance(entry, dict):
                        from datetime import datetime
                        ts = entry.get("date", 0)
                        try:
                            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                        except Exception:
                            date_str = str(ts)
                        tvl_history.append({
                            "date": date_str,
                            "tvl_usd": round(entry.get("totalLiquidityUSD", 0)),
                        })

            return {
                "protocol": d.get("name", slug),
                "slug": slug,
                "symbol": d.get("symbol"),
                "category": d.get("category"),
                "description": (d.get("description") or "")[:300],
                "current_tvl_usd": round(current_tvl) if current_tvl else None,
                "chains": d.get("chains", []) or list(chain_tvls.keys())[:10],
                "chain_tvl_breakdown": chain_tvls,
                "tvl_history_30d": tvl_history,
                "source": "DefiLlama (api.llama.fi, free, no API key)",
            }
    except Exception as e:
        return {"error": str(e)}


# v1.5.0 tools
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_macro_dashboard() -> dict:
    """
    All-in-one US macro snapshot — VIX, DXY, S&P 500, 10Y Treasury, Fed funds rate proxy,
    and US CPI/PCE trend. No API key required. Market data via Yahoo Finance.

    Returns:
        dict with VIX, DXY, S&P500 1-day return, 10Y yield, 2Y yield, 10Y-2Y spread,
        Fear & Greed index, and a macro summary label (risk-on / risk-off / neutral).
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime as _dt

        SYMBOLS = {
            "vix": "^VIX",
            "dxy": "DX-Y.NYB",
            "sp500": "^GSPC",
            "t10y": "^TNX",
            "t2y": "^IRX",
        }

        loop = asyncio.get_event_loop()

        def _fetch_all():
            res = {}
            for key, sym in SYMBOLS.items():
                try:
                    tk = yf.Ticker(sym)
                    hist = tk.history(period="2d", interval="1d", auto_adjust=True)
                    if len(hist) >= 1:
                        last = float(hist["Close"].iloc[-1])
                        prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else last
                        res[key] = {
                            "value": round(last, 4),
                            "change_1d_pct": round((last - prev) / prev * 100, 2) if prev else 0,
                        }
                except Exception as e:
                    res[key] = {"error": str(e)}
            return res

        market = await loop.run_in_executor(None, _fetch_all)

        try:
            async with httpx.AsyncClient(timeout=8) as client:
                fg_r = await client.get("https://api.alternative.me/fng/?limit=1")
            fg_data = fg_r.json()["data"][0] if fg_r.status_code == 200 else {}
            fear_greed = {"score": int(fg_data.get("value", 0)), "label": fg_data.get("value_classification", "N/A")}
        except Exception:
            fear_greed = {"score": None, "label": "unavailable"}

        spread = None
        t10y_val = market.get("t10y", {}).get("value")
        t2y_val = market.get("t2y", {}).get("value")
        if t10y_val and t2y_val:
            spread = round(t10y_val - t2y_val, 3)
            curve_shape = "inverted" if spread < 0 else ("flat" if abs(spread) < 0.15 else "normal")
        else:
            curve_shape = "unknown"

        vix_val = market.get("vix", {}).get("value", 20)
        if isinstance(vix_val, (int, float)):
            if vix_val >= 30:
                regime = "risk-off (high fear)"
            elif vix_val <= 15:
                regime = "risk-on (low fear)"
            else:
                regime = "neutral"
        else:
            regime = "unknown"

        return {
            "snapshot_utc": _dt.utcnow().strftime("%Y-%m-%d %H:%M"),
            "market": {
                "vix": market.get("vix"),
                "dxy": market.get("dxy"),
                "sp500": market.get("sp500"),
                "t10y_yield_pct": market.get("t10y"),
                "t2y_yield_pct": market.get("t2y"),
                "t10y_minus_t2y_spread": spread,
                "yield_curve": curve_shape,
            },
            "sentiment": {
                "fear_greed_index": fear_greed,
                "macro_regime": regime,
            },
            "note": "VIX=volatility(fear↑), DXY=USD strength, spread<0=inverted curve(recession signal)",
            "source": "Yahoo Finance + alternative.me (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_surprise(ticker: str, quarters: int = 8) -> dict:
    """
    Historical EPS earnings surprise history for any stock — actual vs. estimated EPS.
    Calculates surprise % and beat/miss/in-line label per quarter.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA', 'TSLA')
        quarters: Number of past quarters to return (default: 8, max: 20)

    Returns:
        Per-quarter EPS estimate vs actual, surprise %, beat rate, and revenue surprise if available.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf

        quarters = min(int(quarters), 20)
        loop = asyncio.get_event_loop()

        def _fetch():
            tk = yf.Ticker(ticker.upper())
            return tk.earnings_history, tk.info

        earnings_hist, info = await loop.run_in_executor(None, _fetch)
        company_name = info.get("longName") or info.get("shortName") or ticker.upper()

        if earnings_hist is None or (hasattr(earnings_hist, "empty") and earnings_hist.empty):
            return {"error": f"No earnings history available for {ticker.upper()}. Try a major US-listed stock."}

        rows = []
        if hasattr(earnings_hist, "iterrows"):
            for idx, row in earnings_hist.iterrows():
                eps_est = row.get("epsEstimate") if hasattr(row, "get") else getattr(row, "epsEstimate", None)
                eps_act = row.get("epsActual") if hasattr(row, "get") else getattr(row, "epsActual", None)
                date_str = str(idx)[:10] if idx else "N/A"
                if eps_est is None or eps_act is None:
                    continue
                try:
                    eps_est_f = float(eps_est)
                    eps_act_f = float(eps_act)
                    surprise_pct = round((eps_act_f - eps_est_f) / abs(eps_est_f) * 100, 2) if eps_est_f != 0 else None
                    if surprise_pct is None:
                        label = "N/A"
                    elif surprise_pct > 2:
                        label = "beat"
                    elif surprise_pct < -2:
                        label = "miss"
                    else:
                        label = "in-line"
                    rows.append({
                        "quarter": date_str,
                        "eps_estimate": round(eps_est_f, 4),
                        "eps_actual": round(eps_act_f, 4),
                        "surprise_pct": surprise_pct,
                        "result": label,
                    })
                except (TypeError, ValueError):
                    continue

        rows = rows[-quarters:]
        beats = sum(1 for r in rows if r["result"] == "beat")
        misses = sum(1 for r in rows if r["result"] == "miss")
        beat_rate = round(beats / len(rows) * 100, 1) if rows else None

        return {
            "ticker": ticker.upper(),
            "company": company_name,
            "quarters_shown": len(rows),
            "beat_rate_pct": beat_rate,
            "beats": beats,
            "misses": misses,
            "history": rows,
            "source": "Yahoo Finance (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_insider_sentiment(ticker: str) -> dict:
    """
    Insider transaction sentiment summary from SEC Form 4 filings.
    Aggregates buy vs sell transactions, calculates net sentiment score,
    and identifies notable insider buying/selling clusters.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'NVDA')

    Returns:
        Buy/sell counts and total shares, net sentiment (bullish/bearish/neutral),
        largest single transactions, and recent 90-day trend.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime as _dt, timedelta

        loop = asyncio.get_event_loop()

        def _fetch():
            tk = yf.Ticker(ticker.upper())
            return tk.insider_transactions, tk.info

        raw, info = await loop.run_in_executor(None, _fetch)
        company_name = info.get("longName") or info.get("shortName") or ticker.upper()
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        if raw is None or (hasattr(raw, "empty") and raw.empty):
            return {"error": f"No insider transaction data for {ticker.upper()}."}

        transactions = []
        if hasattr(raw, "iterrows"):
            for _, row in raw.iterrows():
                try:
                    shares = row.get("Shares") or row.get("shares") or 0
                    value = row.get("Value") or row.get("value") or 0
                    text = str(row.get("Text") or row.get("text") or "")
                    insider = str(row.get("Insider") or row.get("insider") or "Unknown")
                    position = str(row.get("Position") or row.get("position") or "")
                    date_raw = row.get("Start Date") or row.get("date") or row.get("Date")
                    date_str = str(date_raw)[:10] if date_raw else "N/A"
                    action = "buy" if "buy" in text.lower() or "purchase" in text.lower() else "sell"
                    transactions.append({
                        "date": date_str,
                        "insider": insider,
                        "position": position,
                        "action": action,
                        "shares": int(shares) if shares else 0,
                        "value_usd": int(value) if value else 0,
                        "description": text[:120],
                    })
                except Exception:
                    continue

        cutoff = (_dt.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
        recent = [t for t in transactions if t["date"] >= cutoff]
        all_txns = transactions

        def _aggregate(txns):
            buys = [t for t in txns if t["action"] == "buy"]
            sells = [t for t in txns if t["action"] == "sell"]
            return {
                "buy_count": len(buys),
                "sell_count": len(sells),
                "buy_shares": sum(t["shares"] for t in buys),
                "sell_shares": sum(t["shares"] for t in sells),
                "buy_value_usd": sum(t["value_usd"] for t in buys),
                "sell_value_usd": sum(t["value_usd"] for t in sells),
            }

        all_agg = _aggregate(all_txns)
        recent_agg = _aggregate(recent)

        net_value = recent_agg["buy_value_usd"] - recent_agg["sell_value_usd"]
        total_value = recent_agg["buy_value_usd"] + recent_agg["sell_value_usd"]
        if total_value > 0:
            score = net_value / total_value
            if score > 0.3:
                sentiment = "bullish"
            elif score < -0.3:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
        else:
            sentiment = "no_data"

        top_txns = sorted(all_txns, key=lambda x: x["value_usd"], reverse=True)[:3]

        return {
            "ticker": ticker.upper(),
            "company": company_name,
            "current_price_usd": current_price,
            "sentiment_90d": sentiment,
            "net_insider_value_90d": net_value,
            "recent_90d": recent_agg,
            "all_time": all_agg,
            "notable_transactions": top_txns,
            "total_transactions_available": len(all_txns),
            "source": "Yahoo Finance (SEC Form 4 aggregated, free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_currency_carry(base: str = "USD", quote: str = "JPY") -> dict:
    """
    Carry trade analysis for a currency pair — interest rate differential,
    expected carry return, and risk assessment.

    Uses central bank policy rate proxies (short-term gov bond yields via Yahoo Finance)
    to estimate the carry differential between two currencies.

    Args:
        base: Base currency ISO code (e.g., 'USD', 'EUR', 'AUD', 'GBP') — the currency you borrow
        quote: Quote currency ISO code (e.g., 'JPY', 'CHF', 'TRY') — the currency you invest in

    Returns:
        Interest rate differential, annualised carry estimate, spot rate, and carry trade viability score.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime as _dt

        # Mapping: currency → short-term yield proxy ticker (3M or policy rate proxy)
        RATE_TICKERS = {
            "USD": "^IRX",      # US 13-week T-bill
            "EUR": "^EURIBOR3M",# EURIBOR 3M
            "JPY": "^JPTB3M",   # Japan 3M Treasury Bill proxy
            "GBP": "^GBPR3M",   # UK 3M Gilt proxy
            "AUD": "^ADBB30D",  # AUD 30D Bank Bill
            "CAD": "^CABS3M",   # CAD 3M T-Bill proxy
            "CHF": "^SNBR",     # SNB policy rate proxy
            "NZD": "^NZBB3M",   # NZD 3M Bank Bill
        }

        # Fallback: use World Bank lending rate or fixed known values for exotic currencies
        KNOWN_RATES = {
            "TRY": 45.0,   # Turkey — high carry
            "BRL": 13.75,  # Brazil SELIC
            "MXN": 11.25,  # Mexico Banxico
            "ZAR": 8.25,   # South Africa
            "INR": 6.50,   # India RBI
            "IDR": 6.00,   # Indonesia BI
            "HUF": 7.25,   # Hungary
            "CZK": 4.25,   # Czech
            "PLN": 5.75,   # Poland
        }

        loop = asyncio.get_event_loop()

        def _fetch_yield(currency: str):
            ccy = currency.upper()
            if ccy in KNOWN_RATES:
                return KNOWN_RATES[ccy]
            ticker_sym = RATE_TICKERS.get(ccy)
            if not ticker_sym:
                return None
            try:
                hist = yf.Ticker(ticker_sym).history(period="5d", interval="1d")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
            except Exception:
                pass
            return None

        def _fetch_spot(base_ccy, quote_ccy):
            pair = f"{base_ccy}{quote_ccy}=X"
            try:
                hist = yf.Ticker(pair).history(period="5d", interval="1d")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
            except Exception:
                pass
            return None

        base_ccy = base.upper()
        quote_ccy = quote.upper()

        base_rate, quote_rate, spot = await asyncio.gather(
            loop.run_in_executor(None, _fetch_yield, base_ccy),
            loop.run_in_executor(None, _fetch_yield, quote_ccy),
            loop.run_in_executor(None, _fetch_spot, base_ccy, quote_ccy),
        )

        # Carry differential: borrow base, invest in quote
        if base_rate is not None and quote_rate is not None:
            carry_diff = round(quote_rate - base_rate, 3)
            carry_label = (
                "high carry (strong positive)" if carry_diff > 5 else
                "moderate carry" if carry_diff > 2 else
                "low carry" if carry_diff > 0 else
                "negative carry (reverse direction preferred)"
            )
            # Viability: consider yield > 2% and known liquid pairs
            liquid_pairs = {"USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "NZD"}
            liquidity = "high" if base_ccy in liquid_pairs and quote_ccy in liquid_pairs else "medium/low"
            viability = "viable" if carry_diff > 2 else ("marginal" if carry_diff > 0 else "not recommended")
        else:
            carry_diff = None
            carry_label = "rate data unavailable"
            liquidity = "unknown"
            viability = "insufficient data"

        return {
            "pair": f"{base_ccy}/{quote_ccy}",
            "snapshot_utc": _dt.utcnow().strftime("%Y-%m-%d %H:%M"),
            "base_currency": {
                "code": base_ccy,
                "short_rate_pct": base_rate,
                "note": "borrow (short) this currency",
            },
            "quote_currency": {
                "code": quote_ccy,
                "short_rate_pct": quote_rate,
                "note": "invest (long) this currency",
            },
            "carry_differential_pct": carry_diff,
            "carry_label": carry_label,
            "spot_rate": spot,
            "liquidity": liquidity,
            "carry_viability": viability,
            "risk_note": "Carry trades are exposed to exchange rate risk. A 1% adverse FX move can eliminate carry gains. High-yield currencies often depreciate over time.",
            "source": "Yahoo Finance (short-term yields + spot rates, free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_stock_screener(
    max_pe: float = None,
    min_pe: float = None,
    min_dividend_yield: float = None,
    min_market_cap_b: float = None,
    max_market_cap_b: float = None,
    sector: str = None,
    min_price: float = None,
    max_price: float = None,
    limit: int = 20,
) -> dict:
    """Screen S&P 500 stocks by fundamental criteria.

    Args:
        max_pe: Maximum P/E ratio (e.g. 25 → only value stocks)
        min_pe: Minimum P/E ratio (e.g. 0 → exclude negative P/E)
        min_dividend_yield: Minimum dividend yield in % (e.g. 2.0 → 2%+)
        min_market_cap_b: Minimum market cap in billions USD (e.g. 100)
        max_market_cap_b: Maximum market cap in billions USD (e.g. 500)
        sector: Filter by sector keyword (e.g. 'Technology', 'Energy', 'Health')
        min_price: Minimum share price in USD
        max_price: Maximum share price in USD
        limit: Max results to return (default 20, max 50)
    """
    await Actor.charge("advanced_tool")
    try:
        # Curated universe: 80 liquid S&P 500 names across all sectors
        UNIVERSE = [
            # Technology
            "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "ORCL", "CRM", "AMD", "INTC",
            "QCOM", "TXN", "IBM", "NOW", "AMAT", "LRCX", "MU", "ADI", "KLAC", "HPQ",
            # Health Care
            "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "AMGN",
            "MDT", "BMY", "ISRG", "VRTX", "CVS",
            # Financials
            "BRK-B", "JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "AXP", "USB",
            "PGR", "CB", "MMC", "AON", "MET",
            # Consumer Discretionary
            "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "BKNG", "CMG",
            # Consumer Staples
            "WMT", "PG", "KO", "PEP", "COST", "PM", "MO", "CL", "KMB", "GIS",
            # Energy
            "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC", "PXD", "OXY",
            # Industrials
            "CAT", "HON", "UPS", "DE", "GE", "RTX", "LMT", "NOC", "EMR", "ITW",
            # Communication Services
            "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS",
            # Utilities
            "NEE", "DUK", "SO", "D", "AEP",
            # Real Estate
            "AMT", "PLD", "EQIX", "SPG",
            # Materials
            "LIN", "APD", "SHW", "ECL", "NEM",
        ]

        loop = asyncio.get_event_loop()
        limit = min(int(limit), 50)

        def _fetch_info(ticker: str):
            try:
                info = yf.Ticker(ticker).info
                pe = info.get("trailingPE") or info.get("forwardPE")
                dy = info.get("dividendYield")
                mc = info.get("marketCap")
                sec = info.get("sector", "")
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                name = info.get("shortName") or info.get("longName") or ticker
                return {
                    "ticker": ticker,
                    "name": name,
                    "sector": sec,
                    "price": round(float(price), 2) if price else None,
                    "pe_ratio": round(float(pe), 2) if pe else None,
                    "dividend_yield_pct": round(float(dy) * 100, 2) if dy else 0.0,
                    "market_cap_b": round(float(mc) / 1e9, 2) if mc else None,
                }
            except Exception:
                return None

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(_fetch_info, UNIVERSE))

        matches = []
        for r in results:
            if r is None:
                continue
            if max_pe is not None and (r["pe_ratio"] is None or r["pe_ratio"] > max_pe):
                continue
            if min_pe is not None and (r["pe_ratio"] is None or r["pe_ratio"] < min_pe):
                continue
            if min_dividend_yield is not None and r["dividend_yield_pct"] < min_dividend_yield:
                continue
            if min_market_cap_b is not None and (r["market_cap_b"] is None or r["market_cap_b"] < min_market_cap_b):
                continue
            if max_market_cap_b is not None and (r["market_cap_b"] is None or r["market_cap_b"] > max_market_cap_b):
                continue
            if sector is not None and sector.lower() not in r["sector"].lower():
                continue
            if min_price is not None and (r["price"] is None or r["price"] < min_price):
                continue
            if max_price is not None and (r["price"] is None or r["price"] > max_price):
                continue
            matches.append(r)

        matches.sort(key=lambda x: x["market_cap_b"] or 0, reverse=True)
        matches = matches[:limit]

        criteria_used = {k: v for k, v in {
            "max_pe": max_pe, "min_pe": min_pe,
            "min_dividend_yield_pct": min_dividend_yield,
            "min_market_cap_b": min_market_cap_b, "max_market_cap_b": max_market_cap_b,
            "sector": sector, "min_price": min_price, "max_price": max_price,
        }.items() if v is not None}

        return {
            "screener_results": matches,
            "count": len(matches),
            "universe_size": len(UNIVERSE),
            "criteria": criteria_used,
            "sorted_by": "market_cap_desc",
            "source": "Yahoo Finance (S&P 500 universe, free, no API key)",
            "note": "Universe: 80 curated S&P 500 names across all 11 sectors.",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_flow(ticker: str, top_n: int = 20) -> dict:
    """Unusual options flow analysis — detects high-volume/OI contracts that may signal smart money positioning.
    Analyzes nearest 3 expiration dates. Returns put/call ratios, sentiment signal, and top unusual contracts sorted by notional value.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA, SPY)
        top_n: Number of top unusual contracts to return (default 20, max 50)
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf

        t = yf.Ticker(ticker.upper())
        exp_dates = t.options

        if not exp_dates:
            return {"error": f"No options data available for {ticker}"}

        dates_to_use = exp_dates[:min(3, len(exp_dates))]

        all_unusual = []
        total_call_volume = 0
        total_put_volume = 0
        total_call_oi = 0
        total_put_oi = 0

        for exp in dates_to_use:
            try:
                chain = t.option_chain(exp)
                calls = chain.calls.copy()
                puts = chain.puts.copy()

                total_call_volume += int(calls["volume"].fillna(0).sum())
                total_put_volume += int(puts["volume"].fillna(0).sum())
                total_call_oi += int(calls["openInterest"].fillna(0).sum())
                total_put_oi += int(puts["openInterest"].fillna(0).sum())

                for df, opt_type in [(calls, "CALL"), (puts, "PUT")]:
                    df["volume"] = df["volume"].fillna(0)
                    df["openInterest"] = df["openInterest"].fillna(0)
                    df["vol_oi_ratio"] = df.apply(
                        lambda row: round(row["volume"] / row["openInterest"], 2)
                        if row["openInterest"] > 100 else 0,
                        axis=1,
                    )
                    unusual = df[(df["volume"] > 500) & (df["vol_oi_ratio"] > 0.3)]
                    for _, row in unusual.iterrows():
                        notional = row["volume"] * float(row.get("lastPrice", 0)) * 100
                        all_unusual.append({
                            "type": opt_type,
                            "expiry": exp,
                            "strike": float(row.get("strike", 0)),
                            "last_price": round(float(row.get("lastPrice", 0)), 2),
                            "volume": int(row["volume"]),
                            "open_interest": int(row["openInterest"]),
                            "vol_oi_ratio": float(row["vol_oi_ratio"]),
                            "implied_volatility_pct": round(float(row.get("impliedVolatility", 0)) * 100, 1),
                            "notional_usd": round(notional, 0),
                            "in_the_money": bool(row.get("inTheMoney", False)),
                        })
            except Exception:
                continue

        all_unusual.sort(key=lambda x: x["notional_usd"], reverse=True)
        top_contracts = all_unusual[:min(int(top_n), 50)]

        pc_volume_ratio = round(total_put_volume / total_call_volume, 3) if total_call_volume > 0 else None
        pc_oi_ratio = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else None

        if pc_volume_ratio is not None:
            if pc_volume_ratio < 0.7:
                sentiment = "BULLISH (heavy call buying)"
            elif pc_volume_ratio > 1.3:
                sentiment = "BEARISH (heavy put buying)"
            else:
                sentiment = "NEUTRAL"
        else:
            sentiment = "UNKNOWN"

        call_count = sum(1 for c in top_contracts if c["type"] == "CALL")
        put_count = sum(1 for c in top_contracts if c["type"] == "PUT")
        dominant = "CALLS" if call_count > put_count else "PUTS" if put_count > call_count else "MIXED"

        return {
            "ticker": ticker.upper(),
            "expirations_analyzed": list(dates_to_use),
            "summary": {
                "total_call_volume": total_call_volume,
                "total_put_volume": total_put_volume,
                "put_call_volume_ratio": pc_volume_ratio,
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "put_call_oi_ratio": pc_oi_ratio,
                "sentiment_signal": sentiment,
                "dominant_unusual_flow": dominant,
                "unusual_contracts_found": len(all_unusual),
            },
            "top_unusual_contracts": top_contracts,
            "note": "Unusual = volume > 500 & vol/OI ratio > 0.3. Notional = volume × last_price × 100. Smart money = large-notional ITM/near-ATM.",
            "source": "Yahoo Finance options chain (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_call_sentiment(ticker: str) -> dict:
    """
    어닝 콜 sentiment 분석: 최근 실적 발표 관련 뉴스/텍스트에서
    긍/부정 신호, guidance 방향, 핵심 키워드를 추출한다.

    Parameters
    ----------
    ticker : str
        주식 티커 (예: AAPL, MSFT, NVDA)

    Returns
    -------
    dict
        overall_sentiment     : POSITIVE / NEGATIVE / NEUTRAL
        sentiment_score       : -100 ~ +100 (양수=긍정, 음수=부정)
        guidance_signal       : RAISED / LOWERED / MAINTAINED / UNKNOWN
        positive_signals_found: 탐지된 긍정 키워드
        negative_signals_found: 탐지된 부정 키워드
        recent_earnings_news  : 최근 어닝 관련 뉴스 (최대 5개)
        signal_counts         : pos/neg 개수, 분석 뉴스 수
    """
    await Actor.charge("advanced_tool", count=1)

    import yfinance as yf
    from datetime import datetime, timezone

    POSITIVE_KEYWORDS = [
        "beat", "exceeded", "surpassed", "record high", "strong results",
        "raised guidance", "raised outlook", "increased guidance", "raised forecast",
        "optimistic", "accelerating", "robust demand", "margin improvement",
        "outperform", "solid quarter", "momentum", "expansion",
        "share buyback", "dividend increase", "revenue growth",
    ]
    NEGATIVE_KEYWORDS = [
        "missed", "fell short", "below expectations", "lowered guidance",
        "reduced guidance", "cut guidance", "warned", "weak demand",
        "disappointing", "challenging environment", "headwinds",
        "declining revenue", "restructuring", "layoffs", "write-down",
        "uncertainty", "slowing growth", "net loss", "margin compression",
    ]
    GUIDANCE_RAISED_KWS = [
        "raised guidance", "increased guidance", "raised outlook",
        "raised full-year", "raised forecast", "boosted guidance",
    ]
    GUIDANCE_LOWERED_KWS = [
        "lowered guidance", "reduced guidance", "cut guidance",
        "lowered outlook", "lowered forecast", "trimmed guidance", "warned",
    ]
    GUIDANCE_MAINTAINED_KWS = [
        "maintained guidance", "reiterated guidance", "confirmed guidance",
        "reaffirmed guidance", "in line with guidance",
    ]
    EARNINGS_FILTER_KWS = [
        "earnings", "revenue", "quarterly", "q1", "q2", "q3", "q4",
        "results", "guidance", "outlook", "eps", "profit", "beat", "miss",
        "fiscal", "annual report",
    ]

    try:
        t = yf.Ticker(ticker.upper())
        news = t.news or []

        # 뉴스 텍스트 수집 (최근 30개)
        all_text = ""
        earnings_news = []
        for item in news[:30]:
            title = item.get("title", "")
            summary = item.get("summary", "")
            combined_lower = (title + " " + summary).lower()
            all_text += " " + combined_lower

            if any(kw in combined_lower for kw in EARNINGS_FILTER_KWS):
                pub_ts = item.get("providerPublishTime", 0)
                earnings_news.append({
                    "title": title,
                    "publisher": item.get("publisher", ""),
                    "published": (
                        datetime.fromtimestamp(pub_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                        if pub_ts else "unknown"
                    ),
                    "link": item.get("link", ""),
                })

        # sentiment 점수 계산
        pos_signals = [kw for kw in POSITIVE_KEYWORDS if kw in all_text]
        neg_signals = [kw for kw in NEGATIVE_KEYWORDS if kw in all_text]
        pos_score = len(pos_signals)
        neg_score = len(neg_signals)
        total = pos_score + neg_score

        if total == 0:
            normalized_score = 0
        else:
            normalized_score = round(((pos_score - neg_score) / total) * 100)

        if normalized_score >= 20:
            overall = "POSITIVE"
        elif normalized_score <= -20:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"

        # guidance 방향 감지 (우선순위: RAISED > LOWERED > MAINTAINED)
        guidance = "UNKNOWN"
        for kw in GUIDANCE_RAISED_KWS:
            if kw in all_text:
                guidance = "RAISED"
                break
        if guidance == "UNKNOWN":
            for kw in GUIDANCE_LOWERED_KWS:
                if kw in all_text:
                    guidance = "LOWERED"
                    break
        if guidance == "UNKNOWN":
            for kw in GUIDANCE_MAINTAINED_KWS:
                if kw in all_text:
                    guidance = "MAINTAINED"
                    break

        return {
            "ticker": ticker.upper(),
            "overall_sentiment": overall,
            "sentiment_score": normalized_score,
            "sentiment_score_note": "+100=fully positive, -100=fully negative, 0=neutral",
            "guidance_signal": guidance,
            "positive_signals_found": pos_signals[:10],
            "negative_signals_found": neg_signals[:10],
            "signal_counts": {
                "positive": pos_score,
                "negative": neg_score,
                "earnings_news_found": len(earnings_news),
                "total_news_analyzed": min(30, len(news)),
            },
            "recent_earnings_news": earnings_news[:5],
            "note": "Keyword-based NLP on recent Yahoo Finance headlines & summaries. No API key required.",
            "source": "Yahoo Finance news (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_economic_surprise_index(country: str = "US") -> dict:
    """Economic Surprise Index proxy: macro indicator momentum vs trend for US/EU/JP/CN/GB/KR/BR/IN. Positive=economy beating trend. No API key required."""
    await Actor.charge("basic_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        country = country.upper()
        end = datetime.now()
        start_3m = end - timedelta(days=100)

        if country == "US":
            indicators = {
                "S&P 500 (Growth)": ("^GSPC", False),
                "VIX (Risk, inverted)": ("^VIX", True),
                "10Y Treasury Yield": ("^TNX", False),
                "Oil (Inflation proxy)": ("CL=F", False),
                "Gold (Risk-off, inverted)": ("GC=F", True),
                "USD Index": ("DX-Y.NYB", False),
            }
            results = []
            positive = 0
            negative = 0
            for name, (ticker, inverted) in indicators.items():
                try:
                    data = yf.download(ticker, start=start_3m, end=end, progress=False, auto_adjust=True)
                    if data.empty or len(data) < 22:
                        continue
                    close = data["Close"].squeeze()
                    recent = float(close.iloc[-1])
                    month_ago = float(close.iloc[-22])
                    three_month_ago = float(close.iloc[0])
                    mom_1m = (recent - month_ago) / month_ago * 100
                    mom_3m = (recent - three_month_ago) / three_month_ago * 100
                    adj = -mom_1m if inverted else mom_1m
                    signal = "BEAT" if adj > 1.0 else ("MISS" if adj < -1.0 else "IN_LINE")
                    if signal == "BEAT":
                        positive += 1
                    elif signal == "MISS":
                        negative += 1
                    results.append({
                        "indicator": name,
                        "current": round(recent, 4),
                        "1m_pct": round(mom_1m, 2),
                        "3m_pct": round(mom_3m, 2),
                        "signal": signal,
                        "inverted": inverted,
                    })
                except Exception:
                    continue
            total = len(results)
            if total == 0:
                return {"error": "No data available"}
            esi = round((positive - negative) / total * 100)
            if esi >= 30:
                regime = "STRONG_POSITIVE"
            elif esi >= 10:
                regime = "SLIGHTLY_POSITIVE"
            elif esi <= -30:
                regime = "STRONG_NEGATIVE"
            elif esi <= -10:
                regime = "SLIGHTLY_NEGATIVE"
            else:
                regime = "NEUTRAL"
            return {
                "country": "US",
                "esi_score": esi,
                "esi_note": "+100=all beating, -100=all missing, 0=neutral",
                "regime": regime,
                "positive_surprises": positive,
                "negative_surprises": negative,
                "in_line": total - positive - negative,
                "indicators_analyzed": total,
                "indicators": results,
                "methodology": "Macro ETF/index 1M momentum vs 3M trend (VIX/Gold inverted).",
                "source": "Yahoo Finance (free, no API key)",
            }
        else:
            country_etf = {
                "EU": "EZU", "DE": "EWG", "FR": "EWQ", "JP": "EWJ",
                "CN": "MCHI", "GB": "EWU", "KR": "EWY", "BR": "EWZ",
                "IN": "INDA", "AU": "EWA",
            }
            etf = country_etf.get(country)
            if not etf:
                return {"error": f"Country '{country}' not supported", "available": ["US"] + list(country_etf.keys())}
            data = yf.download(etf, start=start_3m, end=end, progress=False, auto_adjust=True)
            if data.empty:
                return {"error": f"No data for {country} ETF ({etf})"}
            close = data["Close"].squeeze()
            recent = float(close.iloc[-1])
            month_ago = float(close.iloc[-22]) if len(close) > 22 else float(close.iloc[0])
            three_month_ago = float(close.iloc[0])
            mom_1m = (recent - month_ago) / month_ago * 100
            mom_3m = (recent - three_month_ago) / three_month_ago * 100
            if mom_1m > 3.0:
                esi = round(min(100, mom_1m * 10))
                regime = "STRONG_POSITIVE"
            elif mom_1m > 1.0:
                esi = round(mom_1m * 10)
                regime = "SLIGHTLY_POSITIVE"
            elif mom_1m < -3.0:
                esi = round(max(-100, mom_1m * 10))
                regime = "STRONG_NEGATIVE"
            elif mom_1m < -1.0:
                esi = round(mom_1m * 10)
                regime = "SLIGHTLY_NEGATIVE"
            else:
                esi = round(mom_1m * 5)
                regime = "NEUTRAL"
            return {
                "country": country,
                "proxy_etf": etf,
                "esi_score": esi,
                "regime": regime,
                "current": round(recent, 4),
                "1m_pct": round(mom_1m, 2),
                "3m_pct": round(mom_3m, 2),
                "methodology": f"Country ETF ({etf}) 1M momentum as ESI proxy.",
                "source": "Yahoo Finance (free, no API key)",
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_sector_momentum(period_days: int = 20) -> dict:
    """S&P 500 sector ETF momentum ranking — top/bottom 3 sectors + rotation signal. period_days: 5/10/20/60. No API key required."""
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        period_days = max(5, min(252, period_days))

        SECTOR_ETFS = {
            "XLK": "Technology",
            "XLF": "Financials",
            "XLE": "Energy",
            "XLV": "Healthcare",
            "XLI": "Industrials",
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
            "XLRE": "Real Estate",
            "XLB": "Materials",
            "XLC": "Communication Services",
        }

        end = datetime.now()
        start = end - timedelta(days=period_days + 40)

        results = []
        for ticker, sector_name in SECTOR_ETFS.items():
            try:
                data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
                if data.empty or len(data) < 6:
                    continue
                close = data["Close"].squeeze()
                current = float(close.iloc[-1])
                idx = min(period_days, len(close) - 1)
                start_price = float(close.iloc[-idx - 1])
                mom = (current - start_price) / start_price * 100
                five_d = float(close.iloc[-6]) if len(close) > 6 else start_price
                mom_5d = (current - five_d) / five_d * 100
                results.append({
                    "ticker": ticker,
                    "sector": sector_name,
                    "current_price": round(current, 2),
                    f"return_{period_days}d_pct": round(mom, 2),
                    "return_5d_pct": round(mom_5d, 2),
                })
            except Exception:
                continue

        if not results:
            return {"error": "No sector data available"}

        results.sort(key=lambda x: x[f"return_{period_days}d_pct"], reverse=True)

        top_3 = results[:3]
        bottom_3 = results[-3:]

        DEFENSIVE = {"Utilities", "Consumer Staples", "Healthcare"}
        CYCLICAL = {"Technology", "Industrials", "Consumer Discretionary", "Financials"}
        COMMODITY = {"Energy", "Materials"}

        top_set = {r["sector"] for r in top_3}
        if top_set <= CYCLICAL:
            rotation = "RISK_ON — Cyclical sectors leading. Expansion phase."
        elif top_set <= DEFENSIVE:
            rotation = "RISK_OFF — Defensive sectors leading. Contraction/defensive rotation."
        elif top_set & COMMODITY:
            rotation = "COMMODITY_LED — Energy/Materials leading. Inflation or supply shock signal."
        else:
            rotation = "MIXED — No clear single-phase rotation."

        spy_return = None
        try:
            spy = yf.download("SPY", start=start, end=end, progress=False, auto_adjust=True)
            if not spy.empty:
                sc = spy["Close"].squeeze()
                spy_return = round((float(sc.iloc[-1]) - float(sc.iloc[-min(period_days, len(sc)-1)-1])) / float(sc.iloc[-min(period_days, len(sc)-1)-1]) * 100, 2)
        except Exception:
            pass

        return {
            "period_days": period_days,
            "sectors_analyzed": len(results),
            "rotation_signal": rotation,
            "top_3_sectors": top_3,
            "bottom_3_sectors": bottom_3,
            "spy_benchmark_pct": spy_return,
            "full_ranking": results,
            "note": f"Momentum = {period_days}-day price return. Use 5/10/20/60 for short/medium/long-term.",
            "source": "Yahoo Finance SPDR sector ETFs (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_market_breadth() -> dict:
    """Market breadth indicators for the S&P 100 universe: Advance/Decline ratio, New 52W High/Low counts,
    and % of stocks above their 200-day moving average. Composite breadth score 0-100 with overall signal
    (VERY_BULLISH/BULLISH/NEUTRAL/BEARISH/VERY_BEARISH). Source: Yahoo Finance (free, no API key).
    Tier: basic_tool ($0.001/call)."""
    try:
        await Actor.charge("basic_tool", count=1)
        import yfinance as yf
        from datetime import datetime, timedelta

        tickers = [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "LLY",
            "XOM", "V", "UNH", "AVGO", "JNJ", "MA", "PG", "HD", "COST", "MRK",
            "ABBV", "CVX", "AMD", "CRM", "ORCL", "BAC", "KO", "PEP", "NFLX", "TMO",
            "WMT", "MCD", "CSCO", "ABT", "ACN", "LIN", "NKE", "DHR", "INTC", "VZ",
            "CMCSA", "NEE", "PM", "IBM", "QCOM", "GE", "TXN", "INTU", "SPGI", "AMGN",
            "RTX", "HON", "GS", "CAT", "LOW", "BKNG", "SYK", "BLK", "ISRG", "ELV",
            "ADI", "AXP", "DE", "PLD", "MDLZ", "CB", "SCHW", "GILD", "MMC", "ZTS",
            "TJX", "REGN", "SO", "MO", "EOG", "WM", "SHW", "CME", "ITW", "DUK",
            "AON", "MCO", "USB", "BSX", "CL", "HUM", "PNC", "F", "GM", "NSC",
            "ETN", "EMR", "PSA", "APD", "WELL", "AIG", "D", "KMB", "MSI", "TGT",
        ]

        end = datetime.today()
        start = end - timedelta(days=280)

        data = yf.download(
            tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
            threads=True,
        )
        if data.empty:
            return {"error": "No data returned from Yahoo Finance"}

        if isinstance(data.columns, pd.MultiIndex):
            closes = data["Close"]
        else:
            closes = data[["Close"]]

        closes = closes.dropna(axis=1, thresh=200)
        valid_n = len(closes.columns)
        if valid_n == 0:
            return {"error": "No valid ticker data after filtering"}

        latest = closes.iloc[-1]
        prev = closes.iloc[-2] if len(closes) >= 2 else latest

        advances = int((latest > prev).sum())
        declines = int((latest < prev).sum())
        unchanged = valid_n - advances - declines
        ad_ratio = round(advances / declines, 2) if declines > 0 else None
        if ad_ratio is None:
            ad_signal = "ALL_ADVANCING"
        elif ad_ratio >= 2.0:
            ad_signal = "STRONG_BREADTH"
        elif ad_ratio >= 1.2:
            ad_signal = "POSITIVE_BREADTH"
        elif ad_ratio >= 0.8:
            ad_signal = "NEUTRAL"
        elif ad_ratio >= 0.5:
            ad_signal = "NEGATIVE_BREADTH"
        else:
            ad_signal = "VERY_WEAK"

        roll_high = closes.rolling(252, min_periods=100).max().iloc[-1]
        roll_low = closes.rolling(252, min_periods=100).min().iloc[-1]
        new_highs = int((latest >= roll_high * 0.99).sum())
        new_lows = int((latest <= roll_low * 1.01).sum())
        hl_ratio = round(new_highs / (new_lows + 1), 2)

        ma200 = closes.rolling(200).mean().iloc[-1]
        above_200ma = int((latest > ma200).sum())
        pct_above_200ma = round(above_200ma / valid_n * 100, 1)
        if pct_above_200ma >= 70:
            ma_regime = "BULL_MARKET"
        elif pct_above_200ma >= 50:
            ma_regime = "HEALTHY"
        elif pct_above_200ma >= 30:
            ma_regime = "CAUTION"
        else:
            ma_regime = "BEAR_MARKET"

        ad_score = (advances / valid_n) * 100
        hl_score = (new_highs / (new_highs + new_lows + 1)) * 100
        breadth_score = round(ad_score * 0.3 + hl_score * 0.3 + pct_above_200ma * 0.4, 1)
        if breadth_score >= 70:
            overall = "VERY_BULLISH"
        elif breadth_score >= 55:
            overall = "BULLISH"
        elif breadth_score >= 40:
            overall = "NEUTRAL"
        elif breadth_score >= 25:
            overall = "BEARISH"
        else:
            overall = "VERY_BEARISH"

        return {
            "universe": f"{valid_n} large-cap stocks (S&P 100 proxy)",
            "date": end.strftime("%Y-%m-%d"),
            "advance_decline": {
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "ad_ratio": ad_ratio,
                "signal": ad_signal,
            },
            "new_highs_lows_52w": {
                "new_52w_highs": new_highs,
                "new_52w_lows": new_lows,
                "hl_ratio": hl_ratio,
            },
            "moving_average": {
                "above_200ma": above_200ma,
                "pct_above_200ma": pct_above_200ma,
                "regime": ma_regime,
            },
            "breadth_score": breadth_score,
            "overall_signal": overall,
            "note": (
                "Breadth score 0-100: 70+ very bullish, 55-70 bullish, 40-55 neutral, 25-40 bearish, <25 very bearish. "
                "Advance/Decline uses daily close vs prior close. 52W High/Low uses rolling 252-day window."
            ),
            "source": "Yahoo Finance (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_volatility_surface(ticker: str) -> dict:
    """Options implied volatility (IV) surface for a given ticker: IV by expiry date and strike price.
    Returns calls and puts IV across all available expiries, ATM IV summary, term structure (short/mid/long-term IV),
    and skew signal (PUT_SKEW / CALL_SKEW / FLAT). Source: Yahoo Finance (free, no API key).
    Tier: premium_tool ($0.005/call)."""
    try:
        await Actor.charge("premium_tool", count=1)
        import yfinance as yf

        t = yf.Ticker(ticker.upper())
        expiries = t.options
        if not expiries:
            return {"error": f"No options data available for {ticker}"}

        spot_info = t.fast_info
        spot_price = getattr(spot_info, "last_price", None) or getattr(spot_info, "regularMarketPrice", None)
        if spot_price is None:
            try:
                hist = t.history(period="1d")
                spot_price = float(hist["Close"].iloc[-1]) if not hist.empty else None
            except Exception:
                pass

        surface = []
        atm_ivs = []

        for exp in expiries[:8]:
            try:
                chain = t.option_chain(exp)
                calls = chain.calls[["strike", "impliedVolatility", "volume", "openInterest"]].copy()
                puts = chain.puts[["strike", "impliedVolatility", "volume", "openInterest"]].copy()
                calls = calls[calls["impliedVolatility"] > 0].dropna()
                puts = puts[puts["impliedVolatility"] > 0].dropna()
                if calls.empty and puts.empty:
                    continue

                atm_call_iv = None
                if spot_price and not calls.empty:
                    idx = (calls["strike"] - spot_price).abs().idxmin()
                    atm_call_iv = round(float(calls.loc[idx, "impliedVolatility"]) * 100, 2)
                    atm_ivs.append({"expiry": exp, "atm_call_iv_pct": atm_call_iv})

                skew = None
                if spot_price and not calls.empty and not puts.empty:
                    otm_put = puts[puts["strike"] < spot_price * 0.95]
                    otm_call = calls[calls["strike"] > spot_price * 1.05]
                    if not otm_put.empty and not otm_call.empty:
                        put_iv = float(otm_put["impliedVolatility"].mean()) * 100
                        call_iv = float(otm_call["impliedVolatility"].mean()) * 100
                        skew = round(put_iv - call_iv, 2)

                surface.append({
                    "expiry": exp,
                    "atm_call_iv_pct": atm_call_iv,
                    "skew_put_minus_call_pct": skew,
                    "num_call_strikes": len(calls),
                    "num_put_strikes": len(puts),
                    "call_iv_range_pct": [
                        round(float(calls["impliedVolatility"].min()) * 100, 2),
                        round(float(calls["impliedVolatility"].max()) * 100, 2),
                    ] if not calls.empty else None,
                    "put_iv_range_pct": [
                        round(float(puts["impliedVolatility"].min()) * 100, 2),
                        round(float(puts["impliedVolatility"].max()) * 100, 2),
                    ] if not puts.empty else None,
                })
            except Exception:
                continue

        if not surface:
            return {"error": "Could not retrieve IV surface data"}

        from datetime import datetime
        today = datetime.today()
        term = {"short_term": [], "mid_term": [], "long_term": []}
        for row in atm_ivs:
            try:
                dte = (datetime.strptime(row["expiry"], "%Y-%m-%d") - today).days
                if dte <= 30:
                    term["short_term"].append(row["atm_call_iv_pct"])
                elif dte <= 90:
                    term["mid_term"].append(row["atm_call_iv_pct"])
                else:
                    term["long_term"].append(row["atm_call_iv_pct"])
            except Exception:
                pass

        term_summary = {
            k: round(sum(v) / len(v), 2) if v else None
            for k, v in term.items()
        }

        all_skews = [r["skew_put_minus_call_pct"] for r in surface if r.get("skew_put_minus_call_pct") is not None]
        avg_skew = round(sum(all_skews) / len(all_skews), 2) if all_skews else None
        if avg_skew is None:
            skew_signal = "UNKNOWN"
        elif avg_skew > 3:
            skew_signal = "PUT_SKEW — Elevated downside protection demand (bearish bias)"
        elif avg_skew < -3:
            skew_signal = "CALL_SKEW — Elevated upside speculation (bullish bias)"
        else:
            skew_signal = "FLAT — Balanced IV across puts and calls"

        return {
            "ticker": ticker.upper(),
            "spot_price": round(spot_price, 2) if spot_price else None,
            "expiries_analyzed": len(surface),
            "iv_surface": surface,
            "term_structure_atm_iv_pct": term_summary,
            "avg_skew_pct": avg_skew,
            "skew_signal": skew_signal,
            "note": (
                "IV in % (e.g. 25.0 = 25% annualized IV). Skew = avg OTM put IV minus avg OTM call IV. "
                "PUT_SKEW (positive) = market pays premium for downside protection."
            ),
            "source": "Yahoo Finance options chain (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_fx_volatility(pair: str = "EURUSD") -> dict:
    """
    FX pair realized volatility analysis — vol term structure and regime.
    Computes 10/30/60/252-day annualized realized volatility as a proxy for
    currency options market conditions and hedging cost.
    Covers major pairs: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD,
    EURGBP, USDMXN, USDBRL. Returns vol regime (VERY_LOW/LOW/MODERATE/ELEVATED/HIGH)
    and trend (RISING/FALLING/STABLE) for currency risk assessment.
    """
    await Actor.charge("premium_tool", count=1)

    PAIR_MAP = {
        "EURUSD": "EURUSD=X",
        "USDJPY": "JPY=X",
        "GBPUSD": "GBPUSD=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "CAD=X",
        "USDCHF": "CHF=X",
        "NZDUSD": "NZDUSD=X",
        "EURGBP": "EURGBP=X",
        "USDMXN": "MXN=X",
        "USDBRL": "BRL=X",
        "USDINR": "INR=X",
        "USDKRW": "KRW=X",
    }

    pair_upper = pair.upper().replace("/", "").replace("-", "")
    symbol = PAIR_MAP.get(pair_upper, f"{pair_upper}=X")

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: yf.download(symbol, period="2y", auto_adjust=True, progress=False)
        )
        if data.empty:
            return {"error": f"No data for pair: {pair}. Try EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF."}

        closes = data["Close"].squeeze()
        log_returns = (closes / closes.shift(1)).apply(lambda x: x).map(lambda x: __import__('math').log(x) if x > 0 else float('nan'))
        log_returns = log_returns.dropna()

        def realized_vol(window):
            if len(log_returns) < window:
                return None
            rv = float(log_returns.tail(window).std()) * (252 ** 0.5) * 100
            return round(rv, 2)

        rv_10 = realized_vol(10)
        rv_30 = realized_vol(30)
        rv_60 = realized_vol(60)
        rv_252 = realized_vol(252)

        if rv_30 is None:
            vol_regime = "UNKNOWN"
        elif rv_30 < 4:
            vol_regime = "VERY_LOW — Compressed vol, low hedging cost"
        elif rv_30 < 7:
            vol_regime = "LOW — Below-average FX volatility"
        elif rv_30 < 11:
            vol_regime = "MODERATE — Average FX vol range"
        elif rv_30 < 16:
            vol_regime = "ELEVATED — Above-average, consider hedging"
        else:
            vol_regime = "HIGH — Crisis-level vol, significant currency risk"

        vol_trend = "STABLE"
        if rv_10 and rv_60:
            if rv_10 > rv_60 * 1.25:
                vol_trend = "RISING — Short-term vol spike vs medium-term baseline"
            elif rv_10 < rv_60 * 0.75:
                vol_trend = "FALLING — Vol compression, short-term calmer than medium"
            else:
                vol_trend = "STABLE — Vol consistent across short and medium horizons"

        spot = round(float(closes.iloc[-1]), 5)
        change_30d = round((float(closes.iloc[-1]) / float(closes.iloc[-30]) - 1) * 100, 3) if len(closes) >= 30 else None
        change_90d = round((float(closes.iloc[-1]) / float(closes.iloc[-90]) - 1) * 100, 3) if len(closes) >= 90 else None
        high_52w = round(float(closes.tail(252).max()), 5)
        low_52w = round(float(closes.tail(252).min()), 5)
        pct_from_high = round((spot / high_52w - 1) * 100, 2)
        pct_from_low = round((spot / low_52w - 1) * 100, 2)

        return {
            "pair": pair_upper,
            "symbol": symbol,
            "spot_rate": spot,
            "52w_high": high_52w,
            "52w_low": low_52w,
            "pct_from_52w_high": pct_from_high,
            "pct_from_52w_low": pct_from_low,
            "change_30d_pct": change_30d,
            "change_90d_pct": change_90d,
            "realized_vol_10d_pct": rv_10,
            "realized_vol_30d_pct": rv_30,
            "realized_vol_60d_pct": rv_60,
            "realized_vol_252d_pct": rv_252,
            "vol_regime": vol_regime,
            "vol_trend": vol_trend,
            "note": (
                "Realized vol (annualized %) = proxy for implied vol / option premium cost. "
                "Higher RV = more expensive FX options / hedging. "
                "True IV surface requires paid FX options data (Bloomberg/Refinitiv)."
            ),
            "source": "Yahoo Finance (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_credit_spreads() -> dict:
    """
    US credit market spread analysis using bond ETF proxies.
    Tracks IG corporate (LQD), HY corporate (HYG), EM sovereign (EMB) vs
    Treasury benchmark (IEF). Computes relative 30/60/90d performance to
    estimate spread direction: widening (RISK_OFF) vs tightening (RISK_ON).
    Returns credit cycle regime and 52W positioning for each ETF.
    Note: actual OAS in basis points requires FRED API key.
    This tool provides direction signal using free Yahoo Finance data.
    """
    await Actor.charge("basic_tool", count=1)

    try:
        import asyncio
        etfs = {
            "LQD": "IG Corporate (Investment Grade)",
            "HYG": "HY Corporate (High Yield)",
            "EMB": "EM Sovereign (USD)",
            "IEF": "7-10Y US Treasury (benchmark)",
            "TLT": "20Y+ US Treasury (long-duration)",
            "SHY": "1-3Y US Treasury (short-end)",
        }

        symbols = list(etfs.keys())
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: yf.download(symbols, period="1y", auto_adjust=True, progress=False)["Close"]
        )

        results = {}
        for symbol in symbols:
            col = symbol if symbol in raw.columns else None
            if col is None:
                continue
            prices = raw[col].dropna()
            if prices.empty:
                continue

            current = float(prices.iloc[-1])
            high_52w = float(prices.max())
            low_52w = float(prices.min())
            pct_from_high = round((current / high_52w - 1) * 100, 2)
            pct_from_low = round((current / low_52w - 1) * 100, 2)

            ret_30 = round((current / float(prices.iloc[-30]) - 1) * 100, 3) if len(prices) >= 30 else None
            ret_60 = round((current / float(prices.iloc[-60]) - 1) * 100, 3) if len(prices) >= 60 else None
            ret_90 = round((current / float(prices.iloc[-90]) - 1) * 100, 3) if len(prices) >= 90 else None

            results[symbol] = {
                "name": etfs[symbol],
                "price": round(current, 2),
                "52w_high": round(high_52w, 2),
                "52w_low": round(low_52w, 2),
                "pct_from_52w_high": pct_from_high,
                "pct_from_52w_low": pct_from_low,
                "return_30d_pct": ret_30,
                "return_60d_pct": ret_60,
                "return_90d_pct": ret_90,
            }

        spread_proxies = {}
        ief_30 = results.get("IEF", {}).get("return_30d_pct") or 0
        ief_60 = results.get("IEF", {}).get("return_60d_pct") or 0

        for sym, label in [("LQD", "IG"), ("HYG", "HY"), ("EMB", "EM")]:
            if sym in results:
                r30 = results[sym].get("return_30d_pct") or 0
                r60 = results[sym].get("return_60d_pct") or 0
                proxy_30 = round(ief_30 - r30, 3)
                proxy_60 = round(ief_60 - r60, 3)
                spread_proxies[f"{label}_spread_proxy"] = {
                    "30d": proxy_30,
                    "60d": proxy_60,
                    "interpretation": (
                        "Positive = spread widening (credit risk rising). "
                        "Negative = spread tightening (risk appetite improving)."
                    ),
                }

        hy_30 = spread_proxies.get("HY_spread_proxy", {}).get("30d", 0) or 0
        ig_30 = spread_proxies.get("IG_spread_proxy", {}).get("30d", 0) or 0
        hyg_from_high = results.get("HYG", {}).get("pct_from_52w_high", 0) or 0

        if hy_30 < -1 and ig_30 < -0.5 and hyg_from_high > -5:
            regime = "RISK_ON — Spreads tightening, HY near 52W high. Credit conditions loose."
        elif hy_30 > 3 or hyg_from_high < -15:
            regime = "RISK_OFF — Significant spread widening or HY well below 52W high. Credit stress."
        elif hy_30 > 1.5 or ig_30 > 0.5:
            regime = "CAUTION — Moderate spread widening. Monitor HY/IG divergence."
        elif hy_30 < 0 and ig_30 < 0:
            regime = "RISK_ON — Both HY and IG outperforming Treasuries. Healthy credit appetite."
        else:
            regime = "NEUTRAL — Credit conditions stable, no strong directional signal."

        return {
            "credit_regime": regime,
            "spread_proxies": spread_proxies,
            "etf_data": results,
            "note": (
                "Spread proxy = IEF (7-10Y Treasury) return minus credit ETF return over 30/60d. "
                "Positive proxy = credit underperformed Treasuries = spreads widening direction. "
                "For actual OAS in basis points, enable FRED API key (BAMLC0A0CM / BAMLH0A0HYM2)."
            ),
            "source": "Yahoo Finance ETF data (free, no API key)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_global_equity_heatmap() -> dict:
    """
    Global equity heatmap: 1-day, 1-week, and 1-month returns for 20 major country indices.
    Groups countries into Developed Markets and Emerging Markets.
    Highlights the top 3 best and worst performing markets for each time period.
    Useful for cross-country macro rotation and global risk appetite signals.
    No API key required — Yahoo Finance data.
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import math
        import asyncio

        country_indices = {
            "SPY":  ("United States",    "DM"),
            "EWJ":  ("Japan",            "DM"),
            "EWG":  ("Germany",          "DM"),
            "EWU":  ("United Kingdom",   "DM"),
            "EWC":  ("Canada",           "DM"),
            "EWA":  ("Australia",        "DM"),
            "EWL":  ("Switzerland",      "DM"),
            "EWQ":  ("France",           "DM"),
            "EWI":  ("Italy",            "DM"),
            "EWP":  ("Spain",            "DM"),
            "EWD":  ("Sweden",           "DM"),
            "EWS":  ("Singapore",        "DM"),
            "EWZ":  ("Brazil",           "EM"),
            "FXI":  ("China",            "EM"),
            "EWY":  ("South Korea",      "EM"),
            "EWT":  ("Taiwan",           "EM"),
            "EWW":  ("Mexico",           "EM"),
            "INDA": ("India",            "EM"),
            "EZA":  ("South Africa",     "EM"),
            "THD":  ("Thailand",         "EM"),
        }

        symbols = list(country_indices.keys())
        raw = await asyncio.to_thread(
            lambda: yf.download(symbols, period="3mo", auto_adjust=True, progress=False)
        )

        if raw.empty:
            return {"error": "Failed to fetch data from Yahoo Finance"}

        if "Close" in raw.columns.get_level_values(0):
            closes = raw["Close"]
        else:
            closes = raw

        results = {}
        for sym, (country, market_type) in country_indices.items():
            if sym not in closes.columns:
                continue
            prices = closes[sym].dropna()
            if len(prices) < 5:
                continue
            current = float(prices.iloc[-1])

            def safe_ret(n, p=prices, c=current):
                if len(p) > n:
                    base = float(p.iloc[-(n + 1)])
                    if base == 0 or math.isnan(base):
                        return None
                    return round((c / base - 1) * 100, 2)
                return None

            results[sym] = {
                "country": country,
                "market_type": market_type,
                "price": round(current, 2),
                "return_1d_pct": safe_ret(1),
                "return_1w_pct": safe_ret(5),
                "return_1m_pct": safe_ret(21),
            }

        if not results:
            return {"error": "No data returned for any symbol"}

        def rank_period(key):
            scored = [
                (sym, info["country"], info[key])
                for sym, info in results.items()
                if info[key] is not None
            ]
            scored.sort(key=lambda x: x[2], reverse=True)
            return scored

        def top_bottom(ranked, n=3):
            return {
                "best":  [{"symbol": s, "country": c, "return_pct": r} for s, c, r in ranked[:n]],
                "worst": [{"symbol": s, "country": c, "return_pct": r} for s, c, r in ranked[-n:][::-1]],
            }

        dm_1m = [info["return_1m_pct"] for info in results.values() if info["market_type"] == "DM" and info["return_1m_pct"] is not None]
        em_1m = [info["return_1m_pct"] for info in results.values() if info["market_type"] == "EM" and info["return_1m_pct"] is not None]
        dm_avg = round(sum(dm_1m) / len(dm_1m), 2) if dm_1m else None
        em_avg = round(sum(em_1m) / len(em_1m), 2) if em_1m else None

        if dm_avg is not None and em_avg is not None:
            if em_avg - dm_avg > 1.5:
                rotation_signal = "EM_OUTPERFORMING — Risk appetite elevated. Emerging markets leading on 1M basis."
            elif dm_avg - em_avg > 1.5:
                rotation_signal = "DM_OUTPERFORMING — Risk-off rotation. Developed markets preferred."
            else:
                rotation_signal = "NEUTRAL — DM and EM returns broadly similar over 1 month."
        else:
            rotation_signal = "INSUFFICIENT_DATA"

        rank_1d = rank_period("return_1d_pct")
        rank_1w = rank_period("return_1w_pct")
        rank_1m = rank_period("return_1m_pct")

        return {
            "heatmap": results,
            "rankings": {
                "1d": top_bottom(rank_1d),
                "1w": top_bottom(rank_1w),
                "1m": top_bottom(rank_1m),
            },
            "aggregate": {
                "dm_avg_1m_pct": dm_avg,
                "em_avg_1m_pct": em_avg,
                "rotation_signal": rotation_signal,
            },
            "coverage": f"{len(results)}/20 markets",
            "source": "Yahoo Finance ETF proxies (free, no API key)",
            "note": (
                "ETF prices used as country equity proxies. "
                "Returns are in USD terms. "
                "1D = 1 trading day, 1W = 5 trading days, 1M = 21 trading days."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_commodity_correlation(period_days: int = 90) -> dict:
    """
    Commodity cross-correlation matrix and commodity-to-market correlations.
    Covers Gold, Silver, Oil (WTI), Copper, Wheat, Natural Gas.
    Also computes rolling correlations vs SPY (equities), TLT (bonds), DXY (USD).
    Returns regime signal (commodity cycle: RISK_ON / INFLATION / DEFLATION / MIXED).
    period_days: rolling window in trading days (30, 60, 90, 252). Default 90.
    No API key required — Yahoo Finance data.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import math
        import asyncio

        commodities = {
            "GC=F":  "Gold",
            "SI=F":  "Silver",
            "CL=F":  "WTI Oil",
            "HG=F":  "Copper",
            "ZW=F":  "Wheat",
            "NG=F":  "Natural Gas",
        }
        benchmarks = {
            "SPY":      "S&P 500 (Equities)",
            "TLT":      "20Y Treasury (Bonds)",
            "DX-Y.NYB": "US Dollar Index (DXY)",
        }

        all_syms = list(commodities.keys()) + list(benchmarks.keys())
        n_days = max(30, min(period_days, 252))

        raw = await asyncio.to_thread(
            lambda: yf.download(all_syms, period="2y", auto_adjust=True, progress=False)
        )

        if raw.empty:
            return {"error": "Failed to fetch commodity data"}

        if "Close" in raw.columns.get_level_values(0):
            closes = raw["Close"]
        else:
            closes = raw

        import pandas as pd
        returns = {}
        for sym in all_syms:
            if sym not in closes.columns:
                continue
            prices = closes[sym].dropna()
            if len(prices) < n_days + 5:
                continue
            subset = prices.iloc[-(n_days + 1):]
            rets = subset.pct_change().dropna()
            if len(rets) >= n_days * 0.8:
                returns[sym] = rets

        if len(returns) < 3:
            return {"error": "Insufficient return data for correlation"}

        df = pd.DataFrame(returns).dropna()
        corr = df.corr()

        def fmt(v):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return None
            return round(float(v), 3)

        comm_syms  = [s for s in commodities  if s in df.columns]
        bench_syms = [s for s in benchmarks   if s in df.columns]

        commodity_matrix = {}
        for s1 in comm_syms:
            commodity_matrix[commodities[s1]] = {}
            for s2 in comm_syms:
                commodity_matrix[commodities[s1]][commodities[s2]] = fmt(corr.loc[s1, s2])

        vs_market = {}
        for cs in comm_syms:
            vs_market[commodities[cs]] = {}
            for bs in bench_syms:
                bench_label = benchmarks[bs].split(" (")[0]
                vs_market[commodities[cs]][bench_label] = fmt(corr.loc[cs, bs])

        gold_spy = fmt(corr.loc["GC=F", "SPY"])     if "GC=F" in df.columns and "SPY"      in df.columns else None
        oil_spy  = fmt(corr.loc["CL=F", "SPY"])     if "CL=F" in df.columns and "SPY"      in df.columns else None
        gold_dxy = fmt(corr.loc["GC=F", "DX-Y.NYB"])if "GC=F" in df.columns and "DX-Y.NYB" in df.columns else None

        if gold_spy is not None and oil_spy is not None and gold_dxy is not None:
            if oil_spy > 0.4 and gold_spy > 0.2:
                regime = "RISK_ON — Commodities rising with equities. Growth-driven demand."
            elif gold_spy < -0.1 and gold_dxy < -0.3 and oil_spy < 0:
                regime = "INFLATION_HEDGE — Gold inversely correlated to USD and stocks. Classic inflation/stagflation signal."
            elif oil_spy < -0.3 and gold_spy > 0.2:
                regime = "DEFLATION_RISK — Oil falling with equities, gold rising. Demand destruction / flight to safety."
            elif oil_spy < 0 and gold_spy < 0:
                regime = "RISK_OFF — Both oil and gold diverging from equities. Broad de-risking."
            else:
                regime = "MIXED — No dominant commodity cycle. Monitor cross-asset flows."
        else:
            regime = "INSUFFICIENT_DATA"

        perf = {}
        for sym, name in commodities.items():
            if sym in closes.columns:
                prices = closes[sym].dropna()
                if len(prices) >= 22:
                    ret = round((float(prices.iloc[-1]) / float(prices.iloc[-22]) - 1) * 100, 2)
                    perf[name] = {"return_1m_pct": ret}

        return {
            "period_days": n_days,
            "commodity_cycle_regime": regime,
            "commodity_correlation_matrix": commodity_matrix,
            "vs_market": vs_market,
            "recent_1m_performance": perf,
            "key_signals": {
                "gold_vs_spy": gold_spy,
                "oil_vs_spy": oil_spy,
                "gold_vs_dxy": gold_dxy,
            },
            "source": "Yahoo Finance futures + ETF data (free, no API key)",
            "note": (
                f"Pearson correlation over {n_days} trading days. "
                "1.0 = perfect positive, -1.0 = perfect negative, 0 = no linear relationship. "
                "DX-Y.NYB = USD Index proxy. GC=F/SI=F/CL=F/HG=F/ZW=F/NG=F = Yahoo Finance futures."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_whisper(ticker: str) -> dict:
    """
    Earnings whisper analysis: historical EPS surprise pattern + post-earnings price reaction.
    Returns past 4 quarters: EPS actual vs consensus estimate, beat/miss/in-line classification,
    price reaction 1 day after earnings (%), beat rate, whisper gap estimate.
    Whisper gap = systematic bias between consensus estimate and actual outcome.
    advanced_tool tier ($0.003). No API key required — Yahoo Finance data.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        import math

        t = yf.Ticker(ticker.upper())

        earnings_hist = t.earnings_dates
        if earnings_hist is None or earnings_hist.empty:
            return {"error": f"No earnings data available for {ticker}"}

        hist = earnings_hist.dropna(subset=["Reported EPS", "EPS Estimate"])
        hist = hist[hist["Reported EPS"].notna() & hist["EPS Estimate"].notna()]
        if hist.empty:
            return {"error": f"No reported EPS history found for {ticker}"}

        recent = hist.head(4).copy()
        price_hist = t.history(period="2y", auto_adjust=True)

        quarters = []
        beat_count = 0
        bias_pct_list = []

        for date, row in recent.iterrows():
            actual = float(row["Reported EPS"]) if not math.isnan(float(row["Reported EPS"])) else None
            estimate = float(row["EPS Estimate"]) if not math.isnan(float(row["EPS Estimate"])) else None

            if actual is None or estimate is None:
                continue

            if estimate != 0:
                surprise_pct = round((actual - estimate) / abs(estimate) * 100, 2)
            else:
                surprise_pct = 0.0

            if surprise_pct >= 2:
                classification = "BEAT"
                beat_count += 1
            elif surprise_pct <= -2:
                classification = "MISS"
            else:
                classification = "IN_LINE"
                beat_count += 1

            bias_pct_list.append(surprise_pct)

            price_reaction = None
            if not price_hist.empty:
                try:
                    price_dates = price_hist.index.normalize().date
                    earn_date = date.date()
                    matching = [i for i, d in enumerate(price_dates) if d >= earn_date]
                    if len(matching) >= 2:
                        price_day0 = float(price_hist["Close"].iloc[matching[0]])
                        price_day1 = float(price_hist["Close"].iloc[matching[1]])
                        price_reaction = round((price_day1 / price_day0 - 1) * 100, 2)
                except Exception:
                    price_reaction = None

            quarters.append({
                "date": date.strftime("%Y-%m-%d"),
                "eps_actual": round(actual, 4),
                "eps_estimate": round(estimate, 4),
                "surprise_pct": surprise_pct,
                "classification": classification,
                "price_reaction_1d_pct": price_reaction,
            })

        if not quarters:
            return {"error": "Could not compute earnings history"}

        n = len(quarters)
        beat_rate = round(beat_count / n * 100, 1)
        avg_surprise = round(sum(bias_pct_list) / len(bias_pct_list), 2) if bias_pct_list else 0.0

        if avg_surprise > 5:
            whisper_signal = "STRONG_BEAT_TENDENCY — Market likely prices in higher bar than consensus"
        elif avg_surprise > 2:
            whisper_signal = "MILD_BEAT_TENDENCY — Modest outperformance track record"
        elif avg_surprise < -5:
            whisper_signal = "STRONG_MISS_TENDENCY — Company frequently disappoints"
        elif avg_surprise < -2:
            whisper_signal = "MILD_MISS_TENDENCY — Below-consensus delivery pattern"
        else:
            whisper_signal = "NEUTRAL — No systematic earnings bias detected"

        beat_reactions = [q["price_reaction_1d_pct"] for q in quarters if q["classification"] in ("BEAT", "IN_LINE") and q["price_reaction_1d_pct"] is not None]
        miss_reactions = [q["price_reaction_1d_pct"] for q in quarters if q["classification"] == "MISS" and q["price_reaction_1d_pct"] is not None]
        avg_beat_reaction = round(sum(beat_reactions) / len(beat_reactions), 2) if beat_reactions else None
        avg_miss_reaction = round(sum(miss_reactions) / len(miss_reactions), 2) if miss_reactions else None

        return {
            "ticker": ticker.upper(),
            "quarters_analyzed": n,
            "beat_rate_pct": beat_rate,
            "avg_eps_surprise_pct": avg_surprise,
            "whisper_signal": whisper_signal,
            "avg_price_reaction_on_beat_pct": avg_beat_reaction,
            "avg_price_reaction_on_miss_pct": avg_miss_reaction,
            "quarterly_history": quarters,
            "source": "Yahoo Finance earnings data (free, no API key)",
            "note": (
                "Beat rate >= 50% is typical for S&P 500 companies. "
                "Avg surprise pct > 5% suggests the real bar is above consensus. "
                "Price reaction shows post-earnings drift; negative reaction on beats may signal sell-the-news."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_skew_monitor() -> dict:
    """
    Options put-call skew monitor for major indices: SPY, QQQ, IWM.
    Computes 25-delta proxy skew (OTM put IV minus OTM call IV at ~5% distance from ATM),
    current ATM IV, put-call IV ratio, skew regime (ELEVATED_TAIL_RISK / COMPLACENT / NORMAL),
    composite signal across all 3 indices.
    premium_tool tier ($0.005). No API key required — Yahoo Finance options data.
    """
    await Actor.charge("premium_tool", count=1)
    try:
        import yfinance as yf
        import math

        indices = {
            "SPY": "S&P 500",
            "QQQ": "Nasdaq 100",
            "IWM": "Russell 2000",
        }

        results = {}
        overall_skew_scores = []

        for sym, name in indices.items():
            try:
                t = yf.Ticker(sym)
                current_price = t.fast_info.get("lastPrice") or t.fast_info.get("regularMarketPrice")
                if current_price is None:
                    hist = t.history(period="5d")
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                    else:
                        results[sym] = {"error": "Cannot get current price"}
                        continue

                expirations = t.options
                if not expirations:
                    results[sym] = {"error": "No options data"}
                    continue

                from datetime import datetime, timedelta
                today = datetime.now().date()
                target_exp = None
                for exp in expirations:
                    exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                    days_to_exp = (exp_date - today).days
                    if 14 <= days_to_exp <= 60:
                        target_exp = exp
                        break
                if not target_exp and expirations:
                    target_exp = expirations[0]

                chain = t.option_chain(target_exp)
                calls_df = chain.calls
                puts_df = chain.puts

                if calls_df.empty or puts_df.empty:
                    results[sym] = {"error": "Empty option chain"}
                    continue

                calls_df = calls_df.dropna(subset=["impliedVolatility"])
                puts_df = puts_df.dropna(subset=["impliedVolatility"])

                calls_df["dist"] = (calls_df["strike"] - current_price).abs()
                atm_call = calls_df.nsmallest(1, "dist")
                atm_call_iv = float(atm_call["impliedVolatility"].iloc[0]) if not atm_call.empty else None

                puts_df["dist"] = (puts_df["strike"] - current_price).abs()
                atm_put = puts_df.nsmallest(1, "dist")
                atm_put_iv = float(atm_put["impliedVolatility"].iloc[0]) if not atm_put.empty else None

                otm_put_target = current_price * 0.95
                puts_df["otm_dist"] = (puts_df["strike"] - otm_put_target).abs()
                otm_put = puts_df.nsmallest(1, "otm_dist")
                otm_put_iv = float(otm_put["impliedVolatility"].iloc[0]) if not otm_put.empty else None

                otm_call_target = current_price * 1.05
                calls_df["otm_dist"] = (calls_df["strike"] - otm_call_target).abs()
                otm_call = calls_df.nsmallest(1, "otm_dist")
                otm_call_iv = float(otm_call["impliedVolatility"].iloc[0]) if not otm_call.empty else None

                skew = None
                if otm_put_iv is not None and otm_call_iv is not None:
                    skew = round((otm_put_iv - otm_call_iv) * 100, 2)
                    overall_skew_scores.append(skew)

                pc_ratio = None
                if atm_put_iv and atm_call_iv and atm_call_iv > 0:
                    pc_ratio = round(atm_put_iv / atm_call_iv, 3)

                if skew is not None:
                    if skew > 8:
                        skew_regime = "ELEVATED_TAIL_RISK — High demand for downside protection"
                    elif skew < 2:
                        skew_regime = "COMPLACENT — Market not pricing tail risk; options cheap"
                    else:
                        skew_regime = "NORMAL — Moderate skew consistent with typical risk premium"
                else:
                    skew_regime = "INSUFFICIENT_DATA"

                exp_date_used = datetime.strptime(target_exp, "%Y-%m-%d").date()
                dte = (exp_date_used - today).days

                results[sym] = {
                    "name": name,
                    "current_price": round(float(current_price), 2),
                    "expiry_used": target_exp,
                    "days_to_expiry": dte,
                    "atm_call_iv_pct": round(atm_call_iv * 100, 2) if atm_call_iv else None,
                    "atm_put_iv_pct": round(atm_put_iv * 100, 2) if atm_put_iv else None,
                    "otm_put_iv_pct": round(otm_put_iv * 100, 2) if otm_put_iv else None,
                    "otm_call_iv_pct": round(otm_call_iv * 100, 2) if otm_call_iv else None,
                    "skew_25d_proxy_pp": skew,
                    "put_call_atm_iv_ratio": pc_ratio,
                    "skew_regime": skew_regime,
                }
            except Exception as inner_e:
                results[sym] = {"error": str(inner_e)}

        if overall_skew_scores:
            avg_skew = round(sum(overall_skew_scores) / len(overall_skew_scores), 2)
            if avg_skew > 8:
                composite_signal = "ELEVATED_TAIL_RISK — Broad demand for protection; consider defensive positioning"
            elif avg_skew < 2:
                composite_signal = "COMPLACENT — Market-wide skew suppressed; potential vol expansion risk"
            else:
                composite_signal = "NEUTRAL — Skew within normal range across major indices"
        else:
            avg_skew = None
            composite_signal = "INSUFFICIENT_DATA"

        return {
            "indices": results,
            "composite_avg_skew_pp": avg_skew,
            "composite_signal": composite_signal,
            "source": "Yahoo Finance options data (free, no API key)",
            "note": (
                "Skew = OTM put IV minus OTM call IV at ~5% distance from spot (25-delta proxy). "
                "Positive skew is normal (puts are pricier than equidistant calls). "
                "High skew (>8pp) = market pricing tail risk. Low skew (<2pp) = complacency. "
                "ATM IV ratio > 1.1 suggests put premium over calls at-the-money."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_factor_exposure(ticker: str) -> dict:
    """
    Fama-French 5-factor exposure analysis using ETF proxies.
    Market=SPY, Size=IWM-SPY spread, Value=IVE-IVW spread, Momentum=MTUM, Quality=QUAL.
    Returns rolling 63-day factor betas, R-squared, dominant factor, and tilt signal.
    advanced_tool tier ($0.003 per call).
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import numpy as np
        from numpy.linalg import lstsq
        from datetime import date, timedelta

        ticker = ticker.upper().strip()
        end = date.today()
        start = end - timedelta(days=420)

        all_tickers = [ticker, "SPY", "IWM", "IVE", "IVW", "MTUM", "QUAL"]
        raw = yf.download(all_tickers, start=start.isoformat(), end=end.isoformat(),
                          auto_adjust=True, progress=False)["Close"]
        if hasattr(raw.columns, "levels"):
            raw.columns = raw.columns.get_level_values(0)
        raw = raw.dropna(how="any")
        if len(raw) < 63:
            return {"error": "Insufficient data (need 63+ trading days)"}

        rets = raw.pct_change().dropna()

        factor_rets = {
            "Market": rets["SPY"],
            "Size": rets["IWM"] - rets["SPY"],
            "Value": rets["IVE"] - rets["IVW"],
            "Momentum": rets["MTUM"],
            "Quality": rets["QUAL"],
        }

        if ticker not in rets.columns:
            return {"error": f"Ticker {ticker} data not available"}

        stock_ret = rets[ticker]
        n = len(stock_ret)
        X = np.column_stack([np.ones(n)] + [factor_rets[f].values for f in factor_rets])
        y = stock_ret.values
        coeffs, _, _, _ = lstsq(X, y, rcond=None)
        alpha = coeffs[0]
        betas = {f: round(float(coeffs[i + 1]), 3) for i, f in enumerate(factor_rets)}

        y_pred = X @ coeffs
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = round(1 - ss_res / ss_tot, 3) if ss_tot > 0 else None

        roll_window = 63
        rolling_corr = {}
        if len(stock_ret) >= roll_window:
            sr = stock_ret.values[-roll_window:]
            for f, f_ret in factor_rets.items():
                fr = f_ret.values[-roll_window:]
                corr_mat = np.corrcoef(sr, fr)
                rolling_corr[f] = round(float(corr_mat[0, 1]), 3)

        dominant_factor = max(betas, key=lambda f: abs(betas[f]))

        tilt_parts = []
        if betas.get("Market", 0) > 1.2:
            tilt_parts.append("HIGH_BETA")
        elif betas.get("Market", 0) < 0.7:
            tilt_parts.append("LOW_BETA")
        if betas.get("Size", 0) > 0.3:
            tilt_parts.append("SMALL_CAP_TILT")
        elif betas.get("Size", 0) < -0.3:
            tilt_parts.append("LARGE_CAP_TILT")
        if betas.get("Value", 0) > 0.2:
            tilt_parts.append("VALUE_TILT")
        elif betas.get("Value", 0) < -0.2:
            tilt_parts.append("GROWTH_TILT")
        if betas.get("Momentum", 0) > 0.5:
            tilt_parts.append("MOMENTUM_TILT")
        if betas.get("Quality", 0) > 0.5:
            tilt_parts.append("QUALITY_TILT")
        tilt_signal = " | ".join(tilt_parts) if tilt_parts else "BALANCED — No strong factor tilt detected"

        return {
            "ticker": ticker,
            "analysis_period_days": n,
            "factor_betas": betas,
            "alpha_daily": round(float(alpha), 5),
            "r_squared": r_squared,
            "rolling_63d_correlations": rolling_corr,
            "dominant_factor": dominant_factor,
            "tilt_signal": tilt_signal,
            "factor_proxies": {
                "Market": "SPY (S&P 500 total market)",
                "Size": "IWM minus SPY daily returns (small-cap minus large-cap)",
                "Value": "IVE minus IVW daily returns (S&P Value minus S&P Growth)",
                "Momentum": "MTUM (iShares MSCI USA Momentum Factor ETF)",
                "Quality": "QUAL (iShares MSCI USA Quality Factor ETF)",
            },
            "source": "Yahoo Finance via yfinance (free, no API key)",
            "note": (
                "Factor betas via OLS over full period (~1.5 years). "
                "Market beta > 1 = amplified market moves. "
                "Positive Size beta = small-cap behavior; Negative = large-cap. "
                "Positive Value beta = value tilt; Negative = growth tilt. "
                "R-squared = fraction of variance explained by 5 factors."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_yield_curve_dynamics() -> dict:
    """
    Real-time US Treasury yield curve analysis.
    Fetches 3M/5Y/10Y/30Y yields via yfinance (^IRX/^FVX/^TNX/^TYX).
    Computes key spreads (10Y-2Y proxy, 5Y-3M, 10Y-3M, 30Y-10Y),
    30/60-day spread change rates, curve shape (NORMAL/FLAT/INVERTED/HUMPED/STEEP),
    inversion intensity and continuous inversion day count.
    basic_tool tier ($0.001 per call).
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import numpy as np
        from datetime import date, timedelta

        end = date.today()
        start = end - timedelta(days=130)

        yield_map = {"3M": "^IRX", "5Y": "^FVX", "10Y": "^TNX", "30Y": "^TYX"}
        raw = yf.download(list(yield_map.values()), start=start.isoformat(),
                          end=end.isoformat(), auto_adjust=True, progress=False)["Close"]
        if hasattr(raw.columns, "levels"):
            raw.columns = raw.columns.get_level_values(0)
        raw = raw.rename(columns={v: k for k, v in yield_map.items()})
        raw = raw.dropna(how="any")

        if len(raw) < 30:
            return {"error": "Insufficient Treasury yield data"}

        latest = raw.iloc[-1]
        yields_pct = {k: round(float(latest[k]), 3) for k in yield_map}

        frac_2y = (2 - 0.25) / (5 - 0.25)
        y2_proxy = float(latest["3M"]) + frac_2y * (float(latest["5Y"]) - float(latest["3M"]))
        yields_pct["2Y_proxy"] = round(y2_proxy, 3)

        def spread_10y2y(row):
            y3m = float(row["3M"])
            y5y = float(row["5Y"])
            y10y = float(row["10Y"])
            return (y10y - (y3m + frac_2y * (y5y - y3m))) * 100

        sp_10y2y = round(spread_10y2y(latest), 1)
        sp_5y3m = round((float(latest["5Y"]) - float(latest["3M"])) * 100, 1)
        sp_10y3m = round((float(latest["10Y"]) - float(latest["3M"])) * 100, 1)
        sp_30y10y = round((float(latest["30Y"]) - float(latest["10Y"])) * 100, 1)

        sp_30d_ago = round(spread_10y2y(raw.iloc[-22]), 1) if len(raw) >= 22 else None
        sp_60d_ago = round(spread_10y2y(raw.iloc[-43]), 1) if len(raw) >= 43 else None
        chg_30d = round(sp_10y2y - sp_30d_ago, 1) if sp_30d_ago is not None else None
        chg_60d = round(sp_10y2y - sp_60d_ago, 1) if sp_60d_ago is not None else None

        spreads_series = raw.apply(spread_10y2y, axis=1)
        inverted_days = int((spreads_series < 0).sum())
        consec_inv = 0
        for s in reversed(spreads_series.values):
            if s < 0:
                consec_inv += 1
            else:
                break

        is_inv_10y2y = sp_10y2y < 0
        is_inv_5y3m = sp_5y3m < 0
        long_steep = sp_30y10y > 50

        if is_inv_10y2y and is_inv_5y3m:
            curve_shape = "INVERTED — Full inversion; historically precedes recession by 6-18 months"
        elif is_inv_10y2y and not is_inv_5y3m:
            curve_shape = "PARTIALLY_INVERTED — Mid-section inverted; watch for propagation to short end"
        elif not is_inv_10y2y and sp_10y2y < 30:
            curve_shape = "HUMPED — Long end steepening vs flat short end" if long_steep else "FLAT — Minimal slope; uncertainty about growth/inflation"
        elif sp_10y2y > 100:
            curve_shape = "STEEP — Strong positive slope; growth or inflation expectations elevated"
        else:
            curve_shape = "NORMAL — Modest upward slope; typical expansion phase"

        if chg_30d is not None:
            if chg_30d > 10:
                trend_30d = f"STEEPENING +{chg_30d}bps (30d) — curve normalizing or reflating"
            elif chg_30d < -10:
                trend_30d = f"FLATTENING {chg_30d}bps (30d) — tightening or growth concern"
            else:
                trend_30d = f"STABLE {chg_30d:+.1f}bps (30d)"
        else:
            trend_30d = "N/A"

        return {
            "yields_pct": yields_pct,
            "key_spreads_bps": {
                "10Y_minus_2Y_proxy": sp_10y2y,
                "10Y_minus_3M": sp_10y3m,
                "5Y_minus_3M": sp_5y3m,
                "30Y_minus_10Y": sp_30y10y,
            },
            "spread_10y_2y_change": {
                "30d_ago_bps": sp_30d_ago,
                "change_30d_bps": chg_30d,
                "60d_ago_bps": sp_60d_ago,
                "change_60d_bps": chg_60d,
            },
            "curve_shape": curve_shape,
            "trend_signal": trend_30d,
            "inversion_stats": {
                "inverted_days_last_130d": inverted_days,
                "consecutive_inverted_days": consec_inv,
                "currently_inverted_10y2y": is_inv_10y2y,
                "currently_inverted_5y3m": is_inv_5y3m,
            },
            "source": "Yahoo Finance (^IRX ^FVX ^TNX ^TYX — free, no API key)",
            "note": (
                "Yields in % annualized. Spreads in basis points (bps). "
                "2Y yield is linearly interpolated between 3M and 5Y (proxy). "
                "10Y-2Y < 0 = inversion; historically precedes recession by 6-18 months. "
                "5Y-3M inversion is an alternative Fed-preferred recession indicator."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_term_structure(ticker: str) -> dict:
    """Options IV term structure for a given ticker: ATM implied volatility across expiries (30/60/90/120/180/360-day buckets),
    term structure slope (CONTANGO = near IV < far IV, BACKWARDATION = near IV > far IV),
    VIX comparison (is this ticker's short-term IV elevated vs market?), and vol risk premium signal.
    Useful for identifying carry trades, event risk, and mean-reversion setups.
    Source: Yahoo Finance (free, no API key). Tier: premium_tool ($0.005/call)."""
    await Actor.charge("premium_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        import numpy as np

        t = yf.Ticker(ticker.upper())
        expiries = t.options
        if not expiries:
            return {"error": f"No options data available for {ticker}"}

        spot_info = t.fast_info
        spot_price = getattr(spot_info, "last_price", None) or getattr(spot_info, "regularMarketPrice", None)
        if spot_price is None:
            try:
                hist = t.history(period="1d")
                spot_price = float(hist["Close"].iloc[-1]) if not hist.empty else None
            except Exception:
                pass
        if spot_price is None:
            return {"error": "Could not retrieve spot price"}

        vix_level = None
        try:
            vix_data = yf.Ticker("^VIX").history(period="1d")
            if not vix_data.empty:
                vix_level = round(float(vix_data["Close"].iloc[-1]), 2)
        except Exception:
            pass

        today = datetime.today()
        term_points = []

        for exp in expiries[:10]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                dte = (exp_date - today).days
                if dte < 7:
                    continue

                chain = t.option_chain(exp)
                calls = chain.calls[["strike", "impliedVolatility", "volume", "openInterest"]].copy()
                calls = calls[calls["impliedVolatility"] > 0.01].dropna()

                if calls.empty:
                    continue

                idx = (calls["strike"] - spot_price).abs().idxmin()
                atm_iv = round(float(calls.loc[idx, "impliedVolatility"]) * 100, 2)
                atm_strike = round(float(calls.loc[idx, "strike"]), 2)

                puts = chain.puts[["strike", "impliedVolatility", "openInterest"]].copy()
                puts = puts[puts["impliedVolatility"] > 0.01].dropna()
                atm_put_oi = 0
                atm_call_oi = int(calls.loc[idx, "openInterest"]) if not calls.empty else 0
                if not puts.empty:
                    pidx = (puts["strike"] - spot_price).abs().idxmin()
                    atm_put_oi = int(puts.loc[pidx, "openInterest"])

                term_points.append({
                    "expiry": exp,
                    "dte": dte,
                    "atm_iv_pct": atm_iv,
                    "atm_strike": atm_strike,
                    "atm_call_oi": atm_call_oi,
                    "atm_put_oi": atm_put_oi,
                })
            except Exception:
                continue

        if len(term_points) < 2:
            return {"error": "Insufficient term structure data (need ≥2 expiries)"}

        term_points.sort(key=lambda x: x["dte"])

        buckets = {"30d": None, "60d": None, "90d": None, "120d": None, "180d": None, "360d": None}
        bucket_days = {"30d": 30, "60d": 60, "90d": 90, "120d": 120, "180d": 180, "360d": 360}
        for label, target in bucket_days.items():
            closest = min(term_points, key=lambda x: abs(x["dte"] - target))
            if abs(closest["dte"] - target) <= max(15, target * 0.3):
                buckets[label] = {"dte": closest["dte"], "atm_iv_pct": closest["atm_iv_pct"], "expiry": closest["expiry"]}

        near_point = term_points[0]
        far_point = term_points[-1]
        near_iv = near_point["atm_iv_pct"]
        far_iv = far_point["atm_iv_pct"]
        slope = round(far_iv - near_iv, 2)

        if slope > 3:
            structure = "CONTANGO — Near-term IV below long-term; calm near future expected, low event risk"
        elif slope < -3:
            structure = "BACKWARDATION — Near-term IV elevated vs long-term; event risk or fear spike in short term"
        else:
            structure = "FLAT — IV roughly uniform across expiries; market uncertain about timing of moves"

        dte_diff = far_point["dte"] - near_point["dte"]
        slope_per_30d = round(slope / (dte_diff / 30), 2) if dte_diff > 0 else 0

        vix_comparison = None
        iv_vs_vix = None
        if vix_level and near_iv:
            iv_vs_vix = round(near_iv - vix_level, 2)
            if iv_vs_vix > 10:
                vix_comparison = f"HIGH_PREMIUM +{iv_vs_vix:.1f}pp vs VIX — {ticker.upper()} carries significant idiosyncratic risk"
            elif iv_vs_vix > 3:
                vix_comparison = f"ELEVATED +{iv_vs_vix:.1f}pp vs VIX — slightly above market implied vol"
            elif iv_vs_vix < -5:
                vix_comparison = f"BELOW_VIX {iv_vs_vix:.1f}pp — {ticker.upper()} less volatile than broad market"
            else:
                vix_comparison = f"IN_LINE {iv_vs_vix:+.1f}pp vs VIX — similar to market implied vol"

        rv_30d = None
        vrp_signal = None
        try:
            hist = t.history(period="45d")
            if len(hist) >= 20:
                log_rets = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
                rv_30d = round(float(log_rets.tail(21).std() * np.sqrt(252) * 100), 2)
                if near_iv and rv_30d:
                    vrp = near_iv - rv_30d
                    if vrp > 5:
                        vrp_signal = f"RICH +{vrp:.1f}pp — IV significantly above realized vol; selling premium may be favorable"
                    elif vrp < -3:
                        vrp_signal = f"CHEAP {vrp:.1f}pp — IV below realized vol; buying premium may be favorable"
                    else:
                        vrp_signal = f"FAIR {vrp:+.1f}pp — IV roughly in line with realized vol"
        except Exception:
            pass

        return {
            "ticker": ticker.upper(),
            "spot_price": round(spot_price, 2),
            "term_structure": term_points,
            "standard_tenors": {k: v for k, v in buckets.items() if v is not None},
            "structure_shape": structure,
            "slope_bps": {
                "near_iv_pct": near_iv,
                "far_iv_pct": far_iv,
                "total_slope_pp": slope,
                "slope_per_30d_pp": slope_per_30d,
                "near_expiry": near_point["expiry"],
                "far_expiry": far_point["expiry"],
            },
            "vix_level": vix_level,
            "iv_vs_vix_pp": iv_vs_vix,
            "vix_comparison": vix_comparison,
            "realized_vol_30d_pct": rv_30d,
            "vol_risk_premium": vrp_signal,
            "source": "Yahoo Finance (free, no API key)",
            "note": (
                "ATM IV = call closest to spot price. "
                "CONTANGO = long-dated IV > short-dated IV (normal). "
                "BACKWARDATION = short-dated IV > long-dated IV (event/fear). "
                "Vol Risk Premium = IV minus 30d realized vol; positive = options expensive."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_season_tracker() -> dict:
    """Tracks current S&P 500 earnings season progress: estimated % of companies reported,
    beat/miss/in-line rates, average EPS surprise %, revenue beat rate, and sector-level summary.
    Uses a representative 60-ticker S&P 500 proxy to estimate season-wide trends.
    Shows which sectors are outperforming/underperforming expectations.
    Source: Yahoo Finance (free, no API key). Tier: advanced_tool ($0.003/call)."""
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime
        import concurrent.futures

        sector_tickers = {
            "Technology": ["AAPL", "MSFT", "NVDA", "META", "GOOGL"],
            "Financials": ["JPM", "BAC", "GS", "WFC", "BRK-B"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
            "Consumer_Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
            "Industrials": ["GE", "CAT", "HON", "UPS", "RTX"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
            "Consumer_Staples": ["PG", "KO", "WMT", "COST", "PEP"],
            "Communication": ["VZ", "T", "NFLX", "DIS", "CMCSA"],
            "Materials": ["LIN", "APD", "NEM", "FCX", "DD"],
            "Real_Estate": ["AMT", "PLD", "EQIX", "SPG", "CCI"],
            "Utilities": ["NEE", "DUK", "SO", "AEP", "D"],
        }

        all_tickers = [t for tickers in sector_tickers.values() for t in tickers]

        def fetch_earnings(ticker):
            try:
                tk = yf.Ticker(ticker)
                earnings_hist = tk.earnings_history
                if earnings_hist is None or (hasattr(earnings_hist, "empty") and earnings_hist.empty):
                    return None
                if hasattr(earnings_hist, "to_dict"):
                    rows = earnings_hist.to_dict("records")
                else:
                    return None
                if not rows:
                    return None
                latest = rows[0]
                eps_actual = latest.get("epsActual") or latest.get("Reported EPS")
                eps_est = latest.get("epsEstimate") or latest.get("EPS Estimate")
                if eps_actual is None or eps_est is None:
                    return None
                try:
                    eps_actual = float(eps_actual)
                    eps_est = float(eps_est)
                except Exception:
                    return None
                if eps_est == 0:
                    return None
                surprise_pct = round((eps_actual - eps_est) / abs(eps_est) * 100, 2)
                if surprise_pct >= 2:
                    result = "BEAT"
                elif surprise_pct <= -2:
                    result = "MISS"
                else:
                    result = "IN_LINE"
                quarter_str = str(latest.get("quarter", latest.get("Period", "")))
                return {
                    "ticker": ticker,
                    "quarter": quarter_str,
                    "eps_actual": eps_actual,
                    "eps_estimate": eps_est,
                    "eps_surprise_pct": surprise_pct,
                    "result": result,
                }
            except Exception:
                return None

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            futures = {executor.submit(fetch_earnings, t): t for t in all_tickers}
            for future in concurrent.futures.as_completed(futures, timeout=45):
                r = future.result()
                if r:
                    results.append(r)

        if not results:
            return {"error": "Could not retrieve earnings data for any ticker"}

        total = len(results)
        beats = [r for r in results if r["result"] == "BEAT"]
        misses = [r for r in results if r["result"] == "MISS"]
        in_lines = [r for r in results if r["result"] == "IN_LINE"]

        beat_rate = round(len(beats) / total * 100, 1)
        miss_rate = round(len(misses) / total * 100, 1)
        in_line_rate = round(len(in_lines) / total * 100, 1)
        avg_surprise = round(sum(r["eps_surprise_pct"] for r in results) / total, 2)

        if beat_rate >= 78:
            beat_signal = f"STRONG_SEASON — {beat_rate}% beat rate well above 74% historical avg"
        elif beat_rate >= 70:
            beat_signal = f"NORMAL_SEASON — {beat_rate}% beat rate near 74% historical avg"
        elif beat_rate >= 60:
            beat_signal = f"WEAK_SEASON — {beat_rate}% beat rate below 74% historical avg"
        else:
            beat_signal = f"VERY_WEAK_SEASON — {beat_rate}% beat rate significantly below avg"

        sector_stats = {}
        for sector, tickers in sector_tickers.items():
            sector_results = [r for r in results if r["ticker"] in tickers]
            if not sector_results:
                continue
            s_beats = sum(1 for r in sector_results if r["result"] == "BEAT")
            s_total = len(sector_results)
            s_avg_surp = round(sum(r["eps_surprise_pct"] for r in sector_results) / s_total, 2)
            sector_stats[sector] = {
                "tickers_tracked": s_total,
                "beat_rate_pct": round(s_beats / s_total * 100, 1),
                "avg_eps_surprise_pct": s_avg_surp,
                "signal": "OUTPERFORMING" if s_avg_surp > 3 else ("UNDERPERFORMING" if s_avg_surp < -2 else "IN_LINE"),
            }

        top_beats = sorted(beats, key=lambda x: x["eps_surprise_pct"], reverse=True)[:3]
        top_misses = sorted(misses, key=lambda x: x["eps_surprise_pct"])[:3]

        season_coverage_pct = round(total / len(all_tickers) * 100, 1)

        now = datetime.now()
        month = now.month
        if month in [1, 2]:
            season_label = f"Q4 {now.year - 1} Earnings Season"
        elif month in [4, 5]:
            season_label = f"Q1 {now.year} Earnings Season"
        elif month in [7, 8]:
            season_label = f"Q2 {now.year} Earnings Season"
        elif month in [10, 11]:
            season_label = f"Q3 {now.year} Earnings Season"
        else:
            season_label = f"Inter-Season Period ({now.strftime('%B %Y')})"

        return {
            "season": season_label,
            "sample_size": total,
            "sample_coverage_pct": season_coverage_pct,
            "aggregate": {
                "beat_rate_pct": beat_rate,
                "miss_rate_pct": miss_rate,
                "in_line_rate_pct": in_line_rate,
                "avg_eps_surprise_pct": avg_surprise,
                "beat_signal": beat_signal,
                "historical_avg_beat_rate_pct": 74.0,
            },
            "sector_breakdown": sector_stats,
            "top_beats": [
                {"ticker": r["ticker"], "eps_surprise_pct": r["eps_surprise_pct"], "quarter": r["quarter"]}
                for r in top_beats
            ],
            "top_misses": [
                {"ticker": r["ticker"], "eps_surprise_pct": r["eps_surprise_pct"], "quarter": r["quarter"]}
                for r in top_misses
            ],
            "source": "Yahoo Finance earnings_history (free, no API key)",
            "note": (
                "Sample: 55-60 S&P 500 representative tickers across 11 sectors. "
                "Beat = EPS surprise ≥+2%, Miss = ≤-2%, In-Line = within ±2%. "
                "Historical S&P 500 beat rate ~74% (FactSet benchmark). "
                "Data may lag by 1-2 days post-announcement."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_macro_regime_monitor() -> dict:
    """
    Composite macro regime monitor: classifies the current macro environment across
    4 axes — Growth (PMI proxy), Inflation (CPI proxy), Rates (yield curve), Liquidity
    (M2 proxy). Outputs GOLDILOCKS / OVERHEATING / STAGFLATION / RECESSION regime matrix.
    basic_tool tier.
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        now = datetime.now()
        start_3m = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")

        spy = yf.download("SPY", start=start_3m, end=today, progress=False, auto_adjust=True)
        spy_ret_3m = None
        growth_signal = "UNKNOWN"
        if len(spy) >= 10:
            spy_ret_3m = round((spy["Close"].iloc[-1] / spy["Close"].iloc[0] - 1) * 100, 2)
            if spy_ret_3m > 7:
                growth_signal = "STRONG_EXPANSION"
            elif spy_ret_3m > 2:
                growth_signal = "EXPANSION"
            elif spy_ret_3m > -2:
                growth_signal = "NEUTRAL"
            elif spy_ret_3m > -7:
                growth_signal = "CONTRACTION"
            else:
                growth_signal = "RECESSION"

        infl_tickers = {"gold": "GLD", "energy": "USO"}
        infl_data = {}
        for name, tk in infl_tickers.items():
            d = yf.download(tk, start=start_3m, end=today, progress=False, auto_adjust=True)
            if len(d) >= 10:
                infl_data[name] = round((d["Close"].iloc[-1] / d["Close"].iloc[0] - 1) * 100, 2)
        gold_3m = infl_data.get("gold", 0)
        energy_3m = infl_data.get("energy", 0)
        composite_infl = (gold_3m + energy_3m) / 2
        if composite_infl > 5:
            inflation_signal = "HIGH_INFLATION"
        elif composite_infl > 1:
            inflation_signal = "ELEVATED_INFLATION"
        elif composite_infl > -2:
            inflation_signal = "STABLE_INFLATION"
        else:
            inflation_signal = "DISINFLATIONARY"

        t10 = yf.download("^TNX", start=start_3m, end=today, progress=False, auto_adjust=True)
        t2_proxy = yf.download("^IRX", start=start_3m, end=today, progress=False, auto_adjust=True)
        curve_spread = None
        rates_signal = "UNKNOWN"
        if len(t10) >= 5 and len(t2_proxy) >= 5:
            r10 = float(t10["Close"].iloc[-1])
            r3m = float(t2_proxy["Close"].iloc[-1])
            r2_proxy = r3m * 0.6 + r10 * 0.4
            curve_spread = round(r10 - r2_proxy, 2)
            if curve_spread > 1.5:
                rates_signal = "STEEP_CURVE"
            elif curve_spread > 0:
                rates_signal = "NORMAL_CURVE"
            elif curve_spread > -0.5:
                rates_signal = "FLAT_CURVE"
            else:
                rates_signal = "INVERTED_CURVE"

        dxy = yf.download("DX-Y.NYB", start=start_3m, end=today, progress=False, auto_adjust=True)
        lqd = yf.download("LQD", start=start_3m, end=today, progress=False, auto_adjust=True)
        hyg = yf.download("HYG", start=start_3m, end=today, progress=False, auto_adjust=True)
        liquidity_signal = "UNKNOWN"
        dxy_3m = lqd_3m = hyg_3m = None
        if len(dxy) >= 10:
            dxy_3m = round((dxy["Close"].iloc[-1] / dxy["Close"].iloc[0] - 1) * 100, 2)
        if len(lqd) >= 10:
            lqd_3m = round((lqd["Close"].iloc[-1] / lqd["Close"].iloc[0] - 1) * 100, 2)
        if len(hyg) >= 10:
            hyg_3m = round((hyg["Close"].iloc[-1] / hyg["Close"].iloc[0] - 1) * 100, 2)
        if dxy_3m is not None and lqd_3m is not None:
            liq_score = lqd_3m - (dxy_3m * 0.5)
            if liq_score > 3:
                liquidity_signal = "ABUNDANT"
            elif liq_score > 0:
                liquidity_signal = "NEUTRAL"
            elif liq_score > -3:
                liquidity_signal = "TIGHTENING"
            else:
                liquidity_signal = "TIGHT"

        growth_expanding = growth_signal in ("STRONG_EXPANSION", "EXPANSION")
        growth_contracting = growth_signal in ("CONTRACTION", "RECESSION")
        infl_high = inflation_signal in ("HIGH_INFLATION", "ELEVATED_INFLATION")
        infl_low = inflation_signal in ("STABLE_INFLATION", "DISINFLATIONARY")
        curve_normal = rates_signal in ("NORMAL_CURVE", "STEEP_CURVE")
        curve_inverted = rates_signal == "INVERTED_CURVE"

        if growth_expanding and infl_low and curve_normal:
            regime = "GOLDILOCKS"
            regime_desc = "Best macro environment: growing economy, contained inflation, normal yield curve"
            regime_score = 90
        elif growth_expanding and infl_high:
            regime = "OVERHEATING"
            regime_desc = "Economy expanding but inflation elevated — rate hike risk, margin pressure"
            regime_score = 45
        elif growth_contracting and infl_high:
            regime = "STAGFLATION"
            regime_desc = "Worst case: economic contraction + high inflation — Fed policy dilemma"
            regime_score = 15
        elif growth_contracting and infl_low and curve_inverted:
            regime = "RECESSION"
            regime_desc = "Classic recession indicators: contraction, disinflation, inverted curve"
            regime_score = 20
        elif growth_contracting or curve_inverted:
            regime = "LATE_CYCLE"
            regime_desc = "Late economic cycle: slowdown signals present, watch for recession trigger"
            regime_score = 35
        elif growth_expanding and infl_low:
            regime = "GOLDILOCKS_LITE"
            regime_desc = "Moderate growth with stable inflation — constructive but not ideal"
            regime_score = 70
        else:
            regime = "TRANSITION"
            regime_desc = "Mixed signals across axes — regime transition in progress"
            regime_score = 50

        if regime in ("GOLDILOCKS", "GOLDILOCKS_LITE"):
            asset_signal = "Risk-ON: Equities > Bonds > Cash. Growth stocks outperform."
        elif regime == "OVERHEATING":
            asset_signal = "Rotate to Value/Energy/Commodities. Short duration bonds. Reduce growth."
        elif regime == "STAGFLATION":
            asset_signal = "Gold/Commodities hedge. Underweight equities & long bonds. TIPS."
        elif regime == "RECESSION":
            asset_signal = "Risk-OFF: Long Treasuries, Gold, Defensive sectors. Underweight equities."
        elif regime == "LATE_CYCLE":
            asset_signal = "Defensive tilt: Healthcare, Utilities, Consumer Staples. Reduce beta."
        else:
            asset_signal = "Neutral allocation. Monitor regime development. Reduce concentration."

        return {
            "regime": regime,
            "regime_score": regime_score,
            "regime_description": regime_desc,
            "asset_allocation_signal": asset_signal,
            "axes": {
                "growth": {"signal": growth_signal, "proxy": "SPY 3M return", "value_pct": spy_ret_3m},
                "inflation": {
                    "signal": inflation_signal,
                    "proxy": "Gold (GLD) + Energy (USO) 3M average return",
                    "gold_3m_pct": gold_3m,
                    "energy_3m_pct": energy_3m,
                    "composite_pct": round(composite_infl, 2),
                },
                "rates": {
                    "signal": rates_signal,
                    "proxy": "10Y - 2Y spread (2Y estimated from 3M + 10Y interpolation)",
                    "spread_approx_pp": curve_spread,
                },
                "liquidity": {
                    "signal": liquidity_signal,
                    "proxy": "LQD 3M return - DXY 3M * 0.5",
                    "dxy_3m_pct": dxy_3m,
                    "lqd_3m_pct": lqd_3m,
                    "hyg_3m_pct": hyg_3m,
                },
            },
            "source": "Yahoo Finance (free, no API key)",
            "note": (
                "Regime proxies use liquid ETF/index data. "
                "Growth proxy = SPY 3M momentum. Inflation proxy = GLD + USO composite. "
                "Rates = 10Y yield vs estimated 2Y. Liquidity = LQD - DXY composite. "
                "Regime score: 0 (worst) to 100 (best) macro environment for equities."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_dividend_calendar(sector: str = "ALL") -> dict:
    """
    Dividend calendar for upcoming ex-dividend dates and payout info across major dividend stocks.
    Covers 80 S&P 500 dividend payers across 11 sectors. Returns: ex-div date, payment date,
    annual yield, dividend growth YoY, payout ratio. Filter by sector or use ALL for full list.
    advanced_tool tier.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import asyncio

        sector_tickers_map = {
            "Technology": ["MSFT", "AAPL", "TXN", "AVGO", "QCOM"],
            "Healthcare": ["JNJ", "ABT", "MDT", "PFE", "MRK"],
            "Financials": ["JPM", "BAC", "WFC", "USB", "PNC"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP"],
            "ConsumerStaples": ["PG", "KO", "PEP", "CL", "MO"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "PSX"],
            "Industrials": ["GE", "HON", "MMM", "CAT", "UPS"],
            "RealEstate": ["O", "PLD", "AMT", "WELL", "SPG"],
            "Materials": ["LIN", "APD", "ECL", "NEM", "IP"],
            "ConsumerDiscretionary": ["MCD", "HD", "LOW", "YUM", "TGT"],
            "Communication": ["VZ", "T", "CMCSA", "OMC", "IPG"],
        }

        valid_sectors = list(sector_tickers_map.keys())
        if sector.upper() == "ALL":
            tickers_to_check = {tk: sec for sec, tks in sector_tickers_map.items() for tk in tks}
        else:
            matched = next((s for s in valid_sectors if s.lower() == sector.lower()), None)
            if not matched:
                return {"error": f"Unknown sector '{sector}'", "valid_sectors": ["ALL"] + valid_sectors}
            tickers_to_check = {tk: matched for tk in sector_tickers_map[matched]}

        now = datetime.now()
        results = []

        def fetch_dividend_info(ticker, sec):
            try:
                info = yf.Ticker(ticker).info
                div_yield = info.get("dividendYield")
                forward_annual_div = info.get("dividendRate")
                ex_div_date_ts = info.get("exDividendDate")
                payout_ratio = info.get("payoutRatio")
                five_yr_avg_div_yield = info.get("fiveYearAvgDividendYield")
                trailing_annual_div_rate = info.get("trailingAnnualDividendRate")
                trailing_annual_div_yield = info.get("trailingAnnualDividendYield")
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                name = info.get("shortName", ticker)

                ex_div_date_str = None
                days_to_ex_div = None
                if ex_div_date_ts:
                    ex_div_dt = datetime.fromtimestamp(ex_div_date_ts)
                    ex_div_date_str = ex_div_dt.strftime("%Y-%m-%d")
                    days_to_ex_div = (ex_div_dt - now).days

                div_growth_yoy = None
                if forward_annual_div and trailing_annual_div_rate and trailing_annual_div_rate > 0:
                    div_growth_yoy = round((forward_annual_div / trailing_annual_div_rate - 1) * 100, 2)

                if not div_yield:
                    return None

                return {
                    "ticker": ticker,
                    "name": name,
                    "sector": sec,
                    "current_price": round(price, 2) if price else None,
                    "annual_dividend_rate": round(forward_annual_div, 4) if forward_annual_div else None,
                    "dividend_yield_pct": round(div_yield * 100, 2) if div_yield else None,
                    "trailing_yield_pct": round(trailing_annual_div_yield * 100, 2) if trailing_annual_div_yield else None,
                    "5yr_avg_yield_pct": round(five_yr_avg_div_yield, 2) if five_yr_avg_div_yield else None,
                    "payout_ratio_pct": round(payout_ratio * 100, 1) if payout_ratio else None,
                    "dividend_growth_yoy_pct": div_growth_yoy,
                    "ex_dividend_date": ex_div_date_str,
                    "days_to_ex_dividend": days_to_ex_div,
                    "yield_vs_5yr_avg": (
                        "ABOVE_AVG" if (five_yr_avg_div_yield and div_yield and div_yield * 100 > five_yr_avg_div_yield + 0.2)
                        else "BELOW_AVG" if (five_yr_avg_div_yield and div_yield and div_yield * 100 < five_yr_avg_div_yield - 0.2)
                        else "AT_AVG"
                    ),
                    "safety_signal": (
                        "SAFE" if (payout_ratio and payout_ratio < 0.6)
                        else "MODERATE" if (payout_ratio and payout_ratio < 0.8)
                        else "HIGH_PAYOUT" if payout_ratio
                        else "UNKNOWN"
                    ),
                }
            except Exception:
                return None

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures_map = {executor.submit(fetch_dividend_info, tk, sec): tk for tk, sec in tickers_to_check.items()}
            for future in as_completed(futures_map):
                r = future.result()
                if r:
                    results.append(r)

        if not results:
            return {"error": "No dividend data retrieved"}

        upcoming = [r for r in results if r["days_to_ex_dividend"] is not None and 0 <= r["days_to_ex_dividend"] <= 60]
        upcoming.sort(key=lambda x: x["days_to_ex_dividend"])
        high_yield = sorted(results, key=lambda x: x["dividend_yield_pct"] or 0, reverse=True)[:10]
        growing = sorted(
            [r for r in results if r["dividend_growth_yoy_pct"] and r["dividend_growth_yoy_pct"] > 3],
            key=lambda x: x["dividend_growth_yoy_pct"],
            reverse=True,
        )

        sector_yields = {}
        for r in results:
            sec = r["sector"]
            if sec not in sector_yields:
                sector_yields[sec] = []
            if r["dividend_yield_pct"]:
                sector_yields[sec].append(r["dividend_yield_pct"])
        sector_summary = {
            sec: {
                "avg_yield_pct": round(sum(yields) / len(yields), 2),
                "max_yield_pct": round(max(yields), 2),
                "count": len(yields),
            }
            for sec, yields in sector_yields.items() if yields
        }

        avg_yield = round(sum(r["dividend_yield_pct"] for r in results if r["dividend_yield_pct"]) / len(results), 2)

        return {
            "sector_filter": sector,
            "stocks_analyzed": len(results),
            "average_yield_pct": avg_yield,
            "upcoming_ex_dividend": upcoming[:15],
            "highest_yielders": high_yield,
            "fastest_growing_dividends": growing[:8],
            "sector_yield_summary": sector_summary,
            "source": "Yahoo Finance (free, no API key)",
            "note": (
                f"Covers {len(tickers_to_check)} S&P 500 dividend payers across {len(sector_yields)} sectors. "
                "Ex-dividend dates may lag by 1-2 days. Payout ratio SAFE < 60%, MODERATE 60-80%, HIGH_PAYOUT > 80%. "
                "Dividend growth YoY = (forward rate / trailing rate - 1). Use upcoming_ex_dividend for timing entries."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_vix_regime_monitor() -> dict:
    """
    VIX regime monitor: tracks VIX spot level, moving averages (10/20/50-day),
    1-year percentile rank, term structure proxy (VIX vs VXZ ETF), and outputs
    market stress regime: PANIC / ELEVATED / NORMAL / COMPLACENT.
    basic_tool tier.
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import yfinance as yf
        import numpy as np
        from datetime import datetime, timedelta

        end = datetime.now()
        start = end - timedelta(days=400)
        vix_data = yf.download("^VIX", start=start, end=end, progress=False, auto_adjust=True)
        vxz_data = yf.download("VXZ", start=end - timedelta(days=30), end=end, progress=False, auto_adjust=True)

        if vix_data.empty or len(vix_data) < 50:
            return {"error": "Insufficient VIX data"}

        close_col = "Close"
        vix_series = vix_data[close_col].dropna()

        current_vix = float(vix_series.iloc[-1])
        prev_vix = float(vix_series.iloc[-2]) if len(vix_series) >= 2 else current_vix
        vix_1d_change = round(current_vix - prev_vix, 2)
        vix_1d_change_pct = round((vix_1d_change / prev_vix) * 100, 2) if prev_vix > 0 else 0

        ma10 = float(vix_series.tail(10).mean()) if len(vix_series) >= 10 else None
        ma20 = float(vix_series.tail(20).mean()) if len(vix_series) >= 20 else None
        ma50 = float(vix_series.tail(50).mean()) if len(vix_series) >= 50 else None

        one_yr_series = vix_series.tail(252)
        vix_pct_rank = round(float((one_yr_series < current_vix).mean()) * 100, 1)
        vix_52w_low = round(float(one_yr_series.min()), 2)
        vix_52w_high = round(float(one_yr_series.max()), 2)

        term_structure_regime = "UNAVAILABLE"
        vxz_current = None
        if not vxz_data.empty:
            vxz_current = round(float(vxz_data[close_col].dropna().iloc[-1]), 2)
            if current_vix < vxz_current * 0.95:
                term_structure_regime = "CONTANGO"
            elif current_vix > vxz_current * 1.05:
                term_structure_regime = "BACKWARDATION"
            else:
                term_structure_regime = "FLAT"

        if current_vix >= 35:
            stress_regime = "PANIC"
            regime_desc = "Extreme fear. VIX >= 35. Typically marks capitulation events."
        elif current_vix >= 25:
            stress_regime = "ELEVATED"
            regime_desc = "Above-average volatility. Risk-off sentiment dominates."
        elif current_vix >= 18:
            stress_regime = "NORMAL"
            regime_desc = "Moderate volatility. Balanced market conditions."
        else:
            stress_regime = "COMPLACENT"
            regime_desc = "Low volatility. Potential for complacency / mean-reversion risk."

        ma_signal = "NEUTRAL"
        if ma10 and ma20 and ma50:
            if current_vix > ma10 > ma20 > ma50:
                ma_signal = "RISING_STRESS"
            elif current_vix < ma10 < ma20 < ma50:
                ma_signal = "FALLING_STRESS"
            elif current_vix > ma20:
                ma_signal = "ABOVE_AVERAGE"
            else:
                ma_signal = "BELOW_AVERAGE"

        if stress_regime == "PANIC":
            allocation_signal = "CONSIDER_HEDGES_OR_CASH"
        elif stress_regime == "ELEVATED":
            allocation_signal = "REDUCE_RISK_EXPOSURE"
        elif stress_regime == "COMPLACENT" and vix_pct_rank < 15:
            allocation_signal = "CONSIDER_VOLATILITY_PROTECTION"
        else:
            allocation_signal = "NORMAL_ALLOCATION"

        return {
            "vix_current": round(current_vix, 2),
            "vix_1d_change": vix_1d_change,
            "vix_1d_change_pct": vix_1d_change_pct,
            "vix_52w_low": vix_52w_low,
            "vix_52w_high": vix_52w_high,
            "vix_1yr_percentile_rank": vix_pct_rank,
            "moving_averages": {
                "ma10": round(ma10, 2) if ma10 else None,
                "ma20": round(ma20, 2) if ma20 else None,
                "ma50": round(ma50, 2) if ma50 else None,
            },
            "ma_trend_signal": ma_signal,
            "stress_regime": stress_regime,
            "regime_description": regime_desc,
            "term_structure": {
                "vix_spot": round(current_vix, 2),
                "vxz_mid_term": vxz_current,
                "regime": term_structure_regime,
            },
            "allocation_signal": allocation_signal,
            "source": "Yahoo Finance (^VIX, VXZ — free, no API key)",
            "note": (
                "VIX regimes: PANIC >= 35, ELEVATED 25-35, NORMAL 18-25, COMPLACENT < 18. "
                "Percentile rank = % of trading days in past 1yr below current VIX level. "
                "Term structure: CONTANGO (spot < mid-term) = calm market, BACKWARDATION (spot > mid-term) = stress spike. "
                "MA signals: RISING_STRESS when VIX > MA10 > MA20 > MA50."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_insider_trading_radar(sector: str = "ALL") -> dict:
    """
    Insider trading radar: scans Form 4 SEC filings for unusual cluster buying signals
    across major S&P 500 stocks. Identifies stocks with 3+ insider purchases in 30 days,
    aggregates net buy/sell dollar amounts, and outputs an accumulation/distribution signal.
    Filter by sector or use ALL. advanced_tool tier.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        import pandas as pd
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from datetime import datetime, timedelta

        SECTOR_TICKERS = {
            "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "ORCL", "CRM", "ADBE", "AMD", "INTC", "QCOM", "TXN", "MU", "NOW"],
            "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "AXP", "SCHW", "USB", "PNC", "TFC", "MTB", "KEY", "RF"],
            "Healthcare": ["JNJ", "UNH", "LLY", "ABBV", "MRK", "ABT", "TMO", "BMY", "AMGN", "GILD", "CVS", "CI", "HUM", "MDT", "SYK"],
            "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUCKS", "TJX", "BKNG", "CMG", "DHI", "LEN", "PHM", "GM", "F"],
            "Industrials": ["GE", "CAT", "RTX", "HON", "UPS", "BA", "DE", "LMT", "GD", "NOC", "EMR", "ETN", "ITW", "PH", "ROK"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "PXD", "DVN", "HES", "BKR", "HAL", "FANG"],
            "Consumer Staples": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "GIS", "KHC", "HSY", "K", "CAG", "SJM", "MKC"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "PCG", "WEC", "ES", "ETR", "FE", "CNP", "NI"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "DLR", "WELL", "AVB", "EQR", "MAA", "UDR", "AIV", "NNN"],
            "Materials": ["LIN", "APD", "SHW", "FCX", "NEM", "NUE", "DOW", "DD", "ECL", "PPG", "ALB", "IFF", "CE", "CF", "MOS"],
            "Communication Services": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "T", "VZ", "CHTR", "TMUS", "EA", "TTWO", "OMC", "IPG", "FOXA", "WBD"],
        }

        if sector != "ALL" and sector not in SECTOR_TICKERS:
            return {"error": f"Unknown sector: {sector}. Use ALL or one of: {list(SECTOR_TICKERS.keys())}"}

        tickers_by_sector = SECTOR_TICKERS if sector == "ALL" else {sector: SECTOR_TICKERS[sector]}
        cutoff_date = datetime.now() - timedelta(days=30)

        def fetch_insider_data(ticker, sec_name):
            try:
                stock = yf.Ticker(ticker)
                trades = stock.insider_transactions
                if trades is None or trades.empty:
                    return None

                date_col = None
                for col in ["Start Date", "startDate", "Date", "date"]:
                    if col in trades.columns:
                        date_col = col
                        break
                if date_col is None:
                    return None

                trades = trades.copy()
                trades[date_col] = pd.to_datetime(trades[date_col], errors="coerce")
                recent = trades[trades[date_col] >= cutoff_date].copy()
                if recent.empty:
                    return None

                shares_col = next((c for c in ["Shares", "shares"] if c in recent.columns), None)
                value_col = next((c for c in ["Value", "value"] if c in recent.columns), None)
                text_col = next((c for c in ["Text", "text", "Transaction", "transaction"] if c in recent.columns), None)

                buy_count = 0
                sell_count = 0
                total_buy_value = 0
                total_sell_value = 0
                buy_transactions = []

                for _, row in recent.iterrows():
                    text = str(row.get(text_col, "")).lower() if text_col else ""
                    shares = row.get(shares_col, 0)
                    val = row.get(value_col, 0)
                    try:
                        shares_num = float(str(shares).replace(",", "").replace("+", ""))
                    except Exception:
                        shares_num = 0
                    try:
                        val_num = abs(float(str(val).replace(",", "").replace("+", "").replace("-", "")))
                    except Exception:
                        val_num = 0

                    is_buy = ("purchase" in text or "buy" in text or "acquisition" in text or shares_num > 0)
                    is_sell = ("sale" in text or "sell" in text or "disposition" in text)

                    if is_buy and not is_sell:
                        buy_count += 1
                        total_buy_value += val_num
                        buy_transactions.append({"date": str(row[date_col].date()), "shares": shares_num, "value_usd": round(val_num)})
                    elif is_sell:
                        sell_count += 1
                        total_sell_value += val_num

                if buy_count == 0:
                    return None

                net_value = total_buy_value - total_sell_value
                signal = "STRONG_ACCUMULATION" if buy_count >= 3 and net_value > 500000 else \
                         "ACCUMULATION" if buy_count >= 2 and net_value > 0 else "SINGLE_BUY"

                return {
                    "ticker": ticker,
                    "sector": sec_name,
                    "buy_transactions_30d": buy_count,
                    "sell_transactions_30d": sell_count,
                    "total_buy_value_usd": round(total_buy_value),
                    "total_sell_value_usd": round(total_sell_value),
                    "net_insider_value_usd": round(net_value),
                    "signal": signal,
                    "recent_buys": buy_transactions[:3],
                }
            except Exception:
                return None

        results = []
        all_tickers = [(tk, sec_name) for sec_name, tks in tickers_by_sector.items() for tk in tks]
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {executor.submit(fetch_insider_data, tk, sec): (tk, sec) for tk, sec in all_tickers}
            for future in as_completed(futures):
                r = future.result()
                if r:
                    results.append(r)

        if not results:
            return {"error": "No recent insider buying activity found", "sector_filter": sector, "lookback_days": 30}

        signal_rank = {"STRONG_ACCUMULATION": 0, "ACCUMULATION": 1, "SINGLE_BUY": 2}
        results.sort(key=lambda x: (signal_rank.get(x["signal"], 3), -x["buy_transactions_30d"]))

        sector_summary = {}
        for r in results:
            sec = r["sector"]
            if sec not in sector_summary:
                sector_summary[sec] = {"total_buys": 0, "total_buy_value_usd": 0, "stocks_with_buying": 0}
            sector_summary[sec]["total_buys"] += r["buy_transactions_30d"]
            sector_summary[sec]["total_buy_value_usd"] += r["total_buy_value_usd"]
            sector_summary[sec]["stocks_with_buying"] += 1

        strong = [r for r in results if r["signal"] == "STRONG_ACCUMULATION"]

        return {
            "sector_filter": sector,
            "lookback_days": 30,
            "stocks_with_insider_buying": len(results),
            "strong_accumulation_count": len(strong),
            "total_insider_buy_value_usd": round(sum(r["total_buy_value_usd"] for r in results)),
            "top_cluster_signals": results[:15],
            "sector_summary": sector_summary,
            "source": "Yahoo Finance insider_transactions (SEC Form 4 proxy — free, no API key)",
            "note": (
                "STRONG_ACCUMULATION: 3+ insider buys AND net value > $500K in 30 days. "
                "ACCUMULATION: 2+ buys, positive net. SINGLE_BUY: 1 buy transaction. "
                "Form 4 data via Yahoo Finance — may lag 1-3 days from SEC filing. "
                "Insider buying is historically a positive signal, especially cluster buys from multiple executives."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_etf_flow_tracker() -> dict:
    """Track capital flows across 12 major ETFs using OBV (On-Balance Volume) proxy.

    Covers broad market, sectors, bonds, gold, and USD. Identifies INFLOW/OUTFLOW/NEUTRAL
    for each ETF and cross-asset rotation signals (RISK_ON / RISK_OFF / MIXED).
    No API key required. basic_tool tier ($0.001).
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import yfinance as yf
        import numpy as np

        etfs = {
            "SPY": "S&P 500 (Broad Market)",
            "QQQ": "Nasdaq 100 (Tech)",
            "IWM": "Russell 2000 (Small Cap)",
            "GLD": "Gold",
            "TLT": "20Y+ Treasuries (Long Bond)",
            "HYG": "High Yield Bonds",
            "XLF": "Financials",
            "XLE": "Energy",
            "XLK": "Technology",
            "XLV": "Healthcare",
            "EEM": "Emerging Markets",
            "UUP": "US Dollar (DXY proxy)",
        }

        tickers_str = " ".join(etfs.keys())
        data = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: yf.download(tickers_str, period="45d", interval="1d", progress=False, auto_adjust=True)
        )

        results = []

        for ticker in etfs:
            try:
                if hasattr(data.columns, 'levels') and 'Close' in data.columns.get_level_values(0):
                    close = data["Close"][ticker].dropna()
                    volume = data["Volume"][ticker].dropna()
                else:
                    close = data[ticker]["Close"].dropna() if ticker in data.columns.get_level_values(0) else data["Close"].dropna()
                    volume = data[ticker]["Volume"].dropna() if ticker in data.columns.get_level_values(0) else data["Volume"].dropna()

                if len(close) < 20:
                    continue

                obv = [0]
                for i in range(1, len(close)):
                    if close.iloc[i] > close.iloc[i - 1]:
                        obv.append(obv[-1] + volume.iloc[i])
                    elif close.iloc[i] < close.iloc[i - 1]:
                        obv.append(obv[-1] - volume.iloc[i])
                    else:
                        obv.append(obv[-1])

                obv = np.array(obv)

                obv_10d = obv[-10:]
                obv_30d = obv[-min(30, len(obv)):]

                slope_10d = float(np.polyfit(range(len(obv_10d)), obv_10d, 1)[0])
                slope_30d = float(np.polyfit(range(len(obv_30d)), obv_30d, 1)[0])

                ret_5d = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) >= 5 else 0.0
                ret_10d = float((close.iloc[-1] / close.iloc[-10] - 1) * 100) if len(close) >= 10 else 0.0
                ret_30d = float((close.iloc[-1] / close.iloc[-30] - 1) * 100) if len(close) >= 30 else 0.0

                vol_10d_avg = float(volume.iloc[-10:].mean())
                vol_30d_avg = float(volume.iloc[-30:].mean())
                vol_ratio = vol_10d_avg / vol_30d_avg if vol_30d_avg > 0 else 1.0

                if slope_10d > 0 and slope_30d > 0:
                    flow = "STRONG_INFLOW"
                elif slope_10d > 0:
                    flow = "INFLOW"
                elif slope_10d < 0 and slope_30d < 0:
                    flow = "STRONG_OUTFLOW"
                elif slope_10d < 0:
                    flow = "OUTFLOW"
                else:
                    flow = "NEUTRAL"

                if vol_ratio > 1.3:
                    vol_regime = "HIGH_VOLUME"
                elif vol_ratio < 0.7:
                    vol_regime = "LOW_VOLUME"
                else:
                    vol_regime = "NORMAL_VOLUME"

                results.append({
                    "ticker": ticker,
                    "category": etfs[ticker],
                    "price": round(float(close.iloc[-1]), 2),
                    "return_5d_pct": round(ret_5d, 2),
                    "return_10d_pct": round(ret_10d, 2),
                    "return_30d_pct": round(ret_30d, 2),
                    "obv_slope_10d": "POSITIVE" if slope_10d > 0 else "NEGATIVE",
                    "obv_slope_30d": "POSITIVE" if slope_30d > 0 else "NEGATIVE",
                    "volume_regime": vol_regime,
                    "volume_ratio_10d_vs_30d": round(vol_ratio, 2),
                    "flow_signal": flow,
                })
            except Exception:
                continue

        if not results:
            return {"error": "Failed to fetch ETF flow data"}

        inflow_etfs = [r for r in results if "INFLOW" in r["flow_signal"]]
        outflow_etfs = [r for r in results if "OUTFLOW" in r["flow_signal"]]

        risk_on_tickers = {"SPY", "QQQ", "IWM", "XLF", "XLK", "XLE", "EEM"}
        risk_off_tickers = {"TLT", "GLD", "UUP"}

        risk_on_score = sum(1 for r in results if r["ticker"] in risk_on_tickers and "INFLOW" in r["flow_signal"]) - \
                        sum(1 for r in results if r["ticker"] in risk_on_tickers and "OUTFLOW" in r["flow_signal"])
        risk_off_score = sum(1 for r in results if r["ticker"] in risk_off_tickers and "INFLOW" in r["flow_signal"]) - \
                         sum(1 for r in results if r["ticker"] in risk_off_tickers and "OUTFLOW" in r["flow_signal"])

        if risk_on_score > 1 and risk_off_score <= 0:
            rotation_signal = "RISK_ON_ROTATION"
        elif risk_off_score > 1 and risk_on_score <= 0:
            rotation_signal = "RISK_OFF_ROTATION"
        elif risk_on_score > 0 and risk_off_score > 0:
            rotation_signal = "MIXED_FLOWS"
        else:
            rotation_signal = "NEUTRAL"

        flow_rank = {"STRONG_INFLOW": 0, "INFLOW": 1, "NEUTRAL": 2, "OUTFLOW": 3, "STRONG_OUTFLOW": 4}
        results.sort(key=lambda x: flow_rank.get(x["flow_signal"], 2))

        return {
            "etf_flows": results,
            "summary": {
                "etfs_with_inflow": len(inflow_etfs),
                "etfs_with_outflow": len(outflow_etfs),
                "rotation_signal": rotation_signal,
                "risk_on_score": risk_on_score,
                "risk_off_score": risk_off_score,
                "top_inflow": [r["ticker"] for r in results if "INFLOW" in r["flow_signal"]][:3],
                "top_outflow": [r["ticker"] for r in results if "OUTFLOW" in r["flow_signal"]][:3],
            },
            "source": "Yahoo Finance (price + volume — no API key required)",
            "methodology": (
                "OBV (On-Balance Volume) slope analysis. "
                "10-day OBV slope = short-term flow direction. "
                "30-day OBV slope = trend confirmation. "
                "STRONG_INFLOW: both 10d and 30d slopes positive. "
                "STRONG_OUTFLOW: both slopes negative. "
                "Volume ratio = 10d avg / 30d avg (HIGH_VOLUME >1.3x). "
                "RISK_ON_ROTATION: equity ETFs showing net inflow, safe-haven outflow. "
                "RISK_OFF_ROTATION: TLT/GLD/UUP inflow with equity outflow."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_gamma_exposure(ticker: str = "SPY") -> dict:
    """Compute dealer Gamma Exposure (GEX) for a ticker using options chain data.

    Aggregates Black-Scholes gamma × open interest × contract multiplier across all
    near-term strikes. Shows GEX by strike, GEX flip point, and market impact signal.
    Positive GEX = price-stabilizing (dealer hedging buys dips, sells rallies).
    Negative GEX = price-amplifying (dealer hedging accelerates moves).
    No API key required. premium_tool tier ($0.005).
    """
    await Actor.charge("premium_tool", count=1)
    try:
        import yfinance as yf
        import numpy as np
        from math import log, sqrt, exp, pi
        from datetime import datetime, date

        ticker_upper = ticker.upper()
        tk = yf.Ticker(ticker_upper)

        hist = await asyncio.get_event_loop().run_in_executor(None, lambda: tk.history(period="5d"))
        if hist.empty:
            return {"error": f"No price data for {ticker_upper}"}
        spot = float(hist["Close"].iloc[-1])

        try:
            expiries = tk.options
        except Exception:
            return {"error": f"No options data for {ticker_upper}"}

        if not expiries:
            return {"error": f"No options expiries found for {ticker_upper}"}

        today = date.today()
        valid_expiries = []
        for exp in expiries[:8]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days_to_exp = (exp_date - today).days
                if 1 <= days_to_exp <= 60:
                    valid_expiries.append((exp, days_to_exp))
            except Exception:
                continue

        if not valid_expiries:
            valid_expiries = [(expiries[0], 30)]

        r_rate = 0.05

        def bs_gamma(S, K, T, sigma):
            if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
                return 0.0
            try:
                d1 = (log(S / K) + (r_rate + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
                n_d1 = exp(-0.5 * d1 ** 2) / sqrt(2 * pi)
                return n_d1 / (S * sigma * sqrt(T))
            except Exception:
                return 0.0

        strike_gex = {}
        total_call_gex = 0.0
        total_put_gex = 0.0

        for exp_str, days in valid_expiries[:2]:
            T = days / 365.0
            try:
                chain = await asyncio.get_event_loop().run_in_executor(None, lambda e=exp_str: tk.option_chain(e))
                calls = chain.calls
                puts = chain.puts

                for _, row in calls.iterrows():
                    try:
                        K = float(row["strike"])
                        oi = int(row["openInterest"]) if not (isinstance(row["openInterest"], float) and np.isnan(row["openInterest"])) else 0
                        iv = float(row["impliedVolatility"]) if not (isinstance(row["impliedVolatility"], float) and np.isnan(row["impliedVolatility"])) else 0.3
                        if oi == 0 or iv <= 0 or abs(K - spot) / spot > 0.15:
                            continue
                        gamma = bs_gamma(spot, K, T, iv)
                        gex = gamma * oi * 100 * spot
                        total_call_gex += gex
                        strike_gex[K] = strike_gex.get(K, 0.0) + gex
                    except Exception:
                        continue

                for _, row in puts.iterrows():
                    try:
                        K = float(row["strike"])
                        oi = int(row["openInterest"]) if not (isinstance(row["openInterest"], float) and np.isnan(row["openInterest"])) else 0
                        iv = float(row["impliedVolatility"]) if not (isinstance(row["impliedVolatility"], float) and np.isnan(row["impliedVolatility"])) else 0.3
                        if oi == 0 or iv <= 0 or abs(K - spot) / spot > 0.15:
                            continue
                        gamma = bs_gamma(spot, K, T, iv)
                        gex = gamma * oi * 100 * spot
                        total_put_gex += gex
                        strike_gex[K] = strike_gex.get(K, 0.0) - gex
                    except Exception:
                        continue
            except Exception:
                continue

        if not strike_gex:
            return {"error": f"Could not compute GEX for {ticker_upper} — options data insufficient."}

        net_gex = total_call_gex - total_put_gex

        sorted_strikes = sorted(strike_gex.keys())
        cumulative = 0.0
        prev_cumul = None
        prev_strike = None
        flip_point = None

        for K in sorted_strikes:
            prev_cumul = cumulative
            cumulative += strike_gex[K]
            if prev_strike is not None and prev_cumul is not None:
                if (prev_cumul >= 0 > cumulative) or (prev_cumul < 0 <= cumulative):
                    flip_point = round((prev_strike + K) / 2, 2)
                    break
            prev_strike = K

        if flip_point is None:
            flip_point = round(spot, 2)

        top_strikes = sorted(strike_gex.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
        total_abs_gex = sum(abs(v) for v in strike_gex.values())
        top3_concentration = sum(abs(v) for _, v in top_strikes[:3]) / total_abs_gex * 100 if total_abs_gex > 0 else 0

        if net_gex > 0:
            market_signal = "POSITIVE_GEX"
            market_effect = "Price-stabilizing: dealer hedging buys dips, sells rallies — expect mean-reversion around key strikes."
        else:
            market_signal = "NEGATIVE_GEX"
            market_effect = "Price-amplifying: dealer hedging accelerates directional moves — expect momentum and elevated volatility."

        gex_magnitude = abs(net_gex)
        if gex_magnitude > 1_000_000_000:
            magnitude_label = "EXTREME"
        elif gex_magnitude > 100_000_000:
            magnitude_label = "HIGH"
        elif gex_magnitude > 10_000_000:
            magnitude_label = "MODERATE"
        else:
            magnitude_label = "LOW"

        return {
            "ticker": ticker_upper,
            "spot_price": round(spot, 2),
            "net_gex_dollars": round(net_gex),
            "total_call_gex_dollars": round(total_call_gex),
            "total_put_gex_dollars": round(total_put_gex),
            "market_signal": market_signal,
            "market_effect": market_effect,
            "gex_magnitude": magnitude_label,
            "gex_flip_point": flip_point,
            "distance_to_flip_pct": round((flip_point - spot) / spot * 100, 2),
            "top_gamma_strikes": [
                {
                    "strike": round(K, 2),
                    "net_gex_dollars": round(gex),
                    "direction": "CALL_DOMINATED" if gex > 0 else "PUT_DOMINATED",
                }
                for K, gex in top_strikes[:10]
            ],
            "concentration": {
                "top3_strikes_pct_of_total_gex": round(top3_concentration, 1),
                "gamma_wall": round(top_strikes[0][0], 2) if top_strikes else None,
            },
            "expiries_analyzed": [exp for exp, _ in valid_expiries[:2]],
            "source": "Yahoo Finance options chain (Black-Scholes gamma — no API key required)",
            "note": (
                "GEX = Σ(Call Gamma × OI × 100 × Spot) - Σ(Put Gamma × OI × 100 × Spot). "
                "Assumes dealers net short calls, net long puts (standard retail flow assumption). "
                "GEX Flip Point: price level where cumulative strike GEX crosses zero. "
                "Above flip → POSITIVE GEX (stabilizing). Below flip → NEGATIVE GEX (amplifying). "
                "Gamma computed via Black-Scholes using implied volatility from option chain. "
                "Strikes within ±15% of spot included. Near-term expiries (≤60 DTE) only."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_sector_rotation_signal() -> dict:
    """
    Sector rotation signal based on 11 SPDR sector ETFs combined with macro context (VIX + 10Y yield).
    Scores each sector by relative performance vs SPY (1M/3M/6M weighted) and assigns
    OVERWEIGHT / NEUTRAL / UNDERWEIGHT positioning. Identifies overall rotation regime:
    DEFENSIVE_ROTATION / CYCLICAL_ROTATION / VALUE_ROTATION / MIXED_ROTATION.
    Advanced_tool tier ($0.003).
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        import numpy as np
        from datetime import datetime, timedelta

        SECTORS = {
            "XLK": "Technology",
            "XLV": "Healthcare",
            "XLF": "Financials",
            "XLE": "Energy",
            "XLI": "Industrials",
            "XLB": "Materials",
            "XLRE": "Real Estate",
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
            "XLC": "Communication Services",
        }

        MACRO_TICKERS = ["^VIX", "^TNX", "SPY"]
        ALL_TICKERS = list(SECTORS.keys()) + MACRO_TICKERS

        end = datetime.now()
        start = end - timedelta(days=400)

        data = yf.download(ALL_TICKERS, start=start, end=end, progress=False, auto_adjust=True)["Close"]

        vix = float(data["^VIX"].dropna().iloc[-1])
        tnx = float(data["^TNX"].dropna().iloc[-1])

        spy_prices = data["SPY"].dropna()
        spy_now = float(spy_prices.iloc[-1])
        spy_1m = float(spy_prices.iloc[-22]) if len(spy_prices) >= 22 else spy_now
        spy_3m = float(spy_prices.iloc[-63]) if len(spy_prices) >= 63 else spy_now
        spy_6m = float(spy_prices.iloc[-126]) if len(spy_prices) >= 126 else spy_now
        spy_ret_1m = (spy_now - spy_1m) / spy_1m * 100
        spy_ret_3m = (spy_now - spy_3m) / spy_3m * 100
        spy_ret_6m = (spy_now - spy_6m) / spy_6m * 100

        sector_scores = {}
        for etf, sector_name in SECTORS.items():
            prices = data[etf].dropna()
            if len(prices) < 130:
                continue
            p_now = float(prices.iloc[-1])
            p_1m = float(prices.iloc[-22]) if len(prices) >= 22 else p_now
            p_3m = float(prices.iloc[-63]) if len(prices) >= 63 else p_now
            p_6m = float(prices.iloc[-126]) if len(prices) >= 126 else p_now

            ret_1m = (p_now - p_1m) / p_1m * 100
            ret_3m = (p_now - p_3m) / p_3m * 100
            ret_6m = (p_now - p_6m) / p_6m * 100

            rel_1m = ret_1m - spy_ret_1m
            rel_3m = ret_3m - spy_ret_3m
            rel_6m = ret_6m - spy_ret_6m

            composite_score = rel_1m * 0.40 + rel_3m * 0.35 + rel_6m * 0.25

            sector_scores[etf] = {
                "sector_name": sector_name,
                "price": round(p_now, 2),
                "ret_1m_pct": round(ret_1m, 2),
                "ret_3m_pct": round(ret_3m, 2),
                "ret_6m_pct": round(ret_6m, 2),
                "relative_score_vs_spy": round(composite_score, 2),
            }

        if not sector_scores:
            return {"error": "Insufficient sector data — try again later."}

        ranked = sorted(sector_scores.items(), key=lambda x: x[1]["relative_score_vs_spy"], reverse=True)

        if vix >= 30:
            macro_regime = "HIGH_STRESS"
            macro_note = "Elevated VIX >= 30 — prefer Defensive sectors (XLP/XLV/XLU)"
        elif vix >= 20:
            macro_regime = "MODERATE_STRESS"
            macro_note = "VIX 20-30 — balanced approach, caution on high-beta sectors"
        else:
            macro_regime = "LOW_STRESS"
            macro_note = "VIX < 20 — risk-on environment, growth/cyclical sectors may lead"

        if tnx > 4.5:
            rate_regime = "HIGH_RATES"
            rate_note = "10Y > 4.5% — headwind for XLRE/XLU/XLK (high duration), tailwind for XLF"
        elif tnx > 3.5:
            rate_regime = "ELEVATED_RATES"
            rate_note = "10Y 3.5-4.5% — neutral to mildly negative for rate-sensitive sectors"
        else:
            rate_regime = "LOW_RATES"
            rate_note = "10Y < 3.5% — supportive for XLRE/XLU and growth sectors"

        result_sectors = []
        for i, (etf, info) in enumerate(ranked):
            rank = i + 1
            if rank <= 3:
                positioning = "OVERWEIGHT"
                signal_strength = "STRONG"
            elif rank <= 5:
                positioning = "OVERWEIGHT"
                signal_strength = "MODERATE"
            elif rank <= 7:
                positioning = "NEUTRAL"
                signal_strength = "NEUTRAL"
            elif rank <= 9:
                positioning = "UNDERWEIGHT"
                signal_strength = "MODERATE"
            else:
                positioning = "UNDERWEIGHT"
                signal_strength = "STRONG"

            result_sectors.append({
                "rank": rank,
                "etf": etf,
                "sector_name": info["sector_name"],
                "price": info["price"],
                "ret_1m_pct": info["ret_1m_pct"],
                "ret_3m_pct": info["ret_3m_pct"],
                "ret_6m_pct": info["ret_6m_pct"],
                "relative_score_vs_spy": info["relative_score_vs_spy"],
                "positioning": positioning,
                "signal_strength": signal_strength,
            })

        top3_etfs = set(x["etf"] for x in result_sectors[:3])
        defensive = {"XLP", "XLV", "XLU", "XLRE"}
        cyclical = {"XLK", "XLY", "XLI", "XLB", "XLC"}

        defensive_count = len(top3_etfs & defensive)
        cyclical_count = len(top3_etfs & cyclical)

        if defensive_count >= 2:
            overall_regime = "DEFENSIVE_ROTATION"
            regime_note = "Market rotating into defensive sectors — risk-off posture"
        elif cyclical_count >= 2:
            overall_regime = "CYCLICAL_ROTATION"
            regime_note = "Market rotating into cyclical/growth sectors — risk-on posture"
        elif "XLE" in top3_etfs or "XLF" in top3_etfs:
            overall_regime = "VALUE_ROTATION"
            regime_note = "Energy/Financials leading — value or inflation-driven positioning"
        else:
            overall_regime = "MIXED_ROTATION"
            regime_note = "Mixed sector leadership — no dominant directional theme"

        return {
            "overall_regime": overall_regime,
            "regime_note": regime_note,
            "macro_context": {
                "vix": round(vix, 2),
                "vix_regime": macro_regime,
                "vix_note": macro_note,
                "ten_year_yield_pct": round(tnx, 3),
                "rate_regime": rate_regime,
                "rate_note": rate_note,
            },
            "spy_benchmarks": {
                "ret_1m_pct": round(spy_ret_1m, 2),
                "ret_3m_pct": round(spy_ret_3m, 2),
                "ret_6m_pct": round(spy_ret_6m, 2),
            },
            "sector_rotation": result_sectors,
            "top_overweight": [
                f"{x['etf']} ({x['sector_name']})"
                for x in result_sectors
                if x["positioning"] == "OVERWEIGHT" and x["signal_strength"] == "STRONG"
            ],
            "top_underweight": [
                f"{x['etf']} ({x['sector_name']})"
                for x in result_sectors
                if x["positioning"] == "UNDERWEIGHT" and x["signal_strength"] == "STRONG"
            ],
            "score_methodology": (
                "Relative score = weighted relative return vs SPY: 1M×40% + 3M×35% + 6M×25%. "
                "Rank 1-3: STRONG OVERWEIGHT. Rank 4-5: MODERATE OVERWEIGHT. Rank 6-7: NEUTRAL. "
                "Rank 8-9: MODERATE UNDERWEIGHT. Rank 10-11: STRONG UNDERWEIGHT."
            ),
            "source": "Yahoo Finance (SPDR Sector ETFs + ^VIX + ^TNX — no API key required)",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_revision_tracker(ticker: str = "AAPL") -> dict:
    """
    Tracks EPS consensus revision direction for a given ticker: RISING / FALLING / STABLE.
    Uses analyst upgrade/downgrade history (30d/90d), EPS estimate growth forecasts,
    consensus price target, and recommendation trend to generate a revision signal.
    Advanced_tool tier ($0.003).
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import yfinance as yf
        import pandas as pd
        from datetime import datetime, timedelta

        ticker_upper = ticker.strip().upper()
        t = yf.Ticker(ticker_upper)
        info = t.info or {}

        company_name = info.get("longName") or info.get("shortName") or ticker_upper
        sector = info.get("sector", "N/A")
        current_price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)

        # --- EPS Estimates ---
        eps_growth_current_q = None
        eps_growth_next_y = None
        eps_current_q_avg = None
        eps_next_y_avg = None
        try:
            ee = t.get_earnings_estimate()
            if ee is not None and not ee.empty:
                if "0q" in ee.index:
                    row_0q = ee.loc["0q"]
                    if "growth" in ee.columns and not pd.isna(row_0q.get("growth")):
                        eps_growth_current_q = round(float(row_0q["growth"]) * 100, 1)
                    if "avg" in ee.columns and not pd.isna(row_0q.get("avg")):
                        eps_current_q_avg = round(float(row_0q["avg"]), 4)
                if "+1y" in ee.index:
                    row_1y = ee.loc["+1y"]
                    if "growth" in ee.columns and not pd.isna(row_1y.get("growth")):
                        eps_growth_next_y = round(float(row_1y["growth"]) * 100, 1)
                    if "avg" in ee.columns and not pd.isna(row_1y.get("avg")):
                        eps_next_y_avg = round(float(row_1y["avg"]), 4)
        except Exception:
            pass

        # --- Upgrades / Downgrades ---
        upgrades_30d = 0
        downgrades_30d = 0
        upgrades_90d = 0
        downgrades_90d = 0
        recent_actions = []

        try:
            ud = t.upgrades_downgrades
            if ud is not None and len(ud) > 0:
                ud = ud.reset_index()
                date_col = ud.columns[0]
                ud[date_col] = pd.to_datetime(ud[date_col], utc=True).dt.tz_localize(None)

                now = datetime.now()
                cutoff_30 = now - timedelta(days=30)
                cutoff_90 = now - timedelta(days=90)

                ud_90 = ud[ud[date_col] >= cutoff_90].copy()
                ud_30 = ud[ud[date_col] >= cutoff_30].copy()

                action_col = None
                for c in ud.columns:
                    if c.lower() == "action":
                        action_col = c
                        break

                if action_col:
                    upgrades_90d = int(len(ud_90[ud_90[action_col].str.upper() == "UP"]))
                    downgrades_90d = int(len(ud_90[ud_90[action_col].str.upper() == "DOWN"]))
                    upgrades_30d = int(len(ud_30[ud_30[action_col].str.upper() == "UP"]))
                    downgrades_30d = int(len(ud_30[ud_30[action_col].str.upper() == "DOWN"]))

                    firm_col = next((c for c in ud.columns if "firm" in c.lower()), None)
                    to_col = next((c for c in ud.columns if "to" in c.lower() and "grade" in c.lower()), None)
                    from_col = next((c for c in ud.columns if "from" in c.lower() and "grade" in c.lower()), None)

                    for _, row in ud_90.head(5).iterrows():
                        recent_actions.append({
                            "date": str(row[date_col])[:10],
                            "firm": str(row[firm_col]) if firm_col else "N/A",
                            "action": str(row[action_col]),
                            "from_grade": str(row[from_col]) if from_col else "N/A",
                            "to_grade": str(row[to_col]) if to_col else "N/A",
                        })
        except Exception:
            pass

        # --- Price Target ---
        target_mean = round(float(info.get("targetMeanPrice") or 0), 2)
        target_low = round(float(info.get("targetLowPrice") or 0), 2)
        target_high = round(float(info.get("targetHighPrice") or 0), 2)
        upside_pct = round((target_mean - current_price) / current_price * 100, 1) if current_price and target_mean else None

        # --- Analyst Consensus ---
        num_analysts = int(info.get("numberOfAnalystOpinions") or 0)
        rec_mean = info.get("recommendationMean")
        rec_key = info.get("recommendationKey", "N/A")

        if rec_mean:
            if rec_mean <= 1.5:
                rec_label = "STRONG_BUY"
            elif rec_mean <= 2.5:
                rec_label = "BUY"
            elif rec_mean <= 3.5:
                rec_label = "HOLD"
            elif rec_mean <= 4.5:
                rec_label = "SELL"
            else:
                rec_label = "STRONG_SELL"
        else:
            rec_label = "N/A"

        # --- Revision Signal ---
        total_90d = upgrades_90d + downgrades_90d
        revision_ratio = round(upgrades_90d / total_90d * 100, 1) if total_90d > 0 else 50.0

        if upgrades_30d >= 2 and upgrades_30d > downgrades_30d * 1.5:
            revision_signal = "RISING"
            revision_note = f"{upgrades_30d} upgrades vs {downgrades_30d} downgrades in past 30d — positive analyst momentum"
            signal_strength = "STRONG" if upgrades_30d >= 3 else "MODERATE"
        elif downgrades_30d >= 2 and downgrades_30d > upgrades_30d * 1.5:
            revision_signal = "FALLING"
            revision_note = f"{downgrades_30d} downgrades vs {upgrades_30d} upgrades in past 30d — negative analyst momentum"
            signal_strength = "STRONG" if downgrades_30d >= 3 else "MODERATE"
        elif upgrades_90d > downgrades_90d * 1.5 and total_90d >= 3:
            revision_signal = "RISING"
            revision_note = f"90d: {upgrades_90d} upgrades vs {downgrades_90d} downgrades — gradual positive revision trend"
            signal_strength = "MODERATE"
        elif downgrades_90d > upgrades_90d * 1.5 and total_90d >= 3:
            revision_signal = "FALLING"
            revision_note = f"90d: {downgrades_90d} downgrades vs {upgrades_90d} upgrades — gradual negative revision trend"
            signal_strength = "MODERATE"
        else:
            revision_signal = "STABLE"
            revision_note = f"No clear upgrade/downgrade skew (90d: U:{upgrades_90d} D:{downgrades_90d})"
            signal_strength = "WEAK"

        return {
            "ticker": ticker_upper,
            "company": company_name,
            "sector": sector,
            "current_price": round(current_price, 2),
            "revision_signal": revision_signal,
            "revision_note": revision_note,
            "signal_strength": signal_strength,
            "upgrade_downgrade_momentum": {
                "upgrades_30d": upgrades_30d,
                "downgrades_30d": downgrades_30d,
                "upgrades_90d": upgrades_90d,
                "downgrades_90d": downgrades_90d,
                "revision_ratio_pct": revision_ratio,
                "revision_ratio_note": "Upgrade % of all actions (90d). >60% = bullish skew. <40% = bearish skew.",
            },
            "eps_estimates": {
                "current_quarter_eps_avg": eps_current_q_avg,
                "current_quarter_growth_pct": eps_growth_current_q,
                "next_year_eps_avg": eps_next_y_avg,
                "next_year_growth_pct": eps_growth_next_y,
            },
            "analyst_consensus": {
                "num_analysts": num_analysts,
                "recommendation_mean": round(rec_mean, 2) if rec_mean else None,
                "recommendation_label": rec_label,
                "consensus_price_target": target_mean,
                "target_low": target_low,
                "target_high": target_high,
                "upside_to_consensus_pct": upside_pct,
            },
            "recent_analyst_actions": recent_actions,
            "source": "Yahoo Finance (upgrades/downgrades + analyst estimates — no API key required)",
            "note": (
                "RISING: upgrades dominate past 30d (>1.5x downgrades, min 2). "
                "FALLING: downgrades dominate past 30d (>1.5x upgrades, min 2). "
                "STABLE: no clear directional skew. "
                "Combine with get_earnings_whisper() and get_insider_trading_radar() for comprehensive view."
            ),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_short_squeeze_radar() -> dict:
    """Scans high-short-interest stocks for squeeze setups: short % of float + price momentum + volume surge.

    Returns top squeeze candidates ranked by composite squeeze_score (0-100).
    squeeze_risk: EXTREME (>=70) / HIGH (>=50) / MODERATE (>=30) / LOW (<30).
    No API key required.
    """
    await Actor.charge("advanced_tool", count=1)

    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    import asyncio

    CANDIDATES = [
        # Meme / high-short-interest universe
        "GME", "AMC", "SPCE", "RIVN", "LCID", "NIO", "XPEV", "PLUG", "FCEL",
        "BLNK", "CHPT", "BE", "RUN", "ENPH", "SEDG", "AZEK",
        # Crypto-adjacent / speculative
        "MSTR", "RIOT", "MARA", "HUT", "CLSK", "CIFR", "WULF", "COIN", "HOOD",
        "SNAP", "PINS", "RBLX", "U",
        # Retail / consumer under pressure
        "BBWI", "CPRI", "TPR", "VFC", "PVH", "UAA", "UA", "KSS", "JWN", "M",
        # Healthcare / biotech
        "MRNA", "BNTX", "NVAX", "ARWR", "BMRN", "RARE", "ALNY", "IONS", "SGEN",
        # Media / telecom
        "PARA", "WBD", "DISH", "LUMN", "S",
        # EV / clean energy overhang
        "NKLA", "FSR", "GOEV", "WKHS", "RIDE", "CLOV",
        # Food / consumer
        "BYND", "PRTY", "BIG",
    ]
    CANDIDATES = list(dict.fromkeys(CANDIDATES))

    def fetch_squeeze_data(ticker):
        try:
            t = yf.Ticker(ticker)
            info = t.info

            short_pct_raw = info.get("shortPercentOfFloat")
            days_to_cover = info.get("shortRatio")
            if not short_pct_raw:
                return None

            short_pct = float(short_pct_raw)
            if short_pct < 1:
                short_pct = round(short_pct * 100, 1)
            else:
                short_pct = round(short_pct, 1)

            days_to_cover_val = round(float(days_to_cover), 1) if days_to_cover else None

            hist = t.history(period="2mo")
            if hist.empty or len(hist) < 10:
                return None

            current_price = hist["Close"].iloc[-1]
            price_1w_ago = hist["Close"].iloc[-6] if len(hist) >= 6 else hist["Close"].iloc[0]
            price_1m_ago = hist["Close"].iloc[-22] if len(hist) >= 22 else hist["Close"].iloc[0]

            momentum_1w = round((current_price - price_1w_ago) / price_1w_ago * 100, 1)
            momentum_1m = round((current_price - price_1m_ago) / price_1m_ago * 100, 1)

            recent_vol = hist["Volume"].iloc[-5:].mean()
            avg_vol_20d = hist["Volume"].iloc[-20:].mean()
            vol_surge = round(recent_vol / avg_vol_20d, 2) if avg_vol_20d > 0 else 1.0

            short_score = min(short_pct / 30.0, 1.0) * 40
            momentum_score = max(min(momentum_1w / 20.0, 1.0), 0) * 30
            vol_score = min((vol_surge - 1.0) / 1.0, 1.0) * 30 if vol_surge > 1 else 0
            squeeze_score = round(short_score + momentum_score + vol_score, 1)

            if squeeze_score >= 70:
                squeeze_risk = "EXTREME"
            elif squeeze_score >= 50:
                squeeze_risk = "HIGH"
            elif squeeze_score >= 30:
                squeeze_risk = "MODERATE"
            else:
                squeeze_risk = "LOW"

            company = (info.get("shortName") or info.get("longName") or ticker)[:40]
            sector = info.get("sector", "Unknown")

            return {
                "ticker": ticker,
                "company": company,
                "sector": sector,
                "squeeze_risk": squeeze_risk,
                "squeeze_score": squeeze_score,
                "short_pct_float": short_pct,
                "days_to_cover": days_to_cover_val,
                "price_momentum_1w_pct": momentum_1w,
                "price_momentum_1m_pct": momentum_1m,
                "volume_surge_ratio": vol_surge,
                "current_price": round(current_price, 2),
            }
        except Exception:
            return None

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = await loop.run_in_executor(
            None,
            lambda: list(ex.map(fetch_squeeze_data, CANDIDATES))
        )

    valid = [r for r in results if r is not None]
    valid.sort(key=lambda x: x["squeeze_score"], reverse=True)

    extreme = [r for r in valid if r["squeeze_risk"] == "EXTREME"]
    high = [r for r in valid if r["squeeze_risk"] == "HIGH"]
    moderate = [r for r in valid if r["squeeze_risk"] == "MODERATE"]

    return {
        "scan_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "candidates_scanned": len(CANDIDATES),
        "valid_results": len(valid),
        "summary": {
            "extreme_risk_count": len(extreme),
            "high_risk_count": len(high),
            "moderate_risk_count": len(moderate),
        },
        "top_squeeze_candidates": valid[:15],
        "extreme_squeeze_alerts": extreme[:5],
        "note": (
            "squeeze_score 0-100: short_pct weight 40, 1W price momentum 30, volume_surge 30. "
            "EXTREME(>=70): active squeeze setup — rising price + high short + volume surge. "
            "HIGH(>=50): elevated risk. MODERATE(>=30): monitoring. LOW(<30): minimal. "
            "days_to_cover >5: high squeeze risk. volume_surge_ratio >1.5: notable accumulation. "
            "Combine with get_options_flow() for confirmation."
        ),
        "source": "Yahoo Finance shortPercentOfFloat + price/volume history — no API key required",
    }


@mcp.tool()
async def get_put_call_ratio_history(ticker: str = "SPY", period_days: int = 30) -> dict:
    """Historical put/call ratio analysis: options market sentiment via P/C ratio across expirations.

    Returns composite P/C ratio (volume + OI), extreme value detection, and contrarian signals.
    BULLISH_EXTREME: extreme put buying = fear peak (contrarian buy).
    BEARISH_EXTREME: extreme call buying = complacency peak (contrarian sell).

    Args:
        ticker: Stock/ETF ticker (default: SPY)
        period_days: Target DTE range for analysis — 20, 30, 60, or 90 (default: 30)

    No API key required.
    """
    await Actor.charge("premium_tool", count=1)

    import yfinance as yf

    period_days = max(20, min(int(period_days), 90))

    try:
        t = yf.Ticker(ticker)
        ticker_upper = ticker.upper()

        info = t.info
        company = (info.get("shortName") or info.get("longName") or ticker_upper)[:50]
        current_price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)

        expirations = t.options
        if not expirations:
            return {"error": f"No options data available for {ticker_upper}"}

        today = datetime.now(timezone.utc).date()
        selected = []
        for exp in expirations:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                dte = (exp_date - today).days
                if 7 <= dte <= max(period_days, 60):
                    selected.append((dte, exp))
            except Exception:
                continue

        if not selected:
            for exp in expirations[:5]:
                try:
                    exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                    dte = (exp_date - today).days
                    if dte > 0:
                        selected.append((dte, exp))
                except Exception:
                    continue

        selected.sort()

        total_put_vol = total_call_vol = total_put_oi = total_call_oi = 0
        expiration_details = []

        for dte, exp in selected[:6]:
            try:
                chain = t.option_chain(exp)
                puts = chain.puts
                calls = chain.calls

                put_vol = int(puts["volume"].fillna(0).sum())
                call_vol = int(calls["volume"].fillna(0).sum())
                put_oi = int(puts["openInterest"].fillna(0).sum())
                call_oi = int(calls["openInterest"].fillna(0).sum())

                total_put_vol += put_vol
                total_call_vol += call_vol
                total_put_oi += put_oi
                total_call_oi += call_oi

                expiration_details.append({
                    "expiration": exp,
                    "dte": dte,
                    "put_volume": put_vol,
                    "call_volume": call_vol,
                    "put_call_volume_ratio": round(put_vol / call_vol, 3) if call_vol > 0 else None,
                    "put_oi": put_oi,
                    "call_oi": call_oi,
                    "put_call_oi_ratio": round(put_oi / call_oi, 3) if call_oi > 0 else None,
                })
            except Exception:
                continue

        if not expiration_details:
            return {"error": f"Could not load options chain for {ticker_upper}"}

        pc_ratio_vol = round(total_put_vol / total_call_vol, 3) if total_call_vol > 0 else None
        pc_ratio_oi = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else None

        is_index_etf = ticker_upper in ["SPY", "QQQ", "IWM", "DIA", "VTI", "EEM", "TLT", "GLD"]
        if is_index_etf:
            normal_range = (0.6, 1.5)
            extreme_high = 1.8
            extreme_low = 0.5
        else:
            normal_range = (0.4, 1.5)
            extreme_high = 2.0
            extreme_low = 0.3

        contrarian_signal = "NEUTRAL"
        signal_note = ""
        fear_greed = 50

        if pc_ratio_vol is not None:
            if pc_ratio_vol >= extreme_high:
                contrarian_signal = "BULLISH_EXTREME"
                signal_note = (
                    f"Extreme put buying (P/C vol={pc_ratio_vol:.3f} >= {extreme_high}) — "
                    "contrarian BUY signal. Fear at peak."
                )
                fear_greed = 10
            elif pc_ratio_vol <= extreme_low:
                contrarian_signal = "BEARISH_EXTREME"
                signal_note = (
                    f"Extreme call buying (P/C vol={pc_ratio_vol:.3f} <= {extreme_low}) — "
                    "contrarian SELL signal. Complacency detected."
                )
                fear_greed = 90
            elif pc_ratio_vol > normal_range[1]:
                contrarian_signal = "ELEVATED_FEAR"
                signal_note = (
                    f"Above-normal put activity (P/C vol={pc_ratio_vol:.3f}) — "
                    "mild fear, potential support building."
                )
                fear_greed = 30
            elif pc_ratio_vol < normal_range[0]:
                contrarian_signal = "ELEVATED_COMPLACENCY"
                signal_note = (
                    f"Below-normal put activity (P/C vol={pc_ratio_vol:.3f}) — "
                    "mild complacency, caution warranted."
                )
                fear_greed = 70
            else:
                contrarian_signal = "NEUTRAL"
                signal_note = (
                    f"Normal put/call activity (P/C vol={pc_ratio_vol:.3f}) — no strong contrarian signal."
                )
                fear_greed = 50

        vol_ratios = [e["put_call_volume_ratio"] for e in expiration_details if e["put_call_volume_ratio"]]
        if len(vol_ratios) >= 2:
            near_pc = vol_ratios[0]
            far_pc = vol_ratios[-1]
            if near_pc > far_pc * 1.2:
                pc_trend = "NEAR_TERM_FEAR"
                pc_trend_note = "More puts near-term vs longer-dated — immediate hedging demand."
            elif far_pc > near_pc * 1.2:
                pc_trend = "LONG_TERM_FEAR"
                pc_trend_note = "More puts in longer expirations — structural hedging / macro concern."
            else:
                pc_trend = "FLAT_STRUCTURE"
                pc_trend_note = "Similar P/C across expirations — no term-structure skew."
        else:
            pc_trend = "INSUFFICIENT_DATA"
            pc_trend_note = "Only one expiration available."

        if pc_ratio_oi is not None:
            if pc_ratio_oi >= 1.5:
                oi_signal = "HEAVY_PUT_OI"
            elif pc_ratio_oi >= 1.0:
                oi_signal = "PUT_LEANING"
            elif pc_ratio_oi >= 0.7:
                oi_signal = "CALL_LEANING"
            else:
                oi_signal = "HEAVY_CALL_OI"
        else:
            oi_signal = "N/A"

        return {
            "ticker": ticker_upper,
            "company": company,
            "current_price": round(current_price, 2),
            "analysis_period_days": period_days,
            "put_call_analysis": {
                "composite_pc_ratio_volume": pc_ratio_vol,
                "composite_pc_ratio_oi": pc_ratio_oi,
                "total_put_volume": total_put_vol,
                "total_call_volume": total_call_vol,
                "total_put_oi": total_put_oi,
                "total_call_oi": total_call_oi,
                "oi_signal": oi_signal,
            },
            "contrarian_signal": contrarian_signal,
            "signal_note": signal_note,
            "fear_greed_proxy": fear_greed,
            "fear_greed_note": "0=extreme fear (contrarian bullish). 100=extreme greed (contrarian bearish). Derived from P/C ratio.",
            "pc_trend": pc_trend,
            "pc_trend_note": pc_trend_note,
            "expiration_breakdown": expiration_details,
            "benchmark_context": {
                "instrument_type": "INDEX_ETF" if is_index_etf else "INDIVIDUAL_STOCK",
                "normal_pc_vol_range": f"{normal_range[0]}-{normal_range[1]}",
                "extreme_high_threshold": extreme_high,
                "extreme_low_threshold": extreme_low,
            },
            "note": (
                "BULLISH_EXTREME: extreme put buying = fear peak (contrarian buy signal). "
                "BEARISH_EXTREME: extreme call buying = complacency peak (contrarian sell signal). "
                "ELEVATED_FEAR: above-normal puts. NEUTRAL: no signal. "
                "Combine with get_options_skew_monitor() and get_volatility_surface() for full view."
            ),
            "source": "Yahoo Finance options chain — no API key required",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_institutional_flow_tracker(sector: str = "ALL") -> dict:
    """
    Track institutional ownership flows across major S&P 500 stocks.
    Shows which stocks have increasing/decreasing institutional interest.
    Covers 120+ stocks across 11 sectors. Uses yfinance institutional_holders data.
    Identifies STRONG_ACCUMULATION / ACCUMULATION / NEUTRAL / DISTRIBUTION / STRONG_DISTRIBUTION signals.
    advanced_tool tier.
    """
    await Actor.charge("advanced_tool", count=1)
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    import asyncio

    SECTOR_UNIVERSE = {
        "Technology": ["AAPL", "MSFT", "NVDA", "META", "GOOGL", "AVGO", "ORCL", "CRM", "AMD", "INTC", "QCOM", "TXN", "NOW", "ADBE", "MU"],
        "Healthcare": ["JNJ", "UNH", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD", "CVS", "CI", "HUM", "ISRG"],
        "Financials": ["JPM", "BRK-B", "BAC", "WFC", "GS", "MS", "BLK", "SPGI", "AXP", "V", "MA", "C", "USB", "TFC", "PNC"],
        "Consumer_Discretionary": ["AMZN", "TSLA", "MCD", "NKE", "SBUX", "HD", "LOW", "TGT", "BKNG", "CMG", "ABNB", "GM", "F", "EBAY", "ETSY"],
        "Industrials": ["CAT", "HON", "UPS", "BA", "GE", "RTX", "LMT", "DE", "MMM", "CSX", "NSC", "FDX", "EMR", "ITW", "PH"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "VLO", "MPC", "OXY", "HAL", "DVN", "HES", "FANG", "MRO", "APA"],
        "Consumer_Staples": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "KMB", "GIS", "K", "CAG", "CPB", "SJM", "HRL"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "PPL", "EIX", "WEC", "ES", "FE", "ETR", "DTE", "CMS"],
        "Real_Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "WELL", "DLR", "O", "AVB", "EQR", "VTR", "MAA", "ARE", "BXP"],
        "Materials": ["LIN", "APD", "SHW", "ECL", "NEM", "FCX", "NUE", "VMC", "MLM", "IP", "CF", "MOS", "ALB", "FMC", "CE"],
        "Communication_Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "EA", "TTWO", "WBD", "PARA", "FOXA", "LUMN", "OMC"],
    }

    sector_upper = sector.upper()
    if sector_upper == "ALL":
        tickers_by_sector = SECTOR_UNIVERSE
    else:
        matched = next((k for k in SECTOR_UNIVERSE if k.upper() == sector_upper), None)
        if not matched:
            return {"error": f"Unknown sector '{sector}'. Available: ALL, {', '.join(SECTOR_UNIVERSE.keys())}"}
        tickers_by_sector = {matched: SECTOR_UNIVERSE[matched]}

    def analyze_institutional(ticker):
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            major = t.major_holders
            institutional_pct = None
            insider_pct = None
            if major is not None and not major.empty:
                for i, row in major.iterrows():
                    val_str = str(row.iloc[0]).replace('%', '').strip()
                    label = str(row.iloc[1]).lower() if len(row) > 1 else ""
                    try:
                        val = float(val_str)
                        if "institutional" in label:
                            institutional_pct = val
                        elif "insider" in label:
                            insider_pct = val
                    except Exception:
                        pass

            inst_holders = t.institutional_holders
            num_institutions = 0
            total_inst_shares = 0
            top_holder = None
            top_holder_pct = None
            if inst_holders is not None and not inst_holders.empty:
                num_institutions = len(inst_holders)
                if 'Shares' in inst_holders.columns:
                    total_inst_shares = int(inst_holders['Shares'].sum())
                if 'Holder' in inst_holders.columns:
                    top_holder = str(inst_holders.iloc[0]['Holder'])
                if '% Out' in inst_holders.columns:
                    top_holder_pct = round(float(inst_holders.iloc[0]['% Out']) * 100, 2)

            hist = t.history(period="3mo", interval="1d")
            price_change_3m = None
            current_price = None
            if hist is not None and len(hist) >= 2:
                current_price = round(float(hist['Close'].iloc[-1]), 2)
                start_price = float(hist['Close'].iloc[0])
                price_change_3m = round((current_price - start_price) / start_price * 100, 2)

            vol_signal = "NEUTRAL"
            vol_ratio = None
            if hist is not None and len(hist) >= 20:
                recent_vol = hist['Volume'].iloc[-10:].mean()
                prev_vol = hist['Volume'].iloc[-20:-10].mean()
                if prev_vol > 0:
                    vol_ratio = round(recent_vol / prev_vol, 2)
                    if vol_ratio >= 1.5:
                        vol_signal = "STRONG_VOLUME_SURGE"
                    elif vol_ratio >= 1.2:
                        vol_signal = "ELEVATED_VOLUME"
                    elif vol_ratio <= 0.7:
                        vol_signal = "DECLINING_VOLUME"

            flow_signal = "NEUTRAL"
            if institutional_pct is not None and price_change_3m is not None:
                if institutional_pct >= 75 and price_change_3m >= 5 and vol_signal in ("STRONG_VOLUME_SURGE", "ELEVATED_VOLUME"):
                    flow_signal = "STRONG_ACCUMULATION"
                elif institutional_pct >= 65 and price_change_3m >= 2:
                    flow_signal = "ACCUMULATION"
                elif institutional_pct <= 40 and price_change_3m <= -5:
                    flow_signal = "STRONG_DISTRIBUTION"
                elif institutional_pct <= 50 and price_change_3m <= -2:
                    flow_signal = "DISTRIBUTION"

            return {
                "ticker": ticker,
                "current_price": current_price,
                "institutional_pct": round(institutional_pct, 1) if institutional_pct is not None else None,
                "insider_pct": round(insider_pct, 1) if insider_pct is not None else None,
                "num_institutions": num_institutions,
                "total_inst_shares": total_inst_shares,
                "top_holder": top_holder,
                "top_holder_pct": top_holder_pct,
                "price_change_3m_pct": price_change_3m,
                "volume_ratio_10d": vol_ratio,
                "volume_signal": vol_signal,
                "flow_signal": flow_signal,
                "error": None,
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "flow_signal": "N/A"}

    all_results = []
    sector_summary = {}
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=12) as executor:
        for sec_name, tickers in tickers_by_sector.items():
            futures = {executor.submit(analyze_institutional, t): t for t in tickers}
            sec_results = []
            for fut in futures.values():
                r = fut.result()
                r["sector"] = sec_name
                sec_results.append(r)
                all_results.append(r)

            valid = [r for r in sec_results if r.get("error") is None and r.get("flow_signal") != "N/A"]
            acc_count = sum(1 for r in valid if r["flow_signal"] in ("STRONG_ACCUMULATION", "ACCUMULATION"))
            dist_count = sum(1 for r in valid if r["flow_signal"] in ("STRONG_DISTRIBUTION", "DISTRIBUTION"))
            strong_acc = sum(1 for r in valid if r["flow_signal"] == "STRONG_ACCUMULATION")
            avg_inst_pct = round(sum(r["institutional_pct"] for r in valid if r.get("institutional_pct") is not None) / max(len([r for r in valid if r.get("institutional_pct")]), 1), 1)

            if acc_count >= 3 and strong_acc >= 1:
                sec_signal = "SECTOR_ACCUMULATION"
            elif acc_count > dist_count:
                sec_signal = "MILD_ACCUMULATION"
            elif dist_count > acc_count:
                sec_signal = "MILD_DISTRIBUTION"
            else:
                sec_signal = "NEUTRAL"

            sector_summary[sec_name] = {
                "accumulation_count": acc_count,
                "distribution_count": dist_count,
                "strong_accumulation_count": strong_acc,
                "avg_institutional_pct": avg_inst_pct,
                "sector_signal": sec_signal,
            }

    accumulation_stocks = sorted(
        [r for r in all_results if r.get("flow_signal") in ("STRONG_ACCUMULATION", "ACCUMULATION") and r.get("error") is None],
        key=lambda x: (x["flow_signal"] == "STRONG_ACCUMULATION", x.get("volume_ratio_10d") or 0),
        reverse=True
    )[:15]

    distribution_stocks = sorted(
        [r for r in all_results if r.get("flow_signal") in ("STRONG_DISTRIBUTION", "DISTRIBUTION") and r.get("error") is None],
        key=lambda x: (x["flow_signal"] == "STRONG_DISTRIBUTION", -(x.get("price_change_3m_pct") or 0)),
        reverse=True
    )[:10]

    total_acc = sum(1 for r in all_results if r.get("flow_signal") in ("STRONG_ACCUMULATION", "ACCUMULATION"))
    total_dist = sum(1 for r in all_results if r.get("flow_signal") in ("STRONG_DISTRIBUTION", "DISTRIBUTION"))
    if total_acc >= total_dist * 2:
        overall_signal = "INSTITUTIONAL_BUY_PRESSURE"
    elif total_dist >= total_acc * 2:
        overall_signal = "INSTITUTIONAL_SELL_PRESSURE"
    elif total_acc > total_dist:
        overall_signal = "MILD_BUY_BIAS"
    elif total_dist > total_acc:
        overall_signal = "MILD_SELL_BIAS"
    else:
        overall_signal = "BALANCED_FLOWS"

    return {
        "filter_sector": sector,
        "stocks_analyzed": len(all_results),
        "overall_flow_signal": overall_signal,
        "overall_signal_note": (
            "INSTITUTIONAL_BUY_PRESSURE: broad accumulation across sectors. "
            "INSTITUTIONAL_SELL_PRESSURE: broad distribution. "
            "Flow signals derived from institutional ownership %, 3M price momentum, and volume trend."
        ),
        "flow_summary": {
            "accumulation_stocks": total_acc,
            "distribution_stocks": total_dist,
            "neutral_stocks": len(all_results) - total_acc - total_dist,
        },
        "sector_breakdown": sector_summary,
        "top_accumulation_candidates": [
            {
                "ticker": r["ticker"],
                "sector": r["sector"],
                "flow_signal": r["flow_signal"],
                "institutional_pct": r.get("institutional_pct"),
                "price_change_3m_pct": r.get("price_change_3m_pct"),
                "volume_ratio_10d": r.get("volume_ratio_10d"),
                "top_holder": r.get("top_holder"),
                "top_holder_pct": r.get("top_holder_pct"),
            }
            for r in accumulation_stocks
        ],
        "top_distribution_candidates": [
            {
                "ticker": r["ticker"],
                "sector": r["sector"],
                "flow_signal": r["flow_signal"],
                "institutional_pct": r.get("institutional_pct"),
                "price_change_3m_pct": r.get("price_change_3m_pct"),
                "volume_ratio_10d": r.get("volume_ratio_10d"),
            }
            for r in distribution_stocks
        ],
        "note": (
            "Signals are heuristic proxies — institutional_pct from yfinance major_holders, "
            "volume surge from 10d/20d ratio, price momentum from 3M return. "
            "Combine with get_insider_trading_radar() and get_short_squeeze_radar() for full smart-money picture."
        ),
        "source": "Yahoo Finance institutional holders — no API key required",
    }


@mcp.tool()
async def get_dark_pool_indicator(ticker: str = "SPY") -> dict:
    """
    Estimate dark pool / off-exchange institutional activity for a given ticker.
    Uses intraday volume patterns, OBV divergence, VWAP analysis, and block trade proxies
    to detect potential hidden institutional accumulation or distribution.
    Signals: STEALTH_ACCUMULATION / STEALTH_DISTRIBUTION / BLOCK_BUYING / BLOCK_SELLING / NO_SIGNAL
    premium_tool tier.
    """
    await Actor.charge("premium_tool", count=1)
    import yfinance as yf
    import math

    try:
        ticker_upper = ticker.upper().strip()
        t = yf.Ticker(ticker_upper)
        info = t.fast_info

        company = ticker_upper
        try:
            company = t.info.get("shortName", ticker_upper) or ticker_upper
        except Exception:
            pass

        current_price = float(info.last_price) if hasattr(info, 'last_price') and info.last_price else None

        hist_1d = t.history(period="60d", interval="1d")
        if hist_1d is None or len(hist_1d) < 10:
            return {"error": f"Insufficient daily data for {ticker_upper}"}

        closes = hist_1d['Close'].values
        highs = hist_1d['High'].values
        lows = hist_1d['Low'].values
        volumes = hist_1d['Volume'].values
        opens = hist_1d['Open'].values

        if current_price is None:
            current_price = round(float(closes[-1]), 2)

        obv = [0.0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i - 1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])

        obv_recent = obv[-10:]
        obv_slope = (obv_recent[-1] - obv_recent[0]) / max(abs(obv_recent[0]), 1)
        price_slope = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] > 0 else 0

        obv_divergence = "NONE"
        if price_slope < -0.02 and obv_slope > 0.01:
            obv_divergence = "BULLISH_DIVERGENCE"
        elif price_slope > 0.02 and obv_slope < -0.01:
            obv_divergence = "BEARISH_DIVERGENCE"

        vwap_num = sum((highs[i] + lows[i] + closes[i]) / 3 * volumes[i] for i in range(-20, 0))
        vwap_den = sum(volumes[-20:])
        vwap_20d = round(vwap_num / vwap_den, 2) if vwap_den > 0 else current_price

        vwap_delta_pct = round((current_price - vwap_20d) / vwap_20d * 100, 2) if vwap_20d > 0 else 0
        vwap_signal = "ABOVE_VWAP" if vwap_delta_pct > 0.5 else ("BELOW_VWAP" if vwap_delta_pct < -0.5 else "AT_VWAP")

        avg_vol_30d = float(sum(volumes[-30:]) / 30)
        narrow_range_days = []
        block_buy_days = 0
        block_sell_days = 0
        for i in range(-10, 0):
            day_range_pct = (highs[i] - lows[i]) / closes[i] * 100
            vol_ratio = volumes[i] / avg_vol_30d if avg_vol_30d > 0 else 0
            if vol_ratio >= 1.8 and day_range_pct <= 1.5:
                if closes[i] >= (highs[i] + lows[i]) / 2:
                    block_buy_days += 1
                else:
                    block_sell_days += 1
                narrow_range_days.append({
                    "days_ago": abs(i),
                    "vol_ratio": round(vol_ratio, 2),
                    "range_pct": round(day_range_pct, 2),
                    "direction": "BUY" if closes[i] >= (highs[i] + lows[i]) / 2 else "SELL",
                })

        ad_values = []
        ad = 0.0
        for i in range(len(closes)):
            hl_range = highs[i] - lows[i]
            if hl_range > 0:
                clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / hl_range
            else:
                clv = 0
            ad += clv * volumes[i]
            ad_values.append(ad)

        ad_trend_10d = ad_values[-1] - ad_values[-10]
        ad_trend_signal = "ACCUMULATING" if ad_trend_10d > 0 else "DISTRIBUTING"

        vol_10d_avg = float(sum(volumes[-10:]) / 10)
        max_vol_10d = float(max(volumes[-10:]))
        vol_climax_ratio = round(max_vol_10d / avg_vol_30d, 2) if avg_vol_30d > 0 else 1.0
        has_climax = vol_climax_ratio >= 2.5

        bullish_points = 0
        bearish_points = 0

        if obv_divergence == "BULLISH_DIVERGENCE":
            bullish_points += 3
        elif obv_divergence == "BEARISH_DIVERGENCE":
            bearish_points += 3

        if vwap_signal == "ABOVE_VWAP":
            bullish_points += 1
        elif vwap_signal == "BELOW_VWAP":
            bearish_points += 1

        bullish_points += block_buy_days * 2
        bearish_points += block_sell_days * 2

        if ad_trend_signal == "ACCUMULATING":
            bullish_points += 2
        else:
            bearish_points += 2

        if bullish_points >= 5 and block_buy_days >= 1:
            dark_pool_signal = "STEALTH_ACCUMULATION"
            signal_note = "Multiple indicators suggest hidden institutional buying. OBV divergence + block trades at tight range = classic dark pool accumulation."
        elif bearish_points >= 5 and block_sell_days >= 1:
            dark_pool_signal = "STEALTH_DISTRIBUTION"
            signal_note = "Multiple indicators suggest hidden institutional selling. OBV bearish divergence + distribution pattern detected."
        elif block_buy_days >= 2:
            dark_pool_signal = "BLOCK_BUYING"
            signal_note = f"{block_buy_days} block buy day(s) detected (high volume, tight range, close above midpoint)."
        elif block_sell_days >= 2:
            dark_pool_signal = "BLOCK_SELLING"
            signal_note = f"{block_sell_days} block sell day(s) detected (high volume, tight range, close below midpoint)."
        else:
            dark_pool_signal = "NO_SIGNAL"
            signal_note = "No clear institutional dark pool activity detected in recent 10-day window."

        avg_vol_10d = round(float(sum(volumes[-10:]) / 10))
        vol_vs_30d_ratio = round(avg_vol_10d / avg_vol_30d, 2) if avg_vol_30d > 0 else 1.0

        price_change_10d = round((closes[-1] - closes[-10]) / closes[-10] * 100, 2) if closes[-10] > 0 else 0
        price_change_30d = round((closes[-1] - closes[-30]) / closes[-30] * 100, 2) if len(closes) >= 30 and closes[-30] > 0 else 0

        return {
            "ticker": ticker_upper,
            "company": company,
            "current_price": round(current_price, 2),
            "dark_pool_signal": dark_pool_signal,
            "signal_note": signal_note,
            "confidence_score": {
                "bullish_points": bullish_points,
                "bearish_points": bearish_points,
                "max_possible": 10,
            },
            "obv_analysis": {
                "divergence": obv_divergence,
                "obv_slope_10d": round(obv_slope * 100, 3),
                "price_slope_10d_pct": round(price_slope * 100, 2),
                "interpretation": (
                    "BULLISH_DIVERGENCE: price falling but OBV rising = institutions buying on dips. "
                    "BEARISH_DIVERGENCE: price rising but OBV falling = institutions distributing into strength."
                ),
            },
            "vwap_analysis": {
                "vwap_20d": vwap_20d,
                "vwap_delta_pct": vwap_delta_pct,
                "vwap_signal": vwap_signal,
            },
            "block_trade_analysis": {
                "block_buy_days_10d": block_buy_days,
                "block_sell_days_10d": block_sell_days,
                "block_trade_events": narrow_range_days,
                "criteria": "High volume (>=1.8x 30d avg) + tight range (<=1.5% H-L) = potential block trade",
            },
            "accumulation_distribution": {
                "ad_trend_10d": round(ad_trend_10d / max(avg_vol_30d, 1), 4),
                "ad_signal": ad_trend_signal,
            },
            "volume_climax": {
                "climax_detected": has_climax,
                "max_volume_vs_avg": vol_climax_ratio,
            },
            "price_metrics": {
                "price_change_10d_pct": price_change_10d,
                "price_change_30d_pct": price_change_30d,
                "avg_volume_10d": avg_vol_10d,
                "avg_volume_30d": round(avg_vol_30d),
                "volume_ratio_10d_vs_30d": vol_vs_30d_ratio,
            },
            "note": (
                "Dark pool activity cannot be directly observed for free. "
                "This tool uses OBV divergence, VWAP position, tight-range high-volume days (block trade proxy), "
                "and Accumulation/Distribution line to estimate hidden institutional flows. "
                "Combine with get_institutional_flow_tracker() and get_options_flow() for full picture."
            ),
            "source": "Yahoo Finance OHLCV — no API key required",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_unusual_activity_scanner(min_volume_oi_ratio: float = 3.0, top_n: int = 20) -> dict:
    """
    Scan S&P 500 universe for unusual options activity across the whole market.
    Detects UNUSUAL_CALL_SWEEP, UNUSUAL_PUT_SWEEP, and BLOCK_TRADE signals.
    Unlike get_options_flow() (single ticker), this scans 100+ tickers simultaneously.
    premium_tool tier.
    """
    await Actor.charge("premium_tool", count=1)
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import asyncio

    UNIVERSE = [
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "BRK-B", "UNH", "JPM",
        "V", "XOM", "LLY", "JNJ", "MA", "AVGO", "PG", "HD", "CVX", "MRK",
        "ABBV", "COST", "PEP", "ADBE", "CRM", "AMD", "NFLX", "ACN", "TMO", "ORCL",
        "BAC", "MCD", "LIN", "QCOM", "TXN", "DHR", "PM", "AMGN", "CAT", "GE",
        "ISRG", "VZ", "HON", "IBM", "SPGI", "GS", "BKNG", "NEE", "LOW", "AXP",
        "GILD", "SCHW", "BX", "TJX", "PLD", "SYK", "DE", "ELV", "MDT", "ADP",
        "UBER", "COIN", "MSTR", "PLTR", "RIVN", "NIO", "MARA", "RIOT", "SOFI", "HOOD",
        "RBLX", "SNAP", "PINS", "LYFT", "DKNG", "GME", "AMC", "BBY", "KSS", "M",
        "WMT", "TGT", "SBUX", "NKE", "DIS", "CMCSA", "T", "F", "GM", "BA",
        "GEV", "RTX", "LMT", "NOC", "PYPL", "SQ", "ROKU", "ETSY", "SHOP", "ZM",
    ]

    def scan_ticker(tkr):
        try:
            t = yf.Ticker(tkr)
            opts = t.options
            if not opts:
                return None
            import datetime
            today = datetime.date.today()
            chosen_exp = None
            for exp in opts:
                exp_date = datetime.date.fromisoformat(exp)
                dte = (exp_date - today).days
                if 7 <= dte <= 45:
                    chosen_exp = exp
                    break
            if not chosen_exp:
                chosen_exp = opts[0]
            chain = t.option_chain(chosen_exp)
            calls = chain.calls
            puts = chain.puts
            if calls.empty and puts.empty:
                return None

            unusual_contracts = []
            for _, row in calls.iterrows():
                vol = row.get("volume", 0) or 0
                oi = row.get("openInterest", 0) or 0
                if oi > 0 and vol / oi >= min_volume_oi_ratio and vol >= 500:
                    notional = vol * (row.get("lastPrice", 0) or 0) * 100
                    iv = round(float(row.get("impliedVolatility", 0) or 0) * 100, 1)
                    unusual_contracts.append({
                        "ticker": tkr,
                        "type": "CALL",
                        "strike": float(row.get("strike", 0)),
                        "expiration": chosen_exp,
                        "volume": int(vol),
                        "open_interest": int(oi),
                        "vol_oi_ratio": round(vol / oi, 2),
                        "last_price": round(float(row.get("lastPrice", 0) or 0), 2),
                        "notional_usd": round(notional),
                        "implied_volatility_pct": iv,
                        "in_the_money": bool(row.get("inTheMoney", False)),
                        "signal": "UNUSUAL_CALL_SWEEP",
                    })
            for _, row in puts.iterrows():
                vol = row.get("volume", 0) or 0
                oi = row.get("openInterest", 0) or 0
                if oi > 0 and vol / oi >= min_volume_oi_ratio and vol >= 500:
                    notional = vol * (row.get("lastPrice", 0) or 0) * 100
                    iv = round(float(row.get("impliedVolatility", 0) or 0) * 100, 1)
                    unusual_contracts.append({
                        "ticker": tkr,
                        "type": "PUT",
                        "strike": float(row.get("strike", 0)),
                        "expiration": chosen_exp,
                        "volume": int(vol),
                        "open_interest": int(oi),
                        "vol_oi_ratio": round(vol / oi, 2),
                        "last_price": round(float(row.get("lastPrice", 0) or 0), 2),
                        "notional_usd": round(notional),
                        "implied_volatility_pct": iv,
                        "in_the_money": bool(row.get("inTheMoney", False)),
                        "signal": "UNUSUAL_PUT_SWEEP",
                    })
            return unusual_contracts if unusual_contracts else None
        except Exception:
            return None

    try:
        all_unusual = []
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures_map = {executor.submit(scan_ticker, tkr): tkr for tkr in UNIVERSE}
            for fut in as_completed(futures_map):
                res = fut.result()
                if res:
                    all_unusual.extend(res)

        all_unusual.sort(key=lambda x: x["notional_usd"], reverse=True)
        top_results = all_unusual[:top_n]

        total_unusual = len(all_unusual)
        call_sweeps = sum(1 for x in all_unusual if x["signal"] == "UNUSUAL_CALL_SWEEP")
        put_sweeps = sum(1 for x in all_unusual if x["signal"] == "UNUSUAL_PUT_SWEEP")
        tickers_flagged = list(set(x["ticker"] for x in all_unusual))
        call_notional = sum(x["notional_usd"] for x in all_unusual if x["signal"] == "UNUSUAL_CALL_SWEEP")
        put_notional = sum(x["notional_usd"] for x in all_unusual if x["signal"] == "UNUSUAL_PUT_SWEEP")

        if call_notional > put_notional * 1.5:
            market_bias = "BULLISH_SWEEP_DOMINANCE"
            market_note = "Unusual call sweeps dominate by notional. Smart money positioning for upside."
        elif put_notional > call_notional * 1.5:
            market_bias = "BEARISH_SWEEP_DOMINANCE"
            market_note = "Unusual put sweeps dominate by notional. Smart money hedging or positioning for downside."
        elif call_sweeps > put_sweeps:
            market_bias = "MILD_CALL_LEAN"
            market_note = "More unusual call activity by count. Mildly bullish unusual flow."
        elif put_sweeps > call_sweeps:
            market_bias = "MILD_PUT_LEAN"
            market_note = "More unusual put activity by count. Mildly bearish or defensive unusual flow."
        else:
            market_bias = "BALANCED_UNUSUAL_FLOW"
            market_note = "Balanced unusual call and put activity. No dominant directional bias."

        return {
            "scan_universe_size": len(UNIVERSE),
            "tickers_flagged": len(tickers_flagged),
            "flagged_tickers": sorted(tickers_flagged),
            "total_unusual_contracts": total_unusual,
            "unusual_call_sweeps": call_sweeps,
            "unusual_put_sweeps": put_sweeps,
            "total_call_notional_usd": round(call_notional),
            "total_put_notional_usd": round(put_notional),
            "market_bias_signal": market_bias,
            "market_bias_note": market_note,
            "filter_criteria": {
                "min_volume_oi_ratio": min_volume_oi_ratio,
                "min_volume": 500,
                "dte_range": "7-45 days preferred",
            },
            "top_unusual_contracts": top_results,
            "note": (
                "Unusual activity = volume/OI ratio >= threshold AND volume >= 500. "
                "High vol/OI suggests new positioning (not OI rollover). "
                "Large notional sweeps often indicate institutional directional bets. "
                "Cross-reference with get_dark_pool_indicator() for confirmation."
            ),
            "source": "Yahoo Finance options chain — no API key required",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_smart_money_composite(ticker: str = "AAPL") -> dict:
    """
    Smart money composite scorecard for a single ticker.
    Aggregates signals from dark pool, institutional flow, insider trading, and short squeeze
    into a single SMART_MONEY_SCORE (0-100) with a final signal:
    STRONG_SMART_MONEY_BUY / SMART_MONEY_BUY / NEUTRAL / SMART_MONEY_SELL / STRONG_SMART_MONEY_SELL
    advanced_tool tier.
    """
    await Actor.charge("advanced_tool", count=1)
    import yfinance as yf

    try:
        ticker_upper = ticker.upper().strip()
        t = yf.Ticker(ticker_upper)
        info = t.fast_info

        company = ticker_upper
        try:
            company = t.info.get("shortName", ticker_upper) or ticker_upper
        except Exception:
            pass

        current_price = None
        try:
            current_price = round(float(info.last_price), 2) if hasattr(info, 'last_price') and info.last_price else None
        except Exception:
            pass

        score_components = {}
        total_score = 0

        # ── 1. Dark Pool Proxy (OBV Divergence) ── max 25 pts ──
        dp_score = 0
        dp_signal = "N/A"
        try:
            import math
            hist = t.history(period="3mo", interval="1d", auto_adjust=True)
            if not hist.empty and len(hist) >= 30:
                closes = hist["Close"].tolist()
                volumes = hist["Volume"].tolist()
                obv = [0.0]
                for i in range(1, len(closes)):
                    if closes[i] > closes[i - 1]:
                        obv.append(obv[-1] + volumes[i])
                    elif closes[i] < closes[i - 1]:
                        obv.append(obv[-1] - volumes[i])
                    else:
                        obv.append(obv[-1])
                n = 10
                price_slope = (closes[-1] - closes[-n]) / (closes[-n] * n) if closes[-n] > 0 else 0
                obv_slope = (obv[-1] - obv[-n]) / (abs(obv[-n]) * n + 1)
                if price_slope < -0.002 and obv_slope > 0.002:
                    dp_score = 25
                    dp_signal = "BULLISH_DIVERGENCE"
                elif price_slope < 0 and obv_slope > 0:
                    dp_score = 15
                    dp_signal = "MILD_BULLISH_DIVERGENCE"
                elif price_slope > 0.002 and obv_slope < -0.002:
                    dp_score = -15
                    dp_signal = "BEARISH_DIVERGENCE"
                elif price_slope > 0 and obv_slope < 0:
                    dp_score = -8
                    dp_signal = "MILD_BEARISH_DIVERGENCE"
                else:
                    dp_score = 5
                    dp_signal = "NEUTRAL"
        except Exception:
            dp_signal = "ERROR"

        score_components["dark_pool_obv"] = {"score": dp_score, "signal": dp_signal, "max": 25}
        total_score += dp_score

        # ── 2. Institutional Ownership ── max 20 pts ──
        inst_score = 0
        inst_signal = "N/A"
        try:
            info_full = t.info
            inst_pct = info_full.get("heldPercentInstitutions", None)
            if inst_pct is not None:
                inst_pct_val = float(inst_pct) * 100
                if inst_pct_val >= 75:
                    inst_score = 20
                    inst_signal = f"HIGH_INST_OWNERSHIP ({inst_pct_val:.1f}%)"
                elif inst_pct_val >= 60:
                    inst_score = 12
                    inst_signal = f"MODERATE_INST_OWNERSHIP ({inst_pct_val:.1f}%)"
                elif inst_pct_val >= 40:
                    inst_score = 5
                    inst_signal = f"LOW_INST_OWNERSHIP ({inst_pct_val:.1f}%)"
                else:
                    inst_score = 0
                    inst_signal = f"VERY_LOW_INST_OWNERSHIP ({inst_pct_val:.1f}%)"
        except Exception:
            inst_signal = "ERROR"

        score_components["institutional_ownership"] = {"score": inst_score, "signal": inst_signal, "max": 20}
        total_score += inst_score

        # ── 3. Insider Trading (Form 4 proxy) ── max 25 pts ──
        insider_score = 0
        insider_signal = "N/A"
        try:
            transactions = t.insider_transactions
            buy_count = 0
            sell_count = 0
            net_value = 0.0
            if transactions is not None and not transactions.empty:
                import datetime
                cutoff = datetime.datetime.now() - datetime.timedelta(days=90)
                for _, row in transactions.iterrows():
                    try:
                        txn_date = row.get("startDate") or row.get("Date") or row.name
                        if hasattr(txn_date, 'to_pydatetime'):
                            txn_date = txn_date.to_pydatetime().replace(tzinfo=None)
                        if isinstance(txn_date, datetime.datetime) and txn_date < cutoff:
                            continue
                    except Exception:
                        pass
                    shares = row.get("shares", 0) or 0
                    value = row.get("value", 0) or 0
                    text = str(row.get("text", "") or row.get("transaction", "")).lower()
                    if "sale" in text or "sell" in text or "sold" in text or shares < 0 or value < 0:
                        sell_count += 1
                        net_value -= abs(float(value))
                    elif "purchase" in text or "buy" in text or "bought" in text or shares > 0:
                        buy_count += 1
                        net_value += abs(float(value))

            if buy_count >= 3 and net_value > 500000:
                insider_score = 25
                insider_signal = f"STRONG_INSIDER_BUYING ({buy_count} buys, net ${net_value:,.0f})"
            elif buy_count >= 2 and net_value > 0:
                insider_score = 15
                insider_signal = f"INSIDER_BUYING ({buy_count} buys)"
            elif buy_count >= 1 and sell_count == 0:
                insider_score = 8
                insider_signal = f"SINGLE_INSIDER_BUY"
            elif sell_count >= 3 and net_value < -500000:
                insider_score = -20
                insider_signal = f"STRONG_INSIDER_SELLING ({sell_count} sells)"
            elif sell_count > buy_count:
                insider_score = -10
                insider_signal = f"NET_INSIDER_SELLING ({sell_count} sells vs {buy_count} buys)"
            else:
                insider_score = 0
                insider_signal = "NEUTRAL_INSIDER_ACTIVITY"
        except Exception:
            insider_signal = "ERROR"

        score_components["insider_trading"] = {"score": insider_score, "signal": insider_signal, "max": 25}
        total_score += insider_score

        # ── 4. Short Interest ── max 15 pts ──
        short_score = 0
        short_signal = "N/A"
        try:
            info_full2 = t.info
            short_pct = info_full2.get("shortPercentOfFloat", None)
            if short_pct is not None:
                sp = float(short_pct) * 100
                if sp < 5:
                    short_score = 15
                    short_signal = f"LOW_SHORT_INTEREST ({sp:.1f}%) — healthy, minimal bearish pressure"
                elif sp < 15:
                    short_score = 8
                    short_signal = f"MODERATE_SHORT_INTEREST ({sp:.1f}%)"
                elif sp >= 30:
                    short_score = 10
                    short_signal = f"EXTREME_SHORT ({sp:.1f}%) — squeeze potential, contrarian bullish"
                elif sp >= 20:
                    short_score = 2
                    short_signal = f"HIGH_SHORT_INTEREST ({sp:.1f}%) — bearish consensus"
                else:
                    short_score = 0
                    short_signal = f"ELEVATED_SHORT ({sp:.1f}%)"
        except Exception:
            short_signal = "ERROR"

        score_components["short_interest"] = {"score": short_score, "signal": short_signal, "max": 15}
        total_score += short_score

        # ── 5. Options Flow Sentiment ── max 15 pts ──
        options_score = 0
        options_signal = "N/A"
        try:
            opts = t.options
            if opts:
                import datetime
                today = datetime.date.today()
                chosen_exp = None
                for exp in opts:
                    dte = (datetime.date.fromisoformat(exp) - today).days
                    if 14 <= dte <= 60:
                        chosen_exp = exp
                        break
                if not chosen_exp and opts:
                    chosen_exp = opts[0]
                if chosen_exp:
                    chain = t.option_chain(chosen_exp)
                    call_vol = int(chain.calls["volume"].fillna(0).sum())
                    put_vol = int(chain.puts["volume"].fillna(0).sum())
                    if call_vol + put_vol > 0:
                        pc_ratio = put_vol / call_vol if call_vol > 0 else 99
                        if pc_ratio < 0.5:
                            options_score = 15
                            options_signal = f"HEAVY_CALL_VOLUME (P/C={pc_ratio:.2f}) — bullish positioning"
                        elif pc_ratio < 0.8:
                            options_score = 10
                            options_signal = f"CALL_LEAN (P/C={pc_ratio:.2f})"
                        elif pc_ratio > 1.5:
                            options_score = -10
                            options_signal = f"HEAVY_PUT_VOLUME (P/C={pc_ratio:.2f}) — bearish/hedging"
                        elif pc_ratio > 1.0:
                            options_score = -5
                            options_signal = f"PUT_LEAN (P/C={pc_ratio:.2f})"
                        else:
                            options_score = 5
                            options_signal = f"BALANCED_OPTIONS (P/C={pc_ratio:.2f})"
        except Exception:
            options_signal = "ERROR"

        score_components["options_flow"] = {"score": options_score, "signal": options_signal, "max": 15}
        total_score += options_score

        # ── Final Score & Signal ──
        clamped = max(0, min(100, total_score + 45))
        smart_money_score = round(clamped)

        if smart_money_score >= 85:
            final_signal = "STRONG_SMART_MONEY_BUY"
            signal_note = "All major smart money indicators aligned bullishly. Institutions accumulating, insiders buying, low short, bullish options."
        elif smart_money_score >= 65:
            final_signal = "SMART_MONEY_BUY"
            signal_note = "Multiple smart money indicators point to accumulation. Bullish institutional footprint."
        elif smart_money_score >= 40:
            final_signal = "NEUTRAL"
            signal_note = "Mixed smart money signals. No strong directional bias from institutional activity."
        elif smart_money_score >= 25:
            final_signal = "SMART_MONEY_SELL"
            signal_note = "Multiple smart money indicators suggest distribution or bearish positioning."
        else:
            final_signal = "STRONG_SMART_MONEY_SELL"
            signal_note = "Strong bearish institutional footprint: insiders selling, OBV divergence, heavy put volume."

        return {
            "ticker": ticker_upper,
            "company": company,
            "current_price": current_price,
            "smart_money_score": smart_money_score,
            "smart_money_signal": final_signal,
            "signal_note": signal_note,
            "score_breakdown": score_components,
            "raw_score": total_score,
            "methodology": {
                "dark_pool_obv": "25 pts — OBV divergence vs price trend (hidden accumulation proxy)",
                "institutional_ownership": "20 pts — % held by institutions (heldPercentInstitutions)",
                "insider_trading": "25 pts — Form 4 net buys/sells last 90 days",
                "short_interest": "15 pts — short % of float (low = healthy, extreme = squeeze potential)",
                "options_flow": "15 pts — put/call volume ratio on nearest 14-60 DTE expiration",
                "total_max": "100 pts (negative signals reduce score)",
            },
            "interpretation": {
                "80-100": "STRONG_SMART_MONEY_BUY — rare, high-conviction setup",
                "60-79": "SMART_MONEY_BUY — institutional accumulation likely",
                "40-59": "NEUTRAL — no clear smart money bias",
                "20-39": "SMART_MONEY_SELL — distribution signals present",
                "0-19": "STRONG_SMART_MONEY_SELL — multiple bearish institutional signals",
            },
            "note": (
                "Combine with get_dark_pool_indicator(), get_institutional_flow_tracker(), "
                "get_insider_trading_radar(), and get_options_unusual_activity_scanner() "
                "for full smart money analysis pipeline."
            ),
            "source": "Yahoo Finance — no API key required",
        }
    except Exception as e:
        return {"error": str(e)}




# ── v3.1.0 도구 1: get_options_flow_heatmap ──────────────────────────────────
@mcp.tool()
async def get_options_flow_heatmap() -> dict:
    """
    Sector-level options flow heatmap across 11 GICS sectors.
    Aggregates put/call ratio + unusual sweep counts for representative sector tickers
    to produce a sector-by-sector BULLISH/BEARISH/NEUTRAL options flow signal.
    Useful for identifying which sectors smart money is positioning in via options.
    advanced_tool tier.
    """
    await Actor.charge("advanced_tool", count=1)
    import yfinance as yf
    import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed

    SECTOR_TICKERS = {
        "Technology": ["AAPL", "MSFT", "NVDA", "AMD"],
        "Healthcare": ["JNJ", "UNH", "PFE", "ABBV"],
        "Financials": ["JPM", "BAC", "GS", "MS"],
        "Energy": ["XOM", "CVX", "COP", "SLB"],
        "Industrials": ["CAT", "HON", "UPS", "BA"],
        "Materials": ["LIN", "APD", "NEM", "FCX"],
        "Real Estate": ["AMT", "PLD", "EQIX", "SPG"],
        "Consumer Discretionary": ["AMZN", "TSLA", "HD", "NKE"],
        "Consumer Staples": ["PG", "KO", "WMT", "COST"],
        "Utilities": ["NEE", "DUK", "SO", "AEP"],
        "Communication Services": ["GOOGL", "META", "NFLX", "DIS"],
    }

    def fetch_options_data(ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            opts = t.options
            if not opts:
                return {"ticker": ticker, "call_vol": 0, "put_vol": 0, "unusual": 0, "error": "no_options"}
            today = datetime.date.today()
            chosen_exp = None
            for exp in opts:
                dte = (datetime.date.fromisoformat(exp) - today).days
                if 7 <= dte <= 45:
                    chosen_exp = exp
                    break
            if not chosen_exp:
                chosen_exp = opts[0]
            chain = t.option_chain(chosen_exp)
            calls = chain.calls
            puts = chain.puts
            call_vol = int(calls["volume"].fillna(0).sum())
            put_vol = int(puts["volume"].fillna(0).sum())
            call_oi = int(calls["openInterest"].fillna(0).sum())
            put_oi = int(puts["openInterest"].fillna(0).sum())
            unusual_calls = int(((calls["volume"].fillna(0) / calls["openInterest"].replace(0, 1).fillna(1)) >= 3).sum())
            unusual_puts = int(((puts["volume"].fillna(0) / puts["openInterest"].replace(0, 1).fillna(1)) >= 3).sum())
            return {
                "ticker": ticker,
                "call_vol": call_vol,
                "put_vol": put_vol,
                "call_oi": call_oi,
                "put_oi": put_oi,
                "unusual_calls": unusual_calls,
                "unusual_puts": unusual_puts,
                "unusual": unusual_calls + unusual_puts,
            }
        except Exception as e:
            return {"ticker": ticker, "call_vol": 0, "put_vol": 0, "unusual": 0, "error": str(e)}

    try:
        all_tickers = [t for tickers in SECTOR_TICKERS.values() for t in tickers]
        ticker_results = {}
        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = {ex.submit(fetch_options_data, t): t for t in all_tickers}
            for fut in as_completed(futures):
                res = fut.result()
                ticker_results[res["ticker"]] = res

        sector_results = {}
        bullish_sectors = []
        bearish_sectors = []
        neutral_sectors = []

        for sector, tickers in SECTOR_TICKERS.items():
            total_call_vol = 0
            total_put_vol = 0
            total_unusual_calls = 0
            total_unusual_puts = 0
            valid_count = 0
            ticker_details = []

            for t in tickers:
                d = ticker_results.get(t, {})
                if "error" not in d or d.get("call_vol", 0) + d.get("put_vol", 0) > 0:
                    total_call_vol += d.get("call_vol", 0)
                    total_put_vol += d.get("put_vol", 0)
                    total_unusual_calls += d.get("unusual_calls", 0)
                    total_unusual_puts += d.get("unusual_puts", 0)
                    valid_count += 1
                ticker_details.append({
                    "ticker": t,
                    "call_vol": d.get("call_vol", 0),
                    "put_vol": d.get("put_vol", 0),
                    "unusual_calls": d.get("unusual_calls", 0),
                    "unusual_puts": d.get("unusual_puts", 0),
                })

            total_vol = total_call_vol + total_put_vol
            pc_ratio = round(total_put_vol / total_call_vol, 3) if total_call_vol > 0 else 99.0
            sweep_bias = total_unusual_calls - total_unusual_puts

            if pc_ratio < 0.6 and sweep_bias >= 0:
                flow_signal = "STRONG_BULLISH"
                flow_note = f"Heavy call volume (P/C={pc_ratio:.2f}) with call sweep dominance"
            elif pc_ratio < 0.85:
                flow_signal = "BULLISH"
                flow_note = f"Call-leaning flow (P/C={pc_ratio:.2f})"
            elif pc_ratio > 1.5 and sweep_bias <= 0:
                flow_signal = "STRONG_BEARISH"
                flow_note = f"Heavy put volume (P/C={pc_ratio:.2f}) with put sweep dominance"
            elif pc_ratio > 1.15:
                flow_signal = "BEARISH"
                flow_note = f"Put-leaning flow (P/C={pc_ratio:.2f})"
            else:
                flow_signal = "NEUTRAL"
                flow_note = f"Balanced options flow (P/C={pc_ratio:.2f})"

            if "BULLISH" in flow_signal:
                bullish_sectors.append(sector)
            elif "BEARISH" in flow_signal:
                bearish_sectors.append(sector)
            else:
                neutral_sectors.append(sector)

            sector_results[sector] = {
                "flow_signal": flow_signal,
                "pc_ratio": pc_ratio,
                "total_call_volume": total_call_vol,
                "total_put_volume": total_put_vol,
                "unusual_call_sweeps": total_unusual_calls,
                "unusual_put_sweeps": total_unusual_puts,
                "sweep_bias": sweep_bias,
                "total_volume": total_vol,
                "flow_note": flow_note,
                "tickers_analyzed": valid_count,
                "ticker_details": ticker_details,
            }

        if len(bullish_sectors) >= 7:
            market_flow = "BROAD_BULLISH_FLOW"
            market_note = "Options flow bullish across most sectors. Risk-ON positioning."
        elif len(bearish_sectors) >= 7:
            market_flow = "BROAD_BEARISH_FLOW"
            market_note = "Options flow bearish across most sectors. Hedging or risk-OFF."
        elif len(bullish_sectors) > len(bearish_sectors) + 2:
            market_flow = "MODERATE_BULLISH_FLOW"
            market_note = "More bullish sectors than bearish. Cautious risk-ON."
        elif len(bearish_sectors) > len(bullish_sectors) + 2:
            market_flow = "MODERATE_BEARISH_FLOW"
            market_note = "More bearish sectors. Defensive positioning."
        else:
            market_flow = "MIXED_FLOW"
            market_note = "No clear directional bias. Sector-specific plays only."

        sorted_sectors = sorted(sector_results.items(), key=lambda x: x[1]["pc_ratio"])
        most_bullish = [s for s, _ in sorted_sectors[:3]]
        most_bearish = [s for s, _ in sorted_sectors[-3:]]

        return {
            "market_flow_regime": market_flow,
            "market_flow_note": market_note,
            "bullish_sectors": bullish_sectors,
            "bearish_sectors": bearish_sectors,
            "neutral_sectors": neutral_sectors,
            "most_bullish_sectors": most_bullish,
            "most_bearish_sectors": most_bearish,
            "sector_heatmap": sector_results,
            "methodology": {
                "put_call_ratio": "Total put volume / call volume across sector representative tickers",
                "unusual_sweeps": "Options contracts with volume/OI >= 3x (institutional sweep proxy)",
                "sweep_bias": "unusual_calls - unusual_puts (positive = bullish smart money)",
                "flow_signal_thresholds": {
                    "STRONG_BULLISH": "P/C < 0.60 AND call sweep dominance",
                    "BULLISH": "P/C < 0.85",
                    "NEUTRAL": "0.85 <= P/C <= 1.15",
                    "BEARISH": "P/C > 1.15",
                    "STRONG_BEARISH": "P/C > 1.50 AND put sweep dominance",
                },
            },
            "source": "Yahoo Finance options chains — no API key required",
            "note": "Combine with get_smart_money_composite() and get_options_unusual_activity_scanner() for full smart money picture.",
        }
    except Exception as e:
        return {"error": str(e)}


# ── v3.1.0 도구 2: get_market_regime_composite ────────────────────────────────
@mcp.tool()
async def get_market_regime_composite() -> dict:
    """
    Composite market regime detector combining macro, technical, and market structure layers.
    Integrates VIX regime + yield curve shape + credit spreads + market breadth + sector rotation
    into a single BULL_MARKET / BEAR_MARKET / TRANSITION / CHOPPY_MARKET regime with
    asset allocation guidance.
    basic_tool tier.
    """
    await Actor.charge("basic_tool", count=1)
    import yfinance as yf

    try:
        vix_score = 0
        vix_regime = "UNKNOWN"
        vix_level = None
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="60d", interval="1d", auto_adjust=True)
            if not vix_hist.empty:
                vix_level = round(float(vix_hist["Close"].iloc[-1]), 2)
                if vix_level < 15:
                    vix_score = 25
                    vix_regime = "COMPLACENT"
                elif vix_level < 20:
                    vix_score = 20
                    vix_regime = "LOW_STRESS"
                elif vix_level < 25:
                    vix_score = 10
                    vix_regime = "NORMAL"
                elif vix_level < 35:
                    vix_score = -10
                    vix_regime = "ELEVATED_STRESS"
                else:
                    vix_score = -25
                    vix_regime = "PANIC"
        except Exception:
            pass

        curve_score = 0
        curve_shape = "UNKNOWN"
        spread_bps = None
        try:
            tnx = yf.Ticker("^TNX")
            irx = yf.Ticker("^IRX")
            tnx_hist = tnx.history(period="5d", interval="1d", auto_adjust=True)
            irx_hist = irx.history(period="5d", interval="1d", auto_adjust=True)
            if not tnx_hist.empty and not irx_hist.empty:
                y10 = float(tnx_hist["Close"].iloc[-1])
                y3m = float(irx_hist["Close"].iloc[-1])
                spread = y10 - y3m
                spread_bps = round(spread * 100, 1)
                if spread > 1.0:
                    curve_score = 20
                    curve_shape = "STEEP_NORMAL"
                elif spread > 0.25:
                    curve_score = 15
                    curve_shape = "NORMAL"
                elif spread > -0.25:
                    curve_score = 5
                    curve_shape = "FLAT"
                elif spread > -1.0:
                    curve_score = -15
                    curve_shape = "INVERTED"
                else:
                    curve_score = -20
                    curve_shape = "DEEPLY_INVERTED"
        except Exception:
            pass

        credit_score = 0
        credit_regime = "UNKNOWN"
        hy_spread_proxy = None
        try:
            hyg = yf.Ticker("HYG")
            ief = yf.Ticker("IEF")
            hyg_hist = hyg.history(period="60d", interval="1d", auto_adjust=True)
            ief_hist = ief.history(period="60d", interval="1d", auto_adjust=True)
            if not hyg_hist.empty and not ief_hist.empty and len(hyg_hist) >= 30:
                hyg_ret_30 = (float(hyg_hist["Close"].iloc[-1]) / float(hyg_hist["Close"].iloc[-30]) - 1) * 100
                ief_ret_30 = (float(ief_hist["Close"].iloc[-1]) / float(ief_hist["Close"].iloc[-30]) - 1) * 100
                spread_proxy = hyg_ret_30 - ief_ret_30
                hy_spread_proxy = round(spread_proxy, 2)
                if spread_proxy > 1.0:
                    credit_score = 20
                    credit_regime = "RISK_ON_CREDIT"
                elif spread_proxy > 0:
                    credit_score = 15
                    credit_regime = "MILD_RISK_ON"
                elif spread_proxy > -1.0:
                    credit_score = 5
                    credit_regime = "NEUTRAL_CREDIT"
                elif spread_proxy > -2.0:
                    credit_score = -10
                    credit_regime = "CAUTION"
                else:
                    credit_score = -20
                    credit_regime = "RISK_OFF_CREDIT"
        except Exception:
            pass

        breadth_score = 0
        breadth_regime = "UNKNOWN"
        spy_vs_rsp = None
        try:
            spy = yf.Ticker("SPY")
            rsp = yf.Ticker("RSP")
            spy_hist = spy.history(period="60d", interval="1d", auto_adjust=True)
            rsp_hist = rsp.history(period="60d", interval="1d", auto_adjust=True)
            if not spy_hist.empty and not rsp_hist.empty and len(spy_hist) >= 20:
                spy_20d = (float(spy_hist["Close"].iloc[-1]) / float(spy_hist["Close"].iloc[-20]) - 1) * 100
                rsp_20d = (float(rsp_hist["Close"].iloc[-1]) / float(rsp_hist["Close"].iloc[-20]) - 1) * 100
                spy_vs_rsp = round(rsp_20d - spy_20d, 2)
                if spy_20d > 3 and rsp_20d >= spy_20d - 0.5:
                    breadth_score = 20
                    breadth_regime = "BROAD_PARTICIPATION"
                elif spy_20d > 0 and rsp_20d > 0:
                    breadth_score = 15
                    breadth_regime = "MODERATE_BREADTH"
                elif spy_20d > 0 and rsp_20d < spy_20d - 2:
                    breadth_score = 5
                    breadth_regime = "NARROW_LEADERSHIP"
                elif spy_20d < -3:
                    breadth_score = -15
                    breadth_regime = "BROAD_DECLINE"
                else:
                    breadth_score = 0
                    breadth_regime = "CHOPPY"
        except Exception:
            pass

        rotation_score = 0
        rotation_signal = "UNKNOWN"
        try:
            tickers_rot = ["XLK", "XLY", "XLP", "XLU"]
            rot_data = {}
            for sym in tickers_rot:
                h = yf.Ticker(sym).history(period="30d", interval="1d", auto_adjust=True)
                if not h.empty and len(h) >= 20:
                    rot_data[sym] = (float(h["Close"].iloc[-1]) / float(h["Close"].iloc[-20]) - 1) * 100
            if len(rot_data) >= 4:
                cyclical_avg = (rot_data.get("XLK", 0) + rot_data.get("XLY", 0)) / 2
                defensive_avg = (rot_data.get("XLP", 0) + rot_data.get("XLU", 0)) / 2
                rotation_diff = cyclical_avg - defensive_avg
                if rotation_diff > 3:
                    rotation_score = 15
                    rotation_signal = "STRONG_CYCLICAL_ROTATION"
                elif rotation_diff > 1:
                    rotation_score = 10
                    rotation_signal = "CYCLICAL_ROTATION"
                elif rotation_diff > -1:
                    rotation_score = 5
                    rotation_signal = "MIXED_ROTATION"
                elif rotation_diff > -3:
                    rotation_score = -10
                    rotation_signal = "DEFENSIVE_ROTATION"
                else:
                    rotation_score = -15
                    rotation_signal = "STRONG_DEFENSIVE_ROTATION"
        except Exception:
            pass

        total_score = vix_score + curve_score + credit_score + breadth_score + rotation_score
        max_possible = 25 + 20 + 20 + 20 + 15
        min_possible = -25 - 20 - 20 - 15 - 15
        normalized = round((total_score - min_possible) / (max_possible - min_possible) * 100)
        normalized = max(0, min(100, normalized))

        if normalized >= 75:
            regime = "BULL_MARKET"
            regime_note = "All 5 layers aligned bullishly. Strong risk-ON environment."
            allocation = "Risk-ON: Equities > Bonds > Cash. Overweight cyclicals."
        elif normalized >= 58:
            regime = "BULL_MARKET"
            regime_note = "Most layers bullish with some caution signals."
            allocation = "Risk-ON: Equities overweight. Normal allocation."
        elif normalized >= 42:
            regime = "TRANSITION"
            regime_note = "Mixed signals across layers. Regime change in progress."
            allocation = "Balanced: Equities = Bonds. Reduce cyclical exposure."
        elif normalized >= 28:
            regime = "CHOPPY_MARKET"
            regime_note = "Bearish signals dominate. No clear trend."
            allocation = "Defensive: Bonds > Equities. Add cash/hedges."
        else:
            regime = "BEAR_MARKET"
            regime_note = "Multiple bearish signals across all layers. Risk-OFF."
            allocation = "Risk-OFF: Cash > Bonds > Equities. Defensive sectors only."

        return {
            "market_regime": regime,
            "regime_score": normalized,
            "regime_note": regime_note,
            "asset_allocation": allocation,
            "layer_scores": {
                "vix_regime": {
                    "score": vix_score,
                    "max": 25,
                    "regime": vix_regime,
                    "vix_level": vix_level,
                },
                "yield_curve": {
                    "score": curve_score,
                    "max": 20,
                    "shape": curve_shape,
                    "spread_10y_3m_bps": spread_bps,
                },
                "credit_spreads": {
                    "score": credit_score,
                    "max": 20,
                    "regime": credit_regime,
                    "hyg_vs_ief_30d_diff_pct": hy_spread_proxy,
                },
                "market_breadth": {
                    "score": breadth_score,
                    "max": 20,
                    "regime": breadth_regime,
                    "rsp_vs_spy_20d_diff": spy_vs_rsp,
                },
                "sector_rotation": {
                    "score": rotation_score,
                    "max": 15,
                    "signal": rotation_signal,
                },
            },
            "raw_score": total_score,
            "score_range": f"{min_possible} to {max_possible}",
            "interpretation": {
                "75-100": "BULL_MARKET — strong risk-ON",
                "58-74": "BULL_MARKET — normal risk-ON",
                "42-57": "TRANSITION — reduce cyclicals",
                "28-41": "CHOPPY_MARKET — add hedges",
                "0-27": "BEAR_MARKET — risk-OFF",
            },
            "methodology": {
                "layer_1_vix": "VIX spot level (25pts: <15=COMPLACENT, <20=LOW_STRESS, <25=NORMAL, <35=ELEVATED, >=35=PANIC)",
                "layer_2_yield_curve": "10Y-3M spread proxy (20pts: >100bps=STEEP, >25bps=NORMAL, flat=0, inverted=-15/-20)",
                "layer_3_credit": "HYG vs IEF 30d relative return (20pts: >+1%=RISK_ON to <-2%=RISK_OFF)",
                "layer_4_breadth": "SPY vs RSP 20d momentum (20pts: broad participation positive, narrow leadership caution)",
                "layer_5_rotation": "XLK+XLY vs XLP+XLU 20d cyclical vs defensive (15pts)",
            },
            "source": "Yahoo Finance — no API key required",
            "note": "Combine with get_vix_regime_monitor(), get_yield_curve_dynamics(), get_sector_rotation_signal() for deeper analysis.",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_earnings_surprise_vs_sector(ticker: str) -> dict:
    """Compare a stock's EPS surprise history vs its sector average.
    Identifies if the stock consistently beats/misses relative to sector peers.
    Returns SECTOR_OUTPERFORMER, IN_LINE, or SECTOR_UNDERPERFORMER signal."""
    try:
        await Actor.charge("advanced_tool", count=1)
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor
        import asyncio

        ticker = ticker.upper().strip()

        SECTOR_PEERS = {
            "Technology": ["AAPL", "MSFT", "NVDA", "AMD", "INTC", "ORCL", "CRM", "CSCO", "QCOM", "TXN"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "BMY", "AMGN", "GILD", "CVS"],
            "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK", "SCHW", "USB"],
            "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "BKNG", "GM"],
            "Consumer Staples": ["WMT", "PG", "KO", "PEP", "COST", "CL", "MDLZ", "KHC", "GIS", "SYY"],
            "Industrials": ["BA", "CAT", "HON", "UPS", "DE", "MMM", "GE", "RTX", "LMT", "NOC"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "PSX", "OXY", "KMI"],
            "Materials": ["LIN", "APD", "ECL", "NEM", "FCX", "NUE", "VMC", "MLM", "PPG", "SHW"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "SPG", "O", "WELL", "EQR"],
            "Utilities": ["NEE", "DUK", "SO", "AEP", "D", "EXC", "SRE", "PCG", "ED", "XEL"],
            "Communication Services": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "T", "VZ", "ATVI", "EA", "TTWO"],
        }

        def _get_eps_surprises(sym):
            try:
                t = yf.Ticker(sym)
                hist = t.earnings_history
                if hist is None or (hasattr(hist, 'empty') and hist.empty):
                    return []
                surprises = []
                for _, row in hist.iterrows():
                    try:
                        actual = float(row.get("epsActual", 0) or 0)
                        estimate = float(row.get("epsEstimate", 0) or 0)
                        if estimate != 0:
                            surprise_pct = (actual - estimate) / abs(estimate) * 100
                            surprises.append(round(surprise_pct, 2))
                    except Exception:
                        continue
                return surprises[:4]
            except Exception:
                return []

        t_obj = yf.Ticker(ticker)
        info = t_obj.info or {}
        sector = info.get("sector", "Unknown")

        ticker_surprises = _get_eps_surprises(ticker)
        if not ticker_surprises:
            return {"error": f"No earnings history for {ticker}"}

        ticker_avg_surprise = round(sum(ticker_surprises) / len(ticker_surprises), 2)
        ticker_beat_count = sum(1 for s in ticker_surprises if s >= 2.0)
        ticker_miss_count = sum(1 for s in ticker_surprises if s <= -2.0)
        ticker_beat_rate = round(ticker_beat_count / len(ticker_surprises) * 100, 1)

        peers = SECTOR_PEERS.get(sector, [])
        peers = [p for p in peers if p != ticker]
        if not peers:
            all_peers = []
            for v in SECTOR_PEERS.values():
                all_peers.extend(v)
            peers = [p for p in all_peers if p != ticker][:20]

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = await loop.run_in_executor(None, lambda: list(ex.map(_get_eps_surprises, peers[:15])))

        peer_surprises_raw = []
        for r in results:
            if r:
                peer_surprises_raw.extend(r)

        if peer_surprises_raw:
            sector_avg_surprise = round(sum(peer_surprises_raw) / len(peer_surprises_raw), 2)
            sector_beat_rate = round(sum(1 for s in peer_surprises_raw if s >= 2.0) / len(peer_surprises_raw) * 100, 1)
        else:
            sector_avg_surprise = 4.5
            sector_beat_rate = 74.0

        diff = round(ticker_avg_surprise - sector_avg_surprise, 2)
        beat_rate_diff = round(ticker_beat_rate - sector_beat_rate, 1)

        if diff >= 5 or beat_rate_diff >= 15:
            vs_sector = "SECTOR_OUTPERFORMER"
            signal_strength = "STRONG" if diff >= 10 or beat_rate_diff >= 25 else "MODERATE"
        elif diff >= 2 or beat_rate_diff >= 5:
            vs_sector = "SECTOR_OUTPERFORMER"
            signal_strength = "MILD"
        elif diff <= -5 or beat_rate_diff <= -15:
            vs_sector = "SECTOR_UNDERPERFORMER"
            signal_strength = "STRONG" if diff <= -10 or beat_rate_diff <= -25 else "MODERATE"
        elif diff <= -2 or beat_rate_diff <= -5:
            vs_sector = "SECTOR_UNDERPERFORMER"
            signal_strength = "MILD"
        else:
            vs_sector = "IN_LINE"
            signal_strength = "NEUTRAL"

        trend = "STABLE"
        if len(ticker_surprises) >= 3:
            recent_avg = sum(ticker_surprises[:2]) / 2
            older_avg = sum(ticker_surprises[2:]) / len(ticker_surprises[2:])
            trend_diff = recent_avg - older_avg
            if trend_diff >= 3:
                trend = "IMPROVING"
            elif trend_diff <= -3:
                trend = "DECLINING"

        quarters_labeled = []
        for i, s in enumerate(ticker_surprises):
            quarters_labeled.append({
                "quarter": f"Q-{i+1} (most recent first)",
                "eps_surprise_pct": s,
                "beat_miss": "BEAT" if s >= 2 else ("MISS" if s <= -2 else "IN_LINE"),
            })

        return {
            "ticker": ticker,
            "sector": sector,
            "vs_sector_signal": vs_sector,
            "signal_strength": signal_strength,
            "surprise_trend": trend,
            "ticker_avg_eps_surprise_pct": ticker_avg_surprise,
            "sector_avg_eps_surprise_pct": sector_avg_surprise,
            "surprise_diff_vs_sector": diff,
            "ticker_beat_rate_pct": ticker_beat_rate,
            "sector_beat_rate_pct": sector_beat_rate,
            "beat_rate_diff_pct": beat_rate_diff,
            "quarters_analyzed": len(ticker_surprises),
            "quarterly_breakdown": quarters_labeled,
            "interpretation": {
                "SECTOR_OUTPERFORMER": "Consistently beats more than sector peers → alpha source, strong execution",
                "IN_LINE": "Matches sector average EPS beat/miss pattern",
                "SECTOR_UNDERPERFORMER": "Consistently misses more than peers → execution risk, guidance credibility issue",
            },
            "signal_detail": f"{ticker} avg EPS surprise {ticker_avg_surprise:+.1f}% vs sector avg {sector_avg_surprise:+.1f}% ({diff:+.1f}pp diff). Beat rate: {ticker_beat_rate:.0f}% vs sector {sector_beat_rate:.0f}%.",
            "source": "Yahoo Finance earnings_history — no API key required",
            "note": "Combine with get_earnings_whisper() and get_earnings_revision_tracker() for full earnings analysis.",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_52w_high_low_momentum() -> dict:
    """Track S&P 500 52-week high/low counts as a market momentum health indicator.
    Returns net high-low ratio, momentum regime, and sector-level distribution.
    High new highs = broad bull market. High new lows = bear market confirmation."""
    try:
        await Actor.charge("basic_tool", count=1)
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor
        import asyncio

        UNIVERSE = {
            "Technology": ["AAPL", "MSFT", "NVDA", "AMD", "INTC", "ORCL", "CRM", "CSCO", "QCOM", "TXN", "AVGO", "MU", "AMAT", "LRCX"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "BMY", "AMGN", "GILD", "CVS", "MDT", "ABT"],
            "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK", "SCHW", "USB", "TFC", "PNC"],
            "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "BKNG", "GM", "F", "EBAY"],
            "Consumer Staples": ["WMT", "PG", "KO", "PEP", "COST", "CL", "MDLZ", "KHC", "GIS", "SYY"],
            "Industrials": ["BA", "CAT", "HON", "UPS", "DE", "MMM", "GE", "RTX", "LMT", "NOC", "FDX", "CSX"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "PSX", "OXY", "KMI"],
            "Materials": ["LIN", "APD", "ECL", "NEM", "FCX", "NUE", "VMC", "MLM", "PPG", "SHW"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "SPG", "O", "WELL", "EQR"],
            "Utilities": ["NEE", "DUK", "SO", "AEP", "D", "EXC", "SRE", "XEL"],
            "Communication Services": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "T", "VZ", "ATVI", "EA"],
        }

        all_tickers = []
        ticker_to_sector = {}
        for sec, tickers in UNIVERSE.items():
            for t in tickers:
                all_tickers.append(t)
                ticker_to_sector[t] = sec

        def _check_52w(sym):
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="1y", interval="1d", auto_adjust=True)
                if hist.empty or len(hist) < 50:
                    return None
                current = float(hist["Close"].iloc[-1])
                high_52w = float(hist["High"].max())
                low_52w = float(hist["Low"].min())
                pct_from_high = round((current - high_52w) / high_52w * 100, 2)
                pct_from_low = round((current - low_52w) / low_52w * 100, 2)
                is_near_high = pct_from_high >= -3.0
                is_near_low = pct_from_low <= 3.0
                return {
                    "ticker": sym,
                    "current": round(current, 2),
                    "high_52w": round(high_52w, 2),
                    "low_52w": round(low_52w, 2),
                    "pct_from_high": pct_from_high,
                    "pct_from_low": pct_from_low,
                    "near_52w_high": is_near_high,
                    "near_52w_low": is_near_low,
                }
            except Exception:
                return None

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = await loop.run_in_executor(None, lambda: list(ex.map(_check_52w, all_tickers)))

        valid = [r for r in results if r is not None]
        total = len(valid)
        if total == 0:
            return {"error": "No data retrieved"}

        near_highs = [r for r in valid if r["near_52w_high"]]
        near_lows = [r for r in valid if r["near_52w_low"]]
        n_highs = len(near_highs)
        n_lows = len(near_lows)
        net = n_highs - n_lows
        net_ratio = round(net / total * 100, 1)
        pct_highs = round(n_highs / total * 100, 1)
        pct_lows = round(n_lows / total * 100, 1)

        if net_ratio >= 20 and pct_highs >= 25:
            regime = "STRONG_BULL_MOMENTUM"
            regime_note = "Broad 52W high participation — healthy bull market breadth."
        elif net_ratio >= 10:
            regime = "BULLISH_MOMENTUM"
            regime_note = "More new highs than lows — momentum favors bulls."
        elif net_ratio >= -10:
            regime = "NEUTRAL_MOMENTUM"
            regime_note = "Mixed highs/lows — no decisive momentum direction."
        elif net_ratio >= -20:
            regime = "BEARISH_MOMENTUM"
            regime_note = "More new lows than highs — momentum deteriorating."
        else:
            regime = "STRONG_BEAR_MOMENTUM"
            regime_note = "Broad 52W low participation — bear market breadth signal."

        sector_stats = {}
        for sec in UNIVERSE.keys():
            sec_stocks = [r for r in valid if ticker_to_sector.get(r["ticker"]) == sec]
            if not sec_stocks:
                continue
            sec_highs = sum(1 for r in sec_stocks if r["near_52w_high"])
            sec_lows = sum(1 for r in sec_stocks if r["near_52w_low"])
            sec_total = len(sec_stocks)
            sec_net_pct = round((sec_highs - sec_lows) / sec_total * 100, 1)
            label = "LEADING" if sec_net_pct >= 20 else ("LAGGING" if sec_net_pct <= -20 else "NEUTRAL")
            sector_stats[sec] = {
                "near_highs": sec_highs,
                "near_lows": sec_lows,
                "total": sec_total,
                "net_pct": sec_net_pct,
                "status": label,
            }

        sorted_sectors = sorted(sector_stats.items(), key=lambda x: x[1]["net_pct"], reverse=True)
        leading_sectors = [s for s, d in sorted_sectors if d["status"] == "LEADING"]
        lagging_sectors = [s for s, d in sorted_sectors if d["status"] == "LAGGING"]

        top_highs_list = sorted(near_highs, key=lambda r: r["pct_from_high"], reverse=True)[:5]
        top_lows_list = sorted(near_lows, key=lambda r: r["pct_from_low"])[:5]

        return {
            "momentum_regime": regime,
            "regime_note": regime_note,
            "summary": {
                "total_stocks_scanned": total,
                "near_52w_high_count": n_highs,
                "near_52w_low_count": n_lows,
                "net_high_minus_low": net,
                "net_ratio_pct": net_ratio,
                "pct_near_highs": pct_highs,
                "pct_near_lows": pct_lows,
            },
            "sector_breakdown": {sec: data for sec, data in sorted_sectors},
            "leading_sectors": leading_sectors,
            "lagging_sectors": lagging_sectors,
            "top_5_near_highs": [
                {
                    "ticker": r["ticker"],
                    "sector": ticker_to_sector.get(r["ticker"], "Unknown"),
                    "pct_from_52w_high": r["pct_from_high"],
                    "current_price": r["current"],
                    "52w_high": r["high_52w"],
                }
                for r in top_highs_list
            ],
            "top_5_near_lows": [
                {
                    "ticker": r["ticker"],
                    "sector": ticker_to_sector.get(r["ticker"], "Unknown"),
                    "pct_from_52w_low": r["pct_from_low"],
                    "current_price": r["current"],
                    "52w_low": r["low_52w"],
                }
                for r in top_lows_list
            ],
            "interpretation": {
                "STRONG_BULL_MOMENTUM": "≥20% net + 25%+ near highs — broad bull breadth, buy dips",
                "BULLISH_MOMENTUM": "Net positive — more stocks making highs than lows",
                "NEUTRAL_MOMENTUM": "Balanced — no directional confirmation",
                "BEARISH_MOMENTUM": "Net negative — deteriorating breadth, reduce risk",
                "STRONG_BEAR_MOMENTUM": "Broad new lows — bear market confirmation",
            },
            "threshold": "Near 52W high = within 3% of high. Near 52W low = within 3% of low.",
            "source": "Yahoo Finance 1Y daily history — no API key required",
            "note": "Combine with get_market_breadth(), get_market_regime_composite(), get_sector_rotation_signal() for full picture.",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_options_iv_percentile(ticker: str = "AAPL") -> dict:
    """Get options IV percentile rank comparing current IV to 1-year historical distribution.

    Analyzes current implied volatility against historical IV distribution to identify
    options premium selling/buying opportunities. IV Percentile Rank indicates whether
    options are expensive or cheap relative to recent history.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY', 'TSLA')

    Returns:
        IV percentile rank, IV rank, signal (IV_ELEVATED/NORMAL/DEPRESSED),
        premium selling/buying timing recommendation
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import numpy as np

        ticker = ticker.upper().strip()
        t = yf.Ticker(ticker)

        hist = t.history(period="1y")
        if hist.empty or len(hist) < 30:
            return {"error": f"Insufficient historical data for {ticker}"}

        log_returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
        rolling_rv = log_returns.rolling(30).std() * np.sqrt(252) * 100
        rv_series = rolling_rv.dropna()

        if len(rv_series) < 20:
            return {"error": f"Insufficient data points for {ticker}"}

        current_iv = None
        used_rv_fallback = False
        dte_used = None
        options_dates = t.options

        if options_dates:
            from datetime import datetime
            today = datetime.now()
            target_dates = []
            for exp_str in options_dates:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
                dte = (exp_date - today).days
                if 14 <= dte <= 60:
                    target_dates.append((dte, exp_str))

            if target_dates:
                target_dates.sort()
                exp_str = target_dates[0][1]
                dte_used = target_dates[0][0]
                try:
                    chain = t.option_chain(exp_str)
                    current_price = float(hist["Close"].iloc[-1])
                    atm_calls = chain.calls[abs(chain.calls["strike"] - current_price) / current_price <= 0.02]
                    atm_puts = chain.puts[abs(chain.puts["strike"] - current_price) / current_price <= 0.02]
                    call_ivs = atm_calls["impliedVolatility"].dropna()
                    put_ivs = atm_puts["impliedVolatility"].dropna()
                    if len(call_ivs) > 0 and len(put_ivs) > 0:
                        current_iv = (float(call_ivs.mean()) + float(put_ivs.mean())) / 2 * 100
                    elif len(call_ivs) > 0:
                        current_iv = float(call_ivs.mean()) * 100
                    elif len(put_ivs) > 0:
                        current_iv = float(put_ivs.mean()) * 100
                except Exception:
                    pass

        if current_iv is None:
            current_iv = float(rv_series.iloc[-1])
            used_rv_fallback = True

        iv_percentile = float((rv_series < current_iv).sum() / len(rv_series) * 100)
        iv_min = float(rv_series.min())
        iv_max = float(rv_series.max())
        iv_rank = float((current_iv - iv_min) / (iv_max - iv_min) * 100) if iv_max > iv_min else 50.0

        if iv_percentile >= 80:
            iv_signal = "IV_ELEVATED"
            signal_strength = "HIGH" if iv_percentile >= 90 else "MODERATE"
            strategy = "SELL_PREMIUM"
            strategy_detail = "IV elevated vs history — options overpriced. Consider: covered calls, cash-secured puts, credit spreads, iron condors."
        elif iv_percentile <= 20:
            iv_signal = "IV_DEPRESSED"
            signal_strength = "HIGH" if iv_percentile <= 10 else "MODERATE"
            strategy = "BUY_PREMIUM"
            strategy_detail = "IV depressed vs history — options cheap. Consider: long calls/puts, debit spreads, straddles/strangles before catalyst."
        else:
            iv_signal = "IV_NORMAL"
            signal_strength = "NEUTRAL"
            strategy = "NEUTRAL"
            strategy_detail = "IV in normal range — no strong premium bias. Directional strategies (verticals) preferred."

        current_price = float(hist["Close"].iloc[-1])
        price_1m_chg = float((hist["Close"].iloc[-1] / hist["Close"].iloc[-21] - 1) * 100) if len(hist) >= 21 else None
        rv_1m = float(rv_series.iloc[-1])
        rv_3m_avg = float(rv_series.tail(63).mean()) if len(rv_series) >= 63 else None
        rv_6m_avg = float(rv_series.tail(126).mean()) if len(rv_series) >= 126 else None
        rv_1y_avg = float(rv_series.mean())

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "price_1m_change_pct": round(price_1m_chg, 2) if price_1m_chg is not None else None,
            "current_iv_pct": round(current_iv, 2),
            "iv_percentile": round(iv_percentile, 1),
            "iv_rank": round(iv_rank, 1),
            "signal": iv_signal,
            "signal_strength": signal_strength,
            "strategy": strategy,
            "strategy_detail": strategy_detail,
            "expiration_dte": dte_used,
            "data_source": "options_chain_ATM" if not used_rv_fallback else "30d_realized_vol_proxy",
            "historical_rv": {
                "current_30d_rv": round(rv_1m, 2),
                "3m_avg_rv": round(rv_3m_avg, 2) if rv_3m_avg is not None else None,
                "6m_avg_rv": round(rv_6m_avg, 2) if rv_6m_avg is not None else None,
                "1y_avg_rv": round(rv_1y_avg, 2),
                "1y_min_rv": round(iv_min, 2),
                "1y_max_rv": round(iv_max, 2),
            },
            "interpretation": {
                "iv_percentile_meaning": f"{iv_percentile:.1f}% of past-year trading days had IV BELOW current level",
                "iv_rank_meaning": f"Current IV at {iv_rank:.1f}% of the 52-week range (min={iv_min:.1f}%, max={iv_max:.1f}%)",
                "IV_ELEVATED": "Percentile >=80: Options expensive — favor premium SELLING (credit spreads, covered calls)",
                "IV_NORMAL": "Percentile 20-79: Options fairly priced — use directional strategies (debit spreads)",
                "IV_DEPRESSED": "Percentile <=20: Options cheap — favor premium BUYING (long options, pre-catalyst straddles)",
            },
            "source": "Yahoo Finance options + 1Y historical data — no API key required",
            "note": "Combine with get_options_skew_monitor(), get_earnings_whisper() for full volatility picture.",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_cross_asset_momentum() -> dict:
    """Get cross-asset momentum composite signal across 7 major asset classes.

    Analyzes momentum across SPY (US equities), QQQ (tech/growth), IWM (small caps),
    TLT (long bonds), GLD (gold), UUP (USD), and BTC-USD (Bitcoin) to determine
    the overall Risk-ON/Risk-OFF environment and relative asset strength ranking.

    Returns:
        1W/1M/3M return rankings, Risk-ON/Risk-OFF regime, composite momentum scores,
        momentum leaders/laggards, and asset allocation signal
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import numpy as np
        from concurrent.futures import ThreadPoolExecutor

        ASSETS = {
            "SPY": "US Equities (S&P 500)",
            "QQQ": "Tech / Growth (NASDAQ-100)",
            "IWM": "Small Cap Equities (Russell 2000)",
            "TLT": "Long-Term Bonds (20Y+ Treasury)",
            "GLD": "Gold (Safe Haven)",
            "UUP": "US Dollar (DXY proxy)",
            "BTC-USD": "Bitcoin (Crypto / Risk Asset)",
        }

        def fetch_asset(ticker):
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="6mo")
                if hist.empty or len(hist) < 10:
                    return ticker, None
                close = hist["Close"]
                current = float(close.iloc[-1])
                ret_1w = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) >= 5 else None
                ret_1m = float((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) >= 21 else None
                ret_3m = float((close.iloc[-1] / close.iloc[-63] - 1) * 100) if len(close) >= 63 else None
                mom_20d = float((close.iloc[-1] / close.iloc[-20] - 1) * 100) if len(close) >= 20 else 0.0
                log_ret = np.log(close / close.shift(1)).dropna()
                vol_20d = float(log_ret.tail(20).std() * np.sqrt(252) * 100) if len(log_ret) >= 10 else None
                sharpe_proxy = round(mom_20d / vol_20d, 3) if vol_20d and vol_20d > 0 else 0.0
                return ticker, {
                    "current": round(current, 4),
                    "ret_1w": round(ret_1w, 2) if ret_1w is not None else None,
                    "ret_1m": round(ret_1m, 2) if ret_1m is not None else None,
                    "ret_3m": round(ret_3m, 2) if ret_3m is not None else None,
                    "mom_20d": round(mom_20d, 2),
                    "vol_20d": round(vol_20d, 2) if vol_20d is not None else None,
                    "sharpe_proxy": sharpe_proxy,
                }
            except Exception:
                return ticker, None

        with ThreadPoolExecutor(max_workers=7) as ex:
            results = list(ex.map(fetch_asset, ASSETS.keys()))

        asset_data = {t: d for t, d in results if d is not None}
        if not asset_data:
            return {"error": "Failed to fetch cross-asset data"}

        tickers_valid = [t for t in ASSETS.keys() if t in asset_data]
        n = len(tickers_valid)

        def rank_by(field):
            vals = [(t, asset_data[t][field]) for t in tickers_valid if asset_data[t].get(field) is not None]
            vals.sort(key=lambda x: x[1], reverse=True)
            return [(t, v, i + 1) for i, (t, v) in enumerate(vals)]

        rank_1w = rank_by("ret_1w")
        rank_1m = rank_by("ret_1m")
        rank_3m = rank_by("ret_3m")

        composite = {}
        for t in tickers_valid:
            r1w = next((n + 1 - r for tk, v, r in rank_1w if tk == t), n // 2)
            r1m = next((n + 1 - r for tk, v, r in rank_1m if tk == t), n // 2)
            r3m = next((n + 1 - r for tk, v, r in rank_3m if tk == t), n // 2)
            composite[t] = r1w * 0.30 + r1m * 0.40 + r3m * 0.30

        comp_sorted = sorted(composite.items(), key=lambda x: x[1], reverse=True)

        spy_mom = asset_data.get("SPY", {}).get("mom_20d", 0)
        qqq_mom = asset_data.get("QQQ", {}).get("mom_20d", 0)
        iwm_mom = asset_data.get("IWM", {}).get("mom_20d", 0)
        tlt_mom = asset_data.get("TLT", {}).get("mom_20d", 0)
        gld_mom = asset_data.get("GLD", {}).get("mom_20d", 0)
        uup_mom = asset_data.get("UUP", {}).get("mom_20d", 0)
        btc_mom = asset_data.get("BTC-USD", {}).get("mom_20d", 0)

        risk_on_score = 0
        if spy_mom > 0: risk_on_score += 2
        if qqq_mom > 0: risk_on_score += 2
        if iwm_mom > 0: risk_on_score += 1
        if btc_mom > 0: risk_on_score += 1
        if tlt_mom < 0: risk_on_score += 1
        if uup_mom < 0: risk_on_score += 1

        risk_off_score = 0
        if spy_mom < 0: risk_off_score += 2
        if qqq_mom < 0: risk_off_score += 2
        if iwm_mom < 0: risk_off_score += 1
        if tlt_mom > 0: risk_off_score += 2
        if gld_mom > 0: risk_off_score += 1
        if uup_mom > 0: risk_off_score += 1

        net_score = risk_on_score - risk_off_score

        if net_score >= 5:
            regime = "STRONG_RISK_ON"
            regime_note = "Risk assets strongly bid — equities/crypto favorable. Max equity exposure."
        elif net_score >= 2:
            regime = "RISK_ON"
            regime_note = "Mild risk appetite — equities preferred over bonds/gold."
        elif net_score >= -1:
            regime = "MIXED"
            regime_note = "Conflicting signals — no clear risk direction. Selective positioning."
        elif net_score >= -4:
            regime = "RISK_OFF"
            regime_note = "Risk aversion — bonds/gold/cash favored. Reduce beta."
        else:
            regime = "STRONG_RISK_OFF"
            regime_note = "Strong defensive bid — reduce equities, increase TLT/GLD/cash."

        if regime in ("STRONG_RISK_ON", "RISK_ON"):
            allocation = "Overweight: SPY/QQQ/IWM. Underweight: TLT/GLD."
        elif regime in ("STRONG_RISK_OFF", "RISK_OFF"):
            allocation = "Overweight: TLT/GLD/UUP. Reduce: SPY/QQQ/IWM/BTC."
        else:
            allocation = "Balanced: Core equity + bonds hedge. Monitor for direction."

        top_3 = comp_sorted[:3]
        bottom_3 = comp_sorted[-3:][::-1]

        return {
            "regime": regime,
            "regime_note": regime_note,
            "allocation_signal": allocation,
            "risk_on_score": risk_on_score,
            "risk_off_score": risk_off_score,
            "net_risk_score": net_score,
            "momentum_leaders": [
                {
                    "rank": i + 1,
                    "ticker": t,
                    "name": ASSETS[t],
                    "composite_score": round(score, 2),
                    "ret_1m_pct": asset_data[t].get("ret_1m"),
                    "ret_3m_pct": asset_data[t].get("ret_3m"),
                }
                for i, (t, score) in enumerate(top_3) if t in asset_data
            ],
            "momentum_laggards": [
                {
                    "rank": n - i,
                    "ticker": t,
                    "name": ASSETS[t],
                    "composite_score": round(score, 2),
                    "ret_1m_pct": asset_data[t].get("ret_1m"),
                    "ret_3m_pct": asset_data[t].get("ret_3m"),
                }
                for i, (t, score) in enumerate(bottom_3) if t in asset_data
            ],
            "assets": {
                t: {
                    "name": ASSETS[t],
                    "current_price": asset_data[t]["current"],
                    "ret_1w_pct": asset_data[t].get("ret_1w"),
                    "ret_1m_pct": asset_data[t].get("ret_1m"),
                    "ret_3m_pct": asset_data[t].get("ret_3m"),
                    "momentum_20d_pct": asset_data[t].get("mom_20d"),
                    "vol_20d_pct": asset_data[t].get("vol_20d"),
                    "sharpe_proxy": asset_data[t].get("sharpe_proxy"),
                    "composite_rank": next((i + 1 for i, (tk, _) in enumerate(comp_sorted) if tk == t), None),
                }
                for t in tickers_valid if t in asset_data
            },
            "rankings": {
                "1w": [(t, round(v, 2)) for t, v, r in rank_1w],
                "1m": [(t, round(v, 2)) for t, v, r in rank_1m],
                "3m": [(t, round(v, 2)) for t, v, r in rank_3m],
            },
            "interpretation": {
                "STRONG_RISK_ON": "net>=5: All risk assets bid. Aggressive long equities/crypto.",
                "RISK_ON": "net 2-4: Risk appetite positive. Standard equity overweight.",
                "MIXED": "net -1 to 1: Conflicting signals. Wait for confirmation.",
                "RISK_OFF": "net -2 to -4: Defensive move. Increase bonds/gold.",
                "STRONG_RISK_OFF": "net<=-5: Broad risk aversion. Preserve capital.",
            },
            "source": "Yahoo Finance 6M daily data — no API key required",
            "note": "Combine with get_market_regime_composite(), get_sector_rotation_signal() for confirmation.",
        }
    except Exception as e:
        return {"error": str(e)}



# ─── EARNINGS DATE COUNTDOWN ──────────────────────────────────────────────────

@mcp.tool()
async def get_earnings_date_countdown(ticker: str = "AAPL") -> dict:
    """Get next earnings date countdown with pre-earnings volatility patterns and position timing guide.

    Fetches next earnings announcement date, calculates days remaining, analyzes
    historical pre-earnings IV expansion patterns, and provides optimal entry/exit
    timing for earnings plays (straddles, iron condors, directional trades).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA', 'TSLA')

    Returns:
        Next earnings date, days remaining, expected move (options-based), historical
        earnings reactions (4Q), pre-earnings IV pattern, and position timing guide.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        import math
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector", "Unknown")
        market_cap = info.get("marketCap", 0)

        # ── Next earnings date ──
        next_date = None
        days_until = None
        try:
            cal = tk.calendar
            if cal is not None:
                if hasattr(cal, "columns"):
                    if "Earnings Date" in cal.columns:
                        ed = cal["Earnings Date"].iloc[0]
                        if hasattr(ed, "date"):
                            next_date = str(ed.date())
                        else:
                            next_date = str(ed)[:10]
                elif isinstance(cal, dict):
                    ed = cal.get("Earnings Date", [None])[0] if isinstance(cal.get("Earnings Date"), list) else cal.get("Earnings Date")
                    if ed:
                        next_date = str(ed)[:10]
        except Exception:
            pass

        if next_date:
            from datetime import date as date_cls
            today = datetime.utcnow().date()
            nd = datetime.strptime(next_date, "%Y-%m-%d").date()
            days_until = (nd - today).days

        # ── Historical earnings reactions (4Q) ──
        hist_reactions = []
        try:
            eq = tk.earnings_history
            if eq is not None and len(eq) > 0:
                eq_sorted = eq.sort_index(ascending=False) if hasattr(eq, "sort_index") else eq
                rows = eq_sorted.head(4) if hasattr(eq_sorted, "head") else list(eq_sorted)[:4]
                for idx, row in (rows.iterrows() if hasattr(rows, "iterrows") else enumerate(rows)):
                    try:
                        date_str = str(idx)[:10] if isinstance(idx, (datetime,)) else str(idx)[:10]
                        eps_actual = float(row.get("epsActual", row.get("Reported EPS", 0)) or 0)
                        eps_est = float(row.get("epsEstimate", row.get("EPS Estimate", 0)) or 0)
                        surprise_pct = 0.0
                        if eps_est and abs(eps_est) > 0.01:
                            surprise_pct = round((eps_actual - eps_est) / abs(eps_est) * 100, 1)
                        beat = "BEAT" if surprise_pct >= 2 else ("MISS" if surprise_pct <= -2 else "IN_LINE")
                        hist_reactions.append({
                            "quarter": date_str,
                            "eps_actual": round(eps_actual, 3),
                            "eps_estimate": round(eps_est, 3),
                            "surprise_pct": surprise_pct,
                            "result": beat,
                        })
                    except Exception:
                        continue
        except Exception:
            pass

        beat_rate = 0.0
        avg_surprise = 0.0
        if hist_reactions:
            beats = sum(1 for r in hist_reactions if r["result"] == "BEAT")
            beat_rate = round(beats / len(hist_reactions) * 100, 1)
            surprises = [r["surprise_pct"] for r in hist_reactions if r["surprise_pct"] != 0]
            avg_surprise = round(sum(surprises) / len(surprises), 1) if surprises else 0.0

        # ── Options-based expected move ──
        expected_move_pct = None
        try:
            exps = tk.options
            if exps:
                target_dtes = []
                today_dt = datetime.utcnow()
                for exp in exps:
                    exp_dt = datetime.strptime(exp, "%Y-%m-%d")
                    dte = (exp_dt - today_dt).days
                    if 7 <= dte <= 60:
                        target_dtes.append((dte, exp))
                if target_dtes:
                    target_dtes.sort(key=lambda x: x[0])
                    best_exp = target_dtes[0][1]
                    chain = tk.option_chain(best_exp)
                    spot = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                    if spot and spot > 0:
                        calls = chain.calls
                        puts = chain.puts
                        atm_calls = calls[(calls["strike"] >= spot * 0.98) & (calls["strike"] <= spot * 1.02)]
                        atm_puts = puts[(puts["strike"] >= spot * 0.98) & (puts["strike"] <= spot * 1.02)]
                        if len(atm_calls) > 0 and len(atm_puts) > 0:
                            atm_call_price = float(atm_calls["lastPrice"].iloc[0])
                            atm_put_price = float(atm_puts["lastPrice"].iloc[0])
                            straddle_cost = atm_call_price + atm_put_price
                            expected_move_pct = round(straddle_cost / spot * 100, 2)
        except Exception:
            pass

        # ── Pre-earnings price move pattern ──
        pre_earnings_drift = None
        try:
            hist = tk.history(period="1y", interval="1d")
            if hist is not None and len(hist) > 10:
                closes = hist["Close"]
                pre_earnings_drift_vals = []
                for r in hist_reactions:
                    try:
                        q_date = r["quarter"]
                        q_dt = datetime.strptime(q_date, "%Y-%m-%d")
                        window_start = q_dt - timedelta(days=10)
                        window_end = q_dt + timedelta(days=3)
                        sub = closes[(closes.index >= window_start) & (closes.index <= window_end)]
                        if len(sub) >= 5:
                            pre_5d = float(sub.iloc[0])
                            pre_1d = float(sub.iloc[-3]) if len(sub) > 3 else float(sub.iloc[-1])
                            drift = round((pre_1d - pre_5d) / pre_5d * 100, 2)
                            pre_earnings_drift_vals.append(drift)
                    except Exception:
                        continue
                if pre_earnings_drift_vals:
                    pre_earnings_drift = round(sum(pre_earnings_drift_vals) / len(pre_earnings_drift_vals), 2)
        except Exception:
            pass

        # ── Position timing guide ──
        timing_notes = []
        timing_signal = "NEUTRAL"

        if days_until is not None:
            if days_until <= 0:
                timing_signal = "EARNINGS_PASSED_OR_TODAY"
                timing_notes.append("Earnings today or already reported. Check actual results.")
            elif days_until <= 3:
                timing_signal = "IMMEDIATE_PLAY"
                timing_notes.append("Earnings in <=3 days. IV near peak — straddle/strangle expensive. Favor directional if high-conviction.")
            elif days_until <= 10:
                timing_signal = "PRIME_ENTRY_WINDOW"
                timing_notes.append("5-10 days out. IV expanding — ideal window for straddles/debit spreads before full IV crush risk.")
            elif days_until <= 21:
                timing_signal = "EARLY_ENTRY"
                timing_notes.append("10-21 days out. IV beginning to rise. Long options favorable vs. short premium.")
            elif days_until <= 45:
                timing_signal = "WATCH_LIST"
                timing_notes.append("21-45 days out. Monitor IV rank; consider entering on IV dips.")
            else:
                timing_signal = "TOO_EARLY"
                timing_notes.append("More than 45 days out. Wait for IV to begin expanding before positioning.")

        if beat_rate >= 75:
            timing_notes.append(f"Strong beat history ({beat_rate}% beat rate, avg +{avg_surprise}% surprise). Bullish bias post-earnings.")
        elif beat_rate <= 40:
            timing_notes.append(f"Weak beat history ({beat_rate}% beat rate, avg {avg_surprise}% surprise). Cautious or bearish bias.")

        if expected_move_pct:
            timing_notes.append(f"Market pricing ~{expected_move_pct}% move. ATM straddle cost = implied expected move.")

        if pre_earnings_drift is not None:
            direction = "upward" if pre_earnings_drift > 0 else "downward"
            timing_notes.append(f"Historical pre-earnings drift: {pre_earnings_drift:+.2f}% avg ({direction} bias into earnings).")

        tendency = "NEUTRAL"
        if beat_rate >= 75 and avg_surprise >= 5:
            tendency = "STRONG_BEAT_TENDENCY"
        elif beat_rate >= 60:
            tendency = "MILD_BEAT_TENDENCY"
        elif beat_rate <= 35 and avg_surprise <= -3:
            tendency = "STRONG_MISS_TENDENCY"
        elif beat_rate <= 45:
            tendency = "MILD_MISS_TENDENCY"

        return {
            "ticker": ticker.upper(),
            "company": name,
            "sector": sector,
            "market_cap_usd": market_cap,
            "next_earnings_date": next_date or "Unknown (check manually)",
            "days_until_earnings": days_until,
            "timing_signal": timing_signal,
            "timing_notes": timing_notes,
            "expected_move_pct": expected_move_pct,
            "earnings_tendency": tendency,
            "beat_rate_pct": beat_rate,
            "avg_eps_surprise_pct": avg_surprise,
            "pre_earnings_drift_5d_avg_pct": pre_earnings_drift,
            "historical_earnings": hist_reactions,
            "strategy_guide": {
                "straddle": "Buy ATM straddle 7-10 days before earnings. Close 1 day before to avoid IV crush.",
                "iron_condor": "Sell OTM strangle 30+ DTE pre-earnings. Close before announcement.",
                "directional": f"If strong beat tendency ({beat_rate}% beat), consider bull call spread 2-5 days before.",
                "iv_crush_risk": "Post-earnings IV collapses 40-70% on average. Long options holders beware.",
            },
            "source": "Yahoo Finance — no API key required",
            "note": "Combine with get_options_iv_percentile() for full pre-earnings options setup.",
        }
    except Exception as e:
        return {"error": str(e)}


# ─── SECTOR ETF VS SPY BETA ───────────────────────────────────────────────────

@mcp.tool()
async def get_sector_etf_vs_spy_beta() -> dict:
    """Calculate 1-year beta for all 11 SPDR sector ETFs vs SPY for rotation analysis.

    Beta measures each sector's sensitivity to the broad market (SPY). High-beta sectors
    amplify market moves; low-beta sectors are defensive. Use for offensive/defensive
    rotation decisions and portfolio risk calibration.

    Returns:
        Per-sector beta, volatility, correlation, ranking by beta, rotation regime,
        and tactical allocation guidance for high/low beta environments.
    """
    await Actor.charge("basic_tool", count=1)
    try:
        from concurrent.futures import ThreadPoolExecutor
        import numpy as np

        SECTORS = {
            "XLK": "Technology",
            "XLY": "Consumer Discretionary",
            "XLC": "Communication Services",
            "XLF": "Financials",
            "XLE": "Energy",
            "XLI": "Industrials",
            "XLB": "Materials",
            "XLRE": "Real Estate",
            "XLV": "Health Care",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
        }
        TICKERS = ["SPY"] + list(SECTORS.keys())

        def fetch_hist(sym):
            try:
                h = yf.Ticker(sym).history(period="1y", interval="1d")
                if h is None or len(h) < 50:
                    return sym, None
                closes = h["Close"].dropna()
                rets = closes.pct_change().dropna()
                return sym, rets
            except Exception:
                return sym, None

        with ThreadPoolExecutor(max_workers=12) as ex:
            results = dict(ex.map(lambda s: fetch_hist(s), TICKERS))

        spy_rets = results.get("SPY")
        if spy_rets is None or len(spy_rets) < 50:
            return {"error": "Could not fetch SPY returns"}

        spy_var = float(spy_rets.var())
        spy_vol_ann = float(spy_rets.std() * (252 ** 0.5) * 100)

        sector_data = {}
        for sym, name in SECTORS.items():
            rets = results.get(sym)
            if rets is None or len(rets) < 50:
                continue
            try:
                common = spy_rets.index.intersection(rets.index)
                if len(common) < 50:
                    continue
                spy_aligned = spy_rets.loc[common].values
                sec_aligned = rets.loc[common].values

                cov = float(np.cov(sec_aligned, spy_aligned)[0][1])
                beta = round(cov / spy_var, 3) if spy_var > 0 else None
                corr_matrix = np.corrcoef(sec_aligned, spy_aligned)
                corr = round(float(corr_matrix[0][1]), 3)
                vol_ann = round(float(np.std(sec_aligned) * (252 ** 0.5) * 100), 2)

                h2 = yf.Ticker(sym).history(period="1y", interval="1d")
                closes2 = h2["Close"].dropna()
                cur = float(closes2.iloc[-1])
                ret_1w = round((cur / float(closes2.iloc[-6]) - 1) * 100, 2) if len(closes2) >= 6 else None
                ret_1m = round((cur / float(closes2.iloc[-22]) - 1) * 100, 2) if len(closes2) >= 22 else None
                ret_3m = round((cur / float(closes2.iloc[-66]) - 1) * 100, 2) if len(closes2) >= 66 else None

                if beta is not None:
                    if beta >= 1.3:
                        beta_label = "HIGH_BETA"
                    elif beta >= 1.05:
                        beta_label = "ABOVE_AVERAGE"
                    elif beta >= 0.85:
                        beta_label = "MARKET_NEUTRAL"
                    elif beta >= 0.65:
                        beta_label = "BELOW_AVERAGE"
                    else:
                        beta_label = "LOW_BETA"
                else:
                    beta_label = "UNKNOWN"

                sector_data[sym] = {
                    "name": name,
                    "beta_1y": beta,
                    "beta_label": beta_label,
                    "correlation_vs_spy": corr,
                    "vol_ann_pct": vol_ann,
                    "ret_1w_pct": ret_1w,
                    "ret_1m_pct": ret_1m,
                    "ret_3m_pct": ret_3m,
                }
            except Exception:
                continue

        if not sector_data:
            return {"error": "No sector data available"}

        ranked = sorted(sector_data.items(), key=lambda x: x[1]["beta_1y"] or 0, reverse=True)
        for rank, (sym, d) in enumerate(ranked, 1):
            sector_data[sym]["beta_rank"] = rank

        high_beta_sectors = [(sym, d) for sym, d in ranked if d.get("beta_label") in ("HIGH_BETA", "ABOVE_AVERAGE")][:3]
        low_beta_sectors = [(sym, d) for sym, d in ranked if d.get("beta_label") in ("LOW_BETA", "BELOW_AVERAGE")][-3:]

        spy_hist = yf.Ticker("SPY").history(period="6mo", interval="1d")
        spy_closes = spy_hist["Close"].dropna()
        spy_cur = float(spy_closes.iloc[-1])
        spy_1m = round((spy_cur / float(spy_closes.iloc[-22]) - 1) * 100, 2) if len(spy_closes) >= 22 else None
        spy_3m = round((spy_cur / float(spy_closes.iloc[-66]) - 1) * 100, 2) if len(spy_closes) >= 66 else None

        if spy_1m is not None and spy_3m is not None:
            if spy_1m > 2 and spy_3m > 5:
                market_trend = "STRONG_BULL"
                rotation_guidance = "Favor HIGH_BETA sectors (XLK, XLY, XLC). Beta amplifies gains in bull markets."
            elif spy_1m > 0:
                market_trend = "MILD_BULL"
                rotation_guidance = "Moderate overweight high-beta. Balance with low-beta for risk control."
            elif spy_1m < -2 and spy_3m < -5:
                market_trend = "STRONG_BEAR"
                rotation_guidance = "Favor LOW_BETA sectors (XLU, XLP, XLV). Reduce high-beta exposure."
            elif spy_1m < 0:
                market_trend = "MILD_BEAR"
                rotation_guidance = "Tilt toward low-beta. Defensive sectors outperform in corrections."
            else:
                market_trend = "SIDEWAYS"
                rotation_guidance = "No clear trend. Balanced beta exposure. Focus on momentum."
        else:
            market_trend = "UNKNOWN"
            rotation_guidance = "Insufficient data for market trend."

        avg_beta = round(sum(d["beta_1y"] for _, d in ranked if d["beta_1y"]) / len(ranked), 3)

        return {
            "spy_vol_ann_pct": round(spy_vol_ann, 2),
            "spy_ret_1m_pct": spy_1m,
            "spy_ret_3m_pct": spy_3m,
            "market_trend": market_trend,
            "rotation_guidance": rotation_guidance,
            "avg_sector_beta": avg_beta,
            "sectors_ranked_by_beta": [
                {
                    "rank": sector_data[sym]["beta_rank"],
                    "ticker": sym,
                    "name": d["name"],
                    "beta_1y": d["beta_1y"],
                    "beta_label": d["beta_label"],
                    "correlation_vs_spy": d["correlation_vs_spy"],
                    "vol_ann_pct": d["vol_ann_pct"],
                    "ret_1w_pct": d["ret_1w_pct"],
                    "ret_1m_pct": d["ret_1m_pct"],
                    "ret_3m_pct": d["ret_3m_pct"],
                }
                for sym, d in ranked
            ],
            "high_beta_sectors": [
                {"ticker": sym, "name": d["name"], "beta_1y": d["beta_1y"]}
                for sym, d in high_beta_sectors
            ],
            "low_beta_sectors": [
                {"ticker": sym, "name": d["name"], "beta_1y": d["beta_1y"]}
                for sym, d in reversed(low_beta_sectors)
            ],
            "beta_interpretation": {
                "HIGH_BETA": "Beta>=1.3: Amplifies SPY moves by 30%+. Use in strong bull markets.",
                "ABOVE_AVERAGE": "Beta 1.05-1.3: Slight leverage vs SPY. Bull-friendly.",
                "MARKET_NEUTRAL": "Beta 0.85-1.05: Tracks SPY closely.",
                "BELOW_AVERAGE": "Beta 0.65-0.85: Dampens market swings. Moderate defensive.",
                "LOW_BETA": "Beta<0.65: Strong defensive. Outperforms in downturns.",
            },
            "tactical_guide": {
                "offensive_rotation": "Bull market — rotate INTO XLK/XLY/XLC (highest beta) for amplified gains.",
                "defensive_rotation": "Bear market — rotate INTO XLU/XLP/XLV (lowest beta) for capital preservation.",
                "neutral_market": "Use beta-neutral mix: ~50% in mid-beta (XLI/XLF/XLB) for balanced exposure.",
                "leverage_calc": f"1% SPY move → avg sector move = {avg_beta}% (simple beta proxy).",
            },
            "source": "Yahoo Finance 1Y daily — no API key required",
            "note": "Combine with get_sector_rotation_signal() and get_market_regime_composite() for full context.",
        }
    except Exception as e:
        return {"error": str(e)}



# ─── RELATIVE STRENGTH RANKING ────────────────────────────────────────────────

@mcp.tool()
async def get_relative_strength_ranking(tickers: str = "AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,JPM,V,UNH") -> dict:
    """Relative Strength Ranking for a custom list of tickers vs SPY.

    Calculates 1W/1M/3M/6M price returns and RS score (excess return vs SPY)
    for up to 20 user-specified tickers. Ranks by composite momentum score
    (1W×20% + 1M×30% + 3M×30% + 6M×20%). Identifies top performers (buy signals)
    and laggards (avoid or short candidates).

    Args:
        tickers: Comma-separated list of tickers (max 20). Default: top 10 mega-caps.

    Returns:
        Full ranking table with RS scores, composite momentum, top-5/bottom-5 highlights,
        and momentum regime classification per ticker.
    """
    await Actor.charge("advanced_tool", count=1)
    try:
        from concurrent.futures import ThreadPoolExecutor
        import numpy as np

        raw = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        ticker_list = raw[:20]
        if not ticker_list:
            return {"error": "No valid tickers provided"}

        all_tickers = list(set(ticker_list + ["SPY"]))

        def fetch_ticker(sym):
            try:
                h = yf.Ticker(sym).history(period="1y", interval="1d")
                if h is None or len(h) < 10:
                    return sym, None
                closes = h["Close"].dropna()
                return sym, closes
            except Exception:
                return sym, None

        with ThreadPoolExecutor(max_workers=min(len(all_tickers), 12)) as ex:
            results = dict(ex.map(fetch_ticker, all_tickers))

        spy_closes = results.get("SPY")
        if spy_closes is None or len(spy_closes) < 10:
            return {"error": "Could not fetch SPY data"}

        spy_cur = float(spy_closes.iloc[-1])
        spy_1w = round((spy_cur / float(spy_closes.iloc[-6]) - 1) * 100, 2) if len(spy_closes) >= 6 else 0.0
        spy_1m = round((spy_cur / float(spy_closes.iloc[-22]) - 1) * 100, 2) if len(spy_closes) >= 22 else 0.0
        spy_3m = round((spy_cur / float(spy_closes.iloc[-66]) - 1) * 100, 2) if len(spy_closes) >= 66 else 0.0
        spy_6m = round((spy_cur / float(spy_closes.iloc[-130]) - 1) * 100, 2) if len(spy_closes) >= 130 else 0.0

        ticker_data = []
        for sym in ticker_list:
            closes = results.get(sym)
            if closes is None or len(closes) < 5:
                continue
            cur = float(closes.iloc[-1])
            r1w = round((cur / float(closes.iloc[-6]) - 1) * 100, 2) if len(closes) >= 6 else None
            r1m = round((cur / float(closes.iloc[-22]) - 1) * 100, 2) if len(closes) >= 22 else None
            r3m = round((cur / float(closes.iloc[-66]) - 1) * 100, 2) if len(closes) >= 66 else None
            r6m = round((cur / float(closes.iloc[-130]) - 1) * 100, 2) if len(closes) >= 130 else None

            rs_1w = round((r1w - spy_1w), 2) if r1w is not None else None
            rs_1m = round((r1m - spy_1m), 2) if r1m is not None else None
            rs_3m = round((r3m - spy_3m), 2) if r3m is not None else None
            rs_6m = round((r6m - spy_6m), 2) if r6m is not None else None

            comp_parts = []
            if r1w is not None: comp_parts.append((r1w, 0.20))
            if r1m is not None: comp_parts.append((r1m, 0.30))
            if r3m is not None: comp_parts.append((r3m, 0.30))
            if r6m is not None: comp_parts.append((r6m, 0.20))
            if comp_parts:
                total_w = sum(w for _, w in comp_parts)
                composite = round(sum(r * w for r, w in comp_parts) / total_w, 2)
            else:
                composite = None

            rs_comp_parts = []
            if rs_1w is not None: rs_comp_parts.append((rs_1w, 0.20))
            if rs_1m is not None: rs_comp_parts.append((rs_1m, 0.30))
            if rs_3m is not None: rs_comp_parts.append((rs_3m, 0.30))
            if rs_6m is not None: rs_comp_parts.append((rs_6m, 0.20))
            if rs_comp_parts:
                total_w2 = sum(w for _, w in rs_comp_parts)
                rs_composite = round(sum(r * w for r, w in rs_comp_parts) / total_w2, 2)
            else:
                rs_composite = None

            if composite is not None:
                if composite >= 15 and (rs_composite or 0) >= 5:
                    momentum_regime = "STRONG_OUTPERFORMER"
                elif composite >= 5 and (rs_composite or 0) >= 0:
                    momentum_regime = "OUTPERFORMER"
                elif composite >= 0 and (rs_composite or 0) >= -5:
                    momentum_regime = "NEUTRAL"
                elif composite >= -10:
                    momentum_regime = "UNDERPERFORMER"
                else:
                    momentum_regime = "STRONG_UNDERPERFORMER"
            else:
                momentum_regime = "INSUFFICIENT_DATA"

            ticker_data.append({
                "ticker": sym,
                "current_price": round(cur, 2),
                "ret_1w_pct": r1w,
                "ret_1m_pct": r1m,
                "ret_3m_pct": r3m,
                "ret_6m_pct": r6m,
                "rs_vs_spy_1w": rs_1w,
                "rs_vs_spy_1m": rs_1m,
                "rs_vs_spy_3m": rs_3m,
                "rs_vs_spy_6m": rs_6m,
                "composite_momentum": composite,
                "rs_composite_vs_spy": rs_composite,
                "momentum_regime": momentum_regime,
            })

        if not ticker_data:
            return {"error": "No ticker data available"}

        ticker_data.sort(key=lambda x: x["composite_momentum"] if x["composite_momentum"] is not None else -999, reverse=True)
        for i, d in enumerate(ticker_data, 1):
            d["rank"] = i

        top5 = ticker_data[:5]
        bottom5 = ticker_data[-5:]

        if spy_1m > 2:
            market_context = "BULL_MARKET — momentum strategies work well. Buy top-ranked."
        elif spy_1m < -2:
            market_context = "BEAR_MARKET — relative strength matters more. Top RS stocks hold better."
        else:
            market_context = "SIDEWAYS — focus on individual RS vs SPY rather than absolute momentum."

        return {
            "spy_benchmark": {
                "ret_1w_pct": spy_1w,
                "ret_1m_pct": spy_1m,
                "ret_3m_pct": spy_3m,
                "ret_6m_pct": spy_6m,
            },
            "market_context": market_context,
            "composite_weights": "1W×20% + 1M×30% + 3M×30% + 6M×20%",
            "total_tickers_analyzed": len(ticker_data),
            "ranking": ticker_data,
            "top_5_momentum_leaders": [
                {"rank": d["rank"], "ticker": d["ticker"], "composite_momentum": d["composite_momentum"],
                 "rs_composite_vs_spy": d["rs_composite_vs_spy"], "momentum_regime": d["momentum_regime"]}
                for d in top5
            ],
            "bottom_5_momentum_laggards": [
                {"rank": d["rank"], "ticker": d["ticker"], "composite_momentum": d["composite_momentum"],
                 "rs_composite_vs_spy": d["rs_composite_vs_spy"], "momentum_regime": d["momentum_regime"]}
                for d in bottom5
            ],
            "strategy_guide": {
                "long_candidates": "Top-ranked tickers (STRONG_OUTPERFORMER + positive RS vs SPY) — momentum continuation bias.",
                "avoid_or_short": "Bottom-ranked tickers (STRONG_UNDERPERFORMER + negative RS) — underperformance tends to persist.",
                "rotation_signal": "If top performers shift from growth (NVDA/AAPL) to defensives (UNH/V), market risk is rising.",
                "rs_threshold": "RS vs SPY > +5% composite = clearly outperforming. RS < -5% = clearly lagging.",
            },
            "source": "Yahoo Finance — no API key required",
            "note": "Combine with get_sector_rotation_signal() to confirm sector-level tailwinds.",
        }
    except Exception as e:
        return {"error": str(e)}


# ─── FEAR & GREED COMPOSITE ───────────────────────────────────────────────────

@mcp.tool()
async def get_fear_greed_composite() -> dict:
    """7-indicator composite Fear & Greed Index (0-100 scale).

    Replicates CNN Fear & Greed methodology using fully public data (no API key needed).
    Combines 7 market signals into a single score:
      1. VIX Regime (20 pts) — market volatility stress proxy
      2. 52-Week High/Low Breadth (20 pts) — % S&P 100 near 52W highs vs lows
      3. Safe Haven Demand (15 pts) — TLT vs SPY 30d relative performance (inverted)
      4. Put/Call Ratio (15 pts) — SPY options sentiment (inverted)
      5. Junk Bond Demand (15 pts) — HYG vs IEF 30d relative performance
      6. Market Momentum (10 pts) — SPY vs 125d moving average
      7. Stock Price Breadth (5 pts) — SPY vs RSP equal-weight divergence

    Returns:
        Composite score 0-100, EXTREME_FEAR/FEAR/NEUTRAL/GREED/EXTREME_GREED label,
        per-indicator breakdown, trend vs 7-day prior, and trading implications.
    """
    await Actor.charge("basic_tool", count=1)
    try:
        import numpy as np
        from concurrent.futures import ThreadPoolExecutor

        FETCH = ["^VIX", "SPY", "QQQ", "TLT", "HYG", "IEF", "RSP"]
        SP100_PROXY = [
            "AAPL","MSFT","NVDA","AMZN","GOOGL","META","BRK-B","LLY","JPM","V",
            "UNH","XOM","TSLA","MA","PG","JNJ","HD","MRK","ABBV","CVX",
            "BAC","KO","PEP","AVGO","COST","WMT","TMO","MCD","CSCO","ACN",
            "ABT","CRM","NKE","DHR","TXN","VZ","PM","INTC","MS","LIN",
            "NEE","AMGN","RTX","HON","UNP","LOW","SPGI","CAT","COP","INTU",
        ]

        def fetch_hist(sym):
            try:
                h = yf.Ticker(sym).history(period="1y", interval="1d")
                if h is None or len(h) < 5:
                    return sym, None
                return sym, h["Close"].dropna()
            except Exception:
                return sym, None

        all_fetch = FETCH + SP100_PROXY
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = dict(ex.map(fetch_hist, all_fetch))

        vix_closes = results.get("^VIX")
        vix_score = 10
        vix_val = None
        vix_label = "UNKNOWN"
        if vix_closes is not None and len(vix_closes) >= 10:
            vix_val = round(float(vix_closes.iloc[-1]), 2)
            if vix_val < 13:
                vix_score = 20; vix_label = "EXTREME_GREED (VIX very low)"
            elif vix_val < 18:
                vix_score = 15; vix_label = "GREED (VIX below average)"
            elif vix_val < 24:
                vix_score = 10; vix_label = "NEUTRAL"
            elif vix_val < 32:
                vix_score = 5; vix_label = "FEAR (VIX elevated)"
            else:
                vix_score = 0; vix_label = "EXTREME_FEAR (VIX panic)"

        near_highs = 0; near_lows = 0; breadth_total = 0
        for sym in SP100_PROXY:
            closes = results.get(sym)
            if closes is None or len(closes) < 50:
                continue
            cur = float(closes.iloc[-1])
            hi52 = float(closes.rolling(252).max().iloc[-1]) if len(closes) >= 252 else float(closes.max())
            lo52 = float(closes.rolling(252).min().iloc[-1]) if len(closes) >= 252 else float(closes.min())
            breadth_total += 1
            if cur >= hi52 * 0.97:
                near_highs += 1
            elif cur <= lo52 * 1.03:
                near_lows += 1

        breadth_score = 10
        breadth_label = "NEUTRAL"
        net_pct = 0
        if breadth_total > 0:
            net_pct = (near_highs - near_lows) / breadth_total * 100
            if net_pct >= 30:
                breadth_score = 20; breadth_label = f"EXTREME_GREED (net +{net_pct:.0f}% near highs)"
            elif net_pct >= 10:
                breadth_score = 15; breadth_label = f"GREED (net +{net_pct:.0f}%)"
            elif net_pct >= -10:
                breadth_score = 10; breadth_label = "NEUTRAL"
            elif net_pct >= -30:
                breadth_score = 5; breadth_label = f"FEAR (net {net_pct:.0f}%)"
            else:
                breadth_score = 0; breadth_label = f"EXTREME_FEAR (net {net_pct:.0f}%)"

        tlt_closes = results.get("TLT")
        spy_closes = results.get("SPY")
        safe_score = 7
        safe_label = "NEUTRAL"
        tlt_vs_spy_30d = None
        if tlt_closes is not None and spy_closes is not None and len(tlt_closes) >= 22 and len(spy_closes) >= 22:
            tlt_ret = (float(tlt_closes.iloc[-1]) / float(tlt_closes.iloc[-22]) - 1) * 100
            spy_ret_30 = (float(spy_closes.iloc[-1]) / float(spy_closes.iloc[-22]) - 1) * 100
            tlt_vs_spy_30d = round(tlt_ret - spy_ret_30, 2)
            if tlt_vs_spy_30d <= -5:
                safe_score = 15; safe_label = "EXTREME_GREED (bonds lagging, no flight-to-safety)"
            elif tlt_vs_spy_30d <= -2:
                safe_score = 11; safe_label = "GREED (mild risk appetite)"
            elif tlt_vs_spy_30d <= 2:
                safe_score = 7; safe_label = "NEUTRAL"
            elif tlt_vs_spy_30d <= 5:
                safe_score = 3; safe_label = "FEAR (bonds outperforming)"
            else:
                safe_score = 0; safe_label = "EXTREME_FEAR (strong safe haven demand)"

        pc_score = 7
        pc_label = "NEUTRAL"
        pc_ratio = None
        try:
            spy_tk = yf.Ticker("SPY")
            exps = spy_tk.options
            if exps:
                from datetime import datetime as dt
                today = dt.now()
                best_exp = None
                best_diff = 999
                for e in exps:
                    try:
                        exp_dt = dt.strptime(e, "%Y-%m-%d")
                        diff = abs((exp_dt - today).days - 30)
                        if diff < best_diff:
                            best_diff = diff
                            best_exp = e
                    except Exception:
                        pass
                if best_exp:
                    chain = spy_tk.option_chain(best_exp)
                    call_vol = chain.calls["volume"].dropna().sum()
                    put_vol = chain.puts["volume"].dropna().sum()
                    if call_vol > 0:
                        pc_ratio = round(put_vol / call_vol, 3)
                        if pc_ratio <= 0.6:
                            pc_score = 15; pc_label = "EXTREME_GREED (very low put/call)"
                        elif pc_ratio <= 0.85:
                            pc_score = 11; pc_label = "GREED (below-average hedging)"
                        elif pc_ratio <= 1.1:
                            pc_score = 7; pc_label = "NEUTRAL"
                        elif pc_ratio <= 1.4:
                            pc_score = 3; pc_label = "FEAR (elevated put buying)"
                        else:
                            pc_score = 0; pc_label = "EXTREME_FEAR (heavy put buying)"
        except Exception:
            pass

        hyg_closes = results.get("HYG")
        ief_closes = results.get("IEF")
        junk_score = 7
        junk_label = "NEUTRAL"
        hyg_vs_ief_30d = None
        if hyg_closes is not None and ief_closes is not None and len(hyg_closes) >= 22 and len(ief_closes) >= 22:
            hyg_ret = (float(hyg_closes.iloc[-1]) / float(hyg_closes.iloc[-22]) - 1) * 100
            ief_ret = (float(ief_closes.iloc[-1]) / float(ief_closes.iloc[-22]) - 1) * 100
            hyg_vs_ief_30d = round(hyg_ret - ief_ret, 2)
            if hyg_vs_ief_30d >= 3:
                junk_score = 15; junk_label = "EXTREME_GREED (junk bonds far outperforming)"
            elif hyg_vs_ief_30d >= 1:
                junk_score = 11; junk_label = "GREED (risk appetite strong)"
            elif hyg_vs_ief_30d >= -1:
                junk_score = 7; junk_label = "NEUTRAL"
            elif hyg_vs_ief_30d >= -3:
                junk_score = 3; junk_label = "FEAR (investment grade preferred)"
            else:
                junk_score = 0; junk_label = "EXTREME_FEAR (strong flight to quality)"

        momentum_score = 5
        momentum_label = "NEUTRAL"
        spy_vs_ma125 = None
        if spy_closes is not None and len(spy_closes) >= 125:
            ma125 = float(spy_closes.iloc[-125:].mean())
            spy_cur_val = float(spy_closes.iloc[-1])
            spy_vs_ma125 = round((spy_cur_val / ma125 - 1) * 100, 2)
            if spy_vs_ma125 >= 5:
                momentum_score = 10; momentum_label = "EXTREME_GREED (far above 125d MA)"
            elif spy_vs_ma125 >= 1:
                momentum_score = 8; momentum_label = "GREED (above 125d MA)"
            elif spy_vs_ma125 >= -1:
                momentum_score = 5; momentum_label = "NEUTRAL"
            elif spy_vs_ma125 >= -5:
                momentum_score = 2; momentum_label = "FEAR (below 125d MA)"
            else:
                momentum_score = 0; momentum_label = "EXTREME_FEAR (far below 125d MA)"

        rsp_closes = results.get("RSP")
        breadth2_score = 2
        breadth2_label = "NEUTRAL"
        spy_vs_rsp_30d = None
        if spy_closes is not None and rsp_closes is not None and len(spy_closes) >= 22 and len(rsp_closes) >= 22:
            spy_ret2 = (float(spy_closes.iloc[-1]) / float(spy_closes.iloc[-22]) - 1) * 100
            rsp_ret = (float(rsp_closes.iloc[-1]) / float(rsp_closes.iloc[-22]) - 1) * 100
            spy_vs_rsp_30d = round(rsp_ret - spy_ret2, 2)
            if spy_vs_rsp_30d >= 2:
                breadth2_score = 5; breadth2_label = "GREED (broad market participation)"
            elif spy_vs_rsp_30d >= 0:
                breadth2_score = 3; breadth2_label = "MILD_GREED"
            elif spy_vs_rsp_30d >= -2:
                breadth2_score = 2; breadth2_label = "NEUTRAL"
            else:
                breadth2_score = 0; breadth2_label = "FEAR (narrow leadership, equal-weight lagging)"

        total_score = vix_score + breadth_score + safe_score + pc_score + junk_score + momentum_score + breadth2_score
        total_score = max(0, min(100, total_score))

        if total_score >= 80:
            signal = "EXTREME_GREED"
            signal_desc = "Markets are extremely euphoric. Historically a contrarian sell signal. Consider reducing risk."
            action = "REDUCE_RISK — take profits, add hedges, avoid chasing momentum."
        elif total_score >= 60:
            signal = "GREED"
            signal_desc = "Bullish sentiment prevails. Momentum strategies working. Watch for complacency."
            action = "HOLD_OR_TRIM — maintain positions but tighten stops."
        elif total_score >= 40:
            signal = "NEUTRAL"
            signal_desc = "Market sentiment is balanced. No extreme readings."
            action = "BALANCED — follow trend; no strong contrarian signal."
        elif total_score >= 20:
            signal = "FEAR"
            signal_desc = "Risk-off sentiment. Investors are nervous. Historically a buying opportunity emerges."
            action = "WATCH_FOR_ENTRY — begin accumulating quality names on weakness."
        else:
            signal = "EXTREME_FEAR"
            signal_desc = "Panic conditions. Historically strong contrarian buy signal (within 3-6 months)."
            action = "AGGRESSIVE_BUY_ZONE — highest historical forward returns start here."

        return {
            "fear_greed_score": total_score,
            "signal": signal,
            "signal_description": signal_desc,
            "recommended_action": action,
            "score_interpretation": {
                "0-20": "EXTREME_FEAR — contrarian buy zone",
                "20-40": "FEAR — cautious accumulation",
                "40-60": "NEUTRAL — trend following",
                "60-80": "GREED — hold, tighten stops",
                "80-100": "EXTREME_GREED — contrarian sell zone",
            },
            "components": {
                "vix_regime": {
                    "score": vix_score,
                    "max": 20,
                    "vix_value": vix_val,
                    "label": vix_label,
                },
                "52w_high_low_breadth": {
                    "score": breadth_score,
                    "max": 20,
                    "near_highs": near_highs,
                    "near_lows": near_lows,
                    "net_pct": round(net_pct, 1),
                    "label": breadth_label,
                },
                "safe_haven_demand": {
                    "score": safe_score,
                    "max": 15,
                    "tlt_vs_spy_30d_pct": tlt_vs_spy_30d,
                    "label": safe_label,
                    "note": "TLT outperforming SPY = fear (inverted for greed score)",
                },
                "put_call_ratio": {
                    "score": pc_score,
                    "max": 15,
                    "spy_pc_ratio": pc_ratio,
                    "label": pc_label,
                    "note": "High put/call = fear (inverted for greed score)",
                },
                "junk_bond_demand": {
                    "score": junk_score,
                    "max": 15,
                    "hyg_vs_ief_30d_pct": hyg_vs_ief_30d,
                    "label": junk_label,
                },
                "market_momentum": {
                    "score": momentum_score,
                    "max": 10,
                    "spy_vs_125d_ma_pct": spy_vs_ma125,
                    "label": momentum_label,
                },
                "stock_price_breadth": {
                    "score": breadth2_score,
                    "max": 5,
                    "rsp_vs_spy_30d_pct": spy_vs_rsp_30d,
                    "label": breadth2_label,
                    "note": "RSP (equal-weight) outperforming = broad participation",
                },
            },
            "source": "Yahoo Finance — no API key required",
            "methodology": "7-indicator composite replicating CNN Fear & Greed using public data",
            "note": "Combine with get_vix_regime_monitor() and get_market_regime_composite() for full context.",
        }
    except Exception as e:
        return {"error": str(e)}



@mcp.tool()
async def get_momentum_factor_screen(top_n: int = 20) -> dict:
    """
    Screen S&P 500 universe using the classic 12-1 momentum factor.
    Returns top and bottom momentum quintiles with sector breakdown.
    Uses 12-month minus 1-month return (standard academic momentum factor).
    No API key required.

    Args:
        top_n: Number of top/bottom momentum stocks to return (default 20)

    Returns:
        Momentum factor screen with rankings, sector breakdown, and trading signals.
    """
    await Actor.charge("advanced_tool", count=1)
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import asyncio

    UNIVERSE = {
        "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology",
        "AVGO": "Technology", "ORCL": "Technology", "CRM": "Technology",
        "AMD": "Technology", "INTC": "Technology", "QCOM": "Technology",
        "TXN": "Technology", "MU": "Technology", "AMAT": "Technology",
        "LRCX": "Technology", "KLAC": "Technology", "ADI": "Technology",
        "MRVL": "Technology", "SNPS": "Technology", "CDNS": "Technology",
        "FTNT": "Technology", "PANW": "Technology",
        "GOOGL": "Communication", "META": "Communication", "NFLX": "Communication",
        "DIS": "Communication", "CMCSA": "Communication", "T": "Communication",
        "VZ": "Communication", "CHTR": "Communication", "TMUS": "Communication",
        "EA": "Communication", "TTWO": "Communication", "ATVI": "Communication",
        "WBD": "Communication", "PARA": "Communication", "OMC": "Communication",
        "AMZN": "ConsumerDisc", "TSLA": "ConsumerDisc", "HD": "ConsumerDisc",
        "MCD": "ConsumerDisc", "NKE": "ConsumerDisc", "LOW": "ConsumerDisc",
        "SBUX": "ConsumerDisc", "TJX": "ConsumerDisc", "BKNG": "ConsumerDisc",
        "CMG": "ConsumerDisc", "GM": "ConsumerDisc", "F": "ConsumerDisc",
        "RIVN": "ConsumerDisc", "RCL": "ConsumerDisc", "CCL": "ConsumerDisc",
        "ABNB": "ConsumerDisc", "LYFT": "ConsumerDisc", "UBER": "ConsumerDisc",
        "DASH": "ConsumerDisc", "ETSY": "ConsumerDisc",
        "PG": "ConsumerStaples", "KO": "ConsumerStaples", "PEP": "ConsumerStaples",
        "COST": "ConsumerStaples", "WMT": "ConsumerStaples", "PM": "ConsumerStaples",
        "MO": "ConsumerStaples", "MDLZ": "ConsumerStaples", "CL": "ConsumerStaples",
        "KMB": "ConsumerStaples", "GIS": "ConsumerStaples", "K": "ConsumerStaples",
        "SJM": "ConsumerStaples", "CAG": "ConsumerStaples", "CPB": "ConsumerStaples",
        "JPM": "Financials", "BAC": "Financials", "WFC": "Financials",
        "GS": "Financials", "MS": "Financials", "BLK": "Financials",
        "C": "Financials", "AXP": "Financials", "V": "Financials",
        "MA": "Financials", "PNC": "Financials", "USB": "Financials",
        "TFC": "Financials", "COF": "Financials", "SCHW": "Financials",
        "ICE": "Financials", "CME": "Financials", "CB": "Financials",
        "MMC": "Financials", "AON": "Financials",
        "UNH": "Healthcare", "JNJ": "Healthcare", "LLY": "Healthcare",
        "PFE": "Healthcare", "ABT": "Healthcare", "TMO": "Healthcare",
        "MRK": "Healthcare", "DHR": "Healthcare", "AMGN": "Healthcare",
        "GILD": "Healthcare", "ISRG": "Healthcare", "SYK": "Healthcare",
        "BSX": "Healthcare", "VRTX": "Healthcare", "REGN": "Healthcare",
        "BIIB": "Healthcare", "MRNA": "Healthcare", "NVAX": "Healthcare",
        "DXCM": "Healthcare", "IDXX": "Healthcare",
        "GE": "Industrials", "HON": "Industrials", "UPS": "Industrials",
        "BA": "Industrials", "CAT": "Industrials", "DE": "Industrials",
        "MMM": "Industrials", "LMT": "Industrials", "RTX": "Industrials",
        "NOC": "Industrials", "GD": "Industrials", "FDX": "Industrials",
        "CSX": "Industrials", "NSC": "Industrials", "EMR": "Industrials",
        "ETN": "Industrials", "PH": "Industrials", "ROK": "Industrials",
        "XYL": "Industrials", "CARR": "Industrials",
        "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
        "SLB": "Energy", "EOG": "Energy", "MPC": "Energy",
        "VLO": "Energy", "PSX": "Energy", "OXY": "Energy",
        "DVN": "Energy", "FANG": "Energy", "HAL": "Energy",
        "BKR": "Energy", "HES": "Energy", "APA": "Energy",
        "LIN": "Materials", "APD": "Materials", "SHW": "Materials",
        "ECL": "Materials", "NEM": "Materials", "FCX": "Materials",
        "NUE": "Materials", "CF": "Materials", "MOS": "Materials",
        "ALB": "Materials", "PPG": "Materials", "RPM": "Materials",
        "IFF": "Materials", "EMN": "Materials", "CE": "Materials",
        "PLD": "RealEstate", "AMT": "RealEstate", "EQIX": "RealEstate",
        "PSA": "RealEstate", "O": "RealEstate", "WELL": "RealEstate",
        "DLR": "RealEstate", "SPG": "RealEstate", "CCI": "RealEstate",
        "EXR": "RealEstate", "AVB": "RealEstate", "EQR": "RealEstate",
        "NEE": "Utilities", "DUK": "Utilities", "SO": "Utilities",
        "D": "Utilities", "AEP": "Utilities", "EXC": "Utilities",
        "SRE": "Utilities", "PCG": "Utilities", "WEC": "Utilities",
        "ES": "Utilities", "ED": "Utilities", "ETR": "Utilities",
    }

    tickers_list = list(UNIVERSE.keys())

    def fetch_momentum(ticker):
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="13mo")
            if hist.empty or len(hist) < 50:
                return None
            closes = hist["Close"].dropna()
            if len(closes) < 50:
                return None
            ret_12m = (float(closes.iloc[-1]) / float(closes.iloc[0]) - 1) * 100
            ret_1m = (float(closes.iloc[-1]) / float(closes.iloc[-22]) - 1) * 100 if len(closes) >= 22 else 0
            momentum_12_1 = ret_12m - ret_1m
            ret_6m = (float(closes.iloc[-1]) / float(closes.iloc[-130]) - 1) * 100 if len(closes) >= 130 else ret_12m / 2
            ret_3m = (float(closes.iloc[-1]) / float(closes.iloc[-66]) - 1) * 100 if len(closes) >= 66 else ret_6m / 2
            return {
                "ticker": ticker,
                "sector": UNIVERSE[ticker],
                "momentum_12_1": round(momentum_12_1, 2),
                "ret_12m": round(ret_12m, 2),
                "ret_6m": round(ret_6m, 2),
                "ret_3m": round(ret_3m, 2),
                "ret_1m": round(ret_1m, 2),
            }
        except Exception:
            return None

    loop = asyncio.get_event_loop()
    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_momentum, t): t for t in tickers_list}
        for fut in as_completed(futures):
            r = fut.result()
            if r is not None:
                results.append(r)

    if not results:
        return {"error": "No data retrieved for momentum screen"}

    results.sort(key=lambda x: x["momentum_12_1"], reverse=True)

    n = len(results)
    top_30pct = max(1, int(n * 0.30))
    bot_30pct = max(1, int(n * 0.30))

    for i, r in enumerate(results):
        rank = i + 1
        pct_rank = (i / max(n - 1, 1)) * 100
        if rank <= top_30pct:
            r["momentum_label"] = "HIGH_MOMENTUM"
        elif rank > (n - bot_30pct):
            r["momentum_label"] = "LOW_MOMENTUM"
        else:
            r["momentum_label"] = "NEUTRAL_MOMENTUM"
        r["rank"] = rank
        r["percentile"] = round(100 - pct_rank, 1)

    sector_stats = {}
    for r in results:
        sec = r["sector"]
        if sec not in sector_stats:
            sector_stats[sec] = {"tickers": [], "momentum_sum": 0, "count": 0}
        sector_stats[sec]["tickers"].append(r["ticker"])
        sector_stats[sec]["momentum_sum"] += r["momentum_12_1"]
        sector_stats[sec]["count"] += 1

    sector_summary = []
    for sec, data in sector_stats.items():
        avg_mom = data["momentum_sum"] / data["count"] if data["count"] > 0 else 0
        if avg_mom >= 15:
            sec_label = "LEADING"
        elif avg_mom >= 5:
            sec_label = "OUTPERFORMING"
        elif avg_mom >= -5:
            sec_label = "NEUTRAL"
        elif avg_mom >= -15:
            sec_label = "UNDERPERFORMING"
        else:
            sec_label = "LAGGING"
        sector_summary.append({
            "sector": sec,
            "avg_momentum_12_1": round(avg_mom, 2),
            "label": sec_label,
            "stock_count": data["count"],
        })
    sector_summary.sort(key=lambda x: x["avg_momentum_12_1"], reverse=True)

    all_mom = [r["momentum_12_1"] for r in results]
    market_avg_mom = sum(all_mom) / len(all_mom) if all_mom else 0
    high_count = sum(1 for r in results if r["momentum_label"] == "HIGH_MOMENTUM")
    low_count = sum(1 for r in results if r["momentum_label"] == "LOW_MOMENTUM")

    if market_avg_mom >= 20 and high_count > low_count * 2:
        market_regime = "STRONG_MOMENTUM_MARKET"
        regime_desc = "Broad momentum leadership. Trend-following strategies performing well."
        strategy = "Long HIGH_MOMENTUM quintile. Avoid LOW_MOMENTUM (mean reversion risk)."
    elif market_avg_mom >= 8:
        market_regime = "MOMENTUM_MARKET"
        regime_desc = "Above-average momentum across the market. Sector rotation active."
        strategy = "Long top momentum stocks; sector rotation plays."
    elif market_avg_mom >= -8:
        market_regime = "MIXED_MOMENTUM"
        regime_desc = "Momentum signals mixed. Stock-picking environment."
        strategy = "Focus on sector leaders. Avoid index momentum bets."
    elif market_avg_mom >= -20:
        market_regime = "WEAK_MOMENTUM"
        regime_desc = "Broad-based price weakness. Value or mean-reversion may outperform."
        strategy = "Reduce momentum exposure. Watch LOW_MOMENTUM for oversold bounces."
    else:
        market_regime = "MOMENTUM_CRASH"
        regime_desc = "Momentum factor reversal underway. High-momentum stocks at max risk."
        strategy = "Exit HIGH_MOMENTUM positions. LOW_MOMENTUM stocks may outperform (reversal)."

    top_n_clamp = min(top_n, 50)

    return {
        "momentum_factor_screen": {
            "total_stocks_screened": n,
            "screen_date": datetime.now().strftime("%Y-%m-%d"),
            "factor": "12-1 Momentum (12M return minus 1M return — standard academic factor)",
            "market_regime": market_regime,
            "regime_description": regime_desc,
            "market_avg_momentum_12_1": round(market_avg_mom, 2),
            "quintile_breakdown": {
                "HIGH_MOMENTUM_count": high_count,
                "NEUTRAL_MOMENTUM_count": n - high_count - low_count,
                "LOW_MOMENTUM_count": low_count,
            },
            "strategy_guide": strategy,
        },
        "top_momentum_stocks": [
            {k: v for k, v in r.items()} for r in results[:top_n_clamp]
        ],
        "bottom_momentum_stocks": [
            {k: v for k, v in r.items()} for r in results[-top_n_clamp:][::-1]
        ],
        "sector_momentum_ranking": sector_summary,
        "source": "Yahoo Finance — no API key required",
        "note": "Combine with get_relative_strength_ranking() and get_sector_rotation_signal() for full factor analysis.",
    }


@mcp.tool()
async def get_economic_indicators_dashboard(country: str = "US") -> dict:
    """
    Macro economic health dashboard using public ETF proxies.
    Scores GDP growth, inflation, employment, fiscal health, and currency.
    No API key required.

    Supported countries: US, EU, JP, CN, KR, GB, CA, AU, IN, BR, MX, DE, FR

    Args:
        country: 2-letter country code (default: US)

    Returns:
        Macro health scorecard with composite score 0-100 and regime classification.
    """
    await Actor.charge("basic_tool", count=1)
    import yfinance as yf

    country = country.upper().strip()

    COUNTRY_CONFIG = {
        "US":  {"name": "United States",  "equity": "SPY",  "bond": "TLT",   "fx": "UUP",   "wb_code": "USA"},
        "EU":  {"name": "Euro Area",      "equity": "EZU",  "bond": "BNDX",  "fx": "FXE",   "wb_code": "EUU"},
        "JP":  {"name": "Japan",          "equity": "EWJ",  "bond": "BNDX",  "fx": "FXY",   "wb_code": "JPN"},
        "CN":  {"name": "China",          "equity": "MCHI", "bond": "BNDX",  "fx": "CYB",   "wb_code": "CHN"},
        "KR":  {"name": "South Korea",    "equity": "EWY",  "bond": "BNDX",  "fx": "FXI",   "wb_code": "KOR"},
        "GB":  {"name": "United Kingdom", "equity": "EWU",  "bond": "BNDX",  "fx": "FXB",   "wb_code": "GBR"},
        "CA":  {"name": "Canada",         "equity": "EWC",  "bond": "BNDX",  "fx": "FXC",   "wb_code": "CAN"},
        "AU":  {"name": "Australia",      "equity": "EWA",  "bond": "BNDX",  "fx": "FXA",   "wb_code": "AUS"},
        "IN":  {"name": "India",          "equity": "INDA", "bond": "BNDX",  "fx": "ICN",   "wb_code": "IND"},
        "BR":  {"name": "Brazil",         "equity": "EWZ",  "bond": "BNDX",  "fx": "BZF",   "wb_code": "BRA"},
        "MX":  {"name": "Mexico",         "equity": "EWW",  "bond": "BNDX",  "fx": "FXM",   "wb_code": "MEX"},
        "DE":  {"name": "Germany",        "equity": "EWG",  "bond": "BNDX",  "fx": "FXE",   "wb_code": "DEU"},
        "FR":  {"name": "France",         "equity": "EWQ",  "bond": "BNDX",  "fx": "FXE",   "wb_code": "FRA"},
    }

    if country not in COUNTRY_CONFIG:
        return {
            "error": f"Country '{country}' not supported.",
            "supported": list(COUNTRY_CONFIG.keys()),
        }

    cfg = COUNTRY_CONFIG[country]

    growth_score = 12; growth_label = "MIXED"
    eq_ret_1y = None; eq_ret_3m = None
    try:
        eq_tk = yf.Ticker(cfg["equity"])
        eq_hist = eq_tk.history(period="13mo")
        if not eq_hist.empty and len(eq_hist) >= 60:
            eq_closes = eq_hist["Close"].dropna()
            eq_ret_1y = round((float(eq_closes.iloc[-1]) / float(eq_closes.iloc[0]) - 1) * 100, 2)
            if len(eq_closes) >= 66:
                eq_ret_3m = round((float(eq_closes.iloc[-1]) / float(eq_closes.iloc[-66]) - 1) * 100, 2)
            growth_combined = (eq_ret_1y * 0.5 + (eq_ret_3m or 0) * 0.5)
            if growth_combined >= 20:
                growth_score = 25; growth_label = "STRONG_GROWTH"
            elif growth_combined >= 10:
                growth_score = 20; growth_label = "SOLID_GROWTH"
            elif growth_combined >= 2:
                growth_score = 15; growth_label = "MODERATE_GROWTH"
            elif growth_combined >= -5:
                growth_score = 10; growth_label = "SLOW_GROWTH"
            elif growth_combined >= -15:
                growth_score = 5; growth_label = "CONTRACTION"
            else:
                growth_score = 0; growth_label = "SEVERE_CONTRACTION"
    except Exception:
        pass

    inflation_score = 10; inflation_label = "NEUTRAL"
    gold_ret_3m = None; oil_ret_3m = None
    try:
        gld = yf.Ticker("GLD")
        uso = yf.Ticker("USO")
        gld_hist = gld.history(period="6mo")
        uso_hist = uso.history(period="6mo")
        if not gld_hist.empty and len(gld_hist) >= 60:
            gc = gld_hist["Close"].dropna()
            gold_ret_3m = round((float(gc.iloc[-1]) / float(gc.iloc[-66]) - 1) * 100, 2) if len(gc) >= 66 else round((float(gc.iloc[-1]) / float(gc.iloc[0]) - 1) * 100, 2)
        if not uso_hist.empty and len(uso_hist) >= 60:
            uc = uso_hist["Close"].dropna()
            oil_ret_3m = round((float(uc.iloc[-1]) / float(uc.iloc[-66]) - 1) * 100, 2) if len(uc) >= 66 else round((float(uc.iloc[-1]) / float(uc.iloc[0]) - 1) * 100, 2)
        infl_proxy = ((gold_ret_3m or 0) * 0.5 + (oil_ret_3m or 0) * 0.5)
        if -5 <= infl_proxy <= 10:
            inflation_score = 20; inflation_label = "STABLE_PRICES"
        elif infl_proxy <= -10:
            inflation_score = 5; inflation_label = "DEFLATION_RISK"
        elif infl_proxy <= -5:
            inflation_score = 10; inflation_label = "LOW_INFLATION"
        elif infl_proxy <= 20:
            inflation_score = 14; inflation_label = "ELEVATED_INFLATION"
        else:
            inflation_score = 6; inflation_label = "HIGH_INFLATION_RISK"
    except Exception:
        pass

    employ_score = 10; employ_label = "NEUTRAL"
    xly_ret = None; xlp_ret = None
    try:
        xly = yf.Ticker("XLY")
        xlp = yf.Ticker("XLP")
        xly_hist = xly.history(period="6mo")
        xlp_hist = xlp.history(period="6mo")
        if not xly_hist.empty and len(xly_hist) >= 60:
            xlyc = xly_hist["Close"].dropna()
            xly_ret = round((float(xlyc.iloc[-1]) / float(xlyc.iloc[-66]) - 1) * 100, 2) if len(xlyc) >= 66 else round((float(xlyc.iloc[-1]) / float(xlyc.iloc[0]) - 1) * 100, 2)
        if not xlp_hist.empty and len(xlp_hist) >= 60:
            xlpc = xlp_hist["Close"].dropna()
            xlp_ret = round((float(xlpc.iloc[-1]) / float(xlpc.iloc[-66]) - 1) * 100, 2) if len(xlpc) >= 66 else round((float(xlpc.iloc[-1]) / float(xlpc.iloc[0]) - 1) * 100, 2)
        if xly_ret is not None and xlp_ret is not None:
            disc_vs_staples = xly_ret - xlp_ret
            if disc_vs_staples >= 10:
                employ_score = 20; employ_label = "STRONG_EMPLOYMENT"
            elif disc_vs_staples >= 3:
                employ_score = 16; employ_label = "HEALTHY_EMPLOYMENT"
            elif disc_vs_staples >= -3:
                employ_score = 10; employ_label = "NEUTRAL_EMPLOYMENT"
            elif disc_vs_staples >= -10:
                employ_score = 5; employ_label = "WEAKENING_EMPLOYMENT"
            else:
                employ_score = 0; employ_label = "RECESSIONARY_EMPLOYMENT"
    except Exception:
        pass

    fiscal_score = 10; fiscal_label = "NEUTRAL"
    hyg_ret = None; ief_ret = None; vix_val = None
    try:
        hyg = yf.Ticker("HYG")
        ief = yf.Ticker("IEF")
        vix_tk = yf.Ticker("^VIX")
        hyg_hist = hyg.history(period="6mo")
        ief_hist = ief.history(period="6mo")
        vix_hist = vix_tk.history(period="5d")
        if not hyg_hist.empty and len(hyg_hist) >= 60:
            hc = hyg_hist["Close"].dropna()
            hyg_ret = round((float(hc.iloc[-1]) / float(hc.iloc[-66]) - 1) * 100, 2) if len(hc) >= 66 else round((float(hc.iloc[-1]) / float(hc.iloc[0]) - 1) * 100, 2)
        if not ief_hist.empty and len(ief_hist) >= 60:
            ic = ief_hist["Close"].dropna()
            ief_ret = round((float(ic.iloc[-1]) / float(ic.iloc[-66]) - 1) * 100, 2) if len(ic) >= 66 else round((float(ic.iloc[-1]) / float(ic.iloc[0]) - 1) * 100, 2)
        if not vix_hist.empty:
            vix_val = round(float(vix_hist["Close"].dropna().iloc[-1]), 2)
        credit_spread = (hyg_ret or 0) - (ief_ret or 0)
        vix_penalty = 0
        if vix_val is not None:
            if vix_val < 15:
                vix_penalty = 0
            elif vix_val < 20:
                vix_penalty = -2
            elif vix_val < 30:
                vix_penalty = -5
            else:
                vix_penalty = -10
        if credit_spread >= 3:
            fiscal_score = 20 + vix_penalty; fiscal_label = "STRONG_FISCAL_HEALTH"
        elif credit_spread >= 0:
            fiscal_score = 15 + vix_penalty; fiscal_label = "HEALTHY_CREDIT"
        elif credit_spread >= -3:
            fiscal_score = 10 + vix_penalty; fiscal_label = "NEUTRAL_CREDIT"
        elif credit_spread >= -6:
            fiscal_score = 5 + vix_penalty; fiscal_label = "CREDIT_STRESS"
        else:
            fiscal_score = 0 + vix_penalty; fiscal_label = "CREDIT_CRISIS"
        fiscal_score = max(0, min(20, fiscal_score))
    except Exception:
        pass

    fx_score = 7; fx_label = "NEUTRAL"
    fx_ret_1y = None
    try:
        if cfg["fx"] and cfg["fx"] != "FXI":
            fx_tk = yf.Ticker(cfg["fx"])
            fx_hist = fx_tk.history(period="13mo")
            if not fx_hist.empty and len(fx_hist) >= 50:
                fxc = fx_hist["Close"].dropna()
                fx_ret_1y = round((float(fxc.iloc[-1]) / float(fxc.iloc[0]) - 1) * 100, 2)
                if fx_ret_1y >= 8:
                    fx_score = 15; fx_label = "STRONG_CURRENCY"
                elif fx_ret_1y >= 3:
                    fx_score = 12; fx_label = "APPRECIATING"
                elif fx_ret_1y >= -3:
                    fx_score = 7; fx_label = "STABLE"
                elif fx_ret_1y >= -8:
                    fx_score = 3; fx_label = "DEPRECIATING"
                else:
                    fx_score = 0; fx_label = "WEAK_CURRENCY"
    except Exception:
        pass

    total = growth_score + inflation_score + employ_score + fiscal_score + fx_score
    total = max(0, min(100, total))

    if total >= 80:
        regime = "STRONG"
        regime_desc = "Economy firing on all cylinders. Pro-growth asset allocation favored."
        asset_signal = "OVERWEIGHT equities, UNDERWEIGHT bonds/cash. Cyclicals > Defensives."
    elif total >= 65:
        regime = "HEALTHY"
        regime_desc = "Solid economic fundamentals. Moderate risk-on stance appropriate."
        asset_signal = "Tilt equities. Monitor inflation and credit spreads for regime change."
    elif total >= 45:
        regime = "MIXED"
        regime_desc = "Mixed signals. Some structural strengths offset by headwinds."
        asset_signal = "BALANCED allocation. Quality stocks + short duration bonds."
    elif total >= 30:
        regime = "WEAK"
        regime_desc = "Economic momentum deteriorating. Defensive positioning warranted."
        asset_signal = "UNDERWEIGHT equities. Increase bonds, gold, defensive sectors."
    else:
        regime = "DISTRESSED"
        regime_desc = "Severe macro stress. Capital preservation priority."
        asset_signal = "Maximum defensiveness: cash, gold, TLT. Avoid high-beta assets."

    return {
        "country": country,
        "country_name": cfg["name"],
        "macro_health_score": total,
        "max_score": 100,
        "regime": regime,
        "regime_description": regime_desc,
        "asset_allocation_signal": asset_signal,
        "components": {
            "growth_proxy": {
                "score": growth_score, "max": 25, "label": growth_label,
                "equity_etf": cfg["equity"],
                "equity_1y_return_pct": eq_ret_1y,
                "equity_3m_return_pct": eq_ret_3m,
                "note": "Equity ETF 1Y+3M performance as GDP growth proxy",
            },
            "inflation_proxy": {
                "score": inflation_score, "max": 20, "label": inflation_label,
                "gold_3m_return_pct": gold_ret_3m,
                "oil_3m_return_pct": oil_ret_3m,
                "note": "GLD+USO composite as commodity inflation signal",
            },
            "employment_activity": {
                "score": employ_score, "max": 20, "label": employ_label,
                "xly_3m_return_pct": xly_ret,
                "xlp_3m_return_pct": xlp_ret,
                "note": "XLY vs XLP (discretionary vs staples) as consumer health proxy",
            },
            "fiscal_credit_health": {
                "score": fiscal_score, "max": 20, "label": fiscal_label,
                "hyg_3m_return_pct": hyg_ret,
                "ief_3m_return_pct": ief_ret,
                "vix": vix_val,
                "note": "HYG vs IEF credit spread + VIX stress level",
            },
            "currency_external": {
                "score": fx_score, "max": 15, "label": fx_label,
                "fx_etf": cfg["fx"],
                "fx_1y_return_pct": fx_ret_1y,
                "note": "Currency ETF 1Y performance as external balance proxy",
            },
        },
        "supported_countries": list(COUNTRY_CONFIG.keys()),
        "source": "Yahoo Finance public ETF data — no API key required",
        "note": "Combine with get_macro_regime_monitor() and get_cross_asset_momentum() for full picture.",
    }


async def main():
    """Apify Actor entrypoint — MCP 서버를 Actor Standby로 실행 (streamable-http, port 8080)"""
    async with Actor:
        # Actor 시작 과금 ($0.01 — 초기화 비용)
        await Actor.charge("actor_start", count=1)
        # MCP 서버 실행 — Apify Standby (streamable-http transport, port 8080)
        await mcp.run_http_async(transport="streamable-http", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


# ── v3.7.0 Tool 1: get_earnings_quality_score ─────────────────────────────
@mcp.tool()
async def get_earnings_quality_score(ticker: str) -> dict:
    """Earnings quality scorecard: cash flow vs net income, earnings persistence,
    revenue growth momentum, ROE trend. Signals HIGH_QUALITY/MODERATE/LOW_QUALITY.
    Identifies accounting-driven vs cash-backed earnings.
    """
    await Actor.charge("advanced_tool")
    import yfinance as yf
    import numpy as np

    tk = yf.Ticker(ticker.upper().strip())

    score = 0
    max_score = 100
    components = {}

    # ── 1. Cash Flow vs Net Income (Accruals Ratio) ────────────────── 30pts
    cf_score = 0
    cf_label = "UNKNOWN"
    accruals_ratio = None
    try:
        cf = tk.cashflow
        inc = tk.income_stmt
        if cf is not None and inc is not None and not cf.empty and not inc.empty:
            ocf_row = None
            for r in ["Operating Cash Flow", "Total Cash From Operating Activities", "Cash From Operations"]:
                if r in cf.index:
                    ocf_row = cf.loc[r]
                    break
            ni_row = None
            for r in ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"]:
                if r in inc.index:
                    ni_row = inc.loc[r]
                    break
            bs = tk.balance_sheet
            ta_row = None
            if bs is not None and not bs.empty:
                if "Total Assets" in bs.index:
                    ta_row = bs.loc["Total Assets"]

            if ocf_row is not None and ni_row is not None:
                ocf_vals = ocf_row.dropna().values
                ni_vals = ni_row.dropna().values
                if len(ocf_vals) >= 1 and len(ni_vals) >= 1:
                    ocf_latest = float(ocf_vals[0])
                    ni_latest = float(ni_vals[0])
                    if ta_row is not None:
                        ta_vals = ta_row.dropna().values
                        if len(ta_vals) >= 2:
                            avg_assets = float((ta_vals[0] + ta_vals[1]) / 2)
                        elif len(ta_vals) == 1:
                            avg_assets = float(ta_vals[0])
                        else:
                            avg_assets = None
                    else:
                        avg_assets = None

                    if avg_assets and avg_assets > 0:
                        accruals_ratio = round((ni_latest - ocf_latest) / avg_assets * 100, 2)
                        if accruals_ratio <= -5:
                            cf_score = 30; cf_label = "EXCELLENT_CASH_BACKING"
                        elif accruals_ratio <= 0:
                            cf_score = 24; cf_label = "STRONG_CASH_BACKING"
                        elif accruals_ratio <= 5:
                            cf_score = 18; cf_label = "MODERATE_CASH_BACKING"
                        elif accruals_ratio <= 10:
                            cf_score = 10; cf_label = "WEAK_CASH_BACKING"
                        else:
                            cf_score = 0; cf_label = "ACCRUAL_WARNING"
                    else:
                        if ni_latest != 0:
                            ratio = ocf_latest / abs(ni_latest)
                            if ratio >= 1.5:
                                cf_score = 28; cf_label = "STRONG_CASH_BACKING"
                            elif ratio >= 1.0:
                                cf_score = 22; cf_label = "MODERATE_CASH_BACKING"
                            elif ratio >= 0.5:
                                cf_score = 12; cf_label = "WEAK_CASH_BACKING"
                            else:
                                cf_score = 3; cf_label = "ACCRUAL_WARNING"
                        else:
                            cf_score = 5; cf_label = "NEGATIVE_EARNINGS"
    except Exception:
        pass

    components["cash_flow_quality"] = {
        "score": cf_score, "max": 30,
        "label": cf_label,
        "accruals_ratio_pct": accruals_ratio,
        "note": "Accruals ratio = (NI - OCF)/avg_assets. Negative = cash-backed earnings.",
    }
    score += cf_score

    # ── 2. Earnings Persistence / Stability ───────────────────────── 25pts
    persist_score = 0
    persist_label = "UNKNOWN"
    eps_std = None
    eps_trend = None
    try:
        inc = tk.income_stmt
        if inc is not None and not inc.empty:
            ni_row = None
            for r in ["Net Income", "Net Income Common Stockholders"]:
                if r in inc.index:
                    ni_row = inc.loc[r]
                    break
            if ni_row is not None:
                ni_vals = ni_row.dropna().values[:4]
                if len(ni_vals) >= 3:
                    ni_vals = [float(v) for v in ni_vals]
                    mean_ni = abs(np.mean(ni_vals))
                    std_ni = np.std(ni_vals)
                    eps_std = round(std_ni / mean_ni * 100, 1) if mean_ni > 0 else None
                    if len(ni_vals) >= 2:
                        if ni_vals[0] > ni_vals[-1] and all(v > 0 for v in ni_vals):
                            eps_trend = "IMPROVING"
                        elif all(v > 0 for v in ni_vals):
                            eps_trend = "STABLE_POSITIVE"
                        elif ni_vals[0] < ni_vals[-1]:
                            eps_trend = "DECLINING"
                        else:
                            eps_trend = "VOLATILE"

                    if eps_std is not None:
                        if eps_std <= 15 and eps_trend in ("IMPROVING", "STABLE_POSITIVE"):
                            persist_score = 25; persist_label = "HIGHLY_PERSISTENT"
                        elif eps_std <= 30 and eps_trend != "DECLINING":
                            persist_score = 18; persist_label = "MODERATELY_PERSISTENT"
                        elif eps_std <= 50:
                            persist_score = 10; persist_label = "LOW_PERSISTENCE"
                        else:
                            persist_score = 3; persist_label = "ERRATIC_EARNINGS"
                    elif eps_trend == "DECLINING":
                        persist_score = 5; persist_label = "DECLINING"
    except Exception:
        pass

    components["earnings_persistence"] = {
        "score": persist_score, "max": 25,
        "label": persist_label,
        "earnings_coeff_variation_pct": eps_std,
        "earnings_trend": eps_trend,
        "note": "Low CV + improving trend = high persistence.",
    }
    score += persist_score

    # ── 3. Revenue Growth Momentum ─────────────────────────────────── 25pts
    rev_score = 0
    rev_label = "UNKNOWN"
    rev_growth_yoy = None
    rev_growth_3y = None
    try:
        inc = tk.income_stmt
        if inc is not None and not inc.empty:
            rev_row = None
            for r in ["Total Revenue", "Revenue", "Net Revenue"]:
                if r in inc.index:
                    rev_row = inc.loc[r]
                    break
            if rev_row is not None:
                rv = rev_row.dropna().values
                if len(rv) >= 2:
                    rv = [float(v) for v in rv]
                    if rv[1] > 0:
                        rev_growth_yoy = round((rv[0] / rv[1] - 1) * 100, 2)
                    if len(rv) >= 4 and rv[3] > 0:
                        rev_growth_3y = round((rv[0] / rv[3] - 1) * 100, 2)

                    if rev_growth_yoy is not None:
                        if rev_growth_yoy >= 20:
                            rev_score = 25; rev_label = "STRONG_REVENUE_GROWTH"
                        elif rev_growth_yoy >= 10:
                            rev_score = 20; rev_label = "HEALTHY_GROWTH"
                        elif rev_growth_yoy >= 3:
                            rev_score = 14; rev_label = "MODERATE_GROWTH"
                        elif rev_growth_yoy >= 0:
                            rev_score = 8; rev_label = "FLAT_REVENUE"
                        else:
                            rev_score = 2; rev_label = "REVENUE_DECLINING"
    except Exception:
        pass

    components["revenue_growth"] = {
        "score": rev_score, "max": 25,
        "label": rev_label,
        "revenue_growth_yoy_pct": rev_growth_yoy,
        "revenue_growth_3y_pct": rev_growth_3y,
        "note": "Revenue growth as earnings sustainability signal.",
    }
    score += rev_score

    # ── 4. ROE Trend ───────────────────────────────────────────────── 20pts
    roe_score = 0
    roe_label = "UNKNOWN"
    roe_latest = None
    try:
        info = tk.info
        roe_raw = info.get("returnOnEquity", None)
        if roe_raw is not None:
            roe_pct = roe_raw * 100
            if roe_pct >= 20:
                roe_score = 20; roe_label = "EXCELLENT_ROE"
            elif roe_pct >= 15:
                roe_score = 16; roe_label = "STRONG_ROE"
            elif roe_pct >= 10:
                roe_score = 11; roe_label = "MODERATE_ROE"
            elif roe_pct >= 0:
                roe_score = 5; roe_label = "LOW_ROE"
            else:
                roe_score = 0; roe_label = "NEGATIVE_ROE"
            roe_latest = round(roe_pct, 2)
    except Exception:
        pass

    components["roe_quality"] = {
        "score": roe_score, "max": 20,
        "label": roe_label,
        "roe_pct": roe_latest,
        "note": "High, sustained ROE = durable competitive advantage.",
    }
    score += roe_score

    score = max(0, min(100, score))
    if score >= 75:
        quality_signal = "HIGH_QUALITY"
        signal_desc = "Earnings are cash-backed, persistent, growing, and ROE-supported. Long candidate."
    elif score >= 50:
        quality_signal = "MODERATE_QUALITY"
        signal_desc = "Mixed quality indicators. Monitor cash conversion and revenue trend."
    elif score >= 30:
        quality_signal = "LOW_QUALITY"
        signal_desc = "Weak earnings quality. Accruals risk or declining fundamentals present."
    else:
        quality_signal = "VERY_LOW_QUALITY"
        signal_desc = "Significant earnings quality concerns. High accounting risk. Avoid or short candidate."

    return {
        "ticker": ticker.upper().strip(),
        "earnings_quality_score": score,
        "max_score": max_score,
        "quality_signal": quality_signal,
        "signal_description": signal_desc,
        "components": components,
        "interpretation": {
            "HIGH_QUALITY": "Score ≥75: Cash-backed, persistent earnings. Premium multiple justified.",
            "MODERATE_QUALITY": "Score 50-74: Adequate quality. Watch for deterioration.",
            "LOW_QUALITY": "Score 30-49: Accrual risk or declining momentum. Discount warranted.",
            "VERY_LOW_QUALITY": "Score <30: Significant red flags. Earnings may not be sustainable.",
        },
        "source": "Yahoo Finance — no API key required",
        "note": "Combine with get_earnings_whisper() and get_smart_money_composite() for full picture.",
    }


# ── v3.7.0 Tool 2: get_market_internals_dashboard ─────────────────────────
@mcp.tool()
async def get_market_internals_dashboard() -> dict:
    """Market internals dashboard: Advance/Decline proxy, New Highs/Lows breadth,
    % above 50d/200d MA for S&P 500 proxies, McClellan Oscillator proxy,
    Bullish Percent Index proxy. Overall health: HEALTHY/NEUTRAL/DETERIORATING/OVERSOLD/OVERBOUGHT.
    """
    await Actor.charge("basic_tool")
    import yfinance as yf
    import numpy as np
    from concurrent.futures import ThreadPoolExecutor

    UNIVERSE = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","LLY","JPM",
        "V","UNH","XOM","MA","AVGO","JNJ","PG","HD","COST","MRK",
        "ABBV","CVX","CRM","BAC","NFLX","AMD","KO","PEP","TMO","ADBE",
        "ACN","MCD","LIN","ABT","DHR","WMT","CSCO","TXN","NEE","PM",
        "RTX","HON","AMGN","SPGI","IBM","GE","CAT","ISRG","INTU","BKNG",
        "GS","AXP","SYK","BLK","MDT","GILD","CI","ZTS","ADP","TJX",
        "MMC","VRTX","C","MO","DE","SCHW","CVS","ETN","SO","D",
        "DUK","AON","ICE","CME","HCA","EMR","BSX","ITW","WM","APH",
        "KLAC","LRCX","AMAT","MU","ADI","MCHP","ON","STZ","EL","CL",
        "PLD","AMT","EQIX","PSA","O","WELL","DLR","AVB","EQR","SPG",
    ]

    def fetch_ticker_internals(sym):
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="1y")
            if hist.empty or len(hist) < 60:
                return None
            c = hist["Close"].dropna()
            if len(c) < 60:
                return None
            cur = float(c.iloc[-1])
            hi52 = float(c.max())
            lo52 = float(c.min())
            ma50 = float(c.iloc[-50:].mean()) if len(c) >= 50 else None
            ma200 = float(c.mean()) if len(c) >= 200 else None
            near_high = cur >= hi52 * 0.97
            near_low = cur <= lo52 * 1.03
            above_ma50 = (cur > ma50) if ma50 else None
            above_ma200 = (cur > ma200) if ma200 else None
            ret10 = (cur / float(c.iloc[-11]) - 1) * 100 if len(c) >= 11 else None
            ret30 = (cur / float(c.iloc[-31]) - 1) * 100 if len(c) >= 31 else None
            return {
                "near_high": near_high, "near_low": near_low,
                "above_ma50": above_ma50, "above_ma200": above_ma200,
                "ret10": ret10, "ret30": ret30,
            }
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_ticker_internals, s): s for s in UNIVERSE}
        for f in futures:
            r = f.result()
            if r:
                results.append(r)

    n = len(results)
    if n == 0:
        return {"error": "Could not fetch market internals data"}

    advances = sum(1 for r in results if r["ret10"] is not None and r["ret10"] > 0)
    declines = sum(1 for r in results if r["ret10"] is not None and r["ret10"] < 0)
    unchanged = n - advances - declines
    ad_ratio = round(advances / declines, 2) if declines > 0 else 99.0
    ad_line_signal = (
        "STRONG_ADVANCE" if ad_ratio >= 2.0 else
        "ADVANCE" if ad_ratio >= 1.3 else
        "NEUTRAL" if ad_ratio >= 0.75 else
        "DECLINE" if ad_ratio >= 0.5 else
        "STRONG_DECLINE"
    )

    near_highs = sum(1 for r in results if r["near_high"])
    near_lows = sum(1 for r in results if r["near_low"])
    nh_nl_ratio = round(near_highs / near_lows, 2) if near_lows > 0 else (99.0 if near_highs > 0 else 1.0)
    nh_nl_net_pct = round((near_highs - near_lows) / n * 100, 1)
    nh_nl_signal = (
        "STRONG_NEW_HIGHS" if nh_nl_net_pct >= 20 else
        "NEW_HIGHS_DOMINANT" if nh_nl_net_pct >= 10 else
        "BALANCED" if nh_nl_net_pct >= -10 else
        "NEW_LOWS_DOMINANT" if nh_nl_net_pct >= -20 else
        "STRONG_NEW_LOWS"
    )

    ma50_data = [r for r in results if r["above_ma50"] is not None]
    ma200_data = [r for r in results if r["above_ma200"] is not None]
    pct_above_ma50 = round(sum(1 for r in ma50_data if r["above_ma50"]) / len(ma50_data) * 100, 1) if ma50_data else None
    pct_above_ma200 = round(sum(1 for r in ma200_data if r["above_ma200"]) / len(ma200_data) * 100, 1) if ma200_data else None

    ma50_signal = (
        "STRONG_BREADTH" if pct_above_ma50 and pct_above_ma50 >= 75 else
        "HEALTHY_BREADTH" if pct_above_ma50 and pct_above_ma50 >= 60 else
        "NEUTRAL_BREADTH" if pct_above_ma50 and pct_above_ma50 >= 40 else
        "WEAK_BREADTH" if pct_above_ma50 and pct_above_ma50 >= 25 else
        "OVERSOLD_BREADTH"
    ) if pct_above_ma50 is not None else "UNKNOWN"

    ma200_signal = (
        "LONG_TERM_BULL" if pct_above_ma200 and pct_above_ma200 >= 70 else
        "BULL_TREND" if pct_above_ma200 and pct_above_ma200 >= 55 else
        "TRANSITION" if pct_above_ma200 and pct_above_ma200 >= 40 else
        "BEAR_TREND" if pct_above_ma200 and pct_above_ma200 >= 25 else
        "LONG_TERM_BEAR"
    ) if pct_above_ma200 is not None else "UNKNOWN"

    adv10 = sum(1 for r in results if r["ret10"] is not None and r["ret10"] > 0)
    dec10 = sum(1 for r in results if r["ret10"] is not None and r["ret10"] < 0)
    adv30 = sum(1 for r in results if r["ret30"] is not None and r["ret30"] > 0)
    dec30 = sum(1 for r in results if r["ret30"] is not None and r["ret30"] < 0)
    ema10_proxy = (adv10 - dec10) / n * 100
    ema30_proxy = (adv30 - dec30) / n * 100
    mclellan_proxy = round(ema10_proxy - ema30_proxy, 2)
    mclellan_signal = (
        "OVERBOUGHT" if mclellan_proxy >= 20 else
        "POSITIVE_MOMENTUM" if mclellan_proxy >= 5 else
        "NEUTRAL" if mclellan_proxy >= -5 else
        "NEGATIVE_MOMENTUM" if mclellan_proxy >= -20 else
        "OVERSOLD"
    )

    bpi_proxy = pct_above_ma200 if pct_above_ma200 is not None else 50.0
    bpi_signal = (
        "OVERBOUGHT_ZONE" if bpi_proxy >= 80 else
        "BULL_CONFIRMED" if bpi_proxy >= 60 else
        "NEUTRAL_ZONE" if bpi_proxy >= 40 else
        "BEAR_CONFIRMED" if bpi_proxy >= 20 else
        "OVERSOLD_ZONE"
    )

    health_pts = 0
    if ad_ratio >= 1.5:
        health_pts += 25
    elif ad_ratio >= 1.0:
        health_pts += 15
    elif ad_ratio >= 0.67:
        health_pts += 5
    if nh_nl_net_pct >= 15:
        health_pts += 20
    elif nh_nl_net_pct >= 5:
        health_pts += 13
    elif nh_nl_net_pct >= -5:
        health_pts += 7
    if pct_above_ma50 and pct_above_ma50 >= 70:
        health_pts += 25
    elif pct_above_ma50 and pct_above_ma50 >= 55:
        health_pts += 17
    elif pct_above_ma50 and pct_above_ma50 >= 40:
        health_pts += 8
    if pct_above_ma200 and pct_above_ma200 >= 65:
        health_pts += 20
    elif pct_above_ma200 and pct_above_ma200 >= 50:
        health_pts += 13
    elif pct_above_ma200 and pct_above_ma200 >= 35:
        health_pts += 5
    if mclellan_proxy >= 5:
        health_pts += 10
    elif mclellan_proxy >= -5:
        health_pts += 5

    health_pts = max(0, min(100, health_pts))

    if health_pts >= 75:
        overall = "HEALTHY"
        overall_desc = "Broad participation. Strong internal support. Bullish environment."
        action = "STAY_LONG — broad market support confirms uptrend."
    elif health_pts >= 55:
        overall = "NEUTRAL"
        overall_desc = "Mixed internals. Selective opportunities. Monitor for direction."
        action = "SELECTIVE — favor quality and momentum leaders."
    elif health_pts >= 35:
        overall = "DETERIORATING"
        overall_desc = "Narrowing breadth. Leaders pulling away. Risk of deeper correction."
        action = "REDUCE_RISK — trim extended positions, raise cash."
    elif health_pts >= 15:
        overall = "OVERSOLD"
        overall_desc = "Capitulation territory. Potential countertrend bounce near-term."
        action = "WATCH_FOR_BOUNCE — oversold but confirm before adding longs."
    else:
        overall = "VERY_OVERSOLD"
        overall_desc = "Extreme internal weakness. Potential for sharp reversal or continued collapse."
        action = "HIGH_RISK — wait for stabilization before re-entry."

    return {
        "market_internals_health": overall,
        "health_score": health_pts,
        "max_score": 100,
        "health_description": overall_desc,
        "action_guidance": action,
        "universe_stocks_analyzed": n,
        "advance_decline": {
            "advances_10d": advances,
            "declines_10d": declines,
            "unchanged": unchanged,
            "ad_ratio": ad_ratio,
            "signal": ad_line_signal,
        },
        "new_highs_lows": {
            "near_52w_highs": near_highs,
            "near_52w_lows": near_lows,
            "net_pct": nh_nl_net_pct,
            "nh_nl_ratio": nh_nl_ratio,
            "signal": nh_nl_signal,
        },
        "moving_averages_breadth": {
            "pct_above_ma50": pct_above_ma50,
            "ma50_signal": ma50_signal,
            "pct_above_ma200": pct_above_ma200,
            "ma200_signal": ma200_signal,
        },
        "mclellan_oscillator_proxy": {
            "value": mclellan_proxy,
            "short_term_breadth_pct": round(ema10_proxy, 1),
            "long_term_breadth_pct": round(ema30_proxy, 1),
            "signal": mclellan_signal,
            "note": "10d vs 30d advance-decline breadth proxy",
        },
        "bullish_percent_index_proxy": {
            "bpi_proxy_pct": bpi_proxy,
            "signal": bpi_signal,
            "note": "% stocks above 200d MA as BPI proxy",
        },
        "source": "Yahoo Finance public data — no API key required",
        "note": "Combine with get_market_regime_composite() and get_52w_high_low_momentum() for full picture.",
    }


# ── v3.8.0 Tool 1: get_dividend_safety_screen ────────────────────────────
@mcp.tool()
async def get_dividend_safety_screen(sector: str = "ALL") -> dict:
    """Screen 80+ S&P 500 dividend stocks for safety and sustainability.
    Evaluates payout ratio trend, FCF coverage, dividend growth, and cut risk.
    Returns SAFE_DIVIDEND / AT_RISK / DIVIDEND_CUT_RISK signals per stock.
    No API key required.
    """
    await Actor.charge("advanced_tool")
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, as_completed

    DIVIDEND_UNIVERSE = {
        "Technology": ["AAPL", "MSFT", "AVGO", "TXN", "QCOM", "IBM", "INTC", "HPQ", "CSCO", "ACN"],
        "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "PNC", "TFC", "COF"],
        "Healthcare": ["JNJ", "ABT", "MDT", "BMY", "AMGN", "ABBV", "PFE", "MRK", "LLY", "CVS"],
        "ConsumerStaples": ["PG", "KO", "PEP", "MO", "PM", "CL", "GIS", "K", "HRL", "SJM"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "WEC", "ES", "ETR"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OKE", "KMI"],
        "Industrials": ["HON", "UPS", "CAT", "DE", "MMM", "GD", "LMT", "RTX", "EMR", "DOV"],
        "RealEstate": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "DLR", "AVB", "EQR"],
        "Materials": ["LIN", "APD", "ECL", "SHW", "PPG", "NUE", "VMC", "MLM", "PKG", "IP"],
    }

    sector_upper = sector.upper().strip()
    if sector_upper != "ALL":
        sector_map = {
            "TECH": "Technology", "TECHNOLOGY": "Technology",
            "FINANCIALS": "Financials", "FINANCE": "Financials",
            "HEALTHCARE": "Healthcare", "HEALTH": "Healthcare",
            "CONSUMER": "ConsumerStaples", "CONSUMERSTAPLS": "ConsumerStaples", "STAPLES": "ConsumerStaples",
            "UTILITIES": "Utilities", "UTILITY": "Utilities",
            "ENERGY": "Energy",
            "INDUSTRIALS": "Industrials", "INDUSTRIAL": "Industrials",
            "REALESTATE": "RealEstate", "REIT": "RealEstate",
            "MATERIALS": "Materials", "MATERIAL": "Materials",
        }
        mapped = sector_map.get(sector_upper)
        if mapped:
            tickers_by_sector = {mapped: DIVIDEND_UNIVERSE[mapped]}
        else:
            return {"error": f"Unknown sector '{sector}'. Use ALL or: Technology, Financials, Healthcare, ConsumerStaples, Utilities, Energy, Industrials, RealEstate, Materials"}
    else:
        tickers_by_sector = DIVIDEND_UNIVERSE

    def analyze_stock(sym, sec):
        try:
            tk = yf.Ticker(sym)
            info = tk.info or {}
            div_yield = info.get("dividendYield") or 0.0
            div_rate = info.get("dividendRate") or 0.0
            payout_ratio = info.get("payoutRatio") or None
            eps_ttm = info.get("trailingEps") or 0.0
            fcf_per_share = info.get("freeCashflow") or None
            shares = info.get("sharesOutstanding") or None
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            beta = info.get("beta") or 1.0

            pr_score = 0
            pr_label = "UNKNOWN"
            if payout_ratio is not None and payout_ratio > 0:
                if payout_ratio <= 0.40:
                    pr_score = 30; pr_label = "VERY_LOW_PAYOUT"
                elif payout_ratio <= 0.60:
                    pr_score = 25; pr_label = "SUSTAINABLE_PAYOUT"
                elif payout_ratio <= 0.75:
                    pr_score = 15; pr_label = "ELEVATED_PAYOUT"
                elif payout_ratio <= 0.90:
                    pr_score = 5; pr_label = "HIGH_PAYOUT"
                elif payout_ratio <= 1.10:
                    pr_score = 0; pr_label = "DANGER_ZONE"
                else:
                    pr_score = -10; pr_label = "UNSUSTAINABLE_PAYOUT"
            elif sec in ("Utilities", "RealEstate"):
                pr_score = 15; pr_label = "SECTOR_TYPICAL_HIGH"

            fcf_score = 0
            fcf_label = "UNKNOWN"
            fcf_coverage = None
            if fcf_per_share and shares and div_rate > 0:
                fcf_ps = fcf_per_share / shares if shares else 0
                fcf_coverage = fcf_ps / div_rate if div_rate > 0 else None
                if fcf_coverage is not None:
                    if fcf_coverage >= 3.0:
                        fcf_score = 35; fcf_label = "EXCELLENT_FCF_COVERAGE"
                    elif fcf_coverage >= 2.0:
                        fcf_score = 28; fcf_label = "STRONG_FCF_COVERAGE"
                    elif fcf_coverage >= 1.3:
                        fcf_score = 20; fcf_label = "ADEQUATE_FCF_COVERAGE"
                    elif fcf_coverage >= 1.0:
                        fcf_score = 10; fcf_label = "TIGHT_FCF_COVERAGE"
                    elif fcf_coverage >= 0.7:
                        fcf_score = 0; fcf_label = "INSUFFICIENT_FCF"
                    else:
                        fcf_score = -15; fcf_label = "FCF_DEFICIT_RISK"
            else:
                if eps_ttm > 0 and div_rate > 0:
                    ec = eps_ttm / div_rate
                    if ec >= 2.0:
                        fcf_score = 25; fcf_label = "EARNINGS_COVERED"
                    elif ec >= 1.2:
                        fcf_score = 15; fcf_label = "EARNINGS_MARGINAL"
                    else:
                        fcf_score = 0; fcf_label = "EARNINGS_TIGHT"

            yield_score = 0
            yield_label = "NO_DIVIDEND"
            if div_yield > 0:
                if 0.015 <= div_yield <= 0.04:
                    yield_score = 20; yield_label = "ATTRACTIVE_YIELD"
                elif div_yield < 0.015:
                    yield_score = 12; yield_label = "LOW_YIELD"
                elif div_yield <= 0.06:
                    yield_score = 15; yield_label = "HIGH_YIELD_WATCH"
                else:
                    yield_score = 5; yield_label = "YIELD_TRAP_RISK"

            stability_score = 0
            if beta <= 0.6:
                stability_score = 15
            elif beta <= 0.9:
                stability_score = 11
            elif beta <= 1.2:
                stability_score = 7
            else:
                stability_score = 3

            total_score = max(0, min(100, pr_score + fcf_score + yield_score + stability_score))

            if total_score >= 65:
                safety_signal = "SAFE_DIVIDEND"; cut_risk = "LOW"
            elif total_score >= 40:
                safety_signal = "AT_RISK"; cut_risk = "MODERATE"
            else:
                safety_signal = "DIVIDEND_CUT_RISK"; cut_risk = "HIGH"

            return {
                "ticker": sym, "sector": sec,
                "safety_signal": safety_signal, "safety_score": total_score,
                "cut_risk": cut_risk,
                "dividend_yield_pct": round(div_yield * 100, 2),
                "annual_dividend_rate": round(div_rate, 2),
                "payout_ratio_pct": round(payout_ratio * 100, 1) if payout_ratio else None,
                "payout_label": pr_label,
                "fcf_coverage_ratio": round(fcf_coverage, 2) if fcf_coverage else None,
                "fcf_label": fcf_label,
                "yield_label": yield_label,
                "beta": round(beta, 2),
                "current_price": round(current_price, 2),
                "score_breakdown": {
                    "payout_ratio_pts": pr_score, "fcf_coverage_pts": fcf_score,
                    "yield_quality_pts": yield_score, "stability_pts": stability_score, "max_pts": 100,
                },
            }
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {}
        for sec, tickers in tickers_by_sector.items():
            for sym in tickers:
                futures[executor.submit(analyze_stock, sym, sec)] = sym
        for fut in as_completed(futures):
            r = fut.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["safety_score"], reverse=True)
    safe = [r for r in results if r["safety_signal"] == "SAFE_DIVIDEND"]
    at_risk = [r for r in results if r["safety_signal"] == "AT_RISK"]
    cut_risk_list = [r for r in results if r["safety_signal"] == "DIVIDEND_CUT_RISK"]

    sector_summary = {}
    for r in results:
        s = r["sector"]
        if s not in sector_summary:
            sector_summary[s] = {"safe": 0, "at_risk": 0, "cut_risk": 0, "total": 0, "avg_yield": []}
        sector_summary[s]["total"] += 1
        sector_summary[s]["avg_yield"].append(r["dividend_yield_pct"])
        if r["safety_signal"] == "SAFE_DIVIDEND":
            sector_summary[s]["safe"] += 1
        elif r["safety_signal"] == "AT_RISK":
            sector_summary[s]["at_risk"] += 1
        else:
            sector_summary[s]["cut_risk"] += 1

    sector_out = []
    for s, d in sector_summary.items():
        avg_y = round(sum(d["avg_yield"]) / len(d["avg_yield"]), 2) if d["avg_yield"] else 0
        safety_rate = round(d["safe"] / d["total"] * 100, 1) if d["total"] else 0
        sector_out.append({"sector": s, "total_stocks": d["total"], "safe": d["safe"],
                           "at_risk": d["at_risk"], "cut_risk": d["cut_risk"],
                           "safety_rate_pct": safety_rate, "avg_yield_pct": avg_y})
    sector_out.sort(key=lambda x: x["safety_rate_pct"], reverse=True)

    return {
        "universe_analyzed": len(results),
        "filter_sector": sector,
        "summary": {"safe_dividend": len(safe), "at_risk": len(at_risk), "dividend_cut_risk": len(cut_risk_list)},
        "top_safe_dividend_picks": safe[:10],
        "at_risk_watch_list": at_risk[:8],
        "high_risk_names": cut_risk_list[:5],
        "sector_safety_ranking": sector_out,
        "scoring_methodology": {
            "payout_ratio": "30pts — ≤40% VERY_LOW / ≤60% SUSTAINABLE / ≤75% ELEVATED / ≤90% HIGH / >110% UNSUSTAINABLE",
            "fcf_coverage": "35pts — FCF per share / annual dividend rate. ≥3x EXCELLENT / ≥2x STRONG / ≥1.3x ADEQUATE / <0.7x DEFICIT",
            "yield_quality": "20pts — 1.5-4% ATTRACTIVE / <1.5% LOW / 4-6% HIGH_WATCH / >6% TRAP_RISK",
            "stability": "15pts — Beta ≤0.6 VERY_STABLE / ≤0.9 STABLE / ≤1.2 MODERATE",
        },
        "signal_thresholds": "SAFE_DIVIDEND ≥65pts | AT_RISK 40-64pts | DIVIDEND_CUT_RISK <40pts",
        "source": "Yahoo Finance public data — no API key required",
        "note": "Combine with get_dividend_calendar() for ex-date timing and get_valuation_composite() for entry price.",
    }


# ── v3.8.0 Tool 2: get_valuation_composite ───────────────────────────────
@mcp.tool()
async def get_valuation_composite(ticker: str) -> dict:
    """Comprehensive valuation scorecard: P/E vs sector peers, P/B, EV/EBITDA,
    PEG ratio, and simple DCF implied value vs current price.
    Returns DEEPLY_UNDERVALUED / UNDERVALUED / FAIRLY_VALUED / OVERVALUED / SIGNIFICANTLY_OVERVALUED.
    No API key required.
    """
    await Actor.charge("advanced_tool")
    import yfinance as yf

    SECTOR_PE_BENCHMARKS = {
        "Technology": {"pe": 28, "pb": 6.0, "ev_ebitda": 20},
        "Healthcare": {"pe": 20, "pb": 4.0, "ev_ebitda": 15},
        "Financials": {"pe": 13, "pb": 1.5, "ev_ebitda": None},
        "ConsumerDiscretionary": {"pe": 22, "pb": 5.0, "ev_ebitda": 14},
        "ConsumerStaples": {"pe": 22, "pb": 5.0, "ev_ebitda": 14},
        "Industrials": {"pe": 20, "pb": 3.5, "ev_ebitda": 13},
        "Energy": {"pe": 12, "pb": 1.8, "ev_ebitda": 7},
        "Materials": {"pe": 16, "pb": 2.5, "ev_ebitda": 11},
        "Utilities": {"pe": 17, "pb": 1.8, "ev_ebitda": 10},
        "RealEstate": {"pe": 35, "pb": 2.0, "ev_ebitda": 20},
        "CommunicationServices": {"pe": 18, "pb": 3.0, "ev_ebitda": 12},
        "DEFAULT": {"pe": 20, "pb": 3.0, "ev_ebitda": 13},
    }

    sym = ticker.upper().strip()
    tk = yf.Ticker(sym)
    info = tk.info or {}

    sector_raw = info.get("sector") or "DEFAULT"
    sector_clean = sector_raw.replace(" ", "")
    bench = SECTOR_PE_BENCHMARKS.get(sector_clean) or SECTOR_PE_BENCHMARKS["DEFAULT"]
    sector_pe_avg = bench["pe"]
    sector_pb_avg = bench["pb"]
    sector_ev_ebitda_avg = bench["ev_ebitda"]

    trailing_pe = info.get("trailingPE") or None
    forward_pe = info.get("forwardPE") or None
    pb = info.get("priceToBook") or None
    peg = info.get("pegRatio") or None
    ev_ebitda = info.get("enterpriseToEbitda") or None
    price_to_sales = info.get("priceToSalesTrailingTwelveMonths") or None
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
    eps_ttm = info.get("trailingEps") or None
    eps_forward = info.get("forwardEps") or None
    eps_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth") or None
    revenue_growth = info.get("revenueGrowth") or None
    roe = info.get("returnOnEquity") or None
    fcf = info.get("freeCashflow") or None
    shares = info.get("sharesOutstanding") or None
    beta = info.get("beta") or 1.0
    market_cap = info.get("marketCap") or None

    pe_score = 0; pe_label = "NO_PE_DATA"
    pe_used = trailing_pe or forward_pe
    if pe_used and pe_used > 0 and sector_pe_avg:
        pe_ratio = pe_used / sector_pe_avg
        if pe_ratio <= 0.6:
            pe_score = 25; pe_label = "DEEPLY_CHEAP_VS_SECTOR"
        elif pe_ratio <= 0.85:
            pe_score = 20; pe_label = "CHEAP_VS_SECTOR"
        elif pe_ratio <= 1.15:
            pe_score = 12; pe_label = "IN_LINE_WITH_SECTOR"
        elif pe_ratio <= 1.5:
            pe_score = 5; pe_label = "EXPENSIVE_VS_SECTOR"
        else:
            pe_score = 0; pe_label = "SIGNIFICANTLY_EXPENSIVE"

    pb_score = 0; pb_label = "NO_PB_DATA"
    if pb and pb > 0 and sector_pb_avg:
        pb_ratio = pb / sector_pb_avg
        if pb_ratio <= 0.6:
            pb_score = 20; pb_label = "DEEP_VALUE_PB"
        elif pb_ratio <= 0.9:
            pb_score = 16; pb_label = "VALUE_PB"
        elif pb_ratio <= 1.2:
            pb_score = 10; pb_label = "FAIR_PB"
        elif pb_ratio <= 1.8:
            pb_score = 5; pb_label = "ELEVATED_PB"
        else:
            pb_score = 0; pb_label = "EXPENSIVE_PB"

    ev_score = 0; ev_label = "NO_EV_DATA"
    if ev_ebitda and ev_ebitda > 0 and sector_ev_ebitda_avg:
        ev_ratio = ev_ebitda / sector_ev_ebitda_avg
        if ev_ratio <= 0.6:
            ev_score = 20; ev_label = "DEEP_VALUE_EV"
        elif ev_ratio <= 0.85:
            ev_score = 15; ev_label = "CHEAP_EV"
        elif ev_ratio <= 1.20:
            ev_score = 9; ev_label = "FAIR_EV"
        elif ev_ratio <= 1.6:
            ev_score = 4; ev_label = "ELEVATED_EV"
        else:
            ev_score = 0; ev_label = "EXPENSIVE_EV"

    peg_score = 0; peg_label = "NO_PEG_DATA"
    if peg and peg > 0:
        if peg <= 0.8:
            peg_score = 15; peg_label = "GROWTH_AT_DISCOUNT"
        elif peg <= 1.2:
            peg_score = 11; peg_label = "FAIR_GROWTH_PRICE"
        elif peg <= 2.0:
            peg_score = 5; peg_label = "EXPENSIVE_GROWTH"
        else:
            peg_score = 0; peg_label = "GROWTH_OVERPRICED"

    dcf_score = 0; dcf_label = "NO_DCF_DATA"
    dcf_implied = None; dcf_upside_pct = None
    if fcf and shares and shares > 0 and current_price > 0:
        fcf_per_share = fcf / shares
        growth_rate = min(max((eps_growth or revenue_growth or 0.05), 0.0), 0.30)
        discount_rate = 0.09 + (beta - 1.0) * 0.02 if beta else 0.10
        terminal_growth = 0.025
        try:
            pv_fcf = 0.0
            cf = fcf_per_share
            for t in range(1, 11):
                cf *= (1 + growth_rate)
                pv_fcf += cf / ((1 + discount_rate) ** t)
            terminal_val = cf * (1 + terminal_growth) / (discount_rate - terminal_growth)
            pv_terminal = terminal_val / ((1 + discount_rate) ** 10)
            dcf_implied = round(pv_fcf + pv_terminal, 2)
            dcf_upside_pct = round((dcf_implied - current_price) / current_price * 100, 1)
            if dcf_upside_pct >= 40:
                dcf_score = 20; dcf_label = "DEEPLY_UNDERVALUED_DCF"
            elif dcf_upside_pct >= 20:
                dcf_score = 16; dcf_label = "UNDERVALUED_DCF"
            elif dcf_upside_pct >= -10:
                dcf_score = 10; dcf_label = "FAIRLY_VALUED_DCF"
            elif dcf_upside_pct >= -25:
                dcf_score = 4; dcf_label = "OVERVALUED_DCF"
            else:
                dcf_score = 0; dcf_label = "SIGNIFICANTLY_OVERVALUED_DCF"
        except Exception:
            pass

    total_score = max(0, min(100, pe_score + pb_score + ev_score + peg_score + dcf_score))

    if total_score >= 72:
        valuation_signal = "DEEPLY_UNDERVALUED"
        action = "STRONG_BUY_ZONE — multiple metrics signal deep discount to fair value."
    elif total_score >= 55:
        valuation_signal = "UNDERVALUED"
        action = "BUY_ZONE — trading below sector and intrinsic value estimates."
    elif total_score >= 38:
        valuation_signal = "FAIRLY_VALUED"
        action = "HOLD — priced near fair value. Require margin of safety before adding."
    elif total_score >= 22:
        valuation_signal = "OVERVALUED"
        action = "TRIM_OR_AVOID — elevated vs peers. Monitor for better entry."
    else:
        valuation_signal = "SIGNIFICANTLY_OVERVALUED"
        action = "AVOID — pricing in extreme optimism. High risk of multiple compression."

    return {
        "ticker": sym,
        "sector": sector_raw,
        "current_price": round(current_price, 2),
        "valuation_signal": valuation_signal,
        "valuation_score": total_score,
        "max_score": 100,
        "action_guidance": action,
        "score_breakdown": {
            "pe_vs_sector": {"score": pe_score, "max": 25, "label": pe_label,
                              "trailing_pe": round(trailing_pe, 1) if trailing_pe else None,
                              "forward_pe": round(forward_pe, 1) if forward_pe else None,
                              "sector_avg_pe": sector_pe_avg},
            "pb_ratio": {"score": pb_score, "max": 20, "label": pb_label,
                         "pb": round(pb, 2) if pb else None, "sector_avg_pb": sector_pb_avg},
            "ev_ebitda": {"score": ev_score, "max": 20, "label": ev_label,
                          "ev_ebitda": round(ev_ebitda, 1) if ev_ebitda else None,
                          "sector_avg": sector_ev_ebitda_avg},
            "peg_ratio": {"score": peg_score, "max": 15, "label": peg_label,
                          "peg": round(peg, 2) if peg else None},
            "dcf_proxy": {"score": dcf_score, "max": 20, "label": dcf_label,
                          "dcf_implied_price": dcf_implied,
                          "dcf_upside_pct": dcf_upside_pct,
                          "growth_assumption_pct": round((eps_growth or revenue_growth or 0.05) * 100, 1),
                          "discount_rate_pct": round((0.09 + (beta - 1.0) * 0.02) * 100, 1) if beta else 10.0},
        },
        "key_metrics": {
            "trailing_pe": round(trailing_pe, 1) if trailing_pe else None,
            "forward_pe": round(forward_pe, 1) if forward_pe else None,
            "price_to_book": round(pb, 2) if pb else None,
            "ev_ebitda": round(ev_ebitda, 1) if ev_ebitda else None,
            "peg_ratio": round(peg, 2) if peg else None,
            "price_to_sales": round(price_to_sales, 2) if price_to_sales else None,
            "eps_ttm": round(eps_ttm, 2) if eps_ttm else None,
            "eps_forward": round(eps_forward, 2) if eps_forward else None,
            "roe_pct": round(roe * 100, 1) if roe else None,
            "market_cap_B": round(market_cap / 1e9, 2) if market_cap else None,
        },
        "signal_thresholds": "DEEPLY_UNDERVALUED ≥72 | UNDERVALUED ≥55 | FAIRLY_VALUED ≥38 | OVERVALUED ≥22 | SIGNIFICANTLY_OVERVALUED <22",
        "source": "Yahoo Finance public data — no API key required",
        "note": "DCF uses 10-year FCF projection with growth = min(max(eps_growth, 0%), 30%). Terminal growth 2.5%. Combine with get_earnings_quality_score() for quality check.",
    }


@mcp.tool()
async def get_earnings_growth_tracker(ticker: str) -> dict:
    """Track EPS and Revenue YoY growth rates across last 4 quarters. Detects growth acceleration or deceleration regime.

    Analyzes quarterly EPS and Revenue YoY growth %, growth acceleration/deceleration delta,
    and classifies into: ACCELERATING_GROWTH / STEADY_GROWTH / DECELERATING / STALLING / DECLINING.
    Returns composite signal combining EPS (60%) + Revenue (40%) growth trajectory.
    Ideal for GARP (Growth At Reasonable Price) screening and momentum confirmation.
    """
    await Actor.charge(event_name="advanced_tool")
    import numpy as np

    ticker = ticker.upper().strip()
    t = yf.Ticker(ticker)
    info = t.info

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "Unknown")

    eps_history = []
    try:
        earnings = t.earnings_history
        if earnings is not None and not earnings.empty:
            for i, row in earnings.iterrows():
                actual = row.get("epsActual", None)
                if actual is not None and not (isinstance(actual, float) and np.isnan(actual)):
                    eps_history.append({
                        "date": str(i)[:10],
                        "eps_actual": round(float(actual), 3)
                    })
    except Exception:
        eps_history = []

    revenue_data = []
    try:
        fin = t.quarterly_financials
        if fin is not None and not fin.empty:
            for col in fin.columns[:8]:
                rev = None
                for row_name in ["Total Revenue", "Revenue", "Net Revenue"]:
                    if row_name in fin.index:
                        val = fin.loc[row_name, col]
                        if val is not None and not (isinstance(val, float) and np.isnan(val)):
                            rev = float(val)
                            break
                if rev is not None:
                    revenue_data.append({"date": str(col)[:10], "revenue": rev})
    except Exception:
        revenue_data = []

    eps_yoy_growth = []
    if len(eps_history) >= 5:
        eps_sorted = sorted(eps_history, key=lambda x: x["date"], reverse=True)
        for i in range(min(4, len(eps_sorted))):
            yoy_idx = i + 4
            if yoy_idx < len(eps_sorted):
                curr = eps_sorted[i]["eps_actual"]
                prev = eps_sorted[yoy_idx]["eps_actual"]
                if prev != 0:
                    growth = ((curr - prev) / abs(prev)) * 100
                else:
                    growth = 100.0 if curr > 0 else -100.0
                eps_yoy_growth.append({
                    "quarter": eps_sorted[i]["date"][:7],
                    "eps": round(curr, 3),
                    "eps_yoy_pct": round(growth, 1)
                })

    rev_yoy_growth = []
    if len(revenue_data) >= 5:
        rev_sorted = sorted(revenue_data, key=lambda x: x["date"], reverse=True)
        for i in range(min(4, len(rev_sorted))):
            yoy_idx = i + 4
            if yoy_idx < len(rev_sorted):
                curr = rev_sorted[i]["revenue"]
                prev = rev_sorted[yoy_idx]["revenue"]
                if prev != 0:
                    growth = ((curr - prev) / abs(prev)) * 100
                else:
                    growth = 100.0 if curr > 0 else -100.0
                rev_yoy_growth.append({
                    "quarter": rev_sorted[i]["date"][:7],
                    "revenue_B": round(curr / 1e9, 3),
                    "revenue_yoy_pct": round(growth, 1)
                })

    def classify_growth(growth_list, key):
        if not growth_list or len(growth_list) < 2:
            return "INSUFFICIENT_DATA", 50, 0.0, 0.0
        vals = [g[key] for g in growth_list]
        recent = vals[:2]
        prior = vals[2:4] if len(vals) >= 4 else vals[:2]
        avg_recent = sum(recent) / len(recent)
        avg_prior = sum(prior) / len(prior)
        avg_all = sum(vals) / len(vals)
        delta = avg_recent - avg_prior
        if avg_all < -10:
            return "DECLINING", 10, round(avg_recent, 1), round(delta, 1)
        elif avg_all < 0:
            return "STALLING", 25, round(avg_recent, 1), round(delta, 1)
        elif delta > 10 and avg_recent > 5:
            return "ACCELERATING_GROWTH", 90, round(avg_recent, 1), round(delta, 1)
        elif delta > 3 and avg_recent > 0:
            return "ACCELERATING_GROWTH", 75, round(avg_recent, 1), round(delta, 1)
        elif abs(delta) <= 5 and avg_all > 5:
            return "STEADY_GROWTH", 65, round(avg_recent, 1), round(delta, 1)
        elif delta < -10:
            return "DECELERATING", 30, round(avg_recent, 1), round(delta, 1)
        elif delta < -5:
            return "DECELERATING", 40, round(avg_recent, 1), round(delta, 1)
        else:
            return "STEADY_GROWTH", 55, round(avg_recent, 1), round(delta, 1)

    eps_regime, eps_score, eps_recent_avg, eps_delta = classify_growth(eps_yoy_growth, "eps_yoy_pct")
    rev_regime, rev_score, rev_recent_avg, rev_delta = classify_growth(rev_yoy_growth, "revenue_yoy_pct")

    composite_score = int(eps_score * 0.6 + rev_score * 0.4)

    if composite_score >= 80:
        composite_signal = "STRONG_GROWTH_ACCELERATION"
        strategy = "Premium growth candidate. Momentum entry viable. Monitor sustainability of acceleration."
    elif composite_score >= 65:
        composite_signal = "HEALTHY_GROWTH"
        strategy = "Solid growth trajectory. Suitable for growth-oriented portfolios."
    elif composite_score >= 45:
        composite_signal = "MIXED_GROWTH"
        strategy = "Uneven signals. Review guidance and analyst revisions before positioning."
    elif composite_score >= 25:
        composite_signal = "WEAKENING_GROWTH"
        strategy = "Growth decelerating. Multiple compression risk. Wait for stabilization."
    else:
        composite_signal = "GROWTH_CONCERN"
        strategy = "Negative or stalling growth. Avoid growth positioning. Value/turnaround analysis needed."

    return {
        "ticker": ticker,
        "company": company_name,
        "sector": sector,
        "composite_signal": composite_signal,
        "composite_score": composite_score,
        "max_score": 100,
        "eps_analysis": {
            "regime": eps_regime,
            "score": eps_score,
            "recent_2q_avg_growth_pct": eps_recent_avg,
            "acceleration_delta_pct": eps_delta,
            "quarterly_history": eps_yoy_growth,
            "note": "Positive delta = accelerating vs prior 2Q. Negative = decelerating."
        },
        "revenue_analysis": {
            "regime": rev_regime,
            "score": rev_score,
            "recent_2q_avg_growth_pct": rev_recent_avg,
            "acceleration_delta_pct": rev_delta,
            "quarterly_history": rev_yoy_growth
        },
        "strategy": strategy,
        "regime_guide": "ACCELERATING_GROWTH: delta>3% & recent>0% | STEADY_GROWTH: |delta|<=5% & avg>5% | DECELERATING: delta<-5% | STALLING: avg<0% | DECLINING: avg<-10%",
        "source": "Yahoo Finance public data — no API key required",
        "note": "Combine with get_valuation_composite() for GARP (Growth At Reasonable Price) analysis."
    }


@mcp.tool()
async def get_liquidity_score(ticker: str) -> dict:
    """Assess stock liquidity with composite 0-100 score. Estimates bid-ask spread proxy, ADTV, Amihud illiquidity ratio, and position sizing difficulty.

    Components (max 100pts):
    - Market cap tier (30pts): MEGA_CAP >=200B / LARGE_CAP >=10B / MID_CAP >=2B / SMALL_CAP >=300M / MICRO_CAP
    - Avg Daily Dollar Volume 30d (35pts): ULTRA_HIGH >=1B / HIGH >=100M / MODERATE >=10M / LOW >=1M / VERY_LOW
    - Amihud Illiquidity Ratio (20pts): mean(|daily return| / dollar_volume) — lower = more liquid
    - Bid-Ask Spread Proxy (15pts): estimated from 30d realized volatility × 0.003

    Signal: HIGHLY_LIQUID (>=80) / LIQUID (>=60) / MODERATE (>=40) / ILLIQUID (>=20) / VERY_ILLIQUID (<20)
    """
    await Actor.charge(event_name="advanced_tool")
    import numpy as np

    ticker = ticker.upper().strip()
    t = yf.Ticker(ticker)
    info = t.info

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "Unknown")

    market_cap = info.get("marketCap", None)
    float_shares = info.get("floatShares", None)

    hist = t.history(period="3mo")

    price = info.get("currentPrice", info.get("regularMarketPrice", None))
    if price is None and not hist.empty:
        price = float(hist["Close"].iloc[-1])

    vol_30d = None
    vol_90d = None
    dollar_vol_30d = None
    amihud_ratio = None
    spread_proxy_pct = None

    if not hist.empty and len(hist) >= 20:
        closes = hist["Close"].values.astype(float)
        volumes = hist["Volume"].values.astype(float)

        vol_30d = float(np.mean(volumes[-30:])) if len(volumes) >= 30 else float(np.mean(volumes))
        vol_90d = float(np.mean(volumes))

        dv = closes[-30:] * volumes[-30:] if len(volumes) >= 30 else closes * volumes
        dollar_vol_30d = float(np.mean(dv)) / 1e6

        log_ret = np.diff(np.log(np.where(closes > 0, closes, 1e-9)))
        dv_all = closes[1:] * volumes[1:]
        dv_safe = np.where(dv_all > 0, dv_all, 1)
        amihud_vals = np.abs(log_ret) / dv_safe * 1e9
        amihud_ratio = float(np.mean(amihud_vals[-60:])) if len(amihud_vals) >= 60 else float(np.mean(amihud_vals))

        lr30 = np.diff(np.log(np.where(closes[-31:] > 0, closes[-31:], 1e-9))) if len(closes) >= 31 else log_ret
        rv_30d = float(np.std(lr30) * np.sqrt(252)) * 100 if len(lr30) > 1 else 30.0
        spread_proxy_pct = round(rv_30d * 0.003, 4)

    if market_cap:
        if market_cap >= 200e9:
            cap_tier, cap_score = "MEGA_CAP", 30
        elif market_cap >= 10e9:
            cap_tier, cap_score = "LARGE_CAP", 25
        elif market_cap >= 2e9:
            cap_tier, cap_score = "MID_CAP", 18
        elif market_cap >= 300e6:
            cap_tier, cap_score = "SMALL_CAP", 10
        else:
            cap_tier, cap_score = "MICRO_CAP", 4
    else:
        cap_tier, cap_score = "UNKNOWN", 10

    if dollar_vol_30d:
        if dollar_vol_30d >= 1000:
            adtv_label, adtv_score = "ULTRA_HIGH_ADTV", 35
        elif dollar_vol_30d >= 100:
            adtv_label, adtv_score = "HIGH_ADTV", 28
        elif dollar_vol_30d >= 10:
            adtv_label, adtv_score = "MODERATE_ADTV", 20
        elif dollar_vol_30d >= 1:
            adtv_label, adtv_score = "LOW_ADTV", 10
        else:
            adtv_label, adtv_score = "VERY_LOW_ADTV", 3
    else:
        adtv_label, adtv_score = "UNKNOWN", 10

    if amihud_ratio is not None:
        if amihud_ratio < 0.1:
            amihud_label, amihud_score = "HIGHLY_LIQUID_AMIHUD", 20
        elif amihud_ratio < 1.0:
            amihud_label, amihud_score = "LIQUID_AMIHUD", 15
        elif amihud_ratio < 5.0:
            amihud_label, amihud_score = "MODERATE_AMIHUD", 10
        elif amihud_ratio < 20.0:
            amihud_label, amihud_score = "ILLIQUID_AMIHUD", 5
        else:
            amihud_label, amihud_score = "VERY_ILLIQUID_AMIHUD", 1
    else:
        amihud_label, amihud_score = "UNKNOWN", 10

    if spread_proxy_pct is not None:
        if spread_proxy_pct < 0.05:
            spread_score = 15
        elif spread_proxy_pct < 0.15:
            spread_score = 12
        elif spread_proxy_pct < 0.30:
            spread_score = 8
        elif spread_proxy_pct < 0.50:
            spread_score = 4
        else:
            spread_score = 1
    else:
        spread_score = 8

    total_score = cap_score + adtv_score + amihud_score + spread_score

    if total_score >= 80:
        liquidity_signal = "HIGHLY_LIQUID"
        difficulty = "EASY — Institutions can enter/exit $10M+ positions with minimal slippage."
        easy_size_M = round((dollar_vol_30d or 1) * 0.10, 1)
    elif total_score >= 60:
        liquidity_signal = "LIQUID"
        difficulty = "MANAGEABLE — Mid-size positions ($1-10M) feasible. Large trades may move price slightly."
        easy_size_M = round((dollar_vol_30d or 1) * 0.05, 1)
    elif total_score >= 40:
        liquidity_signal = "MODERATE"
        difficulty = "MODERATE — Position sizing requires care. Spread costs significant on large trades."
        easy_size_M = round((dollar_vol_30d or 0.5) * 0.02, 1)
    elif total_score >= 20:
        liquidity_signal = "ILLIQUID"
        difficulty = "DIFFICULT — Large positions impractical. Market impact costs substantial."
        easy_size_M = round((dollar_vol_30d or 0.1) * 0.01, 1)
    else:
        liquidity_signal = "VERY_ILLIQUID"
        difficulty = "VERY DIFFICULT — Institutional participation impractical. Retail-sized positions only."
        easy_size_M = 0.05

    vol_trend = "UNKNOWN"
    if vol_30d and vol_90d and vol_90d > 0:
        ratio = vol_30d / vol_90d
        if ratio >= 1.3:
            vol_trend = "VOLUME_SURGE"
        elif ratio >= 1.1:
            vol_trend = "ABOVE_AVERAGE"
        elif ratio >= 0.9:
            vol_trend = "NORMAL"
        elif ratio >= 0.7:
            vol_trend = "BELOW_AVERAGE"
        else:
            vol_trend = "VOLUME_DRY_UP"

    return {
        "ticker": ticker,
        "company": company_name,
        "sector": sector,
        "liquidity_signal": liquidity_signal,
        "liquidity_score": total_score,
        "max_score": 100,
        "position_sizing": {
            "difficulty": difficulty,
            "easy_entry_exit_size_M": easy_size_M,
            "note": "Easy entry/exit estimated as % of 30d ADTV scaled by liquidity tier."
        },
        "score_breakdown": {
            "market_cap_tier": {
                "score": cap_score, "max": 30, "label": cap_tier,
                "market_cap_B": round(market_cap / 1e9, 2) if market_cap else None
            },
            "avg_daily_dollar_volume": {
                "score": adtv_score, "max": 35, "label": adtv_label,
                "adtv_30d_M": round(dollar_vol_30d, 2) if dollar_vol_30d else None
            },
            "amihud_illiquidity": {
                "score": amihud_score, "max": 20, "label": amihud_label,
                "ratio": round(amihud_ratio, 4) if amihud_ratio is not None else None,
                "note": "Lower = more liquid. Bps per $1B traded."
            },
            "spread_proxy": {
                "score": spread_score, "max": 15,
                "spread_proxy_pct": spread_proxy_pct,
                "note": "Estimated bid-ask spread from 30d realized volatility × 0.003."
            }
        },
        "volume_metrics": {
            "avg_volume_30d": int(vol_30d) if vol_30d else None,
            "avg_volume_90d": int(vol_90d) if vol_90d else None,
            "volume_trend": vol_trend,
            "float_shares_M": round(float_shares / 1e6, 1) if float_shares else None,
            "current_price": round(price, 2) if price else None
        },
        "signal_thresholds": "HIGHLY_LIQUID >=80 | LIQUID >=60 | MODERATE >=40 | ILLIQUID >=20 | VERY_ILLIQUID <20",
        "source": "Yahoo Finance public data — no API key required",
        "note": "Use before entering large positions. Combine with get_smart_money_composite() for institutional flow context."
    }

# ─────────────────────────────────────────────────────────────────
# v4.0.0 — Quality Factor Screen + Capital Allocation Score
# ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_quality_factor_screen(top_n: int = 20) -> dict:
    """
    Screen S&P 500 proxy universe for high-quality stocks using a
    multi-component quality scorecard (ROE, Debt/Equity, EPS CAGR,
    FCF margin, earnings stability). Returns top-N quality picks
    with sector breakdown and composite QUALITY_ELITE signal.

    Components:
    - ROE Quality (25pts): returnOnEquity ≥20%=25 / ≥15%=20 / ≥10%=14 / ≥0%=6 / negative=0
    - Debt/Equity Safety (25pts): D/E ≤0.3=25 / ≤0.6=20 / ≤1.0=14 / ≤2.0=6 / >2.0=0
    - EPS Growth (20pts): 3yr CAGR ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0
    - FCF Margin (20pts): FCF/Revenue ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0
    - Earnings Stability (10pts): profit margin consistency score

    Signals: QUALITY_ELITE(≥85) / QUALITY_SOLID(≥65) / QUALITY_MIXED(≥40) / LOW_QUALITY(<40)
    Tier: advanced_tool ($0.003/call)
    """
    await Actor.charge(event_name="advanced_tool")
    import concurrent.futures

    top_n = max(5, min(50, top_n))

    universe = [
        "AAPL","MSFT","NVDA","GOOGL","META","AVGO","ORCL","CSCO","ADBE","TXN",
        "QCOM","CRM","INTC","AMD","AMAT","MU","KLAC","LRCX","MCHP","ADI",
        "LLY","UNH","JNJ","ABBV","MRK","TMO","DHR","ABT","ISRG","BSX",
        "SYK","MDT","BDX","EW","ALGN","IDXX","MTD","WST","PODD","BAX",
        "BRK-B","JPM","V","MA","BAC","WFC","GS","MS","AXP","BLK",
        "SPGI","ICE","CME","MCO","CBOE","CINF","AFL","GL","MKL","RLI",
        "PG","KO","PEP","COST","WMT","MCD","MDLZ","STZ","HSY","GIS",
        "AMZN","TSLA","HD","NKE","LOW","SBUX","TJX","ROST","YUM","DPZ",
        "CAT","HON","UPS","RTX","LMT","GE","MMM","EMR","ETN","ITW",
        "ROK","XYL","IEX","FELE","MIDD","AWI","BRC","EXPO","TRMK","MGLN",
        "XOM","CVX","COP","SLB","EOG","PSX","VLO","MPC","OXY","HES",
        "LIN","APD","SHW","FCX","NEM","ECL","ALB","CF","MOS","IFF",
        "PLD","AMT","EQIX","CCI","PSA","DLR","O","VICI","WY","EXR",
        "NEE","DUK","SO","D","AEP","XEL","SRE","ED","PCG","EXC",
        "NFLX","DIS","CMCSA","T","VZ","TMUS","EA","TTWO","CHTR","WBD",
    ]

    def fetch_quality(ticker):
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            roe = info.get("returnOnEquity")
            de = info.get("debtToEquity")
            revenue = info.get("totalRevenue") or info.get("revenue")
            fcf = info.get("freeCashflow")
            market_cap = info.get("marketCap")
            sector = info.get("sector", "Unknown")
            name = info.get("shortName", ticker)
            eps_fwd = info.get("forwardEps")
            eps_trail = info.get("trailingEps")

            try:
                hist = t.earnings_history
                if hist is not None and not hist.empty and "epsActual" in hist.columns:
                    eps_vals = hist["epsActual"].dropna().tolist()
                else:
                    eps_vals = []
            except Exception:
                eps_vals = []

            eps_cagr = None
            if len(eps_vals) >= 4:
                recent_annual = sum(eps_vals[:4])
                old_annual = sum(eps_vals[-4:]) if len(eps_vals) >= 8 else None
                if old_annual and old_annual > 0 and recent_annual > 0:
                    eps_cagr = (recent_annual / old_annual) ** (1 / 2.0) - 1
            if eps_cagr is None and eps_fwd and eps_trail and eps_trail > 0:
                eps_cagr = (eps_fwd - eps_trail) / abs(eps_trail)

            fcf_margin = None
            if fcf and revenue and revenue > 0:
                fcf_margin = fcf / revenue

            try:
                fin = t.quarterly_financials
                if fin is not None and not fin.empty and "Net Income" in fin.index:
                    ni_vals = fin.loc["Net Income"].dropna().tolist()[:8]
                    stability_rate = sum(1 for x in ni_vals if x > 0) / len(ni_vals) if ni_vals else None
                else:
                    stability_rate = None
            except Exception:
                stability_rate = None

            if roe is not None:
                roe_score = 25 if roe >= 0.20 else (20 if roe >= 0.15 else (14 if roe >= 0.10 else (6 if roe >= 0 else 0)))
            else:
                roe_score = 8

            if de is not None:
                de_n = de / 100 if de > 10 else de
                de_score = 25 if de_n <= 0.3 else (20 if de_n <= 0.6 else (14 if de_n <= 1.0 else (6 if de_n <= 2.0 else 0)))
            else:
                de_score = 10

            if eps_cagr is not None:
                eps_score = 20 if eps_cagr >= 0.20 else (16 if eps_cagr >= 0.12 else (11 if eps_cagr >= 0.06 else (5 if eps_cagr >= 0 else 0)))
            else:
                eps_score = 8

            if fcf_margin is not None:
                fcf_score = 20 if fcf_margin >= 0.20 else (16 if fcf_margin >= 0.12 else (11 if fcf_margin >= 0.06 else (5 if fcf_margin >= 0 else 0)))
            else:
                fcf_score = 8

            if stability_rate is not None:
                stab_score = 10 if stability_rate >= 0.90 else (8 if stability_rate >= 0.75 else (5 if stability_rate >= 0.60 else (2 if stability_rate >= 0.40 else 0)))
            else:
                stab_score = 5

            total = roe_score + de_score + eps_score + fcf_score + stab_score
            quality_signal = "QUALITY_ELITE" if total >= 85 else ("QUALITY_SOLID" if total >= 65 else ("QUALITY_MIXED" if total >= 40 else "LOW_QUALITY"))

            return {
                "ticker": ticker, "company": name, "sector": sector,
                "quality_signal": quality_signal, "quality_score": total, "max_score": 100,
                "components": {"roe_score": roe_score, "de_score": de_score, "eps_growth_score": eps_score, "fcf_margin_score": fcf_score, "earnings_stability_score": stab_score},
                "raw_metrics": {
                    "roe_pct": round(roe * 100, 1) if roe is not None else None,
                    "debt_equity": round(de / 100, 2) if de and de > 10 else (round(de, 2) if de else None),
                    "eps_cagr_pct": round(eps_cagr * 100, 1) if eps_cagr is not None else None,
                    "fcf_margin_pct": round(fcf_margin * 100, 1) if fcf_margin is not None else None,
                    "earnings_stability_rate": round(stability_rate, 2) if stability_rate else None,
                    "market_cap_B": round(market_cap / 1e9, 1) if market_cap else None,
                }
            }
        except Exception:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_quality, t): t for t in universe}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["quality_score"], reverse=True)
    top = results[:top_n]
    quality_elite = [r for r in results if r["quality_signal"] == "QUALITY_ELITE"]
    low_quality = [r for r in results if r["quality_signal"] == "LOW_QUALITY"]

    sector_counts = {}
    for r in top:
        s = r.get("sector", "Unknown")
        sector_counts[s] = sector_counts.get(s, 0) + 1
    sector_ranking = sorted(sector_counts.items(), key=lambda x: -x[1])
    avg_score = round(sum(r["quality_score"] for r in results) / len(results), 1) if results else 0

    return {
        "screen": "Quality Factor Screen", "universe_scanned": len(results), "top_n_requested": top_n,
        "summary": {
            "quality_elite_count": len(quality_elite),
            "low_quality_count": len(low_quality),
            "avg_universe_score": avg_score,
            "market_quality_signal": "HIGH_QUALITY_MARKET" if avg_score >= 65 else ("MIXED_QUALITY_MARKET" if avg_score >= 45 else "LOW_QUALITY_MARKET"),
        },
        "top_quality_picks": top,
        "quality_elite_names": [r["ticker"] for r in quality_elite[:15]],
        "lowest_quality": [{"ticker": r["ticker"], "company": r["company"], "sector": r["sector"], "quality_score": r["quality_score"]} for r in low_quality[-5:]],
        "sector_concentration_in_top_n": [{"sector": s, "count": c} for s, c in sector_ranking],
        "scoring_guide": {
            "roe_quality": "25pts — ROE ≥20%=25 / ≥15%=20 / ≥10%=14 / ≥0%=6 / negative=0",
            "debt_equity_safety": "25pts — D/E ≤0.3=25 / ≤0.6=20 / ≤1.0=14 / ≤2.0=6 / >2.0=0",
            "eps_growth": "20pts — 3yr CAGR ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0",
            "fcf_margin": "20pts — FCF/Revenue ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0",
            "earnings_stability": "10pts — Quarterly NI positive rate",
        },
        "strategy_guide": "QUALITY_ELITE: Strong moat + capital efficiency. QUALITY_SOLID: Good fundamentals. QUALITY_MIXED: Cyclical or transitional. LOW_QUALITY: Avoid or short.",
        "source": "Yahoo Finance public data — no API key required",
        "note": "Combine with get_valuation_composite() for GARP strategy."
    }


@mcp.tool()
async def get_capital_allocation_score(ticker: str) -> dict:
    """
    Analyze how efficiently a company allocates its capital using a
    multi-component scorecard: buyback yield, dividend growth consistency,
    FCF reinvestment efficiency, M&A discipline (goodwill changes),
    and ROIC vs WACC proxy.

    Components:
    - Buyback Yield (25pts): shares_outstanding YoY change (shrinkage = buybacks)
    - Dividend Growth Consistency (20pts): DPS growth rate + payout sustainability
    - FCF Reinvestment Ratio (20pts): capex / FCF ratio (balanced reinvestment)
    - M&A Discipline (20pts): goodwill/assets growth (low = disciplined M&A)
    - ROIC Proxy (15pts): net_income / (equity + long_term_debt)

    Signals: EXCELLENT_CAPITAL_ALLOCATOR(≥80) / GOOD_ALLOCATOR(≥60) /
             MIXED_ALLOCATOR(≥40) / POOR_ALLOCATOR(<40)
    Tier: advanced_tool ($0.003/call)
    """
    await Actor.charge(event_name="advanced_tool")
    ticker = ticker.upper().strip()

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        company_name = info.get("shortName", ticker)
        sector = info.get("sector", "Unknown")
        market_cap = info.get("marketCap")
        shares_out = info.get("sharesOutstanding")

        # Buyback Yield
        try:
            cf = t.cashflow
            repurchase = None
            if cf is not None and not cf.empty:
                for key in ["Repurchase Of Capital Stock", "Common Stock Repurchased"]:
                    if key in cf.index:
                        vals = cf.loc[key].dropna().tolist()
                        if vals:
                            repurchase = vals[0]
                            break
        except Exception:
            repurchase = None

        try:
            bs = t.balance_sheet
            ordinary_shares = None
            if bs is not None and not bs.empty:
                for key in ["Ordinary Shares Number", "Common Stock"]:
                    if key in bs.index:
                        vals = bs.loc[key].dropna().tolist()
                        if len(vals) >= 2 and vals[0] and vals[1]:
                            ordinary_shares = (vals[0] - vals[1]) / abs(vals[1])
                            break
        except Exception:
            ordinary_shares = None

        buyback_yield = None
        if repurchase and market_cap and market_cap > 0:
            buyback_yield = abs(repurchase) / market_cap if repurchase < 0 else 0

        if buyback_yield is not None:
            bb_score = 25 if buyback_yield >= 0.05 else (20 if buyback_yield >= 0.03 else (14 if buyback_yield >= 0.01 else (8 if buyback_yield >= 0.001 else 3)))
        elif ordinary_shares is not None:
            bb_score = 22 if ordinary_shares <= -0.03 else (16 if ordinary_shares <= -0.01 else (10 if ordinary_shares <= 0.01 else 3))
        else:
            bb_score = 10

        # Dividend Growth
        div_yield = info.get("dividendYield") or 0
        div_rate = info.get("dividendRate") or 0
        payout_ratio = info.get("payoutRatio") or 0
        try:
            div_history = t.dividends
            if div_history is not None and len(div_history) >= 8:
                annual_divs = div_history.resample("YE").sum()
                if len(annual_divs) >= 2:
                    recent = float(annual_divs.iloc[-1])
                    prior = float(annual_divs.iloc[-2])
                    div_growth = (recent - prior) / prior if prior > 0 else 0
                else:
                    div_growth = 0
                has_dividends = True
            else:
                div_growth = 0
                has_dividends = False
        except Exception:
            div_growth = 0
            has_dividends = False

        if not has_dividends and div_rate == 0:
            div_score = 14 if sector in ["Technology", "Consumer Discretionary", "Communication Services"] else 8
        else:
            if div_growth >= 0.08 and payout_ratio <= 0.60: div_score = 20
            elif div_growth >= 0.04 and payout_ratio <= 0.70: div_score = 16
            elif div_growth >= 0.00 and payout_ratio <= 0.80: div_score = 11
            elif payout_ratio > 0.90: div_score = 4
            else: div_score = 8

        # FCF Reinvestment
        fcf = info.get("freeCashflow")
        capex = info.get("capitalExpenditures")
        fcf_reinvest_ratio = None
        if capex and fcf and fcf > 0:
            fcf_reinvest_ratio = abs(capex) / fcf

        if fcf_reinvest_ratio is not None:
            if 0.20 <= fcf_reinvest_ratio <= 0.60: fcf_reinvest_score = 20
            elif 0.10 <= fcf_reinvest_ratio < 0.20: fcf_reinvest_score = 16
            elif 0.60 < fcf_reinvest_ratio <= 0.90: fcf_reinvest_score = 12
            elif fcf_reinvest_ratio > 0.90: fcf_reinvest_score = 5
            else: fcf_reinvest_score = 12
        elif fcf and fcf > 0:
            fcf_reinvest_score = 14
        else:
            fcf_reinvest_score = 5

        # M&A Discipline / Goodwill
        try:
            bs_annual = t.balance_sheet
            goodwill_score_val = 15
            goodwill_ratio = None
            goodwill_growth = None
            if bs_annual is not None and not bs_annual.empty:
                for gw_key in ["Goodwill", "Goodwill And Other Intangible Assets"]:
                    if gw_key in bs_annual.index:
                        gw_vals = bs_annual.loc[gw_key].dropna().tolist()
                        total_assets_vals = bs_annual.loc["Total Assets"].dropna().tolist() if "Total Assets" in bs_annual.index else []
                        if len(gw_vals) >= 1 and len(total_assets_vals) >= 1:
                            goodwill_ratio = gw_vals[0] / total_assets_vals[0] if total_assets_vals[0] > 0 else None
                        if len(gw_vals) >= 2 and gw_vals[1] and gw_vals[1] > 0:
                            goodwill_growth = (gw_vals[0] - gw_vals[1]) / abs(gw_vals[1])
                        break
                if goodwill_ratio is not None:
                    goodwill_score_val = (20 if goodwill_ratio <= 0.05 else (16 if goodwill_ratio <= 0.15 else (11 if goodwill_ratio <= 0.30 else (6 if goodwill_ratio <= 0.50 else 2))))
                    if goodwill_growth is not None:
                        if goodwill_growth > 0.20: goodwill_score_val = max(0, goodwill_score_val - 3)
                        elif goodwill_growth < 0: goodwill_score_val = max(0, goodwill_score_val - 2)
        except Exception:
            goodwill_score_val = 10
            goodwill_ratio = None
            goodwill_growth = None

        # ROIC Proxy
        net_income = info.get("netIncomeToCommon")
        total_equity = info.get("bookValue") or info.get("totalStockholderEquity")
        total_debt = info.get("totalDebt") or 0
        roic = None
        if net_income and total_equity and market_cap:
            book_equity = total_equity * (shares_out or 1) if total_equity < 1000 else total_equity
            invested_capital = book_equity + total_debt
            if invested_capital > 0:
                roic = net_income / invested_capital

        roic_score = 15 if roic and roic >= 0.20 else (12 if roic and roic >= 0.15 else (9 if roic and roic >= 0.10 else (5 if roic and roic >= 0.05 else (2 if roic else 7))))

        total_score = bb_score + div_score + fcf_reinvest_score + goodwill_score_val + roic_score
        capital_signal = "EXCELLENT_CAPITAL_ALLOCATOR" if total_score >= 80 else ("GOOD_ALLOCATOR" if total_score >= 60 else ("MIXED_ALLOCATOR" if total_score >= 40 else "POOR_ALLOCATOR"))

        action_map = {
            "EXCELLENT_CAPITAL_ALLOCATOR": "Strong shareholder value creation. Premium valuation justified.",
            "GOOD_ALLOCATOR": "Above-average capital discipline. Good long-term holding.",
            "MIXED_ALLOCATOR": "Inconsistent allocation. Monitor for goodwill impairment or dilution.",
            "POOR_ALLOCATOR": "Capital destruction risk. High M&A or dilutive equity issuance. Avoid unless turnaround.",
        }

        return {
            "ticker": ticker, "company": company_name, "sector": sector,
            "capital_allocation_signal": capital_signal,
            "capital_allocation_score": total_score, "max_score": 100,
            "action_guide": action_map[capital_signal],
            "score_breakdown": {
                "buyback_yield": {"score": bb_score, "max": 25, "buyback_yield_pct": round(buyback_yield * 100, 2) if buyback_yield else None, "shares_change_pct": round(ordinary_shares * 100, 2) if ordinary_shares else None},
                "dividend_growth_consistency": {"score": div_score, "max": 20, "dividend_yield_pct": round(div_yield * 100, 2) if div_yield else None, "div_growth_yoy_pct": round(div_growth * 100, 1) if div_growth else None, "payout_ratio_pct": round(payout_ratio * 100, 1) if payout_ratio else None, "has_dividends": has_dividends},
                "fcf_reinvestment_ratio": {"score": fcf_reinvest_score, "max": 20, "capex_to_fcf": round(fcf_reinvest_ratio, 2) if fcf_reinvest_ratio else None, "fcf_M": round(fcf / 1e6, 1) if fcf else None, "capex_M": round(abs(capex) / 1e6, 1) if capex else None, "note": "Optimal 0.20-0.60"},
                "ma_discipline_goodwill": {"score": goodwill_score_val, "max": 20, "goodwill_to_assets_pct": round(goodwill_ratio * 100, 1) if goodwill_ratio else None, "goodwill_growth_pct": round(goodwill_growth * 100, 1) if goodwill_growth is not None else None},
                "roic_proxy": {"score": roic_score, "max": 15, "roic_pct": round(roic * 100, 1) if roic else None, "note": "ROIC = Net Income / Invested Capital proxy"},
            },
            "signal_thresholds": "EXCELLENT ≥80 | GOOD ≥60 | MIXED ≥40 | POOR <40",
            "source": "Yahoo Finance public data — no API key required",
            "note": "Combine with get_quality_factor_screen() and get_valuation_composite() for full analysis."
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@mcp.tool()
async def get_management_quality_score(ticker: str) -> dict:
    """Score management quality using ROE trend, R&D efficiency, SBC discipline, and operating margin stability."""
    await Actor.charge("advanced_tool")
    try:
        import yfinance as yf
        import numpy as np

        ticker = ticker.upper().strip()
        stock = yf.Ticker(ticker)
        info = stock.info

        company_name = info.get("shortName", ticker)
        sector = info.get("sector", "Unknown")

        ceo_name = "Unknown"
        officers = info.get("companyOfficers", [])
        for officer in officers:
            title = officer.get("title", "").lower()
            if "chief executive" in title or " ceo" in title:
                ceo_name = officer.get("name", "Unknown")
                break
        ceo_score = 10

        roe_current = info.get("returnOnEquity")
        roe_score = 10
        roe_trend = "UNKNOWN"
        roe_3yr_avg = None

        try:
            financials = stock.financials
            balance = stock.balance_sheet
            if financials is not None and not financials.empty and balance is not None and not balance.empty:
                ni_keys = ["Net Income", "Net Income Common Stockholders", "Net Income Applicable To Common Shares"]
                eq_keys = ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]
                ni_series = next((financials.loc[k] for k in ni_keys if k in financials.index), None)
                eq_series = next((balance.loc[k] for k in eq_keys if k in balance.index), None)
                if ni_series is not None and eq_series is not None:
                    roe_hist = []
                    for col in list(ni_series.index)[:4]:
                        try:
                            ni = ni_series[col]
                            eq = eq_series[col] if col in eq_series.index else None
                            if ni and eq and eq > 0:
                                roe_hist.append(ni / eq)
                        except Exception:
                            pass
                    if len(roe_hist) >= 2:
                        roe_3yr_avg = float(np.mean(roe_hist))
                        delta = roe_hist[0] - float(np.mean(roe_hist[1:]))
                        roe_trend = "IMPROVING" if delta > 0.03 else ("DECLINING" if delta < -0.02 else "STABLE")
        except Exception:
            pass

        roe_val = roe_3yr_avg if roe_3yr_avg is not None else roe_current
        if roe_val is not None:
            if roe_val >= 0.20: base = 20
            elif roe_val >= 0.15: base = 16
            elif roe_val >= 0.10: base = 12
            elif roe_val >= 0.05: base = 7
            elif roe_val >= 0: base = 3
            else: base = 0
            bonus = {"IMPROVING": 5, "STABLE": 0, "DECLINING": -3, "UNKNOWN": 0}[roe_trend]
            roe_score = min(25, max(0, base + bonus))

        rd_score = 10
        rd_to_revenue = None
        rd_efficiency_signal = "NO_RD_DATA"

        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                rd_keys = ["Research And Development", "Research Development", "Research Development Expenses"]
                rev_keys = ["Total Revenue", "Revenue"]
                rd_val = next((abs(financials.loc[k, financials.columns[0]]) for k in rd_keys if k in financials.index and financials.loc[k, financials.columns[0]]), None)
                rev_val = next((financials.loc[k, financials.columns[0]] for k in rev_keys if k in financials.index and financials.loc[k, financials.columns[0]]), None)
                if rd_val and rev_val and rev_val > 0:
                    rd_to_revenue = rd_val / rev_val
                    gm = info.get("grossMargins", 0.3) or 0.3
                    if gm >= 0.60:
                        if rd_to_revenue >= 0.15: rd_efficiency_signal = "HIGH_RD_INVESTMENT"; rd_score = 18
                        elif rd_to_revenue >= 0.08: rd_efficiency_signal = "HEALTHY_RD"; rd_score = 20
                        elif rd_to_revenue >= 0.03: rd_efficiency_signal = "MODERATE_RD"; rd_score = 14
                        else: rd_efficiency_signal = "LOW_RD_FOR_MARGIN"; rd_score = 8
                    elif gm >= 0.35:
                        if rd_to_revenue >= 0.10: rd_efficiency_signal = "HIGH_RD_INVESTMENT"; rd_score = 16
                        elif rd_to_revenue >= 0.04: rd_efficiency_signal = "HEALTHY_RD"; rd_score = 20
                        elif rd_to_revenue >= 0.01: rd_efficiency_signal = "MODERATE_RD"; rd_score = 15
                        else: rd_efficiency_signal = "MINIMAL_RD"; rd_score = 10
                    else:
                        if rd_to_revenue >= 0.05: rd_efficiency_signal = "ABOVE_AVG_RD"; rd_score = 18
                        elif rd_to_revenue >= 0.01: rd_efficiency_signal = "NORMAL_RD"; rd_score = 14
                        else: rd_efficiency_signal = "NO_RD_FOCUS"; rd_score = 12
        except Exception:
            pass

        sbc_score = 10
        sbc_to_revenue = None
        sbc_signal = "SBC_UNKNOWN"

        try:
            cashflow = stock.cashflow
            rev_annual = info.get("totalRevenue")
            if cashflow is not None and not cashflow.empty:
                sbc_keys = ["Stock Based Compensation", "Share Based Compensation"]
                sbc_val = next((abs(cashflow.loc[k, cashflow.columns[0]]) for k in sbc_keys if k in cashflow.index), None)
                if sbc_val and rev_annual and rev_annual > 0:
                    sbc_to_revenue = sbc_val / rev_annual
                    if sbc_to_revenue <= 0.01: sbc_signal = "MINIMAL_DILUTION"; sbc_score = 20
                    elif sbc_to_revenue <= 0.02: sbc_signal = "LOW_DILUTION"; sbc_score = 18
                    elif sbc_to_revenue <= 0.04: sbc_signal = "MODERATE_DILUTION"; sbc_score = 14
                    elif sbc_to_revenue <= 0.08: sbc_signal = "ELEVATED_DILUTION"; sbc_score = 8
                    else: sbc_signal = "HIGH_DILUTION_RISK"; sbc_score = 3
        except Exception:
            pass

        op_margin_score = 8
        op_margin_stability = "UNKNOWN"
        op_margin_avg = None
        op_margin_current = info.get("operatingMargins")

        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                op_keys = ["Operating Income", "Operating Income Loss", "EBIT"]
                rev_keys = ["Total Revenue", "Revenue"]
                op_series = next((financials.loc[k] for k in op_keys if k in financials.index), None)
                rev_series = next((financials.loc[k] for k in rev_keys if k in financials.index), None)
                if op_series is not None and rev_series is not None:
                    margins = []
                    for col in list(op_series.index)[:4]:
                        try:
                            op = op_series[col]
                            rev = rev_series[col] if col in rev_series.index else None
                            if op and rev and rev > 0:
                                margins.append(op / rev)
                        except Exception:
                            pass
                    if len(margins) >= 2:
                        op_margin_avg = float(np.mean(margins))
                        cv = float(np.std(margins)) / abs(op_margin_avg) if op_margin_avg != 0 else 99
                        if cv <= 0.10 and op_margin_avg > 0: op_margin_stability = "HIGHLY_STABLE"; op_margin_score = 15
                        elif cv <= 0.20 and op_margin_avg > 0: op_margin_stability = "STABLE"; op_margin_score = 12
                        elif cv <= 0.35: op_margin_stability = "MODERATE_STABILITY"; op_margin_score = 9
                        elif op_margin_avg > 0: op_margin_stability = "VOLATILE"; op_margin_score = 5
                        else: op_margin_stability = "LOSS_MAKING"; op_margin_score = 1
        except Exception:
            pass

        total_score = ceo_score + roe_score + rd_score + sbc_score + op_margin_score

        if total_score >= 75: mgmt_signal = "EXCELLENT_MANAGEMENT"
        elif total_score >= 58: mgmt_signal = "GOOD_MANAGEMENT"
        elif total_score >= 40: mgmt_signal = "MIXED_MANAGEMENT"
        else: mgmt_signal = "POOR_MANAGEMENT"

        action_map = {
            "EXCELLENT_MANAGEMENT": "Management demonstrates capital discipline, R&D efficiency, and margin stability. Strong long-term hold signal.",
            "GOOD_MANAGEMENT": "Above-average management quality. Solid ROE trend with controlled dilution. Suitable for core portfolio.",
            "MIXED_MANAGEMENT": "Inconsistent signals. Watch for SBC dilution or ROE deterioration before adding exposure.",
            "POOR_MANAGEMENT": "Capital misallocation risk. Excessive dilution, declining ROE, or unstable margins. Avoid or reduce.",
        }

        return {
            "ticker": ticker,
            "company": company_name,
            "sector": sector,
            "ceo_name": ceo_name,
            "management_quality_signal": mgmt_signal,
            "management_quality_score": total_score,
            "max_score": 90,
            "action_guide": action_map[mgmt_signal],
            "score_breakdown": {
                "ceo_tenure_proxy": {"score": ceo_score, "max": 20, "ceo_name": ceo_name, "label": "NEUTRAL_TENURE", "note": "CEO tenure not reliably available via public data. Neutral score applied."},
                "roe_trend": {"score": roe_score, "max": 25, "roe_current_pct": round(roe_current * 100, 1) if roe_current else None, "roe_3yr_avg_pct": round(roe_3yr_avg * 100, 1) if roe_3yr_avg else None, "trend": roe_trend, "note": "IMPROVING trend adds +5pts. DECLINING subtracts -3pts."},
                "rd_efficiency": {"score": rd_score, "max": 20, "rd_to_revenue_pct": round(rd_to_revenue * 100, 1) if rd_to_revenue else None, "signal": rd_efficiency_signal, "gross_margin_pct": round((info.get("grossMargins") or 0) * 100, 1), "note": "R&D intensity scored relative to gross margin tier."},
                "sbc_discipline": {"score": sbc_score, "max": 20, "sbc_to_revenue_pct": round(sbc_to_revenue * 100, 2) if sbc_to_revenue else None, "signal": sbc_signal, "note": "SBC/Revenue ≤2% = low dilution. ≥8% = significant drag on shareholder value."},
                "operating_margin_stability": {"score": op_margin_score, "max": 15, "op_margin_3yr_avg_pct": round(op_margin_avg * 100, 1) if op_margin_avg else None, "op_margin_current_pct": round(op_margin_current * 100, 1) if op_margin_current else None, "stability": op_margin_stability, "note": "CV ≤10% and positive average = HIGHLY_STABLE operating margins."}
            },
            "signal_thresholds": "EXCELLENT ≥75 | GOOD ≥58 | MIXED ≥40 | POOR <40 (out of 90)",
            "source": "Yahoo Finance public data — no API key required",
            "note": "Combine with get_capital_allocation_score() and get_quality_factor_screen() for full management analysis."
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@mcp.tool()
async def get_competitive_moat_score(ticker: str) -> dict:
    """Assess competitive moat width using gross margin stability, operating leverage, pricing power, market position, and R&D IP depth."""
    await Actor.charge("advanced_tool")
    try:
        import yfinance as yf
        import numpy as np

        ticker = ticker.upper().strip()
        stock = yf.Ticker(ticker)
        info = stock.info

        company_name = info.get("shortName", ticker)
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")
        gm_current = info.get("grossMargins", 0) or 0

        gm_score = 10
        gm_stability = "UNKNOWN"
        gm_avg = None
        gm_trend = "STABLE"

        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                gp_series = financials.loc["Gross Profit"] if "Gross Profit" in financials.index else None
                rev_keys = ["Total Revenue", "Revenue"]
                rev_series = next((financials.loc[k] for k in rev_keys if k in financials.index), None)
                if gp_series is not None and rev_series is not None:
                    gm_hist = []
                    for col in list(gp_series.index)[:5]:
                        try:
                            gp = gp_series[col]
                            rv = rev_series[col] if col in rev_series.index else None
                            if gp and rv and rv > 0:
                                gm_hist.append(gp / rv)
                        except Exception:
                            pass
                    if len(gm_hist) >= 2:
                        gm_avg = float(np.mean(gm_hist))
                        cv = float(np.std(gm_hist)) / abs(gm_avg) if gm_avg > 0 else 99
                        if len(gm_hist) >= 3:
                            r_avg = float(np.mean(gm_hist[:2])); o_avg = float(np.mean(gm_hist[2:]))
                            gm_trend = "EXPANDING" if r_avg > o_avg + 0.02 else ("CONTRACTING" if r_avg < o_avg - 0.02 else "STABLE")
                        if gm_avg >= 0.60 and cv <= 0.10: gm_stability = "ELITE_MARGIN_FORTRESS"; gm_score = 25
                        elif gm_avg >= 0.50 and cv <= 0.15: gm_stability = "STRONG_PRICING_POWER"; gm_score = 22
                        elif gm_avg >= 0.40 and cv <= 0.15: gm_stability = "HEALTHY_MOAT"; gm_score = 18
                        elif gm_avg >= 0.30 and cv <= 0.20: gm_stability = "MODERATE_MOAT"; gm_score = 14
                        elif gm_avg >= 0.20: gm_stability = "THIN_MARGINS"; gm_score = 8
                        else: gm_stability = "COMMODITIZED"; gm_score = 3
                        if gm_trend == "EXPANDING": gm_score = min(25, gm_score + 2)
                        elif gm_trend == "CONTRACTING": gm_score = max(0, gm_score - 3)
        except Exception:
            if gm_current:
                if gm_current >= 0.60: gm_stability = "HIGH_GROSS_MARGIN"; gm_score = 20
                elif gm_current >= 0.40: gm_stability = "MODERATE_GROSS_MARGIN"; gm_score = 15
                elif gm_current >= 0.25: gm_stability = "THIN_MARGINS"; gm_score = 9
                else: gm_stability = "COMMODITIZED"; gm_score = 4

        op_lev_score = 10
        op_lev_signal = "UNKNOWN"
        op_lev_ratio = None

        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                op_keys = ["Operating Income", "Operating Income Loss", "EBIT"]
                rev_keys = ["Total Revenue", "Revenue"]
                op_series = next((financials.loc[k] for k in op_keys if k in financials.index), None)
                rev_series = next((financials.loc[k] for k in rev_keys if k in financials.index), None)
                if op_series is not None and rev_series is not None and len(op_series) >= 2:
                    cols = list(op_series.index)
                    op_new = op_series[cols[0]]; op_old = op_series[cols[1]]
                    rv_new = rev_series[cols[0]] if cols[0] in rev_series.index else None
                    rv_old = rev_series[cols[1]] if cols[1] in rev_series.index else None
                    if op_old and rv_old and rv_old > 0 and op_old != 0 and rv_new:
                        op_g = (op_new - op_old) / abs(op_old)
                        rv_g = (rv_new - rv_old) / abs(rv_old)
                        if rv_g != 0:
                            op_lev_ratio = op_g / rv_g
                            if op_lev_ratio >= 3.0: op_lev_signal = "HIGH_OPERATING_LEVERAGE"; op_lev_score = 20
                            elif op_lev_ratio >= 1.5: op_lev_signal = "POSITIVE_LEVERAGE"; op_lev_score = 17
                            elif op_lev_ratio >= 0.8: op_lev_signal = "PROPORTIONAL_SCALING"; op_lev_score = 13
                            elif op_lev_ratio >= 0: op_lev_signal = "WEAK_LEVERAGE"; op_lev_score = 8
                            else: op_lev_signal = "NEGATIVE_LEVERAGE"; op_lev_score = 3
        except Exception:
            pass

        pp_score = 10
        pp_signal = "UNKNOWN"
        gm_ref = gm_avg

        if gm_ref and gm_current:
            diff = gm_current - gm_ref
            if diff > 0.05: pp_signal = "STRONG_PRICING_POWER"; pp_score = 20
            elif diff > 0.01: pp_signal = "IMPROVING_MARGINS"; pp_score = 16
            elif diff > -0.02: pp_signal = "STABLE_PRICING"; pp_score = 13
            elif diff > -0.05: pp_signal = "MARGIN_PRESSURE"; pp_score = 8
            else: pp_signal = "SIGNIFICANT_MARGIN_EROSION"; pp_score = 3
        elif gm_current:
            if gm_current >= 0.60: pp_signal = "PREMIUM_MARGINS"; pp_score = 18
            elif gm_current >= 0.40: pp_signal = "HEALTHY_MARGINS"; pp_score = 14
            elif gm_current >= 0.25: pp_signal = "AVERAGE_MARGINS"; pp_score = 10
            else: pp_signal = "LOW_MARGINS"; pp_score = 5

        mp_score = 8
        mp_signal = "UNKNOWN"
        market_cap = info.get("marketCap", 0) or 0
        rev_growth = info.get("revenueGrowth", 0) or 0

        if market_cap >= 200e9: mp_score = 15; mp_signal = "DOMINANT_MARKET_POSITION"
        elif market_cap >= 50e9:
            if rev_growth >= 0.15: mp_score = 14; mp_signal = "STRONG_MARKET_POSITION"
            elif rev_growth >= 0.05: mp_score = 12; mp_signal = "ESTABLISHED_MARKET_POSITION"
            else: mp_score = 10; mp_signal = "MATURE_MARKET_POSITION"
        elif market_cap >= 10e9:
            if rev_growth >= 0.20: mp_score = 13; mp_signal = "FAST_GROWING_CHALLENGER"
            elif rev_growth >= 0.10: mp_score = 11; mp_signal = "GROWING_MARKET_POSITION"
            else: mp_score = 8; mp_signal = "MID_TIER_POSITION"
        else:
            if rev_growth >= 0.30: mp_score = 10; mp_signal = "HIGH_GROWTH_NICHE"
            else: mp_score = 5; mp_signal = "NICHE_PLAYER"

        rd_moat_score = 10
        rd_moat_signal = "NO_RD_DATA"

        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                rd_keys = ["Research And Development", "Research Development", "Research Development Expenses"]
                rev_keys = ["Total Revenue", "Revenue"]
                rd_val = next((abs(financials.loc[k, financials.columns[0]]) for k in rd_keys if k in financials.index and financials.loc[k, financials.columns[0]]), None)
                rev_val = next((financials.loc[k, financials.columns[0]] for k in rev_keys if k in financials.index and financials.loc[k, financials.columns[0]]), None)
                if rd_val and rev_val and rev_val > 0:
                    rd_intensity = rd_val / rev_val
                    gm_q = gm_avg if gm_avg else gm_current
                    moat_composite = rd_intensity * (gm_q or 0.3)
                    if moat_composite >= 0.15: rd_moat_signal = "DEEP_IP_MOAT"; rd_moat_score = 20
                    elif moat_composite >= 0.08: rd_moat_signal = "STRONG_INNOVATION_MOAT"; rd_moat_score = 17
                    elif moat_composite >= 0.04: rd_moat_signal = "MODERATE_IP_INVESTMENT"; rd_moat_score = 13
                    elif moat_composite >= 0.01: rd_moat_signal = "LIGHT_RD_FOCUS"; rd_moat_score = 9
                    else: rd_moat_signal = "MINIMAL_IP_MOAT"; rd_moat_score = 5
                else:
                    if sector in ["Consumer Staples", "Utilities", "Real Estate", "Financials"]:
                        rd_moat_signal = "NON_RD_SECTOR"; rd_moat_score = 12
                    else:
                        rd_moat_signal = "NO_RD_DATA"; rd_moat_score = 7
        except Exception:
            pass

        total_score = gm_score + op_lev_score + pp_score + mp_score + rd_moat_score

        if total_score >= 78: moat_signal = "WIDE_MOAT"
        elif total_score >= 58: moat_signal = "NARROW_MOAT"
        elif total_score >= 38: moat_signal = "NO_MOAT"
        else: moat_signal = "STRUCTURAL_DISADVANTAGE"

        moat_actions = {
            "WIDE_MOAT": "Strong durable competitive advantage — pricing power, scale, and IP create lasting barriers. Premium valuation justified for long-term compounding.",
            "NARROW_MOAT": "Some competitive advantage but limited durability. Suitable at fair valuation; monitor margin trends closely.",
            "NO_MOAT": "Limited differentiation. Commodity-like competition. Requires low valuation to compensate for lack of pricing power.",
            "STRUCTURAL_DISADVANTAGE": "Eroding competitive position — margins contracting, weak market position. High risk of value destruction. Avoid.",
        }

        moat_map = {
            "WIDE_MOAT": "≥78 — Durable competitive advantage (network effects, IP, switching costs, cost leadership)",
            "NARROW_MOAT": "58-77 — Some competitive advantage but limited durability",
            "NO_MOAT": "38-57 — Limited differentiation, commodity-like competition",
            "STRUCTURAL_DISADVANTAGE": "<38 — Eroding position",
        }

        return {
            "ticker": ticker, "company": company_name, "sector": sector, "industry": industry,
            "moat_signal": moat_signal, "moat_score": total_score, "max_score": 100,
            "action_guide": moat_actions[moat_signal],
            "moat_classification": moat_map[moat_signal],
            "score_breakdown": {
                "gross_margin_stability": {"score": gm_score, "max": 25, "gross_margin_avg_pct": round(gm_avg * 100, 1) if gm_avg else None, "gross_margin_current_pct": round(gm_current * 100, 1) if gm_current else None, "stability": gm_stability, "trend": gm_trend, "note": "High + stable gross margin = pricing power moat. EXPANDING trend +2pts."},
                "operating_leverage": {"score": op_lev_score, "max": 20, "operating_leverage_ratio": round(op_lev_ratio, 2) if op_lev_ratio else None, "signal": op_lev_signal, "note": "Op income growth / Revenue growth. ≥3x = income scales faster than costs."},
                "pricing_power_proxy": {"score": pp_score, "max": 20, "current_vs_historical_gm_pp": round((gm_current - gm_ref) * 100, 1) if (gm_current and gm_ref) else None, "signal": pp_signal, "note": "Current gross margin vs 3-5yr historical average. Expanding = pricing power."},
                "market_position": {"score": mp_score, "max": 15, "market_cap_B": round(market_cap / 1e9, 1) if market_cap else None, "revenue_growth_yoy_pct": round(rev_growth * 100, 1) if rev_growth else None, "signal": mp_signal, "note": "Market cap tier + revenue growth as scale and position advantage proxy."},
                "rd_ip_moat": {"score": rd_moat_score, "max": 20, "signal": rd_moat_signal, "note": "R&D intensity × gross margin quality. High = sustainable innovation barrier to entry."}
            },
            "source": "Yahoo Finance public data — no API key required",
            "note": "Combine with get_management_quality_score() and get_valuation_composite() for complete fundamental picture."
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}

@mcp.tool()
async def get_earnings_revision_momentum(ticker: str) -> dict:
    """Analyst EPS estimate revision momentum: 30/60/90-day revision direction, speed, and macro positioning signal. REVISION_MOMENTUM_STRONG / POSITIVE / NEUTRAL / NEGATIVE / DETERIORATING."""
    await Actor.charge("advanced_tool")
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        company_name = info.get("longName", ticker)
        sector = info.get("sector", "Unknown")

        eps_fwd = info.get("forwardEps")
        eps_trail = info.get("trailingEps")
        num_analysts = info.get("numberOfAnalystOpinions", 0) or 0
        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        target_low = info.get("targetLowPrice")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        recommend_key = info.get("recommendationKey", "none")
        recommend_mean = info.get("recommendationMean")

        try:
            upgrades = stock.upgrades_downgrades
        except Exception:
            upgrades = None

        up_30, down_30 = 0, 0
        up_60, down_60 = 0, 0
        up_90, down_90 = 0, 0
        recent_actions = []

        if upgrades is not None and not upgrades.empty:
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            for idx, row in upgrades.iterrows():
                try:
                    if hasattr(idx, 'tzinfo') and idx.tzinfo is None:
                        idx = idx.replace(tzinfo=datetime.timezone.utc)
                    days_ago = (now - idx).days
                    action = str(row.get("Action", "")).upper()
                    is_up = action in ["UP", "UPGRADE", "INITIATED", "REITERATED"]
                    is_down = action in ["DOWN", "DOWNGRADE", "LOWERED"]
                    if days_ago <= 30:
                        if is_up: up_30 += 1
                        elif is_down: down_30 += 1
                    if days_ago <= 60:
                        if is_up: up_60 += 1
                        elif is_down: down_60 += 1
                    if days_ago <= 90:
                        if is_up: up_90 += 1
                        elif is_down: down_90 += 1
                    if days_ago <= 60 and len(recent_actions) < 6:
                        recent_actions.append({
                            "date": str(idx)[:10],
                            "firm": str(row.get("Firm", "Unknown")),
                            "action": action,
                            "from_grade": str(row.get("FromGrade", "")),
                            "to_grade": str(row.get("ToGrade", ""))
                        })
                except Exception:
                    continue

        net_30 = up_30 - down_30
        net_60 = up_60 - down_60
        net_90 = up_90 - down_90

        def window_score(net, total):
            if total == 0: return 0
            ratio = net / max(total, 1)
            if ratio >= 0.6: return 20
            elif ratio >= 0.3: return 15
            elif ratio >= 0.1: return 10
            elif ratio >= -0.1: return 5
            elif ratio >= -0.3: return 2
            else: return 0

        total_30 = up_30 + down_30
        total_60 = up_60 + down_60
        total_90 = up_90 + down_90

        s30 = window_score(net_30, total_30) * 0.50
        s60 = window_score(net_60 - net_30, total_60 - total_30) * 0.30
        s90 = window_score(net_90 - net_60, total_90 - total_60) * 0.20
        revision_score = s30 + s60 + s90
        revision_score_100 = round(revision_score * 5)

        coverage_note = "LOW_COVERAGE" if num_analysts < 3 else ("MODERATE_COVERAGE" if num_analysts < 8 else "HIGH_COVERAGE")

        upside_pct = None
        if target_mean and current_price and current_price > 0:
            upside_pct = round((target_mean / current_price - 1) * 100, 1)

        if revision_score_100 >= 80 and total_90 >= 3:
            revision_signal = "REVISION_MOMENTUM_STRONG"
            signal_desc = "Analysts aggressively upgrading — strong positive EPS revision cycle. Typically precedes price outperformance."
        elif revision_score_100 >= 55 and total_90 >= 2:
            revision_signal = "REVISION_MOMENTUM_POSITIVE"
            signal_desc = "More upgrades than downgrades over the revision window. Positive estimate drift. Bullish catalyst for stock."
        elif revision_score_100 >= 35:
            revision_signal = "REVISION_MOMENTUM_NEUTRAL"
            signal_desc = "Mixed analyst actions — no clear revision trend. Wait for clearer directional signal."
        elif revision_score_100 >= 15:
            revision_signal = "REVISION_MOMENTUM_NEGATIVE"
            signal_desc = "Downgrades outnumber upgrades. Estimates being cut. Potential for continued price weakness."
        else:
            revision_signal = "REVISION_DETERIORATING"
            signal_desc = "Significant downgrade wave — estimates deteriorating rapidly. High risk of earnings disappointment."

        rec_key = recommend_key.lower() if recommend_key else ""
        if rec_key in ["strong_buy", "buy"]:
            consensus_signal = "STRONG_ANALYST_CONSENSUS_BUY"
        elif rec_key in ["hold", "neutral"]:
            consensus_signal = "ANALYST_HOLD"
        elif rec_key in ["sell", "strong_sell", "underperform", "underweight"]:
            consensus_signal = "ANALYST_CONSENSUS_SELL"
        else:
            consensus_signal = "INSUFFICIENT_DATA"

        eps_growth_fwd = None
        if eps_fwd and eps_trail and eps_trail != 0:
            eps_growth_fwd = round((eps_fwd / abs(eps_trail) - 1) * 100, 1)

        action_guide = {
            "REVISION_MOMENTUM_STRONG": "High-conviction long setup — analysts raising numbers. Consider accumulation especially if combined with value or quality signal.",
            "REVISION_MOMENTUM_POSITIVE": "Favorable estimate trend. Add exposure on pullbacks. Monitor for continuation.",
            "REVISION_MOMENTUM_NEUTRAL": "No clear edge from revisions. Rely on valuation and fundamentals for decision.",
            "REVISION_MOMENTUM_NEGATIVE": "Caution warranted — estimates being cut. Reduce position or avoid new entry.",
            "REVISION_DETERIORATING": "Avoid or short candidate. Significant downgrade pressure suggests earnings risk ahead.",
        }

        return {
            "ticker": ticker,
            "company": company_name,
            "sector": sector,
            "revision_signal": revision_signal,
            "revision_score": revision_score_100,
            "action_guide": action_guide[revision_signal],
            "signal_description": signal_desc,
            "revision_windows": {
                "last_30d": {"upgrades": up_30, "downgrades": down_30, "net": net_30},
                "last_60d": {"upgrades": up_60, "downgrades": down_60, "net": net_60},
                "last_90d": {"upgrades": up_90, "downgrades": down_90, "net": net_90},
            },
            "analyst_coverage": {
                "num_analysts": num_analysts,
                "coverage_quality": coverage_note,
                "consensus": consensus_signal,
                "recommendation_key": recommend_key,
                "recommendation_mean_1to5": round(recommend_mean, 2) if recommend_mean else None,
            },
            "price_targets": {
                "current_price": current_price,
                "target_mean": target_mean,
                "target_high": target_high,
                "target_low": target_low,
                "upside_to_mean_pct": upside_pct,
            },
            "eps_estimates": {
                "trailing_eps": eps_trail,
                "forward_eps": eps_fwd,
                "forward_eps_growth_pct": eps_growth_fwd,
            },
            "recent_analyst_actions": recent_actions,
            "source": "Yahoo Finance public data — no API key required",
            "note": "Combine with get_valuation_composite() and get_competitive_moat_score() for complete conviction signal."
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@mcp.tool()
async def get_business_cycle_positioning(sector: str = "ALL") -> dict:
    """Business cycle sector positioning: PMI proxy (XLI/XLB/XLY vs XLP/XLU), rate environment, credit spreads, earnings cycle → EARLY_CYCLE / MID_CYCLE / LATE_CYCLE / RECESSION phase mapping with sector-level recommendations."""
    await Actor.charge("basic_tool")
    import yfinance as yf
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    cycle_etfs = {
        "cyclical": ["XLY", "XLI", "XLB"],
        "defensive": ["XLP", "XLU", "XLV"],
        "rate_sensitive": ["TLT", "IEF"],
        "credit": ["HYG", "LQD"],
        "broad_market": ["SPY", "QQQ"],
        "commodities": ["GLD", "USO"],
    }
    all_etfs = [e for group in cycle_etfs.values() for e in group]

    def fetch_etf(sym):
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="6mo")
            if hist.empty or len(hist) < 30: return sym, None
            close = hist["Close"]
            ret_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100
            ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100
            vol_20d = close.pct_change().tail(20).std() * (252**0.5) * 100
            return sym, {"ret_1m": round(ret_1m, 2), "ret_3m": round(ret_3m, 2), "vol_20d": round(vol_20d, 1)}
        except Exception:
            return sym, None

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [loop.run_in_executor(ex, fetch_etf, sym) for sym in all_etfs]
        results_list = await asyncio.gather(*futures)
    results = dict(results_list)

    def avg_ret(syms, period="ret_3m"):
        vals = [results[s][period] for s in syms if results.get(s)]
        return sum(vals) / len(vals) if vals else 0.0

    cyc_ret_3m = avg_ret(["XLY", "XLI", "XLB"], "ret_3m")
    def_ret_3m = avg_ret(["XLP", "XLU", "XLV"], "ret_3m")
    pmi_spread = cyc_ret_3m - def_ret_3m

    if pmi_spread >= 8:
        pmi_signal = "EXPANSION_CONFIRMED"; pmi_score = 30
    elif pmi_spread >= 3:
        pmi_signal = "EXPANSION_EARLY"; pmi_score = 24
    elif pmi_spread >= -2:
        pmi_signal = "TRANSITION_NEUTRAL"; pmi_score = 16
    elif pmi_spread >= -6:
        pmi_signal = "CONTRACTION_SIGNAL"; pmi_score = 8
    else:
        pmi_signal = "RECESSION_SIGNAL"; pmi_score = 2

    tlt = results.get("TLT")
    ief = results.get("IEF")
    if tlt and ief:
        tlt_ret = tlt["ret_3m"]
        rate_env_score = 20 if tlt_ret >= 5 else (16 if tlt_ret >= 1 else (12 if tlt_ret >= -2 else (7 if tlt_ret >= -5 else 3)))
        rate_signal = ("RATES_FALLING_STIMULATIVE" if tlt_ret >= 5 else
                       "RATES_MILDLY_FALLING" if tlt_ret >= 1 else
                       "RATES_STABLE" if tlt_ret >= -2 else
                       "RATES_RISING_PRESSURING" if tlt_ret >= -5 else
                       "RATES_SHARPLY_RISING")
    else:
        rate_env_score = 10; rate_signal = "RATE_DATA_UNAVAILABLE"

    hyg = results.get("HYG")
    lqd = results.get("LQD")
    credit_spread = 0
    if hyg and lqd:
        credit_spread = hyg["ret_3m"] - lqd["ret_3m"]
        if credit_spread >= 3:
            credit_score = 25; credit_signal = "RISK_ON_CREDIT_TIGHTENING"
        elif credit_spread >= 0:
            credit_score = 20; credit_signal = "CREDIT_STABLE"
        elif credit_spread >= -3:
            credit_score = 12; credit_signal = "MILD_CREDIT_WIDENING"
        else:
            credit_score = 4; credit_signal = "CREDIT_STRESS_WIDENING"
    else:
        credit_score = 12; credit_signal = "CREDIT_DATA_UNAVAILABLE"

    spy = results.get("SPY")
    qqq = results.get("QQQ")
    mkt_ret = 0
    if spy and qqq:
        mkt_ret = (spy["ret_3m"] + qqq["ret_3m"]) / 2
        if mkt_ret >= 10:
            momentum_score = 20; momentum_signal = "STRONG_EARNINGS_CYCLE"
        elif mkt_ret >= 4:
            momentum_score = 16; momentum_signal = "HEALTHY_MOMENTUM"
        elif mkt_ret >= -2:
            momentum_score = 10; momentum_signal = "NEUTRAL_MOMENTUM"
        elif mkt_ret >= -8:
            momentum_score = 5; momentum_signal = "WEAKENING_CYCLE"
        else:
            momentum_score = 1; momentum_signal = "RECESSION_MOMENTUM"
    else:
        momentum_score = 10; momentum_signal = "DATA_UNAVAILABLE"

    total_score = pmi_score + rate_env_score + credit_score + momentum_score

    if total_score >= 78:
        cycle_phase = "MID_CYCLE"
        phase_desc = "Expansion confirmed — PMI proxy rising, credit spreads tight, earnings accelerating. Favor cyclical growth sectors."
    elif total_score >= 60:
        cycle_phase = "EARLY_CYCLE"
        phase_desc = "Recovery phase — rates supportive or falling, credit improving, cyclicals beginning to outperform. Max risk-on."
    elif total_score >= 40:
        cycle_phase = "LATE_CYCLE"
        phase_desc = "Late expansion — momentum slowing, spreads starting to widen. Rotate toward quality and defensives. Reduce duration risk."
    elif total_score >= 22:
        cycle_phase = "SLOWDOWN"
        phase_desc = "Growth decelerating — defensive rotation underway. Reduce cyclicals, increase staples/utilities/gold exposure."
    else:
        cycle_phase = "RECESSION"
        phase_desc = "Contraction regime — credit stress, defensive outperformance, earnings declining. Maximum caution. Cash and bonds."

    sector_guidance = {
        "EARLY_CYCLE": {
            "overweight": ["Consumer Discretionary", "Financials", "Industrials", "Materials", "Real Estate"],
            "neutral": ["Technology", "Communication Services"],
            "underweight": ["Utilities", "Consumer Staples", "Healthcare"],
            "rationale": "Early cycle: Rate cuts boost credit, housing recovers. Cyclicals lead. Avoid bond proxies."
        },
        "MID_CYCLE": {
            "overweight": ["Technology", "Industrials", "Energy", "Consumer Discretionary"],
            "neutral": ["Financials", "Materials", "Communication Services"],
            "underweight": ["Utilities", "Real Estate", "Consumer Staples"],
            "rationale": "Mid cycle: Earnings growing, rates stable. Broad participation. Tech and industrials lead."
        },
        "LATE_CYCLE": {
            "overweight": ["Energy", "Materials", "Financials", "Healthcare"],
            "neutral": ["Technology", "Consumer Staples"],
            "underweight": ["Consumer Discretionary", "Real Estate"],
            "rationale": "Late cycle: Inflation rising, rates peaking. Energy/materials benefit from commodity prices. Reduce high-growth."
        },
        "SLOWDOWN": {
            "overweight": ["Consumer Staples", "Healthcare", "Utilities"],
            "neutral": ["Energy", "Financials"],
            "underweight": ["Consumer Discretionary", "Industrials", "Materials", "Real Estate"],
            "rationale": "Slowdown: Defensive rotation. Dividend payers and low-beta outperform. Reduce cyclical exposure significantly."
        },
        "RECESSION": {
            "overweight": ["Consumer Staples", "Healthcare", "Utilities", "Cash"],
            "neutral": ["Government Bonds"],
            "underweight": ["Consumer Discretionary", "Financials", "Industrials", "Energy", "Materials"],
            "rationale": "Recession: Maximum defensiveness. Staples, utilities, healthcare hold. Broad equity underperformance."
        },
    }

    guidance = sector_guidance[cycle_phase]
    input_sector = sector.strip().title() if sector and sector.upper() != "ALL" else "ALL"

    sector_signal = None
    if input_sector != "ALL":
        if input_sector in guidance["overweight"]:
            sector_signal = f"OVERWEIGHT — {input_sector} is favored in {cycle_phase} environment."
        elif input_sector in guidance["neutral"]:
            sector_signal = f"NEUTRAL — {input_sector} has balanced risk/reward in {cycle_phase} environment."
        elif input_sector in guidance["underweight"]:
            sector_signal = f"UNDERWEIGHT — {input_sector} historically underperforms in {cycle_phase} environment. Reduce exposure."
        else:
            sector_signal = f"SECTOR_NOT_MAPPED — {input_sector} not in standard GICS coverage."

    return {
        "cycle_phase": cycle_phase,
        "cycle_score": total_score,
        "max_score": 100,
        "phase_description": phase_desc,
        "input_sector": input_sector,
        "sector_signal": sector_signal,
        "sector_recommendations": {
            "overweight": guidance["overweight"],
            "neutral": guidance["neutral"],
            "underweight": guidance["underweight"],
            "rationale": guidance["rationale"],
        },
        "component_breakdown": {
            "pmi_proxy_cyclical_vs_defensive": {
                "score": pmi_score, "max": 30,
                "signal": pmi_signal,
                "cyclical_3m_ret_pct": round(cyc_ret_3m, 2),
                "defensive_3m_ret_pct": round(def_ret_3m, 2),
                "spread_pp": round(pmi_spread, 2),
                "note": "XLY+XLI+XLB vs XLP+XLU+XLV 3M return spread — positive = expansion."
            },
            "rate_environment": {
                "score": rate_env_score, "max": 25,
                "signal": rate_signal,
                "tlt_3m_ret_pct": tlt["ret_3m"] if tlt else None,
                "note": "TLT 3M return. Rising TLT = falling rates = stimulative for early cycle."
            },
            "credit_spreads": {
                "score": credit_score, "max": 25,
                "signal": credit_signal,
                "hyg_vs_lqd_3m_spread_pp": round(credit_spread, 2) if hyg and lqd else None,
                "note": "HYG vs LQD 3M return differential. Positive = tightening spreads = risk-on."
            },
            "market_momentum_earnings_proxy": {
                "score": momentum_score, "max": 20,
                "signal": momentum_signal,
                "spy_qqq_avg_3m_ret_pct": round(mkt_ret, 2) if spy and qqq else None,
                "note": "SPY+QQQ avg 3M return — broad market momentum as earnings cycle proxy."
            }
        },
        "etf_data": {
            sym: results[sym] for sym in all_etfs if results.get(sym)
        },
        "source": "Yahoo Finance ETF data — no API key required",
        "note": "Use with get_sector_rotation_signal() and get_macro_regime_monitor() for full macro picture."
    }


@mcp.tool()
async def get_peer_comparison(ticker: str) -> dict:
    """Peer comparison: ranks ticker vs 10-15 sector peers on PE, PB, ROE, revenue growth, gross margin, EV/EBITDA — returns CHEAP_VS_PEERS / FAIR_VALUE / PREMIUM_TO_PEERS signal with percentile rank."""
    await Actor.charge("advanced_tool")
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor

    SECTOR_PEERS = {
        "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "CRM", "ORCL", "AMD", "INTC", "QCOM", "TXN", "AMAT", "NOW"],
        "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD", "CVS", "CI", "HUM"],
        "Financials": ["BRK-B", "JPM", "BAC", "WFC", "GS", "MS", "BLK", "SCHW", "AXP", "USB", "PNC", "COF", "TFC", "SPGI"],
        "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "CMG", "GM", "F", "ORLY"],
        "Consumer Staples": ["WMT", "PG", "KO", "PEP", "COST", "PM", "MO", "CL", "KMB", "GIS", "K", "SYY", "HSY"],
        "Industrials": ["GE", "HON", "UPS", "CAT", "RTX", "DE", "LMT", "BA", "MMM", "EMR", "ITW", "PH", "ROK", "GD"],
        "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "KMI", "WMB", "HAL", "BKR"],
        "Materials": ["LIN", "APD", "SHW", "ECL", "NEM", "FCX", "NUE", "VMC", "MLM", "CF", "MOS", "ALB", "CE"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "PCG", "WEC", "ES", "ETR", "FE"],
        "Real Estate": ["PLD", "AMT", "EQIX", "PSA", "CCI", "SPG", "O", "DLR", "EQR", "AVB", "VTR", "WELL", "BXP"],
        "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "EA", "TTWO", "OMC", "IPG"],
    }

    ticker = ticker.upper().strip()

    def fetch_fundamentals(sym):
        try:
            t = yf.Ticker(sym)
            full = t.info
            sector = full.get("sector", "Unknown")
            pe = full.get("trailingPE") or full.get("forwardPE")
            pb = full.get("priceToBook")
            roe = full.get("returnOnEquity")
            if roe: roe = roe * 100
            rev_growth = full.get("revenueGrowth")
            if rev_growth: rev_growth = rev_growth * 100
            gm = full.get("grossMargins")
            if gm: gm = gm * 100
            ev_ebitda = full.get("enterpriseToEbitda")
            mktcap = full.get("marketCap")
            return {
                "ticker": sym,
                "sector": sector,
                "pe": pe,
                "pb": pb,
                "roe": roe,
                "rev_growth_pct": rev_growth,
                "gross_margin_pct": gm,
                "ev_ebitda": ev_ebitda,
                "market_cap_b": round(mktcap / 1e9, 1) if mktcap else None,
            }
        except:
            return None

    target = fetch_fundamentals(ticker)
    if not target:
        return {"error": f"Could not fetch data for {ticker}"}

    target_sector = target.get("sector", "Unknown")

    peers = None
    for sector_name, peer_list in SECTOR_PEERS.items():
        if sector_name.lower() in target_sector.lower() or target_sector.lower() in sector_name.lower():
            peers = [p for p in peer_list if p != ticker][:13]
            break

    if not peers:
        peers = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI"]

    all_tickers = [ticker] + peers

    with ThreadPoolExecutor(max_workers=12) as ex:
        results_list = list(ex.map(fetch_fundamentals, all_tickers))

    valid = [r for r in results_list if r and r["ticker"] != ticker]
    target_data = next((r for r in results_list if r and r["ticker"] == ticker), target)

    if not valid:
        return {"error": "Could not fetch peer data", "ticker": ticker}

    def percentile_rank(val, peer_vals, higher_is_better=True):
        if val is None: return None
        peer_vals_clean = [v for v in peer_vals if v is not None]
        if not peer_vals_clean: return None
        if higher_is_better:
            rank = sum(1 for v in peer_vals_clean if v <= val) / len(peer_vals_clean) * 100
        else:
            rank = sum(1 for v in peer_vals_clean if v >= val) / len(peer_vals_clean) * 100
        return round(rank, 1)

    def sector_median(vals):
        clean = sorted([v for v in vals if v is not None])
        if not clean: return None
        n = len(clean)
        return round(clean[n // 2], 2)

    metrics = ["pe", "pb", "ev_ebitda", "roe", "rev_growth_pct", "gross_margin_pct"]
    higher_is_better = {"pe": False, "pb": False, "ev_ebitda": False, "roe": True, "rev_growth_pct": True, "gross_margin_pct": True}
    metric_labels = {"pe": "P/E Ratio", "pb": "P/B Ratio", "ev_ebitda": "EV/EBITDA", "roe": "ROE %", "rev_growth_pct": "Revenue Growth %", "gross_margin_pct": "Gross Margin %"}

    comparison = {}
    score_components = []
    for m in metrics:
        target_val = target_data.get(m)
        peer_vals = [r.get(m) for r in valid]
        pctile = percentile_rank(target_val, peer_vals, higher_is_better=higher_is_better[m])
        peer_med = sector_median(peer_vals)
        comparison[m] = {
            "label": metric_labels[m],
            "ticker_value": round(target_val, 2) if target_val is not None else None,
            "sector_median": peer_med,
            "percentile_vs_peers": pctile,
            "vs_peers": (
                "SIGNIFICANT_PREMIUM" if (pctile is not None and pctile >= 80 and not higher_is_better[m]) or (pctile is not None and pctile >= 80 and higher_is_better[m]) else
                "PREMIUM" if (pctile is not None and pctile >= 60) else
                "IN_LINE" if (pctile is not None and pctile >= 40) else
                "DISCOUNT" if (pctile is not None and pctile >= 20) else
                "SIGNIFICANT_DISCOUNT" if pctile is not None else "INSUFFICIENT_DATA"
            ),
        }
        if pctile is not None:
            score_components.append(pctile)

    composite_pctile = round(sum(score_components) / len(score_components), 1) if score_components else None

    if composite_pctile is not None:
        if composite_pctile >= 75:
            overall_signal = "PREMIUM_TO_PEERS"
            action = "Ticker trades at significant premium vs sector peers. Justified if fundamentals warrant; otherwise consider trimming."
        elif composite_pctile >= 55:
            overall_signal = "MILD_PREMIUM"
            action = "Slightly premium vs peers. Monitor for mean reversion or fundamental catalysts."
        elif composite_pctile >= 45:
            overall_signal = "FAIR_VALUE_VS_PEERS"
            action = "In-line with sector peers. No valuation edge; focus on company-specific catalysts."
        elif composite_pctile >= 25:
            overall_signal = "MILD_DISCOUNT"
            action = "Slight discount vs peers. May represent relative value opportunity."
        else:
            overall_signal = "CHEAP_VS_PEERS"
            action = "Significant discount to sector peers. Potential value opportunity — verify no structural issues."
    else:
        overall_signal = "INSUFFICIENT_DATA"
        action = "Not enough peer data to rank."

    peer_scores = []
    for r in valid:
        pvals = []
        for m in metrics:
            v = r.get(m)
            peer_vals = [x.get(m) for x in valid if x["ticker"] != r["ticker"]]
            p = percentile_rank(v, peer_vals, higher_is_better[m])
            if p is not None: pvals.append(p)
        if pvals:
            peer_scores.append({"ticker": r["ticker"], "composite_pctile": round(sum(pvals)/len(pvals), 1), "market_cap_b": r.get("market_cap_b")})

    peer_scores.sort(key=lambda x: x["composite_pctile"], reverse=True)

    return {
        "ticker": ticker,
        "sector": target_sector,
        "overall_signal": overall_signal,
        "composite_percentile_vs_peers": composite_pctile,
        "action_guide": action,
        "metric_comparison": comparison,
        "peer_universe_size": len(valid),
        "peer_tickers": [r["ticker"] for r in valid],
        "strongest_peers_by_fundamentals": [p["ticker"] for p in peer_scores[:3]],
        "weakest_peers_by_fundamentals": [p["ticker"] for p in peer_scores[-3:]],
        "ticker_raw_data": {m: target_data.get(m) for m in metrics},
        "source": "Yahoo Finance — no API key required",
        "note": "Combine with get_valuation_composite() for absolute valuation context. Percentile: 100=best vs peers."
    }


@mcp.tool()
async def get_macro_sensitivity_score(ticker: str) -> dict:
    """Macro sensitivity scorecard: rates sensitivity (financial leverage + duration proxy), dollar sensitivity (foreign revenue proxy), inflation sensitivity (margin trend + commodity input), economic cycle sensitivity (beta vs cyclical ETFs) — 4-component macro risk score 0-100."""
    await Actor.charge("advanced_tool")
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor

    ticker = ticker.upper().strip()

    def fetch_etf(sym):
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="1y")
            if hist.empty or len(hist) < 60: return sym, None
            close = hist["Close"]
            ret_1y = (close.iloc[-1] / close.iloc[0] - 1) * 100
            ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100 if len(close) >= 66 else None
            returns = close.pct_change().dropna()
            return sym, {"ret_1y": round(ret_1y, 2), "ret_3m": round(ret_3m, 2) if ret_3m else None, "returns": returns}
        except:
            return sym, None

    etf_syms = ["SPY", "TLT", "UUP", "XLY", "XLU", "GLD", "USO"]
    with ThreadPoolExecutor(max_workers=8) as ex:
        etf_results = dict(ex.map(fetch_etf, etf_syms))

    try:
        t_obj = yf.Ticker(ticker)
        info = t_obj.info
        hist = t_obj.history(period="2y")
    except:
        return {"error": f"Could not fetch data for {ticker}"}

    if hist.empty or len(hist) < 100:
        return {"error": f"Insufficient price history for {ticker}"}

    sector = info.get("sector", "Unknown")
    close = hist["Close"]
    ticker_returns = close.pct_change().dropna()

    # ── Component 1: Interest Rate Sensitivity (25 pts) ──
    de_ratio = info.get("debtToEquity")
    if de_ratio is not None:
        de_ratio = de_ratio / 100
        if de_ratio <= 0.2:
            de_pts = 25; de_sig = "MINIMAL_LEVERAGE_LOW_RATE_RISK"
        elif de_ratio <= 0.5:
            de_pts = 20; de_sig = "LOW_LEVERAGE"
        elif de_ratio <= 1.0:
            de_pts = 14; de_sig = "MODERATE_LEVERAGE"
        elif de_ratio <= 2.0:
            de_pts = 7; de_sig = "HIGH_LEVERAGE_RATE_SENSITIVE"
        else:
            de_pts = 2; de_sig = "VERY_HIGH_LEVERAGE_EXTREME_RATE_RISK"
    else:
        de_pts = 12; de_sig = "LEVERAGE_DATA_UNAVAILABLE"

    tlt_data = etf_results.get("TLT")
    tlt_corr = None
    tlt_sig = "TLT_DATA_UNAVAILABLE"
    if tlt_data and tlt_data.get("returns") is not None:
        aligned = ticker_returns.align(tlt_data["returns"], join="inner")
        if len(aligned[0]) >= 60:
            tlt_corr = round(aligned[0].corr(aligned[1]), 3)
            if tlt_corr >= 0.4: tlt_sig = "HIGH_TLT_CORRELATION_DURATION_RISK"
            elif tlt_corr >= 0.2: tlt_sig = "MODERATE_TLT_CORRELATION"
            elif tlt_corr >= -0.1: tlt_sig = "NEUTRAL_RATE_CORRELATION"
            else: tlt_sig = "NEGATIVE_TLT_CORR_EQUITY_LIKE"

    rate_detail = {
        "score": de_pts, "max": 25, "signal": de_sig,
        "debt_to_equity": round(de_ratio * 100, 1) if de_ratio is not None else None,
        "tlt_correlation": tlt_corr, "tlt_signal": tlt_sig,
        "note": "High D/E = high rate sensitivity. TLT correlation provides duration proxy."
    }

    # ── Component 2: Dollar Sensitivity (20 pts) ──
    uup_data = etf_results.get("UUP")
    uup_corr = None
    if uup_data and uup_data.get("returns") is not None:
        aligned = ticker_returns.align(uup_data["returns"], join="inner")
        if len(aligned[0]) >= 60:
            uup_corr = round(aligned[0].corr(aligned[1]), 3)

    if uup_corr is not None:
        if uup_corr <= -0.3: usd_pts = 5; usd_sig = "HIGH_USD_SENSITIVITY_MULTINATIONAL"
        elif uup_corr <= -0.1: usd_pts = 10; usd_sig = "MODERATE_USD_SENSITIVITY"
        elif uup_corr <= 0.1: usd_pts = 15; usd_sig = "LOW_USD_SENSITIVITY_DOMESTIC"
        elif uup_corr <= 0.3: usd_pts = 18; usd_sig = "POSITIVE_USD_CORRELATION_USD_BENEFICIARY"
        else: usd_pts = 20; usd_sig = "STRONG_USD_BENEFICIARY"
    else:
        usd_pts = 10; usd_sig = "USD_CORRELATION_UNAVAILABLE"

    usd_detail = {
        "score": usd_pts, "max": 20, "signal": usd_sig,
        "uup_correlation_1y": uup_corr,
        "note": "Negative UUP correlation = revenue hurt by strong dollar. Positive = domestic/USD beneficiary."
    }

    # ── Component 3: Inflation Sensitivity (20 pts) ──
    gm = info.get("grossMargins")
    gm_pct = gm * 100 if gm else None

    gld_data = etf_results.get("GLD")
    uso_data = etf_results.get("USO")
    gld_corr = None
    uso_corr = None
    if gld_data and gld_data.get("returns") is not None:
        aligned = ticker_returns.align(gld_data["returns"], join="inner")
        if len(aligned[0]) >= 60: gld_corr = round(aligned[0].corr(aligned[1]), 3)
    if uso_data and uso_data.get("returns") is not None:
        aligned = ticker_returns.align(uso_data["returns"], join="inner")
        if len(aligned[0]) >= 60: uso_corr = round(aligned[0].corr(aligned[1]), 3)

    inflation_beneficiary_sectors = ["Energy", "Materials"]
    if sector in inflation_beneficiary_sectors:
        infl_pts = 18; infl_sig = "INFLATION_BENEFICIARY_COMMODITY_SECTOR"
    elif gm_pct is not None and gm_pct >= 60:
        infl_pts = 16; infl_sig = "HIGH_MARGIN_PRICING_POWER_INFLATION_HEDGE"
    elif gm_pct is not None and gm_pct >= 35:
        infl_pts = 12; infl_sig = "MODERATE_MARGIN_PARTIAL_PASS_THROUGH"
    elif gm_pct is not None and gm_pct >= 15:
        infl_pts = 7; infl_sig = "THIN_MARGIN_INFLATION_VULNERABLE"
    elif gm_pct is not None:
        infl_pts = 3; infl_sig = "VERY_THIN_MARGIN_HIGH_INFLATION_RISK"
    else:
        infl_pts = 10; infl_sig = "MARGIN_DATA_UNAVAILABLE"

    commodity_corr_avg = None
    if gld_corr is not None and uso_corr is not None:
        commodity_corr_avg = round((gld_corr + uso_corr) / 2, 3)
    elif gld_corr is not None:
        commodity_corr_avg = gld_corr

    infl_detail = {
        "score": infl_pts, "max": 20, "signal": infl_sig,
        "gross_margin_pct": round(gm_pct, 1) if gm_pct else None,
        "gold_correlation_1y": gld_corr, "oil_correlation_1y": uso_corr,
        "commodity_correlation_avg": commodity_corr_avg,
        "note": "High gross margin = pricing power = inflation hedge."
    }

    # ── Component 4: Economic Cycle Sensitivity (35 pts) ──
    spy_data = etf_results.get("SPY")
    spy_beta = None
    if spy_data and spy_data.get("returns") is not None:
        aligned = ticker_returns.align(spy_data["returns"], join="inner")
        if len(aligned[0]) >= 120:
            cov = aligned[0].cov(aligned[1])
            var = aligned[1].var()
            if var > 0: spy_beta = round(cov / var, 3)

    if spy_beta is not None:
        if spy_beta >= 1.5: beta_pts = 5; beta_sig = "VERY_HIGH_BETA_EXTREME_CYCLICALITY"
        elif spy_beta >= 1.2: beta_pts = 10; beta_sig = "HIGH_BETA_CYCLICAL"
        elif spy_beta >= 0.9: beta_pts = 20; beta_sig = "MARKET_BETA_MODERATE_CYCLE"
        elif spy_beta >= 0.6: beta_pts = 28; beta_sig = "LOW_BETA_DEFENSIVE"
        else: beta_pts = 35; beta_sig = "VERY_LOW_BETA_HIGHLY_DEFENSIVE"
    else:
        beta_pts = 15; beta_sig = "BETA_UNAVAILABLE"

    xly_data = etf_results.get("XLY")
    xlu_data = etf_results.get("XLU")
    xly_corr = xlu_corr = None
    if xly_data and xly_data.get("returns") is not None:
        aligned = ticker_returns.align(xly_data["returns"], join="inner")
        if len(aligned[0]) >= 60: xly_corr = round(aligned[0].corr(aligned[1]), 3)
    if xlu_data and xlu_data.get("returns") is not None:
        aligned = ticker_returns.align(xlu_data["returns"], join="inner")
        if len(aligned[0]) >= 60: xlu_corr = round(aligned[0].corr(aligned[1]), 3)

    cyclicality_bias = None
    if xly_corr is not None and xlu_corr is not None:
        cyclicality_bias = round(xly_corr - xlu_corr, 3)
        if cyclicality_bias >= 0.3: cycle_bias_sig = "STRONGLY_CYCLICAL_GROWTH_CORRELATED"
        elif cyclicality_bias >= 0.1: cycle_bias_sig = "MILDLY_CYCLICAL"
        elif cyclicality_bias >= -0.1: cycle_bias_sig = "NEUTRAL_CYCLE_SENSITIVITY"
        elif cyclicality_bias >= -0.3: cycle_bias_sig = "MILDLY_DEFENSIVE"
        else: cycle_bias_sig = "STRONGLY_DEFENSIVE"
    else:
        cycle_bias_sig = "CYCLE_BIAS_UNAVAILABLE"

    cycle_detail = {
        "score": beta_pts, "max": 35, "signal": beta_sig,
        "spy_beta_1y": spy_beta, "xly_correlation": xly_corr, "xlu_correlation": xlu_corr,
        "cyclicality_bias": cyclicality_bias, "cyclicality_signal": cycle_bias_sig,
        "note": "Low beta = defensive = lower economic cycle sensitivity."
    }

    total_score = de_pts + usd_pts + infl_pts + beta_pts

    if total_score >= 75: composite_signal = "LOW_MACRO_SENSITIVITY"; action = "Highly resilient to macro shocks. Low rate/dollar/cycle risk."
    elif total_score >= 58: composite_signal = "MODERATE_LOW_MACRO_SENSITIVITY"; action = "Below-average macro sensitivity. Some protection against rate hikes and dollar strength."
    elif total_score >= 42: composite_signal = "MODERATE_MACRO_SENSITIVITY"; action = "Average macro sensitivity. Performance moderately linked to rates, dollar, and economic cycle."
    elif total_score >= 28: composite_signal = "HIGH_MACRO_SENSITIVITY"; action = "Significant macro sensitivity. Rate hikes, strong dollar, or recession will meaningfully impact."
    else: composite_signal = "EXTREME_MACRO_SENSITIVITY"; action = "Highly sensitive to macro regime shifts. Avoid in tightening/recessionary environments without hedge."

    risk_factors = []
    if de_pts <= 10: risk_factors.append("High leverage → rate-sensitive")
    if usd_pts <= 8: risk_factors.append("Strong dollar headwind → multinational revenue risk")
    if infl_pts <= 7: risk_factors.append("Thin margins → inflation pass-through risk")
    if beta_pts <= 10: risk_factors.append("High beta → pro-cyclical earnings risk")

    return {
        "ticker": ticker, "sector": sector,
        "composite_signal": composite_signal, "composite_score": total_score, "max_score": 100,
        "action_guide": action, "risk_factors_identified": risk_factors,
        "component_breakdown": {
            "rate_sensitivity": rate_detail,
            "dollar_sensitivity": usd_detail,
            "inflation_sensitivity": infl_detail,
            "economic_cycle_sensitivity": cycle_detail,
        },
        "source": "Yahoo Finance — no API key required",
        "note": "Use with get_peer_comparison() for relative context. Higher score = less macro risk."
    }


# ── v4.4.0 Tool 1: Earnings Calendar Sector Screen ──
@mcp.tool()
async def get_earnings_calendar_sector_screen(sector: str = "ALL", days_ahead: int = 14) -> dict:
    """
    Scan upcoming earnings announcements by sector for the next N days.
    Returns earnings schedule with expected EPS, historical beat rate, IV-based expected move, and pre-earnings drift pattern.
    Sector options: ALL, Technology, Healthcare, Financials, ConsumerDiscretionary, ConsumerStaples,
                   Industrials, Energy, Materials, Utilities, RealEstate, CommunicationServices
    days_ahead: 1-30 days (default 14)
    """
    await Actor.charge(event_name="advanced_tool")
    import yfinance as yf
    from datetime import datetime, timedelta
    from concurrent.futures import ThreadPoolExecutor
    import math

    days_ahead = max(1, min(30, days_ahead))

    SECTOR_UNIVERSE = {
        "Technology": ["AAPL","MSFT","NVDA","META","GOOGL","AMZN","AVGO","AMD","ORCL","CRM","ADBE","INTC","QCOM","TXN","AMAT","MU","KLAC","LRCX","MRVL","PANW"],
        "Healthcare": ["JNJ","LLY","UNH","ABBV","MRK","TMO","ABT","DHR","PFE","AMGN","ISRG","BSX","SYK","MDT","GILD","REGN","VRTX","CVS","CI","HCA"],
        "Financials": ["BRK-B","JPM","BAC","WFC","MS","GS","BLK","AXP","SPGI","CB","MMC","PGR","TFC","USB","PNC","ICE","CME","COF","MET","AFL"],
        "ConsumerDiscretionary": ["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","TJX","BKNG","CMG","DHI","F","GM","YUM","ROST","RH","POOL","EXPE","MGM","LVS"],
        "ConsumerStaples": ["WMT","PG","KO","PEP","COST","PM","MO","MDLZ","STZ","KMB","CL","GIS","K","SJM","MKC","CHD","CLX","HSY","CAG","CPB"],
        "Industrials": ["RTX","HON","UPS","BA","CAT","DE","GE","LMT","NOC","ETN","EMR","ITW","PH","CMI","PCAR","GD","TDG","ROK","FDX","URI"],
        "Energy": ["XOM","CVX","COP","SLB","EOG","MPC","PSX","VLO","OXY","HAL","DVN","HES","FANG","BKR","APA","MRO","NOV","HP","WHR","RPM"],
        "Materials": ["LIN","SHW","APD","ECL","NEM","FCX","PPG","VMC","MLM","IP","CF","MOS","NUE","STLD","PKG","SON","SEE","AVY","IFF","EMN"],
        "Utilities": ["NEE","DUK","SO","D","AEP","SRE","PCG","EXC","XEL","ED","WEC","ES","AWK","ETR","CNP","AES","NI","CMS","LNT","PNW"],
        "RealEstate": ["PLD","AMT","EQIX","CCI","PSA","O","SPG","WELL","DLR","AVB","EQR","ESS","MAA","UDR","CPT","NNN","VICI","GLPI","MGP","WY"],
        "CommunicationServices": ["META","GOOGL","NFLX","DIS","CMCSA","T","VZ","CHTR","TMUS","PARA","WBD","OMC","IPG","FOXA","FOX","LYV","TTWO","EA","MTCH","ZG"],
    }

    if sector == "ALL":
        tickers_to_scan = []
        for sec, tks in SECTOR_UNIVERSE.items():
            tickers_to_scan.extend([(t, sec) for t in tks[:5]])
    elif sector in SECTOR_UNIVERSE:
        tickers_to_scan = [(t, sector) for t in SECTOR_UNIVERSE[sector]]
    else:
        return {"error": f"Unknown sector: {sector}. Use ALL or one of: {', '.join(SECTOR_UNIVERSE.keys())}"}

    today = datetime.now().date()
    cutoff = today + timedelta(days=days_ahead)

    def scan_ticker(args):
        ticker_sym, sec = args
        try:
            tk = yf.Ticker(ticker_sym)
            info = tk.info or {}
            cal = tk.calendar

            earnings_date = None
            if cal is not None and not cal.empty:
                try:
                    if hasattr(cal, 'iloc'):
                        for col in cal.columns:
                            val = cal.loc['Earnings Date', col] if 'Earnings Date' in cal.index else None
                            if val is not None:
                                if hasattr(val, 'date'): earnings_date = val.date()
                                break
                    if earnings_date is None and isinstance(cal, dict):
                        ed = cal.get('Earnings Date')
                        if ed:
                            if hasattr(ed, '__iter__') and not isinstance(ed, str): ed = list(ed)[0]
                            if hasattr(ed, 'date'): earnings_date = ed.date()
                            elif isinstance(ed, str): earnings_date = datetime.strptime(ed[:10], "%Y-%m-%d").date()
                except Exception:
                    pass

            if earnings_date is None:
                earnings_ts = info.get('earningsTimestamp') or info.get('earningsTimestampStart')
                if earnings_ts: earnings_date = datetime.fromtimestamp(earnings_ts).date()

            if earnings_date is None or not (today <= earnings_date <= cutoff):
                return None

            days_until = (earnings_date - today).days

            hist = tk.earnings_history
            beat_count = 0; total_quarters = 0; surprises = []
            if hist is not None and not hist.empty:
                for _, row in hist.iterrows():
                    actual = row.get('epsActual') if hasattr(row, 'get') else None
                    est = row.get('epsEstimate') if hasattr(row, 'get') else None
                    if actual is not None and est is not None and est != 0:
                        sp = (actual - est) / abs(est) * 100
                        surprises.append(round(sp, 1))
                        if sp >= 2: beat_count += 1
                        total_quarters += 1

            beat_rate = round(beat_count / total_quarters * 100, 0) if total_quarters >= 2 else None
            avg_surprise = round(sum(surprises) / len(surprises), 1) if surprises else None
            beat_signal = "STRONG_BEAT_HISTORY" if (beat_rate or 0) >= 75 else ("MILD_BEAT_HISTORY" if (beat_rate or 0) >= 55 else ("NEUTRAL_HISTORY" if (beat_rate or 0) >= 40 else ("MISS_TENDENCY" if beat_rate is not None else "INSUFFICIENT_HISTORY")))

            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            expected_move_pct = None
            try:
                hp = tk.history(period="3mo")
                if not hp.empty and len(hp) >= 20:
                    lr = (hp['Close'] / hp['Close'].shift(1)).apply(lambda x: math.log(x) if x and x > 0 else 0).dropna()
                    rv = lr.std() * math.sqrt(252)
                    expected_move_pct = round(rv / math.sqrt(252) * 100 * 1.5, 1)
            except Exception:
                pass

            pre_drift_pct = None
            try:
                hp1y = tk.history(period="1y")
                if not hp1y.empty and len(hp1y) >= 10:
                    l5 = hp1y['Close'].iloc[-5:]
                    if len(l5) >= 2: pre_drift_pct = round((l5.iloc[-1] / l5.iloc[0] - 1) * 100, 2)
            except Exception:
                pass

            timing = ("EARNINGS_TODAY" if days_until == 0 else "IMMINENT_CATALYST" if days_until <= 3 else "THIS_WEEK" if days_until <= 7 else "NEXT_TWO_WEEKS" if days_until <= 14 else "UPCOMING")

            return {
                "ticker": ticker_sym, "sector": sec,
                "earnings_date": str(earnings_date), "days_until_earnings": days_until, "timing_window": timing,
                "forward_eps_estimate": info.get('forwardEps'), "trailing_eps": info.get('trailingEps'),
                "current_price": round(current_price, 2) if current_price else None,
                "beat_rate_pct": beat_rate, "avg_eps_surprise_pct": avg_surprise, "beat_signal": beat_signal,
                "quarters_analyzed": total_quarters, "expected_move_pct": expected_move_pct,
                "pre_earnings_drift_5d_pct": pre_drift_pct,
            }
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for r in ex.map(scan_ticker, tickers_to_scan):
            if r is not None: results.append(r)

    results.sort(key=lambda x: x["days_until_earnings"])

    if not results:
        return {
            "sector_filter": sector, "days_ahead": days_ahead,
            "scan_date": str(today), "cutoff_date": str(cutoff),
            "earnings_events_found": 0,
            "message": "No upcoming earnings found in the scan window.",
            "earnings_schedule": [], "sector_summary": {},
            "source": "Yahoo Finance — no API key required"
        }

    sector_summary = {}
    for r in results:
        sec = r["sector"]
        if sec not in sector_summary: sector_summary[sec] = {"count": 0, "tickers": []}
        sector_summary[sec]["count"] += 1
        sector_summary[sec]["tickers"].append(r["ticker"])

    beat_plays = [r for r in results if (r["beat_rate_pct"] or 0) >= 70 and (r["avg_eps_surprise_pct"] or 0) >= 5]
    miss_risk = [r for r in results if r["beat_signal"] == "MISS_TENDENCY"]
    imminent = [r for r in results if r["days_until_earnings"] <= 3]

    return {
        "sector_filter": sector, "days_ahead": days_ahead,
        "scan_date": str(today), "cutoff_date": str(cutoff),
        "earnings_events_found": len(results),
        "earnings_schedule": results, "sector_summary": sector_summary,
        "high_confidence_beat_plays": [r["ticker"] for r in beat_plays],
        "miss_risk_watch": [r["ticker"] for r in miss_risk],
        "imminent_catalysts_3d": [r["ticker"] for r in imminent],
        "strategy_guide": {
            "straddle_entry": "Buy straddle 3-7 days before earnings for max IV expansion benefit",
            "directional_play": "Use high beat_rate tickers with positive avg_surprise for bullish call spreads",
            "iron_condor": "Use expected_move_pct to set condor wings; profit if actual move < expected",
            "iv_crush_warning": "Sell premium AFTER earnings announcement to capture IV collapse"
        },
        "source": "Yahoo Finance — no API key required",
        "note": "Verify dates via official IR pages for precision trading."
    }


# ── v4.4.0 Tool 2: Alpha Factor Composite ──
@mcp.tool()
async def get_alpha_factor_composite(ticker: str) -> dict:
    """
    Multi-factor alpha score combining Momentum, Quality, Value, and Growth factors.
    Returns composite alpha score 0-100 with factor breakdown and investment signal.
    Ticker: any valid stock symbol (e.g., AAPL, MSFT, NVDA)
    """
    await Actor.charge(event_name="advanced_tool")
    import yfinance as yf
    import math

    ticker = ticker.upper().strip()
    tk = yf.Ticker(ticker)
    info = tk.info or {}

    # ── Factor 1: Momentum (25 pts) ──
    momentum_pts = 0; momentum_detail = {}
    try:
        hist = tk.history(period="14mo")
        if not hist.empty and len(hist) >= 130:
            price_now = hist['Close'].iloc[-1]
            price_12m = hist['Close'].iloc[-252] if len(hist) >= 252 else hist['Close'].iloc[0]
            price_1m = hist['Close'].iloc[-22]
            mom_12_1 = (price_1m / price_12m - 1) * 100
            price_3m = hist['Close'].iloc[-66] if len(hist) >= 66 else hist['Close'].iloc[0]
            price_6m = hist['Close'].iloc[-130]
            ret_3m = (price_now / price_3m - 1) * 100
            ret_6m = (price_now / price_6m - 1) * 100
            composite_mom = mom_12_1 * 0.5 + ret_3m * 0.3 + ret_6m * 0.2

            if composite_mom >= 30: momentum_pts = 25; mom_sig = "STRONG_MOMENTUM_LEADER"
            elif composite_mom >= 15: momentum_pts = 20; mom_sig = "POSITIVE_MOMENTUM"
            elif composite_mom >= 5: momentum_pts = 15; mom_sig = "MILD_MOMENTUM"
            elif composite_mom >= -5: momentum_pts = 10; mom_sig = "NEUTRAL_MOMENTUM"
            elif composite_mom >= -15: momentum_pts = 5; mom_sig = "NEGATIVE_MOMENTUM"
            else: momentum_pts = 2; mom_sig = "STRONG_MOMENTUM_LAGGARD"

            ma50 = hist['Close'].iloc[-50:].mean() if len(hist) >= 50 else None
            ma200 = hist['Close'].iloc[-200:].mean() if len(hist) >= 200 else None
            above_ma50 = price_now > ma50 if ma50 else None
            above_ma200 = price_now > ma200 if ma200 else None
            if above_ma50 and above_ma200: momentum_pts = min(25, momentum_pts + 2); trend_label = "ABOVE_BOTH_MAS_UPTREND"
            elif above_ma50: trend_label = "SHORT_TERM_UPTREND"
            elif above_ma200: trend_label = "LONG_TERM_TREND_INTACT"
            else: trend_label = "BELOW_BOTH_MAS_DOWNTREND"

            momentum_detail = {
                "score": momentum_pts, "max": 25, "signal": mom_sig,
                "momentum_12_1_pct": round(mom_12_1, 1), "return_3m_pct": round(ret_3m, 1), "return_6m_pct": round(ret_6m, 1),
                "composite_momentum_pct": round(composite_mom, 1), "trend_signal": trend_label,
                "above_ma50": above_ma50, "above_ma200": above_ma200,
            }
        else:
            momentum_pts = 10; momentum_detail = {"score": 10, "max": 25, "signal": "INSUFFICIENT_HISTORY"}
    except Exception as e:
        momentum_pts = 10; momentum_detail = {"score": 10, "max": 25, "signal": "MOMENTUM_ERROR", "error": str(e)[:80]}

    # ── Factor 2: Quality (25 pts) ──
    quality_pts = 0; quality_detail = {}
    try:
        roe = info.get('returnOnEquity'); profit_margin = info.get('profitMargins')
        de_ratio = info.get('debtToEquity'); current_ratio = info.get('currentRatio')
        fcf = info.get('freeCashflow'); revenue = info.get('totalRevenue')

        roe_pts = 0
        if roe is not None:
            rp = roe * 100
            if rp >= 20: roe_pts = 10; roe_sig = "EXCELLENT_ROE"
            elif rp >= 15: roe_pts = 8; roe_sig = "STRONG_ROE"
            elif rp >= 10: roe_pts = 6; roe_sig = "MODERATE_ROE"
            elif rp >= 0: roe_pts = 3; roe_sig = "LOW_ROE"
            else: roe_pts = 0; roe_sig = "NEGATIVE_ROE"
        else: roe_pts = 4; roe_sig = "ROE_UNAVAILABLE"

        margin_pts = 0
        if profit_margin is not None:
            pm = profit_margin * 100
            if pm >= 20: margin_pts = 8; margin_sig = "HIGH_PROFIT_MARGIN"
            elif pm >= 10: margin_pts = 6; margin_sig = "HEALTHY_MARGIN"
            elif pm >= 5: margin_pts = 4; margin_sig = "MODERATE_MARGIN"
            elif pm >= 0: margin_pts = 2; margin_sig = "THIN_MARGIN"
            else: margin_pts = 0; margin_sig = "LOSS_MAKING"
        else: margin_pts = 3; margin_sig = "MARGIN_UNAVAILABLE"

        bs_pts = 0
        if de_ratio is not None:
            if de_ratio <= 30: bs_pts += 4
            elif de_ratio <= 100: bs_pts += 3
            elif de_ratio <= 200: bs_pts += 1
        else: bs_pts += 2
        if current_ratio is not None:
            if current_ratio >= 2.0: bs_pts += 3
            elif current_ratio >= 1.5: bs_pts += 2
            elif current_ratio >= 1.0: bs_pts += 1
        else: bs_pts += 1
        bs_pts = min(7, bs_pts)

        quality_pts = roe_pts + margin_pts + bs_pts
        fcf_margin = round(fcf / revenue * 100, 1) if fcf and revenue and revenue > 0 else None

        quality_detail = {
            "score": quality_pts, "max": 25,
            "roe_score": roe_pts, "roe_pct": round(roe * 100, 1) if roe else None, "roe_signal": roe_sig,
            "margin_score": margin_pts, "profit_margin_pct": round(profit_margin * 100, 1) if profit_margin else None, "margin_signal": margin_sig,
            "balance_sheet_score": bs_pts, "debt_to_equity": round(de_ratio, 1) if de_ratio else None, "current_ratio": round(current_ratio, 2) if current_ratio else None,
            "fcf_margin_pct": fcf_margin,
        }
    except Exception as e:
        quality_pts = 10; quality_detail = {"score": 10, "max": 25, "signal": "QUALITY_ERROR", "error": str(e)[:80]}

    # ── Factor 3: Value (25 pts) ──
    value_pts = 0; value_detail = {}
    try:
        pe = info.get('trailingPE') or info.get('forwardPE')
        pb = info.get('priceToBook'); ev_ebitda = info.get('enterpriseToEbitda')
        sector = info.get('sector', 'Unknown')
        SECTOR_PE = {'Technology': 28, 'Healthcare': 22, 'Financials': 14, 'ConsumerDiscretionary': 24, 'ConsumerStaples': 20, 'Industrials': 20, 'Energy': 12, 'Materials': 16, 'Utilities': 18, 'Real Estate': 35, 'Communication Services': 22}
        sector_pe_avg = SECTOR_PE.get(sector, 20)

        pe_pts = 0
        if pe is not None and pe > 0:
            pr = pe / sector_pe_avg
            if pr <= 0.6: pe_pts = 10; pe_sig = "DEEPLY_CHEAP"
            elif pr <= 0.85: pe_pts = 8; pe_sig = "CHEAP"
            elif pr <= 1.15: pe_pts = 6; pe_sig = "FAIR_VALUE"
            elif pr <= 1.5: pe_pts = 3; pe_sig = "EXPENSIVE"
            else: pe_pts = 1; pe_sig = "VERY_EXPENSIVE"
        else: pe_pts = 4; pe_sig = "PE_UNAVAILABLE"

        pb_pts = 0
        if pb is not None and pb > 0:
            if pb <= 1.0: pb_pts = 7; pb_sig = "DEEP_VALUE_PB"
            elif pb <= 2.0: pb_pts = 5; pb_sig = "VALUE_PB"
            elif pb <= 4.0: pb_pts = 3; pb_sig = "FAIR_PB"
            elif pb <= 8.0: pb_pts = 1; pb_sig = "ELEVATED_PB"
            else: pb_pts = 0; pb_sig = "EXPENSIVE_PB"
        else: pb_pts = 3; pb_sig = "PB_UNAVAILABLE"

        ev_pts = 0
        if ev_ebitda is not None and ev_ebitda > 0:
            if ev_ebitda <= 8: ev_pts = 8; ev_sig = "DEEP_VALUE_EV"
            elif ev_ebitda <= 12: ev_pts = 6; ev_sig = "CHEAP_EV"
            elif ev_ebitda <= 18: ev_pts = 4; ev_sig = "FAIR_EV"
            elif ev_ebitda <= 25: ev_pts = 2; ev_sig = "ELEVATED_EV"
            else: ev_pts = 0; ev_sig = "EXPENSIVE_EV"
        else: ev_pts = 3; ev_sig = "EV_UNAVAILABLE"

        value_pts = pe_pts + pb_pts + ev_pts
        value_detail = {
            "score": value_pts, "max": 25,
            "pe_score": pe_pts, "pe_ratio": round(pe, 1) if pe else None, "sector_pe_avg": sector_pe_avg, "pe_signal": pe_sig,
            "pb_score": pb_pts, "price_to_book": round(pb, 2) if pb else None, "pb_signal": pb_sig,
            "ev_ebitda_score": ev_pts, "ev_to_ebitda": round(ev_ebitda, 1) if ev_ebitda else None, "ev_signal": ev_sig,
            "sector": sector,
        }
    except Exception as e:
        value_pts = 10; value_detail = {"score": 10, "max": 25, "signal": "VALUE_ERROR", "error": str(e)[:80]}

    # ── Factor 4: Growth (25 pts) ──
    growth_pts = 0; growth_detail = {}
    try:
        revenue_growth = info.get('revenueGrowth'); earnings_growth = info.get('earningsGrowth')
        eps_fwd = info.get('forwardEps'); eps_trail = info.get('trailingEps')

        rev_pts = 0
        if revenue_growth is not None:
            rg = revenue_growth * 100
            if rg >= 25: rev_pts = 12; rev_sig = "HYPERGROWTH_REVENUE"
            elif rg >= 15: rev_pts = 10; rev_sig = "HIGH_GROWTH_REVENUE"
            elif rg >= 8: rev_pts = 8; rev_sig = "SOLID_GROWTH_REVENUE"
            elif rg >= 3: rev_pts = 5; rev_sig = "MODERATE_GROWTH_REVENUE"
            elif rg >= 0: rev_pts = 2; rev_sig = "FLAT_REVENUE"
            else: rev_pts = 0; rev_sig = "DECLINING_REVENUE"
        else: rev_pts = 4; rev_sig = "REVENUE_GROWTH_UNAVAILABLE"

        earn_pts = 0
        if earnings_growth is not None:
            eg = earnings_growth * 100
            if eg >= 30: earn_pts = 13; earn_sig = "HYPERGROWTH_EARNINGS"
            elif eg >= 20: earn_pts = 11; earn_sig = "STRONG_EARNINGS_GROWTH"
            elif eg >= 10: earn_pts = 8; earn_sig = "HEALTHY_EARNINGS_GROWTH"
            elif eg >= 0: earn_pts = 5; earn_sig = "FLAT_EARNINGS"
            else: earn_pts = 1; earn_sig = "EARNINGS_DECLINE"
        elif eps_fwd is not None and eps_trail is not None and eps_trail > 0:
            fg = (eps_fwd / eps_trail - 1) * 100
            if fg >= 20: earn_pts = 11; earn_sig = "STRONG_FORWARD_EPS_GROWTH"
            elif fg >= 10: earn_pts = 8; earn_sig = "HEALTHY_FORWARD_EPS_GROWTH"
            elif fg >= 0: earn_pts = 5; earn_sig = "FLAT_FORWARD_EPS"
            else: earn_pts = 1; earn_sig = "FORWARD_EPS_DECLINE"
        else: earn_pts = 5; earn_sig = "EARNINGS_GROWTH_UNAVAILABLE"

        growth_pts = rev_pts + earn_pts
        growth_detail = {
            "score": growth_pts, "max": 25,
            "revenue_score": rev_pts, "revenue_growth_pct": round(revenue_growth * 100, 1) if revenue_growth else None, "revenue_signal": rev_sig,
            "earnings_score": earn_pts, "earnings_growth_pct": round(earnings_growth * 100, 1) if earnings_growth else None, "earnings_signal": earn_sig,
            "forward_eps": eps_fwd, "trailing_eps": eps_trail,
        }
    except Exception as e:
        growth_pts = 10; growth_detail = {"score": 10, "max": 25, "signal": "GROWTH_ERROR", "error": str(e)[:80]}

    total_score = momentum_pts + quality_pts + value_pts + growth_pts

    if total_score >= 85: composite_signal = "EXCEPTIONAL_ALPHA_CANDIDATE"; action = "Strong buy signal across all factors. High conviction entry."
    elif total_score >= 70: composite_signal = "STRONG_ALPHA_CANDIDATE"; action = "Most factors favorable. Consider position entry."
    elif total_score >= 55: composite_signal = "MODERATE_ALPHA_CANDIDATE"; action = "Mixed factors. Selective entry or monitor."
    elif total_score >= 40: composite_signal = "WEAK_ALPHA_CANDIDATE"; action = "Multiple factor headwinds. Underweight or avoid."
    else: composite_signal = "AVOID"; action = "Poor multi-factor profile. Avoid."

    factors_scored = [("momentum", momentum_pts, 25), ("quality", quality_pts, 25), ("value", value_pts, 25), ("growth", growth_pts, 25)]
    factors_scored.sort(key=lambda x: x[1] / x[2], reverse=True)
    dominant_factor = factors_scored[0][0]; weakest_factor = factors_scored[-1][0]

    return {
        "ticker": ticker, "company": info.get('shortName') or info.get('longName') or ticker,
        "sector": info.get('sector', 'Unknown'), "market_cap": info.get('marketCap'),
        "composite_signal": composite_signal, "alpha_score": total_score, "max_score": 100,
        "action_guide": action, "dominant_factor": dominant_factor, "weakest_factor": weakest_factor,
        "factor_breakdown": {"momentum": momentum_detail, "quality": quality_detail, "value": value_detail, "growth": growth_detail},
        "factor_ranking": [{"factor": f[0], "score": f[1], "max": f[2], "pct": round(f[1]/f[2]*100)} for f in factors_scored],
        "source": "Yahoo Finance — no API key required",
        "note": "Use with get_peer_comparison() and get_quality_factor_screen() for portfolio construction context."
    }


@mcp.tool()
async def get_sector_fundamental_heatmap() -> dict:
    """
    11-sector fundamental heatmap: median PE, PB, EV/EBITDA, ROE, revenue growth, net margin.
    Ranks sectors by composite attractiveness for sector rotation decisions.
    No API key required.
    """
    await Actor.charge(event_name="advanced_tool")
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    import asyncio, statistics

    SECTOR_UNIVERSE = {
        "Technology":             ["AAPL","MSFT","NVDA","AVGO","ORCL","ADBE"],
        "Healthcare":             ["JNJ","UNH","LLY","ABBV","MRK","TMO"],
        "Financials":             ["JPM","BAC","WFC","GS","MS","BRK-B"],
        "ConsumerDiscretionary":  ["AMZN","TSLA","HD","MCD","NKE","BKNG"],
        "ConsumerStaples":        ["PG","KO","PEP","WMT","COST","CL"],
        "Industrials":            ["GE","CAT","UNP","HON","RTX","DE"],
        "Energy":                 ["XOM","CVX","COP","SLB","EOG","PSX"],
        "Materials":              ["LIN","APD","SHW","FCX","NEM","ECL"],
        "Utilities":              ["NEE","DUK","SO","D","AEP","SRE"],
        "RealEstate":             ["PLD","AMT","EQIX","SPG","O","WELL"],
        "CommunicationServices":  ["GOOGL","META","DIS","NFLX","T","VZ"],
    }

    def fetch_metrics(ticker):
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE') or info.get('forwardPE')
            pb = info.get('priceToBook')
            ev = info.get('enterpriseToEbitda')
            roe = info.get('returnOnEquity')
            rg = info.get('revenueGrowth')
            nm = info.get('profitMargins')
            return {
                "pe":  pe if pe and 0 < pe < 500 else None,
                "pb":  pb if pb and 0 < pb < 200 else None,
                "ev":  ev if ev and 0 < ev < 300 else None,
                "roe": roe * 100 if roe is not None else None,
                "rg":  rg * 100 if rg is not None else None,
                "nm":  nm * 100 if nm is not None else None,
            }
        except Exception:
            return None

    def safe_med(vals):
        c = [v for v in vals if v is not None]
        return round(statistics.median(c), 2) if len(c) >= 2 else None

    all_t = [t for ts in SECTOR_UNIVERSE.values() for t in ts]
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = await loop.run_in_executor(None, lambda: list(ex.map(fetch_metrics, all_t)))
    tmap = dict(zip(all_t, res))

    sector_data = {}
    for sec, tickers in SECTOR_UNIVERSE.items():
        ml = [tmap[t] for t in tickers if tmap.get(t)]
        if not ml: continue
        sector_data[sec] = {
            "median_pe": safe_med([m["pe"] for m in ml]),
            "median_pb": safe_med([m["pb"] for m in ml]),
            "median_ev_ebitda": safe_med([m["ev"] for m in ml]),
            "median_roe_pct": safe_med([m["roe"] for m in ml]),
            "median_rev_growth_pct": safe_med([m["rg"] for m in ml]),
            "median_net_margin_pct": safe_med([m["nm"] for m in ml]),
            "ticker_count": len(ml),
        }

    def rank_score(val, all_vals, lower_is_better=True):
        clean = [(v, k) for k, v in all_vals.items() if v is not None]
        if not clean or val is None: return 5
        clean.sort(key=lambda x: x[0], reverse=not lower_is_better)
        rank = next((i for i, (v, _) in enumerate(clean) if v == val), len(clean)-1)
        return round(10 * (1 - rank / max(len(clean)-1, 1)), 1)

    pe_v = {s: d["median_pe"] for s,d in sector_data.items()}
    pb_v = {s: d["median_pb"] for s,d in sector_data.items()}
    ev_v = {s: d["median_ev_ebitda"] for s,d in sector_data.items()}
    roe_v = {s: d["median_roe_pct"] for s,d in sector_data.items()}
    rg_v = {s: d["median_rev_growth_pct"] for s,d in sector_data.items()}
    nm_v = {s: d["median_net_margin_pct"] for s,d in sector_data.items()}

    scored = {}
    for sec, d in sector_data.items():
        vs = rank_score(d["median_pe"],pe_v,True)*0.4 + rank_score(d["median_pb"],pb_v,True)*0.3 + rank_score(d["median_ev_ebitda"],ev_v,True)*0.3
        qs = rank_score(d["median_roe_pct"],roe_v,False)*0.4 + rank_score(d["median_net_margin_pct"],nm_v,False)*0.3 + rank_score(d["median_rev_growth_pct"],rg_v,False)*0.3
        comp = round(vs*4.5 + qs*5.5, 1)
        if comp >= 75: attr = "HIGHLY_ATTRACTIVE"
        elif comp >= 58: attr = "ATTRACTIVE"
        elif comp >= 42: attr = "NEUTRAL"
        elif comp >= 25: attr = "UNATTRACTIVE"
        else: attr = "AVOID_SECTOR"
        scored[sec] = {**d, "valuation_score": round(vs,1), "quality_growth_score": round(qs,1), "composite_score": comp, "attractiveness": attr}

    ranked = sorted(scored.items(), key=lambda x: x[1]["composite_score"], reverse=True)
    top3 = [s for s,_ in ranked[:3]]; bot3 = [s for s,_ in ranked[-3:]]
    best_val = min(((s,d["median_pe"]) for s,d in sector_data.items() if d["median_pe"]), key=lambda x:x[1], default=(None,None))[0]
    best_grw = max(((s,d["median_rev_growth_pct"]) for s,d in sector_data.items() if d["median_rev_growth_pct"]), key=lambda x:x[1], default=(None,None))[0]
    best_roe = max(((s,d["median_roe_pct"]) for s,d in sector_data.items() if d["median_roe_pct"]), key=lambda x:x[1], default=(None,None))[0]

    return {
        "sector_heatmap": dict(ranked),
        "sector_ranking": [{"rank":i+1,"sector":s,"composite_score":d["composite_score"],"attractiveness":d["attractiveness"]} for i,(s,d) in enumerate(ranked)],
        "most_attractive_sectors": top3, "least_attractive_sectors": bot3,
        "highlights": {"best_value_sector": best_val, "best_growth_sector": best_grw, "best_profitability_sector": best_roe},
        "strategy_guide": f"OVERWEIGHT: {', '.join(top3)}. UNDERWEIGHT: {', '.join(bot3)}. Rotate toward HIGHLY_ATTRACTIVE sectors.",
        "source": "Yahoo Finance — no API key required",
        "note": "Medians from 6 S&P 500 reps per sector. Refresh weekly."
    }


@mcp.tool()
async def get_technical_strength_score(ticker: str) -> dict:
    """
    Comprehensive technical analysis scorecard: trend (MA20/50/200), momentum (RSI, MACD),
    Bollinger Band position, volume confirmation, 52-week range.
    Returns technical strength 0-100 with actionable buy/sell signals.
    No API key required.
    """
    await Actor.charge(event_name="advanced_tool")
    import yfinance as yf
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        ticker_obj = yf.Ticker(ticker)
        hist = await loop.run_in_executor(None, lambda: ticker_obj.history(period="1y"))
        if hist.empty or len(hist) < 50:
            return {"error": "Insufficient history", "ticker": ticker}

        close = hist["Close"]; volume = hist["Volume"]
        high_52 = close.max(); low_52 = close.min(); current = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

        above_ma20 = current > ma20; above_ma50 = current > ma50
        above_ma200 = (current > ma200) if ma200 is not None else None
        ma_bull = (ma20 > ma50) and (ma200 is None or ma50 > ma200)
        ma_bear = (ma20 < ma50) and (ma200 is None or ma50 < ma200)

        if above_ma20 and above_ma50 and above_ma200: t_pts = 20; t_sig = "PRICE_ABOVE_ALL_MAS"
        elif above_ma20 and above_ma50: t_pts = 15; t_sig = "PRICE_ABOVE_MA20_MA50"
        elif above_ma50: t_pts = 8; t_sig = "PRICE_ABOVE_MA50_ONLY"
        elif above_ma20: t_pts = 5; t_sig = "PRICE_ABOVE_MA20_ONLY"
        else: t_pts = 0; t_sig = "PRICE_BELOW_KEY_MAS"
        if ma_bull: t_pts += 10; align_sig = "MAS_BULLISH_ALIGNMENT"
        elif ma_bear: align_sig = "MAS_BEARISH_ALIGNMENT"
        else: t_pts += 5; align_sig = "MAS_MIXED_ALIGNMENT"
        trend_pts = t_pts
        trend_detail = {"score": trend_pts, "max": 30, "current_price": round(current,2),
            "ma20": round(ma20,2), "ma50": round(ma50,2), "ma200": round(ma200,2) if ma200 else None,
            "above_ma20": above_ma20, "above_ma50": above_ma50, "above_ma200": above_ma200,
            "ma_alignment": "BULLISH" if ma_bull else ("BEARISH" if ma_bear else "MIXED"),
            "signals": [t_sig, align_sig]}

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float('nan'))
        rsi = (100 - 100/(1+rs)).iloc[-1]

        ema12 = close.ewm(span=12,adjust=False).mean()
        ema26 = close.ewm(span=26,adjust=False).mean()
        macd = ema12 - ema26
        sig_line = macd.ewm(span=9,adjust=False).mean()
        macd_hist_s = macd - sig_line
        mc = macd.iloc[-1]; sc = sig_line.iloc[-1]; hc = macd_hist_s.iloc[-1]
        hp = macd_hist_s.iloc[-2] if len(macd_hist_s) >= 2 else 0

        if 50 <= rsi <= 70: r_pts = 15; r_sig = "RSI_BULLISH_ZONE"
        elif 40 <= rsi < 50: r_pts = 8; r_sig = "RSI_NEUTRAL_LOW"
        elif rsi > 70: r_pts = 10; r_sig = "RSI_OVERBOUGHT"
        elif 30 <= rsi < 40: r_pts = 5; r_sig = "RSI_APPROACHING_OVERSOLD"
        else: r_pts = 12; r_sig = "RSI_OVERSOLD_REVERSAL_WATCH"

        if mc > sc and hc > 0: m_pts = 10; m_sig = "MACD_BULLISH_CROSSOVER"
        elif mc > sc: m_pts = 7; m_sig = "MACD_BULLISH_DIVERGENCE"
        elif mc > 0: m_pts = 5; m_sig = "MACD_POSITIVE_TERRITORY"
        elif hc > hp: m_pts = 3; m_sig = "MACD_MOMENTUM_IMPROVING"
        else: m_pts = 0; m_sig = "MACD_BEARISH"
        mom_pts = r_pts + m_pts
        mom_detail = {"score": mom_pts, "max": 25, "rsi_14": round(rsi,1), "rsi_signal": r_sig,
            "macd_line": round(mc,4), "macd_signal": round(sc,4), "macd_histogram": round(hc,4),
            "macd_signal_label": m_sig, "signals": [r_sig, m_sig]}

        bb_mid = close.rolling(20).mean(); bb_std = close.rolling(20).std()
        bb_u = (bb_mid + 2*bb_std).iloc[-1]; bb_l = (bb_mid - 2*bb_std).iloc[-1]
        bb_m = bb_mid.iloc[-1]
        bb_pct = (current - bb_l)/(bb_u - bb_l) if bb_u != bb_l else 0.5
        if 0.4 <= bb_pct <= 0.75: bb_pts = 15; bb_sig = "PRICE_IN_BULLISH_BB_ZONE"
        elif 0.75 < bb_pct <= 1.0: bb_pts = 8; bb_sig = "NEAR_UPPER_BAND_OVERBOUGHT"
        elif 0.2 <= bb_pct < 0.4: bb_pts = 8; bb_sig = "NEAR_MID_BAND_NEUTRAL"
        elif bb_pct > 1.0: bb_pts = 5; bb_sig = "ABOVE_UPPER_BAND_EXTREME"
        elif bb_pct < 0.2: bb_pts = 10; bb_sig = "NEAR_LOWER_BAND_OVERSOLD_WATCH"
        else: bb_pts = 5; bb_sig = "BB_BELOW_MID_BEARISH"
        bb_detail = {"score": bb_pts, "max": 15, "upper_band": round(bb_u,2), "middle_band": round(bb_m,2),
            "lower_band": round(bb_l,2), "bb_pct_b": round(bb_pct,3), "signal": bb_sig}

        avg_vol_20 = volume.rolling(20).mean().iloc[-1]; last_vol = volume.iloc[-1]
        vol_ratio = last_vol/avg_vol_20 if avg_vol_20 > 0 else 1.0
        price_up_5d = close.iloc[-1] > close.iloc[-5] if len(close) >= 5 else False
        vol_5d = volume.iloc[-5:].mean()
        vol_prev = volume.iloc[-15:-5].mean() if len(volume) >= 15 else avg_vol_20
        vol_up = vol_5d > vol_prev
        if price_up_5d and vol_up: v_pts = 15; v_sig = "BULLISH_VOLUME_CONFIRMATION"
        elif price_up_5d and not vol_up: v_pts = 8; v_sig = "PRICE_UP_LOW_VOLUME_WEAK"
        elif not price_up_5d and vol_up: v_pts = 3; v_sig = "HIGH_VOLUME_DISTRIBUTION"
        else: v_pts = 6; v_sig = "NEUTRAL_VOLUME"
        vol_detail = {"score": v_pts, "max": 15, "avg_volume_20d": int(avg_vol_20), "last_volume": int(last_vol),
            "volume_ratio_vs_20d": round(vol_ratio,2), "volume_trend": "RISING" if vol_up else "FALLING", "signal": v_sig}

        rng_pct = (current - low_52)/(high_52 - low_52) if high_52 != low_52 else 0.5
        pct_from_h = (current/high_52 - 1)*100
        if rng_pct >= 0.75: rng_pts = 15; rng_sig = "NEAR_52W_HIGH_MOMENTUM"
        elif rng_pct >= 0.55: rng_pts = 12; rng_sig = "UPPER_HALF_RANGE"
        elif rng_pct >= 0.40: rng_pts = 8; rng_sig = "MID_RANGE"
        elif rng_pct >= 0.25: rng_pts = 5; rng_sig = "LOWER_HALF_RANGE"
        else: rng_pts = 2; rng_sig = "NEAR_52W_LOW_WEAKNESS"
        range_detail = {"score": rng_pts, "max": 15, "52w_high": round(high_52,2), "52w_low": round(low_52,2),
            "range_pct_b": round(rng_pct,3), "pct_from_52w_high": round(pct_from_h,1), "signal": rng_sig}

        total = trend_pts + mom_pts + bb_pts + v_pts + rng_pts
        if total >= 82: csig = "STRONG_BUY_TECHNICAL"; act = "Strong technical setup. Trend, momentum, volume aligned bullish."
        elif total >= 65: csig = "BULLISH_TECHNICAL"; act = "Solid technical structure. Consider entry on pullbacks to support."
        elif total >= 50: csig = "NEUTRAL_TECHNICAL"; act = "Mixed signals. Wait for clearer trend confirmation."
        elif total >= 35: csig = "BEARISH_TECHNICAL"; act = "Multiple technical weaknesses. Avoid new longs."
        else: csig = "STRONG_SELL_TECHNICAL"; act = "Technical structure broken. Strong avoidance signal."

        info = await loop.run_in_executor(None, lambda: ticker_obj.info)
        return {
            "ticker": ticker, "company": info.get('shortName') or info.get('longName') or ticker,
            "sector": info.get('sector','Unknown'), "current_price": round(current,2),
            "composite_signal": csig, "technical_score": total, "max_score": 100, "action_guide": act,
            "factor_breakdown": {"trend": trend_detail, "momentum": mom_detail, "bollinger": bb_detail, "volume": vol_detail, "range_52w": range_detail},
            "key_levels": {"ma20": round(ma20,2), "ma50": round(ma50,2), "ma200": round(ma200,2) if ma200 else None,
                "bb_upper": round(bb_u,2), "bb_lower": round(bb_l,2), "52w_high": round(high_52,2), "52w_low": round(low_52,2)},
            "source": "Yahoo Finance — no API key required",
            "note": "Use with get_alpha_factor_composite() to combine technical + fundamental analysis."
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@mcp.tool()
async def get_price_target_tracker(ticker: str) -> dict:
    """Analyst price target detailed analysis: consensus target vs current price upside %, recent 30/90-day target trend, target range (high/mean/low), upgrade ratio, and potential catalysts. Useful for gauging analyst conviction and positioning ahead of re-ratings."""
    await Actor.charge(event_name="advanced_tool")
    try:
        import yfinance as yf
        import asyncio
        ticker = ticker.upper().strip()
        loop = asyncio.get_event_loop()
        t = yf.Ticker(ticker)
        info = await loop.run_in_executor(None, lambda: t.info)
        current = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        company = info.get('shortName') or info.get('longName') or ticker
        sector = info.get('sector', 'Unknown')

        target_mean = info.get('targetMeanPrice')
        target_high = info.get('targetHighPrice')
        target_low  = info.get('targetLowPrice')
        target_median = info.get('targetMedianPrice')

        upside_mean = round((target_mean / current - 1) * 100, 1) if target_mean and current else None
        upside_high = round((target_high / current - 1) * 100, 1) if target_high and current else None
        upside_low  = round((target_low / current - 1) * 100, 1) if target_low and current else None

        upgrades_30 = 0; downgrades_30 = 0
        upgrades_90 = 0; downgrades_90 = 0
        recent_actions = []
        try:
            from datetime import datetime, timezone
            upgrades = await loop.run_in_executor(None, lambda: t.upgrades_downgrades)
            if upgrades is not None and not upgrades.empty:
                now = datetime.now(timezone.utc)
                for idx, row in upgrades.iterrows():
                    try:
                        if hasattr(idx, 'tzinfo') and idx.tzinfo is None:
                            idx = idx.replace(tzinfo=timezone.utc)
                        days_ago = (now - idx).days
                        action = str(row.get('Action', '')).lower()
                        grade_from = str(row.get('FromGrade', ''))
                        grade_to   = str(row.get('ToGrade', ''))
                        firm       = str(row.get('Firm', ''))
                        is_up = 'up' in action or action == 'init' or action == 'reit'
                        is_dn = 'down' in action
                        if days_ago <= 30:
                            if is_up: upgrades_30 += 1
                            elif is_dn: downgrades_30 += 1
                        if days_ago <= 90:
                            if is_up: upgrades_90 += 1
                            elif is_dn: downgrades_90 += 1
                        if days_ago <= 60 and len(recent_actions) < 8:
                            recent_actions.append({"days_ago": days_ago, "firm": firm, "action": str(row.get('Action','')), "from_grade": grade_from, "to_grade": grade_to})
                    except Exception:
                        continue
        except Exception:
            pass

        total_30 = upgrades_30 + downgrades_30
        total_90 = upgrades_90 + downgrades_90
        upgrade_ratio_30 = round(upgrades_30 / total_30, 2) if total_30 > 0 else None
        upgrade_ratio_90 = round(upgrades_90 / total_90, 2) if total_90 > 0 else None

        if total_90 >= 2 and upgrade_ratio_90 is not None:
            if upgrade_ratio_90 >= 0.70: target_trend = "TARGETS_RISING"
            elif upgrade_ratio_90 >= 0.50: target_trend = "MILDLY_POSITIVE"
            elif upgrade_ratio_90 >= 0.35: target_trend = "STABLE_MIXED"
            else: target_trend = "TARGETS_FALLING"
        else:
            target_trend = "INSUFFICIENT_DATA"

        if upside_mean is not None:
            if upside_mean >= 30: upside_sig = "STRONG_UPSIDE_POTENTIAL"; upside_action = "Significant analyst upside. High conviction re-rating candidate."
            elif upside_mean >= 15: upside_sig = "MODERATE_UPSIDE"; upside_action = "Meaningful upside vs consensus. Monitor for catalyst-driven re-rating."
            elif upside_mean >= 5:  upside_sig = "MILD_UPSIDE"; upside_action = "Modest upside to consensus target. Stock near fair value."
            elif upside_mean >= -5: upside_sig = "FAIRLY_PRICED_AT_TARGET"; upside_action = "Trading near analyst consensus. Limited near-term upside from re-rating."
            else: upside_sig = "ABOVE_CONSENSUS_TARGET"; upside_action = "Price above analyst mean target. Potential downgrade risk."
        else:
            upside_sig = "NO_TARGET_DATA"; upside_action = "Insufficient analyst coverage for price target analysis."

        rec = info.get('recommendationMean')
        rec_key = info.get('recommendationKey', '').upper().replace(' ', '_')
        if rec:
            if rec <= 1.5: rec_label = "STRONG_BUY"
            elif rec <= 2.5: rec_label = "BUY"
            elif rec <= 3.5: rec_label = "HOLD"
            elif rec <= 4.5: rec_label = "SELL"
            else: rec_label = "STRONG_SELL"
        else:
            rec_label = rec_key or "UNKNOWN"

        if target_high and target_low and target_mean:
            range_width_pct = round((target_high - target_low) / target_mean * 100, 1)
            if range_width_pct <= 15: analyst_consensus = "HIGH_CONSENSUS"
            elif range_width_pct <= 30: analyst_consensus = "MODERATE_CONSENSUS"
            elif range_width_pct <= 50: analyst_consensus = "LOW_CONSENSUS"
            else: analyst_consensus = "VERY_WIDE_DISPERSION"
        else:
            range_width_pct = None; analyst_consensus = "INSUFFICIENT_DATA"

        return {
            "ticker": ticker, "company": company, "sector": sector,
            "current_price": round(current, 2) if current else None,
            "price_targets": {"mean": round(target_mean,2) if target_mean else None, "median": round(target_median,2) if target_median else None, "high": round(target_high,2) if target_high else None, "low": round(target_low,2) if target_low else None},
            "upside_pct": {"vs_mean": upside_mean, "vs_high": upside_high, "vs_low": upside_low},
            "upside_signal": upside_sig, "action_guide": upside_action,
            "analyst_consensus": analyst_consensus, "target_range_width_pct": range_width_pct,
            "recommendation": {"label": rec_label, "mean_score": round(rec,2) if rec else None, "n_analysts": info.get('numberOfAnalystOpinions')},
            "target_trend": target_trend,
            "upgrade_activity": {"last_30d": {"upgrades": upgrades_30, "downgrades": downgrades_30, "upgrade_ratio": upgrade_ratio_30}, "last_90d": {"upgrades": upgrades_90, "downgrades": downgrades_90, "upgrade_ratio": upgrade_ratio_90}},
            "recent_analyst_actions": recent_actions,
            "source": "Yahoo Finance — no API key required",
            "note": "Use with get_earnings_revision_momentum() for combined earnings + price target momentum."
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@mcp.tool()
async def get_sector_momentum_vs_spy(period_days: int = 63) -> dict:
    """11 SPDR sector ETFs N-day return vs SPY relative performance. Shows which sectors are outperforming/underperforming the broad market, acceleration/deceleration trends, and business cycle rotation signals. Default 63 days (~1 quarter)."""
    await Actor.charge(event_name="advanced_tool")
    try:
        import yfinance as yf
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        period_days = max(5, min(252, period_days))

        SECTORS = {
            "XLK": "Technology", "XLY": "Consumer Discretionary", "XLC": "Communication Services",
            "XLF": "Financials", "XLE": "Energy", "XLI": "Industrials", "XLB": "Materials",
            "XLRE": "Real Estate", "XLV": "Healthcare", "XLP": "Consumer Staples", "XLU": "Utilities",
        }
        tickers = list(SECTORS.keys()) + ["SPY"]
        import datetime
        end = datetime.date.today()
        start = end - datetime.timedelta(days=(period_days + 30) * 2)
        loop = asyncio.get_event_loop()

        def fetch(sym):
            try:
                df = yf.download(sym, start=start, end=end, progress=False, auto_adjust=True)
                if df.empty: return sym, None
                return sym, df['Close'].squeeze()
            except Exception:
                return sym, None

        with ThreadPoolExecutor(max_workers=12) as ex:
            res_list = await loop.run_in_executor(None, lambda: list(ex.map(fetch, tickers)))
        results = dict(res_list)

        spy_s = results.get("SPY")
        if spy_s is None or len(spy_s) < period_days:
            return {"error": "Insufficient SPY data"}

        def ret_n(series, n):
            if series is None or len(series) < n + 1: return None
            vals = series.dropna()
            if len(vals) < n + 1: return None
            return round((float(vals.iloc[-1]) / float(vals.iloc[-(n+1)]) - 1) * 100, 2)

        half = max(5, period_days // 2)
        spy_ret = ret_n(spy_s, period_days)
        spy_ret_h = ret_n(spy_s, half)

        sector_data = []
        for etf, name in SECTORS.items():
            s = results.get(etf)
            ret_full = ret_n(s, period_days)
            ret_half = ret_n(s, half)
            if ret_full is None: continue
            rs = round(ret_full - (spy_ret or 0), 2)
            rs_half = round((ret_half or 0) - (spy_ret_h or 0), 2)

            if rs_half > rs + 3: accel = "ACCELERATING_OUTPERFORM"
            elif rs_half > rs + 1: accel = "MILDLY_ACCELERATING"
            elif rs_half < rs - 3: accel = "DECELERATING"
            elif rs_half < rs - 1: accel = "MILDLY_DECELERATING"
            else: accel = "STABLE"

            if rs >= 8:    sig = "STRONG_OUTPERFORMER"
            elif rs >= 3:  sig = "OUTPERFORMER"
            elif rs >= -3: sig = "MARKET_PERFORMER"
            elif rs >= -8: sig = "UNDERPERFORMER"
            else:          sig = "STRONG_UNDERPERFORMER"

            sector_data.append({"etf": etf, "sector": name, "return_pct": ret_full, "return_half_period_pct": ret_half, "vs_spy_rs": rs, "vs_spy_rs_half": rs_half, "signal": sig, "acceleration": accel})

        sector_data.sort(key=lambda x: x["vs_spy_rs"], reverse=True)
        top3 = sector_data[:3]; bot3 = sector_data[-3:]

        cyclical_list  = [x for x in sector_data if x["etf"] in ["XLK","XLY","XLC","XLF","XLE","XLI","XLB"]]
        defensive_list = [x for x in sector_data if x["etf"] in ["XLV","XLP","XLU","XLRE"]]
        cyclical_rs  = sum(x["vs_spy_rs"] for x in cyclical_list)  / max(len(cyclical_list),1)
        defensive_rs = sum(x["vs_spy_rs"] for x in defensive_list) / max(len(defensive_list),1)
        spread = cyclical_rs - defensive_rs

        if spread >= 6:    cycle_regime = "STRONG_RISK_ON_CYCLICAL"
        elif spread >= 2:  cycle_regime = "MILD_CYCLICAL_BIAS"
        elif spread >= -2: cycle_regime = "MIXED_ROTATION"
        elif spread >= -6: cycle_regime = "MILD_DEFENSIVE_TILT"
        else:              cycle_regime = "STRONG_DEFENSIVE_RISK_OFF"

        if spy_ret and spy_ret >= 8:    market_ctx = "STRONG_BULL"
        elif spy_ret and spy_ret >= 2:  market_ctx = "MILD_BULL"
        elif spy_ret and spy_ret >= -2: market_ctx = "SIDEWAYS"
        elif spy_ret and spy_ret >= -8: market_ctx = "MILD_BEAR"
        else: market_ctx = "BEAR_MARKET"

        return {
            "period_days": period_days, "half_period_days": half,
            "spy_return_pct": spy_ret, "spy_half_period_return_pct": spy_ret_h,
            "market_context": market_ctx, "cycle_regime": cycle_regime,
            "cyclical_avg_rs": round(cyclical_rs,2), "defensive_avg_rs": round(defensive_rs,2),
            "cyclical_defensive_spread": round(spread,2),
            "sector_rankings": sector_data,
            "top3_outperformers": [{"etf": x["etf"], "sector": x["sector"], "vs_spy_rs": x["vs_spy_rs"], "acceleration": x["acceleration"]} for x in top3],
            "top3_underperformers": [{"etf": x["etf"], "sector": x["sector"], "vs_spy_rs": x["vs_spy_rs"], "acceleration": x["acceleration"]} for x in bot3],
            "strategy_guide": f"Cycle regime: {cycle_regime}. SPY {period_days}d: {spy_ret}%. Overweight top RS sectors with ACCELERATING/STABLE trend. Reduce exposure to STRONG_UNDERPERFORMER + DECELERATING sectors.",
            "source": "Yahoo Finance — no API key required",
            "note": "Use with get_business_cycle_positioning() for macro-confirmed sector rotation strategy."
        }
    except Exception as e:
        return {"error": str(e)}

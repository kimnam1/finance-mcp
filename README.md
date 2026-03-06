# Finance MCP Server

[![smithery badge](https://smithery.ai/badge/@kimnam1/finance-mcp)](https://smithery.ai/server/@kimnam1/finance-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)

**v4.6.0** — Real-time financial data for AI assistants (Claude, GPT, etc.)

No API keys required. **117 tools** covering Forex, Crypto, Macro Economics, Commodities, Stock Indices, ETFs, Portfolio Backtesting, Asset Correlation, Portfolio Volatility/Sharpe, Crypto Fear & Greed Index, Market Sentiment, Dividend Analysis, Sector Rotation, Stock Fundamentals, Earnings Calendar, Stock News, US Federal Reserve data (FRED), SEC EDGAR filings/insider trades, US Treasury yield curve, Options Chain, Institutional Holdings (13F), Historical Treasury Yields, Analyst Ratings, Short Interest, FOMC Economic Calendar, DeFi TVL, **Macro Dashboard**, **Earnings Surprise**, **Insider Sentiment**, **Currency Carry Trade**, **Stock Screener**, **Unusual Options Flow**, **Earnings Call Sentiment**, **Economic Surprise Index**, **Sector Momentum**, **Market Breadth**, **Volatility Surface**, **FX Volatility**, **Credit Spreads**, **Global Equity Heatmap**, **Commodity Correlation**, **Earnings Whisper**, **Options Skew Monitor**, **Factor Exposure**, **Yield Curve Dynamics**, **Options IV Term Structure**, **Earnings Season Tracker**, **Macro Regime Monitor**, **Dividend Calendar**, **VIX Regime Monitor**, **Insider Trading Radar**, **ETF Flow Tracker**, **Options Gamma Exposure / GEX**, **Sector Rotation Signal**, **Earnings Revision Tracker**, **Short Squeeze Radar**, **Put/Call Ratio History**, **Institutional Flow Tracker**, **Dark Pool Indicator**, **Options Unusual Activity Scanner**, **Smart Money Composite**, **Options Flow Heatmap**, **Market Regime Composite**, **Earnings Surprise vs Sector**, **52W High/Low Momentum**, **Options IV Percentile**, **Cross-Asset Momentum**, **Earnings Date Countdown**, **Sector ETF vs SPY Beta**, **Relative Strength Ranking**, **Fear & Greed Composite**, **Momentum Factor Screen**, **Economic Indicators Dashboard**, **Earnings Quality Score**, **Market Internals Dashboard**, **Dividend Safety Screen**, **Valuation Composite**, **Earnings Growth Tracker**, **Liquidity Score**, **Quality Factor Screen**, **Capital Allocation Score**, **Management Quality Score**, **Competitive Moat Score**, **Earnings Revision Momentum**, **Business Cycle Positioning**, **Peer Comparison**, **Macro Sensitivity Score**, **Earnings Calendar Sector Screen**, **Alpha Factor Composite**, **Sector Fundamental Heatmap**, **Technical Strength Score**, **Price Target Tracker**, and **Sector Momentum vs SPY**.

---

## Quick Install

### Option A: Local (no account required)

```bash
pip install fastmcp httpx yfinance
```

Add to Claude Desktop / Claude Code config:

```json
{
  "mcpServers": {
    "finance": {
      "command": "python3",
      "args": ["/path/to/server.py"]
    }
  }
}
```

Restart Claude. That's it — no API keys, no accounts, no billing.

### Option B: Apify Cloud (hosted, always-on)

No local install required. The server runs on Apify's infrastructure.

1. Get your Apify API token at [apify.com/account/integrations](https://apify.com/account/integrations)
2. Add to your MCP client config:

```json
{
  "mcpServers": {
    "finance-mcp": {
      "url": "https://kimnam1--finance-mcp.apify.actor/mcp?token=YOUR_APIFY_TOKEN"
    }
  }
}
```

Supports Claude Desktop, Claude Code, Cursor, Cline, and any MCP-compatible client.
Billed pay-per-use via Apify ($0.001–$0.003 per tool call).

---

## Tools (59 total)

### Forex — ECB (European Central Bank)
| Tool | Description |
|------|-------------|
| `get_exchange_rate` | Real-time rate between two currencies |
| `convert_currency` | Convert to multiple currencies at once |
| `get_historical_rates` | Historical rates over a date range |
| `get_rate_trend` | Exchange rate trend for last N days |
| `list_supported_currencies` | All supported currency codes (~30 major) |

### Crypto — Binance + CoinGecko
| Tool | Description |
|------|-------------|
| `get_crypto_price` | Real-time price + 24h stats for any Binance pair |
| `get_crypto_market` | Top N coins ranked by market cap |
| `get_crypto_historical` | OHLCV candles — daily, 4h, or hourly |
| `compare_crypto` | Side-by-side comparison of multiple coins |

### Macro Economics — World Bank
| Tool | Description |
|------|-------------|
| `get_gdp` | GDP (total or per capita) for any country |
| `get_inflation` | Annual CPI inflation rate by country |
| `get_macro_overview` | GDP + inflation + unemployment in one call |
| `compare_gdp_growth` | GDP growth rate comparison across countries |
| `get_interest_rate` | Lending interest rate history by country |
| `compare_interest_rates` | Multi-country interest rate comparison |
| `compare_population` | Population trends across countries |

### US Federal Reserve Data — FRED *(NEW in v1.1.0, optional API key)*
| Tool | Description |
|------|-------------|
| `get_fed_funds_rate` | Federal funds rate history + current value |
| `get_us_cpi` | US CPI inflation + YoY change rate |
| `get_us_pce` | PCE price index (Fed's preferred inflation gauge) vs 2% target |
| `get_us_m2` | M2 money supply (billions USD) + MoM/YoY changes |
| `get_us_unemployment` | US unemployment rate history |

> Get a free FRED API key at fred.stlouisfed.org/docs/api/api_key.html  
> Set `FRED_API_KEY=yourkey` in environment to activate these 5 tools.  
> Server runs normally without the key — these tools are simply disabled.

### Commodities — Binance + Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_commodity_price` | Gold price (USD/oz via PAXG) |
| `get_commodity_prices` | Silver, oil, copper, natural gas, wheat — all at once |

### Stock Indices — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_stock_index` | Current level + daily change for major indices |
| `compare_stock_indices` | Side-by-side global index comparison |

### ETFs & Backtesting — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_etf_info` | Current price + stats for any ETF (SPY, QQQ, ARKK, GLD...) |
| `get_index_history` | Historical OHLCV for indices and ETFs |
| `backtest_buy_hold` | Buy-and-hold return calculator — stocks, ETFs, crypto |

### Portfolio Analytics — Yahoo Finance + alternative.me
| Tool | Description |
|------|-------------|
| `get_asset_correlation` | Pearson correlation matrix for 2-6 assets |
| `get_portfolio_volatility` | Annualized return, volatility, Sharpe ratio, max drawdown |
| `get_fear_greed_index` | Crypto Fear & Greed Index — current score + 7-day history |

### Dividend Analysis — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_dividend_info` | Trailing yield, payout ratio, ex-dividend date, 5-yr avg |

### Sector Rotation — SPDR ETFs
| Tool | Description |
|------|-------------|
| `compare_sectors` | All 11 S&P 500 sectors ranked by performance (1d/5d/1m/3m/ytd) |

### Stock Fundamentals — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_stock_summary` | P/E, EPS, market cap, 52-week range, revenue growth, ROE |

### Earnings — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_earnings_calendar` | Upcoming earnings dates with EPS estimates |
| `get_batch_earnings` | Batch earnings lookup for a watchlist |

### News — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_stock_news` | Latest news headlines for any ticker |

### Market Sentiment — Yahoo Finance
| Tool | Description |
|------|-------------|
| `get_market_sentiment` | VIX + DXY + 10Y/2Y Treasury yields in one call |

### SEC EDGAR — US Securities and Exchange Commission *(NEW in v1.2.0)*
| Tool | Description |
|------|-------------|
| `get_sec_filings` | Recent filings (10-K, 10-Q, 8-K) with direct SEC URLs — no API key |
| `get_insider_trades` | Form 4 insider buy/sell filings for any ticker |
| `get_company_facts` | XBRL financial facts: Revenue, NetIncome, Assets, EPS (historical) |

### US Treasury — Treasury.gov *(NEW in v1.2.0)*
| Tool | Description |
|------|-------------|
| `get_treasury_yield_curve` | Full yield curve (1M–30Y), curve shape (normal/inverted), 10Y-3M spread |

### Options Chain — Yahoo Finance *(NEW in v1.3.0)*
| Tool | Description |
|------|-------------|
| `get_options_chain` | Calls + puts for any ticker: strike, bid/ask, volume, OI, IV, ITM — top 10 by open interest |

### Institutional Holdings — Yahoo Finance (13F) *(NEW in v1.3.0)*
| Tool | Description |
|------|-------------|
| `get_institutional_holdings` | Top 10 institutional holders, top 5 mutual fund holders, major holders % summary |

### Historical Treasury Yields — Treasury.gov *(NEW in v1.3.0)*
| Tool | Description |
|------|-------------|
| `get_historical_treasury_yields` | 1M–30Y yield history over any date range: min/max/mean stats |

### Analyst Ratings — Yahoo Finance *(NEW in v1.4.0)*
| Tool | Description |
|------|-------------|
| `get_analyst_ratings` | Analyst consensus (buy/hold/sell), price target (current/high/low/mean/median), last 10 upgrades/downgrades |

### Short Interest — Yahoo Finance *(NEW in v1.4.0)*
| Tool | Description |
|------|-------------|
| `get_short_interest` | Short shares, days-to-cover, % of float short, MoM change, squeeze risk assessment |

### FOMC Economic Calendar — Federal Reserve *(NEW in v1.4.0)*
| Tool | Description |
|------|-------------|
| `get_economic_calendar` | Annual FOMC meeting schedule: dates, SEP (dot plot) sessions, statement/minutes release dates, next upcoming meeting |

### DeFi TVL — DefiLlama *(NEW in v1.4.0)*
| Tool | Description |
|------|-------------|
| `get_crypto_defi_tvl` | Protocol TVL + 30-day history + chain breakdown, or Top 20 DeFi protocols ranked by TVL |

### Macro Dashboard — Yahoo Finance *(NEW in v1.5.0)*
| Tool | Description |
|------|-------------|
| `get_macro_dashboard` | VIX + DXY + S&P 500 + 10Y/2Y yields + yield spread + Fear & Greed + macro regime label (risk-on/off/neutral) |

### Earnings Surprise — Yahoo Finance *(NEW in v1.5.0)*
| Tool | Description |
|------|-------------|
| `get_earnings_surprise` | EPS surprise % per quarter (beat/miss/in-line), trailing beat rate, consensus vs actual over last N quarters |

### Insider Sentiment — SEC EDGAR *(NEW in v1.5.0)*
| Tool | Description |
|------|-------------|
| `get_insider_sentiment` | Form 4 aggregate: 90-day net buy/sell sentiment (bullish/bearish/neutral), top 3 insider transactions by value |

### Currency Carry Trade — Yahoo Finance *(NEW in v1.5.0)*
| Tool | Description |
|------|-------------|
| `get_currency_carry` | Interest rate differential, spot rate, carry label (high/moderate/low/negative), trade viability, 8 EM fixed rates |

### Stock Screener — Yahoo Finance *(NEW in v1.6.0)*
| Tool | Description |
|------|-------------|
| `get_stock_screener` | Filter S&P 500 universe (80 stocks, all 11 GICS sectors) by P/E, dividend yield, market cap, sector, price. Parallel fetch via ThreadPoolExecutor. Results sorted by market cap. |

### Unusual Options Flow — Yahoo Finance *(NEW in v1.6.0)*
| Tool | Description |
|------|-------------|
| `get_options_flow` | Smart money signal detection: put/call volume ratio, OI ratio, sentiment label (BULLISH/BEARISH/NEUTRAL), top unusual contracts by notional value. Covers nearest 3 expiration dates. |

### Earnings Call Sentiment — Yahoo Finance *(NEW in v1.6.0)*
| Tool | Description |
|------|-------------|
| `get_earnings_call_sentiment` | Keyword NLP on recent earnings news headlines. Sentiment score -100 to +100 (POSITIVE/NEGATIVE/NEUTRAL). Guidance signal: RAISED/LOWERED/MAINTAINED/UNKNOWN. Top 5 earnings news with links. No API key. |

### Economic Surprise Index — Yahoo Finance *(NEW in v1.7.0)*
| Tool | Description |
|------|-------------|
| `get_economic_surprise_index` | ESI proxy: US 6-indicator composite (S&P500/VIX/10Y/Oil/Gold/USD), 10 countries via ETF momentum proxy (EU/DE/FR/JP/CN/GB/KR/BR/IN/AU). Score -100 to +100, regime label. No API key. |

### Sector Momentum — Yahoo Finance *(NEW in v1.7.0)*
| Tool | Description |
|------|-------------|
| `get_sector_momentum` | 11 SPDR sector ETFs ranked by N-day return (period_days: 5/10/20/60). Top 3 / bottom 3 sectors. Rotation signal: RISK_ON/RISK_OFF/COMMODITY_LED/MIXED. vs SPY benchmark. No API key. |

### Market Breadth — Yahoo Finance *(NEW in v1.8.0)*
| Tool | Description |
|------|-------------|
| `get_market_breadth` | S&P 100 proxy (100 stocks) batch analysis. Advance/Decline ratio, 52W High/Low counts, % above 200MA. Composite breadth score 0-100. Regime: VERY_BULLISH/BULLISH/NEUTRAL/BEARISH/VERY_BEARISH. |

### Volatility Surface — Yahoo Finance *(NEW in v1.8.0— premium)*
| Tool | Description |
|------|-------------|
| `get_volatility_surface` | IV surface for any ticker: ATM call IV per expiry (up to 8 dates), OTM put/call skew, term structure (short/mid/long-term), skew signal (PUT_SKEW/CALL_SKEW/FLAT). Annualized IV in %. |

### FX Volatility — Yahoo Finance *(NEW in v1.9.0— premium)*
| Tool | Description |
|------|-------------|
| `get_fx_volatility` | FX pair realized vol term structure. 10/30/60/252d annualized RV as proxy for hedging cost. 12 pairs (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP, USDMXN, USDBRL, USDINR, USDKRW). Vol regime + trend. 52W spot range. |

### Credit Spreads — Yahoo Finance *(NEW in v1.9.0)*
| Tool | Description |
|------|-------------|
| `get_credit_spreads` | US credit spread direction via bond ETF proxies (LQD/HYG/EMB vs IEF). 30/60d relative performance to detect widening/tightening. Regime: RISK_ON/RISK_OFF/CAUTION/NEUTRAL. 52W positioning for each ETF. |

---

## Example Queries

```
# FRED macro (v1.1.0)
get_fed_funds_rate(months=24)
→ Current: 4.33% | Peak: 5.33% (Jul 2023) | Min: 0.08% (Mar 2022)

get_us_cpi(months=12)
→ Current CPI: 315.6 | YoY: +3.1% (Target: 2.0%)

get_us_m2(months=6)
→ M2: $21.4T | MoM: +0.3% | YoY: -1.1% (QT in progress)

# Portfolio analytics
get_portfolio_volatility([{"symbol":"SPY","weight":0.6},{"symbol":"BTC","weight":0.4}], "1y")
→ Return: 15.2% | Volatility: 22.1% | Sharpe: 0.84 | Max Drawdown: -18.3%

# Sector rotation
compare_sectors()
→ XLK (Tech): +1.2% | XLF (Finance): -0.3% | XLE (Energy): -1.8%

# GDP comparison
compare_gdp_growth(["KR", "FR", "DE"], 2015, 2023)
→ Korea: avg 2.8% CAGR | France: avg 1.1% | Germany: avg 1.2%

# Earnings calendar
get_earnings_calendar("NVDA")
→ Next: May 28, 2026 | EPS Est: $0.94 | Revenue Est: $43.1B
```

---

## Competitive Comparison

| Server | Tools | API Keys | Free |
|--------|-------|----------|------|
| **Finance MCP (this)** | **63** | **0 required** | **✅** |
| FMP MCP (imbenrabi) | 250+ | 1 (paid FMP) | ❌ |
| financial-datasets/mcp-server | ~8 | 1 (paid) | ❌ |
| akshatbindal/finance-mcp | ~10 | 0 | ✅ |
| Alpaca MCP | few | Alpaca account | ❌ |

**Our edge:** No API key, no account — just clone and run. SEC EDGAR, options chain, 13F institutional data, and US Treasury feeds all free.

---

## Data Sources

| Source | Data | Auth |
|--------|------|------|
| ECB via Frankfurter | Forex rates | None |
| Binance Public API | Crypto + Gold (PAXG) | None |
| CoinGecko Public API | Market cap rankings | None |
| World Bank Open Data | GDP, inflation, macro | None |
| FRED (St. Louis Fed) | Fed rate, CPI, M2, PCE | Optional free key |
| Yahoo Finance | Equities, ETFs, futures, news | None |
| alternative.me | Crypto Fear & Greed Index | None |

---

## Changelog

- **v4.6.0**: Price target tracker per ticker (consensus mean/median/high/low price targets vs current price, upside % to each target, upside signal STRONG_UPSIDE_POTENTIAL ≥30%/MODERATE_UPSIDE ≥15%/MILD_UPSIDE ≥5%/FAIRLY_PRICED_AT_TARGET/ABOVE_CONSENSUS_TARGET, target range width as consensus conviction proxy HIGH_CONSENSUS ≤15%/MODERATE_CONSENSUS/LOW_CONSENSUS/VERY_WIDE_DISPERSION, recommendation mean score 1-5 label STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL, target trend TARGETS_RISING/MILDLY_POSITIVE/STABLE_MIXED/TARGETS_FALLING from 30d/90d upgrade ratio, recent analyst actions with firm+action+from/to grade; advanced tier) + sector momentum vs SPY (11 SPDR sector ETFs N-day return vs SPY configurable 5-252 days default 63d, excess return RS per sector, half-period RS for acceleration/deceleration detection ACCELERATING_OUTPERFORM/MILDLY_ACCELERATING/STABLE/MILDLY_DECELERATING/DECELERATING, RS signal STRONG_OUTPERFORMER ≥8pp/OUTPERFORMER ≥3pp/MARKET_PERFORMER/UNDERPERFORMER/STRONG_UNDERPERFORMER, full sector rankings + top-3 outperformers and underperformers, cycle regime from cyclical vs defensive RS spread STRONG_RISK_ON_CYCLICAL/MILD_CYCLICAL_BIAS/MIXED_ROTATION/MILD_DEFENSIVE_TILT/STRONG_DEFENSIVE_RISK_OFF, market context STRONG_BULL/MILD_BULL/SIDEWAYS/MILD_BEAR/BEAR_MARKET; advanced tier) — 117 tools

- **v4.5.0**: Sector fundamental heatmap (11 GICS sectors × median PE/PB/EV-EBITDA/ROE/revenue growth/net margin from 6 S&P 500 reps per sector; composite attractiveness score 0-100 = valuation sub-score 45% + quality/growth sub-score 55%; HIGHLY_ATTRACTIVE/ATTRACTIVE/NEUTRAL/UNATTRACTIVE/AVOID_SECTOR; top-3 overweight sectors, bottom-3 underweight, highlights for best value/growth/profitability sector; rotation strategy guide; advanced tier) + technical strength scorecard per ticker (5-component technical analysis score 0-100: Trend/MA alignment 30pts — price vs MA20/50/200 + bullish MA alignment; Momentum/RSI+MACD 25pts — RSI-14 zone + MACD crossover/territory; Bollinger Band position 15pts — B% zone; Volume confirmation 15pts — price direction + volume direction; 52W range position 15pts — proximity to highs/lows; composite STRONG_BUY_TECHNICAL ≥82/BULLISH_TECHNICAL ≥65/NEUTRAL_TECHNICAL ≥50/BEARISH_TECHNICAL ≥35/STRONG_SELL_TECHNICAL; key price levels: MA20/50/200/BB_upper/BB_lower/52W_high/52W_low; advanced tier) — 115 tools
- **v4.4.0**: Earnings calendar sector screen (scans S&P 500 proxy by sector for upcoming earnings in next 1-30 days: date + timing window EARNINGS_TODAY/IMMINENT_CATALYST/THIS_WEEK/NEXT_TWO_WEEKS/UPCOMING + historical beat rate + avg EPS surprise + expected move % via realized vol × 1.5 earnings premium + pre-earnings 5-day drift + high-confidence beat plays list beat_rate ≥70% + avg_surprise ≥5% + miss risk watch + strategy guide for straddle/iron condor/directional/IV crush; sector filter: ALL or specific sector; advanced tier) + alpha factor composite per ticker (4-factor alpha scorecard 0-100 total: Momentum 25pts = 12-1 factor×50% + 3M×30% + 6M×20% + MA50/200 trend bonus; Quality 25pts = ROE 10pts + profit margin 8pts + balance sheet D/E + current ratio 7pts; Value 25pts = PE vs sector benchmark 10pts + PB 7pts + EV/EBITDA 8pts; Growth 25pts = revenue growth 12pts + earnings growth 13pts; composite EXCEPTIONAL_ALPHA_CANDIDATE ≥85/STRONG ≥70/MODERATE ≥55/WEAK ≥40/AVOID <40; dominant and weakest factor identified; factor ranking; action guide; advanced tier) — 113 tools
- **v4.3.0**: Peer comparison per ticker (6-metric fundamental comparison vs 10-15 sector peers: PE/PB/EV-EBITDA/ROE/revenue growth/gross margin — percentile rank for each metric, composite percentile → PREMIUM_TO_PEERS/MILD_PREMIUM/FAIR_VALUE/MILD_DISCOUNT/CHEAP_VS_PEERS; sector peer universes for all 11 GICS sectors with 13-14 S&P 500 peers; strongest/weakest peers by composite; action guide per tier, advanced tier) + macro sensitivity scorecard per ticker (4-component macro risk score 0-100: rate sensitivity 25pts via D/E leverage + TLT correlation; dollar sensitivity 20pts via UUP correlation — negative = multinational risk; inflation sensitivity 20pts via gross margin + Energy/Materials sector bonus + commodity correlations; economic cycle sensitivity 35pts via SPY 1Y OLS beta + XLY vs XLU cyclicality bias → LOW_MACRO_SENSITIVITY ≥75/MODERATE_LOW ≥58/MODERATE ≥42/HIGH_MACRO_SENSITIVITY ≥28/EXTREME_MACRO_SENSITIVITY <28; risk factors list, action guide, advanced tier) — 111 tools
- **v4.2.0**: Earnings revision momentum per ticker (analyst upgrade/downgrade momentum over 30/60/90-day windows, weighted revision score = 30d×50%+60d incremental×30%+90d incremental×20%, signal REVISION_MOMENTUM_STRONG/POSITIVE/NEUTRAL/NEGATIVE/REVISION_DETERIORATING; analyst consensus STRONG_ANALYST_CONSENSUS_BUY/ANALYST_HOLD/ANALYST_CONSENSUS_SELL; coverage quality LOW/MODERATE/HIGH_COVERAGE; price targets mean/high/low with upside %; forward/trailing EPS with growth %; recent 6 analyst actions with firm+grade; action guide per tier, advanced tier) + business cycle positioning (4-component ETF-based cycle phase detector: PMI proxy 30pts XLY+XLI+XLB vs XLP+XLU+XLV spread, rate environment 25pts TLT 3M return, credit spread 25pts HYG vs LQD, market momentum 20pts SPY+QQQ avg; composite 0-100 → EARLY_CYCLE/MID_CYCLE/LATE_CYCLE/SLOWDOWN/RECESSION; sector overweight/neutral/underweight recommendations per phase; optional single-sector positioning signal, basic tier) — 109 tools
- **v4.1.0**: Management quality scorecard per ticker (5-component: CEO tenure proxy neutral 10pts, ROE trend 25pts — 3-4yr historical ROE with IMPROVING +5pts/DECLINING -3pts adjustment, R&D efficiency 20pts — R&D/revenue scored relative to gross margin tier HEALTHY_RD/HIGH_RD_INVESTMENT, SBC discipline 20pts — stock-based compensation/revenue ≤1%=20 MINIMAL_DILUTION/≥8%=3 HIGH_DILUTION_RISK, operating margin stability 15pts — 4yr CV ≤10%=HIGHLY_STABLE; composite 0-90 → EXCELLENT_MANAGEMENT ≥75/GOOD ≥58/MIXED ≥40/POOR <40, advanced tier) + competitive moat scorecard per ticker (5-component: gross margin stability 25pts — 5yr avg × CV, ELITE_MARGIN_FORTRESS ≥60% stable=25/EXPANDING trend +2pts/CONTRACTING -3pts; operating leverage 20pts — op income growth/revenue growth ratio ≥3x=20; pricing power proxy 20pts — current vs 3-5yr avg gross margin delta >5pp=20 STRONG_PRICING_POWER; market position 15pts — market cap tier with revenue growth adjustments; R&D IP moat 20pts — R&D intensity × gross margin quality composite ≥0.15=20 DEEP_IP_MOAT; composite 0-100 → WIDE_MOAT ≥78/NARROW_MOAT ≥58/NO_MOAT ≥38/STRUCTURAL_DISADVANTAGE <38, advanced tier) — 107 tools

- **v4.0.0**: Quality factor screen (screens 150-ticker S&P 500 proxy universe across 11 sectors using 5-component scorecard: ROE quality 25pts ≥20%=25/≥15%=20/≥10%=14/≥0%=6/negative=0, debt/equity safety 25pts D/E ≤0.3=25/≤0.6=20/≤1.0=14/≤2.0=6/>2.0=0, EPS growth CAGR 20pts ≥20%=20/≥12%=16/≥6%=11/≥0%=5/negative=0, FCF margin 20pts ≥20%=20/≥12%=16/≥6%=11/≥0%=5/negative=0, earnings stability 10pts — quarterly NI positive rate; composite 0-100 → QUALITY_ELITE ≥85/QUALITY_SOLID ≥65/QUALITY_MIXED ≥40/LOW_QUALITY <40; top-N picks, elite names, lowest quality list, sector concentration, market quality signal, ThreadPoolExecutor 12 parallel, advanced tier) + capital allocation scorecard per ticker (5-component: buyback yield 25pts — repurchase/market cap or shares shrinkage proxy; dividend growth consistency 20pts — YoY DPS growth + payout sustainability; FCF reinvestment ratio 20pts — capex/FCF optimal range 0.20-0.60; M&A discipline via goodwill/assets 20pts — ≤5% organic grower to >50% acquisition risk; ROIC proxy 15pts — net income/invested capital; composite 0-100 → EXCELLENT_CAPITAL_ALLOCATOR ≥80/GOOD_ALLOCATOR ≥60/MIXED_ALLOCATOR ≥40/POOR_ALLOCATOR <40 with action guide, advanced tier) — 105 tools
- **v3.9.0**: Earnings growth tracker per ticker (tracks EPS + Revenue YoY growth rates across last 4 quarters; calculates acceleration/deceleration delta by comparing recent 2Q avg vs prior 2Q avg; regime ACCELERATING_GROWTH/STEADY_GROWTH/DECELERATING/STALLING/DECLINING; composite signal STRONG_GROWTH_ACCELERATION/HEALTHY_GROWTH/MIXED_GROWTH/WEAKENING_GROWTH/GROWTH_CONCERN from EPS 60% + Revenue 40%; strategy for GARP screening, advanced tier) + liquidity score per ticker (composite 0-100: market cap tier 30pts MEGA/LARGE/MID/SMALL/MICRO-CAP, avg daily dollar volume 30d 35pts ULTRA_HIGH/HIGH/MODERATE/LOW/VERY_LOW, Amihud illiquidity ratio 20pts — mean(|log return|/dollar_volume)×1e9, bid-ask spread proxy 15pts from 30d realized vol×0.003; signal HIGHLY_LIQUID ≥80/LIQUID ≥60/MODERATE ≥40/ILLIQUID ≥20/VERY_ILLIQUID <20; position sizing guidance with easy entry/exit size in $M, volume trend VOLUME_SURGE/ABOVE_AVERAGE/NORMAL/BELOW_AVERAGE/VOLUME_DRY_UP, advanced tier) — 103 tools
- **v3.8.0**: Dividend safety screen (scans 80+ S&P 500 dividend stocks across 9 sectors: 4-component safety scorecard — payout ratio 30pts VERY_LOW/SUSTAINABLE/ELEVATED/HIGH/UNSUSTAINABLE, FCF coverage ratio 35pts ≥3x EXCELLENT/≥2x STRONG/≥1.3x ADEQUATE/≥1.0x TIGHT/<0.7x FCF_DEFICIT_RISK, yield quality 20pts ATTRACTIVE/LOW/HIGH_YIELD_WATCH/YIELD_TRAP_RISK, beta stability 15pts; composite 0-100 → SAFE_DIVIDEND ≥65/AT_RISK 40-64/DIVIDEND_CUT_RISK <40; top-10 safe picks, at-risk watch list, high-risk names, sector safety ranking sorted by safety rate %, sector filter support, ThreadPoolExecutor 12 parallel, advanced tier) + valuation composite per ticker (5-component multi-factor scorecard: P/E vs sector benchmark 25pts DEEPLY_CHEAP/CHEAP/IN_LINE/EXPENSIVE/SIGNIFICANTLY_EXPENSIVE, P/B vs sector 20pts DEEP_VALUE/VALUE/FAIR/ELEVATED/EXPENSIVE, EV/EBITDA vs sector 20pts same scale, PEG ratio 15pts ≤0.8 GROWTH_AT_DISCOUNT/≤1.2 FAIR/≤2.0 EXPENSIVE/>2 OVERPRICED, DCF proxy 20pts — 10-year FCF projection growth capped 30% + beta-adjusted discount rate 9%+ + 2.5% terminal growth → implied price vs current price upside %; composite 0-100 → DEEPLY_UNDERVALUED ≥72/UNDERVALUED ≥55/FAIRLY_VALUED ≥38/OVERVALUED ≥22/SIGNIFICANTLY_OVERVALUED <22 with actionable guidance, built-in sector PE/PB/EV benchmarks for 11 sectors, full key metrics output, advanced tier) — 101 tools
- **v3.7.0**: Earnings quality score per ticker (4-component scorecard: cash flow quality 30pts via accruals ratio (NI-OCF)/avg_assets with EXCELLENT_CASH_BACKING/STRONG/MODERATE/WEAK/ACCRUAL_WARNING; earnings persistence 25pts via 4-year net income coefficient of variation + trend HIGHLY_PERSISTENT/MODERATELY_PERSISTENT/LOW_PERSISTENCE/ERRATIC; revenue growth momentum 25pts via YoY+3Y CAGR STRONG_REVENUE_GROWTH/HEALTHY_GROWTH/MODERATE_GROWTH/FLAT/DECLINING; ROE quality 20pts via returnOnEquity EXCELLENT/STRONG/MODERATE/LOW/NEGATIVE; composite 0-100 signal HIGH_QUALITY/MODERATE_QUALITY/LOW_QUALITY/VERY_LOW_QUALITY, advanced tier) + market internals dashboard (100-stock S&P 500 proxy universe scanned in parallel: Advance/Decline proxy from 10d returns with A/D ratio and signal; New Highs/Lows — stocks within 3% of 52W high/low threshold with net % and NH/NL ratio; % above MA50 and MA200 with STRONG_BREADTH/HEALTHY/NEUTRAL/WEAK/OVERSOLD_BREADTH and LONG_TERM_BULL/BULL_TREND/TRANSITION/BEAR_TREND/LONG_TERM_BEAR; McClellan Oscillator proxy from 10d vs 30d breadth differential; Bullish Percent Index proxy from % above 200d MA; composite health score 0-100 → HEALTHY/NEUTRAL/DETERIORATING/OVERSOLD/VERY_OVERSOLD with action guidance, basic tier) — 99 tools
- **v3.6.0**: Momentum factor screen (12-1 momentum factor for 140+ S&P 500 proxy tickers across 11 sectors: 12M return minus 1M return, HIGH_MOMENTUM/NEUTRAL_MOMENTUM/LOW_MOMENTUM quintiles top/bottom 30%, sector-level avg momentum LEADING/OUTPERFORMING/NEUTRAL/UNDERPERFORMING/LAGGING, market regime STRONG_MOMENTUM_MARKET/MOMENTUM_MARKET/MIXED_MOMENTUM/WEAK_MOMENTUM/MOMENTUM_CRASH, top-N and bottom-N stocks with full 1W/1M/3M/6M/12M return breakdown, strategy guide for long/short/mean-reversion plays, advanced tier) + economic indicators dashboard by country (macro health scorecard for 13 countries US/EU/JP/CN/KR/GB/CA/AU/IN/BR/MX/DE/FR: 5-component ETF proxy model — growth 25pts via equity ETF, inflation 20pts via GLD+USO, employment 20pts via XLY vs XLP, fiscal/credit 20pts via HYG/IEF + VIX, currency 15pts via currency ETF; composite 0-100 with STRONG/HEALTHY/MIXED/WEAK/DISTRESSED regime and asset allocation signal, basic tier) — 97 tools
- **v3.5.0**: Relative strength ranking for custom ticker lists (up to 20 tickers, 1W/1M/3M/6M returns + RS score vs SPY, composite momentum 1W×20%+1M×30%+3M×30%+6M×20%, momentum_regime STRONG_OUTPERFORMER/OUTPERFORMER/NEUTRAL/UNDERPERFORMER/STRONG_UNDERPERFORMER, top-5 leaders + bottom-5 laggards, market context BULL_MARKET/BEAR_MARKET/SIDEWAYS, strategy guide, advanced tier) + fear & greed composite index (7-indicator CNN-replication using public data: VIX 20pts + 52W high/low breadth 20pts + safe haven demand TLT/SPY 15pts + put/call ratio SPY 15pts + junk bond demand HYG/IEF 15pts + market momentum SPY/125d MA 10pts + stock price breadth RSP/SPY 5pts = score 0-100, EXTREME_FEAR/FEAR/NEUTRAL/GREED/EXTREME_GREED signal, recommended action REDUCE_RISK/HOLD_OR_TRIM/BALANCED/WATCH_FOR_ENTRY/AGGRESSIVE_BUY_ZONE, full per-component breakdown, basic tier) — 95 tools
- **v3.4.0**: Earnings date countdown per ticker (next earnings date, days_until, timing_signal EARNINGS_PASSED_OR_TODAY/IMMEDIATE_PLAY/PRIME_ENTRY_WINDOW/EARLY_ENTRY/WATCH_LIST/TOO_EARLY, ATM straddle-based expected move %, historical 4Q EPS beat/miss, beat rate, avg surprise, 5d pre-earnings drift pattern, earnings_tendency STRONG_BEAT_TENDENCY/MILD_BEAT_TENDENCY/NEUTRAL/STRONG_MISS_TENDENCY/MILD_MISS_TENDENCY, full strategy guide for straddle/condor/directional/IV-crush risk, advanced tier) + sector ETF vs SPY beta (1-year OLS beta for all 11 SPDR sector ETFs vs SPY daily returns: XLK/XLY/XLC/XLF/XLE/XLI/XLB/XLRE/XLV/XLP/XLU, beta_label HIGH_BETA/ABOVE_AVERAGE/MARKET_NEUTRAL/BELOW_AVERAGE/LOW_BETA, annualized vol %, SPY correlation, 1W/1M/3M return, sectors ranked by beta, market trend STRONG_BULL/MILD_BULL/SIDEWAYS/MILD_BEAR/STRONG_BEAR from SPY 1M/3M, rotation_guidance for offensive/defensive positioning, tactical allocation guide, basic tier) — 93 tools
- **v3.3.0**: Options IV percentile per ticker (ATM IV vs 1-year historical distribution, IV percentile rank 0-100, IV rank, IV_ELEVATED/IV_NORMAL/IV_DEPRESSED signal, SELL_PREMIUM/BUY_PREMIUM strategy with detail, historical RV stats 30d/3m/6m/1y/min/max, advanced tier) + cross-asset momentum (7 assets SPY/QQQ/IWM/TLT/GLD/UUP/BTC-USD — 1W/1M/3M return rankings, weighted composite rank, STRONG_RISK_ON/RISK_ON/MIXED/RISK_OFF/STRONG_RISK_OFF regime with net score, momentum leaders/laggards top-3, allocation signal, basic tier) — 91 tools
- **v3.2.0**: Earnings surprise vs sector per ticker (compare EPS surprise % and beat rate vs 10-15 sector representative peers, SECTOR_OUTPERFORMER/IN_LINE/SECTOR_UNDERPERFORMER signal, strength STRONG/MODERATE/MILD, trend IMPROVING/STABLE/DECLINING, quarterly breakdown 4 most recent quarters, advanced tier) + 52W high/low momentum (scans 150-ticker S&P 500 proxy across 11 GICS sectors, counts near 52W high/low within 3% threshold, net ratio → STRONG_BULL_MOMENTUM/BULLISH_MOMENTUM/NEUTRAL_MOMENTUM/BEARISH_MOMENTUM/STRONG_BEAR_MOMENTUM, sector LEADING/NEUTRAL/LAGGING, top-5 nearest highs/lows, basic tier) — 89 tools
- **v3.1.0**: Options flow heatmap (11 GICS sectors × 4 representative tickers, sector-level put/call ratio + unusual sweep counts, flow signal STRONG_BULLISH/BULLISH/NEUTRAL/BEARISH/STRONG_BEARISH per sector, market flow regime BROAD_BULLISH_FLOW/MODERATE_BULLISH_FLOW/MIXED_FLOW/MODERATE_BEARISH_FLOW/BROAD_BEARISH_FLOW, most bullish/bearish sectors ranked, advanced tier) + market regime composite (5-layer regime detector: VIX regime 25pts + yield curve shape 20pts + credit spreads HYG/IEF 20pts + market breadth SPY/RSP 20pts + sector rotation XLK+XLY vs XLP+XLU 15pts = regime score 0-100, BULL_MARKET/TRANSITION/CHOPPY_MARKET/BEAR_MARKET, asset allocation guidance, basic tier) — 87 tools
- **v3.0.0**: Options unusual activity scanner (market-wide 100-ticker S&P 500 scan, volume/OI ratio ≥3× + volume ≥500 threshold, detects UNUSUAL_CALL_SWEEP/UNUSUAL_PUT_SWEEP, ranks by notional USD, market bias signal BULLISH_SWEEP_DOMINANCE/BEARISH_SWEEP_DOMINANCE/MILD_CALL_LEAN/MILD_PUT_LEAN/BALANCED_UNUSUAL_FLOW, 12-thread parallel scan, premium tier) + smart money composite per ticker (5-component scorecard: OBV divergence dark pool 25pts + institutional ownership % 20pts + Form 4 insider transactions 90d 25pts + short interest 15pts + options P/C sentiment 15pts = SMART_MONEY_SCORE 0-100, signal STRONG_SMART_MONEY_BUY/SMART_MONEY_BUY/NEUTRAL/SMART_MONEY_SELL/STRONG_SMART_MONEY_SELL, full per-component breakdown, advanced tier) — 85 tools
- **v2.9.0**: Institutional flow tracker (120+ S&P 500 stocks across 11 sectors, institutional ownership % from yfinance, top holder + stake %, 3M price momentum, 10d/20d volume surge, heuristic flow signal STRONG_ACCUMULATION/ACCUMULATION/NEUTRAL/DISTRIBUTION/STRONG_DISTRIBUTION, sector aggregation SECTOR_ACCUMULATION/MILD_ACCUMULATION/NEUTRAL/MILD_DISTRIBUTION, overall INSTITUTIONAL_BUY_PRESSURE/INSTITUTIONAL_SELL_PRESSURE/BALANCED_FLOWS, top-15 accumulation + top-10 distribution candidates, sector filter, advanced tier) + dark pool indicator per ticker (OBV divergence BULLISH_DIVERGENCE/BEARISH_DIVERGENCE, 20d VWAP vs price %, block trade proxy: days with volume ≥1.8× 30d avg + range ≤1.5% = institutional block order BUY/SELL, A/D line 10d trend ACCUMULATING/DISTRIBUTING, volume climax ≥2.5× avg, composite signal STEALTH_ACCUMULATION/STEALTH_DISTRIBUTION/BLOCK_BUYING/BLOCK_SELLING/NO_SIGNAL with confidence points 0-10, premium tier) — 83 tools
- **v2.8.0**: Short squeeze radar (60+ high-short-interest stocks, composite squeeze_score 0-100: short % of float ×40 + 1W momentum ×30 + volume surge ×30, EXTREME/HIGH/MODERATE/LOW risk tiers, top-15 candidates + extreme alerts, advanced tier) + put/call ratio history per ticker (composite P/C ratio from volume + OI across up to 6 expirations 7-90 DTE, contrarian signal BULLISH_EXTREME/BEARISH_EXTREME/ELEVATED_FEAR/ELEVATED_COMPLACENCY/NEUTRAL, fear/greed proxy 0-100, P/C trend NEAR_TERM_FEAR/LONG_TERM_FEAR/FLAT_STRUCTURE, OI signal HEAVY_PUT_OI/PUT_LEANING/CALL_LEANING/HEAVY_CALL_OI, calibrated thresholds for index ETFs vs individual stocks, premium tier) — 81 tools
- **v2.7.0**: Sector rotation signal (11 SPDR sector ETFs scored by relative return vs SPY: 1M×40%+3M×35%+6M×25% composite, OVERWEIGHT/NEUTRAL/UNDERWEIGHT per sector, DEFENSIVE/CYCLICAL/VALUE/MIXED_ROTATION regime, VIX + 10Y yield macro overlay, advanced tier) + earnings revision tracker per ticker (analyst upgrade/downgrade momentum 30d/90d, RISING/FALLING/STABLE signal, EPS estimate current-quarter + next-year growth %, consensus price target with upside %, recent 5 analyst actions with firm + grade change, recommendation mean label STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL, advanced tier) — 79 tools
- **v2.6.0**: ETF flow tracker (12 ETFs: SPY/QQQ/IWM/GLD/TLT/HYG/XLF/XLE/XLK/XLV/EEM/UUP — OBV slope 10d/30d, STRONG_INFLOW/INFLOW/NEUTRAL/OUTFLOW/STRONG_OUTFLOW per ETF, volume regime, 5d/10d/30d returns, rotation signal RISK_ON/RISK_OFF/MIXED_FLOWS, basic tier) + options gamma exposure GEX (Black-Scholes gamma × OI × 100 × spot per strike, net GEX = call GEX − put GEX, GEX flip point, POSITIVE_GEX/NEGATIVE_GEX market impact signal, top 10 gamma strikes, gamma wall, concentration %, premium tier) — 77 tools
- **v2.5.0**: VIX regime monitor (spot, MA10/20/50, 1yr percentile rank, PANIC/ELEVATED/NORMAL/COMPLACENT stress regime, term structure CONTANGO/BACKWARDATION/FLAT via VXZ proxy, allocation signal, basic tier) + insider trading radar (SEC Form 4 cluster buy scanner across 165 S&P 500 stocks / 11 sectors, STRONG_ACCUMULATION signal for 3+ buys with $500K+ net, sector summary, advanced tier) — 75 tools
- **v2.4.0**: Macro regime monitor (4-axis: Growth/Inflation/Rates/Liquidity → GOLDILOCKS/OVERHEATING/STAGFLATION/RECESSION/LATE_CYCLE, regime score 0-100, asset allocation signal, basic tier) + dividend calendar (80 S&P 500 payers, 11 sectors, upcoming ex-div dates, yield vs 5yr avg, payout ratio safety SAFE/MODERATE/HIGH_PAYOUT, dividend growth YoY, advanced tier) — 73 tools
- **v2.3.0**: Options IV term structure (CONTANGO/BACKWARDATION/FLAT, VIX comparison, vol risk premium RICH/CHEAP/FAIR, 30/60/90/120/180/360d tenors, premium tier) + earnings season tracker (S&P 500 60-ticker proxy, beat/miss/in-line rates, sector breakdown, STRONG/NORMAL/WEAK_SEASON signal, advanced tier) — 71 tools
- **v2.2.0**: Factor exposure (Fama-French 5-factor OLS regression, ETF proxies, tilt signal) + yield curve dynamics (3M/5Y/10Y/30Y yields, spreads in bps, curve shape, inversion stats) — 69 tools
- **v2.1.0**: Earnings whisper (4Q EPS surprise pattern, price reaction, whisper gap signal) + options skew monitor (SPY/QQQ/IWM 25-delta skew, tail risk vs complacency signal) — 67 tools
- **v2.0.0**: Global equity heatmap (20 countries, DM/EM, 1D/1W/1M returns) + commodity correlation matrix (6 commodities × SPY/TLT/DXY, regime signal) — 65 tools
- **v1.9.0**: FX volatility realized vol term structure (premium) + credit spreads ETF proxy — 63 tools
- **v1.8.0**: Market breadth (S&P 100 proxy, A/D ratio, 200MA) + volatility surface (IV surface, premium tier) — 61 tools
- **v1.7.0**: Economic surprise index + sector momentum — 59 tools
- **v1.6.0**: Stock screener + unusual options flow + earnings call sentiment — 57 tools
- **v1.5.0**: Macro dashboard + earnings surprise + insider sentiment + currency carry trade — 54 tools
- **v1.4.0**: Analyst ratings + short interest + FOMC economic calendar + DeFi TVL — 50 tools
- **v1.3.0**: Options chain + institutional holdings (13F) + historical Treasury yields — 46 tools
- **v1.2.0**: SEC EDGAR filings/insider trades/XBRL facts + Treasury yield curve — 43 tools
- **v1.1.0**: FRED API integration (5 US macro tools), Apify Actor support — 39 tools
- **v1.0.0**: Earnings calendar + batch earnings + stock news — 34 tools
- **v0.9.0**: Dividend analysis + sector rotation + stock fundamentals — 29 tools
- **v0.8.0**: Multi-commodity prices + market sentiment (VIX/DXY/yields) — 26 tools
- **v0.7.0**: Asset correlation + portfolio volatility/Sharpe + Fear & Greed — 24 tools
- **v0.6.0**: ETF info + index history + buy-and-hold backtesting — 21 tools
- **v0.5.0**: Interest rates + population + stock indices (Yahoo Finance) — 18 tools
- **v0.4.0**: Gold price + GDP growth comparison + portfolio P&L — 15 tools
- **v0.3.0**: World Bank macro (GDP, inflation, unemployment) — 11 tools
- **v0.2.0**: Crypto prices (Binance + CoinGecko) — 9 tools
- **v0.1.0**: Forex tools via ECB/Frankfurter — 5 tools

---

## License

MIT — free for personal and commercial use.

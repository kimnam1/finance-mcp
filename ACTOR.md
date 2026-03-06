# Finance MCP Server — Apify Store Description

## What it does

Finance MCP Server gives AI assistants (Claude, GPT, Cursor, etc.) access to real-time financial data through the Model Context Protocol (MCP). **119 tools**, zero required API keys, zero setup friction.

Ask your AI: "What's the current Fed funds rate?", "Compare SPY vs QQQ over 3 years", "Show me GDP growth for Korea, France, and Germany" — and get live data, not stale training data.

## Why use this Actor

Most financial data APIs cost money or require account setup. This server pulls from public, official sources:

- **ECB / Frankfurter** — Forex rates (30+ currencies)
- **Binance Public API** — Crypto prices, OHLCV, Gold (PAXG)
- **CoinGecko Public API** — Market cap rankings, coin comparison
- **World Bank Open Data** — GDP, inflation, interest rates, population (200+ countries)
- **FRED (St. Louis Fed)** — Fed funds rate, CPI, PCE, M2 money supply, US unemployment
- **Yahoo Finance** — Stocks, ETFs, indices, earnings, dividends, news, sector rotation, VIX/DXY

No sign-up. No billing. Just data.

## Tools (93 total)

### Forex (5)
- `get_exchange_rate` — Real-time rate between two currencies
- `convert_currency` — Convert to multiple currencies at once
- `get_historical_rates` — Historical rates over a date range
- `get_rate_trend` — Exchange rate trend for last N days
- `list_supported_currencies` — All supported currency codes

### Crypto (4)
- `get_crypto_price` — Real-time price + 24h stats for any Binance pair
- `get_crypto_market` — Top N coins ranked by market cap
- `get_crypto_historical` — OHLCV candles (daily, 4h, hourly)
- `compare_crypto` — Side-by-side comparison of multiple coins

### Macro Economics — World Bank (7)
- `get_gdp` — GDP (total or per capita) for any country
- `get_inflation` — Annual CPI inflation rate
- `get_macro_overview` — GDP + inflation + unemployment in one call
- `compare_gdp_growth` — GDP growth comparison across countries
- `get_interest_rate` — Lending interest rate history
- `compare_interest_rates` — Multi-country interest rate comparison
- `compare_population` — Population trends across countries

### US Federal Reserve — FRED (5) *(optional free API key)*
- `get_fed_funds_rate` — Federal funds rate history + current value
- `get_us_cpi` — US CPI + YoY change
- `get_us_pce` — PCE price index vs 2% Fed target
- `get_us_m2` — M2 money supply + MoM/YoY changes
- `get_us_unemployment` — US unemployment rate history

### Commodities (2)
- `get_commodity_price` — Gold price (USD/oz via PAXG)
- `get_commodity_prices` — Silver, oil, copper, natural gas, wheat

### Stock Indices (2)
- `get_stock_index` — Current level + daily change for major indices
- `compare_stock_indices` — Side-by-side global index comparison

### ETFs & Backtesting (3)
- `get_etf_info` — Current price + stats for any ETF
- `get_index_history` — Historical OHLCV for indices and ETFs
- `backtest_buy_hold` — Buy-and-hold return calculator

### Portfolio Analytics (3)
- `get_asset_correlation` — Pearson correlation matrix for 2-6 assets
- `get_portfolio_volatility` — Annualized return, volatility, Sharpe ratio, max drawdown
- `get_fear_greed_index` — Crypto Fear & Greed Index + 7-day history

### Dividend Analysis (1)
- `get_dividend_info` — Trailing yield, payout ratio, ex-dividend date, 5-yr avg

### Sector Rotation (1)
- `compare_sectors` — All 11 S&P 500 sectors ranked by performance

### Stock Fundamentals (1)
- `get_stock_summary` — P/E, EPS, market cap, 52-week range, revenue growth, ROE

### Earnings (2)
- `get_earnings_calendar` — Upcoming earnings with EPS estimates
- `get_batch_earnings` — Batch earnings lookup for a watchlist

### News (1)
- `get_stock_news` — Latest headlines for any ticker

### Market Sentiment (1)
- `get_market_sentiment` — VIX + DXY + 10Y/2Y Treasury yields in one call

### SEC EDGAR (3)
- `get_sec_filings` — Recent 10-K, 10-Q, 8-K filings with direct SEC URLs
- `get_insider_trades` — Form 4 insider buy/sell filings for any ticker
- `get_company_facts` — XBRL financial facts: Revenue, NetIncome, Assets, EPS (historical)

### US Treasury (1)
- `get_treasury_yield_curve` — Full yield curve (1M–30Y), normal vs inverted, 10Y-3M spread

### Options Chain (1) *(NEW in v1.3.0)*
- `get_options_chain` — Calls + puts: strike, bid/ask, volume, open interest, IV, ITM flag. Top 10 by OI per side.

### Institutional Holdings / 13F (1) *(NEW in v1.3.0)*
- `get_institutional_holdings` — Top 10 institutional holders, top 5 mutual fund holders, % held by insiders/institutions

### Historical Treasury Yields (1) *(NEW in v1.3.0)*
- `get_historical_treasury_yields` — Any maturity (1M–30Y) over any date range, with min/max/mean stats

### Analyst Ratings (1) *(NEW in v1.4.0)*
- `get_analyst_ratings` — Analyst consensus (buy/hold/sell count), price target (current/high/low/mean/median), last 10 upgrades/downgrades with analyst firm names

### Short Interest (1) *(NEW in v1.4.0)*
- `get_short_interest` — Shares short, days-to-cover, % of float short, MoM change, squeeze risk level (low/moderate/high/extreme)

### FOMC Economic Calendar (1) *(NEW in v1.4.0)*
- `get_economic_calendar` — Full-year FOMC meeting schedule: dates, SEP (dot plot) sessions, statement and minutes release dates, next upcoming meeting countdown

### DeFi TVL — DefiLlama (1) *(NEW in v1.4.0)*
- `get_crypto_defi_tvl` — Any DeFi protocol's TVL + 30-day history + chain breakdown, or Top 20 protocols ranked by TVL

### Macro Dashboard (1) *(NEW in v1.5.0)*
- `get_macro_dashboard` — VIX, DXY, S&P 500, 10Y/2Y yields, spread, Fear & Greed Index, macro regime label (risk-on/off/neutral) in one call

### Earnings Surprise (1) *(NEW in v1.5.0)*
- `get_earnings_surprise` — EPS surprise % per quarter (beat/miss/in-line), trailing beat rate, consensus vs actual over last N quarters

### Insider Sentiment (1) *(NEW in v1.5.0)*
- `get_insider_sentiment` — Form 4 aggregate: 90-day net buy/sell sentiment (bullish/bearish/neutral), top 3 insider transactions

### Currency Carry Trade (1) *(NEW in v1.5.0)*
- `get_currency_carry` — Interest rate differential between two currencies, spot rate, carry label (high/moderate/low/negative), trade viability assessment, 8 EM fixed rates (TRY, BRL, MXN, ZAR, INR, IDR, HUF, CZK)

### Stock Screener (1) *(NEW in v1.6.0)*
- `get_stock_screener` — Filter S&P 500 universe (80 stocks, all 11 sectors) by P/E ratio, dividend yield, market cap, sector, price range. ThreadPoolExecutor parallel fetch. Returns top matches sorted by market cap.

### Unusual Options Flow (1) *(NEW in v1.6.0)*
- `get_options_flow` — Detect smart money positioning via unusual options activity. Put/Call volume & OI ratios, sentiment signal (BULLISH/BEARISH/NEUTRAL), top unusual contracts sorted by notional value ($). Covers nearest 3 expiration dates.

### Earnings Call Sentiment (1) *(NEW in v1.6.0)*
- `get_earnings_call_sentiment` — NLP sentiment analysis on recent earnings-related news headlines. Keyword-based positive/negative score (-100 to +100), guidance signal (RAISED/LOWERED/MAINTAINED/UNKNOWN), top 5 recent earnings news with links.

### Economic Surprise Index (1) *(NEW in v1.7.0)*
- `get_economic_surprise_index` — ESI proxy for US (6-indicator composite: S&P500/VIX/10Y/Oil/Gold/USD) and 10 countries (ETF momentum proxy). Returns ESI score (-100 to +100), regime (STRONG_POSITIVE/SLIGHTLY_POSITIVE/NEUTRAL/SLIGHTLY_NEGATIVE/STRONG_NEGATIVE), per-indicator BEAT/MISS/IN_LINE. No API key required.

### Sector Momentum (1) *(NEW in v1.7.0)*
- `get_sector_momentum` — 11 SPDR S&P 500 sector ETFs (XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLRE/XLB/XLC) ranked by N-day return. Returns top 3 / bottom 3 sectors, rotation signal (RISK_ON/RISK_OFF/COMMODITY_LED/MIXED), vs SPY benchmark. period_days: 5/10/20/60.

### Market Breadth (1) *(NEW in v1.8.0)*
- `get_market_breadth` — S&P 100 proxy (100 stocks) batch analysis. Advance/Decline ratio, 52W High/Low counts, % above 200-day MA. Composite breadth score 0-100 with regime label (VERY_BULLISH/BULLISH/NEUTRAL/BEARISH/VERY_BEARISH). Identifies underlying market health beyond price indices.

### Volatility Surface (1) *(NEW in v1.8.0— premium tool)*
- `get_volatility_surface` — Options IV surface for any ticker. ATM call IV per expiry (up to 8 dates), OTM put/call IV skew, term structure (short/mid/long-term), put/call skew signal (PUT_SKEW/CALL_SKEW/FLAT). Annualized IV in %. Useful for detecting tail risk pricing and hedging cost.

### FX Volatility (1) *(NEW in v1.9.0— premium tool)*
- `get_fx_volatility` — FX pair realized volatility analysis. 10/30/60/252-day annualized RV as proxy for implied vol and hedging cost. Covers 12 pairs (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP, USDMXN, USDBRL, USDINR, USDKRW). Vol regime (VERY_LOW to HIGH) and trend (RISING/FALLING/STABLE). 52W spot range.

### Credit Spreads (1) *(NEW in v1.9.0)*
- `get_credit_spreads` — US credit market spread direction analysis using bond ETF proxies (LQD/HYG/EMB vs IEF). 30/60d relative performance to detect spread widening vs tightening. Credit cycle regime (RISK_ON/RISK_OFF/CAUTION/NEUTRAL). 52W positioning for each ETF. Note: actual OAS in bps requires FRED API key.

### Global Equity Heatmap (1) *(NEW in v2.0.0)*
- `get_global_equity_heatmap` — 1-day, 1-week, 1-month USD returns for 20 major country equity indices (12 DM + 8 EM). Top 3 best/worst markets per period. DM vs EM aggregate with rotation signal (DM_OUTPERFORMING / EM_OUTPERFORMING / NEUTRAL). ETF proxies via Yahoo Finance, no API key required.

### Commodity Correlation (1) *(NEW in v2.0.0)*
- `get_commodity_correlation` — Pearson correlation matrix for 6 commodities (Gold/Silver/WTI Oil/Copper/Wheat/Natural Gas) vs each other and vs SPY/TLT/DXY. Configurable rolling window (30–252 days). Commodity cycle regime (RISK_ON / INFLATION_HEDGE / DEFLATION_RISK / RISK_OFF / MIXED). 1M recent performance per commodity.

### Earnings Whisper (1) *(NEW in v2.1.0)*
- `get_earnings_whisper` — Historical EPS surprise pattern for any ticker: past 4 quarters of actual vs consensus EPS, BEAT/MISS/IN_LINE classification, post-earnings price reaction (1-day %), beat rate, avg surprise %, whisper gap signal (STRONG_BEAT_TENDENCY / MILD_BEAT_TENDENCY / NEUTRAL / STRONG_MISS_TENDENCY). Identifies whether the market prices in a "whisper number" above consensus. Advanced tool tier.

### Options Skew Monitor (1) *(NEW in v2.1.0)*
- `get_options_skew_monitor` — Real-time put-call skew for SPY, QQQ, IWM: 25-delta proxy skew (OTM put IV minus OTM call IV at ~5% from spot), ATM IV, put-call IV ratio, per-index skew regime (ELEVATED_TAIL_RISK / COMPLACENT / NORMAL), composite cross-index signal. Identifies market-wide tail risk pricing vs complacency. Premium tool tier.

### Factor Exposure (1) *(NEW in v2.2.0)*
- `get_factor_exposure` — Fama-French 5-factor OLS regression for any ticker using ETF proxies: Market (SPY), Size (IWM−SPY), Value (IVE−IVW), Momentum (MTUM), Quality (QUAL). Returns factor betas, daily alpha, R-squared, rolling 63-day correlations, dominant factor, and tilt signal (HIGH_BETA / LOW_BETA / SMALL_CAP_TILT / LARGE_CAP_TILT / VALUE_TILT / GROWTH_TILT / MOMENTUM_TILT / QUALITY_TILT). Uses ~1.5 years of daily returns. Advanced tool tier.

### Yield Curve Dynamics (1) *(NEW in v2.2.0)*
- `get_yield_curve_dynamics` — Real-time US Treasury yield curve analysis via yfinance (^IRX/^FVX/^TNX/^TYX). Returns 3M/5Y/10Y/30Y yields + interpolated 2Y proxy, key spreads in bps (10Y−2Y, 5Y−3M, 10Y−3M, 30Y−10Y), 30/60-day spread change rates, curve shape classification (NORMAL / FLAT / INVERTED / PARTIALLY_INVERTED / HUMPED / STEEP), steepening/flattening trend, and inversion stats (inverted days in last 130d, consecutive inversion day count). Basic tool tier.

### Options IV Term Structure (1) *(NEW in v2.3.0)*
- `get_options_term_structure` — Per-ticker ATM implied volatility term structure across all available expiries, bucketed into standard 30/60/90/120/180/360-day tenors. Returns term structure shape (CONTANGO / BACKWARDATION / FLAT), slope in pp per 30 days, VIX comparison (idiosyncratic vs market-level vol), and vol risk premium signal (RICH / CHEAP / FAIR = short-term ATM IV minus 30-day realized vol). Useful for identifying event risk, carry trades, and mean-reversion setups. Premium tool tier.

### Earnings Season Tracker (1) *(NEW in v2.3.0)*
- `get_earnings_season_tracker` — Real-time S&P 500 earnings season progress using a 60-ticker representative proxy across 11 sectors. Returns aggregate beat/miss/in-line rates, average EPS surprise %, beat signal vs 74% historical avg (STRONG_SEASON / NORMAL_SEASON / WEAK_SEASON / VERY_WEAK_SEASON), sector-level breakdown (beat rate + avg EPS surprise + OUTPERFORMING/IN_LINE/UNDERPERFORMING), and top-3 beats and misses. Season label auto-detected from current month (Q1/Q2/Q3/Q4). Advanced tool tier.

### Macro Regime Monitor (1) *(NEW in v2.4.0)*
- `get_macro_regime_monitor` — Composite 4-axis macro regime classification: Growth (SPY 3M momentum), Inflation (GLD + USO composite), Rates (10Y−2Y spread proxy), Liquidity (LQD − DXY composite). Outputs regime label (GOLDILOCKS / OVERHEATING / STAGFLATION / RECESSION / LATE_CYCLE / GOLDILOCKS_LITE / TRANSITION), regime score 0–100, and concrete asset allocation signal per regime. Uses liquid ETF proxies, no API key required. Basic tool tier.

### Dividend Calendar (1) *(NEW in v2.4.0)*
- `get_dividend_calendar` — Comprehensive dividend calendar for 80 S&P 500 dividend payers across 11 sectors. Returns: upcoming ex-dividend dates within 60 days sorted by proximity, highest yielders, fastest-growing dividends (YoY), sector yield summary, payout ratio safety classification (SAFE < 60% / MODERATE 60–80% / HIGH_PAYOUT > 80%), yield vs 5-year average (ABOVE_AVG / AT_AVG / BELOW_AVG). Filter by sector (Technology, Healthcare, Financials, Utilities, ConsumerStaples, Energy, Industrials, RealEstate, Materials, ConsumerDiscretionary, Communication) or ALL. Advanced tool tier.

### VIX Regime Monitor (1) *(NEW in v2.5.0)*
- `get_vix_regime_monitor` — Real-time VIX stress monitoring. Returns VIX spot, 1-day change, 52-week range, 1-year percentile rank, MA10/20/50-day moving averages, MA trend signal (RISING_STRESS / FALLING_STRESS / ABOVE_AVERAGE / BELOW_AVERAGE), stress regime (PANIC ≥ 35 / ELEVATED 25–35 / NORMAL 18–25 / COMPLACENT < 18), VIX term structure via VXZ mid-term futures ETF proxy (CONTANGO / BACKWARDATION / FLAT), and actionable allocation signal (CONSIDER_HEDGES_OR_CASH / REDUCE_RISK_EXPOSURE / CONSIDER_VOLATILITY_PROTECTION / NORMAL_ALLOCATION). Basic tool tier.

### Insider Trading Radar (1) *(NEW in v2.5.0)*
- `get_insider_trading_radar` — SEC Form 4 cluster buy scanner across 165 S&P 500 stocks in 11 sectors. Identifies insider accumulation signals for the past 30 days: STRONG_ACCUMULATION (3+ buys, net > $500K), ACCUMULATION (2+ buys, net positive), SINGLE_BUY. Returns ranked list of top cluster signals, each with buy/sell transaction counts, total buy/sell dollar value, net insider flow, and individual trade details. Sector summary of total insider buy flow by industry. Filter by sector or ALL. Advanced tool tier.

### ETF Flow Tracker (1) *(NEW in v2.6.0)*
- `get_etf_flow_tracker` — Cross-asset capital flow monitor for 12 major ETFs: SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000), GLD (Gold), TLT (20Y+ Bonds), HYG (High Yield), XLF (Financials), XLE (Energy), XLK (Technology), XLV (Healthcare), EEM (Emerging Markets), UUP (US Dollar). Uses OBV (On-Balance Volume) slope analysis to classify each ETF as STRONG_INFLOW / INFLOW / NEUTRAL / OUTFLOW / STRONG_OUTFLOW. Includes 5d/10d/30d price returns, volume regime (HIGH/NORMAL/LOW), and cross-asset rotation signal (RISK_ON_ROTATION / RISK_OFF_ROTATION / MIXED_FLOWS / NEUTRAL). No API key required. Basic tool tier.

### Options Gamma Exposure — GEX (1) *(NEW in v2.6.0)*
- `get_options_gamma_exposure` — Dealer Gamma Exposure (GEX) calculator for any optionable ticker. Computes Black-Scholes gamma × open interest × 100 (contract multiplier) × spot price for all near-term strikes within ±15% of spot across the two nearest expiries (≤60 DTE). Net GEX = total call GEX − total put GEX. Returns: market_signal (POSITIVE_GEX = price-stabilizing / NEGATIVE_GEX = price-amplifying), GEX flip point (price level where cumulative strike GEX crosses zero), distance to flip in %, top 10 gamma strikes by absolute GEX with CALL_DOMINATED / PUT_DOMINATED classification, gamma wall (highest gamma concentration strike), top-3 strike concentration %, GEX magnitude (EXTREME / HIGH / MODERATE / LOW). Requires only Yahoo Finance options chain. Default ticker: SPY. Premium tool tier.

### Sector Rotation Signal (1) *(NEW in v2.7.0)*
- `get_sector_rotation_signal` — Macro-aware sector rotation model covering all 11 SPDR sector ETFs (XLK/XLV/XLF/XLE/XLI/XLB/XLRE/XLY/XLP/XLU/XLC). Scores each sector by relative performance vs SPY using a weighted composite: 1-month return × 40% + 3-month return × 35% + 6-month return × 25%. Ranks all 11 sectors and assigns positioning: Rank 1-3 = STRONG OVERWEIGHT, 4-5 = MODERATE OVERWEIGHT, 6-7 = NEUTRAL, 8-9 = MODERATE UNDERWEIGHT, 10-11 = STRONG UNDERWEIGHT. Overlays macro context: VIX regime (HIGH_STRESS ≥30 / MODERATE_STRESS 20-30 / LOW_STRESS <20) and 10Y yield regime (HIGH_RATES >4.5% / ELEVATED_RATES 3.5-4.5% / LOW_RATES <3.5%) with actionable rate impact notes. Identifies overall rotation regime: DEFENSIVE_ROTATION (defensive sectors top 3), CYCLICAL_ROTATION (growth/cyclical sectors top 3), VALUE_ROTATION (Energy/Financials leading), MIXED_ROTATION. No API key required. Advanced tool tier.

### Earnings Revision Tracker (1) *(NEW in v2.7.0)*
- `get_earnings_revision_tracker` — Analyst EPS revision momentum tracker for any ticker. Counts analyst upgrades and downgrades over the past 30 and 90 days and classifies the revision direction: RISING (upgrades dominate, >1.5× downgrades, minimum 2 actions), FALLING (downgrades dominate), or STABLE (no clear skew). Signal strength: STRONG (3+ actions in dominant direction) or MODERATE. Includes: upgrade/downgrade counts for 30d and 90d windows, revision ratio % (upgrade share of 90d total — >60% bullish, <40% bearish), recent 5 analyst actions with firm name and grade change (from/to grade), EPS estimate averages for current quarter and next year with YoY growth %, consensus price target (mean/low/high) with upside % to current price, analyst recommendation mean on 1-5 scale with label (STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL). Default ticker: AAPL. Advanced tool tier.

### Short Squeeze Radar (1) *(NEW in v2.8.0)*
- `get_short_squeeze_radar` — Scans 60+ high-short-interest stocks for active squeeze setups. Computes a composite squeeze_score (0-100) per ticker: short % of float × 40 + 1-week price momentum × 30 + 5d/20d volume surge ratio × 30. Risk tiers: EXTREME (≥70), HIGH (≥50), MODERATE (≥30), LOW (<30). Returns per-ticker: company name, sector, short_pct_float, days_to_cover, 1W and 1M price momentum %, volume_surge_ratio, current price. Output includes top-15 candidates ranked by score and a separate extreme_squeeze_alerts list. Universe covers meme stocks (GME, AMC), EV/clean energy (RIVN, NIO, PLUG), crypto-adjacent (MSTR, RIOT, COIN), retail (KSS, JWN, M), biotech (MRNA, NVAX), and media/telecom names. No API key required. Advanced tool tier.

### Put/Call Ratio History (1) *(NEW in v2.8.0)*
- `get_put_call_ratio_history` — Analyzes options market sentiment via put/call ratio across up to 6 expirations (7-90 DTE) for any ticker or ETF. Returns composite P/C ratio from total volume and open interest, contrarian signal (BULLISH_EXTREME / BEARISH_EXTREME / ELEVATED_FEAR / ELEVATED_COMPLACENCY / NEUTRAL), fear/greed proxy score (0=extreme fear, 100=extreme greed), P/C trend across the term structure (NEAR_TERM_FEAR / LONG_TERM_FEAR / FLAT_STRUCTURE), and OI signal (HEAVY_PUT_OI / PUT_LEANING / CALL_LEANING / HEAVY_CALL_OI). Includes benchmark context: normal P/C range and extreme thresholds calibrated separately for index ETFs (SPY, QQQ, IWM, DIA, TLT, GLD) vs individual stocks. Per-expiration breakdown with put/call volume and OI. Contrarian interpretation: extreme put buying signals fear peak (buy signal), extreme call buying signals complacency (sell signal). Configurable period_days (20/30/60/90). Default ticker: SPY. Premium tool tier.

### Institutional Flow Tracker (1) *(NEW in v2.9.0)*
- `get_institutional_flow_tracker` — Tracks institutional ownership flows across 120+ S&P 500 stocks in 11 sectors. For each stock: institutional ownership % (from yfinance major_holders), top institutional holder and stake %, number of institutions holding shares, 3-month price momentum %, 10d/20d volume surge ratio, and a composite flow signal (STRONG_ACCUMULATION / ACCUMULATION / NEUTRAL / DISTRIBUTION / STRONG_DISTRIBUTION). Signal heuristic: high institutional ownership (≥75%) + positive price momentum (≥5%) + volume surge = STRONG_ACCUMULATION. Sector aggregation: SECTOR_ACCUMULATION / MILD_ACCUMULATION / NEUTRAL / MILD_DISTRIBUTION. Overall market signal: INSTITUTIONAL_BUY_PRESSURE / INSTITUTIONAL_SELL_PRESSURE / BALANCED_FLOWS. Returns top 15 accumulation candidates and top 10 distribution candidates. Sector filter supported (Technology / Healthcare / Financials / etc. or ALL). Combine with get_insider_trading_radar() and get_short_squeeze_radar() for full smart-money picture. Advanced tool tier.

### Dark Pool Indicator (1) *(NEW in v2.9.0)*
- `get_dark_pool_indicator` — Estimates off-exchange institutional activity using four proxies that together identify stealth buying/selling. (1) OBV Divergence: price falling while OBV rising = BULLISH_DIVERGENCE (hidden institutional accumulation on dips). (2) VWAP Position: 20-day VWAP vs current price — institutions targeting VWAP for block order execution. (3) Block Trade Proxy: days where volume ≥1.8× 30-day average AND daily range ≤1.5% (tight range + high volume = institutional block at a fixed price, classified BUY if close above midpoint, SELL if below). (4) Accumulation/Distribution line 10-day trend. Composite dark pool signal: STEALTH_ACCUMULATION / STEALTH_DISTRIBUTION / BLOCK_BUYING / BLOCK_SELLING / NO_SIGNAL. Confidence score (bullish/bearish points out of 10). Also returns: volume climax detection (volume spike ≥2.5× 30d avg), 10d and 30d price momentum, average volume comparison 10d vs 30d. Default ticker: SPY. Premium tool tier.

### Options Unusual Activity Scanner (1) *(NEW in v3.0.0)*
- `get_options_unusual_activity_scanner` — Market-wide unusual options sweep scanner covering 100 S&P 500 / high-activity tickers simultaneously. Identifies contracts where volume/OI ratio exceeds threshold (default 3×) AND volume ≥ 500 — the classic signal for new institutional directional positioning (not OI rollover). Returns: UNUSUAL_CALL_SWEEP or UNUSUAL_PUT_SWEEP per contract, strike, expiration, notional USD, implied volatility %, and in-the-money flag. Ranks results by notional USD. Market bias signal: BULLISH_SWEEP_DOMINANCE / BEARISH_SWEEP_DOMINANCE / MILD_CALL_LEAN / MILD_PUT_LEAN / BALANCED_UNUSUAL_FLOW — determined by call vs put notional comparison. Total flagged tickers, count of call/put sweeps, aggregate call/put notional. Configurable min_volume_oi_ratio and top_n. 12-thread parallel scan. Use alongside get_dark_pool_indicator() to cross-validate institutional intent. Premium tool tier.

### Smart Money Composite (1) *(NEW in v3.0.0)*
- `get_smart_money_composite` — Single-ticker smart money scorecard that aggregates 5 independent signals into one SMART_MONEY_SCORE (0–100). Component 1: Dark pool OBV divergence (25 pts) — price vs OBV 10-day slope divergence detects hidden institutional accumulation. Component 2: Institutional ownership % (20 pts) — heldPercentInstitutions from Yahoo Finance. Component 3: Insider trading activity (25 pts) — Form 4 transactions in past 90 days: STRONG_INSIDER_BUYING (3+ buys, net >$500K) → 25 pts; STRONG_INSIDER_SELLING (3+ sells) → −20 pts. Component 4: Short interest (15 pts) — low short % = healthy (15 pts); extreme short % = squeeze potential (10 pts contrarian). Component 5: Options put/call volume ratio (15 pts) — nearest 14–60 DTE expiration; heavy call volume = bullish. Final signal: STRONG_SMART_MONEY_BUY (≥85) / SMART_MONEY_BUY (≥65) / NEUTRAL (≥40) / SMART_MONEY_SELL (≥25) / STRONG_SMART_MONEY_SELL (<25). Full score breakdown with per-component signal label and max points. Advanced tool tier.

### Earnings Surprise vs Sector (1) *(NEW in v3.2.0)*

`get_earnings_surprise_vs_sector(ticker)` — Compare a stock's EPS surprise history vs sector peers. Fetches last 4 quarters of actual vs estimated EPS, calculates average surprise % and beat rate, then benchmarks against 10-15 sector representative stocks. Returns **SECTOR_OUTPERFORMER / IN_LINE / SECTOR_UNDERPERFORMER** with strength (STRONG/MODERATE/MILD) and trend (IMPROVING/STABLE/DECLINING). Advanced tier.

### 52-Week High/Low Momentum (1) *(NEW in v3.2.0)*

`get_52w_high_low_momentum()` — Scans 150-ticker S&P 500 proxy universe across all 11 GICS sectors. Counts stocks within 3% of 52-week highs vs lows. Net ratio drives regime: **STRONG_BULL_MOMENTUM / BULLISH_MOMENTUM / NEUTRAL_MOMENTUM / BEARISH_MOMENTUM / STRONG_BEAR_MOMENTUM**. Sector-level LEADING/NEUTRAL/LAGGING classification. Top-5 nearest highs and lows. Basic tier.

### Options IV Percentile (1) *(NEW in v3.3.0)*

`get_options_iv_percentile(ticker)` — Compares current ATM implied volatility (or 30-day realized vol proxy) against the full 1-year historical IV distribution for any ticker. **IV Percentile Rank** = % of past trading days where IV was below current level. **IV Rank** = position within the 52-week IV range. Signal: **IV_ELEVATED** (percentile ≥80 → SELL_PREMIUM) / **IV_NORMAL** (20–79) / **IV_DEPRESSED** (≤20 → BUY_PREMIUM). Signal strength: HIGH / MODERATE / NEUTRAL. Strategy detail: covered calls / credit spreads (elevated) or long options / pre-catalyst straddles (depressed). Historical RV stats: 30d current, 3m avg, 6m avg, 1y avg, min, max. Advanced tool tier.

### Cross-Asset Momentum (1) *(NEW in v3.3.0)*

`get_cross_asset_momentum()` — Simultaneous momentum analysis across 7 major asset classes: SPY (US equities), QQQ (tech/growth), IWM (small caps), TLT (long bonds), GLD (gold), UUP (USD), BTC-USD (Bitcoin). Returns 1W/1M/3M return rankings and a weighted composite rank (1W×30% + 1M×40% + 3M×30%). **Risk-ON/Risk-OFF regime scoring**: equity+crypto momentum vs bonds+gold+USD momentum → **STRONG_RISK_ON / RISK_ON / MIXED / RISK_OFF / STRONG_RISK_OFF** with net score -8 to +8. Momentum leaders and laggards (top-3 each). Asset allocation signal: "Overweight: SPY/QQQ/IWM. Underweight: TLT/GLD." Per-asset: current price, returns, 20d momentum %, 20d vol %, Sharpe proxy, composite rank. Basic tool tier.

### Relative Strength Ranking (1) *(NEW in v3.5.0)*

`get_relative_strength_ranking(tickers)` — Ranks a custom list of up to 20 tickers by composite momentum vs SPY. Calculates 1W/1M/3M/6M price returns + RS score (excess return vs SPY benchmark) per ticker. **Composite momentum score**: weighted average 1W×20% + 1M×30% + 3M×30% + 6M×20%. **RS composite vs SPY**: same weighted structure applied to excess returns. Momentum regime per ticker: **STRONG_OUTPERFORMER** (composite ≥15% + RS ≥+5%) / **OUTPERFORMER** / **NEUTRAL** / **UNDERPERFORMER** / **STRONG_UNDERPERFORMER** (composite ≤-10%). Full ranked table with current price, all period returns, RS scores, composite score. Top-5 momentum leaders and bottom-5 laggards highlighted. Market context (BULL_MARKET / BEAR_MARKET / SIDEWAYS) from SPY 30d return. Strategy guide: long candidates (top-ranked momentum + positive RS), avoid-or-short (bottom-ranked), rotation signal (growth vs defensive shift in top leaders). Use to identify individual stock momentum within a sector or a watchlist. Advanced tool tier.

### Momentum Factor Screen (1) *(NEW in v3.6.0)*

`get_momentum_factor_screen(top_n)` — Screens 140+ S&P 500 proxy tickers across 11 GICS sectors using the classic **12-1 momentum factor** (12-month return minus 1-month return — the standard academic momentum anomaly). Per-stock output: momentum_12_1 score, 12M/6M/3M/1M individual returns, momentum quintile label (**HIGH_MOMENTUM** / **NEUTRAL_MOMENTUM** / **LOW_MOMENTUM**, top/bottom 30% cutoff), rank and percentile. Market-wide regime: **STRONG_MOMENTUM_MARKET** / **MOMENTUM_MARKET** / **MIXED_MOMENTUM** / **WEAK_MOMENTUM** / **MOMENTUM_CRASH**. Sector momentum ranking: avg momentum per sector with LEADING/OUTPERFORMING/NEUTRAL/UNDERPERFORMING/LAGGING. Strategy guide for each regime: long HIGH_MOMENTUM in bull runs, mean-reversion plays in MOMENTUM_CRASH, sector rotation signals. ThreadPoolExecutor 12 parallel. Advanced tool tier.

### Economic Indicators Dashboard (1) *(NEW in v3.6.0)*

`get_economic_indicators_dashboard(country)` — Country-level macro health scorecard using ETF proxies for 13 countries (US/EU/JP/CN/KR/GB/CA/AU/IN/BR/MX/DE/FR). Five components: **(1)** Growth proxy (25 pts) — country equity ETF 1Y + 3M return as GDP momentum signal. **(2)** Inflation proxy (20 pts) — GLD + USO composite 3M return; moderate = STABLE_PRICES, high = HIGH_INFLATION_RISK, negative = DEFLATION_RISK. **(3)** Employment/activity (20 pts) — XLY (discretionary) vs XLP (staples) 3M spread: STRONG_EMPLOYMENT / HEALTHY / NEUTRAL / WEAKENING / RECESSIONARY. **(4)** Fiscal/credit health (20 pts) — HYG vs IEF credit spread + VIX penalty adjustment: STRONG_FISCAL_HEALTH / HEALTHY_CREDIT / NEUTRAL / CREDIT_STRESS / CREDIT_CRISIS. **(5)** Currency/external (15 pts) — country currency ETF 1Y return: STRONG_CURRENCY / APPRECIATING / STABLE / DEPRECIATING / WEAK_CURRENCY. Composite score 0–100 with regime **STRONG** (≥80) / **HEALTHY** (≥65) / **MIXED** (≥45) / **WEAK** (≥30) / **DISTRESSED** (<30) and actionable asset allocation signal. Basic tool tier.

### Earnings Quality Score (1) *(NEW in v3.7.0)*

`get_earnings_quality_score(ticker)` — Earnings quality scorecard that identifies cash-backed vs accounting-driven earnings. **4 components**: **(1)** Cash Flow Quality (30 pts) — accruals ratio = (Net Income - Operating Cash Flow) / avg total assets. Negative accruals = earnings backed by real cash: **EXCELLENT_CASH_BACKING** / **STRONG_CASH_BACKING** / **MODERATE_CASH_BACKING** / **WEAK_CASH_BACKING** / **ACCRUAL_WARNING**. **(2)** Earnings Persistence (25 pts) — coefficient of variation of 4-year net income trend. Low variance + improving = **HIGHLY_PERSISTENT** / **MODERATELY_PERSISTENT** / **LOW_PERSISTENCE** / **ERRATIC_EARNINGS**. **(3)** Revenue Growth Momentum (25 pts) — YoY and 3-year revenue CAGR: **STRONG_REVENUE_GROWTH** (≥20%) / **HEALTHY_GROWTH** (≥10%) / **MODERATE_GROWTH** (≥3%) / **FLAT_REVENUE** / **REVENUE_DECLINING**. **(4)** ROE Quality (20 pts) — return on equity from yfinance: **EXCELLENT_ROE** (≥20%) / **STRONG_ROE** / **MODERATE_ROE** / **LOW_ROE** / **NEGATIVE_ROE**. Composite score 0–100: **HIGH_QUALITY** (≥75) / **MODERATE_QUALITY** (50–74) / **LOW_QUALITY** (30–49) / **VERY_LOW_QUALITY** (<30). Advanced tool tier.

### Market Internals Dashboard (1) *(NEW in v3.7.0)*

`get_market_internals_dashboard()` — Comprehensive market health dashboard scanning a 100-stock S&P 500 proxy universe in parallel. **Five indicators**: **(1)** Advance/Decline proxy — 10-day returns to classify advancing vs declining stocks, A/D ratio, signal STRONG_ADVANCE / ADVANCE / NEUTRAL / DECLINE / STRONG_DECLINE. **(2)** New Highs / New Lows — stocks within 3% of 52-week high vs low, net % and NH/NL ratio, signal STRONG_NEW_HIGHS / NEW_HIGHS_DOMINANT / BALANCED / NEW_LOWS_DOMINANT / STRONG_NEW_LOWS. **(3)** % Above MA50 and MA200 — short-term breadth signal STRONG_BREADTH / HEALTHY_BREADTH / NEUTRAL_BREADTH / WEAK_BREADTH / OVERSOLD_BREADTH; long-term signal LONG_TERM_BULL / BULL_TREND / TRANSITION / BEAR_TREND / LONG_TERM_BEAR. **(4)** McClellan Oscillator proxy — 10d vs 30d advance-decline breadth differential: OVERBOUGHT / POSITIVE_MOMENTUM / NEUTRAL / NEGATIVE_MOMENTUM / OVERSOLD. **(5)** Bullish Percent Index proxy — % of stocks above 200d MA as BPI: OVERBOUGHT_ZONE / BULL_CONFIRMED / NEUTRAL_ZONE / BEAR_CONFIRMED / OVERSOLD_ZONE. Composite health score 0–100 → **HEALTHY** / **NEUTRAL** / **DETERIORATING** / **OVERSOLD** / **VERY_OVERSOLD** with action guidance. Basic tool tier.

### Fear & Greed Composite Index (1) *(NEW in v3.5.0)*

`get_fear_greed_composite()` — 7-indicator composite replicating CNN Fear & Greed Index using fully public data (no API key required). Total score 0–100: **EXTREME_FEAR** (<20) → contrarian buy zone / **FEAR** (20–40) / **NEUTRAL** (40–60) / **GREED** (60–80) / **EXTREME_GREED** (>80) → contrarian sell zone. The 7 components: **(1)** VIX Regime (20 pts): VIX < 13 = extreme greed, > 32 = extreme fear. **(2)** 52W High/Low Breadth (20 pts): scans 50-ticker S&P 100 proxy, net % near 52W highs vs lows. **(3)** Safe Haven Demand (15 pts): TLT vs SPY 30d relative performance, inverted (bonds outperforming = fear). **(4)** Put/Call Ratio (15 pts): SPY nearest 30d expiry composite P/C, inverted (heavy puts = fear). **(5)** Junk Bond Demand (15 pts): HYG vs IEF 30d relative return (junk outperforming = greed). **(6)** Market Momentum (10 pts): SPY price vs 125-day moving average. **(7)** Stock Price Breadth (5 pts): RSP equal-weight ETF vs SPY 30d divergence (broad participation = greed). Full per-component breakdown with score, max score, current values. Recommended action: REDUCE_RISK / HOLD_OR_TRIM / BALANCED / WATCH_FOR_ENTRY / AGGRESSIVE_BUY_ZONE. Basic tool tier.

### Earnings Date Countdown (1) *(NEW in v3.4.0)*

`get_earnings_date_countdown(ticker)` — Next earnings date with position timing guide. Fetches next announcement date from yfinance calendar, calculates **days_until_earnings**, and maps to timing signal: **EARNINGS_PASSED_OR_TODAY / IMMEDIATE_PLAY** (≤3 days) / **PRIME_ENTRY_WINDOW** (3–10 days, ideal for straddles before IV crush) / **EARLY_ENTRY** (10–21 days) / **WATCH_LIST** (21–45 days) / **TOO_EARLY** (>45 days). Options-based expected move from ATM straddle cost/spot price. Historical 4-quarter EPS beat/miss breakdown with surprise %, beat rate %, avg surprise %. Pre-earnings 5-day price drift average (upward vs downward bias into earnings). Earnings tendency: **STRONG_BEAT_TENDENCY / MILD_BEAT_TENDENCY / NEUTRAL / STRONG_MISS_TENDENCY / MILD_MISS_TENDENCY**. Full strategy guide: straddle entry timing, iron condor setup, directional trade bias, IV crush risk warning. Advanced tool tier.

### Sector ETF vs SPY Beta (1) *(NEW in v3.4.0)*

`get_sector_etf_vs_spy_beta()` — 1-year OLS beta calculation for all 11 SPDR sector ETFs (XLK/XLY/XLC/XLF/XLE/XLI/XLB/XLRE/XLV/XLP/XLU) vs SPY. Beta = cov(sector, SPY) / var(SPY) using 252 daily return observations. Per-sector output: **beta_1y**, **beta_label** (HIGH_BETA ≥1.3 / ABOVE_AVERAGE ≥1.05 / MARKET_NEUTRAL 0.85–1.05 / BELOW_AVERAGE 0.65–0.85 / LOW_BETA <0.65), annualized volatility %, SPY correlation, 1W/1M/3M return. Sectors ranked from highest to lowest beta. High-beta top-3 and low-beta bottom-3 highlighted. Market trend (STRONG_BULL/MILD_BULL/SIDEWAYS/MILD_BEAR/STRONG_BEAR) from SPY 1M/3M returns drives **rotation_guidance**: in bull markets favor XLK/XLY/XLC (amplified gains); in bear markets rotate to XLU/XLP/XLV (capital preservation). Tactical guide: leverage calc, offensive vs defensive sector allocation. ThreadPoolExecutor 12 parallel. Basic tool tier.

### Options Flow Heatmap (1) *(NEW in v3.1.0)*
- `get_options_flow_heatmap` — Sector-level options flow aggregation heatmap covering all 11 GICS sectors. Analyzes 44 representative tickers (4 per sector: Technology/Healthcare/Financials/Energy/Industrials/Materials/Real Estate/Consumer Discretionary/Consumer Staples/Utilities/Communication Services). For each sector: aggregates total call and put volume, detects unusual sweeps (volume/OI ≥ 3×), calculates put/call ratio. Sector flow signal: STRONG_BULLISH (P/C < 0.60 + call sweep dominance) / BULLISH (P/C < 0.85) / NEUTRAL / BEARISH (P/C > 1.15) / STRONG_BEARISH (P/C > 1.50 + put sweep dominance). Sweep bias = unusual_calls − unusual_puts per sector. Overall market flow regime: BROAD_BULLISH_FLOW / MODERATE_BULLISH_FLOW / MIXED_FLOW / MODERATE_BEARISH_FLOW / BROAD_BEARISH_FLOW. Returns most bullish 3 sectors and most bearish 3 sectors ranked by P/C ratio. Use alongside get_sector_rotation_signal() to cross-validate momentum vs options positioning. Advanced tool tier.

### Dividend Safety Screen (1) *(NEW in v3.8.0)*

`get_dividend_safety_screen(sector)` — Screens 80+ S&P 500 dividend-paying stocks across 9 sectors for dividend sustainability and cut risk. **4-component scorecard per stock**: **(1)** Payout Ratio (30 pts) — ≤40% VERY_LOW_PAYOUT / ≤60% SUSTAINABLE_PAYOUT / ≤75% ELEVATED_PAYOUT / ≤90% HIGH_PAYOUT / >110% UNSUSTAINABLE_PAYOUT. **(2)** FCF Coverage Ratio (35 pts) — FCF per share / annual dividend rate: ≥3× EXCELLENT_FCF_COVERAGE / ≥2× STRONG / ≥1.3× ADEQUATE / ≥1.0× TIGHT / <0.7× FCF_DEFICIT_RISK. Falls back to earnings coverage when FCF unavailable. **(3)** Dividend Yield Quality (20 pts) — 1.5–4% ATTRACTIVE_YIELD / <1.5% LOW_YIELD / 4–6% HIGH_YIELD_WATCH / >6% YIELD_TRAP_RISK. **(4)** Beta Stability (15 pts) — ≤0.6 very stable / ≤0.9 stable / ≤1.2 moderate / >1.2 volatile. Composite score 0–100: **SAFE_DIVIDEND** (≥65) / **AT_RISK** (40–64) / **DIVIDEND_CUT_RISK** (<40). Returns top-10 safe picks, at-risk watch list, high-risk names, and sector safety ranking sorted by safety rate %. Optional sector filter (ALL or specific sector). ThreadPoolExecutor 12 parallel. Advanced tool tier.

### Earnings Growth Tracker (1) *(NEW in v4.0.0)*

`get_earnings_growth_tracker(ticker)` — Tracks EPS and Revenue YoY growth rates across the last 4 quarters. **Acceleration detection**: compares recent 2Q average growth vs prior 2Q average to calculate delta. **EPS regime** (4 quarters of yfinance earnings_history): ACCELERATING_GROWTH (delta >3% & recent >0%) / STEADY_GROWTH (|delta| ≤5% & avg >5%) / DECELERATING (delta <-5%) / STALLING (avg <0%) / DECLINING (avg <-10%). **Revenue regime**: same classification from quarterly income statement. **Composite score** 0–100 = EPS score ×60% + Revenue score ×40%. **Composite signal**: STRONG_GROWTH_ACCELERATION (≥80) / HEALTHY_GROWTH (≥65) / MIXED_GROWTH (≥45) / WEAKENING_GROWTH (≥25) / GROWTH_CONCERN (<25). Returns quarterly breakdown with YoY %, acceleration delta, and strategy guidance for GARP screening. Advanced tool tier.

### Liquidity Score (1) *(NEW in v4.0.0)*

`get_liquidity_score(ticker)` — Composite 0–100 liquidity assessment to guide position sizing. **4-component scoring**: **(1)** Market cap tier (30 pts) — MEGA_CAP ≥$200B / LARGE_CAP ≥$10B / MID_CAP ≥$2B / SMALL_CAP ≥$300M / MICRO_CAP. **(2)** Avg Daily Dollar Volume 30d (35 pts) — ULTRA_HIGH ≥$1B / HIGH ≥$100M / MODERATE ≥$10M / LOW ≥$1M / VERY_LOW. **(3)** Amihud Illiquidity Ratio (20 pts) — mean(|daily log return| / dollar volume) × 1e9 bps; HIGHLY_LIQUID <0.1 / LIQUID <1.0 / MODERATE <5.0 / ILLIQUID <20 / VERY_ILLIQUID. **(4)** Bid-Ask Spread Proxy (15 pts) — estimated from 30d realized volatility × 0.003 (rough Kyle lambda proxy). **Signal**: HIGHLY_LIQUID (≥80) / LIQUID (≥60) / MODERATE (≥40) / ILLIQUID (≥20) / VERY_ILLIQUID (<20). Returns position sizing guidance with easy entry/exit estimate in $M, volume trend (VOLUME_SURGE / ABOVE_AVERAGE / NORMAL / BELOW_AVERAGE / VOLUME_DRY_UP), float shares, and full score breakdown. Advanced tool tier.

### Quality Factor Screen (1) *(NEW in v4.0.0)*

`get_quality_factor_screen(top_n=20)` — Screens 150-ticker S&P 500 proxy universe across 11 sectors for high-quality stocks using a **5-component quality scorecard**. **(1)** ROE Quality (25 pts) — ≥20%=25 / ≥15%=20 / ≥10%=14 / ≥0%=6 / negative=0. **(2)** Debt/Equity Safety (25 pts) — D/E ≤0.3=25 / ≤0.6=20 / ≤1.0=14 / ≤2.0=6 / >2.0=0. **(3)** EPS Growth CAGR (20 pts) — 3yr CAGR ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0. **(4)** FCF Margin (20 pts) — FCF/Revenue ≥20%=20 / ≥12%=16 / ≥6%=11 / ≥0%=5 / negative=0. **(5)** Earnings Stability (10 pts) — quarterly NI positive rate ≥90%=10 / ≥75%=8 / ≥60%=5 / ≥40%=2 / <40%=0. **Composite 0–100**: QUALITY_ELITE (≥85) / QUALITY_SOLID (≥65) / QUALITY_MIXED (≥40) / LOW_QUALITY (<40). Returns top-N quality picks with score breakdown, QUALITY_ELITE names list, lowest quality candidates, sector concentration analysis, and market-wide quality signal HIGH_QUALITY_MARKET / MIXED_QUALITY_MARKET / LOW_QUALITY_MARKET. Advanced tool tier.

### Capital Allocation Score (1) *(NEW in v4.0.0)*

### Management Quality Score (1) *(NEW in v4.1.0)*

Scores management quality across 5 dimensions: CEO tenure proxy, ROE improvement trend (3-4yr history, IMPROVING adds +5pts), R&D efficiency relative to gross margin tier (HEALTHY_RD / HIGH_RD_INVESTMENT / NO_RD_DATA), SBC discipline (stock-based compensation / revenue: MINIMAL_DILUTION ≤1% to HIGH_DILUTION_RISK ≥8%), operating margin stability (coefficient of variation over 4 years, CV ≤10% = HIGHLY_STABLE). Composite 0-90 → EXCELLENT_MANAGEMENT ≥75 / GOOD_MANAGEMENT ≥58 / MIXED_MANAGEMENT ≥40 / POOR_MANAGEMENT <40. Action guidance per tier.

### Competitive Moat Score (1) *(NEW in v4.1.0)*

Quantifies competitive moat width across 5 components: gross margin stability over 5 years (ELITE_MARGIN_FORTRESS ≥60% stable = 25pts, CONTRACTING trend -3pts penalty), operating leverage ratio (op income growth / revenue growth ≥3x = HIGH_OPERATING_LEVERAGE = 20pts), pricing power proxy (current vs historical gross margin delta: STRONG_PRICING_POWER +5pp = 20pts), market position (mega-cap ≥$200B = DOMINANT_MARKET_POSITION = 15pts, adjusted for revenue growth), R&D IP moat (R&D intensity × gross margin quality composite: DEEP_IP_MOAT ≥0.15 = 20pts). Composite 0-100 → WIDE_MOAT ≥78 / NARROW_MOAT ≥58 / NO_MOAT ≥38 / STRUCTURAL_DISADVANTAGE <38 with action guidance.

### Earnings Revision Momentum (1) *(NEW in v4.2.0)*

`get_earnings_revision_momentum(ticker)` — Tracks analyst EPS upgrade/downgrade momentum over **30/60/90-day sliding windows**. Weighted revision score = 30d×50% + 60d incremental×30% + 90d incremental×20%, normalized to 0-100. Signals: **REVISION_MOMENTUM_STRONG** (≥80, analysts aggressively upgrading) / **REVISION_MOMENTUM_POSITIVE** (≥55, more upgrades than downgrades) / **REVISION_MOMENTUM_NEUTRAL** (≥35) / **REVISION_MOMENTUM_NEGATIVE** (≥15, estimates being cut) / **REVISION_DETERIORATING** (<15, significant downgrade wave). Also includes: analyst consensus (STRONG_ANALYST_CONSENSUS_BUY/ANALYST_HOLD/ANALYST_CONSENSUS_SELL), coverage quality (LOW/MODERATE/HIGH_COVERAGE), price target mean/high/low with % upside, forward vs trailing EPS with growth %, recent 6 analyst actions with firm name and grade change. Action guide per signal tier. Advanced tool tier.

### Peer Comparison (1) *(NEW in v4.3.0)*

`get_peer_comparison(ticker)` — Ranks ticker vs **10-15 sector peers** on 6 fundamental metrics: P/E ratio, P/B ratio, EV/EBITDA, ROE %, revenue growth %, and gross margin %. Computes percentile rank vs peer universe for each metric (0=worst, 100=best in peer group). Composite percentile from all 6 metrics. **Overall signals**: PREMIUM_TO_PEERS (≥75th pctile) / MILD_PREMIUM (≥55) / FAIR_VALUE_VS_PEERS (≥45) / MILD_DISCOUNT (≥25) / CHEAP_VS_PEERS (<25). Sector peer universes defined for all 11 GICS sectors with 13-14 S&P 500 representative peers. Strongest/weakest peers by composite fundamentals. Action guide per signal. Use with `get_valuation_composite()` for absolute + relative valuation context. Advanced tool tier.

### Macro Sensitivity Score (1) *(NEW in v4.3.0)*

`get_macro_sensitivity_score(ticker)` — 4-component **macro risk scorecard** measuring how sensitive a stock is to macro regime shifts. **(1) Rate Sensitivity (25 pts)** — debt/equity ratio as leverage proxy: ≤0.2=25 MINIMAL_LEVERAGE / ≤1.0=14 MODERATE / ≥2.0=2 EXTREME_RATE_RISK + TLT 1Y price correlation as duration proxy. **(2) Dollar Sensitivity (20 pts)** — UUP (dollar ETF) 1-year price correlation: negative corr = multinational revenue hurt by strong dollar (HIGH_USD_SENSITIVITY) / positive = STRONG_USD_BENEFICIARY. **(3) Inflation Sensitivity (20 pts)** — gross margin ≥60%=16 HIGH_MARGIN_PRICING_POWER / Energy/Materials = INFLATION_BENEFICIARY=18 / thin margins ≥15%=7 INFLATION_VULNERABLE + gold/oil correlation context. **(4) Economic Cycle Sensitivity (35 pts)** — 1-year OLS beta vs SPY: ≥1.5=5 VERY_HIGH_BETA / ≥0.9=20 MARKET_BETA / ≤0.6=35 VERY_LOW_BETA_HIGHLY_DEFENSIVE + XLY vs XLU correlation spread → cyclicality bias STRONGLY_CYCLICAL to STRONGLY_DEFENSIVE. **Composite 0-100**: LOW_MACRO_SENSITIVITY (≥75) / MODERATE_LOW (≥58) / MODERATE (≥42) / HIGH_MACRO_SENSITIVITY (≥28) / EXTREME_MACRO_SENSITIVITY (<28). Risk factors list identifies specific vulnerabilities. Advanced tool tier.

### Business Cycle Positioning (1) *(NEW in v4.2.0)*

`get_business_cycle_positioning(sector)` — Detects current macro business cycle phase using **4 real-time ETF proxies**. **(1)** PMI Proxy (30pts) — XLY+XLI+XLB (cyclical) vs XLP+XLU+XLV (defensive) 3M return spread: EXPANSION_CONFIRMED (≥8pp) / EXPANSION_EARLY / TRANSITION_NEUTRAL / CONTRACTION_SIGNAL / RECESSION_SIGNAL. **(2)** Rate Environment (25pts) — TLT 3M return as rates falling/rising proxy: RATES_FALLING_STIMULATIVE to RATES_SHARPLY_RISING. **(3)** Credit Spread Proxy (25pts) — HYG vs LQD 3M relative return: RISK_ON_CREDIT_TIGHTENING to CREDIT_STRESS_WIDENING. **(4)** Market Momentum / Earnings Proxy (20pts) — SPY+QQQ avg 3M return. **Composite 0-100 → Cycle Phase**: EARLY_CYCLE (≥60) / MID_CYCLE (≥78) / LATE_CYCLE (≥40) / SLOWDOWN (≥22) / RECESSION (<22). For each phase: overweight/neutral/underweight sector recommendations with rationale. Optional `sector` parameter (e.g. "Technology") returns single-sector OVERWEIGHT/NEUTRAL/UNDERWEIGHT positioning signal. Full ETF return dataset included. Basic tool tier.

`get_capital_allocation_score(ticker)` — Evaluates management's capital allocation efficiency using a **5-component scorecard**. **(1)** Buyback Yield (25 pts) — annual repurchase / market cap ≥5%=25 / ≥3%=20 / ≥1%=14 / ≥0.1%=8 / minimal=3; shares outstanding YoY shrinkage as proxy if repurchase data unavailable. **(2)** Dividend Growth Consistency (20 pts) — YoY DPS growth ≥8% + payout ≤60%=20 / ≥4%+≤70%=16 / stable+≤80%=11 / unsustainable payout>90%=4; growth sector without dividend: neutral 14pts. **(3)** FCF Reinvestment Ratio (20 pts) — capex/FCF ratio, optimal range 0.20–0.60=20 (balanced growth); too light (<0.10) or too heavy (>0.90) penalized. **(4)** M&A Discipline via Goodwill/Assets (20 pts) — ≤5% assets=20 (organic grower) / ≤15%=16 / ≤30%=11 / ≤50%=6 / >50%=2 (acquisition risk); rapid goodwill growth penalty applied. **(5)** ROIC Proxy (15 pts) — net income / invested capital (equity + long-term debt) ≥20%=15 / ≥15%=12 / ≥10%=9 / ≥5%=5. **Signal**: EXCELLENT_CAPITAL_ALLOCATOR (≥80) / GOOD_ALLOCATOR (≥60) / MIXED_ALLOCATOR (≥40) / POOR_ALLOCATOR (<40). Full score breakdown with raw metrics, action guide per signal. Advanced tool tier.

### Valuation Composite (1) *(NEW in v3.8.0)*

`get_valuation_composite(ticker)` — Multi-factor valuation scorecard comparing a stock against its sector benchmark. **5-component scoring**: **(1)** P/E vs Sector (25 pts) — trailing or forward PE divided by sector average PE (built-in benchmarks for 11 sectors): DEEPLY_CHEAP_VS_SECTOR (ratio ≤0.6) / CHEAP / IN_LINE / EXPENSIVE / SIGNIFICANTLY_EXPENSIVE. **(2)** P/B vs Sector (20 pts) — DEEP_VALUE_PB / VALUE_PB / FAIR_PB / ELEVATED_PB / EXPENSIVE_PB. **(3)** EV/EBITDA vs Sector (20 pts) — DEEP_VALUE_EV / CHEAP_EV / FAIR_EV / ELEVATED_EV / EXPENSIVE_EV. **(4)** PEG Ratio (15 pts) — ≤0.8 GROWTH_AT_DISCOUNT / ≤1.2 FAIR_GROWTH_PRICE / ≤2.0 EXPENSIVE_GROWTH / >2.0 GROWTH_OVERPRICED. **(5)** DCF Proxy (20 pts) — 10-year FCF discounted cash flow: growth rate = min(max(eps_growth, 0%), 30%), discount rate = 9% + beta adjustment, terminal growth 2.5%. Compares DCF implied price vs current price: ≥40% upside DEEPLY_UNDERVALUED_DCF / ≥20% UNDERVALUED / ≥-10% FAIRLY_VALUED / ≥-25% OVERVALUED / <-25% SIGNIFICANTLY_OVERVALUED. Composite 0–100: **DEEPLY_UNDERVALUED** (≥72) / **UNDERVALUED** (≥55) / **FAIRLY_VALUED** (≥38) / **OVERVALUED** (≥22) / **SIGNIFICANTLY_OVERVALUED** (<22). Actionable guidance: STRONG_BUY_ZONE / BUY_ZONE / HOLD / TRIM_OR_AVOID / AVOID. Full key metrics: trailing PE, forward PE, P/B, EV/EBITDA, PEG, P/S, EPS TTM, forward EPS, ROE %, market cap. Advanced tool tier.

### Earnings Calendar Sector Screen (1) *(NEW in v4.4.0)*

`get_earnings_calendar_sector_screen(sector, days_ahead)` — Scans the S&P 500 proxy universe for **upcoming earnings announcements** within the next N days, organized by sector. Returns a prioritized earnings playbook. **Earnings schedule**: date, days_until_earnings, timing window EARNINGS_TODAY / IMMINENT_CATALYST (≤3d) / THIS_WEEK / NEXT_TWO_WEEKS / UPCOMING, forward EPS estimate, current price. **Historical quality**: beat rate % (last available quarters), avg EPS surprise %, beat signal STRONG_BEAT_HISTORY / MILD_BEAT_HISTORY / NEUTRAL_HISTORY / MISS_TENDENCY / INSUFFICIENT_HISTORY. **Expected move** proxy: 30d realized vol × √(1/252) × 1.5 earnings premium = pre-earnings expected swing %. **Pre-earnings drift**: last 5-day price change %. **Sector summary**: earnings count and tickers per sector. **Smart lists**: high-confidence beat plays (beat_rate ≥70% + avg_surprise ≥5%), miss risk watch, imminent catalysts. **Strategy guide**: straddle entry timing, iron condor wing sizing, directional trade setup, IV crush warning. Sector options: ALL / Technology / Healthcare / Financials / ConsumerDiscretionary / ConsumerStaples / Industrials / Energy / Materials / Utilities / RealEstate / CommunicationServices. days_ahead: 1–30 (default 14). Advanced tool tier.

### Alpha Factor Composite (1) *(NEW in v4.4.0)*

`get_alpha_factor_composite(ticker)` — Comprehensive **multi-factor alpha scorecard** across 4 investment dimensions, each scored 0–25 (100 total). **(1) Momentum (25 pts)** — Classic 12-1 momentum factor (12M return minus 1M return) × 50% + 3M return × 30% + 6M return × 20% = composite momentum score. MA50/MA200 trend bonus (+2 pts if above both). Signals: STRONG_MOMENTUM_LEADER / POSITIVE_MOMENTUM / MILD_MOMENTUM / NEUTRAL_MOMENTUM / NEGATIVE_MOMENTUM / STRONG_MOMENTUM_LAGGARD + ABOVE_BOTH_MAS_UPTREND / SHORT_TERM_UPTREND / LONG_TERM_TREND_INTACT / BELOW_BOTH_MAS_DOWNTREND. **(2) Quality (25 pts)** — ROE sub-score 10pts (≥20%=10 / ≥15%=8 / ≥10%=6 / ≥0%=3 / negative=0), profit margin sub-score 8pts (≥20%=8 HIGH / ≥10%=6 HEALTHY / ≥5%=4 MODERATE / ≥0%=2 THIN / loss=0), balance sheet strength 7pts (D/E ratio + current ratio composite). **(3) Value (25 pts)** — P/E vs sector benchmark PE 10pts (ratio ≤0.6=10 DEEPLY_CHEAP / ≤0.85=8 CHEAP / ≤1.15=6 FAIR / ≤1.5=3 EXPENSIVE / >1.5=1 VERY_EXPENSIVE; built-in sector PE benchmarks), P/B 7pts (≤1.0=7 DEEP_VALUE / ≤2.0=5 VALUE / ≤4.0=3 FAIR / ≤8.0=1 ELEVATED), EV/EBITDA 8pts (≤8=8 DEEP_VALUE / ≤12=6 CHEAP / ≤18=4 FAIR / ≤25=2 ELEVATED). **(4) Growth (25 pts)** — Revenue growth YoY 12pts (≥25%=12 HYPERGROWTH / ≥15%=10 / ≥8%=8 / ≥3%=5 / ≥0%=2 / negative=0) + Earnings growth 13pts (≥30%=13 / ≥20%=11 / ≥10%=8 / ≥0%=5 / negative=1; forward vs trailing EPS proxy fallback). **Composite signals**: EXCEPTIONAL_ALPHA_CANDIDATE (≥85) / STRONG_ALPHA_CANDIDATE (≥70) / MODERATE_ALPHA_CANDIDATE (≥55) / WEAK_ALPHA_CANDIDATE (≥40) / AVOID (<40). Identifies dominant and weakest factor. Factor ranking by normalized score. Action guide per signal tier. Advanced tool tier.

### Sector Fundamental Heatmap (1) *(NEW in v4.5.0)*

`get_sector_fundamental_heatmap()` — **Cross-sector valuation and quality matrix** covering all 11 GICS sectors. Computes **median fundamentals** from 6 representative S&P 500 stocks per sector: P/E, P/B, EV/EBITDA, ROE %, Revenue Growth %, Net Profit Margin %. Scores each sector by **composite attractiveness** (0–100): valuation sub-score 45% (lower P/E × 40% + lower P/B × 30% + lower EV/EBITDA × 30%) + quality/growth sub-score 55% (higher ROE × 40% + higher net margin × 30% + higher revenue growth × 30%). **Attractiveness labels**: HIGHLY_ATTRACTIVE (≥75) / ATTRACTIVE (≥58) / NEUTRAL (≥42) / UNATTRACTIVE (≥25) / AVOID_SECTOR. Returns ranked sector list, most/least attractive top-3, highlights for best value sector (lowest median P/E), best growth sector (highest median revenue growth), best profitability sector (highest median ROE). Includes overweight/underweight rotation strategy guide. Advanced tool tier.

### Price Target Tracker (1) *(NEW in v4.6.0)*

`get_price_target_tracker(ticker)` — **Analyst price target detailed analysis**. Fetches consensus mean/median/high/low price targets, calculates **upside % to mean/high/low**, and classifies analyst conviction: **STRONG_UPSIDE_POTENTIAL** (≥30% upside) / MODERATE_UPSIDE / MILD_UPSIDE / FAIRLY_PRICED_AT_TARGET / ABOVE_CONSENSUS_TARGET. **Target consensus width**: range width % as analyst agreement proxy — HIGH_CONSENSUS (≤15%) / MODERATE_CONSENSUS / LOW_CONSENSUS / VERY_WIDE_DISPERSION. **Recommendation**: mean score 1–5 label (STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL). **Target trend** from 30d/90d upgrade vs downgrade ratios: TARGETS_RISING / MILDLY_POSITIVE / STABLE_MIXED / TARGETS_FALLING. Upgrade activity breakdown with upgrade ratio. Recent analyst actions with firm, action type, from/to grade (last 8 within 60 days). Advanced tool tier.

### Sector Momentum vs SPY (1) *(NEW in v4.6.0)*

`get_sector_momentum_vs_spy(period_days=63)` — **11 SPDR sector ETFs relative strength vs SPY** over a configurable window (5–252 days, default 63d ≈ 1 quarter). For each sector: absolute return %, **excess return vs SPY (RS)**, half-period RS for **acceleration detection** (ACCELERATING_OUTPERFORM / MILDLY_ACCELERATING / STABLE / MILDLY_DECELERATING / DECELERATING), RS signal (STRONG_OUTPERFORMER ≥8pp / OUTPERFORMER ≥3pp / MARKET_PERFORMER / UNDERPERFORMER / STRONG_UNDERPERFORMER). Full sector rankings, **top-3 outperformers and underperformers**. **Cycle regime** from cyclical vs defensive RS spread: STRONG_RISK_ON_CYCLICAL / MILD_CYCLICAL_BIAS / MIXED_ROTATION / MILD_DEFENSIVE_TILT / STRONG_DEFENSIVE_RISK_OFF. Market context (STRONG_BULL / MILD_BULL / SIDEWAYS / MILD_BEAR / BEAR_MARKET). Strategy guide for overweight/underweight positioning. Advanced tool tier.

### Technical Strength Score (1) *(NEW in v4.5.0)*

`get_technical_strength_score(ticker)` — **5-component technical analysis scorecard** (0–100) using 1-year daily price/volume history. **(1) Trend / MA Alignment (30 pts)** — Price vs MA20/MA50/MA200 position (above all 3 = 20 pts, above MA20+MA50 = 15 pts); MA bullish alignment MA20 > MA50 > MA200 adds +10 pts. **(2) Momentum / RSI + MACD (25 pts)** — RSI-14: BULLISH_ZONE 50–70 = 15 pts / OVERBOUGHT >70 = 10 pts / OVERSOLD_REVERSAL_WATCH <30 = 12 pts; MACD bullish crossover = 10 pts / above signal = 7 pts / positive territory = 5 pts / momentum improving = 3 pts. **(3) Bollinger Band Position (15 pts)** — B% in 40–75% = 15 pts PRICE_IN_BULLISH_BB_ZONE; near lower band (<20%) = 10 pts oversold watch; near upper band = 8 pts; extreme above upper = 5 pts. **(4) Volume Confirmation (15 pts)** — Price up 5d + volume rising = 15 pts BULLISH_VOLUME_CONFIRMATION; price up + low volume = 8 pts WEAK; high vol + price down = 3 pts DISTRIBUTION; neutral = 6 pts. **(5) 52-Week Range Position (15 pts)** — ≥75% of range = 15 pts NEAR_52W_HIGH_MOMENTUM; ≥55% = 12 pts; ≥40% = 8 pts MID_RANGE; <25% = 2 pts NEAR_52W_LOW_WEAKNESS. **Composite signals**: STRONG_BUY_TECHNICAL (≥82) / BULLISH_TECHNICAL (≥65) / NEUTRAL_TECHNICAL (≥50) / BEARISH_TECHNICAL (≥35) / STRONG_SELL_TECHNICAL (<35). Returns key price levels: MA20/50/200, BB upper/lower, 52W high/low. Advanced tool tier.

### Market Regime Composite (1) *(NEW in v3.1.0)*
- `get_market_regime_composite` — 5-layer composite market regime detector. Layer 1: VIX regime (25 pts) — COMPLACENT (<15) / LOW_STRESS (<20) / NORMAL (<25) / ELEVATED_STRESS (<35) / PANIC (≥35). Layer 2: Yield curve shape (20 pts) — 10Y minus 3M spread: STEEP_NORMAL (>100 bps) / NORMAL / FLAT / INVERTED / DEEPLY_INVERTED. Layer 3: Credit spreads (20 pts) — HYG vs IEF 30d relative performance: RISK_ON_CREDIT / MILD_RISK_ON / NEUTRAL_CREDIT / CAUTION / RISK_OFF_CREDIT. Layer 4: Market breadth (20 pts) — SPY vs RSP (equal-weight) 20d momentum comparison: BROAD_PARTICIPATION / MODERATE_BREADTH / NARROW_LEADERSHIP / BROAD_DECLINE / CHOPPY. Layer 5: Sector rotation (15 pts) — XLK + XLY (cyclical) vs XLP + XLU (defensive) 20d relative performance: STRONG_CYCLICAL_ROTATION / CYCLICAL_ROTATION / MIXED / DEFENSIVE_ROTATION / STRONG_DEFENSIVE_ROTATION. Total regime score normalized to 0–100: BULL_MARKET (≥58) / TRANSITION (42–57) / CHOPPY_MARKET (28–41) / BEAR_MARKET (<28). Includes specific asset allocation guidance: e.g., "Risk-ON: Equities > Bonds > Cash. Overweight cyclicals." Basic tool tier.

## Pricing

Pay-per-use via Apify's pay-per-event system:

| Usage | Cost |
|-------|------|
| Session start | $0.010 |
| Basic tool call (Forex, Crypto, Macro, Indices, ETF, FRED, News, Treasury, SEC EDGAR, FOMC Calendar, DeFi TVL, **Macro Dashboard**, **Economic Surprise Index**, **Global Equity Heatmap**, **Market Breadth**, **Credit Spreads**, **Yield Curve Dynamics**, **Macro Regime Monitor**, **VIX Regime Monitor**, **ETF Flow Tracker**, **Market Regime Composite**, **52W High/Low Momentum**, **Cross-Asset Momentum**, **Sector ETF vs SPY Beta**, **Fear & Greed Composite**, **Economic Indicators Dashboard**, **Market Internals Dashboard**) | $0.001 |
| Advanced tool call (Portfolio, Backtesting, Dividend, Sector, Earnings, Options Chain, 13F Holdings, Analyst Ratings, Short Interest, **Earnings Surprise**, **Insider Sentiment**, **Currency Carry**, **Stock Screener**, **Options Flow**, **Earnings Call Sentiment**, **Sector Momentum**, **Commodity Correlation**, **Earnings Whisper**, **Factor Exposure**, **Earnings Season Tracker**, **Dividend Calendar**, **Insider Trading Radar**, **Sector Rotation Signal**, **Earnings Revision Tracker**, **Short Squeeze Radar**, **Institutional Flow Tracker**, **Smart Money Composite**, **Options Flow Heatmap**, **Earnings Surprise vs Sector**, **Options IV Percentile**, **Earnings Date Countdown**, **Relative Strength Ranking**, **Momentum Factor Screen**, **Earnings Quality Score**, **Dividend Safety Screen**, **Valuation Composite**, **Earnings Growth Tracker**, **Liquidity Score**, **Earnings Calendar Sector Screen**, **Alpha Factor Composite**, **Sector Fundamental Heatmap**, **Technical Strength Score**, **Price Target Tracker**, **Sector Momentum vs SPY**, **Short Interest Trend**, **Options Max Pain**) | $0.003 |
| Premium tool call (**Volatility Surface**, **FX Volatility**, **Options Skew Monitor**, **Options IV Term Structure**, **Options Gamma Exposure / GEX**, **Put/Call Ratio History**, **Dark Pool Indicator**, **Options Unusual Activity Scanner**) | $0.005 |

A typical session (100 basic + 20 advanced + 5 premium calls): ~$0.195 total.

## How to connect to Claude Desktop

1. Start this Actor on Apify
2. Copy the MCP endpoint URL from the Actor run
3. Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "finance": {
      "command": "npx",
      "args": ["mcp-remote", "YOUR_APIFY_MCP_URL"]
    }
  }
}
```

4. Restart Claude. Start asking financial questions.

## Input

- **FRED API Key** *(optional)*: Free key from fred.stlouisfed.org — enables 5 FRED tools. Server runs without it.

## License

MIT — free for personal and commercial use.

#!/usr/bin/env python3
"""
apify-convert.py — Finance MCP server.py → Apify Actor 자동 변환기

사용법:
    python3 apify-convert.py

출력:
    apify_server.py  — Apify Actor.charge() 주입된 서버 파일

작동 방식:
    @mcp.tool() 데코레이터가 붙은 모든 async 함수에
    docstring 직후에 await Actor.charge() 호출을 자동 삽입.

가격 전략:
    - basic_tool  ($0.001): forex, macro, crypto 기본 조회
    - advanced_tool ($0.003): 포트폴리오, 실적, 섹터 로테이션 등
"""

import re

# 기본 요금이 붙는 도구 키워드
BASIC_TOOLS = [
    "get_exchange_rate",
    "convert_currency",
    "get_historical_rates",
    "get_supported_currencies",
    "get_currency_comparison",
    "get_crypto_price",
    "get_crypto_market_overview",
    "get_crypto_historical",
    "get_crypto_dominance",
    "get_gdp",
    "get_gdp_comparison",
    "get_inflation",
    "get_unemployment_rate",
    "get_macro_overview",
    "get_lending_rate",
    "get_population",
    "get_commodity_price",
    "get_multi_commodity_prices",
    "get_stock_index",
    "get_index_history",
    "get_etf_info",
    "get_fear_greed_index",
    "get_stock_news",
    "get_market_sentiment",
    # FRED 도구 (v1.1.0)
    "get_fed_funds_rate",
    "get_us_cpi",
    "get_us_pce",
    "get_us_m2",
    "get_us_unemployment",
    # SEC EDGAR + Treasury 도구 (v1.2.0)
    "get_sec_filings",
    "get_insider_trades",
    "get_company_facts",
    "get_treasury_yield_curve",
]

# 고급 요금이 붙는 도구 키워드 (나머지 모두)
ADVANCED_TOOLS = [
    "backtest_etf_portfolio",
    "calculate_portfolio_pnl",
    "compare_gdp_growth",
    "get_asset_correlation",
    "get_portfolio_volatility",
    "get_dividend_analysis",
    "get_sector_rotation",
    "get_stock_fundamental",
    "get_earnings_calendar",
    "get_batch_earnings",
]

APIFY_IMPORT = "from apify import Actor\n"

APIFY_MAIN = '''

async def main():
    """Apify Actor entrypoint — MCP 서버를 Actor로 감싸서 실행"""
    async with Actor:
        # Actor 시작 과금 ($0.01 — 초기화 비용)
        await Actor.charge("actor_start", count=1)
        # MCP 서버 실행 (stdio transport)
        mcp.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
'''

def determine_price_tier(func_name: str) -> str:
    """함수 이름으로 가격 티어 결정"""
    for tool in BASIC_TOOLS:
        if tool in func_name:
            return "basic_tool"
    return "advanced_tool"

def inject_actor_charge(source: str) -> str:
    """
    @mcp.tool() 데코레이터 다음에 오는 async def 함수에
    docstring 이후 Actor.charge() 호출 삽입.
    """
    lines = source.split("\n")
    result = []
    
    i = 0
    in_mcp_tool = False
    func_name = ""
    
    while i < len(lines):
        line = lines[i]
        
        # @mcp.tool() 감지
        if line.strip() == "@mcp.tool()":
            in_mcp_tool = True
            result.append(line)
            i += 1
            continue
        
        # async def 감지 (in_mcp_tool 상태에서)
        if in_mcp_tool and line.strip().startswith("async def "):
            # 함수 이름 추출
            match = re.match(r'\s*async def (\w+)', line)
            if match:
                func_name = match.group(1)
            
            # 함수 시그니처 수집 (멀티라인 가능)
            # 괄호 깊이를 추적해서 depth==0이고 줄 끝이 ':' 일 때 종료
            result.append(line)
            paren_depth = line.count('(') - line.count(')')
            i += 1
            
            while i < len(lines):
                cur = lines[i]
                result.append(cur)
                paren_depth += cur.count('(') - cur.count(')')
                i += 1
                # paren_depth == 0: 시그니처 닫힘. 줄 끝에 ':' 있으면 종료
                if paren_depth <= 0 and cur.rstrip().endswith(':'):
                    break
            
            # 들여쓰기 감지
            body_indent = "    "
            if i < len(lines):
                stripped = lines[i].lstrip()
                spaces = len(lines[i]) - len(stripped)
                body_indent = " " * spaces
            
            # 독스트링 처리
            if i < len(lines) and lines[i].strip().startswith('"""'):
                # 멀티라인 독스트링
                result.append(lines[i])
                
                if lines[i].strip() == '"""' or (lines[i].count('"""') >= 2 and lines[i].strip() != '"""'):
                    # 한 줄 독스트링이거나 여는 줄에 닫힘
                    if lines[i].count('"""') < 2:
                        i += 1
                        while i < len(lines) and '"""' not in lines[i]:
                            result.append(lines[i])
                            i += 1
                        if i < len(lines):
                            result.append(lines[i])
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
                    while i < len(lines) and '"""' not in lines[i]:
                        result.append(lines[i])
                        i += 1
                    if i < len(lines):
                        result.append(lines[i])
                        i += 1
            
            # Actor.charge() 주입
            tier = determine_price_tier(func_name)
            result.append(f"{body_indent}await Actor.charge('{tier}', count=1)")
            
            in_mcp_tool = False
            continue
        
        if in_mcp_tool and not line.strip().startswith("async def "):
            # 데코레이터와 함수 사이에 다른 게 끼어 있으면 초기화
            if line.strip() and not line.strip().startswith("@"):
                in_mcp_tool = False
        
        result.append(line)
        i += 1
    
    return "\n".join(result)

def convert():
    # 원본 읽기
    with open("server.py", "r") as f:
        source = f.read()
    
    # Apify import 추가 (fastmcp import 다음에)
    source = source.replace(
        "from fastmcp import FastMCP",
        f"from fastmcp import FastMCP\n{APIFY_IMPORT}"
    )
    
    # Actor.charge() 주입
    source = inject_actor_charge(source)
    
    # 기존 if __name__ 블록 제거 후 Apify main() 추가
    if 'if __name__ == "__main__"' in source:
        # 기존 메인 블록 제거
        source = re.sub(
            r'\nif __name__ == "__main__".*',
            "",
            source,
            flags=re.DOTALL
        )
    
    source += APIFY_MAIN
    
    # 출력
    with open("apify_server.py", "w") as f:
        f.write(source)
    
    print("✅ apify_server.py 생성 완료")
    print()
    print("📋 다음 단계:")
    print("  1. pip install apify-client apify")
    print("  2. apify login")
    print("  3. apify create finance-mcp --template python-start")
    print("  4. cp apify_server.py finance-mcp/src/main.py")
    print("  5. apify push")
    print("  6. Apify Console → Monetization → Pay per event:")
    print("     - actor_start: $0.01")
    print("     - basic_tool:  $0.001")
    print("     - advanced_tool: $0.003")

if __name__ == "__main__":
    convert()

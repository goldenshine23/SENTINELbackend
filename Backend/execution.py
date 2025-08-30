from metaapi_cloud_sdk import MetaApi
from strategy.strategy import (
    analyze_symbol,
    calculate_lot_size,
    calculate_pips,
    should_trade,
    has_open_trades,
    score_trade
)

async def execute_trade(account, signal, symbol, lot_size, sl_pips, tp_pips):
    try:
        terminal = await account.get_terminal()
        price = (await terminal.get_symbol_price(symbol)).bid

        if signal == 'buy':
            sl = price - sl_pips
            tp = price + tp_pips
        else:
            sl = price + sl_pips
            tp = price - tp_pips

        print(f"[ORDER] Placing {signal.upper()} order on {symbol} at {price:.5f}")
        result = await terminal.create_market_order(symbol, signal, lot_size, sl, tp)
        print(f"[RESULT] ✅ Trade placed: {result}")
    except Exception as e:
        print(f"[ERROR] ❌ Trade execution failed: {e}")

async def run_trading_for_user(user):
    metaapi = MetaApi(user.metaapi_token)  # Initialize here inside async function
    account = await metaapi.metatrader_account_api.get_account(user.account_id)

    if account.state != 'DEPLOYED':
        print(f"[{user.id}] Deploying account...")
        await account.deploy()
        await account.wait_connected()
    else:
        print(f"[{user.id}] Account already deployed.")

    symbols = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD",
        "AUDUSD", "NZDUSD", "XAUUSD", "BTCUSD", "ETHUSD"
    ]

    best_score = -float('inf')
    best_analysis = None
    best_symbol = None

    for symbol in symbols:
        analysis = await analyze_symbol(metaapi, user.account_id, symbol)
        score = score_trade(analysis)
        print(f"[{user.id}][SCORE] {symbol} → {score:.2f}")
        if score > best_score:
            best_score = score
            best_analysis = analysis
            best_symbol = symbol

    if best_analysis and should_trade(best_analysis):
        open_trades = await has_open_trades(account, best_symbol)
        if not open_trades:
            balance = await account.get_balance()
            lot_size = calculate_lot_size(balance, risk_percent=1)
            sl_pips = calculate_pips(best_symbol, 'sl')
            tp_pips = calculate_pips(best_symbol, 'tp')

            await execute_trade(
                account,
                signal=best_analysis['direction'],
                symbol=best_symbol,
                lot_size=lot_size,
                sl_pips=sl_pips,
                tp_pips=tp_pips
            )
        else:
            print(f"[{user.id}][SKIP] Existing trade on {best_symbol}")
    else:
        print(f"[{user.id}][SKIP] No valid trade setup.")

async def execution_engine():
    # Placeholder: add logic to manage multiple users if needed
    pass

async def trade_execution(user):
    # Wrapper function to run trading logic for a user
    await run_trading_for_user(user)
import asyncio

async def run_trading_for_all_users(users):
    tasks = [run_trading_for_user(user) for user in users]
    await asyncio.gather(*tasks)

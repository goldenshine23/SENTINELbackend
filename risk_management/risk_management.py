def calculate_lot_size(balance, stop_loss_pips, pip_value=10, risk_percentage=None):
    # Set default risk based on account balance
    if balance < 200:
        risk_percentage = 10
    elif risk_percentage is None:
        risk_percentage = 2  # Default mid-point of 1–3%

    # Ensure stop loss does not exceed 30 pips
    stop_loss_pips = min(stop_loss_pips, 30)

    # Calculate the dollar amount at risk
    risk_amount = balance * (risk_percentage / 100)

    # Calculate lot size
    lot_size = risk_amount / (stop_loss_pips * pip_value)

    # Return lot size with minimum of 0.01
    return round(max(0.01, lot_size), 2)

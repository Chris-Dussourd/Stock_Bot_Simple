# Stock_Exchange_Bot
Simple trading bot that uses past stock history to buy on dips and sell on peaks.

More Documentation to come. Here is a short explanation.

#Functions for visualizing profits. 

- Estimate_Profits...py
- Simulates a trading bot. 
  1. The bot buys at the the first price available (previous_buy - last price the stock was purchased at). 
  2. It loops through prices until the price dips to a new buy price or raises to a new sell price.
      where buy_price = previous_buy*(1-buy_proportion) and sell_price = average_buy*(1+sell_proportion)
  3. If more stock was bought, it updates the average buy price and continues looping until a new buy price or sell price is hit. (The bot was stop buying more stock after it has bought buys_allowed times.
  4. If stock was sold, it continues looping through prices and buys when the stock dips by new_buy_proportion below the sell price.
  5. When the end of the price data is reached, it calculates the estimated profit the bot obtained.
  6. Loops over multiple new_buy_proportions, buy_propotions, and/or sell_proportions and calculates profit for each.
  
  
#Simple trading bot

- Based on the estimated profit on price history data, set a particular new_buy_propotion, buy_proportion, and/or sell_proportion for each ticker. As of right now, this is something that needs to be done manually in InitialTransactionsDictionary.py.
- Setup additional parameters for the bot to use. Examples
    1. transactions[ticker]['Available Balance'] - amount of money available for each ticker
    2. transactions['Max Buys'] - the maximum number of times the bot can buy the same stock
- Open and run 'Main_Bot_Runner.py'. Bot will place buy and and sell orders on your TD Ameritrade account. I recommend setting the sell_proportion at 3 percent or more; otherwise, TD Ameritrade may contact you to make trades less frequently.
- Type in 'Check' into the terminal. The transactions dictionary will be printed to the screen.

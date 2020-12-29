
# This python script takes in the price history dictionary from a pickle file.
# price_history[ticker]=[minute level opening price data]
# This estimates what profit we would get if we buy at particular percent from original price and sell at another percent of original price.

# The algorithm buys stock  - It sells the same stock if it jumps up to sell percent above the original price using a limit order
#                           - It buys the same stock if it falls to buy percent below the original buy price. It will re-buy same stock 5-10 times.
#                           - It re-calculates limit order sell price to be a total profit of sell percent above the average buy price.
#                           - Once all shares have been sold, it sets a limit buy order at new_buy_proportion below the sell price

import pandas as pd
import time
import pickle
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt


if __name__=="__main__":
    file_name = 'save.p'

    price_history = pickle.load(open("Price_History_April3_May15.p","rb"))

    test_tickers = ['SVC']
    sell_proportion = {'SVC': 0.05}

    #test_tickers = ['MSFT']
    #Number of times we allow the bot to re-buy the same stock without any sells
    buys_allowed = 3
    profit_ticker_percent = {}
    times_sold = {}

    buy_percent = []
    new_buy_percent = []

    update_xy=True

    #Get the profit for each ticker
    for ticker in test_tickers:

        profit_ticker_percent[ticker] = []
        times_sold[ticker]=[]
        
        if len(buy_percent) > 0:
            update_xy = False
        
        #Create a 3-D plot of profit vs new_buy_percent and buy_percent to find the optimal times to buy and sell this stock
        for x in range(1):

            #Buy percent ranges from 0.1% buy below previous sell to 10% 
            buy_proportion = 0.03

            for y in range(1):

                #New buy percent ranges from 0.05% below last sell price to 5% below
                new_buy_proportion = 0.01

                total_profit = 0
                total_profit_percent = 0
                index = 0

                #Previous buy - the first time we buy the stock
                previous_buy = price_history[ticker][index]
                #average buy - the average limit order buy price
                average_buy = previous_buy
                #num buys - the total number of buys we have without any sells
                num_buys = 1
                profit_proportion = 0
                count_sold = 0

                #Run the rest of the algorithm
                while index < len(price_history[ticker]):

                    price = price_history[ticker][index]

                    #If price falls below buy percent of the previous buy price and we haven't reached our buys allowed limit, make another buy
                    if price <= previous_buy*(1-buy_proportion) and num_buys<buys_allowed:
                        previous_buy = price
                        average_buy = (num_buys*average_buy + previous_buy)/(num_buys+1)
                        num_buys+=1

                    #If price jumps up to sell percent above the average buy price, sell all of our stock
                    if price >= average_buy*(1+sell_proportion[ticker]):

                        profit_proportion += sell_proportion[ticker]*num_buys

                        #Set a new buy limit order
                        count_sold += num_buys
                        num_buys = 1
                        previous_buy = average_buy*(1+sell_proportion[ticker])*(1-new_buy_proportion)
                        average_buy = previous_buy
                        
                        #Keep looping through price history until the price falls to the new buy price
                        while index < len(price_history[ticker]) and price_history[ticker][index] > previous_buy:
                            index=index+1
                    else:
                        index+=1

                profit_ticker_percent[ticker].append(profit_proportion*100)
                times_sold[ticker].append(count_sold)
                if update_xy:
                    new_buy_percent.append(new_buy_proportion*100)
                    buy_percent.append(buy_proportion*100)

                last_price = price_history[ticker][-1] 
                """         
                print('-------------------------------------------------------------')
                print('{} had a profit percent of {}.'.format(ticker,profit_ticker_percent[ticker]/buys_allowed))
                print('The number times we bought and sold was {}.'.format(times_sold))
                print('The last price is {}, and the last buy average was {}.'.format(last_price,average_buy))
                print('-------------------------------------------------------------')
                """
                    
            #total_profit_percent = sum(profit_ticker_percent.values())/buys_allowed        
            #print('Total percent profit:  {}'.format(total_profit_percent))
            #print('Average percent profit:  {}'.format(total_profit_percent/len(test_tickers)))

        print('The max times {} was sold was {}'.format(ticker,max(times_sold[ticker])))

    """
    pickle.dump(profit_ticker_percent,open("PofitbyPercent_BuyNewBuy_April3_May15_3_SGBX.p","wb"))
    pickle.dump(buy_percent,open("BuyPercent_SGBX.p","wb"))
    pickle.dump(new_buy_percent,open("NewBuyPercent_SGBX.p","wb"))
    """


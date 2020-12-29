
# This python script takes in the price history dictionary from a pickle file.
# price_history[ticker]=[minute level opening price data]
# This estimates what profit we would get if we buy at particular percent from original price and sell at another percent of original price.

#There are three different algorithms I am testing. All algorithms use the following behavior:
#   - It sells the same stock if it jumps up to sell percent above the average buy price using a limit order
#   - It buys the same stock if it falls to buy percent below a certain price. It can re-buy the same stock 3-4 times.
#   - It re-calculates limit order sell price to be a total profit of sell percent above the average buy price.

# Max Price Algorithm
#   - It keeps track of the max price of the stock since we last sold it. It updates a buy order to buy_percent below the max price if max price went up by more than 1 percent.
#   - This keeps the bot in the range of the stock so that it can keep buying and selling (prevents a bot from having a sitting buy order if there is a large jump in price)

# Keep Some Algorithm
#   - The algorithm always owns some of the stock. It sets optimal buy and sell orders
#   - Works the same as max price, it just never fully sells all of stock.
                  
# New Buy Percent Algorithm
#   - It sets a buy price at new buy percent below last purchase price


import pandas as pd
import time
import pickle
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt

def new_buy_algo(price,buy_order,sell_order,buy_proportion,sell_proportion,new_buy_proportion,num_buys,max_buys,profit_proportion):
    """
    Estimates profit if we buy stock at new_buy_proportion below last sell price, buy again at buy percent below previous buy price, and 
    sell at sell_proportion above average buy price.
    Pass in the latest price and algorithm will determine if orders were filled, what new orders to place, and profit obtained

    price - current price of stock
    buy_order - the price that we buy more stock (0 if no buy orders)
    sell_order - the price that we sell the stock (0 if no sell orders)
    buy_proportion - the proportion below the last buy price for a new buy order
    sell_proportion - the propoartion above the average buy price for a new sell order
    new_buy_proportion - the proportion below the last sell price for a new buy order
    num_buys - the number of times we bought the stock so far
    max_buys - the number of times we are allowed to buy the same stock
    profit_proportion - the profit we have obtained so far

    Returns num_buys, buy_order, sell_order, and profit proportion
    """
    if buy_order>0 and price<=buy_order:
        #Our buy order was successfully placed
        num_buys+=1

        total_buy=0
        #Re-calculate sell price
        for i in range(num_buys):
            #What is the total amount spent on buy orders thus far
            total_buy += buy_order*(1+buy_proportion)**i
        average_buy = total_buy/num_buys

        sell_order = average_buy*(1+sell_proportion)

        if num_buys<max_buys:
            #Calculate new buy order price
            buy_order = buy_order*(1-buy_proportion)
        else:
            buy_order = 0
    
    if sell_order>0 and price>=sell_order:
        #Our sell order was successfully placed
        profit_proportion += num_buys/max_buys*sell_proportion

        buy_order = sell_order*(1-new_buy_proportion)
        sell_order = 0
        num_buys = 0
    
    return (num_buys,buy_order,sell_order,profit_proportion)



def max_price_algo(price,buy_order,sell_order,buy_proportion,sell_proportion,new_buy_proportion,num_buys,max_buys,profit_proportion,calc_proportion):
    """
    Estimates profit if we buy stock at new_buy_proportion below max price since last sell, buy again at buy percent below previous buy price, and 
    sell at sell_proportion above average buy price.
    Pass in the latest price and algorithm will determine if orders were filled, what new orders to place, and profit obtained

    price - current price of stock
    buy_order - the price that we buy more stock (0 if no buy orders)
    sell_order - the price that we sell the stock (0 if no sell orders)
    buy_proportion - the proportion below the last buy price for a new buy order
    sell_proportion - the propoartion above the average buy price for a new sell order
    new_buy_proportion - the proportion below the last sell price for a new buy order
    num_buys - the number of times we bought the stock so far
    max_buys - the number of times we are allowed to buy the same stock
    profit_proportion - the profit we have obtained so far
    calc_proportion - if max price increases by this proportion, re-calculate the buy order

    Returns num_buys, buy_order, sell_order, and profit proportion
    """
    if buy_order>0 and price<=buy_order:
        #Our buy order was successfully placed
        num_buys+=1

        total_buy=0
        #Re-calculate sell price
        for i in range(num_buys):
            #What is the total amount spent on buy orders thus far
            total_buy += buy_order*(1+buy_proportion)**i
        average_buy = total_buy/num_buys

        sell_order = average_buy*(1+sell_proportion)

        if num_buys<max_buys:
            #Calculate new buy order price
            buy_order = buy_order*(1-buy_proportion)
        else:
            buy_order = 0
    
    if sell_order>0 and price>=sell_order:
        #Our sell order was successfully placed
        profit_proportion += num_buys/max_buys*sell_proportion

        buy_order = sell_order*(1-new_buy_proportion)
        sell_order = 0
        num_buys = 0

    #If we haven't bought any stock yet and the price increases above calc_proportion, re-caculate buy order
    if num_buys==0 and price*(1-new_buy_proportion)>buy_order*(1+calc_proportion):   
        buy_order = price*(1-new_buy_proportion)
    
    return (num_buys,buy_order,sell_order,profit_proportion)
    

def new_buy_zero(price,buy_order,sell_order,buy_proportion,sell_proportion,num_buys,max_buys,profit_proportion,calc_proportion,last_sell):
    """
    This assumes new_buy_proportion is zero. It won't ever sell all of stock.
    Estimates profit if we buy again at buy percent below previous buy price, and 
    sell at sell_proportion above average buy price.
    Pass in the latest price and algorithm will determine if orders were filled, what new orders to place, and profit obtained

    price - current price of stock
    buy_order - the price that we buy more stock (0 if no buy orders)
    sell_order - the price that we sell the stock (0 if no sell orders)
    buy_proportion - the proportion below the last buy price for a new buy order
    sell_proportion - the propoartion above the average buy price for a new sell order
    num_buys - the number of times we bought the stock so far
    max_buys - the number of times we are allowed to buy the same stock
    profit_proportion - the profit we have obtained so far
    calc_proportion - if max price increases by this proportion, re-calculate the buy order (set to zero if we don't want to change buy order)
    last_sell - the last price the stock was sold at. If last sell is zero, set this equal to the first buy price

    Returns num_buys, buy_order, sell_order, profit proportion, and last_sell
    """
    if buy_order>0 and price<=buy_order:
        #Our buy order was successfully placed
        num_buys+=1

        total_buy=0
        #Re-calculate sell price
        for i in range(num_buys):
            #What is the total amount spent on buy orders thus far
            total_buy += buy_order/(1-buy_proportion)**i
        average_buy = total_buy/num_buys

        sell_order = average_buy*(1+sell_proportion)

        if num_buys<max_buys:
            #Calculate new buy order price
            buy_order = buy_order*(1-buy_proportion)
        else:
            buy_order = 0
    
    if sell_order>0 and price>=sell_order:
        #Our sell order was successfully placed
        profit_proportion += num_buys/max_buys*sell_proportion

        buy_order = sell_order*(1-buy_proportion)
        last_sell = sell_order
        sell_order = 0
        num_buys = 1 #Assume we don't sell all of stock
        

    #If we only have 1 buy and price increases by calc proportion, change buy order
    if num_buys==1 and calc_proportion>0 and price>last_sell*(1+calc_proportion):   
        buy_order = price*(1-buy_proportion)
        profit_proportion += 1/max_buys*calc_proportion
        last_sell = price

    #For calc proportion equal to zero, re-calculate at the sell proportion
    if num_buys==1 and calc_proportion==0 and price>last_sell*(1+sell_proportion):
        buy_order = price*(1-buy_proportion)
        profit_proportion += 1/max_buys*sell_proportion
        last_sell = price
    
    return (num_buys,buy_order,sell_order,profit_proportion,last_sell)


if __name__=="__main__":
    file_name = 'save.p'

    price_history = pickle.load(open("Price_History_April3_May15.p","rb"))

    test_tickers = ['ASTC']

    #test_tickers = ['MSFT']
    #Number of times we allow the bot to re-buy the same stock without any sells
    max_buys = 3
    profit_ticker_percent = {}

    buy_percent = []
    new_buy_percent = []

    update_x=True

    #Calc Proportion to Test for new_buy_proportion = 0
    new_buy_zero_calc = [0,0.02,0.05,0.1,0.2,0.3,0.5,1]

    #New buy proportions to test
    new_buy_proportions = [0]

    #Max price new buy proportions to test
    max_price_new_buys = [0]
    #Max price calc proportion to test
    calc_proportion = 0.01

    #Total algorithms we are running
    total_algos = len(new_buy_zero_calc)+len(new_buy_proportions)+len(max_price_new_buys)

    #Get the profit for each ticker
    for ticker in test_tickers:

        for y in range(20):

            sell_proportion = y*0.5/100+1/100

            #Reset profits before trying out new sell percent
            profit_ticker_percent[ticker] = []
            for i in range(total_algos):
                profit_ticker_percent[ticker].append([])

            if len(buy_percent) > 0:
                update_x = False
        
            #Create a 2-D plot of profit buy_percent for each sell percent
            for x in range(200):

                #Buy percent ranges from 0.5% buy below previous sell to 10% 
                buy_proportion = x*0.1/100+0.5/100

                index=0
                #Buy order - the new price for us to buy stock
                buy_order = [price_history[ticker][index]] * total_algos
                #Sell order - the new price for us to sell stock (start at zero because we don't own stock)
                sell_order = [0] * total_algos
                #num buys - the total number of buys we have without any sells
                num_buys = [0] * total_algos
                profit_proportion = [0] * total_algos
                #Last sell is used for new buy zero calculations
                last_sell = [price_history[ticker][index]] * len(new_buy_zero_calc)

                #Loop for each price in price_history
                while index < len(price_history[ticker]):
                    
                    price = price_history[ticker][index]

                    #For each new calc proportion for new buy zero, run the new_buy_zero algorithm
                    for i in range(len(new_buy_zero_calc)):
                        (num_buys[i],buy_order[i],sell_order[i],profit_proportion[i],last_sell[i]) = new_buy_zero(price,buy_order[i],sell_order[i],buy_proportion,sell_proportion,num_buys[i],max_buys,profit_proportion[i],new_buy_zero_calc[i],last_sell[i])

                    #For each new buy proportion, run the new_buy algorithms
                    for j in range(len(new_buy_proportions)):
                        k = j + len(new_buy_zero_calc) #get the index right for variables shared with new_buy_zero algorithm
                        (num_buys[k],buy_order[k],sell_order[k],profit_proportion[k]) = new_buy_algo(price,buy_order[k],sell_order[k],buy_proportion,sell_proportion,new_buy_proportions[j],num_buys[k],max_buys,profit_proportion[k])
                
                    #For each new buy proportion, run the new_buy algorithms
                    for j in range(len(max_price_new_buys)):
                        k = j + len(new_buy_zero_calc) + len(new_buy_proportions) #get the index right for variables shared with new_buy_proportion algorithm
                        #Max price algorithm with new_buy_proportion = 0.25/100 and calc_proportion = 0.01
                        (num_buys[k],buy_order[k],sell_order[k],profit_proportion[k]) = max_price_algo(price,buy_order[k],sell_order[k],buy_proportion,sell_proportion,max_price_new_buys[j],num_buys[k],max_buys,profit_proportion[k],calc_proportion)

                    index+=1

                last_price = price_history[ticker][-1] 
                #For new_buy_zero calcs, set profit based on ending price.
                for i in range(len(new_buy_zero_calc)):
                    profit_proportion[i] -= (1/max_buys)*(last_sell[i]-last_price)/last_sell[i]

                for i in range(total_algos):
                    profit_ticker_percent[ticker][i].append(profit_proportion[i]*100)
                if update_x:
                    buy_percent.append(buy_proportion*100)

                
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

            fig = plt.figure()

            #Plot results of each new_buy_zero_calc algorithm
            for index in range(len(new_buy_zero_calc)):
                plt.plot(buy_percent,profit_ticker_percent[ticker][index],label="zero = {}".format(new_buy_zero_calc[index]*100))
            
            #Plot results of each new_buy_proportion algorithm
            for index in range(len(new_buy_proportions)):
                index2 = index+len(new_buy_zero_calc)
                plt.plot(buy_percent,profit_ticker_percent[ticker][index2],label="new = {}".format(new_buy_proportions[index]*100))

            #Plot results of each max_price algorithm
            for index in range(len(max_price_new_buys)):
                index2 = index+len(new_buy_proportions)+len(new_buy_zero_calc)
                plt.plot(buy_percent,profit_ticker_percent[ticker][index2],label="max = {}".format(max_price_new_buys[index]*100))

            plt.xlabel('Buy Percent')
            plt.ylabel('Profit')
            plt.title('Sell Percent = {}'.format(sell_proportion*100))
            plt.legend()
            plt.show()

    """
    pickle.dump(profit_ticker_percent,open("PofitbyPercent_BuyNewBuy_April3_May15_3_SGBX.p","wb"))
    pickle.dump(buy_percent,open("BuyPercent_SGBX.p","wb"))
    pickle.dump(new_buy_percent,open("NewBuyPercent_SGBX.p","wb"))
    """



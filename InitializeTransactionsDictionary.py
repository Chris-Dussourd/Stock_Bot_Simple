import math,pickle
from TDAmeritrade_API import get_access,get_account

#Initialize dictionary
def initialize_transactions():
    """
    Store information related to trading on each stock into a dictionary
    Store the dictionary as a pickle file ("transactions.p")
    """
    #Create a dictionary to save successful buys, sells, and money available to bot.
    transactions={}

    #Maximum number of times the bot can buy the same stock
    transactions['Max Buys']=3

    #TD Ameritrade Limitations
    requests_allowed=2                                   #Minimum number of requests allowed per second to TD Ameritrade API
    transactions['Last Requests']=[0]*requests_allowed
    
    #Initialize tokens in dictionary
    transactions['Access Token']=''
    transactions['Access Expire Time']=0

    #Store API call errors to see if we need to manually place orders
    transactions['API Errors']=[]

    #Create a dictionary for each ticker to run on transactions
    tickers_list = ['NAIL','SVC','MTDR','HXL','BIMI','SGBX','NOVN','MIST','ASTC','CREX']
    transactions['Tickers']=tickers_list
    for ticker in tickers_list:
        transactions[ticker]={}
    
    #Make the base balance for each stock to use 1000
    for ticker in tickers_list:
        transactions[ticker]['Available Balance'] = 1000


    #The proportion dip in price where we buy more of the same stock
    transactions['NAIL']['Buy Proportion'] = 8/100
    transactions['HXL']['Buy Proportion'] = 11/100
    transactions['MTDR']['Buy Proportion'] = 4.5/100
    transactions['SVC']['Buy Proportion'] = 5/100
    transactions['BIMI']['Buy Proportion'] = 3/100
    transactions['SGBX']['Buy Proportion'] = 10/100
    transactions['NOVN']['Buy Proportion'] = 6/100
    transactions['MIST']['Buy Proportion'] = 5/100
    transactions['ASTC']['Buy Proportion'] = 4/100
    transactions['CREX']['Buy Proportion'] = 8/100

    #The proportion raise from the average buy where we sell all the stock
    transactions['NAIL']['Sell Proportion'] = 6/100
    transactions['HXL']['Sell Proportion'] = 3.5/100
    transactions['MTDR']['Sell Proportion'] = 3.5/100
    transactions['SVC']['Sell Proportion'] = 4/100
    transactions['BIMI']['Sell Proportion'] = 2/100
    transactions['SGBX']['Sell Proportion'] = 2/100
    transactions['NOVN']['Sell Proportion'] = 1.5/100
    transactions['MIST']['Sell Proportion'] = 4/100
    transactions['ASTC']['Sell Proportion'] = 3/100
    transactions['CREX']['Sell Proportion'] = 7/100

    #The proportion dip in price after selling all stock where we buy again
    transactions['NAIL']['New Buy Proportion'] = 0
    transactions['HXL']['New Buy Proportion'] = 0
    transactions['MTDR']['New Buy Proportion'] = 0
    transactions['SVC']['New Buy Proportion'] = 0
    transactions['BIMI']['New Buy Proportion'] = 0
    transactions['SGBX']['New Buy Proportion'] = 0
    transactions['NOVN']['New Buy Proportion'] = 0
    transactions['MIST']['New Buy Proportion'] = 0
    transactions['ASTC']['New Buy Proportion'] = 0
    transactions['CREX']['New Buy Proportion'] = 0

    #The first buy we set the order at
    transactions['NAIL']['First Buy'] = 28.71
    transactions['HXL']['First Buy'] = 43.41
    transactions['MTDR']['First Buy'] = 9.91
    transactions['SVC']['First Buy'] = 10.71
    transactions['BIMI']['First Buy'] = 2.83
    transactions['SGBX']['First Buy'] = 2.73
    transactions['NOVN']['First Buy'] = 0.49
    transactions['MIST']['First Buy'] = 4.8
    transactions['ASTC']['First Buy'] = 3
    transactions['CREX']['First Buy'] = 3

    #Add empty arrays/values to all the ticker dictionaries
    for ticker in tickers_list:
        transactions[ticker]['Order Quantity']=math.floor(transactions[ticker]['Available Balance']/(transactions[ticker]['First Buy']*(1+transactions[ticker]['Sell Proportion'])*transactions['Max Buys']))
        transactions[ticker]['Bid Price']=0
        transactions[ticker]['Ask Price']=0
        transactions[ticker]['Stock Bought']=0
        transactions[ticker]['Stock Sold']=0

        #Keep track of current costs of currently bought stock 
        transactions[ticker]['Previous Buy']=0  #Last purchase price of stock
        transactions[ticker]['Average Buy']=0   #Average purchase cost of stock
        transactions[ticker]['Previous Sell']=0 #Last sale price of stock
        transactions[ticker]['Stock Owned']=0   #Amount of stock I currently own
        transactions[ticker]['Last Fill']=0   #If partially filled sell order, this stores how much stock has been filled

        transactions[ticker]['Limit Buy ID']=0     #Order ID
        transactions[ticker]['Limit Buy Price']=0  #The buy price of the most recent limit buy order
        transactions[ticker]['Limit Sell ID']=0    #Order ID
        transactions[ticker]['Limit Sell Price']=0 #The sell price of the most recent limit sell order

        #Max numer of digits we can use when placing orders (>$1 stocks = 2 digits, <$1 stocks = 4 digits)
        if ticker=='NOVN':
            transactions[ticker]['Max Digits']=4
        else:
            transactions[ticker]['Max Digits']=2       

    pickle.dump(transactions,open("Transactions.p","wb"))


def add_stock_transactions(ticker,price,balance,buy_proportion,sell_proportion,new_buy_proportion,max_digits):
    """
    Adds a new stock to the transactions dictionary
    ticker - the stock symbol 
    price - the price to buy the first stock
    balance - the amount of money we are allowing trading for this stock
    buy_proportion - the proportion dip in price from previous buy where we buy more shares of the stock
    sell_proportion - the proportion rise in price from average buy where we sell all the stock
    new_buy_proportion - after the sale of the stock, the proportion dip in price before we buy more stock
    max_digits - the max number of digits allowed when placing orders (2 for stocks >$1 and 4 for stocks <$1)
    """

    transactions = pickle.load(open("Transactions.p","rb"))

    transactions['Tickers'].append(ticker)
    transactions[ticker]={}

    transactions[ticker]['First Buy']=price
    transactions[ticker]['Available Balance']=balance
    transactions[ticker]['New Buy Proportion']=new_buy_proportion
    transactions[ticker]['Buy Proportion']=buy_proportion
    transactions[ticker]['Sell Proportion']=sell_proportion

    transactions[ticker]['Order Quantity']=math.floor(transactions['Available Balance']/(transactions[ticker]['First Buy']*(1+transactions['Sell Proportion'])*transactions['Max Buys']))
    transactions[ticker]['Bid Price']=0
    transactions[ticker]['Ask Price']=0
    transactions[ticker]['Stock Bought']=0
    transactions[ticker]['Stock Sold']=0

    #One limit buy order should always be placed. Place a limit sell order if we have bought stock 
    transactions[ticker]['Limit Buy ID']=0     #Order ID
    transactions[ticker]['Limit Buy Price']=0  #The buy price of the most recent limit buy order
    transactions[ticker]['Limit Sell ID']=0    #Order ID
    transactions[ticker]['Limit Sell Price']=0 #The sell price of the most recent limit sell order
    transactions[ticker]['Previous Buy']=0  #Last purchase price of stock
    transactions[ticker]['Previous Sell']=0 #Last sale price of stock
    transactions[ticker]['Average Buy']=0   #Average purchase cost of stock
    transactions[ticker]['Stock Owned']=0   #Amount of stock I currently own
    transactions[ticker]['Last Fill']=0   #If partially filled sell order, this stores how much stock has been filled

    transactions[ticker]['Max Digits']=max_digits

    #Save Updates
    pickle.dump(transactions,open("Transactions.p","wb"))


def recover_transactions(transactions):
    """
    Recover transactions if process terminated or accidentally closed
    """

    [access_token,expire_time]=get_access('','')
    account_data = get_account(access_token)

    positions = account_data['securitiesAccount']['positions']
    orders = account_data['securitiesAccount']['orderStrategies']

    #Reset transactions limit buy id and limit sell id to 0.
    for ticker in transactions['Tickers']:
        transactions[ticker]['Limit Buy ID'] = 0
        transactions[ticker]['Limit Buy Price'] = 0
        transactions[ticker]['Limit Sell ID'] = 0
        transactions[ticker]['Limit Sell Price'] = 0

    #Update limit buy and sell orders using currently queued orders
    for order in orders:

        if order['status'] == 'WORKING':

            ticker = order['orderLegCollection'][0]['instrument']['symbol']
            if ticker in transactions['Tickers']:

                if order['orderLegCollection'][0]['instruction']=='BUY':

                    transactions[ticker]['Limit Buy ID'] = order['orderId']
                    transactions[ticker]['Limit Buy Price'] = order['price']

                elif order['orderLegCollection'][0]['instruction']=='SELL':

                    transactions[ticker]['Limit Sell ID'] = order['orderId']
                    transactions[ticker]['Limit Sell Price'] = order['price']


    #Update stock owned and after buy price
    for position in positions:

        ticker = position['instrument']['symbol']
        if ticker in transactions['Tickers']:
            
            #Update stock owned and average price
            transactions[ticker]['Available Balance'] -= (position['longQuantity']-transactions[ticker]['Stock Owned'])*position['averagePrice']
            transactions[ticker]['Stock Owned'] = position['longQuantity']
            transactions[ticker]['Average Buy'] = position['averagePrice']
            #Update previous buy depending on how much stock we bought
            if position['longQuantity']==transactions[ticker]['Order Quantity']:
                transactions[ticker]['Previous Buy'] = position['averagePrice']
            elif position['longQuantity']>2*transactions[ticker]['Order Quantity']:
                transactions[ticker]['Previous Buy'] = position['averagePrice']*(1-transactions[ticker]['Buy Proportion'])
            else:
                transactions[ticker]['Previous Buy'] = position['averagePrice']*(1-transactions[ticker]['Buy Proportion']/2)

    




import datetime,time,dateutil.parser
import pytz, pickle
from TDAmeritrade_API import *

#TD Ameritrade_algorithm_buysell v2
# CD 6/14/20 Update algorithm not to sell all if new_buy_percent = 0 (lowers API calls and prevents negative cost basis)
# CD 6/14/20 Update algorithm to text if funds are low or if a ticker has not been traded in 5 days.


def ordering_bot(lock,transactions,errors):
    """
    Runs a bot to buy and sell stock. 
    Uses the transactions dictionary to set up parameters for when to buy and sell stock. 

    Within the transactions dictionary there are dictionaries for each stock. The keys of each stock dictionary are:
        First Buy - the price of the first buy for the stock (ignore if we already have orders in place)
        Order Quantity - the amount of stock to buy and sell for each transactions
        Available Balance - the amount of the money the stock has available for new purchases

        Previous Buy - the price of the previous successfully filled purchase of stock
        Average Buy - the average cost of the buying the stock currently owned
        Stock Owned - the amount of stock we currently own

        New Buy Proportion - if we own zero of this stock, buy at this proportion below the last sale price
        Buy Proportion - if the stock dips below the previous buy price by this proportion, buy again
        Sell Proportion - the proportion above the average buy price to sell all our stock

        Limit Buy ID - the order ID of a currently placed limit buy order
        Limit Buy Price - the price of a currently placed limit buy order
        Limit Sell ID - the order ID of a currently placed limit sell order
        Limit Sell Price - the price of a currently placed limit sell order

        Bid Price - the last bid price of the stock
        Stock Bought - the total amount of stock purchased by the bot
        Stock Sold - the total amount of stock sold by the bot

    
    Keys of the transactions dictionary that apply to all stocks
        Access Token - the token we use to access the TD Ameritrade site
        Access Expire Time - time the access token expires
        Max Buys - the number of buy orders we allow the bot to place without any sells (prevents continuous purchase of stock heading to zero)
        Last Requests - the last requests we made to the TD Ameritrade API (make sure we don't make more than two calls per second)
    """
    #Initialize min request index to 0 since no transactions have started yet
    min_request_index=0

    #Run this code until we encounter an error or trading hours have ended (include extended hours)
    open_time = datetime.datetime(2020,1,1,4,00,0,0).time()
    close_time = datetime.datetime(2020,1,1,17,0,0,0).time()
    open_time_seconds = datetime.timedelta(hours=open_time.hour,minutes=open_time.minute,seconds=open_time.second).total_seconds()

    #Continue looping while we don't have any errors
    while len(errors)==0:

        #Reset API errors list
        transactions['API Errors']=[]

        current = datetime.datetime.now()
        current_seconds = datetime.timedelta(hours=current.hour,minutes=current.minute,seconds=current.second).total_seconds()
        #Sleep until trading opens for the day
        if open_time_seconds>=current_seconds+60:
            time.sleep(open_time_seconds-current_seconds-60)
        if close_time<datetime.datetime.now().time():
            time.sleep(open_time_seconds+86300-current_seconds)

        #If the day is Saturday, sleep for two more days
        if datetime.datetime.now().weekday()==5:
            time.sleep(2*86300)

        while len(errors)==0 and open_time<=datetime.datetime.now().time() and close_time>=datetime.datetime.now().time():
            
            ############################### Get a new access token if we need it ##########################
            #Get the access token and the expire time of the access token.
            (transactions['Access Token'],transactions['Access Expire Time']) = get_access(transactions['Access Token'],transactions['Access Expire Time'])



            ############################### Get Bid  and Ask Price #########################
            lock.acquire()
            try:
                #Get quote information from API call
                new_quotes = get_multi_quotes(transactions['Access Token'],','.join(transactions['Tickers']))
                for ticker in transactions['Tickers']:
                    #For each ticker store the latest bid price
                    if ticker in new_quotes and 'bidPrice' in new_quotes[ticker] and 'askPrice' in new_quotes[ticker]:
                        transactions[ticker]['Bid Price'] = new_quotes[ticker]['bidPrice']
                        transactions[ticker]['Ask Price'] = new_quotes[ticker]['askPrice']

                transactions['Last Requests'][min_request_index]=time.time()
            except:
                transactions['API Errors'].append('Could not get quotes')

            last_requests=transactions['Last Requests']
            lock.release()
            #Make sure we are not making too many requests to the TD Ameritrade API
            min_request_index=check_request_times(last_requests)



            ############################### Place Limit Buy Orders #########################
            lock.acquire()
            #Make sure each ticker has a buy order in place
            for ticker in transactions['Tickers']:
                #If we don't have a buy order and we have funds to make another buy
                if transactions[ticker]['Limit Buy ID']==0:
                    #Place the new limit buy order for each ticker (for first buy and if all stock has been sold)
                    place_buy_order(transactions,ticker)
                    transactions['Last Requests'][min_request_index]=time.time()

                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade API
                min_request_index=check_request_times(last_requests)
            lock.release()


            ############################### Track Orders ###################################
            lock.acquire()
            for ticker in transactions['Tickers']:
                #Check if there are limit buy orders and the ask price dipped below the limit buy order
                if transactions[ticker]['Limit Buy Price']>0 and \
                    transactions[ticker]['Bid Price']<=transactions[ticker]['Limit Buy Price']:
                    #Track the buy order (remove from limit buy array if filled)
                    track_buy_orders(transactions,ticker)
                    transactions['Last Requests'][min_request_index]=time.time()

                #Check if there are limit sell orders and the bid price rose above the limit sell order
                elif transactions[ticker]['Limit Sell Price']>0 and \
                    transactions[ticker]['Ask Price']>=transactions[ticker]['Limit Sell Price']:
                    #Track the sell order (remove from limit sell arrays if filled)
                    track_sell_orders(transactions,ticker)
                    transactions['Last Requests'][min_request_index]=time.time()
            
                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade API
                min_request_index=check_request_times(last_requests)
            lock.release()


            ############################### Place/Replace Limit Sell Orders #########################
            lock.acquire()
            for ticker in transactions['Tickers']:
                #If we own stock and don't have a limit sell order placed, check if we should place a limit sell order
                if transactions[ticker]['Stock Owned']>0:
                    
                    #Place a limit sell order if we own stock and yet we don't have a limit sell order placed
                    if transactions[ticker]['Limit Sell ID']==0:
                        #Place the new limit sell order
                        place_sell_order(transactions,ticker)
                        transactions['Last Requests'][min_request_index]=time.time()
                    
                    #Place a limit sell order if we own stock, the current sell does not match the expected sell (average buy price * (1+sell proportion))
                    elif transactions[ticker]['Limit Sell Price'] != round(transactions[ticker]['Average Buy']*(1 + \
                        transactions[ticker]['Sell Proportion']),transactions[ticker]['Max Digits']):
                        #Replace the limit sell order
                        replace_sell_order(transactions,ticker)
                        transactions['Last Requests'][min_request_index]=time.time()

                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade API
                min_request_index=check_request_times(last_requests)
            lock.release()
            

            ############################### Cancel Buy Orders ########################
            lock.acquire()
            for ticker in transactions['Tickers']:
                #Cancel buy order when we successfully sold stock (new buy order closer to price can be placed)
                if transactions[ticker]['Previous Sell']>0 and transactions[ticker]['Limit Buy ID']>0:
                    #Cancel buy order on TD Ameritrade and remove it from buy arrays
                    cancel_buy_orders(transactions,ticker)   
                    transactions['Last Requests'][min_request_index]=time.time()

                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade site
                min_request_index=check_request_times(last_requests)
            lock.release()

        lock.acquire()

        #Get the access token and the expire time of the access token.
        (transactions['Access Token'],transactions['Access Expire Time']) = get_access(transactions['Access Token'],transactions['Access Expire Time'])

        #Track all the buy and sell orders to make sure we are up to date
        for ticker in transactions['Tickers']:

            #Check if there are limit buy orders
            if transactions[ticker]['Limit Buy Price']>0:
                #Track the buy order (remove from limit buy array if filled)
                track_buy_orders(transactions,ticker)
                transactions['Last Requests'][min_request_index]=time.time()

                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade API
                min_request_index=check_request_times(last_requests)
            
            #Check if there are limit sell orders
            if transactions[ticker]['Limit Sell Price']>0:
                #Track the sell order (remove from limit sell arrays if filled)
                track_sell_orders(transactions,ticker)
                transactions['Last Requests'][min_request_index]=time.time()
            
                last_requests=transactions['Last Requests']
                #Make sure we are not making too many requests to the TD Ameritrade API
                min_request_index=check_request_times(last_requests)

        #Save transactions dictionary
        pickle.dump(transactions,open("Transactions.p","wb"))

        lock.release()


def check_request_times(last_requests):
    """
    Checks if we are making too many api requests and get the latest request time index
    last_requests - last requests made to the site. 
        If all of these are within one second, wait before making another call.

    Returns the index of the latest request time in transaction['Last Requests']
    """
    copy_requests = last_requests.copy()
    copy_requests.sort()

    if (copy_requests[1]-copy_requests[0])<1 and (copy_requests[1]-copy_requests[0])>0:
        time.sleep(1-(copy_requests[1]-copy_requests[0])) #Sleep to make sure we don't have too many requests per second.
    return last_requests.index(min(last_requests)) #Min Index



def place_buy_order(transactions,ticker):
    """
    Code to interface with TD Ameritrade to place a limit order to buy stock
    This code assumes we currently have no stock of this ticker. 
    We are placing a buy order for the first time ('First Buy') or basing price on previous sell price

    transactions - dictionary of info related to bot transactions
            'Previous Sell' - last sale price of stock
            'New Buy Proportion' - proportion below previous sell to buy stock
            'First Buy' - buy price to make the first purchase of stock
            

    Returns the status code of the request.
    """
    if transactions[ticker]['Stock Owned']==0 and transactions[ticker]['Previous Sell']>0:
        #We sold the stock. Set new buy price at New Buy Proportion below previous sell
        buy_price = transactions[ticker]['Previous Sell']*(1-transactions[ticker]['New Buy Proportion'])
    elif transactions[ticker]['Stock Owned']>0:
        #Place another limit buy order Buy proportion below previous buy
        buy_price = transactions[ticker]['Previous Buy']*(1-transactions[ticker]['Buy Proportion'])
    else:
        #We haven't bought or sold any of this stock yet
        buy_price = transactions[ticker]['First Buy']

    #Round buy price according to number of digits allowed (2 digits for >$1 stocks, 4 digits for <$1 stocks)
    buy_price = round(buy_price,transactions[ticker]['Max Digits'])

    #Make sure we have the funds to buy before placing the order
    if transactions[ticker]['Available Balance'] > buy_price*transactions[ticker]['Order Quantity']:

        #Build the order leg collections for placing orders on TD Ameritrade
        orderLegCollection_buy = [{ 'instrument':{'symbol': ticker,'assetType':'EQUITY'},
                                    'instruction':'BUY',
                                    'quantity':transactions[ticker]['Order Quantity']}]

        #Create main order request
        buy_request = build_order_request('SEAMLESS','GOOD_TILL_CANCEL','LIMIT',orderLegCollection_buy,'SINGLE',str(buy_price))

        try:
            #Make the actual post request
            post_order_response = post_order(transactions['Access Token'],buy_request)

            #Check request to make sure it successfully posted
            if post_order_response.status_code==201:
                transactions[ticker]['Available Balance']-= buy_price*transactions[ticker]['Order Quantity']
                #Reset the previous sell since we have a new buy order in place
                transactions[ticker]['Previous Sell']=0

                response_headers=post_order_response.headers
                #Get the order id of the buy order from the headers
                if 'Location' in response_headers:
                    order_id = int(response_headers['Location'].split('orders/')[1])

                    transactions[ticker]['Limit Buy ID'] = order_id
                    transactions[ticker]['Limit Buy Price'] = buy_price
                        
            return post_order_response.status_code
        except:
            transactions['API Errors'].append('Could not place buy order for {} at price {}'.format(ticker,buy_price))
            return 0


def track_buy_orders(transactions,ticker):
    """
    Determines if we successfully bought stock with our limit order. Updates transactions limit buy list.
    transactions - dictionary containing information about transactions. 
        'Limit Buy ID' - the ID of the limit buy order (set to zero if filled)
        'Limit Buy Price' - the price of the limit buy order (set to zero if filled)
    ticker - the stock ticker we are trading

    """
    try:
        #Get the order
        limit_order=get_order_by_id(transactions['Access Token'],transactions[ticker]['Limit Buy ID'])
    
        #Check if the order was filled
        if limit_order['status']=='FILLED':

            #Reset limit buy arrays and add in amount of stock we have purchased
            transactions[ticker]['Limit Buy ID']=0
            transactions[ticker]['Limit Buy Price']=0
            transactions[ticker]['Stock Bought']+=limit_order['quantity']

            #Add in the last buy price and calculate the average cost of stock
            transactions[ticker]['Previous Buy']=limit_order['price']
            transactions[ticker]['Average Buy']=(transactions[ticker]['Average Buy']*transactions[ticker]['Stock Owned'] + \
                limit_order['price']*limit_order['quantity'])/(transactions[ticker]['Stock Owned']+limit_order['quantity'])
            transactions[ticker]['Stock Owned']+=limit_order['quantity']
    except:
        transactions['API Errors'].append('Could not get buy orders')


def track_sell_orders(transactions,ticker):
    """
    Determines if we successfully sold stock with our limit order. Updates transactions limit sell list.
    transactions - dictionary containing information about transactions. 
        'Limit Sell ID' - the ID of the limit sell order (set to zero if filled)
        'Limit Sell Price' - the price of the limit sell order (set to zero if filled)
    ticker - the stock ticker we are trading

    """
    try:
        #Get the order
        limit_order=get_order_by_id(transactions['Access Token'],transactions[ticker]['Limit Sell ID'])
    
        #Check if the order was filled
        if limit_order['status']=='FILLED':

            #Reset limit sell arrays and add in amount of stock sold
            transactions[ticker]['Limit Sell ID']=0
            transactions[ticker]['Limit Sell Price']=0
            transactions[ticker]['Stock Sold']+=limit_order['quantity']

            #Reset the previous buy price and average buy price since we already sold it
            transactions[ticker]['Previous Buy']=0
            transactions[ticker]['Average Buy']=0
            #Add in previous sell price and set stock owned to zero
            transactions[ticker]['Previous Sell']=limit_order['price']
            transactions[ticker]['Stock Owned']=0

            #Add profit to our balance
            transactions[ticker]['Available Balance']+=limit_order['price']*limit_order['quantity']
            transactions[ticker]['Last Fill']=0
        else:
            #Subtract of filled quantity (just in case it was partially filled)
            transactions[ticker]['Stock Owned']-=(limit_order['filledQuantity']-transactions[ticker]['Last Fill'])
            transactions[ticker]['Stock Sold']+=(limit_order['filledQuantity']-transactions[ticker]['Last Fill'])
            transactions[ticker]['Available Balance']+=(limit_order['filledQuantity']-transactions[ticker]['Last Fill'])*limit_order['price']
            transactions[ticker]['Last Fill']=limit_order['filledQuantity']
    except:
        transactions['API Errors'].append('Could not get sell orders')


def place_sell_order(transactions,ticker):
    """
    Uses the average price of bought stock to set a sell price

    transactions - dictionary of info related to bot transactions
            'Average Buy' - the average buy price of the stock
            'Sell Proportion' - proportion above the average buy to set limit sell order
    ticker - the stock we are trading
    """
    orderLegCollection_sell = [{'instrument':{'symbol': ticker,'assetType':'EQUITY'},
                            'instruction':'SELL',
                            'quantity':transactions[ticker]['Stock Owned']}]

    #Place sell order at sell proportion above the average buy cost
    sell_price = round(transactions[ticker]['Average Buy']*(1+transactions[ticker]['Sell Proportion']),transactions[ticker]['Max Digits'])

    #Create main order request
    sell_request = build_order_request('SEAMLESS','GOOD_TILL_CANCEL','LIMIT',orderLegCollection_sell,'SINGLE',str(sell_price))

    try:
        #Make the actual post request
        post_order_response = post_order(transactions['Access Token'],sell_request)

        #Check request to make sure it successfully posted
        if post_order_response.status_code==201:

            response_headers=post_order_response.headers
            #Get the order id of the buy order from the headers
            if 'Location' in response_headers:
                order_id = int(response_headers['Location'].split('orders/')[1])

                transactions[ticker]['Limit Sell ID'] = order_id
                transactions[ticker]['Limit Sell Price'] = sell_price
    
    except:
        transactions['API Errors'].append('Could not place buy order for {} at price {}'.format(ticker,sell_price))



def replace_sell_order(transactions,ticker):
    """
    Uses the average price of bought stock to reset the sale price

    transactions - dictionary of info related to bot transactions
            'Average Buy' - the average buy price of the stock
            'Sell Proportion' - proportion above the average buy to set limit sell order
    ticker - the stock we are trading
    """
    orderLegCollection_sell = [{'instrument':{'symbol': ticker,'assetType':'EQUITY'},
                            'instruction':'SELL',
                            'quantity':transactions[ticker]['Stock Owned']}]

    #Place sell order at sell proportion above the average buy cost
    sell_price = round(transactions[ticker]['Average Buy']*(1+transactions[ticker]['Sell Proportion']),transactions[ticker]['Max Digits'])

    #Create main order request
    sell_request = build_order_request('SEAMLESS','GOOD_TILL_CANCEL','LIMIT',orderLegCollection_sell,'SINGLE',str(sell_price))

    try:
        #Make the actual put request to replace order
        put_order_response = replace_order(transactions['Access Token'],transactions[ticker]['Limit Sell ID'],sell_request)

        #Check request to make sure it successfully posted
        if put_order_response.status_code==201:

            response_headers=put_order_response.headers
            #Get the order id of the buy order from the headers
            if 'Location' in response_headers:
                order_id = int(response_headers['Location'].split('orders/')[1])

                transactions[ticker]['Limit Sell ID'] = order_id
                transactions[ticker]['Limit Sell Price'] = sell_price
    
        #Try tracking the order to get latest information
        else:
            track_sell_orders(transactions,ticker)
    except:
        transactions['API Errors'].append('Could not REplace buy order for {} at price {}'.format(ticker,sell_price))



def cancel_buy_orders(transactions,ticker):
    """
    Cancels a currently placed buy order
    transactions - dictionary containing information about transactions. Add new information to this.
        'Limit Buy ID' - order ID of current limit buy
        'Limit Buy Price' - price of current limit buy
    ticker - the stock we are trading

    Returns: The status code of the delete request
    """
    try:
        #Cancel the order with the min price
        delete_response = delete_order(transactions['Access Token'],transactions[ticker]['Limit Buy ID'])

        if delete_response.status_code==200:
            #Add back the cost of the limit buy back to available balance and reset limit buy values
            transactions[ticker]['Available Balance'] += transactions[ticker]['Limit Buy Price']*transactions[ticker]['Order Quantity']
            transactions[ticker]['Limit Buy ID']=0
            transactions[ticker]['Limit Buy Price']=0

        return delete_response.status_code
    except:
        transactions['API Errors'].append('Could not cancel order for {} at price {}'.format(ticker,transactions[ticker]['Limit Buy Price']))
        return 0



        
#Functions to access the TD Ameritrade API. Make sure you have authenticated access to their site first.

import requests, requests, time, datetime, dateutil.parser,json
import TDAuth_Info

def get_access(access_token='',expire_time=0):
    """
    Gets a new access token if the old one already expired 
    access_token - token used to access the TD Ameritrade site
    expire_time - time in seconds since epoch when the token will expire
    """
    #Get a new access token if it expires or is five minutes away from exp#iration
    if (expire_time==0) or (len(access_token)==0) or (time.time()-expire_time>=-300):

        #API needed to authorize account with refresh token
        auth_url = 'https://api.tdameritrade.com/v1/oauth2/token'

        #Data needed for token
        data = {'grant_type':'refresh_token',
                'refresh_token':TDAuth_Info.refresh_token,
                'client_id':TDAuth_Info.client_id}

        #Post the data to get the token
        auth_reply_json = requests.post(url=auth_url,data=data)
        auth_reply=auth_reply_json.json()

        #Now use the token to get account information
        access_token = auth_reply['access_token']
        expire_time=time.time()+auth_reply['expires_in']
    
    return (access_token,expire_time)
        

def get_user_principals(access_token):
    """
    Get the user info and preferences for subscribing to the websocket and get the token timestamp as milliseconds
    access token - used to get information on my account
    """
    #Make request to user info and preferences to get principals for login
    user_url = 'https://api.tdameritrade.com/v1/userprincipals'
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    params = {'fields':'streamerSubscriptionKeys,streamerConnectionInfo'}
    user_principals_json = requests.get(url=user_url,headers=headers,params=params)
    user_principals = user_principals_json.json()

    #convert token timestamp to milliseconds (required for login to websocket)
    tokenTimeStamp = user_principals['streamerInfo']['tokenTimestamp']
    token_date = dateutil.parser.parse(tokenTimeStamp,ignoretz=True)
    epoch = datetime.datetime.utcfromtimestamp(0)
    tokenTimeStampAsMs = int((token_date-epoch).total_seconds()*1000.0)
    
    return (user_principals,tokenTimeStampAsMs)


def get_orders(access_token,start_date,end_date,status):
    """
    Get orders for the account in the specified date range on TD Ameritrade
    access_token - token used to access the TD Ameritrade site
    start_date - beginning time period to get orders (includes start_date in returned orders)
    end_date - ending time period to get orders (includes end_date in returned orders)
    status - the status of the orders to return (Ex: filled, queued)
    Returns the orders data in a dictionary format
    """

    orders_url = 'https://api.tdameritrade.com/v1/orders'
    headers={'Authorization': 'Bearer {}'.format(access_token)}
    #Parameters for the order
    params = {'accountId':TDAuth_Info.account_num,
              'fromEnteredTime': start_date,
              'toEnteredTime': end_date,
              'status': status}

    #Make the get request to TD Ameritrade
    orders_data_json = requests.get(url=orders_url,headers=headers,params=params)
    return orders_data_json.json()


def get_order_by_id(access_token,order_ID):
    """
    Gets a specific order
    access_token - used to login to TD Ameritrade site
    order_ID - the ID of the order we are getting
    """

    orders_url = 'https://api.tdameritrade.com/v1/accounts/{}/orders/{}'.format(TDAuth_Info.account_num,order_ID)
    headers={'Authorization': 'Bearer {}'.format(access_token)}

    #Make the get request to TD Ameritrade
    orders_data_json = requests.get(url=orders_url,headers=headers)
    return orders_data_json.json()


def delete_order(access_token,order_ID):
    """
    Deletes orders on the TD Ameritrade Site
    access_token - token used to access the TD Ameritrade site
    order_ID - the ID of the order to delete
    """
    orders_url = 'https://api.tdameritrade.com/v1/accounts/{}/orders/{}'.format(TDAuth_Info.account_num,order_ID)
    headers={'Authorization': 'Bearer {}'.format(access_token)}
    order_status = requests.delete(url=orders_url,headers=headers)
    return order_status


def post_order(access_token,json_request):
    """
    Posts an order to the TD Ameritrade website
    access_token - token used to access the TD Ameritrade site
    json_request - the order request in json format
    Returns the response to the post request
    """
    orders_url = 'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(TDAuth_Info.account_num)

    #The header for placing in order needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Post the order on TD Ameritrade and check the response
    post_order_response=requests.post(url=orders_url,headers=headers,json=json_request)

    return post_order_response


def replace_order(access_token,order_ID,json_request):
    """
    Replaces an order on the TD Ameritrade website
    access_token - token used to access the TD Ameritrade site
    order_ID - ID of the order to replace
    json_request - the new order request in json format to replace the old one
    Returns the response to the replace order request
    """
    orders_url = 'https://api.tdameritrade.com/v1/accounts/{}/orders/{}'.format(TDAuth_Info.account_num,order_ID)

    #The header for placing in order needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Post the order on TD Ameritrade and check the response
    replace_order_response=requests.put(url=orders_url,headers=headers,json=json_request)

    return replace_order_response


def build_order_request(session,duration,orderType,orderLegCollection,orderStrategy,price=''):
    """
    Build a request to the TD Ameritrade API
    session - trading session, 'Normal', 'AM', 'PM', 'SEAMLESS' for extended hours and day hours
    duration - 'DAY' or 'GOOD_TO_CANCEL'
    orderType - 'MARKET' or 'LIMIT'
    orderLegCollection - contains instruction ('BUY' or 'SELL'), symbol, assetType, quantity, etc
    orderStrategy - 'SINGLE', 'TRIGGER', or 'OCO' - one cancels the other
    price - if limit order, the price to buy or sell the order
    Returns an order requests. 
    """
    #Build order request based on parameters
    order_request = { 'session':session,
                       'duration':duration,
                       'orderType':orderType,
                       'orderLegCollection':orderLegCollection,
                       'orderStrategyType':orderStrategy}

    if len(price)>0:
        order_request['price']=price

    return order_request


def get_quote(access_token,ticker):
    """
    Get quote/price information for a stock
    access_token - token used to access the TD Ameritrade site
    ticker - the stock ticker symbol
    """
    quote_url = 'https://api.tdameritrade.com/v1/marketdata/{}/quotes'.format(ticker)

    #The header for getting a quote needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Make the get request to TD Ameritrade
    quote_data_json = requests.get(url=quote_url,headers=headers)
    return quote_data_json.json()


def get_multi_quotes(access_token,tickers):
    """
    Gets quotes for multiple ticker symbols
    access_token - token used to access the TD Ameritrade site
    tickers - comma delimited list of ticker symbols to get quotes for (Ex: 'MSFT,APPL,AMZN')
    """
    quote_url = 'https://api.tdameritrade.com/v1/marketdata/quotes'

    #The header for getting a quote needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Pass in the symbols as parameters
    params = {'symbol':tickers}

    #Make the get request to TD Ameritrade
    quote_data_json = requests.get(url=quote_url,headers=headers,params=params)
    return quote_data_json.json()



def get_price_history_lookback(access_token,ticker,periodType,period,frequencyType,frequency):
    """
    Get price history of a stock looking back from today
    access_token - token used to access the TD Ameritrade site
    ticker - the stock ticker symbol
    periodType - day, month, year, or ytd (default - day)
    period - the number of periods to show (default 10 days, 1 month, 1 year, 1 ytd)
    frequencyType - the frequency of data to return; minute (1-10 days only), daily, weekly, and monthly
    frequency - the number of frequency to be included in each candle (granularity of data) - 1 is default
                    1, 5, 10, 15, and 30 available for minute (only 1 for other types)
    """
    
    price_url = 'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(ticker)

    #The header for getting a quote needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Parameters for period of time and frequency of data to get
    params = {'periodType':periodType,
              'period': period,
              'frequencyType': frequencyType,
              'frequency': frequency}
                
    #Make the get request to TD Ameritrade
    price_history_json = requests.get(url=price_url,headers=headers,params=params)
    return price_history_json.json()
    


def get_price_history_dates(access_token,ticker,start_date,end_date,frequencyType,frequency):
    """
    Get price history of a stock using provided dates

    I recommend using this for only minute level data for 1-10 days. 
    Use the lookback function for other periods since it says bad request when trying other dates.

    Note: It seems TD Ameritrade only stores two months of data for detail of one minute
          TD Ameritrade stores 8 months of data for detail of 5, 10, 15, and 30 minutes

    access_token - token used to access the TD Ameritrade site
    ticker - the stock ticker symbol
    startDate - in milliseconds since epoch
    endDate - in milliseconds since epoch (default is yesterday)
    frequencyType - the frequency of data to return; minute (day only), daily, weekly, and monthly
    frequency - the number of frequency to be included in each candle (granularity of data) - 1 is default
                    1, 5, 10, 15, and 30 available for minute (only 1 for other types)
    """
    
    price_url = 'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(ticker)

    #The header for getting a quote needs to define the input type (json)
    headers = {'Authorization':'Bearer {}'.format(access_token),
               'Content-Type':'application/json'}

    #Parameters for period of time and frequency of data to get
    params = {'startDate':start_date,
              'endDate': end_date,
              'frequencyType': frequencyType,
              'frequency': frequency}
                
    #Make the get request to TD Ameritrade
    price_history_json = requests.get(url=price_url,headers=headers,params=params)
    return price_history_json.json()
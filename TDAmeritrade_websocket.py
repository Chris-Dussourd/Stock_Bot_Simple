
from websocket import create_connection
from TDAmeritrade_API import get_access
import time, urllib.parse, json

def login_websocket(ws,user_principals,tokenTimeStampAsMs,errors):
    """
    Logs into the websocket using user principals information
    ws - websocket object, assumes a connection has already been created
    user_principals - user info and preferences obtained by making API call to TD Ameritrade site
    tokenTimeStampAsMs - timestamp in milliseconds used to login
    errors - keeps track of errors

    Returns the login response from the TD Websocket
    """
    #Create the login request using info from user info and preferences
    credentials = { 'userid':user_principals['accounts'][0]['accountId'],
                    'token':user_principals['streamerInfo']['token'],
                    'company':user_principals['accounts'][0]['company'],
                    'segment':user_principals['accounts'][0]['segment'],
                    'cddomain':user_principals['accounts'][0]['accountCdDomainId'],
                    'usergroup':user_principals['streamerInfo']['userGroup'],
                    'accesslevel':user_principals['streamerInfo']['accessLevel'],
                    'authorized':'Y',
                    'timestamp':tokenTimeStampAsMs,
                    'appid':user_principals['streamerInfo']['appId'],
                    'acl':user_principals['streamerInfo']['acl']}

    login_request = {'requests':[{  'service':'ADMIN',
                                    'requestid':'0',
                                    'command':'LOGIN',
                                    'account':user_principals['accounts'][0]['accountId'],
                                    'source':user_principals['streamerInfo']['appId'],
                                    'parameters':{
                                        'credential':urllib.parse.urlencode(credentials),
                                        'token':user_principals['streamerInfo']['token'],
                                        'version':'1.0',
                                        'qoslevel':'0'}}]}

    login_request_json = json.dumps(login_request)

    try: 
        #Login to the websocket
        ws.send(login_request_json)
        login_reply_json=ws.recv()
        login_reply=json.loads(login_reply_json)
        if 'response' not in login_reply or 'content' not in login_reply['response'][0] \
            or 'code' not in login_reply['response'][0]['content'] or login_reply['response'][0]['content']['code']!=0:
            #Did not successfully login to the websocket
            errors.append('Unsuccessful login attempt to websocket.')
    except:
        errors.append('Failed to login to websocket.')
        

def refresh_access(ws,lock,transactions,errors):
    """
    Ping the connection every 4.5 seconds to make sure I continue to receive data.

    ws - websocket server to ping (keep active)
    errors - array of errors. If this is not empty, end the loop
    """
    n=0
    #While there are not errors in this thread or others, keep pinging the websocket and getting new access token
    while len(errors)==0:
        #Ping every 4.5 seconds
        time.sleep(270)
        n+=1 #Number of sleeps since last refresh
        try:
            #Ping the websocket
            ws.ping()
            #After six 4.5 minute sleeps, get a new access token. (it expires every 30 minutes)
            if n==6:
                lock.acquire()
                (transactions['Access Token'],transactions['Access Expire Time']) = get_access()
                lock.release()
                n=0 #Reset count
        except:
            #Add a value to error array
            errors.append('Unable to maintain connection to websocket')
        

def subscribe_quote_websocket(ws,user_principals,request_id,symbol,fields,errors):
    """
    Subscribe to a stock quote websocket. 
    ws - websocket server
    requestid - request number made to websocket (must be unique to other requests)
    symbol - comma delimited string of symbols that contains the ticker symbols we are subscribing to
    fields - comma delimited string of numbers that contains which fields we are subscribing to
        Ex:  1 - Bid Price
             2 - Ask Price
             3 - Last Price 
    errors - list of errors, adds to the error list if unable to subscribe
    """
    #Make a request for price info
    price_request = {'requests':[{'service':'QUOTE',
                    'requestid':request_id,
                    'command':'SUBS',
                    'account':user_principals['accounts'][0]['accountId'],
                    'source':user_principals['streamerInfo']['appId'],
                    'parameters':{'keys':symbol,
                                'fields':fields}}]}
    try:
        price_request_json=json.dumps(price_request)
        ws.send(price_request_json)

        #Get the response. First response contains heartbeat. Second one contains subscription message
        ws.recv()
        quote_reply_json=ws.recv()
        quote_reply=json.loads(quote_reply_json)
        if 'response' not in quote_reply or 'content' not in quote_reply['response'][0] \
            or 'code' not in quote_reply['response'][0]['content'] or quote_reply['response'][0]['content']['code']!=0:
            #Did not successfully subscribe to the websocket
            errors.append('Unable to subscribe to websocket to information on level one quote.')

    except:
        errors.append('Unable to subscribe to websocket to information on level one quote.')
        return ''


def read_websocket(ws,lock,transactions,errors):
    """
    Listens in the websockets for stock price updates 

    ws - TD Ameritrade websocket server to get stock price 
    lock - lock for updating transactions dictionary
    transactions - dictionary of information on stock trading transactions
    errors - array of errors. If this is not empty, end the loop
    """
    while len(errors)==0:
        try:
            #Retrieve data from websocket server
            data = ws.recv()
            received_message = json.loads(data)

            #Check if message received contains price updates
            if 'data' in received_message and 'content' in received_message['data'][0]:
                lock.acquire()
                #New bid price information
                if '1' in received_message['data'][0]['content'][0]:
                    transactions['Bid Price']=received_message['data'][0]['content'][0]['1']
                #New ask price information
                if '2' in received_message['data'][0]['content'][0]:
                    transactions['Ask Price']=received_message['data'][0]['content'][0]['2']
                #New price information
                if '3' in received_message['data'][0]['content'][0]:
                    transactions['Current Price']=received_message['data'][0]['content'][0]['3']
                lock.release()

            """ Not sure if i want to get acct activity from websocket if it takes a few minutes to update.
            elif received_message['type']=='user':
                lock.acquire()
                #If we successfully bought Bitcoin

                    #Add transaction to Recent Buys and Buy History arrays
                    transactions['Recent Buys'].append('test')
                
                #If we successfully sold Bitcoin or cancelled due to self-trade
                #!!!!!!!!Update this when decrement and cancel is no longer allowed. (it will cancel newest order)

                    #Add transaction to Sell History array
                    transactions['Recent Sells'].append('test')

                #If order was canceled for reason other than self-trade

                    #Add to canceled order array
                    transactions['Canceled Orders'].append('test')
            """
        except:
            errors.append('Failed to read data from websocket.')
            
    

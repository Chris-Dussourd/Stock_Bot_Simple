
import threading,pyodbc,pickle
from TDAmeritrade_API import *
from TDAmeritrade_algorithm_buysell import ordering_bot,check_request_times
from TDAmeritrade_user import user_interface
from TDAmeritrade_odbc import store_results,retrieve_open_orders
from TDAmeritrade_excel import save_results

#This Bot places limit buy and sell orders on Stock.
#It takes divides the money availble and places limit buys based on market conditions.
#If price is lower place more limit buy orders with available cash. 
#If the price is higher, place limit buy orders at the higher price. 
#The goal is to keep the bot close to market prices to maximize buying and selling.

#Description of threading - This bot creates 4 threads.
#   Thread 1: Keeps websocket channel open to TD Ameritrade websocket
#   Thread 2: Checks websocket for updates in price and bot's orders
#   Thread 3: Places new limit buy and sell orders
#   Thread 4: Looks for user's input and stops for debugging

def time_diff(time_1,time_2):
    """
    Check the difference in days (to neareast hour) between time_2 and time_1
    time_1 - datetime object
    time_2 - datetime object
    Returns the difference between the two times to the nearest second
    """
    time_delta=time_2-time_1
    time_difference=time_delta.days*24*60*60+time_delta.seconds
    return time_difference #In seconds


def run_bot(transactions):
    """
    Runs a bot to buy and sell stock. 
    Loads the transactions dictionary to set up parameters for when to buy and sell stock. 

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

    Stores latest results of transaction dictionary as a pickle file
    """
    #Keep track of any errors
    errors=[]

    #Start multithreading
    lock=threading.Lock() #Lock for transactions dictionary
    #Thread 1 - Place limit buys and limit sell orders on TD Ameritrade site
    ordering_thread=threading.Thread(target=ordering_bot,args=(lock,transactions,errors,))
    #Thread 2 - Check for user input and provide user with details on transactions and status
    user_thread=threading.Thread(target=user_interface,args=(lock,transactions,errors,))

    #Start the threads
    ordering_thread.start()
    user_thread.start()

    #Wait for the threads to join
    ordering_thread.join()
    user_thread.join()

    print("-------------")
    print("-------------")
    print("-------------")
    print("Here is a list of errors that ended the run.")
    print(errors)
    print("-------------")
    print("-------------")
    print("-------------")
    print(transactions)

    return errors
    








    
            

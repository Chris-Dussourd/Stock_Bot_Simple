

#Functions to interact with the user of bot
# update_user - Gives an update message to user about current status of bot and transactions made.

import datetime


def user_interface(lock,transactions,errors):
    """
    User interaction. User can get information about the transactions
    """
    user_input="Random"
    while len(errors)==0:
        try:
            while user_input!="Check" and user_input!="Stop":
                user_input=input("Enter 'Check' to check the status of bot or 'Stop' to stop it: ")
            
            if user_input=="Check":
                lock.acquire()
                print("--------------------")
                print("--------------------")
                print(transactions)
                print("--------------------")
                print("--------------------")
                lock.release()
                #Reset user_input
                user_input="Random"
            elif user_input=="Stop":
                errors.append('User asked to stop bot.')
        except:
            errors.append('Error in user interface.')

"""
    print("----------------------------")
    print("----------------------------")
    print("Update: ",datetime.datetime.now())
    print("\n Current Balance: ",transactions['Current Balance'])
    print("Available Balance: ",transactions['Available Balance'])
    if len(transactions['Limit Buys'])>0:
        print("Current limit buy orders: ",transactions['Limit Buys'][0])
    else:
        print("Current limit buy orders: None")
    print("Buy Cost (per limit order): ",transactions['Buy Cost'])
    if len(transactions['Limit Sells'])>0:
        print("Current limit sell orders: ",transactions['Limit Sells'][0])
    else:
        print("Current limit sell orders: None")
    current_price=get_bitcoin_price()
    print("Current price of Bitcoin: ",current_price)
    print("Bitcoin owned: ", transactions['Bitcoin Purchased'])
    print("Transaction Made: ",transactions['Number Transactions'])
    estimate_profit=transactions['Current Balance']+transactions['Bitcoin Purchased']*current_price
    print('Estimated Profit: ',estimate_profit)
"""
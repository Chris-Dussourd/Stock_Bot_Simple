# Authenticate the TD Ameritrade developer app and get a refresh token.
# Refresh tokens expire after 90 days. Access tokens expire after 30 minutes. Use the refresh token to get updated access tokens.

from splinter import Browser
import requests
import urllib.parse
from TDAuth_Info import consumer_key,redirect_uri,client_id,username,password,driver_path

#Create a new chrome browser
#Note: you will need to update the chrome driver in your driver path to match that of your latest version of google chrome.
executable_path = {'executable_path':driver_path}
browser=Browser('chrome',**executable_path,headless=False)

#Information needed to authenticate my TD account
auth_url='https://auth.tdameritrade.com/auth'

#Params pass into authenticate url in order to obtain a code
params_temp={'response_type' : 'code',
             'redirect_uri' : redirect_uri,
             'client_id' : client_id}

params=urllib.parse.urlencode(params_temp)

#Newly created url that asks users to authenticate themselves
authorization_url = auth_url + '?' + params

#Visit the website with the browser and fill out the form
browser.visit(authorization_url)
username_browser = browser.find_by_id('username0').fill(username)
password_browser = browser.find_by_id('password').fill(password)
#Click the login button
submit = browser.find_by_id('accept').first.click()

#User selects two factor authentication method and types in the code. Waits for user to say 'Done'
user_input = input('Type "Done" when you have successfully completed two factor authentication:  ')

if user_input == 'Done':
    #Grab the url from the browser (mainly the info after the code)
    new_url = browser.url
    parse_url = urllib.parse.unquote(new_url.split('code=')[1])

    #browser.quit() 

    #Define information needed to get an access and refresh token
    api_url = r'https://api.tdameritrade.com/v1/oauth2/token'
    headers = {'Content-Type':"application/x-www-form-urlencoded"}
    data = {'grant_type':'authorization_code',
            'access_type':'offline',
            'code':parse_url,
            'client_id':client_id,
            'redirect_uri':redirect_uri}

    #Post the data to get the token
    auth_reply_json = requests.post(url=api_url,headers=headers,data=data)
    auth_reply=auth_reply_json.json()

    #Get the access and refresh token
    access_token = auth_reply['access_token']
    refresh_token = auth_reply['refresh_token']

    print('Refresh token: ' + refresh_token)
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, StringProperty
from kivy.event import EventDispatcher
from kivy.network.urlrequest import UrlRequest
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
import certifi
# Python imports
import sys
sys.path.append("/".join(x for x in __file__.split("/")[:-1]))
from json import dumps
import os.path
import progressspinner
import functools
import datetime as dt
# Load the kv files
folder = os.path.dirname(os.path.realpath(__file__))
Builder.load_file(folder + "/themedwidgets.kv")
Builder.load_file(folder + "/signinscreen.kv")
Builder.load_file(folder + "/createaccountscreen.kv")
Builder.load_file(folder + "/welcomescreen.kv")
Builder.load_file(folder + "/loadingpopup.kv")
Builder.load_file(folder + "/createshopaccountscreen.kv")
Builder.load_file(folder + "/isashop.kv")
Builder.load_file("kvs/forgotpassword.kv")

# Import the screens used to log the user in
from welcomescreen import WelcomeScreen
from signinscreen import SignInScreen
from createaccountscreen import CreateAccountScreen
from createshopaccountscreen import CreateShopAccountScreen
from isashop import IsAShopScreen

# Template for firebaseloginscreen.py taken from https://github.com/Dirk-Sandberg/FirebaseLoginScreen
# Please refer to the LICENSE file

import requests
import json

class FirebaseLoginScreen(Screen, EventDispatcher):
    """To use this module, instantiate the login screen
    in the KV language like so:
    FirebaseLoginScreen:
        web_api_key: "your_firebase_web_api_key"
        on_login_success:
            # do something here

    NOTES:
    1) You MUST set the web api key.
    2) You probably want to switch screens to a Screen in your project once the
    user has logged in.
    """

    # Firebase Project meta info - MUST BE CONFIGURED BY DEVELOPER
    web_api_key = StringProperty()  # From Settings tab in Firebase project

    # Firebase Authentication Credentials - what developers want to retrieve
    refresh_token = ""
    localId = ""
    idToken = ""

    # Properties used to send events to update some parts of the UI
    login_success = BooleanProperty(False)  # Called upon successful sign in
    sign_up_msg = StringProperty()
    sign_in_msg = StringProperty()
    email_exists = BooleanProperty(False)
    email_not_found = BooleanProperty(False)

    debug = False
    popup = Factory.LoadingPopup()
    popup.background = folder + "/transparent_image.png"


    def on_login_success(self, *args):
        """Overwrite this method to switch to your app's home screen.
        """
        print("Logged in successfully", args)

    def on_web_api_key(self, *args):
        """When the web api key is set, look for an existing account in local
        memory.
        """
        # Try to load the users info if they've already created an account
        self.refresh_token_file = App.get_running_app().user_data_dir + "/refresh_token.txt"
        if self.debug:
            print("Looking for a refresh token in:", self.refresh_token_file)
        if os.path.exists(self.refresh_token_file):
            self.load_saved_account()
            #pass

    def sign_up(self, email, password, username,phone, shopname=None, zipcode=None, admin=False):
        """If you don't want to use Firebase, just overwrite this method and
        do whatever you need to do to sign the user up with their email and
        password.
        """

        if self.debug:
            print("Attempting to create a new account: ", email, password)
        signup_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key=" + self.web_api_key
        signup_payload = dumps(
            {"email": email, "password": password, "username": username, "returnSecureToken": "true"})

        sign_up_request = UrlRequest(signup_url, req_body=signup_payload,
                   on_success=functools.partial(self.successful_signup, username,shopname, zipcode,admin, email, phone),
                   on_failure=self.sign_up_failure,
                   on_error=self.sign_up_error, ca_file=certifi.where())



    def successful_login(self, urlrequest, log_in_data):
        """Collects info from Firebase upon successfully registering a new user.
        """

        self.hide_loading_screen()
        self.refresh_token = log_in_data['refreshToken']
        self.localId = log_in_data['localId']
        self.idToken = log_in_data['idToken']
        print("AM I GETTING HEREEEEEE")
        self.save_refresh_token(self.refresh_token)
        self.login_success = True
        if self.debug:
            print("Successfully logged in a user: ", log_in_data)


    def successful_signup(self, username, shopname, zipcode, admin, email, phone, urlrequest, log_in_data):

        #print(username)
        self.hide_loading_screen()
        self.refresh_token = log_in_data['refreshToken']
        self.localId = log_in_data['localId']
        self.idToken = log_in_data['idToken']
        #print("I GOT HEREEEE!!!")
        self.save_refresh_token(self.refresh_token)

        stock_image = "./images/BabyYoda.png"
        post = "Promotions coming soon!"
        expiration = "12/10/2020, 01:00:00"
        if self.debug:
            print("Successfully logged in a user: ", log_in_data)

        if admin:
            user_info = '{"username":"%s","shopname":"%s","zipcode":"%s" ,"admin":true, "content": "%s", "post": "%s", "expiration": "%s" , "facebook_id": "", "insta_id": "", "email": "%s", "phone": "%s"}' % (username, shopname,zipcode, stock_image,post,expiration, email, phone)
            fave_info = '{" " : true}'
            current_date = str(dt.datetime.now().strftime("%Y-%m-%d"))
            availability = '{"%s" : {"8am-9am" : true, "9am-10am" : true, "10am-11am" : true, "11am-12pm" : true, "1pm-2pm" : true, "2pm-3pm" : true, "3pm-4pm" : true, "4pm-5pm" : true}}' % (current_date)

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                                  "/favorites.json?auth=" + self.idToken, data=fave_info)

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                                  "/availability.json?auth=" + self.idToken, data=availability)

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                                  ".json?auth=" + self.idToken, data=user_info)


        else:
            user_info = '{"username":"%s", "admin":false, "email": "%s", "phone": "%s"}' % (username, email, phone)
            fave_info = '{" " : true}'
            notify_info = '{" " : true}'

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                                "/favorites.json?auth=" + self.idToken, data=fave_info)

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                                  "/notifyinfo.json?auth=" + self.idToken, data=notify_info)

            post = requests.patch("https://nappyhour-6eb5d.firebaseio.com/" + self.localId +
                           ".json?auth=" + self.idToken, data = user_info)

        self.login_success = True





    def sign_up_failure(self, urlrequest, failure_data):
        """Displays an error message to the user if their attempt to log in was
        invalid.
        """
        self.hide_loading_screen()
        self.email_exists = False  # Triggers hiding the sign in button
        print(failure_data)
        msg = failure_data['error']['message'].replace("_", " ").capitalize()
        # Check if the error msg is the same as the last one
        if msg == self.sign_up_msg:
            # Need to modify it somehow to make the error popup display
            msg = " " + msg + " "
        self.sign_up_msg = msg
        if msg == "Email exists":
            self.email_exists = True
        if self.debug:
            print("Couldn't sign the user up: ", failure_data)

    def sign_up_error(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Sign up Error: ", args)

    def sign_in(self, email, password):
        """Called when the "Log in" button is pressed.

        Sends the user's email and password in an HTTP request to the Firebase
        Authentication service.
        """
        if self.debug:
            print("Attempting to sign user in: ", email, password)
        sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + self.web_api_key
        sign_in_payload = dumps(
            {"email": email, "password": password, "returnSecureToken": True})
        print(sign_in_payload)
        print("OOOOOOOO")
        UrlRequest(sign_in_url, req_body=sign_in_payload,
                   on_success=self.successful_login,
                   on_failure=self.sign_in_failure,
                   on_error=self.sign_in_error, ca_file=certifi.where())



    def sign_in_failure(self, urlrequest, failure_data):
        """Displays an error message to the user if their attempt to create an
        account was invalid.
        """
        self.hide_loading_screen()
        self.email_not_found = False  # Triggers hiding the sign in button
        print(failure_data)
        msg = failure_data['error']['message'].replace("_", " ").capitalize()
        # Check if the error msg is the same as the last one
        if msg == self.sign_in_msg:
            # Need to modify it somehow to make the error popup display
            msg = " " + msg + " "
        self.sign_in_msg = msg
        if msg == "Email not found":
            self.email_not_found = True
        if self.debug:
            print("Couldn't sign the user in: ", failure_data)

    def sign_in_error(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Sign in error", args)

    def reset_password(self, email):
        """Called when the "Reset password" button is pressed.
        """
        
        print("testing password reset")
        if self.debug:
            print("Attempting to send a password reset email to: ", email)
        reset_pw_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key=" + self.web_api_key
        reset_pw_data = dumps({"email": email, "requestType": "PASSWORD_RESET"})

        UrlRequest(reset_pw_url, req_body=reset_pw_data,
                   on_success=self.successful_reset,
                   on_failure=self.sign_in_failure,
                   on_error=self.sign_in_error, ca_file=certifi.where())

    def delete_account(self, email):
        print("testing delete account")
        delete_acct_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/deleteAccount" + self.web_api_key
        delete_acct_data = dumps({"email": email, "requestType": "DELETE_ACCOUNT"})

        UrlRequest(delete_acct_url, req_body=delete_acct_data,
                    ca_file=certifi.where())


    #def update_pw(self,email, newpassword):
     #   new_pw_url = "https://nappyhour-6eb5d.firebaseapp.com/__/auth/action?mode=action&oobCode=code" + self.web_api_key
     #   new_pw_data = dumps({"email":email, "password": newpassword})

      #  UrlRequest(new_pw_url, req_body=new_pw_data,
       #            on_success=self.successful_reset,
       #            on_failure=self.sign_in_failure,
       #            on_error=self.sign_in_error, ca_file=certifi.where())


    def successful_reset(self, urlrequest, reset_data):
        """Notifies the user that a password reset email has been sent to them.
        """
        self.hide_loading_screen()
        if self.debug:
            print("Successfully sent a password reset email", reset_data)
        self.sign_in_msg = "Reset password instructions sent to your email."

    def save_refresh_token(self, refresh_token):
        """Saves the refresh token in a local file to enable automatic sign in
        """
        if self.debug:
            print("Saving the refresh token to file: ", self.refresh_token_file)
        with open(self.refresh_token_file, "w") as f:
            f.write(refresh_token)

    def load_refresh_token(self):
        """Reads the refresh token from local storage.
        """
        if self.debug:
            print("Loading refresh token from file: ", self.refresh_token_file)
        with open(self.refresh_token_file, "r") as f:
            self.refresh_token = f.read()

    def load_saved_account(self):
        """Uses the refresh token to get the user's idToken and localId by
        sending it as a request to Google/Firebase's REST API.

        Called immediately when a web_api_key is set and if the refresh token
        file exists.
        """
        if self.debug:
            print("Attempting to log in a user automatically using a refresh token.")
        self.load_refresh_token()
        refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + self.web_api_key
        refresh_payload = dumps({"grant_type": "refresh_token", "refresh_token": self.refresh_token})
        UrlRequest(refresh_url, req_body=refresh_payload,
                   on_success=self.successful_account_load,
                   on_failure=self.failed_account_load,
                   on_error=self.failed_account_load, ca_file=certifi.where())

    def successful_account_load(self, urlrequest, loaded_data):
        """Sets the idToken and localId variables upon successfully loading an
        account using the refresh token.
        """
        self.hide_loading_screen()
        if self.debug:
            print("Successfully logged a user in automatically using the refresh token")
        self.idToken = loaded_data['id_token']
        self.localId = loaded_data['user_id']
        self.login_success = True

    def failed_account_load(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Failed to load an account.", args)

    def display_loading_screen(self, *args):
        self.popup.color = self.tertiary_color
        self.popup.open()

    def hide_loading_screen(self, *args):
        self.popup.dismiss()



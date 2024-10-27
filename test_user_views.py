"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows
from flask import url_for

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
os.environ['DATABASE_URL'] = "postgresql://postgres:17273185@localhost/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class UserViewTestCase(TestCase):

    # HELPERS

    def requery_user(self, user_id):
        """ Helper to re-query a user from database """
        
        return User.query.get(user_id)

    
    def do_login(self, client, user):
        """Helper to log a user in """

        with client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user.id

    
    ####################################################


    def setUp(self):

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        db.session.commit()


    def tearDown(self):

        db.session.remove()


    def test_homepage(self):
        
        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@testuser</p>', html)


    def test_home_anon_page(self): 

        with self.client as c:

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>What's Happening?</h1>", html)


    def test_list_all_users(self):

        with self.client as c:

            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            users = User.query.all()

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertEqual(len(users), 1)


    def test_list_search_users(self):

        with self.client as c:

            resp = c.get('/users?q=testuser')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertNotIn("other testuser", html)


    def test_users_show(self):

        first_msg = Message(text="first testing message")
        second_msg = Message(text="second testing message")

        self.testuser.messages.append(first_msg)
        self.testuser.messages.append(second_msg)

        with self.client as c:

            resp = c.get(f'/users/{ self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            for msg in self.testuser.messages:
                self.assertIn(msg.text, html)


    def test_uers_likes(self):

        first_msg = Message(text="first testing message")
        second_msg = Message(text="second testing message")

        self.testuser.messages.append(first_msg)
        self.testuser.messages.append(second_msg)

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        second_user.likes.append(first_msg)
        second_user.likes.append(second_msg)
     
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = second_user.id

            # Without re-querying, it triggeers `DetachedInstanceError`
            second_user = self.requery_user(second_user.id)

            resp = c.get(f'/users/{ second_user.id }/likes')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            for msg in second_user.likes:
                self.assertIn(msg.text, html)
                self.assertIn(msg.user.username, html)
                self.assertIn(msg.timestamp.strftime('%d %B %Y'), html)


    def test_show_followings(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        third_user = User.signup(username="third user",
                                email="thirdtest@test.com",
                                password="thirdtestuser",
                                image_url=None)

        self.testuser.following.append(second_user)
        self.testuser.following.append(third_user)

        db.session.commit()
        
        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.get(f'/users/{ self.testuser.id }/following')
            html = resp.get_data(as_text=True)

            user = self.requery_user(self.testuser.id)

            self.assertEqual(resp.status_code, 200)
            for followed_user in user.following:
                self.assertIn(followed_user.username, html)
                self.assertIn("Unfollow", html)
                self.assertNotIn("<button>Follow</button>", html)


    def test_show_followings_unauthorized_access(self):

        with self.client as c:

            resp = c.get(f'/users/{ self.testuser.id }/following', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_users_followers(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        third_user = User.signup(username="third user",
                                email="thirdtest@test.com",
                                password="thirdtestuser",
                                image_url=None)

        self.testuser.followers.append(second_user)
        self.testuser.followers.append(third_user)

        db.session.commit()

        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.get(f'/users/{ self.testuser.id }/followers')
            html = resp.get_data(as_text=True)

            user = self.requery_user(self.testuser.id)

            self.assertEqual(resp.status_code, 200)
            for follower in user.followers:
                self.assertIn(follower.username, html)
                self.assertIn("Follow", html)
                self.assertNotIn("<button>Unfollow</button>", html)


    def test_users_followers_unauthorized_access(self):

        with self.client as c:

            resp = c.get(f'/users/{ self.testuser.id }/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_add_follow(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        db.session.commit()

        # After commiting, `second_user` becomes detached, 
        # so re-query `second_user` to bind it to the 
        # current session.
        followed_user = self.requery_user(second_user.id)

        with self.client as c:
            self.do_login(c, self.testuser)
            
            resp = c.post(f'/users/follow/{ followed_user.id }', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(followed_user.username, html)
            self.assertNotIn("Follow</button>", html)

    
    def test_add_follow_unauthorized_access(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        db.session.commit()

        # After commiting, `second_user` becomes detached, 
        # so re-query `second_user` to bind it to the 
        # current session.
        followed_user = self.requery_user(second_user.id)

        with self.client as c:

            resp = c.post(f'/users/follow/{ followed_user.id }', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_stop_following(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        self.testuser.following.append(second_user)
        db.session.commit()

        # After commiting, `second_user` becomes detached, 
        # so re-query `second_user` to bind it to the 
        # current session.
        followed_user = self.requery_user(second_user.id)

        with self.client as c:
            self.do_login(c, self.testuser)
        
            resp = c.post(f'/users/stop-following/{ followed_user.id }', follow_redirects=True)
            html = resp.get_data(as_text=True)

            user = self.requery_user(self.testuser.id)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(followed_user.username, html)
            self.assertNotIn("Follow</button>", html)

    def test_stop_following_unauthorized_access(self):

        second_user = User.signup(username="second user",
                                email="secondtest@test.com",
                                password="secondtestuser",
                                image_url=None)

        db.session.commit()

        # After commiting, `second_user` becomes detached, 
        # so re-query `second_user` to bind it to the 
        # current session.
        followed_user = self.requery_user(second_user.id)

        with self.client as c:

            resp = c.post(f'/users/stop-following/{ followed_user.id }', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_profile_with_get_request(self):
        
        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.get(f'/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.username, html)
            self.assertIn(self.testuser.email, html)
            self.assertIn(self.testuser.image_url, html)

    def test_profile_with_post_request(self):

        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.post(f'/users/profile', data={'password': 'testuser'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Profile updated successfully!", html)

    def test_profile_unauthorized_access(self):

        with self.client as c:

            resp = c.post('/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_delete_user(self):
        
        with self.client as c:
            self.do_login(c, self.testuser)

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sign me up!", html)
        
    def test_delete_user_unauthorized_access(self):

        with self.client as c:

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
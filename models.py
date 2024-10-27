"""SQLAlchemy models for Warbler."""

# Import datetime module for handling date and time
from datetime import datetime
# Import Bcrypt for password hashing
from flask_bcrypt import Bcrypt
# SQLAlchemy for ORM (Object Relational Mapping) with Flask
from flask_sqlalchemy import SQLAlchemy

# Create an instance of Bcrypt for pw hashing
bcrypt = Bcrypt()
# Create an instance of SQLAlchemy to interact with the database
db = SQLAlchemy()


class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    # Establishes a many-to-many relationship between users

    # Specifies the name of database table
    __tablename__ = 'follows'

    # To track the approval status of follow requests for private accounts
    is_approved = db.Column(
        db.Boolean, 
        default=False
    )

    # Define a foreign key column for user being followed
    # `ondelete="cascade"`, if a user is deleted from the user table, 
    # all corresponding entries in the follows table will also be deleted
    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    # Define a foreign key column for the user who is following
    # `ondelete="cascade"`, if a user is deleted from the user table, 
    # all corresponding entries in the follows table will also be deleted
    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    # `user_following_id` should be used to link this relationship to `User`.
    user_following = db.relationship('User', foreign_keys=[user_following_id])



class Likes(db.Model):
    """Mapping user likes to warbles."""

    # Specifies database table name
    __tablename__ = 'likes' 

    # Define a primary key column
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Define a foreign key column in `users` table
    # deletes cascade if a user is deleted
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    # Define a foreign key column in `messages` table
    # deletes cascade if a message is deleted
    ######
    # Ensure that each message can only be liked once ######
    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade'),
        unique=True
    )


class User(db.Model):
    """User in the system."""

    # Specifies the database table name
    __tablename__ = 'users'

    # Define a primary key column
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Define a email column
    # email cannot be null
    # ensures that each eamil is unique
    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    # username cannot be null
    # ensures that each username is unique
    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    # define a image column
    # default image url for users without a custom image
    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    # define a header image column
    # default header image url
    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )

    # define a column for user biography
    bio = db.Column(
        db.Text,
    )

    # define a column for user location
    location = db.Column(
        db.Text,
    )

    # define a password
    # password cannot be null
    password = db.Column(
        db.Text,
        nullable=False,
    )

    # define a private account
    # indicate whether the user account is private or public
    is_private = db.Column(
        db.Boolean,
        default=False
    )

    # Establishes a one-to-many relationship with `Message` Model ("one" side)
    # Can get list of messages objects from user with `.messages`
    # `users` is the referenced table
    # `messages` is the referencing table
    messages = db.relationship('Message')

    ### SELF-REFERENTIAL MANY-TO-MANY RELATIONSHIPS ###

    # Create a relationship between `User` model and itself.
    # The relationship is between users who follow each other.

    # Establishes a many-to-many relationship
    followers = db.relationship(
        "User",
        # "Through" relationship
        secondary="follows",
        # defines the join condition for the followers
        # identify the users who are being followed
        primaryjoin=(Follows.user_being_followed_id == id),
        # defines the join condition for the following users
        # identify which users are following the current user 
        secondaryjoin=(Follows.user_following_id == id)
    )

    # Establishes a many-to-many relationship
    following = db.relationship(
        "User",
        # "Through" relationship
        secondary="follows",
        # find the users doing the following
        primaryjoin=(Follows.user_following_id == id),
        # identify who is being followed
        secondaryjoin=(Follows.user_being_followed_id == id)
    )

    # Establishes a many-to-many relationship with `Message` Model
    # Each user can like many messages, 
    # and each message can be liked by many users
    likes = db.relationship(
        'Message',
        secondary="likes"
    )

    # String representation of the User instance
    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        # List comprehension to find followers
        found_user_list = [user for user in self.followers if user == other_user]
        # Returns True if other_user is found, else Flase
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        # List comprehension to find followed users
        found_user_list = [user for user in self.following if user == other_user]
        # Returns True if other_user is found, else Flase
        return len(found_user_list) == 1
    
    def change_password(self, current_password, new_password):
        """ Handle the password change """
    
        # Check if if the provided current password matches the stored hash
        if not bcrypt.check_password_hash(self.password, current_password):
            # Password change failed
            # The current password provided by the user does not match the one in the database.
            return False

        # Hashes the new password using Bcrypt and update user password
        self.password = bcrypt.generate_password_hash(new_password).decode('UTF-8')

        # Save the user with the new password
        db.session.commit()

        # Password change successful
        return True

    ############### Allow “Private” Accounts methods

    # Helper (TODO: IS THIS UNNECCSSARY)
    # def check_is_private(self):
        # """ Checks whether a user has set their account to private. """

        # Returns `True` if the account is private.
        # `False` if the account is public.
        # return self.is_private

    def can_view_profile(self, viewer):
        """ Checks whether a specific viewer (another user or the currently logged-in user) is allowed to view the profile of the current user. """

        # if the current user profile is public,
        # Viewer can view the profile.
        if not self.is_private:
            return True

        # if the current user profile is private, 

        # If the viewer is the profile owner, allow viewing 
        if viewer == self:
            return True

        # Checks if the `viewer` is following the owner of the profile, and if the follow request has been approved,
        approved_follow = Follows.query.filter_by(is_approved=True, user_being_followed_id = self.id, user_following_id = viewer.id).first()

        # If `approved_follow` object is found(<Follows 144, 303>), return `True`
        # If `approved_follow` is `None`, return `False`
        return approved_follow

    def approve_follow(self, follower):
        """ Used by private account holder to approve a follow request """

        # Finds the follow request in the `follows` table
        follow = Follows.query.filter_by(self.id==user_being_followed_id, follower.id==user_following_id).first()

        # TODO: UPDATE CONDITION
        if follow:
            follow.is_approved = True
            db.session.commit()
        

    ################################################

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        # Hashes the password using Bcrypt
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        # Create a new User instance with the hashed password
        user = User(
            username=username,
            email=email,
            password=hashed_pwd, 
            image_url=image_url,
        )

        # Adds the new user to the database session
        db.session.add(user)
        # Returns the new user instance
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        # Queries the database for the first user with the given username
        user = cls.query.filter_by(username=username).first()

        # Check if the user was found
        if user:
            # Checkes if the provided password matches the stored hash
            is_auth = bcrypt.check_password_hash(user.password, password)
            # If authentication is successful
            if is_auth:
                # Returns the user instance
                return user

        # Retruns False if user is not found or password is incorrect
        return False


class Message(db.Model):
    """An individual message ("warble")."""

    # Specifies table name
    __tablename__ = 'messages'

    # Define a primary column
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Define a column for storing the message text, 
    text = db.Column(
        # limited to 140 characters
        db.String(140),
        # Message cannot be null
        nullable=False,
    )

    # Define a timestamp column
    timestamp = db.Column(
        db.DateTime,
        # Timestamp cannot be bull
        nullable=False,
        # Sets the default to the current UTC time
        default=datetime.utcnow(),
    )

    # Define a user id foreignkey
    # Establish the link between the two tables
    user_id = db.Column(
        db.Integer,
        # References the `id` column in the `users` table,
        # deletes cascade if user is deleted
        db.ForeignKey('users.id', ondelete='CASCADE'),
        # User ID cannot be null
        nullable=False,
    )

    # Establish a one-to-many relationship ("many" side)
    user = db.relationship('User')


# Establishes a connection between a FLASK APPLICATION and a SQLAlchemy DATABASE
def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    # Assign the Flask app instance to the `app` property of the `db` object (an instance of `SQLAlchemy()`)
    # Tell SQLAlchemy which Flask app it should work with
    db.app = app

    # A helper method that initializes the Flask app with SQLAlchemy
    # It configures the app so that the database can be accessed within the app'scontext
    # This ensures that the Flask app is fully integrated with SQLAlchemy and is ready to handle database queries or operations
    db.init_app(app)

# QUESTIONS

-   `models.py`: The `unique=True` constraint in the `likes` table

    -   How each message can only be liked once by preventing duplicate entries in the database?

        -   Can't multiple users like one single message?

        -   When a user attempts to like a message, a new entry is created in the `likes` table linking the user's `user_id` with the `message_id`.
        -   If the same user tries to like the same message again, the attempt to insert a new record with the same `message_id` will violate the unique constraint, leading to a database error
            -   What about a different user tries to like the message that has been already liked?

-   Part Three: Add Tests

    -   Following the instruction, we should set `FLASK_ENV` to `production`, so it does not use debug mode, and therefore won't use the Debug Toolbar during our tests. 

        -   The question is, what is the difference between setting `FLASK_ENV=production` and `app.config['TESTING'] = True`.

# Visualization of Self-Referential Many-to-Many Relationship

In the `Warbler` app, users can follow each other, which creates a **many-to-many relationship**. This is accomplished using a **self-referential relationship**, where the `User` table references itself through an association table (`Follows`).

## Tables Involved

### 1. **User** Table
| id  | username | email               |
| --- | -------- | --------------------|
| 1   | alice    | alice@example.com   |
| 2   | bob      | bob@example.com     |
| 3   | charlie  | charlie@example.com |

The `User` table stores the basic information about users.

### 2. **Follows** Table (Association Table)
| user_being_followed_id | user_following_id |
| ---------------------- | ----------------- |
| 2                      | 1                 |
| 3                      | 1                 |
| 1                      | 2                 |

The `Follows` table acts as a bridge between users. It contains two foreign keys:
- `user_being_followed_id`: The ID of the user being followed.
- `user_following_id`: The ID of the user doing the following.

## Relationships

### 1. **Followers** Relationship (Who follows the current user?)
```py
followers = db.relationship(
    "User",
    secondary="follows",
    primaryjoin=(Follows.user_being_followed_id == id),
    secondaryjoin=(Follows.user_following_id == id)
)
```

### Following Relationship (Who is the current user following?)
```py
following = db.relationship(
    "User",
    secondary="follows",
    primaryjoin=(Follows.user_following_id == id),
    secondaryjoin=(Follows.user_being_followed_id == id)
)

```
### Diagram (followers)

    ┌─────────────┐              ┌─────────────┐
    │  User       │              │  Follows    │
    │─────────────│              │─────────────│
    │ id          │<─────────────┤ user_being  │
    │ username    │ ──primary──► │ followed_id │
    └─────────────┘              |             |
                                 │─────────────│
    ┌─────────────┐              |             |
    │  User       │              │  Follows    │
    │─────────────│ ◄─secondary──┤ user_follow │
    │ id          │ ────────────►│ _ing_id     │
    │ username    │              |             |
    └─────────────┘              └─────────────┘


### How It Works

- **Followers**: For each user, the `primaryjoin` finds entries in the `Follows` table where the user is being followed, and the `secondaryjoin` finds the users who are following them.

- **Following**: The `primaryjoin` finds entries where the user is following someone, and the `secondaryjoin` finds who is being followed.

# Database Schema Diagram

## Tables:
- **users**
- **follows**
- **messages**
- **likes**

### users
| Column Name        | Type      | Constraints         |
|--------------------|-----------|---------------------|
| id                 | Integer   | Primary Key         |
| email              | Text      | Not Null, Unique    |
| username           | Text      | Not Null, Unique    |
| image_url          | Text      | Default             |
| header_image_url   | Text      | Default             |
| bio                | Text      |                     |
| location           | Text      |                     |
| password           | Text      | Not Null            |
| is_private         | Boolean   | Default                             |


### messages
| Column Name   | Type        | Constraints            |
|---------------|-------------|------------------------|
| id            | Integer     | Primary Key            |
| text          | String(140) | Not Null               |
| timestamp     | DateTime    | Not Null, Default Now  |
| user_id       | Integer     | Foreign Key (users.id) |

### follows
| Column Name               | Type       | Constraints                         |
|---------------------------|------------|-------------------------------------|
| is_approved               | Boolean    | Default                             |
| user_being_followed_id    | Integer    | Foreign Key (users.id), Primary Key |
| user_following_id         | Integer    | Foreign Key (users.id), Primary Key |

### likes
| Column Name   | Type      | Constraints                       |
|---------------|-----------|-----------------------------------|
| id            | Integer   | Primary Key                       |
| user_id       | Integer   | Foreign Key (users.id)            |
| message_id    | Integer   | Foreign Key (messages.id), Unique |

## Relationships:

1. **users -> messages**:  
   One-to-Many relationship.  
   Each user can have multiple messages, but each message is linked to only one user (`user_id` in `messages` table).

2. **users -> follows (self-referential many-to-many)**:  
   A many-to-many relationship.  
   Users can follow multiple other users and be followed by multiple users. This is done through the `follows` table which uses two foreign keys (`user_being_followed_id` and `user_following_id`).

3. **users -> likes -> messages**:  
   A many-to-many relationship.  
   A user can like multiple messages, and a message can be liked by multiple users. The `likes` table connects the `users` and `messages` tables via `user_id` and `message_id`.

# Research and Understand Login Strategy

## How is the logged in user being kept track of?

The Flask `g` object is used to keep track of a logged-in user. 

## What is Flask’s `g` object?

Flaks's `g` object is a global namespace object for temporary storing and sharing  data during a single request. The data stored in `g` is only available for the duration of a request and will be cleared after the request ends. 

## What is the purpose of `add_user_to_g` ?

The purpose of it is checking if user is logged in and store the user in the `g` object. 

## What does `@app.before_request` mean?

The `@app.before_request` decorator defines a function that runs before any request is handled. 

# Adding AJAX 

1.  Like/unlike a warble using AJAX

    When a user clicks the "like" or "unlike" button, we will use Axios to send a request to the server
    without reloading the page. We can modify the appearance of the like button dynamically based on the response from the server. 

    1.  Include Axios using a CDN link.
    2.  Backend: Create a route to handle the like/unlike logic in `app.py`
    3.  Frontend: Use Axios to send AJAX requests for liking/unliking 

    **PROBLEM**

    -   The like button is not clickable.

        -   Ensured set up (CDN link, CSS file, JS file etc.)
        -   Ensured HTML structure 
        -   Checked CSS
            -   Now, I suspect the `.message-link` is blocking the button since it has `z-index: 1`. I adjusted a couple of CSS rules but it's not being reflected on the webpage.  

        **1.    `<a>` closing tag**
        **2.    `z-index`**

2.  Popup modal

    the user should be able to create or "compose" a warble (which is a short message, like a tweet) from a modal dialog. This modal will pop up on every page when the user clicks a button in the navigation bar, allowing the user to compose and submit the warble without leaving the page they are currently on. The warble is submitted using AJAX (without page reload), and it appears on the page dynamically.

    -   Note: Modal is a UI component that appears as an overlay on top of the current page. It is commonly used for input forms without navigating to a new page.

    1. Add the modal to HTML

        -   There is an existing `a` element on the `base.html` template.
        -   There is an existing `new.html` (form) template. 

        -   Switched `a` tag to `button` tag
        -   Moved the new message form to `base.html` template
        -   Added `id='warbler-modal'` to modal HTML
        -   Inject new message form into every page beside the homepage, 404 page.
        -   Define the form in `app.py` and pass form to templates in `before_request`
        -   Modify `base.html`, check if the `message_form` is present
        -   Ensure form is excluded from 404 page and homepage

# DRY Up the Templates

Leverage Jinja features: `{% include %}`, `{% macro %}`, `{% import %}`, to DRY (Don't Repeat Yourself) up the templates in Flask application.


# DRY Up the Authorization

create a custom **decorator** to check if a user is logged in. This decorator will centralize the logic for user authorization, avoiding repetitive code in each route.

```py
from functools import wraps
from flask import redirect, url_for, flash, g

# Basic login required decorator.
# `f` is the ORIGINAL FUNCTION we want to protect (like a route function).
def login_required(f):

    # decorator from the `functools` module.
    # wraps the original function `f`
    # ensure the original function's name and documentation are preserved 
    @wraps(f)

    # inner function adds new behavior (checking if the user is logged) 
    # before calling the original function.
    # *args, **kwargs are used to pass an arbitrary number of positional and 
    # keyword arguments to a function.
    def decorated_function(*args, **kwargs):

        if not g.user:  # If no user is logged in
            flash("You need to be logged in to access this page.", "danger")
            return redirect(url_for('login'))  # Redirect to login page

        return f(*args, **kwargs)  # Call the wrapped route function

    # This happens (execute) first because it's the step where the original function is wrapped by `check_login`
    return decorated_function

```

# Optimize Queries

This task is about optimizing database queries in the application.
When applications make more database queries than necessary, it leads to 
performance issues like slow loading times or excessive server load. 

1.   The following query retrieves messages from the users that the current user is     following and the current user's own messages. But, it is likely followed by **additional queries** to retrieve the **user data** for each message, such as user's `username` etc.

    -   Fetches a list of messages in one query.
    -   For each message, it then makes additional queries to get the user details for each `message.user_id`.

```sql
21.8748	

.\app.py:416 (homepage)

SELECT messages.id AS messages_id, 
    messages.text AS messages_text, 
    messages.timestamp AS messages_timestamp, 
    messages.user_id AS messages_user_id 
FROM messages 
JOIN follows ON messages.user_id = follows.user_being_followed_id 
WHERE messages.user_id = %(user_id_1)s OR follows.user_following_id = %(user_following_id_1)s 
ORDER BY messages.timestamp DESC 
LIMIT %(param_1)s

```

**Eager Loading**

Use `joinedload` in SQLAlchemy to eagerly load the related `User` model along with the `Message` in one query. This ensures that the user's details are fetched with the message itself, preventing multiple additional queries, and reduces the loading time from 
21.8748 ms to 6.9327 ms.

```py
from sqlalchemy.orm import joinedload

# Eagerly load the User model when querying the Message
messages = (Message
            .query
            .options(joinedload(Message.user))  # Eagerly load the user
            .join(Follows, Message.user_id == Follows.user_being_followed_id)
            .filter((Message.user_id == g.user.id) | (Follows.user_following_id == g.user.id))
            .order_by(Message.timestamp.desc())
            .limit(100)
            .all())
```


# Make a change password form

1.  Define a Flask WTF form
2.  Add a method in `User` model to handle the password change. 
    -   Check if the current password is correct.
    -   Hash the new password.
    -   Save the new password to the database.
3.  Create a view function to handle password change
4.  Create a new template for the change password form


# Allow “Private” Accounts

1. Changes schema (User model)

    -   User table
        -   add a new column to indicated whether an account is private or public.

    -   Follows table
        -   add a new column to track the approval status for follow requests for private accounts.

2.  Design considerations

    -   Approval for follow requests
        -   When a user requests to follow a private account, an entry is added to the `follows` table with `is_approved=False`.
        -   The account owner(the private user) will need to approve the follow request, after which `is_approved` will be set to `True`.
        -   Only approved followers should be able to see the private user's messags. 

    -   Avoiding sprinkling `if` conditions 

3.  Useful functions on `User` or `Message` classes

    -   `User` class method
    -   `Message` class method

4.  Adjustments to routes

    -   user's profile route
    -   showing messages route

5.  Approval workflow for private accounts

    -   New route to handle approval process
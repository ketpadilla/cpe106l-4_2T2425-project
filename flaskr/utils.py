from flask import Flask, session, redirect
from functools import wraps

def login_required(f):
  """Decorator to ensure that a user is logged in before accessing a route.

  This decorator checks if the 'logged_in' key is present in the session. If the user
  is not logged in, they are redirected to the home page.

  Args:
    f (function): The route function to be wrapped.

  Returns:
    function: The wrapped function that enforces login requirements.
  """
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else: 
      print('Not logged in. Returning to Home Page')
      return redirect('/')

  return wrap

def debug_border():
  """Print a debug border to the console.

  This function prints a line of dashes to visually separate debug messages in the console.
  """
  print("-" * 50)
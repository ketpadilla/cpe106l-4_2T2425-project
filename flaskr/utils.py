from flask import Flask, session, redirect
from functools import wraps

def login_required(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else: 
      print('Not logged in. Returning to Home Page')
      return redirect('/')

  return wrap
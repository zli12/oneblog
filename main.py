import webapp2
import os
import jinja2
import hashlib
import hmac
import string
import random

from google.appengine.ext import db
 
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
	autoescape = True)
SECRET = "helloworld"

def hash_str(key,s):
    return hmac.new(key,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(SECRET,s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_secure_password(pw,salt=""):
	if not salt:
		salt = randomizer()
	return salt +'+'+ hmac.new(salt,pw).hexdigest()

def check_password(pw,secure_pw):
	salt = secure_pw.split('+')[0]
	if secure_pw == make_secure_password(pw,salt):
		return True
	return False


def randomizer():
	seed = ""
	all_letters = string.letters
	letter_count = len(all_letters)
	for i in range(1,6):
		k = random.randint(0,letter_count-1)
		seed = seed + all_letters[k]
	return seed


class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template, **params):
    	t = jinja_env.get_template(template)
    	return t.render(params)

    def render(self, template, **kw):
    	self.write(self.render_str(template, **kw))
       

class Post(db.Model):
	title = db.StringProperty(required = True)
	essay = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_edited = db.DateTimeProperty(auto_now = True)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self):
		self._render_text = self.essay.replace('\n', '<br>')
		return self.render_str("post.html", p = self)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)
	last_login = db.DateTimeProperty(auto_now = True)

	# def user_check(self)


class MainPage(Handler):
	def get(self):
		self.redirect('/blog')

class HomePage(Handler):
	def get(self):
		posts = Post.all().order('-created')

		self.render("home.html",posts=posts)

class NewPost(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		title = self.request.get("title")
		essay = self.request.get("essay")

		if title and essay:
			p = Post(title = title, essay = essay)
			p.put()
			new_url = "/blog/"+ str(p.key().id())
			self.redirect(new_url)
		else:
			error = "we need both a title and some content!"
			self.render("newpost.html",title=title,essay=essay,error=error)

class ViewPost(Handler):
	def get(self,url):
		post_id = int(url)
		key = db.Key.from_path('Post', post_id)
		post = db.get(key)
		if post:
			self.render("permalink.html",post=post)
		else:
			self.error(404)
			
class Signup(Handler):
	def get(self):
		self.render("signup.html")

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		password2 = self.request.get("password2")
		email = self.request.get("email")

		if username:
			q = User.all()
			q.filter("username = ",username)
			if q.get():
				error = "username is taken."
				self.render("signup.html", unerror=error, username=username,email=email)
			elif not password:
				error = "you need a password."
				self.render("signup.html", pwerror=error, username=username,email=email)
			elif password2 != password:
				error = "passwords don't match, please retry."
				self.render("signup.html", pwerror=error, username=username,email=email)
			else:
				user_cookie_val = make_secure_val(str(username))
				secure_password = make_secure_password(password)
				u = User(username = username, password=secure_password, email=email)
				u.put();
				self.response.headers.add_header('Set-Cookie',"username=" + user_cookie_val)
				self.redirect("/blog/welcome")
		else:
			error = "you need a username."
			self.render("signup.html", unerror=error, username=username,email=email)

class SignupConfirmation(Handler):
	def get(self):
		user_cookie_val = self.request.cookies.get("username")
		if user_cookie_val:
			username = check_secure_val(user_cookie_val)
			if username:
				self.render("welcome.html", username = username)
				return

		self.redirect("/blog/signup")

class Login(Handler):
	def get(self):
		self.render("login.html")

	def post(self):		
		username = self.request.get("username")
		password = self.request.get("password")

		if not username:
			error = "username required."
			self.render("login.html", username=username, unerror=error)
			return
		elif not password:
			error = "password required."
		else:
			q = User.all()
			q.filter("username =", username)
			user = q.get()

			if user:
				password_val = user.password
				if check_password(str(password),str(password_val)):
					secure_username = make_secure_val(str(username))
					self.response.headers.add_header("Set-Cookie", "username="+secure_username)
					self.redirect("/blog/welcome")
					return
				else:
					error = "Login information incorrect, please retry."
			else:
				error = "Login information incorrect, please retry."
			
		self.render("login.html", username=username, pwerror=error)

class Logout(Handler):
	def get(self):
		self.response.headers.add_header("Set-Cookie", "username= ; Expires=Thu, 01-Jan-1970 00:00:00 GMT")
		self.redirect("/blog/signup")
    	
app = webapp2.WSGIApplication([(r'/', MainPage),
	(r'/blog', HomePage),
	(r'/blog/newpost', NewPost),
	(r'/blog/(\d+)',ViewPost),
	(r'/blog/signup',Signup),
	(r'/blog/welcome',SignupConfirmation),
	(r'/blog/login',Login),
	(r'/blog/logout',Logout)],
	debug=True)
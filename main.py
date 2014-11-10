import webapp2
import os
import jinja2

from google.appengine.ext import db
 
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
	autoescape = True)

def blog_key(name = 'default'):
	return db.Key.from_path('blogs', name)

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
			p = Post(parent=blog_key(),title = title, essay = essay)
			p.put()
			new_url = "/blog/"+ str(p.key().id())
			self.redirect(new_url)
		else:
			error = "we need both a title and some content!"
			self.render("newpost.html",title=title,essay=essay,error=error)

class ViewPost(Handler):
	def get(self,url):
		post_id = int(url)
		key = db.Key.from_path('Post', post_id, parent=blog_key())
		post = db.get(key)
		if post:
			self.render("permalink.html",post=post)
		else:
			self.error(404)
			

    	
app = webapp2.WSGIApplication([(r'/', MainPage),
	(r'/blog', HomePage),
	(r'/blog/newpost', NewPost),
	(r'/blog/(\d+)',ViewPost)],
	debug=True)
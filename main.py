import webapp2
import os
import jinja2

from google.appengine.ext import db
 
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
	autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template, **params):
    	t = jinja_env.get_template(template)
    	return t.render(params)

    def render(self, template, **kw):
    	self.write(self.render_str(template, **kw))
       
class Post(db.Model):
	post_id = db.IntegerProperty(required = True)
	title = db.StringProperty(required = True)
	essay = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_edited = db.DateTimeProperty(auto_now = True)
	#created_by = db.StringProperty()

	def render(self):
		self._render_text = self.content.replace('\n'. '<br>')
		return render_str("post.html", p = self)

class MainPage(Handler):
	def get(self):
		self.redirect('/blog')

class HomePage(Handler):
	def render_front(self):
		posts = Post.all().order('-created')

		self.render("home.html",posts=posts)

	def get(self):
		self.render_front()

class NewPost(Handler):
	def render_front(self, title="", essay="", error=""):
		posts = db.GqlQuery("select * from Post order by created desc")

		self.render("newpost.html",title=title,essay=essay,error=error,posts=posts)

	def get(self):
		self.render_front()

	def post(self):
		title = self.request.get("title")
		essay = self.request.get("essay")
		debug_msg = "start"
		if title and essay:
			count = Post.all().count()
			a = Post(title = title, post_id=count+1, essay = essay)
			a.put()

			count += 1
			debug_msg += "count is: " + str(count)

			posts = db.GqlQuery("select * from Post order by created desc")

			post_entity_id = 0
			for post in posts:
				debug_msg += "post_id: " + str(post.post_id)
				if post.post_id == count:
					debug_msg += " FOUND EQUAL "
					post_entity_id = post.id()

			self.write(debug_msg)

			if post_entity_id > 0:
				new_url = "/blog/"+ str(post_entity_id)
				self.redirect(new_url)
		else:
			error = "we need both a title and some content!"
			self.render_front(title,essay,error)

class ViewPost(Handler):
	def get(self,url):
		post_id = int(url)
		if post_id:
			requested_post = Post.get_by_id(post_id)
			self.render("post.html",post=requested_post)
		else:
			self.write("Post Not Found!")
			

    	
app = webapp2.WSGIApplication([(r'/', MainPage),
	(r'/blog', HomePage),
	(r'/blog/newpost', NewPost),
	(r'/blog/(\d+)',ViewPost)],
	debug=True)
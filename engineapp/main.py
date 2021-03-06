#!/usr/bin/env python
# This is main file, which will render html pages. Template used: Jinja2

import webapp2
import cgi
import jinja2
import os
import logging
import re
from google.appengine.ext import db
import hashlib
import hmac
from string import letters
import random
from google.appengine.ext.db import metadata

from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import app_identity
from urllib import urlencode

import httplib2
from collections import defaultdict
import json


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
secret = 'Navjot'



class VehicleLocation(ndb.Model):
    lat=ndb.StringProperty()
    long=ndb.StringProperty()
    name=ndb.StringProperty()


class UserCode(ndb.Model):
    """User-Code profile"""
    code=ndb.IntegerProperty()
    email =ndb.StringProperty(required=True)


    @classmethod
    def user_code(cls, user):
        """Checks and adds code to user email"""
        code = UserCode.query(UserCode.email == user).get()

        if not code:
            return "Email Id Does Not exist, Code can not be generated"
        else:
            codeNumber=random.randrange(100000, 99999999)
            code.code=codeNumber
            code.put()
            return codeNumber
    @classmethod
    def by_name(cls, name,code):
        u = UserCode.query(UserCode.email==name, UserCode.code==code).get()
        logging.info("*******************************")
        logging.info(code)
        logging.info(u)
        return u


class COMMENT(db.Model):
    """ This class makes four entries to the data store.
    comment_id will correspond to the blog id where comment is being made.
    comment_list will contain list of all users who are not authorize to
    comment the blog. This includes owner of blog and users who commented blog
    already.
    """
    comment_id = db.IntegerProperty(required=True)
    comment_list = db.StringListProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    owner = db.StringProperty(required=False)


class PER_COMMENT(db.Model):
    """In this class, per_comment_id will contain id of each individual comment.
    owner_comment corresponds to owner of comment and comment corresponds to
    comment whihc is made by user
    """
    per_comment_id = db.IntegerProperty()
    owner_comment = db.StringProperty()
    comment = db.TextProperty()


class Blog(db.Model):
    subject = db.TextProperty(required=True)
    blog = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    owner = db.StringProperty(required=False)


class LIKE(db.Model):
    """In this class c_post_id contains the id of the post/blog.
    Every blog has a like button.
    c_likes contains number of likes each blog.
    like_list contains users who likes the blog and therefore not
    authorize to like again.
    """
    c_post_id = db.IntegerProperty(required=True)
    c_likes = db.IntegerProperty()
    like_list = db.StringListProperty()


class User(db.Model):
    user_name = db.StringProperty(required=True)
    user_pw_hash = db.StringProperty(required=True)
    user_email = db.StringProperty(required=True)

    # returns object to that id
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent=users_key())

    # returns object to name.
    @classmethod
    def by_name(cls, name):
        u = User.all().filter('user_name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email):
        pw_hash = make_pw_hash(name, pw)
        return User(parent=users_key(),
                    user_name=name,
                    user_pw_hash=pw_hash,
                    user_email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.user_pw_hash):
            return u


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)



def make_secure_val(val):
    # make_secure_val return a encrypted hmac value.
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    # this check whether the value received from browser matched the one
    # in the database.
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class MainHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Setting cookies which will be used to differentiate a valid user.
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # cookie 'user-id' being set for user will be key id.
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    # logout will simply remove the user_id cookie
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    # For every request, initialize function will get call and then populate
    # uid and user
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        self.uid = self.read_secure_cookie('user_id')
        self.user = self.uid and User.by_id(int(self.uid))


def users_key(group='default'):
    return db.Key.from_path('User', group)


class GenerateCode(MainHandler):
    def send_data(self, file, code="", items=""):
        self.render(file, code=code,items=items)

    def get(self):
        self.send_data("sign-up.html")

    def post(self):
        user_email=self.request.get("userEmail")
        data=UserCode.user_code(user_email)
        self.send_data("sign-up.html",code=data)




class Register(MainHandler):
    """ class Register generates the sign-up page and then act on post
     of sign-up page form.
     IF data valid, sets the cookie for that user."""

    def send_data(self, file, items=""):
        self.render(file, items=items)

    def get(self):
        if self.user:
            self.redirect('/blog')
        else:
            self.send_data("sign-up.html")

    def post(self):
        if self.user:
            self.redirect('/blog')
        else:

            user_name = self.request.get("email")
            user_pass = self.request.get("password")
            user_pass_re = self.request.get("passwordRe")

            user_code=self.request.get("code")

            check_name = EMAIL_RE.match(user_name)
            check_pass = PASS_RE.match(user_pass)

            try:
                user_code=int(user_code)
                check_code="1"
            except:
                check_code="Code needs to be a number"
            user_error = ""
            pass_error = ""
            code_error=""
            pass_re_error = ""
            check_re_pass = "Ok"
            page_rendered = False

            if (user_pass != user_pass_re):
                pass_re_error = "Password does not match"
                check_re_pass = None
            if (check_pass and check_name and check_re_pass and len(check_code)<3):
                codeCheck=UserCode.by_name(user_name,user_code)
                if codeCheck is None:
                    code_error = 'Code Does Not match'
                    self.send_data("sign-up.html",
                                   items={"email": user_name,
                                          "EmailError": user_error,
                                          "PassError": pass_error,
                                          "codeError": code_error,
                                          })
                    page_rendered = True


                u = User.by_name(user_name)
                if u is not None and not page_rendered:
                    msg = 'That user already REGISTERED.'
                    self.send_data("sign-up.html",
                                   items={
                                          "email": user_name,
                                          "EmailError": msg,
                                          "PassError": pass_error,
                                       "codeError": code_error})
                    page_rendered = True

                if (u is None) and (codeCheck is not None):
                    u = User.register(user_name, user_pass, user_name)
                    u.put()
                    self.login(u)
                    self.redirect('/')
            if not check_name:
                user_error = "User Email not correct"
            if not check_pass:
                pass_error = "Password not correct"
            if len(check_code) > 3:
                code_error="Code needs to be a number"

            if not page_rendered:
                self.send_data("sign-up.html",
                               items={
                                      "email": user_name,
                                      "EmailError": user_error,
                                      "PassError": pass_error,
                                       "codeError":code_error,
                                      "PassReError": pass_re_error,
                                      })


class ThanksHandler(webapp2.RequestHandler):

    def get(self):
        if self.user:
            user_name = self.request.get('userName')
            self.response.out.write("Welcome " + user_name)
        else:
            self.redirect('/blog')


class Login(MainHandler):

    def get(self):
        if self.user:
            #logging.info("Inside GET ---------------------")
            self.logout()
            self.redirect('/')
        else:
            self.redirect('/')

    def post(self):
        logging.info("Inside POST LOGIN---------------------")
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        u = User.login(self.username, self.password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('webPage.html', error=msg)



class Logout(MainHandler):

    def get(self):
        if self.user:
            self.logout()
            self.render('logout.html')
        else:
            self.redirect('/blog/login')

# password encryption


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt=salt)


class BlogPage(MainHandler):

    def render_front(self, subject="", blog='', error=''):
        self.render('newblog.html', subject=subject, blog=blog, error=error)

    def get(self):
        if self.user:
            self.render_front()
        else:
            self.redirect('/blog/login')

    def post(self):
        if self.user:
            user_subject = self.request.get("subject")
            user_blog = self.request.get("blog")
            if user_blog and user_subject:
                a = Blog(
                    subject=user_subject, blog=user_blog,
                    owner=self.user.user_name)
                a_key = a.put()
                list_appended = []
                list_appended.append(self.user.user_name)
                b = LIKE(
                    c_post_id=a_key.id(), c_likes=0,
                    like_list=[self.user.user_name])
                b.put()
                c = COMMENT(comment_id=a_key.id(), comment_list=[],
                            owner=self.user.user_name)
                c.put()
                c.put()
                self.redirect('/blog/%d' % a_key.id())
            else:
                error = "Pl input both fields."
                self.render_front(
                    subject=user_subject, blog=user_blog, error=error)
        else:
            self.redirect('/blog/login')


class Permalink(MainHandler):

    def get(self, blog_id):
        if self.user:
            s = Blog.get_by_id(int(blog_id))
            likes = db.GqlQuery("select * from LIKE")
            self.render('blog.html', blogs=[s], like=likes, newblog='True')
        else:
            self.redirect('/blog/login')


def delete_database():
    for blog in blogs_all:
        try:
            while True:
                q = db.GqlQuery("SELECT __key__ FROM LIKE")
                db.delete(q.fetch(200))
        except Exception, e:
            self.response.out.write(repr(e) + '\n')
    for blog in blogs:
        blog.delete()


class MainWebPage(MainHandler):
    def render_front(self):
        self.render('webPage.html', error=" ", user=self.user)

    def get(self):
        self.render_front()



class MainBlogPage(MainHandler):
    # This function create ojects for all the entries in data base
    # and then renders the blog.html

    def render_front(self, like_error="",
                     comment_error="",
                     like_error_id="",
                     comment_error_id="", current_user="", delete_error="",
                     delete_error_id="", comment_delete_error="",
                     comment_delete_id="",
                     comment_edit_error="", comment_edit_id=""):
        blogs_all = db.GqlQuery("select * from Blog order by created desc ")
        likes = db.GqlQuery("select * from LIKE")
        comments = db.GqlQuery("select * from COMMENT")
        per_comments = db.GqlQuery("select * from PER_COMMENT")
        blogs = blogs_all.fetch(limit=10)






        uid = self.read_secure_cookie('user_id')
        user = User.by_id(int(self.uid))
        user_logged = user.user_name
        self.render('blog.html', blogs=blogs, like=likes,
                    comments=comments, like_error=like_error,
                    like_error_id=like_error_id,
                    comment_error=comment_error,
                    comment_error_id=comment_error_id,
                    delete_error=delete_error,
                    delete_error_id=delete_error_id,
                    current_user=current_user,
                    each_comment=per_comments,
                    comment_delete_error=comment_delete_error,
                    comment_delete_id=comment_delete_id,
                    comment_edit_error=comment_edit_error,
                    comment_edit_id=comment_edit_id,
                    user_logged=user_logged)


    def get(self):
            self.render_front()




class OpenBlog(MainHandler):


    def render_front(self, post_id, like_error="",
                     comment_error="",
                     like_error_id="",
                     comment_error_id="", current_user="", delete_error="",
                     delete_error_id="", comment_delete_error="",
                     comment_delete_id="",
                     comment_edit_error="", comment_edit_id=""):

        s = Blog.get_by_id(int(post_id))

        likes = db.GqlQuery("select * from LIKE")
        comments = db.GqlQuery("select * from COMMENT")
        per_comments = db.GqlQuery("select * from PER_COMMENT")

        user_logged=self.user

        self.render('getBlog.html', blog=s, like=likes,
                    comments=comments, like_error=like_error,
                    like_error_id=like_error_id,
                    comment_error=comment_error,
                    comment_error_id=comment_error_id,
                    delete_error=delete_error,
                    delete_error_id=delete_error_id,
                    current_user=current_user,
                    each_comment=per_comments,
                    comment_delete_error=comment_delete_error,
                    comment_delete_id=comment_delete_id,
                    comment_edit_error=comment_edit_error,
                    comment_edit_id=comment_edit_id,
                    user_logged=user_logged)


    def get(self):
        logging.info("***********Inside GET of OpenBlog")
        if self.user:
            post_id = self.request.get("post_id")

            self.render_front(post_id)

        else:
            self.redirect('/blog/login')


    def post(self):
        logging.info("***********Inside POST of OpenBlog")

        if self.user:
            post_id = self.request.get("post_id")
            comment_post_id=self.request.get("comment_post_id")

            comment_clicked = False
            if comment_post_id:

                logging.info("--------------------Inside Post_id %s"%(comment_post_id))
                comment_clicked = True
                s = Blog.get_by_id(int(comment_post_id))
    # check wether author of blog is current user, if so dnt let him comment
                if self.user.user_name == s.owner:
                    comment_error_id = int(comment_post_id)

                    comment_error = """"
                    Owner of Blog not authorize to comment on his/her blog"""

                    self.render_front(post_id=comment_post_id,
                        comment_error=comment_error,
                        comment_error_id=comment_error_id,
                        current_user=self.user.user_name)
                else:
                    self.redirect('/blog/addcomment?post_id=' + comment_post_id)

            like_button_id = self.request.get("like_button_id")
            like_error_id = ""
            like_error = ""
            if like_button_id:
                logging.info("--------------------Inside Like_id")
                s = LIKE.get_by_id(int(like_button_id))

                # check wether author of blog/prviously likes the page is
                # current user, if so dnt let him like
                if (self.user.user_name) in s.like_list:
                    logging.info("Item found")
                    like_error = """
                    Error: Author not authorize to like own Blog.
                      Or You likes the blog already"""
                    like_error_id = int(like_button_id)
                    self.render_front(post_id=post_id,
                        like_error=like_error, like_error_id=like_error_id,
                        current_user=self.user.user_name)
                else:
                    updated_list = s.like_list
                    updated_list.append(self.user.user_name)
                    s.like_list = updated_list
                    s.c_likes = s.c_likes + 1
                    s.put()
                    s.put()
                    self.redirect('/blog')

            delete_post_id = self.request.get("delete_post_id")
            if delete_post_id:
                logging.info("--------------------Inside delete_id")
                s = Blog.get_by_id(int(delete_post_id))
                if s and self.user.user_name == s.owner:
                    s.delete()
                    s.delete()
                    self.redirect('/blog')
                else:
                    delete_error_id = int(delete_post_id)
                    del_error = "Only Owner is authorize to delete a blog"
                    self.render_front(delete_error=del_error, post_id=delete_post_id,
                                      delete_error_id=delete_error_id)

            each_comment_id_for_edit = self.request.get(
                "each_comment_id_for_edit")
            each_comment_id_for_delete = self.request.get(
                "each_comment_id_for_delete")
            if each_comment_id_for_edit:
                logging.info("--------------------Inside each comment edit_id")
                comment_obj = PER_COMMENT.get_by_id(
                    int(each_comment_id_for_edit))
                logging.info("EDIT REQUEST")
                if comment_obj.owner_comment == self.user.user_name:
                    self.redirect(
                        '/blog/editComment?comment_id=' +
                        each_comment_id_for_edit+'&blog_id='+post_id)
                else:
                    comment_delete_error = \
                        "Only author of blog can EDIT the comment"
                    self.render_front(comment_edit_error=comment_delete_error,post_id=post_id,
                        comment_edit_id=int(each_comment_id_for_edit))
            if each_comment_id_for_delete:
                logging.info("--------------------Inside each comment delet_id")
                comment_obj = PER_COMMENT.get_by_id(
                    int(each_comment_id_for_delete))
                if comment_obj.owner_comment == self.user.user_name:
                    comment_obj.delete()
                    comment_obj.delete()




                    comment_delete_error = ""
                else:
                    comment_delete_error =\
                        "Only author of blog can delete the comment"
                self.render_front(comment_delete_error=comment_delete_error,post_id=post_id,
                        comment_delete_id=int(each_comment_id_for_delete))

        else:
            self.redirect('/blog/login')



class EditBlog(MainHandler):

    def render_front(self, post_id):
        s = Blog.get_by_id(int(post_id))
        self.render('edit-blog.html', s=s)

    def get(self):
        if self.user:
            post_id = self.request.get("post_id")
            post = Blog.get_by_id(int(post_id))
            if(self.user.user_name == post.owner):
                self.render_front(post_id)
            else:
                self.redirect("/blog")
        else:
            self.redirect('/blog/login')

    def post(self):
        if self.user:
            logging.info("***********INSIDE EditBlog POST")

            post_id = self.request.get("post_id")

            post = Blog.get_by_id(int(post_id))
            if (self.user.user_name == post.owner):
                self.render_front(post_id)
            else:

                s = Blog.get_by_id(int(post_id))

                likes = db.GqlQuery("select * from LIKE")
                comments = db.GqlQuery("select * from COMMENT")
                per_comments = db.GqlQuery("select * from PER_COMMENT")

                user_logged = self.user

                self.render('getBlog.html', blog=s, like=likes,
                            comments=comments,

                            each_comment=per_comments,
                            user_logged=user_logged)

                #self.redirect('/blog')

            #self.redirect('/blog/edit?post_id='+post_id)
        else:
            self.redirect('/blog/login')


class PostEdition(MainHandler):

    def post(self):
        if self.user:
            blog_id = self.request.get("blog_id")
            user_blog = self.request.get("blog")
            if user_blog:
                post = Blog.get_by_id(int(blog_id))
                post.blog = user_blog
                post.put()
                post.put()
                self.redirect('/blog')
            else:
                error = "Pl input field."
                post = Blog.get_by_id(int(blog_id))
                self.render('edit-blog.html', s=post, error=error)
        else:
            self.redirect("/blog")


class AddingComment(MainHandler):

    def post(self):
        if self.user:
            blog_id = self.request.get("blog_id")
            comment = self.request.get("comment")
            if comment:
                comment_obj = COMMENT.get_by_id(int(blog_id))
                if comment_obj and blog_id in comment_obj.comment_list:
                    list_of_comment = comment_obj.comment_list
                    list_of_comment.append(comment)
                    comment_obj.put()

                else:
                    a = COMMENT(
                        comment_id=int(blog_id), comment_list=[comment])
                    a.put()
                    each_comment = PER_COMMENT(per_comment_id=int(blog_id),
                                          owner_comment=self.user.user_name,
                                               comment=comment)
                    each_comment.put()
                    each_comment.put()

                    s = Blog.get_by_id(int(blog_id))

                    likes = db.GqlQuery("select * from LIKE")
                    comments = db.GqlQuery("select * from COMMENT")
                    per_comments = db.GqlQuery("select * from PER_COMMENT")

                    user_logged = self.user

                    self.render('getBlog.html', blog=s, like=likes,
                                comments=comments,

                                each_comment=per_comments,
                                user_logged=user_logged)




            else:
                self.redirect('/blog/addcomment?post_id=' + blog_id)
        else:
            self.redirect('/blog/login')


class AddComment(MainHandler):

    def render_front(self, post_id):
        s = Blog.get_by_id(int(post_id))
        self.render('adding-comment.html', s=s)

    def get(self):
        if self.user:
            blog_id = self.request.get("post_id")
            if blog_id:
                self.render_front(blog_id)
        else:
            self.redirect('/blog/login')




class EditComment(MainBlogPage):

    def get(self):
        if self.user:
            blog_id=self.request.get("blog_id")
            comment_id = self.request.get("comment_id")
            comment_obj = PER_COMMENT.get_by_id(int(comment_id))
            if comment_obj:
                self.render('edit-comment.html',
                            comment_obj=comment_obj, blog_id=blog_id)
            else:
                self.redirect('/blog')
        else:
            self.redirect('/blog/login')

    def post(self):
        if self.user:
            blog_id = self.request.get("post_id")
            comment = self.request.get("comment")
            comment_id = self.request.get("comment_id")
            comment_obj = PER_COMMENT.get_by_id(int(comment_id))
            if comment_obj:
                comment_obj.comment = comment
                comment_obj.put()
                comment_obj.put()

                s = Blog.get_by_id(int(blog_id))

                likes = db.GqlQuery("select * from LIKE")
                comments = db.GqlQuery("select * from COMMENT")
                per_comments = db.GqlQuery("select * from PER_COMMENT")

                user_logged = self.user

                self.render('getBlog.html', blog=s, like=likes,
                            comments=comments,

                            each_comment=per_comments,
                            user_logged=user_logged)

        else:
            self.redirect('/blog/login')

class ContactForm(MainHandler):
    def get(self):
        self.redirect('/')
    def post(self):
        email=self.request.get("email")



class GetGps(MainHandler):
    def post(self):
        logging.info("----------------------GPS post")
        if self.request.headers['authorization'] == '112233':
            data_x=self.request.get("x")
            data_y = self.request.get("y")
            vehicle=self.request.get("vehicle")
            find_vehicle=VehicleLocation.query(VehicleLocation.name==vehicle).get()
            if find_vehicle:
                find_vehicle.lat=data_x
                find_vehicle.long=data_y
                find_vehicle.put()
            else:
                obj=VehicleLocation(lat=data_x,long=data_y,name=vehicle)
                obj.put()
            logging.info(data_x+" AND "+data_y)
            self.request.response.write("Thanks")
        else:
            logging.info("Failed AUth")
    def get(self):
        logging.info("----------------------GPS get")



class SendMailHandler(webapp2.RequestHandler):
    def get(self):
        email=self.request.get("email")
        phone=self.request.get("phone")
        comment=self.request.get("comment")
        MAILGUN_API_KEY = 'key-794f608b617e7d0d6110ab9e001c351c'

        http = httplib2.Http()
        http.add_credentials('api', MAILGUN_API_KEY)

        url = 'https://api.mailgun.net/v3/sandbox79a3cc42a8ef4bbbb472227da1f6772b.mailgun.org/messages'
        data = {
            'from': 'Mailgun Sandbox <postmaster@sandbox79a3cc42a8ef4bbbb472227da1f6772b.mailgun.org>',
            'to': 'navjot.chakal@yahoo.com',
            'subject':' Got MESSAGE from Drive Pro',
            'text': '''
            Received Query From '''+email+'''
            Contact Number : '''+phone+
            '''
            And the message is
            '''+comment
        }

        resp, content = http.request(
            url, 'POST', urlencode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"})

        if resp.status != 200:
            raise RuntimeError(
                'Mailgun API error: {} {}'.format(resp.status, content))

        self.redirect('/')


class ShowMaps(MainHandler):

    def get(self):
        all_vehicles=VehicleLocation.query().fetch()
        #logging.info(all_vehicles)

        data={}


        l=[]
        json_data=""
        for i in all_vehicles:

            data['title']=i.name
            data['location']={'lat':float(i.lat),'lng':float(i.long)}
            #data['long']=i.long
            json_data=json_data+json.dumps(data)+"&"

        logging.info(json_data)
        self.render('maps.html',items=json_data)


app = webapp2.WSGIApplication([('/blog/newpost', BlogPage),
                               ('/generateCode',GenerateCode),
                               ('/blog/(\d+)', Permalink),
                               ('/blog', MainBlogPage),
                               ('/', MainWebPage),
                               ('/blog/getBlog',OpenBlog),
                               ('/blog/register', Register),
                               ('/blog/welcome', ThanksHandler),
                               ('/blog/login', Login),
                               ('/login', Login),
                               ('/blog/logout', Logout),
                               ('/blog/edit', EditBlog),
                               ('/blog/postEdition', PostEdition),
                               ('/blog/addcomment', AddComment),
                               ('/blog/comment', AddingComment),
                               ('/blog/editComment', EditComment),
                               ('/contactForm',SendMailHandler),
                               ('/getGPS',GetGps),
                               ('/navigation',ShowMaps)
                               ], debug=True)

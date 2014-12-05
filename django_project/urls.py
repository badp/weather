from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
  url(r'^admin/', include(admin.site.urls)),
  url(r"^$", "weather.views.home_page", name="home"),
  url(r"^about$", "weather.views.about", name="about"),
  url(r"^thanks$", "weather.views.thanks", name="thanks"),
  url(r"^votes/vote$", "weather.views.vote_add", name="add a vote"),
  url(r'^login$', "django.contrib.auth.views.login",
      {'template_name': 'login.html'}, name="login"),
  url(r'^logout$', "django.contrib.auth.views.logout",
      {'template_name': 'logout.html'}, name="logout"),
)

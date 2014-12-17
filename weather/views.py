# -*- coding: utf-8 -*-

import models
import random
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

import logging

HINTS = [
  u"Choose with <kbd>←</kbd>/<kbd>→</kbd> then confirm with <kbd>Enter</kbd>.",
  u"Choose with <kbd>Alt</kbd>-<kbd>1</kbd> through"
  u" <kbd>Alt</kbd>-<kbd>5</kbd> then confirm with <kbd>Enter</kbd>.",
  u"Don't overthink it. What is your overall mood?",
  u"While you need to be logged in to vote, voter information is actually"
  u" never saved to the database.",
  u"If there is more on your chest than these answers can say,"
  u"  your manager might be able to help.",
  u"Votes are compared against your manager's perception thereof."
  u" There are no badges or points to be won."
  u"If you would rather not vote for a day, just refresh the page and hit"
  u" Enter."
]


@login_required
def home_page(request):

  return render(
    request, "home.html",
    {"feedback": "What is your mood like?",
     "choices": models.VOTE_CHOICES,
     "hint": random.choice(HINTS)}
  )


def about(request):
  return render(request, "about.html")


def thanks(request):
  return render(request, "thanks.html")


@login_required
def vote_add(request):
  if request.method != "POST":
    return HttpResponseBadRequest()

  if not models.Team.objects.count():
    models.init()

  choice = request.POST.get("choice", None)
  models.UserProfile.of(request.user).vote(choice)

  return HttpResponseRedirect("/thanks")

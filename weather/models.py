from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from collections import OrderedDict
from datetime import date, timedelta
import signals


class UserProfile(models.Model):
  user = models.OneToOneField(User, primary_key=True)
  # Optional new fields go here, but for now I don't need any.
  # Mostly a soft deletion bit.

  @classmethod
  def of(cls, user):
    return cls.objects.get(user=user)

  def vote(self, vote):
    TodayVotes(user=self, vote=vote).save()

  def __unicode__(self):
    return self.user.username


# Ensure that we have a UserProfile for all users
def create_user_profile(sender, instance, created, **kwargs):
  if created:
      UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)


class Team(models.Model):
  HIERARCHICAL = 0
  CIRCULAR = 1
  SHAPE_CHOICES = [
    (HIERARCHICAL, "Hierarchical"),
    (CIRCULAR,     "Circular"),
  ]

  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=25, unique=True)
  members = models.ManyToManyField(UserProfile)
  shape = models.IntegerField(
    choices=SHAPE_CHOICES,
    default=HIERARCHICAL,
    help_text="If a group is hierarchical, members report to one manager.\n"
              "If a group is circular, members report to each other.",
  )
  manager = models.ForeignKey(User, on_delete=models.PROTECT,
                              related_name="owned_by")
  supervisor = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name="supervised_by")

  def get_votes(self, for_past_days=5):
    cutoff_point = date.today() - timedelta(days=for_past_days)
    return Votes.objects.filter(team=self,
                                is_vote=True,
                                date__gte=cutoff_point)

  def get_vote_averages(self, for_past_days=5):
    # this returns a list of dicts with keys "date" and "vote__avg"
    data = (self.get_votes(for_past_days=for_past_days)
            .values('date')
            .annotate(models.Avg('vote')))
    # turn that into a simpler dict from date to average
    response = OrderedDict()
    for point in data:
      response[point["date"]] = point["vote__avg"]
    return response

  def get_predictions(self, for_past_days=5):
    cutoff_point = date.today() - timedelta(days=for_past_days)
    return Votes.objects.filter(team=self,
                                is_prediction=True,
                                date__gte=cutoff_point)

  def get_all_voters(self):
    return UserProfile.objects.filter(team=self)

  def get_all_predictors(self):
    if self.shape == self.HIERARCHICAL:
      return [self.manager]
    else:
      return self.get_all_voters()

  def check_for_warnings(self, send_signals=False):

    def is_prediction_successful(pred, avg):
      if self.shape == self.HIERARCHICAL:
        ranges = [(1, 3), (1, 3), (0, 0), (3, 5), (3, 5)]
      else:
        ranges = [(1, 2.2), (2.2, 2.8), (2.8, 3.2), (3.2, 3.8), (3.8, 5)]
      low, hi = ranges[pred-1]
      return low <= avg <= hi

    def is_concerning(self, failures, num_predictions, pvalue_threshold=0.1):
      base_prob = 0.5 if self.shape == self.HIERARCHICAL else 0.4
      successes = num_predictions - failures
      test_pvalue = choose(num_predictions, successes)
      test_pvalue *= base_prob ** successes
      test_pvalue *= (1-base_prob) ** failures

      # TODO: adjust pvalue threshold to num_predictions?
      return (test_pvalue <= pvalue_threshold, test_pvalue)

    avgs = self.get_vote_averages()
    predictions = self.get_predictions()

    num_predictions = predictions.count()
    failures = 0

    for day in avgs:
      avg = avgs[day]
      day_predictions = predictions.filter(date=day)
      for pred in day_predictions:
        if not is_prediction_successful(pred.vote, avg):
          failures += 1

    threshold_hit = is_concerning(self, failures, num_predictions)

    if send_signals and threshold_hit:
      # TODO: add a ton more information here
      signals.problem_detected.send(sender=self.__class__, team=self)

    return threshold_hit

  def __unicode__(self):
    return self.name


VOTE_CHOICES = [
  (1, ":C"),
  (2, ":/"),
  (3, ":|"),
  (4, ":)"),
  (5, ":D"),
]


# class Membership(models.Model):
#   id = models.AutoField(primary_key=True, editable=False)
#   team = models.ForeignKey(Team)
#   member = models.ForeignKey(UserProfile)

#   def __unicode__(self):
#     return "%s/%s" % (self.team, self.member)


class TodayVotes(models.Model):
  user = models.ForeignKey(UserProfile, primary_key=True)
  vote = models.IntegerField(choices=VOTE_CHOICES, blank=True)

  @classmethod
  # This accepts kwargs because it is a signal handler
  def do_switchover(cls, **kwargs):
    for team in Team.objects.all():
      voters = team.get_all_voters()
      predictors = team.get_all_predictors()
      votes = TodayVotes.objects.filter(user__in=voters)
      predictions = TodayVotes.objects.filter(user__in=predictors)
      if votes.count() < 3:
        print "Skipping %s, not enough votes" % team
        continue
      else:
        for vote in votes:
          Votes(team=team, vote=vote.vote, is_vote=True).save()
        for prediction in predictions:
          Votes(team=team, vote=vote.vote, is_prediction=True).save()

      # Send warnings
      team.check_for_warnings(send_signals=True)

    TodayVotes.objects.all().delete()

  def __unicode__(self):
    return "%d" % self.vote


signals.day_switchover.connect(TodayVotes.do_switchover)


class Votes(models.Model):

  id = models.AutoField(primary_key=True, editable=False)
  # Is it okay to cascade delete votes?
  # It's probably best not to delete users or teams to begin with.
  # If we HAVE to delete things, then we might as well delete it all.

  team = models.ForeignKey(Team, editable=False)
  is_vote = models.BooleanField(default=False)
  is_prediction = models.BooleanField(default=False)
  vote = models.IntegerField(choices=VOTE_CHOICES, editable=False)
  date = models.DateField(auto_now_add=True, editable=False)

  class Meta:
    ordering = ["team", "date"]
    get_latest_by = "date"

  def __unicode__(self):
    return ("{s.team}@{s.date}:{s.vote}"
            " ({s.is_vote}, {s.is_prediction})".format(s=self))


# from http://stackoverflow.com/a/3025547/13992
# by http://stackoverflow.com/users/4279/j-f-sebastian
def choose(n, k):
  """
  A fast way to calculate binomial coefficients by Andrew Dalke (contrib).
  """
  if 0 <= k <= n:
    ntok = 1
    ktok = 1
    for t in xrange(1, min(k, n - k) + 1):
      ntok *= n
      ktok *= t
      n -= 1
    return ntok // ktok
  else:
    return 0


# This is called on syncdb
def init(sender, **kwargs):
  # Only run this once. HACK: change parameter in connect() instead
  if ".admin." not in sender.__name__:
    return
  # Don't do anything if the DB is already populated
  if User.objects.all().count() != 0:
    return
  print "Bootstrapping triggered by %s." % sender.__name__
  root = User.objects.create_superuser("root", "root@localhost", "root")
  print "Superuser created (username/password are 'root')"
  user1 = User.objects.create_user('one', 'one@localhost', 'one')
  user2 = User.objects.create_user('two', 'two@localhost', 'two')
  user3 = User.objects.create_user('tri', 'tri@localhost', 'tri')
  print "Users one, two, tri created and added to team 'demo'."
  team = Team(name="demo", shape=Team.CIRCULAR, manager=root, supervisor=root)
  team.save()
  for user in (root, user1, user2, user3):
    team.members.add(UserProfile.of(user))
  assert team.get_all_voters().count() == 4

  # Create votes in the past
  for days_in_the_past in range(6):
    day = date.today() - timedelta(days=days_in_the_past)
    Votes(vote=3, team=team, is_vote=True, date=day).save()
    Votes(vote=2, team=team, is_vote=True, date=day).save()
    Votes(vote=1, team=team, is_vote=True, date=day).save()
    Votes(vote=4, team=team, is_prediction=True, date=day).save()
    TodayVotes(user=UserProfile.of(user1), vote=1).save()
    TodayVotes(user=UserProfile.of(user2), vote=2).save()
    TodayVotes(user=UserProfile.of(user3), vote=3).save()
    TodayVotes(user=UserProfile.of(root),  vote=4).save()
  print "Voting history created."

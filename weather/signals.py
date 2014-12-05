from django.dispatch import Signal
from django.core.mail import send_mail

problem_detected = Signal(providing_args=["team"])


def email_sending_problem_handler(self, team, **kwargs):
  print "Warning supervisor of team %s" % team
  send_mail("Please investigate possible issue with %s" % team.name,
            "Manager prediction failures have reached threshold.",
            "no-reply@localhost",
            [team.supervisor.user.email])


day_switchover = Signal()

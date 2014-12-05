from django.core.management.base import NoArgsCommand
from weather import signals


class Command(NoArgsCommand):
  def handle_noargs(self, *args, **kwargs):
    signals.day_switchover.send(__name__)

from weather import models
from django.db.models import signals as db_signals

db_signals.post_syncdb.connect(models.init)

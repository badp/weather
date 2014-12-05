from django.contrib import admin
import weather.models as models

# Register your models here.


class TeamAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Team, TeamAdmin)


class TodayVotesAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.TodayVotes, TodayVotesAdmin)


class VotesAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Votes, VotesAdmin)

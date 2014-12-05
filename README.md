# [Weather Awareness System][0]

This is the proof-of-concept implementation of WAS. [Read more][0].

It requires Django 1.6 and Python 2.7 (as packaged e.g. in Ubuntu 14.10.)

## General deployment roadmap

1. Plug into your authentication system so people don't have to log onto WAS specifically
2. Add an HTML template as appropriate to `{% include %}` into your web application
3. Add or customize `problem_detected` signal handlers (see `weather\signals.py`)
4. Determine a moment when it is appropriate to show the block, and show it to the user at that time.
5. Secure the contents of the `TodayVotes` table, for example through database roles. The other tables defined in the weather application contain public data.
6. Schedule a daily job as appropriate for your system. It should run `python manage.py do_day_rollover`.
7. Remove (or customize) the bootstrapping code in the `init` function of the `models.py` file.

   [0]: http://bit.ly/WAS-thesis

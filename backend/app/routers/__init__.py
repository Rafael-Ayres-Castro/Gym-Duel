from . import auth, me, notifications, rules, scoreboard, streaks, workouts

ALL = (auth.router, me.router, workouts.router, scoreboard.router, rules.router, streaks.router, notifications.router)

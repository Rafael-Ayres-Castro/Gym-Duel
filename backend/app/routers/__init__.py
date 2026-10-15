from . import auth, me, rules, scoreboard, workouts

ALL = (auth.router, me.router, workouts.router, scoreboard.router, rules.router)

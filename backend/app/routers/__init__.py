from . import auth, me, scoreboard, workouts

ALL = (auth.router, me.router, workouts.router, scoreboard.router)

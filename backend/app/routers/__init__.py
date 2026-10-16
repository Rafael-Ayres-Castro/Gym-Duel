from . import auth, me, notifications, photos, rules, scoreboard, streaks, workouts

ALL = (
    auth.router, me.router, workouts.router, scoreboard.router, rules.router,
    streaks.router, notifications.router, photos.router,
)

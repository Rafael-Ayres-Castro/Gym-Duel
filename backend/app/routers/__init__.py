from . import auth, badges, challenges, me, notifications, photos, rewards, rules, scoreboard, streaks, workouts

ALL = (
    auth.router, me.router, workouts.router, scoreboard.router, rules.router, streaks.router,
    notifications.router, photos.router, rewards.router, challenges.router, badges.router,
)

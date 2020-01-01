from flamejam import app, db
from flamejam.models.jam import Jam, JamStatusCode
from flamejam.models.user import User

from uwsgidecorators import timer

from datetime import datetime, timedelta


@timer(1)
def tick(_):
    """This function is meant to be called regularly

    Its purpose is to send out mails and do site maintenance.
    """

    msg = ""

    with app.app_context():
        # Send Notifications
        for jam in Jam.query.all():
            n = jam.send_all_notifications()
            if n >= 0:
                msg += f"sending notification {n} on jam {jam.slug}\n"

        # Delete unverified users
        for user in User.query.filter_by(is_verified=False):
            # new_mail is set on users that *changed* their address
            if not user.new_email and user.registered < datetime.utcnow() - timedelta(days=7):
                msg += f"deleted user {user.username} for being unverified too long\n"
                db.session.delete(user)

        # Remove invitations after game rating has started
        for jam in Jam.query.all():
            if jam.get_status().code >= JamStatusCode.RATING:
                for team in jam.teams:
                    for i in team.invitations:
                        msg += (
                            f"deleted invitation {i.id} on jam {jam.slug} - jam rating has started\n"
                        )
                        db.session.delete(i)

        db.session.commit()

        return msg

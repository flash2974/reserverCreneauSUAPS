import pytz
import time
import schedule
import threading

from flask import flash, redirect, render_template, request, url_for
from flask_login import UserMixin, login_required, login_user, logout_user


from src.utilities import read_config, save_config
from src import login_manager, app
from src import auto, notifier
from src import PASSWORD, TOKEN, DEBUG


# === FLASK AUTH ===
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and request.args.get("token") == TOKEN:
        user = User("admin")
        login_user(user, remember=True)
        return redirect(url_for("home"))

    if request.method == "POST":
        password = request.form["password"]
        want_remember = "remember" in request.form

        if password == PASSWORD:
            user = User("admin")
            login_user(user, remember=want_remember)
            return redirect(url_for("home"))
        else:
            flash("Mot de passe incorrect.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/debug_headers")
def debug_headers():
    return dict(request.headers)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/test")
@login_required
def test():
    notifier.notify("Hello from `/test` !")
    return "Message sent !"


@app.route("/")
@login_required
def home():
    activities_dict = auto.get_activities()
    config_file = read_config()
    jobs = [
        (
            job.next_run.astimezone(pytz.timezone("Europe/Paris")).strftime(
                "%d-%m-%Y %H:%M:%S"
            ),
            job.note,
        )
        for job in sorted(schedule.jobs, key=lambda job: job.next_run)
    ]
    sports = sorted(list({activity["activity_name"] for activity in activities_dict}))

    return render_template(
        "index.html",
        activities_dict=activities_dict,
        config_file=config_file,
        sports=sports,
        jobs=jobs,
    )


@app.route("/reserver", methods=["POST"])
@login_required
def reserver():
    activity_id = request.form.get(
        "id_resa"
    )  # Récupère l'ID de l'activité sélectionnée
    if not activity_id:
        flash("Aucune activité sélectionnée pour la réservation.", "error")
        return redirect("/")

    with auto:
        auto.set_periode()
        auto.reserver_creneau(activity_id)

    print(f"Réservation effectuée pour l'activité ID : {activity_id}")
    flash("Réservation effectuée !", "success")
    return url_for("home")


@app.route("/update", methods=["POST"])
@login_required
def update():
    action = request.form.get("action")

    with auto:
        if action == "sauvegarder":
            selected_ids = request.form.getlist("id_resa")
            save_config({"ids_resa": selected_ids})
            auto.set_all_schedules()
            flash("Sauvegardé !")

        elif action.startswith("reserver_"):
            activity_id = action.split("_")[1]
            auto.set_periode()
            auto.reserver_creneau(activity_id)
            flash("Réservation effectuée !", "success")

    return redirect(url_for("home"))


def start_scheduler():
    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)

    with auto:
        auto.set_all_schedules()
    threading.Thread(target=scheduler_loop, daemon=True).start()


start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)

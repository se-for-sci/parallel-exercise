import nox

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["run"]

@nox.session(python="3.13")
def run(session):
    session.install("-e.")
    session.run("cgol")


@nox.session(python="3.13t")
def run_noGIL(session):
    session.install("-e.")
    session.run("cgol")


@nox.session(python=["3.13","3.13t"])
def time(session):
    session.install("-e.")
    session.run("python","timing/time_cgol.py")

import nox

@nox.session(python=["3.11"])
def tests(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("poetry", "shell")
    session.run("coverage", "run", "-m", "pytest", "--junit-xml=reports/junit/junit.xml")
    session.run("coverage", "report")
    session.run("coverage", "xml", "-o", "reports/coverage.xml")
    session.run("coverage", "html", "-d", "reports/coverage")
    session.run("genbadge", "coverage", "-i", "reports/coverage.xml", "-o", ".badges/coverage-badge.svg")
    session.run("genbadge", "tests", "-o", ".badges/tests-badge.svg")

@nox.session
def lint(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("poetry", "shell")
    session.run("pylint", "src/", "--exit-zero")
    #session.run("black", "--check", ".")
    session.run("flake8", ".", "--exit-zero", "--statistics", "--output-file=reports/flake8/flake8stats.txt")
    session.run("genbadge", "flake8", "-o", ".badges/flake8-badge.svg")
    session.run("flynt", "src/")

@nox.session
def typing(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("poetry", "shell")
    session.run("mypy", ".")

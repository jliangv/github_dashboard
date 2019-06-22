# github_dashboard

This is a Flask app that can be launch locally by invoking:
python main.py

Required dependencies: flask, pandas

Please set up environment variables to row it locally: PILLAR_USER, PILLAR_TOKEN

Local endpoints for the app:

Main Table:

/showrepos/{org}/Name

Ex: http://127.0.0.1:5000/showrepos/facebook/Name


Order By Forks/Star/Contributors:

/showrepos/{org}/forks

/showrepos/{org}/stars

/showrepos/{org}/contributors

Ex: http://127.0.0.1:5000/showrepos/facebook/forks


Top contribution by group (internal/external):

/topcontrib/{org}

Ex: http://127.0.0.1:5000/topcontrib/libra

Ex: http://127.0.0.1:5000/topcontrib/facebook (might hit API rate limit)

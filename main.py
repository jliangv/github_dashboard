import requests
import collections
import pandas as pd
import os
from flask import Flask
from flask import jsonify
from flask import Flask, render_template

app = Flask(__name__)
user = os.environ['PILLAR_USER']
token = os.environ['PILLAR_TOKEN']

@app.route('/getorg/<org>')
def get_org(org):
    """
    test to get the top level info on a particular org
    """
    url = 'https://api.github.com/orgs/' + org
    r = requests.get(url, auth=(user, token))
    return r.text


@app.route('/getrepos/<org>')
def get_repos(org):
    """
    test to get the list of repos for an org in JSON
    """
    url = 'https://api.github.com/orgs/{}/repos'.format(org)
    r = requests.get(url, auth=(user, token))
    print(type(r.json()))
    return jsonify(r.json())

def counter_to_df(counter):
    """
    convert counter to dataframe with some logic to handle empty counter
    """
    if not len(counter):
        counter['na'] = 0

    df = pd.DataFrame.from_dict(counter, orient='index').reset_index()
    df.rename(columns={'index':'Login', 0:'Total Contributions'}, inplace=True)
    return df
 

@app.route('/topcontrib/<org>')
def show_top_contrib(org):
    """
    Show two tables for the top contributors count by contribution
    - internal contributors - associated with the same org of the repo
    - external contributors - not associated with the same org
    """
    url = 'https://api.github.com/orgs/{}/repos'.format(org)
    r = requests.get(url, auth=(user, token))
    repos = [x['name'] for x in r.json()]

    is_internals = {}
    in_contributors = collections.Counter()
    ex_contributors = collections.Counter()

    # check all repos and collect aggregate stats
    for repo in repos:
        per_page = 100 # at most 100 is allowed, i tried using higher number,
                       # but only got back 100 records, need to use pagination
        page = 1
        while True:
            url = "https://api.github.com/repos/{}/{}/contributors?per_page={}&page={}".format(
                org, repo, per_page, page)
            r = requests.get(url, auth=(user, token))
            data = r.json()
    
            # to get user repos https://api.github.com/users/{user}/repos
            # need to request the api asynchrnonously if possible
            # but 5000 rate limit is not quite enough for many request
            for contributor in data:
                organizations_url = contributor["organizations_url"]
                r = requests.get(organizations_url, auth=(user, token))
                orgs_data = r.json()
                contributor_login = contributor["login"]
                contributions = contributor["contributions"]
                if contributor_login in is_internals:
                    is_internal = is_internals[contributor_login]
                else:                
                    is_internal = any(org_data.get("login")==org for org_data in orgs_data)
                    print("Checking is_internal for {}, got:{}".format(contributor_login, is_internal))
    
                if is_internal:
                    in_contributors[contributor_login] = contributions
                else:
                    ex_contributors[contributor_login] = contributions
    
            if len(data) < per_page:
                break
            page += 1
            if page > 100:
                print("Not expecting so many collaborators, count:{}".format(count))
                # order of thousands of collaborators for the most populars projects
                # something could be wrong with we have hitting 10k
                break

    in_df = counter_to_df(in_contributors) 
    ex_df = counter_to_df(ex_contributors) 
    return render_template('home.html', 
            page_title='Top Contributors for ' + org,
            tables=[in_df.to_html(classes='in_data', index=False), 
                    ex_df.to_html(classes="ex_data", index=False)],
            titles=["na", "Top Internal", "Top External"]
            )


def extract_contributor_count(org, repo):
    """
    helper function to get the contributor count for a specified
    org and repo
    """
    per_page = 100 # at most 100 is allowed, i tried using higher number,
                   # but only got back 100 records, need to use pagination
    count = 0
    page = 1
    while True:
        url = "https://api.github.com/repos/{}/{}/contributors?per_page={}&page={}".format(
            org, repo, per_page, page)
        r = requests.get(url, auth=(user, token))
        data = r.json()
        count += len(data)
        if len(data) < per_page:
            break
        page += 1
        if page > 100:
            print("Not expecting so many collaborators, count:{}".format(count))
            # order of thousands of collaborators for the most populars projects
            # something could be wrong with we have hitting 10k
            break
    return count



@app.route('/showrepos/<org>/<by>')
def show_repos(org, by):
    """
    render a html table as the "dashboard" for this assignment
    org - the orgination
    by - the column to short the table by
         possible values: Forks, Name, Contributors, Stars
    """
    url = 'https://api.github.com/orgs/{}/repos'.format(org)
    r = requests.get(url, auth=(user, token))
    data = r.json()
    data = [{
                'Name':x.get('name'),
                'Forks':x.get('forks_count'),
                'Stars':x.get('stargazers_count'),
                'Contributors':extract_contributor_count(org, x.get('name'))
            }
            for x in data]
    df = pd.DataFrame(data, columns= ['Name', 'Forks', 'Stars', 'Contributors'])
    if by:
        df.sort_values(by=[by, 'Name'], inplace=True, ascending=False)
    return render_template('home.html', 
            page_title='Repos for ' + org,
            tables=[df.to_html(classes='data', index=False)], 
            titles=df.columns.values)

    
if __name__ == '__main__':
   app.run()

import datetime
import pandas as pd
import requests

yt_url = "https://your_youtrack_server_url/api/issues"
yt_token = "your_token"
my_projects_filter = "{Project name 1}, {Project name 2}, {Project name 3}"

def get_all_issues_from_api(issue_types: list, projects=my_projects_filter):
    headers = {'Authorization': 'Bearer ' + yt_token}
    payload = {'$top': -1, '$skip': 0, 'fields': 'project(name),numberInProject,summary,created,reporter(login),customFields(id,projectCustomField(field(name)),value(name,isResolved)),created,updated,resolved', 'query': f'project: {projects} Type: {", ".join(issue_types)}'} #created: 2024-05-26 .. *
    response = requests.get(url=yt_url, params=payload, headers=headers)
    return response.json()

def get_custom_field_value(issue, field_name: str):
    field_value = None
    for cs in issue["customFields"]:
        if cs["projectCustomField"]["field"]["name"] == field_name:
            field_value = cs["value"]["name"]
            break
    return field_value

def get_leak_tag_for_bugs(bug):
    """made for a specific case"""
    if get_custom_field_value(bug, "Type") == "Bug":
        return "prod"
    else:
        return "test"

def get_priority_num(issue):
    priorities = {"Blocker": 0, "Critical": 1, "Medium": 2, "Low": 3, "Minor": 4}
    priority = get_custom_field_value(issue, "Priority")
    return priorities[priority]

def get_resolve_status(issue):
    resolved = None
    for cs in issue["customFields"]:
        if cs["projectCustomField"]["field"]["name"] == "State":
            key_list = list(cs["value"])
            if "isResolved" in key_list:
                resolved = cs["value"]["isResolved"]
            break
    return resolved

def get_team(issue):
    """made for a specific case"""
    team = ""
    if issue["project"]["name"] == "Analytics Portal":
        for cs in issue["customFields"]:
            if cs["projectCustomField"]["field"]["name"] == "Block":
                for block in cs["value"]:
                    team = team + block["name"]
                break
    else:
        team = issue["project"]["name"]
    return team.split(" ")[0]

def get_created_date(issue):
    return datetime.datetime.fromtimestamp(int(str(issue["created"])[:-3]))

def get_resolved_date(issue):
    try:
        return datetime.datetime.fromtimestamp(int(str(issue["resolved"])[:-3]))
    except:
        return None

def get_ttm(issue):
    resolved_date = get_resolved_date(issue)
    created_date = get_created_date(issue)
    if resolved_date is not None:
        delta = resolved_date - created_date
        return delta.total_seconds() // 3600 # в часах
    else:
        return 0

def get_csv_for_issues_from_api(issue_types: list, file_name: str):
    """create csv file with summary,id,reporter,leak_tag (for bugs),priority,priority_num,status,created_date,resolved,resolved_date,ttm,team fields"""
    all_issues = get_all_issues_from_api(issue_types=issue_types)
    summaries = list()
    ids = list()
    reporters = list()
    priorities = list()
    priorities_num = list()
    status = list()
    resolved = list()
    created_date = list()
    resolved_date = list()
    ttm = list()
    teams = list()
    if "Bug" in issue_types:
        leak_tags = list()

    for issue in all_issues:
        summaries.append(issue["summary"])
        ids.append(issue["numberInProject"])
        reporters.append(issue["reporter"]["login"])
        priorities.append(get_custom_field_value(issue, "Priority"))
        priorities_num.append(get_priority_num(issue))
        status.append(get_custom_field_value(issue, "State"))
        created_date.append(get_created_date(issue))
        resolved.append(get_resolve_status(issue))
        resolved_date.append(get_resolved_date(issue))
        ttm.append(get_ttm(issue))
        teams.append(get_team(issue))
        if "Bug" in issue_types:
            leak_tags.append(get_leak_tag_for_bugs(issue))

    data_df = {'summary': summaries, 'id': ids, 'reporter': reporters, "priority": priorities,
               "priority_num": priorities_num, "status": status, "created_date": created_date, "resolved": resolved,
               "resolved_date": resolved_date, "ttm": ttm, "team": teams}
    if "Bug" in issue_types:
        data_df["leak_tag"] = leak_tags

    df = pd.DataFrame(data_df)
    print('DataFrame:\n', df)

    df.to_csv(file_name, index=False, header=True)

def main():
    get_csv_for_issues_from_api(issue_types=["Bug", "Bug-debug"], file_name="bugs.csv")
    get_csv_for_issues_from_api(issue_types=["Task"], file_name="tasks.csv")

if __name__ == "__main__":
    main()

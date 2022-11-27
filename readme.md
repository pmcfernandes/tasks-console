### tasks
Create tasks with console and python

#### Usage
    task.py list [--project=<project>]
    task.py find <regex> [--project=<project>]
    task.py add <task> [--due=<date>] [--project=<project>]
    task.py <id> change [<task>] [--due=<date>] [--mark=<mark>] [--project=<project>]
    task.py <id> resolved
    task.py <id> delete
    task.py show projects
    task.py -h | --help

#### examples
    
    python3 task.py list
    python3 task.py list --project=supermarket
    python3 task.py find "hello world \w*"
    python3 task.py find "buy chocolate \w*" --project=supermarket
    python3 task.py add "My first task"
    python3 task.py add "My first task" --due=2weeks
    python3 task.py add "buy chocolate for easter" --due=2weeks --project=supermarket
    python3 task.py 1 change "hello task"
    python3 task.py 1 change --due=1month
    python3 task.py 1 change --project=easter
    python3 task.py 1 resolved
    python3 task.py 1 delete
    python3 task.py show projects

    

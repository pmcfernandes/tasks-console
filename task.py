"""Task console app. Add and list your life tasks

Usage:
  task.py list [--project=<project>]
  task.py find <regex> [--project=<project>]
  task.py add <task> [--due=<date>] [--project=<project>]
  task.py <id> change [<task>] [--due=<date>] [--mark=<mark>] [--project=<project>]
  task.py <id> resolved
  task.py <id> delete
  task.py show projects
  task.py -h | --help

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
from datetime import datetime
from time import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from dateutil.relativedelta import relativedelta
import sqlite3
import os
import re


def getProjectByName(conn, name: str) -> int:
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM projects WHERE name LIKE '{name}'")
    rows = cur.fetchall()

    if len(rows) == 1:
        return int(rows[0][0])
    elif len(rows) == 0:
        cur.execute("""
            INSERT INTO projects (name) VALUES (?);
        """, (name, ))

        inserted_id = cur.lastrowid

        try:
            conn.commit()
        except:
            conn.rollback()
            raise Exception(f"Can't create a new project with name '{name}'.")

        return inserted_id
    else:
        return 0


def calculateDueDate(due: str):
    dt = datetime.now()

    if due.endswith("day") or due.endswith("days"):
        s = re.sub(r'day\w*', "", due)
        s = "1" if s == "" else s
        dt = dt + relativedelta(days=int(s))
    if due.endswith("week") or due.endswith("weeks"):
        s = re.sub(r'week\w*', "", due)
        s = "1" if s == "" else s
        dt = dt + relativedelta(weeks=int(s))
    if due.endswith("month") or due.endswith("months"):
        s = re.sub(r'month\w*', "", due)
        s = "1" if s == "" else s
        dt = dt + relativedelta(months=int(s))
    if due.endswith("year") or due.endswith("years"):
        s = re.sub(r'year\w*', "", due)
        s = "1" if s == "" else s
        dt = dt + relativedelta(years=int(s))

    return datetime.timestamp(dt)


if __name__ == "__main__":
    arguments = docopt(__doc__, argv=None, help=True, version="1.0", options_first=False)
    console = Console()

    firstTime = False if os.path.exists("tasks.db") else True
    conn = sqlite3.connect("tasks.db")

    if firstTime:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id int, title text, dt int, due int, resolved int);
        """)

        cur.execute("""
            CREATE TABLE projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name text);
        """)

    if arguments["add"]:
        if arguments["<task>"] is not None:
            text = str(arguments["<task>"])

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tasks (project_id, title, dt, resolved) VALUES (?, ?, ?, ?);
            """, (0, text, time(), 0))

            task_id = cur.lastrowid

            if arguments["--due"] is not None:
                due = str(arguments["--due"])
                due_date = calculateDueDate(due)

                cur.execute(f"""
                    UPDATE tasks SET due = ? WHERE id = {task_id} 
                """, (due_date,))

            if arguments["--project"] is not None:
                project = str(arguments["--project"])
                project_id = getProjectByName(conn, project)

                if project_id > 0:
                    cur.execute(f"""
                        UPDATE tasks SET project_id = ? WHERE id = {task_id} 
                    """, (project_id,))

            try:
                conn.commit()
                console.print(f"Task added with id {task_id}")
            except:
                conn.rollback()
                console.print("Error adding task.")

    if arguments["change"]:
        task_id = int(arguments["<id>"])
        cur = conn.cursor()

        if arguments["<task>"] is not None:
            text = str(arguments["<task>"])
            cur.execute(f"""
                UPDATE tasks SET title = ? WHERE id = {task_id} 
            """, (text,))

        if arguments["--due"] is not None:
            due = str(arguments["--due"])
            due_date = calculateDueDate(due)

            cur.execute(f"""
               UPDATE tasks SET due = ? WHERE id = {task_id} 
            """, (due_date,))

        if arguments["--mark"] is not None:
            mark = str(arguments["--mark"])
            resolved = 1 if mark.lower() == "resolved" else 0

            cur.execute(f"""
                UPDATE tasks SET resolved = ? WHERE id = {task_id} 
            """, (resolved,))

        if arguments["--project"] is not None:
            project = str(arguments["--project"])
            project_id = getProjectByName(conn, project)

            if project_id > 0:
                cur.execute(f"""
                   UPDATE tasks SET project_id = ? WHERE id = {task_id} 
               """, (project_id,))

        try:
            conn.commit()
            console.print(f"Task with id {task_id} updated.")
        except:
            conn.rollback()
            console.print("Error updating task.")

    if arguments["resolved"]:
        if arguments["<id>"] is not None:
            task_id = int(arguments["<id>"])

            cur = conn.cursor()
            cur.execute(f"""
                UPDATE tasks SET resolved = 1 WHERE id = {task_id} 
            """)

            try:
                conn.commit()
                console.print(f"Task with id {task_id} is mark as resolved.")
            except:
                conn.rollback()
                console.print("Error updating task.")

    if arguments["delete"]:
        if arguments["<id>"] is not None:
            if Confirm.ask("You want remove this task?"):
                task_id = int(arguments["<id>"])

                cur = conn.cursor()
                cur.execute(f"""
                    DELETE FROM tasks WHERE id = {task_id};
                """)

                try:
                    conn.commit()
                    console.print("Task deleted.")
                except:
                    conn.rollback()

    if arguments['list'] or arguments['find']:
        i = 0

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Id", style="dim", width=6)
        table.add_column("Date", style="dim", width=10)
        table.add_column("Due", style="dim", width=10)
        table.add_column("Title")

        if arguments["--project"] is None:
            table.add_column("Project")

        # Get rows
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT tasks.id, dt, title, due, projects.id AS project_id, projects.name as project_name 
            FROM tasks
                LEFT JOIN projects ON projects.id = tasks.project_id 
            WHERE resolved = 0
        """)
        for row in rows:
            if arguments['find']:
                regex = str(arguments["<regex>"])
                if re.match(rf'{regex}', str(row[2])) is None:
                    continue
                else:
                    if arguments["--project"] is not None:
                        project = str(arguments["--project"])
                        if str(row[5]) != project:
                            continue

            i += 1
            inserted_date = datetime.utcfromtimestamp(int(row[1])).strftime('%Y-%m-%d')

            if row[3] is None:
                due_date = ""
            else:
                due_date = datetime.utcfromtimestamp(int(row[3])).strftime('%Y-%m-%d')

            if arguments["--project"] is None:
                table.add_row(str(row[0]), inserted_date, due_date, str(row[2]), str(row[5]))
            else:
                table.add_row(str(row[0]), inserted_date, due_date, str(row[2]))

        console.print(table)
        console.print("Total tasks: {total}".format(total=i))

    if arguments["show"]:
        if arguments["projects"]:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name")

            # Get rows
            cur = conn.cursor()
            rows = cur.execute("SELECT name from projects")
            for row in rows:
                table.add_row(str(row[0]))

            console.print(table)

    conn.close()

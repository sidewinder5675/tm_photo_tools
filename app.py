from flask import Flask, render_template, request, redirect, url_for, jsonify

from dir_creator import create_working_directory, copy_and_rename_images
import os
from datetime import datetime
from gif_creator import process_images


app = Flask(__name__)


@app.route("/view_projects")
def view_projects():
    sorted_projects = get_sorted_projects()
    return render_template(
        "view_projects.html",
        sorted_projects=sorted_projects,
        folder_exists=folder_exists,
    )


@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    if request.method == "POST":
        date = request.form.get("date")
        project_name = request.form.get("project_name")

        if not date or not project_name:
            return render_template(
                "create_project.html", error="Please enter valid inputs."
            )

        working_directory = create_working_directory(date, project_name)
        # Replace the following line with the actual SD card path
        sd_card_path = "/path/to/sd/card"

        if sd_card_path:
            copy_and_rename_images(sd_card_path, working_directory, project_name)

        return redirect(url_for("index"))
    return render_template("create_project.html")


@app.route("/")
def index():
    return render_template("index.html")


def get_sorted_projects():
    base_directory = "Projects"
    project_directories = os.listdir(base_directory)
    sorted_projects = []

    for project_dir in project_directories:
        project_path = os.path.join(base_directory, project_dir)
        if os.path.isdir(project_path):
            project_name = project_dir.split(" ", 1)[1]
            project_date = datetime.strptime(project_dir.split(" ", 1)[0], "%Y-%m-%d")
            sorted_projects.append(
                {"name": project_name, "date": project_date, "path": project_path}
            )

    sorted_projects.sort(key=lambda x: x["date"])

    return sorted_projects


def folder_exists(basePath, folderName):
    folderPath = os.path.join(basePath, folderName)
    return os.path.isdir(folderPath)


@app.route("/create_gif", methods=["POST"])
def create_gif():
    data = request.get_json()
    project_path = data.get("projectPath")

    try:
        process_images(project_path, os.path.join(project_path, "RAWs"))
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


if __name__ == "__main__":
    app.run(host="192.168.1.250", port=5003, debug=True)

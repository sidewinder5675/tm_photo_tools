import os
import shutil
from tqdm import tqdm


# Function to create the working directory
def create_working_directory(date, project_name):
    base_directory = os.path.expanduser("~/Pictures")
    date_folder = date.replace("/", "-")
    working_directory = os.path.join(base_directory, f"{date_folder} {project_name}")
    os.makedirs(working_directory, exist_ok=True)
    return working_directory


# Function to copy and rename images from SD card to working directory
def copy_and_rename_images(sd_card_path, working_directory, project_name):
    raws_directory = os.path.join(working_directory, "RAWs", "Card 1")
    os.makedirs(raws_directory, exist_ok=True)
    image_files = [
        file
        for file in os.listdir(sd_card_path)
        if file.lower().endswith(
            (".jpg", ".jpeg", ".png", ".cr2", ".cr3", ".nef", ".arw")
        )
    ]

    # Use tqdm to display progress bar
    progress_bar = tqdm(image_files, desc="Copying images", unit="image", ncols=80)
    for file in progress_bar:
        src_path = os.path.join(sd_card_path, file)
        dst_name = f"{project_name} | {file}"
        dst_path = os.path.join(raws_directory, dst_name)
        shutil.copy2(src_path, dst_path)

    # Update progress bar description after completion
    progress_bar.set_description("Copying images [Done]")

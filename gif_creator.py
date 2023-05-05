import os
import sys
import shutil
from datetime import datetime
import subprocess
from tqdm import tqdm
import imageio
import rawpy
import concurrent.futures
from PIL import Image


def get_capture_time(file_path):
    cmd = ["exiftool", "-DateTimeOriginal", file_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = proc.communicate()

    if proc.returncode != 0:
        raise ValueError(f"Error reading EXIF data for {file_path}")

    date_time_str = stdout.decode().split(": ")[-1].strip()
    return datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")


def make_directories(output_path):
    main_folder = os.path.join(output_path, "GIFs")
    os.makedirs(main_folder, exist_ok=True)

    raw_gif_folder = os.path.join(main_folder, "RAW_GIFs")
    os.makedirs(raw_gif_folder, exist_ok=True)

    gif_exports_folder = os.path.join(main_folder, "GIF_EXPORTS")
    os.makedirs(gif_exports_folder, exist_ok=True)

    finished_gifs_folder = os.path.join(main_folder, "FINISHED_GIFs")
    os.makedirs(finished_gifs_folder, exist_ok=True)

    exported_gif_unstablized = os.path.join(main_folder, "UNSTABILIZED_GIF_EXPORTS")
    os.makedirs(exported_gif_unstablized, exist_ok=True)

    return (
        raw_gif_folder,
        gif_exports_folder,
        finished_gifs_folder,
        exported_gif_unstablized,
    )


def get_image_paths(folder_path):
    image_paths = []

    for card_folder in os.listdir(folder_path):
        card_folder_path = os.path.join(folder_path, card_folder)
        if os.path.isdir(card_folder_path):
            for file in os.listdir(card_folder_path):
                if file.lower().endswith(".cr3"):
                    image_paths.append(os.path.join(card_folder_path, file))

    return image_paths


def convert_cr3_to_png(cr3_path, png_path, max_size=512):
    with rawpy.imread(cr3_path) as raw:
        rgb = raw.postprocess()
    pil_image = Image.fromarray(rgb)

    # Resize the image while maintaining the aspect ratio
    aspect_ratio = float(pil_image.width) / float(pil_image.height)
    if pil_image.width > pil_image.height:
        new_width = max_size
        new_height = int(max_size / aspect_ratio)
    else:
        new_height = max_size
        new_width = int(max_size * aspect_ratio)

    resized_image = pil_image.resize((new_width, new_height), Image.ANTIALIAS)
    resized_image.save(png_path, "PNG")


def convert_images_to_png(sequence_images):
    png_paths = []

    def convert_image_to_png(img_path):
        png_path = os.path.splitext(img_path)[0] + ".png"
        convert_cr3_to_png(img_path, png_path)
        return png_path

    with concurrent.futures.ThreadPoolExecutor() as executor:
        png_paths = list(executor.map(convert_image_to_png, sequence_images))

    return png_paths


def create_low_quality_gif(sequence_images, gif_path):
    sequence_images = sorted(sequence_images, key=get_capture_time)

    png_sequence = []

    for img in sequence_images:
        png_path = os.path.splitext(img)[0] + ".png"
        convert_cr3_to_png(img, png_path)
        png_sequence.append(png_path)

    sorted_png_sequence = sorted(png_sequence, key=lambda x: os.path.basename(x))

    with imageio.get_writer(gif_path, mode="I", duration=0.1) as writer:
        for png_file in sorted_png_sequence:
            image = imageio.imread(png_file)
            writer.append_data(image)

    for png_file in png_sequence:
        os.remove(png_file)


def find_image_files(folder_path):
    image_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".cr3"):
                image_files.append(os.path.join(root, f))
    return image_files


def process_sequence(
    sequence, gif_counter, raw_gif_folder, gif_exports_folder, finished_gifs_folder
):
    gif_folder = os.path.join(
        raw_gif_folder, f"GIF{gif_counter} | {len(sequence)} images"
    )
    os.makedirs(gif_folder, exist_ok=True)

    gif_export_subfolder = os.path.join(
        gif_exports_folder, f"GIF{gif_counter} | {len(sequence)} images"
    )
    os.makedirs(gif_export_subfolder, exist_ok=True)

    pbar = tqdm(sequence, unit="image", ncols=100, desc=f"Processing GIF {gif_counter}")
    for img in pbar:
        original_name = os.path.basename(img)
        shutil.copy(img, os.path.join(gif_folder, original_name))

        # Update progress bar description
        pbar.set_description(f"Processing GIF {gif_counter} - {original_name}")

    gif_name = f"GIF{gif_counter}.gif"
    gif_path = os.path.join(finished_gifs_folder, gif_name)
    print(f"Creating GIF {gif_counter} with {len(sequence)} images...")
    create_low_quality_gif(
        [os.path.join(gif_folder, os.path.basename(img)) for img in sequence],
        gif_path,
    )


def process_images(output_path, folder_path):
    (
        raw_gif_folder,
        gif_exports_folder,
        finished_gifs_folder,
        exported_gif_unstablized,
    ) = make_directories(output_path)
    files = find_image_files(folder_path)
    files.sort(key=os.path.getmtime)

    print(f"Processing {len(files)} images...")
    gif_counter = 0
    current_sequence = []
    prev_time = None

    for file in tqdm(files, unit="image", ncols=100):
        current_time = get_capture_time(file)
        if prev_time is None or (current_time - prev_time).total_seconds() <= 1:
            current_sequence.append(file)
        else:
            if len(current_sequence) >= 20:
                gif_counter += 1
                process_sequence(
                    current_sequence,
                    gif_counter,
                    raw_gif_folder,
                    gif_exports_folder,
                    finished_gifs_folder,
                )
            current_sequence = [file]
        prev_time = current_time

    if len(current_sequence) >= 10:
        gif_counter += 1
        process_sequence(
            current_sequence,
            gif_counter,
            raw_gif_folder,
            gif_exports_folder,
            finished_gifs_folder,
        )

    print(f"Completed processing. Created {gif_counter} GIF sequence folders.")


if __name__ == "__main__":
    folder_path = input("Enter the path to the top-level folder: ").strip()
    output_path = folder_path
    raws_folder = os.path.join(folder_path, "RAWs")

    process_images(output_path, raws_folder)

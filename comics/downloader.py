from typing import List
from dotenv import load_dotenv
from comics.models import DownloadJob, DownloadJobStep
from comics.utils import sanitize_filename
import threading
import shutil
import img2pdf

import requests
import os

load_dotenv()

DOWNLOAD_BASE_FOLDER = os.getenv("DOWNLOAD_FOLDER")


def create_folders(job: DownloadJob):
    os.makedirs(f"{DOWNLOAD_BASE_FOLDER}\\{job.id}", exist_ok=True)

    for issue_index in range(job.total_issues):
        os.makedirs(f"{DOWNLOAD_BASE_FOLDER}\\{job.id}\\{issue_index}", exist_ok=True)


def download_images(job: DownloadJob, steps: List[DownloadJobStep], threads=4):
    if not steps:
        print("No images to download.")
        return

    def worker(step: DownloadJobStep):
        download_image(job, step)

    # Create a thread pool
    thread_list = []
    for step in steps:
        if len(thread_list) >= threads:
            for t in thread_list:
                t.join()
            thread_list.clear()

        t = threading.Thread(target=worker, args=(step,))
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()


def download_image(job: DownloadJob, download_job_step: DownloadJobStep):
    link = download_job_step.image_link
    save_path = f"{DOWNLOAD_BASE_FOLDER}\\{job.id}\\{download_job_step.issue_index_number}\\{download_job_step.page_number}.png"

    try:
        response = requests.get(link, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):  # Download in chunks
                file.write(chunk)

        # update db
        job.downloaded_pages += 1
        job.save()

        download_job_step.complete = True
        download_job_step.save()

    except requests.exceptions.RequestException as e:
        print(
            f"Failed to download {download_job_step.issue_index_number}, {download_job_step.page_number}, {download_job_step.image_link}"
        )
        download_job_step.retry = True
        download_job_step.complete = False
        download_job_step.save()


# Recursively removes a download job's folder and it's contents
def recursive_remove_folder(job: DownloadJob):
    path = f"{DOWNLOAD_BASE_FOLDER}\\{job.id}"
    if os.path.exists(path):  # Check if the folder exists
        shutil.rmtree(path)  # Remove directory and all contents


def combine(job: DownloadJob):
    cleaned = sanitize_filename(job.name)
    folder = f"{DOWNLOAD_BASE_FOLDER}\\{job.id}"
    output_pdf_path = os.path.join(folder, f"{cleaned}.pdf")

    image_paths = []

    # Sort subdirectories numerically
    for sub_dir in sorted(os.listdir(folder), key=lambda x: int(x)):
        sub_dir_path = os.path.join(folder, sub_dir)

        if os.path.isdir(sub_dir_path):  # Ensure it's a directory
            # Sort images numerically and add to the list
            images = sorted(
                os.listdir(sub_dir_path), key=lambda x: int(os.path.splitext(x)[0])
            )
            image_paths.extend(os.path.join(sub_dir_path, img) for img in images)

    if not image_paths:
        print("No images found to combine.")
        return

    # Convert images to PDF
    with open(output_pdf_path, "wb") as pdf_file:
        pdf_file.write(img2pdf.convert(image_paths))

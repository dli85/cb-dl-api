import re
import os


def comic_to_json(comic):
    return {
        "id": comic.id,
        "title": comic.title,
        "date_published": comic.date_published,
        "link": comic.link,
        "writers": comic.writers,
        "artists": comic.artists,
        "number_issues": comic.number_issues,
        "last_updated": comic.last_updated,
    }


def issue_to_json(issue):
    return {
        "id": issue.id,
        "title": issue.title,
        "link": issue.link,
        "comic_id": issue.comic_id.id,
        "pages": issue.pages,
    }


def page_to_json(page):
    return {
        "page_number": page.page_number,
        "title": page.title,
        "image_link": page.image_link,
    }


def download_job_to_json(job):
    return {
        "id": job.id,
        "downloaded_pages": job.downloaded_pages,
        "total_pages": job.total_pages,
        "total_issues": job.total_issues,
        "complete": job.complete,
        "name": job.name,
    }


# Extracts a year and creates a date
def create_date(date_string):
    match = re.search(r"\b(\d{4})\b", date_string)
    if match:  # Check if a match was found
        return f"{int(match.group(1))}-01-01"
    else:
        raise ValueError("A four digit date was not found in date string")


def sanitize_filename(filename: str, replacement: str = "_") -> str:

    invalid_chars = r'[<>:"/\\|?*]'  # Includes backslash (\\) and forward slash (/)

    cleaned_filename = re.sub(invalid_chars, replacement, filename)

    cleaned_filename = cleaned_filename.strip()

    if not cleaned_filename:
        cleaned_filename = "complete"

    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if cleaned_filename.upper() in reserved_names:
        cleaned_filename = f"_{cleaned_filename}"

    return cleaned_filename


if __name__ == "__main__":
    print(create_date("1111"))

import re


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
        }


# Extracts a year and creates a date
def create_date(date_string):
    match = re.search(r"\b(\d{4})\b", date_string)
    if match:  # Check if a match was found
        return f"{int(match.group(1))}-01-01"
    else:
        raise ValueError("A four digit date was not found in date string")


if __name__ == "__main__":
    print(create_date("1111"))

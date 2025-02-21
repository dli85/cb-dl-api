from typing import List
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .utils import *
from .models import Comic, Issue, Page, DownloadJob, DownloadJobStep
from django.shortcuts import get_object_or_404
from .downloader import (
    download_images,
    create_folders,
    recursive_remove_folder,
    combine,
)


@api_view(["GET"])
def get_all_comics(request):
    comics = Comic.objects.all()  # Retrieve all comics
    comic_list = [
        {
            "id": comic.id,
            "title": comic.title,
            "date_published": comic.date_published,
            "link": comic.link,
            "writers": comic.writers,
            "artists": comic.artists,
            "number_issues": comic.number_issues,
            "last_updated": comic.last_updated,
        }
        for comic in comics
    ]
    return Response({"comics": comic_list})


@api_view(["GET"])
def get_comic(request, comic_id):
    comic = Comic.objects.get(id=comic_id)
    return Response(comic_to_json(comic))


@api_view(["GET"])
def get_issues_for_comic(request, comic_id):
    # Retrieve the comic by its ID
    comic = get_object_or_404(Comic, id=comic_id)

    # Retrieve all issues related to the comic
    issues = Issue.objects.filter(comic_id=comic)

    # Prepare the list of issues
    issue_list = [issue_to_json(issue) for issue in issues]

    # Return the list of issues for the comic
    return Response({"issues": issue_list})


@api_view(["GET"])
def get_pages_by_issue(request, issue_id):
    # Retrieve the issue by its ID
    issue = get_object_or_404(Issue, id=issue_id)

    # Retrieve all pages related to the issue
    pages = Page.objects.filter(issue_id=issue)

    # Prepare the list of pages
    page_list = [page_to_json(page) for page in pages]

    # Return the list of pages for the issue
    return Response({"pages": page_list})


@api_view(["POST"])
def add_comic(request):
    # Ensure the request has valid data (title, link, etc.)
    try:
        data = request.data

        title = data.get("title")
        link = data.get("link")
        date_published = data.get("date_published")
        writers = data.get("writers")
        artists = data.get("artists")
        number_issues = data.get("number_issues")

        # Check that required fields are present
        if not title or not link:
            return Response({"error": "Missing required fields."}, status=400)

        # Create and save the new comic
        comic = Comic.objects.create(
            title=title,
            link=link,
            date_published=date_published,
            writers=writers,
            artists=artists,
            number_issues=number_issues,
        )

        # Return the created comic's data
        return Response(
            {
                "id": comic.id,
                "title": comic.title,
                "link": comic.link,
                "date_published": comic.date_published,
                "writers": comic.writers,
                "artists": comic.artists,
                "number_issues": comic.number_issues,
            },
            status=201,
        )

    except Exception as e:
        # If there was an error with the request, send an error response
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
def search_comics(request):
    title_query = request.GET.get("title", "")

    if not title_query:
        return Response({"error": "No title query provided."}, status=400)

    # Filter comics by the title (case-insensitive search)
    comics = Comic.objects.filter(title__icontains=title_query)

    # Prepare the results to return as JSON
    comic_list = [comic_to_json(comic) for comic in comics]

    return Response({"comics": comic_list})


@api_view(["DELETE"])
def delete_comic(request, comic_id):
    try:
        # Check if the comic exists
        comic = Comic.objects.get(id=comic_id)

        # Delete the comic
        comic.delete()

        return Response({"message": "Comic deleted successfully."}, status=200)

    except Comic.DoesNotExist:
        return Response({"error": "Comic not found."}, status=404)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def update_comic(request, comic_id):
    try:

        # Get data from the request
        data = request.data

        comic = Comic.objects.get(id=comic_id)

        # Update the comic's fields with new data
        comic.title = data.get("title", comic.title)
        comic.link = data.get("link", comic.link)
        comic.date_published = data.get("date_published", comic.date_published)
        comic.writers = data.get("writers", comic.writers)
        comic.artists = data.get("artists", comic.artists)
        comic.number_issues = data.get("number_issues", comic.number_issues)

        # Save the updated comic
        comic.save()

        return Response(
            {
                "id": comic.id,
                "title": comic.title,
                "link": comic.link,
                "date_published": comic.date_published,
                "writers": comic.writers,
                "artists": comic.artists,
                "number_issues": comic.number_issues,
            },
            status=200,
        )

    except Comic.DoesNotExist:
        return Response({"error": "Comic not found."}, status=404)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def create_and_start_download(request):
    data = request.data
    issue_ids = data["issue_ids"]

    steps: List[DownloadJobStep] = []

    downloaded_pages = 0
    total_pages = 0
    total_issues = 0
    complete = False
    try:
        download_job = DownloadJob.objects.create(
            downloaded_pages=downloaded_pages,
            total_pages=total_pages,
            total_issues=total_issues,
            complete=complete,
        )
    except Exception as e:
        # If there was an error with the request, send an error response
        return Response({"error failed to create download job": str(e)}, status=500)

    issue_index = 0

    total_pages = 0

    for issue_id in issue_ids:
        issue = Issue.objects.get(id=issue_id)

        pages = Page.objects.filter(issue_id=issue)

        for page in pages:

            download_job_step = DownloadJobStep.objects.create(
                download_job=download_job,
                page=page,
                image_link=page.image_link,
                page_number=page.page_number,
                issue_index_number=issue_index,
                complete=False,
            )

            total_pages += 1

            steps.append(download_job_step)

        issue_index += 1

    download_job.total_pages = total_pages
    download_job.total_issues = issue_index
    download_job.save()

    create_folders(download_job)
    download_images(download_job, steps)

    # Update the job if no more things to download.
    incomplete_steps = DownloadJobStep.objects.filter(
        download_job_id=download_job.id, complete=False
    )
    if not incomplete_steps:
        download_job.complete = True
        download_job.save()

    return Response(download_job_to_json(download_job), status=200)


@api_view(["POST"])
def retry_download_job(request, job_id):
    download_job = DownloadJob.objects.get(id=job_id)
    incomplete_steps = DownloadJobStep.objects.filter(
        download_job_id=job_id, complete=False
    )

    create_folders(download_job)
    download_images(download_job, incomplete_steps)

    # Update the job if no more things to download.
    incomplete_steps = DownloadJobStep.objects.filter(
        download_job_id=download_job.id, complete=False
    )
    if not incomplete_steps:
        download_job.complete = True
        download_job.save()

    combine(download_job)

    return Response({"message": "ok"}, status=200)


@api_view(["GET"])
def get_all_download_jobs(request):
    incomplete_jobs = DownloadJob.objects.filter(complete=False)
    complete_jobs = DownloadJob.objects.filter(complete=True)

    incomplete_job_list = [download_job_to_json(job) for job in incomplete_jobs]

    complete_job_list = [download_job_to_json(job) for job in complete_jobs]

    return Response(
        {"incomplete": incomplete_job_list, "complete": complete_job_list}, status=200
    )


@api_view(["DELETE"])
def delete_download_job(request, job_id):
    try:
        download_job = get_object_or_404(DownloadJob, id=job_id)

        DownloadJobStep.objects.filter(download_job=download_job).delete()
        recursive_remove_folder(download_job)
        download_job.delete()

        return Response(download_job_to_json(download_job), status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
def delete_completed_download_jobs(request):
    try:
        completed_jobs = DownloadJob.objects.filter(complete=True)

        if not completed_jobs.exists():
            return Response({"message": "No completed jobs."}, status=200)

        DownloadJobStep.objects.filter(download_job__in=completed_jobs).delete()

        for download_job in completed_jobs:
            recursive_remove_folder(download_job)

        completed_jobs.delete()

        return Response(
            {"message": "All completed download jobs deleted successfully."}, status=200
        )

    except Exception as e:
        return Response({"error": str(e)}, status=500)

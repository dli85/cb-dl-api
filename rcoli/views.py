from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from comics.utils import *
from comics.models import Comic, Issue, Page
from crawlers.rcoli import run_spider, InfoPageSpider, crawl_issues
from django.shortcuts import get_object_or_404

from dotenv import load_dotenv
import os

load_dotenv()


@api_view(["POST"])
def add_comics_and_issues(request):
    # Ensure the request has valid data (title, link, etc.)
    data = request.data
    urls = data["urls"]
    try:
        comics = run_spider(urls, InfoPageSpider)
    except Exception as e:
        # If there was an error with the request, send an error response
        return Response({"error": str(e)}, status=500)

    result = []

    for comic in comics:
        try:
            title = comic["title"]
            link = comic["link"]
            writers = comic["writers"]
            artists = comic["artists"]
            date_published = comic["date_published"]
            issues = comic["issues"]
            number_issues = len(issues)
            # Check that required fields are present
            if not title or not link:
                return Response({"error": "Missing required fields."}, status=400)

            # Create and save the new comic
            created_comic = Comic.objects.create(
                title=title,
                link=link,
                date_published=create_date(date_published),
                writers=writers,
                artists=artists,
                number_issues=number_issues,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=403)

        print("comic created")

        for issue in issues:
            try:
                issue_title = issue["issue_title"]
                issue_link = os.getenv("RCOLI_BASE_LINK") + issue["issue_link"]
                pages = 0

                if not issue_title or not issue_link:
                    return Response(
                        {"error": "Issue is missing required fields."}, status=400
                    )

                Issue.objects.create(
                    title=issue_title,
                    link=issue_link,
                    comic_id=created_comic,
                    pages=pages,
                )
            except Exception as e:
                print(issue.link, issue.title)

        result.append(comic_to_json(created_comic))

    return Response(result)


@api_view(["PATCH"])
def add_or_update_comics_and_issues(request):
    data = request.data
    urls = data["urls"]

    try:
        comics = run_spider(urls, InfoPageSpider)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    result = []

    for comic in comics:
        try:
            title = comic["title"]
            link = comic["link"]
            writers = comic.get("writers", "")
            artists = comic.get("artists", "")
            date_published = comic.get("date_published", "")
            issues = comic.get("issues", [])
            number_issues = len(issues)

            if not title or not link:
                return Response({"error": "Missing required fields."}, status=400)

            # Check if the comic already exists
            existing_comic = Comic.objects.filter(link=link).first()

            if existing_comic:
                # Update the existing comic
                existing_comic.title = title
                existing_comic.writers = writers
                existing_comic.artists = artists
                existing_comic.date_published = create_date(date_published)
                existing_comic.number_issues = number_issues
                existing_comic.save()
            else:
                # Create a new comic
                existing_comic = Comic.objects.create(
                    title=title,
                    link=link,
                    date_published=create_date(date_published),
                    writers=writers,
                    artists=artists,
                    number_issues=number_issues,
                )

            for issue in issues:
                issue_title = issue["issue_title"]
                issue_link = os.getenv("RCOLI_BASE_LINK") + issue["issue_link"]
                pages = 0

                if not issue_title or not issue_link:
                    return Response(
                        {"error": "Issue is missing required fields."}, status=400
                    )

                # Check if the issue already exists
                existing_issue = Issue.objects.filter(
                    link=issue_link, comic_id=existing_comic
                ).first()

                if existing_issue:
                    existing_issue.title = issue_title
                    existing_issue.pages = pages
                    existing_issue.save()
                else:
                    Issue.objects.create(
                        title=issue_title,
                        link=issue_link,
                        comic_id=existing_comic,
                        pages=pages,
                    )

            result.append(comic_to_json(existing_comic))
        except Exception as e:
            return Response({"error": str(e)}, status=403)

    return Response(result)


def process_add_pages_for_issues(issue_requests):
    workload = []
    for issue_request in issue_requests:
        issue_id = issue_request["id"]
        high_quality = issue_request["high_quality"]
        issue = get_object_or_404(Issue, id=issue_id)
        link = issue.link + "&s=&readType=1"
        if high_quality:
            link = link + "&s=&quality=hq"
        else:
            link = link + "&s=&quality=lq"

        workload.append({"issue_id": issue.id, "link": link})

    successes, failures = crawl_issues(workload)

    for success in successes:

        issue_id = success["issue_id"]
        pages = success["pages"]
        num_pages = len(pages)

        issue = Issue.objects.get(id=issue_id)

        # update number of pages
        issue.pages = num_pages
        try:
            issue.save()

            # delete all existing pages with the issue id
            Page.objects.filter(issue_id=issue_id).delete()

            for page in pages:
                page_number = page["page"]
                image_link = page["link"]
                title = issue.title

                Page.objects.create(
                    issue_id=issue,
                    page_number=page_number,
                    title=title,
                    image_link=image_link,
                )
        except Exception as e:
            print(e)
            failures.append({"issue_id": success["issue_id"], "link": success["link"]})

    return successes, failures


@api_view(["POST"])
def add_pages(request):
    data = request.data
    issue_requests = data["issue_requests"]

    successes, failures = process_add_pages_for_issues(issue_requests)

    return Response(
        {
            "successes": [
                {"issue_id": cur_issue["issue_id"], "link": cur_issue["link"]}
                for cur_issue in successes
            ],
            "failures": [
                {"issue_id": cur_issue["issue_id"], "link": cur_issue["link"]}
                for cur_issue in failures
            ],
        }
    )


@api_view(["POST"])
def add_pages_missing_issues(request):
    """
    Add pages for all issues whose pages haven't been added (check by pagecount = 0)
    """
    data = request.data
    issue_requests = data["issue_requests"]

    missing_issues = [
        issue_request
        for issue_request in issue_requests
        if Issue.objects.filter(id=issue_request["id"], pages=0).exists()
    ]

    successes, failures = process_add_pages_for_issues(missing_issues)

    return Response(
        {
            "successes": [
                {"issue_id": cur_issue["issue_id"], "link": cur_issue["link"]}
                for cur_issue in successes
            ],
            "failures": [
                {"issue_id": cur_issue["issue_id"], "link": cur_issue["link"]}
                for cur_issue in failures
            ],
        }
    )

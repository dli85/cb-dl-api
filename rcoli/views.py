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
        return Response({"crawler error": str(e)}, status=500)

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
            result.append(
                {
                    "error": "An issue was encountered while adding a comic to db: "
                    + str(e),
                    "link": link,
                }
            )
            continue

        print("comic created")

        for issue in issues:
            issue_title = issue["issue_title"]
            issue_link = os.getenv("RCOLI_BASE_LINK") + issue["issue_link"]
            pages = 0

            if not issue_title or not issue_link:
                return Response(
                    {"error": "Issue is missing required fields."}, status=400
                )

            Issue.objects.create(
                title=issue_title, link=issue_link, comic_id=created_comic, pages=pages
            )

        result.append(comic_to_json(created_comic))

    return Response(result)


@api_view(["POST"])
def add_pages(request):
    data = request.data
    issue_requests = data["issue_requests"]

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

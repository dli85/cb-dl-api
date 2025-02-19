from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from comics.utils import *
from comics.models import Comic, Issue
from crawlers.rcoli import run_spider, InfoPageSpider

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

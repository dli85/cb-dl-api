from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .utils import *
from .models import Comic
import json


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
    title_query = request.GET.get("title", "")  # Get the 'title' parameter from the request URL

    if not title_query:
        return Response({"error": "No title query provided."}, status=400)

    # Filter comics by the title (case-insensitive search)
    comics = Comic.objects.filter(title__icontains=title_query)

    # Prepare the results to return as JSON
    comic_list = [
        comic_to_json(comic)
        for comic in comics
    ]

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

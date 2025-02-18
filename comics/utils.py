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
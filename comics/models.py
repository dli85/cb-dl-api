from django.db import models


class Comic(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    date_published = models.DateField()
    link = models.URLField(unique=True, null=False, blank=False)
    writers = models.CharField(max_length=255)
    artists = models.CharField(max_length=255)
    number_issues = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Issue(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField(unique=True, null=False, blank=False)
    comic_id = models.ForeignKey(Comic, on_delete=models.CASCADE, related_name="issues")
    pages = models.IntegerField()

    def __str__(self):
        return self.title


class Page(models.Model):
    issue_id = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="pages_in_issue"
    )  # Unique related_name
    page_number = models.IntegerField()
    title = models.CharField(max_length=255, null=False, blank=False)
    image_link = models.URLField(unique=True, max_length=500, null=False, blank=False)

    def __str__(self):
        return self.title


class DownloadJob(models.Model):
    # downloadjob id used as folder name
    downloaded_pages = models.IntegerField()
    total_pages = models.IntegerField()
    total_issues = models.IntegerField()
    complete = models.BooleanField()
    name = models.CharField(max_length=255, null=False, blank=False)

class DownloadJobStep(models.Model):
    download_job = models.ForeignKey(
        DownloadJob, on_delete=models.CASCADE, related_name="download_job_steps"
    )
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="download_job_steps"
    )
    image_link = models.URLField(max_length=500, null=False, blank=False)
    page_number = models.IntegerField()
    # issue_index_number used as issue folder name
    issue_index_number = models.IntegerField()
    complete = models.BooleanField()
    issue_link = models.URLField(unique=True, null=False, blank=False)
    retry = models.BooleanField()

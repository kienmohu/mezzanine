from django.db import models
from django.utils.translation import ugettext_lazy as _

from mezzanine.conf import settings
from mezzanine.core.fields import FileField
from mezzanine.core.models import Displayable, Ownable, RichText, Slugged
from mezzanine.generic.fields import CommentsField, RatingField
from mezzanine.utils.models import AdminThumbMixin
from pyquery import PyQuery as pq
import os


class BlogPost(Displayable, Ownable, RichText, AdminThumbMixin):
    """
    A blog post.
    """

    categories = models.ManyToManyField("BlogCategory",
                                        verbose_name=_("Categories"),
                                        blank=True, related_name="blogposts")
    allow_comments = models.BooleanField(verbose_name=_("Allow comments"),
                                         default=True)
    comments = CommentsField(verbose_name=_("Comments"))
    rating = RatingField(verbose_name=_("Rating"))
    featured_image = FileField(verbose_name=_("Featured Image"),
                               upload_to="blog", format="Image",
                               max_length=255, null=True, blank=True,
                               help_text='Choose a feature image or one will' +
                            ' be chosen from the first local ' +
                            'img in the content field')
    related_posts = models.ManyToManyField("self",
                                 verbose_name=_("Related posts"), blank=True)

    admin_thumb_field = "featured_image"

    country = models.ForeignKey("Country", null=True, blank=True)

    class Meta:
        verbose_name = _("General post")
        verbose_name_plural = _("General posts")
        ordering = ("-publish_date",)
        get_latest_by = "publish_date"

    def save(self, *args, **kwargs):
        if not self.featured_image:
            # Try to use image from content field
            pq_content = pq(self.content)
            pq_imgs = pq_content.find('img')
            if pq_imgs.size():
                for index in range(0, pq_imgs.size()):
                    img = pq_imgs.eq(index)
                    src = img.attr('src')
                    if src.startswith(settings.MEDIA_URL):
                        name = src[len(settings.MEDIA_URL):]
                        if os.path.exists(settings.MEDIA_ROOT + os.path.sep + name):
                            self.featured_image = name
                            break
        return super(BlogPost, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        url_name = "blog_post_detail"
        kwargs = {"slug": self.slug}
        if settings.BLOG_URLS_USE_DATE:
            url_name = "blog_post_detail_date"
            month = str(self.publish_date.month)
            if len(month) == 1:
                month = "0" + month
            day = str(self.publish_date.day)
            if len(day) == 1:
                day = "0" + day
            kwargs.update({
                "day": day,
                "month": month,
                "year": self.publish_date.year,
            })
        return (url_name, (), kwargs)

    # These methods are wrappers for keyword and category access.
    # For Django 1.3, we manually assign keywords and categories
    # in the blog_post_list view, since we can't use Django 1.4's
    # prefetch_related method. Once we drop support for Django 1.3,
    # these can probably be removed.

    def category_list(self):
        return getattr(self, "_categories", self.categories.all())

    def keyword_list(self):
        try:
            return self._keywords
        except AttributeError:
            keywords = [k.keyword for k in self.keywords.all()]
            setattr(self, "_keywords", keywords)
            return self._keywords


class BlogCategory(Slugged):
    """
    A category for grouping blog posts into a series.
    """

    # This is made just for the project section of procor

    SECTION_KNOWLEDGE_TUPLE = ('knowledge', 'Knowledge')
    SECTION_ACTION_TUPLE = ('action', 'Action')
    SECTION_GLOBAL_TUPLE = ('global community', 'Global Community')

    PROCOR_PROJECT_SECTION_TUPLE = [
        SECTION_KNOWLEDGE_TUPLE,
        SECTION_ACTION_TUPLE,
        SECTION_GLOBAL_TUPLE,
    ]

    project_section = models.CharField(max_length=50, null=True, blank=True,
            choices=PROCOR_PROJECT_SECTION_TUPLE,
            help_text='This will relate this category to a project section.')

    class Meta:
        verbose_name = _("Post Category")
        verbose_name_plural = _("Post Categories")

    @models.permalink
    def get_absolute_url(self):
        return ("blog_post_list_category", (), {"category": self.slug})


class Region(models.Model):
    name = models.CharField(max_length=50)


class Country(models.Model):
    name = models.CharField(max_length=80)
    region = models.ForeignKey(Region)
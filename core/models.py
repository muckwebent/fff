from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models.signals import post_save
from django.utils.html import mark_safe
from PIL import Image
from shortuuid.django_fields import ShortUUIDField
import shortuuid
RELATIONSHIP = (
    ("student", "Student"),
    ("parent", "Parent"),
    ("oldstudent", "Old Student"),
)

GENDER = (
    ("female", "Female"),
    ("male", "Male"),
)

WHO_CAN_SEE_MY_FRIENDS = (
    ("Only Me", "Only Me"),
    ("Everyone", "Everyone"),
)


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.user.id, ext)
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class User(AbstractUser):
    full_name = models.CharField(max_length=1000, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GENDER, null=True, blank=True)

    otp = models.CharField(max_length=100, null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name='core_user_set',  # Changed related_name to avoid clash
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='core_user_set_permissions',  # Changed related_name to avoid clash
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return str(self.username)


class Profile(models.Model):
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_directory_path, default="default.jpg", null=True, blank=True)
    full_name = models.CharField(max_length=1000, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GENDER, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=1000, null=True, blank=True)
    working_at = models.CharField(max_length=1000, null=True, blank=True)

    verified = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        if self.full_name:
            return str(self.full_name)
        else:
            return str(self.user.username)

    def thumbnail(self):
        return mark_safe(
            '<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 30px;" />' % (
                self.image))


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)


class HomeFeatures(models.Model):
    title = models.CharField(max_length=50)
    details = models.CharField(max_length=700)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Testimonials(models.Model):
    image = models.ImageField(upload_to='media')
    name = models.CharField(max_length=30)
    post = models.CharField(max_length=15)
    testimony = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=500, blank=True ,null=True)
    caption = models.CharField(max_length=1000, blank=True, null=True)
    image = models.FileField(upload_to=user_directory_path, null=True, blank=True)
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    likes = models.ManyToManyField(User, blank=True, related_name="likes")
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)
    views = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Post"

    def save(self, *args, **kwargs):
        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:4]
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) + "-" + str(uniqueid.lower())
        super(Post, self).save(*args, **kwargs)

    def thumbnail(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 5px;" />' % (self.image))

    def gallery_images(self):
        return Gallery.objects.filter(post=self)

    def title_len_count(self):
        return len(self.title)

    def galley_img_count(self):
        return Gallery.objects.filter(post=self).count()

    def post_comments(self):
        comments = Comment.objects.filter(post=self, active=True)
        return comments

    def post_comments_count(self):
        comments_count = Comment.objects.filter(post=self, active=True).count()
        return comments_count

class Gallery(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to="gallery", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.post)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Gallery"

    def thumbnail(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 30px;" />' % (self.image))

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
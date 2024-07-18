from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.models import User, Profile, Subscriber
from core.forms import UserRegisterForm, UserUpdateForm, SubscribeForm
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import send_mail


@login_required
def post_detail(request, slug):
    post = Post.objects.get(active=True, visibility="Everyone", slug=slug)
    context = {
        "p": post
    }
    return render(request, "core/post-detail.html", context)


def send_notification(user, sender, post, comment, notification_type):
    notification = Notification.objects.create(
        user=user,
        sender=sender,
        post=post,
        comment=comment,
        notification_type=notification_type
    )
    return notification


@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('post-caption')
        visibility = request.POST.get('visibility')
        image = request.FILES.get('post-thumbnail')

        print("Title ============", title)
        print("thumbnail ============", image)
        print("visibility ============", visibility)

        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:4]

        if title and image:
            post = Post(title=title, image=image, visibility=visibility, user=request.user,
                        slug=slugify(title) + "-" + str(uniqueid.lower()))
            post.save()

            return JsonResponse({'post': {
                'title': post.title,
                'image_url': post.image.url,
                "full_name": post.user.profile.full_name,
                "profile_image": post.user.profile.image.url,
                "date": timesince(post.date),
                "id": post.id,
            }})
        else:
            return JsonResponse({'error': 'Invalid post data'})

    return JsonResponse({"data": "Sent"})


@csrf_exempt
def like_post(request):
    id = request.GET['id']
    post = Post.objects.get(id=id)
    user = request.user
    bool = False

    if user in post.likes.all():
        post.likes.remove(user)
        bool = False
    else:
        post.likes.add(user)
        bool = True
        # Do this during noticiation lecture
        if post.user != request.user:
            send_notification(post.user, user, post, None, noti_new_like)

    data = {
        "bool": bool,
        'likes': post.likes.all().count()
    }
    return JsonResponse({"data": data})


@csrf_exempt
def comment_on_post(request):
    id = request.GET['id']
    comment = request.GET['comment']
    post = Post.objects.get(id=id)
    comment_count = Comment.objects.filter(post=post).count()
    user = request.user

    new_comment = Comment.objects.create(
        post=post,
        comment=comment,
        user=user
    )

    # Notifications system
    if new_comment.user != post.user:
        send_notification(post.user, user, post, new_comment, noti_new_comment)

    data = {
        "bool": True,
        'comment': new_comment.comment,
        "profile_image": new_comment.user.profile.image.url,
        "date": timesince(new_comment.date),
        "comment_id": new_comment.id,
        "post_id": new_comment.post.id,
        "comment_count": comment_count + int(1)
    }
    return JsonResponse({"data": data})


@csrf_exempt
def like_comment(request):
    id = request.GET['id']
    comment = Comment.objects.get(id=id)
    user = request.user
    bool = False

    if user in comment.likes.all():
        comment.likes.remove(user)
        bool = False
    else:
        comment.likes.add(user)
        bool = True

        # Notifications system
        if comment.user != user:
            send_notification(comment.user, user, comment.post, comment, noti_comment_liked)

    data = {
        "bool": bool,
        'likes': comment.likes.all().count()
    }
    return JsonResponse({"data": data})


@csrf_exempt
def reply_comment(request):
    id = request.GET['id']
    reply = request.GET['reply']

    comment = Comment.objects.get(id=id)
    user = request.user

    new_reply = ReplyComment.objects.create(
        comment=comment,
        reply=reply,
        user=user
    )

    # Notifications system
    if comment.user != user:
        send_notification(comment.user, user, comment.post, comment, noti_comment_replied)

    data = {
        "bool": True,
        'reply': new_reply.reply,
        "profile_image": new_reply.user.profile.image.url,
        "date": timesince(new_reply.date),
        "reply_id": new_reply.id,
        "post_id": new_reply.comment.post.id,
    }
    return JsonResponse({"data": data})


@csrf_exempt
def delete_comment(request):
    id = request.GET['id']

    comment = Comment.objects.get(id=id, user=request.user)
    comment.delete()

    data = {
        "bool": True,
    }
    return JsonResponse({"data": data})


def subscribe(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            form.save()
            send_mail(
                'Welcome to First Fruit Family Fund',
                'Thank you for subscribing to our newsletter. Stay motivated!',
                settings.EMAIL_HOST_USER,
                [form.cleaned_data['email']],
                fail_silently=False,
            )
            messages.success(request, 'Subscription successful! Check your email for a welcome message.')
            return redirect('thank_you')
        else:
            messages.error(request, 'Subscription failed. Please check the email you entered.')
    else:
        form = SubscribeForm()
    return render(request, 'index.html', {'form': form})



def RegisterView(request, *args, **kwargs):
    if request.user.is_authenticated:
        messages.warning(request, f"Hey {request.user.username}, you are already logged in")
        return render(request, 'userauths/sign-up.html')

    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        form.save()
        full_name = form.cleaned_data.get('full_name')
        phone = form.cleaned_data.get('phone')
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')

        user = authenticate(email=email, password=password)
        login(request, user)

        messages.success(request, f"Hi {request.user.username}, your account have been created successfully.")

        profile = Profile.objects.get(user=request.user)
        profile.full_name = full_name
        profile.phone = phone
        profile.save()

        return redirect('core/index')

    context = {'form': form}
    return render(request, 'userauths/sign-up.html', context)


def LoginView(request):
    # if request.user.is_authenticated:
    #     return redirect('core:feed')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "You are Logged In")
                return redirect('core/index')
            else:
                messages.error(request, 'Username or password does not exit.')

        except:
            messages.error(request, 'User does not exist')

    return HttpResponseRedirect("/")


def LogoutView(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return render(request,'userauths/sign-up.html')


@login_required
def my_profile(request):
    profile = request.user.profile
    posts = Post.objects.filter(active=True, user=request.user)

    context = {
        "posts": posts,
        "profile": profile,
    }
    return render(request, "userauths/my-profile.html", context)




@login_required
def profile_update(request):
    if request.method == "POST":
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)

        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect('userauths:profile-update')
    else:
        p_form = ProfileUpdateForm(instance=request.user.profile)
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'p_form': p_form,
        'u_form': u_form,
    }
    return render(request, 'userauths/profile-update.html', context)



from .models import HomeFeatures, Testimonials
# Create your views here.
def index(res):
    features = HomeFeatures.objects.all()
    context = {
        'features': features
    }
    return render(res,'index.html', context)

def about(res):
    testimony = Testimonials.objects.all()
    context = {
        "testimony":testimony
    }
    return render(res, 'about.html', context)

def blog(res):
    return render(res, 'blog.html')
def blog_details(res):
    return render(res, 'blog-details.html')
def contact(res):
    return render(res, 'contact.html')
def portfolio(res):
    return render(res, 'portfolio.html')
def pricing(res):
    return render(res, 'pricing.html')
def service(res):
    return render(res, 'services.html')
def team(res):
    return render(res, 'team.html')
def testimonial(res):
    return render(res, 'testimonial.html')


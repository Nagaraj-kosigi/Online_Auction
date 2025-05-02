# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max, Count, Q
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Auction, Bid, Category, UserProfile, get_default_end_date
from .forms import AuctionForm, BidForm, UserProfileForm, CustomUserCreationForm, CustomPasswordResetForm, OTPVerificationForm, ChangePasswordForm
from django.core.management.base import BaseCommand
from auctions.models import Auction
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
import uuid


import random
import logging
from datetime import timedelta

def generate_otp():
    # Generate a 6-digit OTP
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile with OTP
            profile = UserProfile.objects.create(user=user)
            otp = generate_otp()
            profile.email_verification_otp = otp
            profile.otp_expiry = timezone.now() + timedelta(minutes=15)  # OTP valid for 15 minutes
            profile.save()

            # Send OTP email
            subject = 'Your Email Verification OTP'
            html_message = render_to_string('registration/otp_email.html', {
                'user': user,
                'otp': otp,
                'expiry_minutes': 15,
            })
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Store user_id in session to identify the user during verification
            request.session['verification_user_id'] = user.id

            messages.success(request, f"Account created for {user.username}! Please check your email for the OTP to verify your account.")

            # No longer showing OTP in messages

            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_otp(request):
    # Check if user is in verification process
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, "Verification session expired. Please register again.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "User not found. Please register again.")
        return redirect('register')

    if profile.email_verified:
        messages.info(request, "Your email is already verified. Please login.")
        return redirect('login')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']

            if not profile.is_otp_valid():
                messages.error(request, "OTP has expired. Please request a new one.")
                return render(request, 'registration/verify_otp.html', {
                    'form': form,
                    'resend': True,
                    'email': user.email
                })

            if entered_otp == profile.email_verification_otp:
                profile.email_verified = True
                profile.email_verification_otp = None  # Clear OTP after successful verification
                profile.otp_expiry = None
                profile.save()

                # Clear verification session
                if 'verification_user_id' in request.session:
                    del request.session['verification_user_id']

                messages.success(request, "Your email has been verified successfully! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        # If form is invalid, it will be rendered again with errors
    else:
        form = OTPVerificationForm()

    return render(request, 'registration/verify_otp.html', {
        'form': form,
        'resend': False,
        'email': user.email
    })

def resend_otp(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, "Verification session expired. Please register again.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "User not found. Please register again.")
        return redirect('register')

    # Generate new OTP
    otp = generate_otp()
    profile.email_verification_otp = otp
    profile.otp_expiry = timezone.now() + timedelta(minutes=15)  # OTP valid for 15 minutes
    profile.save()

    # Send new OTP email
    subject = 'Your New Email Verification OTP'
    html_message = render_to_string('registration/otp_email.html', {
        'user': user,
        'otp': otp,
        'expiry_minutes': 15,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email.")

    # No longer showing OTP in messages

    return redirect('verify_otp')

def forgot_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    # Generate password reset token
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    # Build reset URL
                    reset_url = request.build_absolute_uri(
                        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                    )

                    # Send email
                    subject = 'Password Reset Request'
                    html_message = render_to_string('registration/password_reset_email.html', {
                        'user': user,
                        'reset_url': reset_url,
                    })
                    plain_message = strip_tags(html_message)

                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                messages.success(request, "Password reset link has been sent to your email.")
                return redirect('login')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'registration/password_reset_form.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Check if user is admin or staff
                if user.is_superuser or user.is_staff:
                    # Redirect to admin panel
                    return HttpResponseRedirect(reverse('admin:index'))
                else:
                    # Redirect to auction UI
                    next_url = request.POST.get('next', '')
                    if next_url:
                        return HttpResponseRedirect(next_url)
                    else:
                        return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    # Get the next URL if provided
    next_url = request.GET.get('next', '')

    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url
    })

def user_logout(request):
    auth_logout(request)
    return redirect('index')

def index(request):
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    search_query = request.GET.get('search')

    auctions = Auction.objects.filter(is_active=True, end_date__gt=timezone.now())

    if category_id:
        auctions = auctions.filter(category_id=category_id)

    if search_query:
        auctions = auctions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    auctions = auctions.annotate(bid_count=Count('bids'))

    # Sorting
    sort_by = request.GET.get('sort', 'end_date')
    if sort_by == 'end_date':
        auctions = auctions.order_by('end_date')
    elif sort_by == 'price_low':
        auctions = auctions.order_by('current_price')
    elif sort_by == 'price_high':
        auctions = auctions.order_by('-current_price')
    elif sort_by == 'newest':
        auctions = auctions.order_by('-start_date')

    paginator = Paginator(auctions, 12)  # Show 12 auctions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'auctions/index.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by
    })

def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    bids = auction.bids.filter(status='active').order_by('-bid_time')[:10]
    bid_form = BidForm(auction=auction, user=request.user if request.user.is_authenticated else None)

    if request.method == 'POST' and request.user.is_authenticated:
        bid_form = BidForm(request.POST, auction=auction, user=request.user)
        if bid_form.is_valid():
            bid = bid_form.save(commit=False)
            bid.auction = auction
            bid.bidder = request.user
            bid.save()

            # Update auction current price
            auction.current_price = bid.amount
            auction.save()

            messages.success(request, "Your bid has been placed successfully!")
            return redirect('auction_detail', auction_id=auction.id)

    # Check if auction has ended but winner not determined yet
    if auction.has_ended and auction.is_active:
        highest_bid = auction.bids.filter(status='active').order_by('-amount').first()
        if highest_bid:
            auction.winner = highest_bid.bidder
            auction.is_active = False
            auction.save()

    return render(request, 'auctions/auction_detail.html', {
        'auction': auction,
        'bids': bids,
        'bid_form': bid_form,
    })

@login_required
def create_auction(request):
    # Set up logging
    logger = logging.getLogger('auctions')

    if request.method == 'POST':
        form = AuctionForm(request.POST, request.FILES)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.created_by = request.user
            auction.current_price = auction.starting_price

            # Handle image upload
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Log image details for debugging
                logger.debug(f"Image upload: {image_file.name}, size: {image_file.size}, content_type: {image_file.content_type}")

                # Ensure the image is properly saved
                auction.image = image_file

            # Save the auction
            auction.save()

            # Format end date for display in the success message
            end_date_formatted = auction.end_date.strftime('%B %d, %Y at %I:%M %p')

            # Check if image was saved correctly
            if auction.image:
                try:
                    image_url = auction.image.url
                    logger.debug(f"Image saved successfully. URL: {image_url}")
                    messages.success(request, f"Your auction has been created successfully with image! It will end on {end_date_formatted}.")
                except Exception as e:
                    logger.error(f"Error getting image URL: {e}")
                    messages.success(request, f"Your auction has been created successfully, but there might be an issue with the image. It will end on {end_date_formatted}.")
            else:
                logger.warning(f"No image was saved for auction {auction.id}")
                messages.success(request, f"Your auction has been created successfully! It will end on {end_date_formatted}.")

            return redirect('auction_detail', auction_id=auction.id)
        else:
            # Log form errors
            logger.warning(f"Form validation errors: {form.errors}")
    else:
        # Initialize form with default values
        form = AuctionForm(initial={
            'end_date': get_default_end_date().strftime('%Y-%m-%dT%H:%M'),
        })

    # Calculate min and max dates for template context
    min_date = timezone.now() + timedelta(hours=1)
    max_date = timezone.now() + timedelta(days=30)

    return render(request, 'auctions/create_auction.html', {
        'form': form,
        'min_date': min_date.strftime('%Y-%m-%dT%H:%M'),
        'max_date': max_date.strftime('%Y-%m-%dT%H:%M'),
    })

@login_required
def my_auctions(request):
    user_auctions = Auction.objects.filter(created_by=request.user).order_by('-start_date')
    won_auctions = Auction.objects.filter(winner=request.user, is_active=False)
    active_bids = Bid.objects.filter(
        bidder=request.user,
        status='active',
        auction__is_active=True
    ).values('auction').annotate(
        max_bid=Max('amount')
    ).order_by('-max_bid')

    active_bid_auctions = []
    for bid in active_bids:
        auction = Auction.objects.get(pk=bid['auction'])
        is_highest = auction.current_price == bid['max_bid']
        active_bid_auctions.append({
            'auction': auction,
            'max_bid': bid['max_bid'],
            'is_highest': is_highest
        })

    return render(request, 'auctions/my_auctions.html', {
        'user_auctions': user_auctions,
        'won_auctions': won_auctions,
        'active_bid_auctions': active_bid_auctions
    })

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
        profile.save()

    # Handle profile form
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
        password_form = ChangePasswordForm(request.user)
    # Handle password form
    elif request.method == 'POST' and 'change_password' in request.POST:
        password_form = ChangePasswordForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            # Update session auth hash to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully!")
            return redirect('profile')
        profile_form = UserProfileForm(instance=profile)
    else:
        profile_form = UserProfileForm(instance=profile)
        password_form = ChangePasswordForm(request.user)

    return render(request, 'auctions/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'profile': profile
    })

def end_expired_auctions():
    """End auctions that have passed their end date"""
    expired_auctions = Auction.objects.filter(
        is_active=True,
        end_date__lt=timezone.now()
    )

    for auction in expired_auctions:
        highest_bid = auction.bids.filter(status='active').order_by('-amount').first()
        if highest_bid:
            auction.winner = highest_bid.bidder
        auction.is_active = False
        auction.save()

    return len(expired_auctions)

@login_required
def edit_auction(request, auction_id):
    # Set up logging
    logger = logging.getLogger('auctions')

    auction = get_object_or_404(Auction, id=auction_id, created_by=request.user)

    if not auction.is_active:
        return HttpResponseForbidden("You can't edit an inactive or ended auction.")

    # Check if auction has bids - if so, restrict end date changes
    has_bids = auction.bids.filter(status='active').exists()

    if request.method == 'POST':
        form = AuctionForm(request.POST, request.FILES, instance=auction)

        # If auction has bids, only allow extending the end date, not shortening it
        if has_bids and 'end_date' in form.cleaned_data:
            new_end_date = form.cleaned_data['end_date']
            if new_end_date < auction.end_date:
                form.add_error('end_date', "You cannot shorten the auction duration once bids have been placed.")

        if form.is_valid():
            updated_auction = form.save(commit=False)

            # Handle image upload
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Log image details for debugging
                logger.debug(f"Image upload during edit: {image_file.name}, size: {image_file.size}, content_type: {image_file.content_type}")

                # Ensure the image is properly saved
                updated_auction.image = image_file

            # Save the auction
            updated_auction.save()

            # Format end date for display in the success message
            end_date_formatted = updated_auction.end_date.strftime('%B %d, %Y at %I:%M %p')

            # Check if image was saved correctly
            if updated_auction.image:
                try:
                    image_url = updated_auction.image.url
                    logger.debug(f"Image saved successfully during edit. URL: {image_url}")
                    messages.success(request, f"Auction updated successfully with image! It will end on {end_date_formatted}.")
                except Exception as e:
                    logger.error(f"Error getting image URL during edit: {e}")
                    messages.success(request, f"Auction updated successfully, but there might be an issue with the image. It will end on {end_date_formatted}.")
            else:
                messages.success(request, f"Auction updated successfully! It will end on {end_date_formatted}.")

            return redirect('my_auctions')
    else:
        # Format the datetime for the datetime-local input
        initial_data = {}
        if auction.end_date:
            initial_data['end_date'] = auction.end_date.strftime('%Y-%m-%dT%H:%M')

        form = AuctionForm(instance=auction, initial=initial_data)

        # If auction has bids, add a note about end date restrictions
        if has_bids:
            form.fields['end_date'].help_text += " Note: You can only extend the end date, not shorten it, because bids have been placed."

    # Calculate min and max dates for template context
    min_date = timezone.now() + timedelta(hours=1)
    max_date = timezone.now() + timedelta(days=30)

    return render(request, 'auctions/edit_auction.html', {
        'form': form,
        'auction': auction,
        'has_bids': has_bids,
        'min_date': min_date.strftime('%Y-%m-%dT%H:%M'),
        'max_date': max_date.strftime('%Y-%m-%dT%H:%M'),
    })

@require_POST
@login_required
def delete_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, created_by=request.user)

    if auction.is_active and not auction.has_ended:
        auction.delete()
        messages.success(request, "Auction cancelled successfully.")
    else:
        messages.error(request, "Cannot cancel an ended or inactive auction.")

    return redirect('my_auctions')

@login_required
def my_bids(request):
    active_bids = Bid.objects.filter(
        bidder=request.user,
        status='active',
        auction__is_active=True,
        auction__end_date__gt=timezone.now()
    ).order_by('-bid_time')

    cancelled_bids = Bid.objects.filter(
        bidder=request.user,
        status='cancelled'
    ).order_by('-bid_time')



    return render(request, 'auctions/my_bids.html', {
        'active_bids': active_bids,
        'cancelled_bids': cancelled_bids
    })

@require_POST
@login_required
def cancel_bid(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id, bidder=request.user)
    auction = bid.auction

    # Check if auction is still active and not ended
    if not auction.is_active or auction.has_ended:
        messages.error(request, "Cannot cancel bid on an ended or inactive auction.")
        return redirect('my_bids')

    # Check if this is the highest bid
    highest_bid = auction.bids.filter(status='active').order_by('-amount').first()

    if highest_bid and highest_bid.id == bid.id:
        # This is the highest bid, find the next highest bid
        next_highest_bid = auction.bids.filter(status='active').exclude(id=bid.id).order_by('-amount').first()

        if next_highest_bid:
            # Update auction current price to next highest bid
            auction.current_price = next_highest_bid.amount
        else:
            # No other bids, revert to starting price
            auction.current_price = auction.starting_price

        auction.save()

    # Mark bid as cancelled
    bid.status = 'cancelled'
    bid.save()

    messages.success(request, "Bid cancelled successfully.")
    return redirect('my_bids')



@login_required
def delete_account(request):
    user = request.user

    if request.method == 'POST':
        password = request.POST.get('password')

        # Verify password
        if user.check_password(password):
            # Log the user out
            auth_logout(request)

            # Delete the user account
            user.delete()

            messages.success(request, "Your account has been deleted successfully.")
            return redirect('index')
        else:
            messages.error(request, "Incorrect password. Account deletion cancelled.")

    return render(request, 'auctions/delete_account.html')
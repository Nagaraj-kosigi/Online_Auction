# urls.py (auctions app)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('accounts/login/', views.custom_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('auctions/<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('auctions/create/', views.create_auction, name='create_auction'),
    path('my-auctions/', views.my_auctions, name='my_auctions'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('bids/<int:bid_id>/cancel/', views.cancel_bid, name='cancel_bid'),

    path('profile/', views.profile, name='profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('auctions/<int:auction_id>/edit/', views.edit_auction, name='edit_auction'),
    path('auctions/<int:auction_id>/delete/', views.delete_auction, name='delete_auction'),
]
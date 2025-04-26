# Online Auction System with Fraud Detection

A comprehensive online auction platform built with Django, featuring real-time bidding, user authentication, and an advanced fraud detection system powered by machine learning.

## Features

### User Management
- User registration with email verification
- Secure login and authentication
- Profile management
- Password reset functionality

### Auction Management
- Create and manage auctions
- Upload product images
- Set starting prices and auction duration
- Browse auctions by category
- Search functionality

### Bidding System
- Place bids on active auctions
- Automatic bid validation
- Bid cancellation
- Bid scheduling

### Fraud Detection
- ML-powered fraud detection system
- Risk scoring for auctions
- Admin dashboard for fraud management
- User reporting system for suspicious auctions

### Admin Features
- Custom admin panels
- Fraud management dashboard
- User and auction management
- System statistics and reporting

## Technology Stack

- **Backend**: Django 5.x
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5, JavaScript
- **Machine Learning**: scikit-learn, NumPy
- **Authentication**: Django's built-in auth with custom extensions
- **Email**: SMTP integration for real emails

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/online-auction-system.git
cd online-auction-system
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Create a superuser
```bash
python manage.py createsuperuser
```

6. Run the development server
```bash
python manage.py runserver
```

## Usage

1. Access the application at http://localhost:8000
2. Register a new account or login
3. Browse available auctions or create your own
4. Place bids on items you're interested in
5. Admin interface is available at http://localhost:8000/admin

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive design components
- scikit-learn for the machine learning capabilities

# HandCraft - Handmade Goods Marketplace

A full-stack marketplace platform connecting artisans and crafters with customers seeking unique, handmade goods. Built with Django REST Framework and Next.js.

---

## Table of Contents

1. [Project Description](#project-description)
2. [Goal](#goal)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Tech Stack](#tech-stack)
6. [Folder Structure](#folder-structure)
7. [Setup and Installation](#setup-and-installation)
8. [API Documentation](#api-documentation)
9. [User Roles](#user-roles)
10. [Business Logic](#business-logic)
11. [Roadmap](#roadmap)

---

## Project Description

HandCraft is an Etsy-like marketplace that empowers independent artisans and crafters to showcase and sell their handmade products to a global audience. The platform supports custom orders, real-time messaging between buyers and sellers, reviews and ratings, wishlists, and comprehensive artisan profiles with portfolio galleries.

The application is designed with scalability, security, and performance in mind -- leveraging Elasticsearch for product discovery, Redis for caching and real-time features, Celery for background task processing, and AWS S3 for media storage.

---

## Goal

To build a production-grade, horizontally scalable marketplace that:

- Provides artisans with powerful tools to manage their shops, products, and orders.
- Offers customers a seamless shopping experience with rich search, filtering, and discovery.
- Facilitates direct communication between buyers and sellers for custom orders.
- Maintains high code quality, test coverage, and deployment reliability through containerization.

---

## Features

### Customer Features
- Browse and search handmade products with full-text search (Elasticsearch).
- Filter by category, price range, tags, artisan location, and shipping options.
- Add products to cart and complete checkout with order tracking.
- Submit custom order requests directly to artisans.
- Leave reviews and ratings on purchased products.
- Maintain wishlists and follow favorite shops.
- Direct messaging with artisans.

### Artisan Features
- Create and manage an artisan profile with bio, avatar, and portfolio.
- List products with multiple images, variants, and pricing.
- Manage incoming orders and update order status.
- Accept or decline custom order requests with quoting.
- View shop analytics and sales dashboard.
- Respond to customer reviews.

### Platform Features
- JWT-based authentication with token refresh.
- Role-based access control (Customer, Artisan, Admin).
- Image upload and storage via AWS S3.
- Background task processing for emails and notifications (Celery + Redis).
- Full-text product search with autocomplete (Elasticsearch).
- Pagination, throttling, and rate limiting.
- Comprehensive admin panel.
- Docker-based development and production environments.

---

## Architecture

```
                    +-------------------+
                    |   Nginx (Proxy)   |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+       +-----------v-----------+
    | Next.js Frontend  |       |  Django REST Backend  |
    | (SSR + CSR)       |       |  (API Server)         |
    +-------------------+       +-----------+-----------+
                                            |
                         +------------------+------------------+
                         |                  |                  |
               +---------v---+    +---------v---+    +---------v---+
               | PostgreSQL  |    |    Redis     |    |Elasticsearch|
               | (Primary DB)|    | (Cache/Queue)|    | (Search)    |
               +-------------+    +------+------+    +-------------+
                                         |
                                  +------v------+
                                  |   Celery    |
                                  |  (Workers)  |
                                  +-------------+
                                         |
                                  +------v------+
                                  |   AWS S3    |
                                  | (Media)     |
                                  +-------------+
```

---

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Python 3.11, Django 4.2, DRF 3.14   |
| Frontend       | Next.js 14, React 18, Tailwind CSS  |
| Database       | PostgreSQL 15                       |
| Cache / Broker | Redis 7                             |
| Task Queue     | Celery 5.3                          |
| Search         | Elasticsearch 8.x                   |
| File Storage   | AWS S3 (boto3 / django-storages)    |
| Containerization| Docker, Docker Compose             |
| Web Server     | Nginx                               |
| Auth           | JWT (djangorestframework-simplejwt) |

---

## Folder Structure

```
handcraft/
|-- README.md
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- Makefile
|
|-- backend/
|   |-- manage.py
|   |-- requirements.txt
|   |-- config/
|   |   |-- __init__.py
|   |   |-- settings/
|   |   |   |-- __init__.py
|   |   |   |-- base.py
|   |   |   |-- development.py
|   |   |   |-- production.py
|   |   |-- urls.py
|   |   |-- wsgi.py
|   |   |-- asgi.py
|   |   |-- celery.py
|   |
|   |-- apps/
|   |   |-- __init__.py
|   |   |-- accounts/       # User management, artisan/customer profiles
|   |   |-- products/       # Product catalog, categories, images, custom orders
|   |   |-- orders/         # Order processing, order items, custom requests
|   |   |-- reviews/        # Product reviews and ratings
|   |   |-- messaging/      # Buyer-seller conversations
|   |   |-- favorites/      # Wishlists and favorite shops
|   |
|   |-- utils/
|       |-- __init__.py
|       |-- storage.py      # S3 storage backend
|       |-- pagination.py   # Custom pagination classes
|       |-- exceptions.py   # Custom exception handlers
|
|-- frontend/
|   |-- package.json
|   |-- next.config.js
|   |-- public/
|   |-- src/
|       |-- app/            # Next.js App Router pages
|       |-- components/     # Reusable React components
|       |-- lib/            # API client, auth utilities
|       |-- hooks/          # Custom React hooks
|       |-- context/        # React Context providers
|       |-- styles/         # Global styles
|
|-- nginx/
    |-- nginx.conf
```

---

## Setup and Installation

### Prerequisites

- Docker and Docker Compose installed
- AWS account with S3 bucket (for production media storage)
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/handcraft.git
   cd handcraft
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`** with your configuration (database credentials, AWS keys, etc.)

4. **Build and start services:**
   ```bash
   make build
   make up
   ```

5. **Run database migrations:**
   ```bash
   make migrate
   ```

6. **Create a superuser:**
   ```bash
   make superuser
   ```

7. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/v1/
   - Admin Panel: http://localhost:8000/admin/
   - Elasticsearch: http://localhost:9200

### Makefile Commands

| Command            | Description                            |
|--------------------|----------------------------------------|
| `make build`       | Build all Docker containers            |
| `make up`          | Start all services                     |
| `make down`        | Stop all services                      |
| `make restart`     | Restart all services                   |
| `make migrate`     | Run Django migrations                  |
| `make makemigrations` | Create new migrations               |
| `make superuser`   | Create Django superuser                |
| `make shell`       | Open Django shell                      |
| `make test`        | Run backend tests                      |
| `make logs`        | Tail service logs                      |
| `make lint`        | Run linters                            |
| `make flush`       | Flush database                         |

---

## API Documentation

### Base URL

```
http://localhost:8000/api/v1/
```

### Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Endpoints Overview

#### Accounts
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| POST   | `/auth/register/`                 | Register a new user         |
| POST   | `/auth/login/`                    | Obtain JWT token pair       |
| POST   | `/auth/token/refresh/`            | Refresh access token        |
| GET    | `/accounts/me/`                   | Get current user profile    |
| PUT    | `/accounts/me/`                   | Update current user profile |
| GET    | `/accounts/artisans/`             | List artisan profiles       |
| GET    | `/accounts/artisans/:id/`         | Get artisan profile detail  |

#### Products
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| GET    | `/products/`                      | List products (filterable)  |
| POST   | `/products/`                      | Create product (artisan)    |
| GET    | `/products/:id/`                  | Get product detail          |
| PUT    | `/products/:id/`                  | Update product (owner)      |
| DELETE | `/products/:id/`                  | Delete product (owner)      |
| GET    | `/products/categories/`           | List categories             |
| GET    | `/products/search/`               | Full-text search            |
| POST   | `/products/:id/images/`           | Upload product images       |

#### Orders
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| GET    | `/orders/`                        | List user orders            |
| POST   | `/orders/`                        | Create order from cart      |
| GET    | `/orders/:id/`                    | Get order detail            |
| PATCH  | `/orders/:id/status/`             | Update order status         |
| POST   | `/orders/custom-requests/`        | Submit custom order request |
| GET    | `/orders/custom-requests/`        | List custom order requests  |

#### Reviews
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| GET    | `/products/:id/reviews/`          | List reviews for product    |
| POST   | `/products/:id/reviews/`          | Create review               |
| PUT    | `/reviews/:id/`                   | Update own review           |
| DELETE | `/reviews/:id/`                   | Delete own review           |

#### Messaging
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| GET    | `/messages/conversations/`        | List conversations          |
| POST   | `/messages/conversations/`        | Start conversation          |
| GET    | `/messages/conversations/:id/`    | Get conversation messages   |
| POST   | `/messages/conversations/:id/`    | Send message                |

#### Favorites
| Method | Endpoint                          | Description                 |
|--------|-----------------------------------|-----------------------------|
| GET    | `/favorites/wishlist/`            | Get user wishlist           |
| POST   | `/favorites/wishlist/`            | Add product to wishlist     |
| DELETE | `/favorites/wishlist/:id/`        | Remove from wishlist        |
| GET    | `/favorites/shops/`               | Get favorite shops          |
| POST   | `/favorites/shops/`               | Follow a shop               |
| DELETE | `/favorites/shops/:id/`           | Unfollow a shop             |

---

## User Roles

### Customer
- Browse and search products.
- Place orders and track their status.
- Submit custom order requests.
- Leave reviews on purchased products.
- Manage wishlist and favorite shops.
- Message artisans.

### Artisan
- All customer capabilities, plus:
- Create and manage an artisan shop profile.
- List, update, and remove products.
- Manage incoming orders (accept, ship, cancel).
- Respond to custom order requests with quotes.
- Reply to reviews.
- View shop analytics.

### Admin
- Full access to Django admin panel.
- Manage users, products, orders, and reviews.
- Moderate content and resolve disputes.
- View platform-wide analytics.

---

## Business Logic

### Order Lifecycle
1. **Cart** -- Customer adds products to cart (client-side state).
2. **Checkout** -- Customer submits order; stock is validated and reserved.
3. **Pending** -- Order is created; artisan is notified.
4. **Confirmed** -- Artisan confirms the order and begins preparation.
5. **Shipped** -- Artisan marks order as shipped with tracking info.
6. **Delivered** -- Order marked as delivered.
7. **Completed** -- Auto-completed after 14 days if no dispute.
8. **Cancelled** -- Either party can cancel before shipping; refund initiated.

### Custom Order Flow
1. Customer submits a custom order request to an artisan.
2. Artisan reviews the request and sends a quote (price + timeline).
3. Customer accepts or declines the quote.
4. On acceptance, a standard order is created with the quoted price.

### Review System
- Only customers who have received a delivered order can leave a review.
- Reviews include a 1-5 star rating and text.
- Optional image attachments.
- Artisans can reply to reviews (one reply per review).
- Average rating is recalculated on each new review.

### Search and Discovery
- Full-text search powered by Elasticsearch.
- Filters: category, price range, tags, artisan location, rating.
- Sort by: relevance, price (asc/desc), newest, rating, popularity.

---

## Roadmap

### Phase 1 -- MVP (Current)
- [x] User authentication (JWT)
- [x] Artisan and customer profiles
- [x] Product CRUD with image upload
- [x] Category and tag management
- [x] Order placement and tracking
- [x] Review system
- [x] Messaging system
- [x] Wishlist and favorite shops
- [x] Docker-based development environment

### Phase 2 -- Enhanced Features
- [ ] Payment gateway integration (Stripe)
- [ ] Real-time notifications (WebSockets)
- [ ] Email notifications (transactional emails)
- [ ] Advanced analytics dashboard for artisans
- [ ] Product variant support (size, color, material)
- [ ] Coupon and discount system

### Phase 3 -- Scale and Polish
- [ ] Recommendation engine
- [ ] Multi-language support (i18n)
- [ ] Mobile-responsive PWA
- [ ] SEO optimization
- [ ] CDN integration for media
- [ ] Automated testing pipeline (CI/CD)
- [ ] Load testing and performance optimization

### Phase 4 -- Growth
- [ ] Mobile apps (React Native)
- [ ] Artisan verification program
- [ ] Promoted listings (advertising)
- [ ] Social sharing integration
- [ ] Affiliate program
- [ ] Multi-currency support

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

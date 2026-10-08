<div align="center">

# ⚡ Weasleys' Wizard Wheezes ⚡

<img src="assets/logo.PNG" alt="Weasleys' Wizard Wheezes logo" width="200" />

### _A Harry Potter themed e-commerce marketplace — for every Harry Potter fan._

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

[![Architecture diagram](https://gitdiagram.com/diagram-badge.svg)](https://gitdiagram.com/eshaabbasi/weasleyswizard_backend?utm_source=readme&utm_medium=badge)

[🌐 Live Demo](https://weasleys-wizard-frontend.vercel.app) · [🎨 Front-end](./frontend) · [🧠 Back-end](./backend) · [📋 Planning Materials](./docs/Weasleys_Wizard_Wheezes_Project_Plan.pdf)

![Weasleys' Wizard Wheezes home page](./assets/screenshot.png)

</div>

---

## 📚 Table of Contents

- [About the App](#-about-the-app)
- [Getting Started](#-getting-started)
- [User Roles](#-user-roles)
- [User Stories](#-user-stories)
- [ERD](#️-entity-relationship-diagram-erd)
- [Wireframes](#️-wireframes)
- [Features](#-features)
- [API Routes](#️-api-routes)
- [Technologies Used](#-technologies-used)
- [Attributions](#-attributions)
- [Next Steps](#-next-steps)

---

## 🪄 About the App

**Weasleys' Wizard Wheezes** is a Harry Potter themed e-commerce marketplace where multiple wizarding shop owners sell magical joke-shop products, and customers can browse, buy, review and favorite them. Find wands, trunks, house apparel and magical gifts, all in one enchanted place.

A shop owner registers a shop, which stays **pending** until the platform Admin authorizes it. A shop cannot post products before approval. Once approved, the owner manages their own products (with multiple images uploaded via Cloudinary). Customers browse only authorized shops, add items to a cart, check out through a themed mock **Gringotts** payment flow, track orders through **Owl Post** delivery stages, and leave reviews (optionally with their own photos). The Admin has platform-wide oversight: authorizing or suspending shops, and deleting any product, for example after reviewing a pattern of bad reviews.

### 💡 Why I built it

I built this as my capstone project for the General Assembly software engineering course. I wanted something fun that is also a real, full-stack marketplace: three user roles, role-based permissions enforced on the server, image uploads, and a full purchase flow, all wrapped in a world I love.

---

## 🚀 Getting Started

| Resource                                                          | Link                                                                                                      |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 🌐 **Deployed app**                                               | [weasleys-wizard-frontend.vercel.app](https://weasleys-wizard-frontend.vercel.app)                        |
| 📋 **Planning materials** (user stories, ERD, wireframes, routes) | [Project Plan PDF](./docs/Weasleys_Wizard_Wheezes_Project_Plan.pdf)                                       |
| 🧠 **Back-end code**                                              | [`/backend`](./backend)                                                                                   |
| 🎨 **Front-end code**                                             | [`/frontend`](./frontend)                                                                                 |
| 🧩 **Architecture diagram**                                       | [GitDiagram](https://gitdiagram.com/eshaabbasi/weasleyswizard_backend?utm_source=readme&utm_medium=badge) |

### Repository structure

```
WeasleysWizard/
├── frontend/     React app (deployed on Vercel)
├── backend/      FastAPI app (deployed on Render)
├── docs/         Planning materials (project plan PDF)
├── assets/       Logo and screenshot used in this README
└── README.md
```

### Run it locally

**1. Clone the repo**

```bash
git clone https://github.com/EshaAbbasi/WeasleysWizard.git
cd WeasleysWizard
```

**2. Start the back-end** (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` (adjust names to match your code):

```env
DATABASE_URL=postgresql://user:password@host:5432/postgres   # Supabase connection string
SECRET_KEY=your-jwt-secret
ALGORITHM=HS256
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
FRONTEND_URL=http://localhost:5173
```

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` and the Swagger docs at `http://localhost:8000/docs`.

**3. Start the front-end** (React), in a second terminal

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

> If your front-end uses Create React App instead of Vite, use `REACT_APP_API_URL` and `npm start`.

---

## 🎭 User Roles

| Role              | What they can do                                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 👑 **Admin**      | Authorize or suspend shops, view all shops / products / orders platform-wide, delete any product or review                                       |
| 🧙 **Shop Owner** | Register a shop (pending approval), add / edit / delete own products once approved (with multiple images), view orders containing own products   |
| 🛒 **Customer**   | Browse authorized shops and products by category, add to cart, check out, view own order history, write reviews (with images), favorite products |

---

## 📖 User Stories

Full cards with acceptance criteria are in the [planning PDF](./docs/Weasleys_Wizard_Wheezes_Project_Plan.pdf).

### 🛒 Customer

| #    | Story                                                                   | Acceptance criteria                                                      |
| ---- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| US01 | Register and log in, so I can save a cart, checkout and track my orders | Register/login returns a JWT; guests cannot checkout or review           |
| US02 | Browse products from authorized shops only                              | Product list excludes shops where `is_authorized` is false               |
| US03 | Filter products by category                                             | Category filter returns only matching products                           |
| US04 | View multiple images per product                                        | Product detail displays all URLs in `image_urls`                         |
| US05 | Add products to a cart with live stock limits                           | Cart blocks quantity above current stock                                 |
| US06 | Complete a mock checkout                                                | Order + order_items are created; cart clears after success               |
| US07 | View my order history and status                                        | `GET /orders` returns only the logged-in user's orders                   |
| US08 | Write a review with a star rating and optional images                   | Review saved with rating, comment and `image_urls`; linked to my user id |
| US09 | Edit or delete my own review                                            | PUT/DELETE blocked unless `review.user_id` matches the logged-in user    |
| US10 | Mark a product as a favorite                                            | Favorites list returns only my favorited products                        |

### 🧙 Shop Owner

| #    | Story                                                        | Acceptance criteria                                                     |
| ---- | ------------------------------------------------------------ | ----------------------------------------------------------------------- |
| US11 | Register a shop                                              | New shop is created with `is_authorized = false` by default             |
| US12 | Be blocked from posting products until my shop is authorized | `POST /products` returns 403 if the shop is not authorized              |
| US13 | Add a product with multiple images                           | Images upload to Cloudinary via the backend; URLs saved in `image_urls` |
| US14 | Edit or delete only my own products                          | PUT/DELETE blocked unless the product belongs to my shop                |
| US15 | View orders containing my products                           | Orders endpoint filters order_items by my shop's product ids            |

### 👑 Admin

| #    | Story                                             | Acceptance criteria                                                |
| ---- | ------------------------------------------------- | ------------------------------------------------------------------ |
| US16 | View and authorize pending shops                  | `PUT /admin/shops/{id}/authorize` flips `is_authorized` to true    |
| US17 | Suspend a shop                                    | Suspended shop's products stop appearing to customers              |
| US18 | Delete any product on the platform                | `DELETE /products/{id}` succeeds for admin regardless of ownership |
| US19 | View all shops, products and orders platform-wide | Admin-only endpoints return all records                            |

---

## 🗺️ Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ SHOPS : "owns"
    USERS ||--o{ ORDERS : "places"
    USERS ||--o{ REVIEWS : "writes"
    SHOPS ||--o{ PRODUCTS : "sells"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    PRODUCTS ||--o{ ORDER_ITEMS : "appears in"
    PRODUCTS ||--o{ REVIEWS : "receives"

    USERS {
        int id PK
        string username
        string email
        string password_hash
        string role
    }
    SHOPS {
        int id PK
        int owner_id FK
        string name
        text description
        bool is_authorized
        string status
    }
    PRODUCTS {
        int id PK
        int shop_id FK
        string name
        string category
        numeric price_gbp
        int stock
        jsonb image_urls
    }
    ORDERS {
        int id PK
        int user_id FK
        numeric total_gbp
        string status
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        numeric price_at_purchase
    }
    REVIEWS {
        int id PK
        int user_id FK
        int product_id FK
        int rating
        text comment
        jsonb image_urls
        bool is_favorite
    }
```

> The cart lives in React state and is written to `orders` / `order_items` at checkout.

---

## 🖼️ Wireframes

The full wireframes are in the [planning PDF](./docs/Weasleys_Wizard_Wheezes_Project_Plan.pdf).

| #   | Screen                                                         | Role       |
| --- | -------------------------------------------------------------- | ---------- |
| 1   | Register / Login                                               | Everyone   |
| 2   | Browse Shops & Products (category filter)                      | Customer   |
| 3   | Product Detail (image gallery + "Owls from customers" reviews) | Customer   |
| 4   | Cart & Gringotts Checkout                                      | Customer   |
| 5   | My Orders (Owl Post tracking)                                  | Customer   |
| 6   | Favorites                                                      | Customer   |
| 7   | Shop Registration (pending approval)                           | Shop Owner |
| 8   | Add / Edit Product (multi-image upload)                        | Shop Owner |
| 9   | Shop Owner Dashboard                                           | Shop Owner |
| 10  | Admin Dashboard (authorize shops, delete products)             | Admin      |
| 11  | Admin: Product Moderation                                      | Admin      |

**Navigation flow**

- **Customer:** Register/Login → Browse → Product Detail → Cart → Checkout → My Orders
- **Shop Owner:** Shop Registration → (pending) → Dashboard → Add/Edit Product
- **Admin:** Admin Dashboard → Authorize Shops / Moderate Products

---

## ✨ Features

- 🔐 JWT authentication with three roles and protected routes (`RoleRoute`)
- 🏪 Multi-vendor marketplace: only approved shops are visible to customers
- 🖼️ Multiple images per product and per review, uploaded through the backend to Cloudinary
- 🛍️ Cart with live stock limits and a themed Gringotts checkout
- 🦉 Order tracking: _Owl Post Received → In Transit via Floo Network → Delivered_
- ⭐ Reviews with star ratings and photos, plus favorites
- 💰 Prices shown in Galleons, Sickles and Knuts alongside GBP
- 🚫 "Banned at Hogwarts!" badge on mischief products
- 🛡️ Admin moderation tools

---

## 🛣️ API Routes

Interactive docs are available at `/docs` (Swagger UI) when the back-end is running. Role checks are enforced server-side.

| Method | Route                         | Purpose                                                 | Access                         |
| ------ | ----------------------------- | ------------------------------------------------------- | ------------------------------ |
| POST   | `/auth/register`              | Sign up (choose role)                                   | Public                         |
| POST   | `/auth/login`                 | Sign in, returns JWT                                    | Public                         |
| GET    | `/me`                         | Current user profile                                    | Logged in                      |
| POST   | `/shops`                      | Register a new shop                                     | Shop Owner                     |
| GET    | `/shops/mine`                 | View my shop                                            | Shop Owner                     |
| GET    | `/shops`                      | List authorized shops                                   | Public                         |
| GET    | `/admin/shops`                | List all shops incl. pending                            | Admin                          |
| PUT    | `/admin/shops/{id}/authorize` | Approve / suspend a shop                                | Admin                          |
| POST   | `/upload-image`               | Upload one image to Cloudinary, return URL              | Shop Owner / Customer          |
| GET    | `/products`                   | List / search / filter products (authorized shops only) | Public                         |
| GET    | `/products/{id}`              | Product detail incl. images + reviews                   | Public                         |
| POST   | `/products`                   | Add product (blocked if shop not authorized)            | Shop Owner                     |
| PUT    | `/products/{id}`              | Edit own product                                        | Shop Owner (own)               |
| DELETE | `/products/{id}`              | Delete product                                          | Shop Owner (own) / Admin (any) |
| GET    | `/admin/products`             | List all products platform-wide                         | Admin                          |
| POST   | `/orders`                     | Checkout (creates order + order_items)                  | Customer                       |
| GET    | `/orders`                     | My order history                                        | Customer (own)                 |
| GET    | `/shops/{id}/orders`          | Orders containing my shop's products                    | Shop Owner                     |
| GET    | `/admin/orders`               | All orders platform-wide                                | Admin                          |
| POST   | `/reviews`                    | Add review (rating, comment, optional images)           | Customer                       |
| GET    | `/reviews/{product_id}`       | List reviews for a product                              | Public                         |
| PUT    | `/reviews/{id}`               | Edit own review                                         | Customer (own)                 |
| DELETE | `/reviews/{id}`               | Delete review                                           | Customer (own) / Admin (any)   |
| GET    | `/favorites`                  | List my favorited products                              | Customer                       |

---

## 🧰 Technologies Used

| Layer                 | Technology                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------ |
| **Front-end**         | JavaScript, React, React Router, Context API (Auth + Cart)                                 |
| **Back-end**          | Python, **FastAPI**, SQLAlchemy, JWT authentication, bcrypt                                |
| **Database**          | **PostgreSQL** hosted on **Supabase**                                                      |
| **Image storage**     | Cloudinary (uploads handled by the backend only; the API secret is never exposed to React) |
| **Front-end hosting** | **Vercel**                                                                                 |
| **Back-end hosting**  | **Render**                                                                                 |
| **Tools**             | Git & GitHub, VS Code, Swagger UI, GitDiagram                                              |

### Code layout

```
backend/app/
├── main.py  models.py  schemas.py  database.py  auth.py  dependencies.py
├── cloudinary_config.py
└── routers/   auth, shops, products, orders, reviews, uploads, admin

frontend/src/
├── pages/        Login, Register, Shops, ProductList, ProductDetail, Cart, Checkout,
│                 MyOrders, Favorites, ShopDashboard, AddEditProduct, AdminDashboard
├── components/   Navbar, ProductCard, ReviewCard, ImageUploader, RoleRoute
└── context/      AuthContext, CartContext
```

---

## 🙏 Attributions

- **Images:** product imagery from [Harry Potter Shop UK](https://harrypottershop.co.uk/?srsltid=AU7gw4VgNUOurTL9umt7DcG6yQ4KHKopZeIMmFdqht91SLSrOE8O2e6sand)
- **Music:** magical background music from [Free To Use Music](https://freetouse.com/music/search/magic)
- **Architecture diagram:** generated with [GitDiagram](https://gitdiagram.com/eshaabbasi/weasleyswizard_backend?utm_source=readme&utm_medium=badge)
- **Harry Potter** characters, names and the wizarding world are created by J.K. Rowling. This is a fan-made, non-commercial educational project and is not affiliated with or endorsed by Warner Bros., J.K. Rowling or any rights holders. Product descriptions were written by me.

---

## 🔮 Next Steps

Planned future enhancements:

- 🗂️ **Categories table:** replace the fixed category list with admin-managed, relational categories
- 🎟️ **Coupons:** admin-managed discount codes with activation and expiry dates
- 💳 **Real payments:** replace the mock Gringotts checkout with Stripe
- 📧 **Notifications:** email updates when an order status changes or a shop is approved
- 🔎 **Search and pagination:** faster product discovery with search, sorting and paging
- 📊 **Shop analytics:** sales and stock insights for shop owners
- 🚩 **Review flagging:** let users report reviews for admin moderation
- 🌗 **Accessibility and mobile polish:** further responsive and a11y improvements

---

<div align="center">

**Made with ✨ and a little bit of magic by [Esha Abbasi](https://github.com/EshaAbbasi)**

_"Mischief managed."_

</div>

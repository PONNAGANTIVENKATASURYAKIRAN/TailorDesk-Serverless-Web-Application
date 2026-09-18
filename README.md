## **TailorDesk: Serverless Web Application & Automated CI/CD Pipeline on AWS**

A full-stack, serverless web application and administrative ledger designed for Lakshmi Devi Ladies Tailors & Boutique (Guntur, AP). It provides a responsive booking catalog for customers alongside a real-time order intake and worker productivity tracker for shop owners, backed by an automated GitHub Actions CI/CD deployment workflow.

## **Key Features**

* **Interactive Customer Booking Flow:** 3-step service selection, custom alteration notes, garment previews, and direct WhatsApp order dispatch.
* **Smart Customer Memory:** Recognizes returning clients by phone number to eliminate duplicate profiles and streamline repeat bookings.
* **Owner Kanban Board:** Real-time customer pipeline categorized by order stage (*Reached to Stitching*, *Selected but Not Now*, and *Just Browsed*).
* **Worker Ledger & Payout Settlement:** Tracks daily stitched pieces, calculates shop margins per garment, and enables one-click balance settlements with worker privacy modes.
* **Bilingual UI:** Instant switching between English and Telugu across all customer touchpoints.
* **Customer Feedback System:** In-app rating and review capture with moderation controls in the administrative dashboard.
* **Automated CI/CD Workflows:** Fully integrated GitHub Actions pipelines (`frontend.yml` and `backend.yml`) utilizing GitHub Secrets for zero-downtime deployments and secure credential management.

## **Tech Stack**

* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Hosting & CDN:** Amazon S3, AWS CloudFront
* **API Layer:** Amazon API Gateway (HTTP/REST Lambda Proxy Integration)
* **Compute:** AWS Lambda (Python 3.12 runtime)
* **Database:** Amazon DynamoDB (On-Demand Capacity)
* **CI/CD & DevOps:** GitHub Actions, AWS CLI, GitHub Encrypted Secrets
* **Security & Auth:** Email/PIN administrative authentication, AWS IAM least-privilege policies, HTTPS termination via CloudFront

## **Live Demo & Owner Access**

* **Demo URL:** [d34hvud16ku84i.cloudfront.net](https://www.google.com/search?q=https://d34hvud16ku84i.cloudfront.net&utm_source=gemini)
* **Owner Dashboard:** Click **Owner** in the top navigation bar.
* **Demo Username:** `suryakiran9391@gmail.com`
* **Demo Passcode:** `Surya@9848`

---

## **Repository Structure**

```text
.
├── .github/
│   └── workflows/
│       ├── frontend.yml               # S3 sync & CloudFront cache invalidation
│       └── backend.yml                # Automated Lambda function deployment
├── frontend/
│   ├── index.html                     # Booking UI & Owner Kanban Dashboard
│   └── style.css                      # Responsive layout & theme styling
├── backend/
│   ├── lambda_customer_catalog.py     # Catalog, booking & review API handler
│   └── lambda_worker_handler.py       # Ledger calculations & payout settlements
└── README.md

```

# FAQ System

A Django-based FAQ system that supports multilingual questions and answers with WYSIWYG, caching, and a RESTful API.

## Installation

### Prerequisites

- Python 3.11 (see [Dockerfile](Dockerfile))
- Redis (for caching; see [faq_system/faq_system/settings.py](faq_system/faq_system/settings.py))
- Node.js & npm (if you intend to modify frontend assets)

### Setup

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/Sahil-Chhoker/FAQ-app.git
   cd FAQ-app
   ```

2. **Create and Activate a Virtual Environment**:
   
    ```python
    python -m venv .venv
    .venv\Scripts\activate # On linux source .venv/bin/activate
    ```

3. **Create Environment File**:

    Create a `.env` file in the project root with the following format:
    ```
    DJANGO_SECRET_KEY='your_django_secret_key'
    REDIS_URL="your_redis_url"
    ```

4. **Install Python Dependencies**:

    ```python
    pip install -r requirements.txt
    ```

5. **Setup Database**:

    ```python
    python faq_system/manage.py migrate
    ```

6. **Collect Static Files**:

    ```python
    python faq_system/manage.py collectstatic --no-input
    ```

7. **Run Development Server**:

    ```python
    python faq_system/manage.py runserver
    ```

8. **If using Docker**:

    ```
    docker built -t faq-system .
    docker run -p 8000:8000 faq-system
    ```

9. **If using Docker Compose**:

    ```
    docker-compose up --build
    ```

# API Documentation

**NOTE**: This is a web-app fully complete in itself, you can go to http://localhost:8000, after running the development server and access all the features.

---

The API is powered by Django REST Framework and is accessible at `/api/faqs/`. Below are the available endpoints:

## Endpoints

1. **List FAQs**:

    [`GET /api/faqs/`](faq_system/faqs/views.py): Returns a list of FAQs.

    Example:
    ```
    [
        {
            "id": 1,
            "question": "Is it free for everyone?",
            "answer": "Yes, it's free for everyone.",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
    ]
    ```

2. **Retrieve FAQ**:

    [`GET /api/faqs/{id}`](faq_system/faqs/views.py): Returns a single FAQ by its ID.

3. **Create FAQ**:

    [`POST /api/faqs/`](faq_system/faqs/views.py): Creates a new FAQ.

    Payload Example:

    ```
    {
        "question": "How do I reset my password?",
        "answer": "Click on the ‘Forgot Password’ link on the login page."
    }
    ```

4. **Update FAQ**:

    [`PUT /api/faqs/{id}`](faq_system/faqs/views.py): Updates an existing FAQ.

5. **Delete FAQ**:

   [`DELETE /api/faqs/{id}/`](faq_system/faqs/views.py): Deletes an FAQ.

6. **Bulk Create FAQ**:
   
   [`POST /api/faqs/bulk_create/`](faq_system/faqs/views.py): Creates multiple FAQs in a single request.


## Running Tests

To run tests for project, execute:
```python
python faq_system/manage.py test
```

## Additional Information

1. Frontend Templates:
    The HTML templates for the FAQ pages can be found under [faqs](faq_system/templates/faqs).

2. Static Files:
    JavaScript and CSS assets are located in [staticfiles](faq_system/staticfiles).

3. CKEditor Integration:
    For rich text editing, the project uses CKEditor5. See the configuration in [settings.py](faq_system/faq_system/settings.py)


## Assumptions Made
1. CKEditor 5 is used along with `django_ckeditor_5` because `ckeditor4` was found vurnerable.

3. There is no way of translating other languages into English, therefore all the questions and answers must be written in English only.

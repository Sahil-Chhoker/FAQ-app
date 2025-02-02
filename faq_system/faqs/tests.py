from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from .models import FAQ


class FAQViewTests(TestCase):
    def setUp(self):
        cache.clear()
        # Create test users
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="userpass123"
        )

        # Create test client and FAQ
        self.client = Client()
        self.faq = FAQ.objects.create(
            question="Is it free for everyone?", answer="Yes, its free for everyone."
        )

        # Create API endpoints
        self.list_url = reverse("faq-list")
        self.detail_url = reverse("faq-detail", kwargs={"pk": self.faq.pk})

    def tearDown(self):
        cache.clear()

    def test_list_view_anonymous(self):
        """Test that anonymous users can view FAQs"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_create_view_authenticated(self):
        """Test that authenticated users can create FAQs"""
        self.client.login(username="admin", password="adminpass123")
        data = {"question": "New test question?", "answer": "Test answer."}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FAQ.objects.count(), 2)

    def test_create_view_unauthenticated(self):
        """Test that unauthenticated users cannot create FAQs"""
        data = {"question": "New test question?", "answer": "Test answer."}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FAQ.objects.count(), 1)

    def test_edit_view_authenticated(self):
        """Test that authenticated users can edit FAQs"""
        self.client.login(username="admin", password="adminpass123")
        data = {"question": "Updated question?", "answer": "Updated answer."}
        response = self.client.put(
            self.detail_url, data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.faq.refresh_from_db()
        self.assertEqual(self.faq.question, "Updated question?")

    def test_delete_view_authenticated(self):
        """Test that authenticated users can delete FAQs"""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FAQ.objects.count(), 0)

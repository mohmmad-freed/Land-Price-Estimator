from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from Normal_User_Side.models import Project
from django.contrib.auth import get_user_model
User = get_user_model()

class ProjectModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="TestPassword123",
            type="normal"
        )

    def test_project_creation(self):
        project = Project.objects.create(
            user=self.user,
            name="Test Project",
            governorate="Ramallah",
            land_size=500,
            land_type="agricultural",
            political_classification="a",
            status="draft"
        )

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.user.email, "testuser@example.com")
        self.assertEqual(project.status, "draft")
        self.assertEqual(project.land_size, 500)



class ProjectIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            type="normal_user"
        )
        self.client = Client()
        self.client.login(email="testuser@example.com", password="testpass123")

        self.project_data = {
            "name": "Test Project",
            "governorate": "ramallah",
            "land_type": "agricultural",
            "political_classification": "a",
            "description": "Test description",
            "land_size": 100
        }

    def test_create_project_draft(self):
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "save"})
        self.assertEqual(response.status_code, 302, "Draft creation should redirect")
        
        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "draft", "Project status should be 'draft'")
        self.assertEqual(project.user, self.user, "Project should be linked to the logged-in user")

    @patch("Normal_User_Side.views.predict_land_price")
    def test_create_project_with_estimation(self, mock_predict):
        mock_predict.return_value = 50000  
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "estimate"})
        self.assertEqual(response.status_code, 302, "Estimation creation should redirect")

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "completed", "Project status should be 'completed'")
        self.assertEqual(project.estimated_price, 50000, "Estimated price should match mocked ML value")

    @patch("Normal_User_Side.views.predict_land_price")
    def test_estimation_failure_handled(self, mock_predict):
        mock_predict.side_effect = Exception("ML error")
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "estimate"})
        self.assertEqual(response.status_code, 302, "Redirect should occur even if ML fails")

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "draft", "Project should fallback to 'draft' on ML failure")
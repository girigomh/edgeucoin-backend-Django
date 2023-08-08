from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid

# Create your models here.

def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)

    return 'images/{filename}'.format(filename=filename)

class Genders(models.TextChoices):
    FEMALE = "female"
    MALE = "male"

class SchoolLevel(models.TextChoices):
    ELEMENTARY = "Elementary School"
    MIDDLE = "Middle School"
    HIGH = "High School"

class UserAccountManager(BaseUserManager):
    
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    
class UserAccount(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin"
        SCHOOL = "school"
        STUDENT = "student"
        TEACHER = "teacher"
        PARENT = "parent"

    role = models.CharField(max_length=8, choices=Roles.choices, default=Roles.TEACHER)
    
    username = None
    email = models.EmailField(_('Email address'), unique=True)
    is_active = models.BooleanField(default = True)
    is_admin = models.BooleanField(default = False)
    is_staff = models.BooleanField(default = False)
    is_superuser = models.BooleanField(default = False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserAccountManager()

    def __str__(self):
        return self.email
    
class School(models.Model):
    name = models.CharField(max_length=40, null=True)
    image = models.FileField(upload_to=upload_to, null=True, blank=True)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=SchoolLevel.choices, default=SchoolLevel.ELEMENTARY)
    contact = models.CharField(max_length=80, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    contact_2 = models.CharField(max_length=80, null=True, blank=True)
    email_2 = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=40, blank=True, null=True)
    extras = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=40, null=True, blank=True)
    state = models.CharField(max_length=40, null=True, blank=True)
    country = models.CharField(max_length=40, null=True, blank=True)
    zipcode = models.CharField(max_length=20, null=True, blank=True)

class Student(models.Model):
    name = models.CharField(max_length=40, null=True)
    image = models.FileField(upload_to=upload_to, null=True, blank=True)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    grade = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=6, choices=Genders.choices, default=Genders.MALE)
    athlete = models.BooleanField(default=False)
    college_bound = models.BooleanField(default=False)
    workforce_bound = models.BooleanField(default=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    coin = models.IntegerField(default=0)
    interests = models.JSONField(null=True)

class Parent(models.Model):
    name = models.CharField(max_length=40, null=True)
    image = models.FileField(upload_to=upload_to, null=True, blank=True)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=6, choices=Genders.choices, default=Genders.MALE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True)
    students = models.ManyToManyField(Student, blank=True)

class Teacher(models.Model):
    name = models.CharField(max_length=40, null=True)
    image = models.FileField(upload_to=upload_to, null=True, blank=True)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    subject = models.JSONField(null=True)
    gender = models.CharField(max_length=6, choices=Genders.choices, default=Genders.MALE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, blank=True)

class Goal(models.Model):
    name = models.CharField(max_length=40)
    responses = models.JSONField(null=True)
    
class AwardGoal(models.Model):
    class GoalTypes(models.TextChoices):
        ACADEMIC = "ACADEMIC", "academic"
        BEHAVIORAL = "BEHAVIORAL", "behavioral"
        PARENT = "PARENT", "parent"

    class Status(models.TextChoices):
        INCOMPLETE = "INCOMPLETE", "incomplete"
        COMPLETED = "COMPLETED", "completed"
    
    type = models.CharField(max_length=20, choices=GoalTypes.choices, default=GoalTypes.BEHAVIORAL)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reporter = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    score = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INCOMPLETE)
    view_status = models.BooleanField(default=False)

class Reward(models.Model):
    title = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=200, blank=True)
    coin = models.IntegerField()
    image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    schools = models.ManyToManyField(School, blank=True)
    students = models.ManyToManyField(Student, blank=True)

class Record(models.Model):
    date = models.DateField(auto_now_add=True)
    score = models.IntegerField()
    note = models.CharField(max_length=200)
    goal = models.ForeignKey(AwardGoal, on_delete=models.CASCADE)
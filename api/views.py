from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.pagination import LimitOffsetPagination
from django.contrib.auth.models import update_last_login
from .serializers import *
from .models import *
import os
from server.settings import BASE_DIR


def file_save(file):
    ext = file.name.split(".")[-1]
    name = "%s.%s" % (uuid.uuid4(), ext)
    filename = os.path.join("images", name)
    with open(os.path.join(BASE_DIR, "media", filename), "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)
        f.close()
    return filename


class SignUpView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.data.get("role")
            if role == "admin":
                user = get_user_model().objects.create_super_user(
                    **serializer.validated_data
                )
                user.save()
            else:
                user = get_user_model().objects.create_user(**serializer.validated_data)
                user.save()
                if role == "parent":
                    Parent.objects.create(user=user)
                elif role == "teacher":
                    Teacher.objects.create(user=user)
                elif role == "student":
                    Student.objects.create(user=user)
                elif role == "school":
                    School.objects.create(user=user)

            return Response(status=HTTP_201_CREATED)
        return Response(status=HTTP_400_BAD_REQUEST)


class AuthCheck(APIView):
    def get(self, request):
        return Response(request.user.is_authenticated)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        result = super(EmailTokenObtainPairView, self).post(request)
        try:
            user = get_user_model().objects.get(email=request.data["email"])
            update_last_login(None, user)
        except Exception as exec:
            return None
        return result


class ResetPasswordView(APIView):
    def get_object(self, email):
        user = get_object_or_404(get_user_model(), email=email)
        return user

    def put(self, request):
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data["email"]
            user = self.get_object(email)
            password = serializer.data["password"]
            if user.check_password(password):
                return Response(
                    {
                        "status": HTTP_400_BAD_REQUEST,
                        "message": "It should be different from your last password.",
                    }
                )
            user.set_password(password)
            user.save()
            return Response({"status": HTTP_200_OK})
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(request.user).data
        if user.role == "teacher":
            serializer["profile"] = TeacherSerializer(user.teacher).data
        if user.role == "school":
            serializer["profile"] = SchoolSerializer(user.school).data
        if user.role == "student":
            serializer["profile"] = StudentSerializer(user.student).data
        if user.role == "parent":
            serializer["profile"] = ParentSerializer(user.parent).data
        return Response(serializer, status=HTTP_200_OK)


class UserView(APIView):
    queryset = CustomUser.objects.all().order_by("name")
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination

    def get(self, request):
        try:
            user = request.user
            if user.role == "student":
                school = user.student.school
            if user.role == "teacher":
                school = user.teacher.school
            if user.role == "parent":
                school = user.parent.school
            userArr = []
            if user.role != "teacher":
                for serializer in TeacherSerializer(
                    school.teacher_set.all(), many=True
                ).data:
                    userArr.append(int(serializer.get("user")))
            if user.role != "student":
                for serializer in StudentSerializer(
                    school.student_set.all(), many=True
                ).data:
                    userArr.append(int(serializer.get("user")))
            if user.role != "parent":
                for serializer in ParentSerializer(
                    school.parent_set.all(), many=True
                ).data:
                    userArr.append(int(serializer.get("user")))
            excludeUsersArr = []
            excludeUsers = self.request.query_params.get("exclude")
            if excludeUsers:
                userIds = excludeUsers.split(",")
                for userId in userIds:
                    excludeUsersArr.append(int(userId))

            users = CustomUser.objects.filter(id__in=userArr).exclude(
                id__in=excludeUsersArr
            )
            return Response(UserSerializer(users, many=True).data, status=HTTP_200_OK)
        except:
            return []


class ParentView(APIView):
    model = Parent
    serializer_class = ParentSerializer

    def get(self, request):
        parents = self.model.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            parents = school.parent_set.all()
        if request.query_params.get("student", None) is not None:
            student = Student.objects.get(id=request.query_params.get("student"))
            parents = student.parent_set.all()
        serializers = self.serializer_class(parents, many=True).data
        for serializer in serializers:
            parent = self.model.objects.get(id=serializer.get("id"))
            user_serializer = UserSerializer(parent.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            school_serializer = SchoolSerializer(parent.school).data
            school_serializer["name"] = UserSerializer(parent.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(parent.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
            serializer["students"] = parent.students.count()
        if request.query_params.get("id", None) is not None:
            parent = self.model.objects.get(id=request.query_params.get("id"))
            serializer = self.serializer_class(parent).data
            user_serializer = UserSerializer(parent.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            school_serializer = SchoolSerializer(parent.school).data
            school_serializer["name"] = UserSerializer(parent.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(parent.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
            student_serializers = StudentSerializer(
                parent.students.all(), many=True
            ).data
            for student_serializer in student_serializers:
                student = Student.objects.get(id=student_serializer.get("id"))
                student_serializer["name"] = UserSerializer(student.user).data.get(
                    "name"
                )
                student_serializer["image"] = UserSerializer(student.user).data.get(
                    "image"
                )
            serializer["students"] = student_serializers
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            parent = self.model.objects.get(id=request.query_params.get("id"))
            if request.data.get("school", None) is not None:
                parent.school = School.objects.get(id=request.data.get("school"))
            if request.data.get("gender", None) is not None:
                parent.gender = request.data.get("gender")
            if request.data.get("phone", None) is not None:
                parent.phone = request.data.get("phone")
            if request.data.get("relationship", None) is not None:
                parent.relationship = request.data.get("relationship")
            parent.save()

            user = parent.user
            if request.data.get("email", None) is not None:
                user.email = request.data.get("email")
            if request.data.get("password", None) is not None:
                user.set_password(request.data.get("password"))
            if request.data.get("name", None) is not None:
                user.name = request.data.get("name")
            if request.FILES.get("image", None) is not None:
                user.image = file_save(request.FILES["image"])
            user.save()

            if request.data.get("students[]", None) is not None:
                parent.students.clear()
                for s_id in request.POST.getlist("students[]"):
                    student = Student.objects.get(id=s_id)
                    parent.students.add(student)
            if request.data.get("student", None) is not None:
                student = Student.objects.get(id=request.data.student)
                parent.students.add(student)

            return Response({"status": "success"}, status=HTTP_200_OK)

        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(
                **user_serializer.validated_data
            )
            data = request.data
            data["user"] = user.id
            parent_serializer = self.serializer_class(data=data)
            if parent_serializer.is_valid():
                parent = self.model.objects.create(**parent_serializer.validated_data)
                parent.save()
                for s_id in request.POST.getlist("students[]"):
                    student = Student.objects.get(id=s_id)
                    parent.students.add(student)
                return Response(
                    {
                        "status": "success",
                    },
                    status=HTTP_201_CREATED,
                )
            return Response(parent_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)


class TeacherView(APIView):
    model = Teacher
    serializer_class = TeacherSerializer

    def get(self, request):
        teachers = self.model.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            teachers = school.teacher_set.all()
        if request.query_params.get("student", None) is not None:
            student = Student.objects.get(id=request.query_params.get("student"))
            teachers = student.teacher_set.all()

        serializers = self.serializer_class(teachers, many=True).data
        for serializer in serializers:
            teacher = self.model.objects.get(id=serializer.get("id"))
            user_serializer = UserSerializer(teacher.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            school_serializer = SchoolSerializer(teacher.school).data
            school_serializer["name"] = UserSerializer(teacher.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(teacher.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
            serializer["students"] = teacher.students.count()

        if request.query_params.get("id", None) is not None:
            teacher = self.model.objects.get(id=request.query_params.get("id"))
            serializer = self.serializer_class(teacher).data
            user_serializer = UserSerializer(teacher.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            school_serializer = SchoolSerializer(teacher.school).data
            school_serializer["name"] = UserSerializer(teacher.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(teacher.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
            serializer["students"] = StudentSerializer(
                teacher.students.all(), many=True
            ).data
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            teacher = self.model.objects.get(id=request.query_params.get("id"))
            if request.data.get("school", None) is not None:
                teacher.school = School.objects.get(id=request.data.get("school"))
            if request.data.get("subject[]", None) is not None:
                teacher.subject = request.data.getlist("subject[]")
            if request.data.get("gender", None) is not None:
                teacher.gender = request.data.get("gender")
            teacher.save()

            user = teacher.user
            if request.data.get("email", None) is not None:
                user.email = request.data.get("email")
            if request.data.get("password", None) is not None:
                user.set_password(request.data.get("password"))
            if request.data.get("name", None) is not None:
                user.name = request.data.get("name")
            if request.FILES.get("image", None) is not None:
                user.image = file_save(request.FILES["image"])
            user.save()

            if request.data.get("students[]", None) is not None:
                teacher.students.clear()
                for s_id in request.POST.getlist("students[]"):
                    student = Student.objects.get(id=s_id)
                    teacher.students.add(student)

            if request.data.get("student", None) is not None:
                student = Student.objects.get(id=request.data.student)
                teacher.students.add(student)

            return Response({"status": "success"}, status=HTTP_200_OK)

        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(
                **user_serializer.validated_data
            )
            user.save()
            data = request.data
            data["user"] = user.id
            teacher_serializer = self.serializer_class(data=data)
            if teacher_serializer.is_valid():
                teacher = self.model.objects.create(**teacher_serializer.validated_data)
                teacher.save()

                for s_id in request.POST.getlist("students[]"):
                    student = Student.objects.get(id=s_id)
                    teacher.students.add(student)
                return Response(
                    {
                        "status": "success",
                        "user": user_serializer.data,
                        "profile": teacher_serializer.data,
                    },
                    status=HTTP_201_CREATED,
                )
            return Response(teacher_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)


class SchoolView(APIView):
    model = School
    serializer_class = SchoolSerializer

    def get(self, request):
        schools = self.model.objects.all()
        serializers = self.serializer_class(schools, many=True).data
        for serializer in serializers:
            school = self.model.objects.get(id=serializer.get("id"))
            user_serializer = UserSerializer(school.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            serializer["teachers"] = school.teacher_set.count()
            serializer["students"] = school.student_set.count()
        if request.query_params.get("id", None) is not None:
            school = self.model.objects.get(id=request.query_params.get("id"))
            serializer = self.serializer_class(school).data
            user_serializer = UserSerializer(school.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            serializer["teachers"] = TeacherSerializer(
                school.teacher_set.all(), many=True
            ).data
            serializer["students"] = StudentSerializer(
                school.student_set.all(), many=True
            ).data
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            school = School.objects.get(id=request.query_params.get("id"))
            if request.data.get("level", None) is not None:
                school.level = request.data["level"]
            if request.data.get("contact", None) is not None:
                school.contact = request.data["contact"]
            if request.data.get("contact_2", None) is not None:
                school.contact_2 = request.data["contact_2"]
            if request.data.get("email", None) is not None:
                school.email = request.data["email"]
            if request.data.get("email_2", None) is not None:
                school.email_2 = request.data["email_2"]
            if request.data.get("address", None) is not None:
                school.address = request.data["address"]
            if request.data.get("extras", None) is not None:
                school.extras = request.data["extras"]
            if request.data.get("city", None) is not None:
                school.city = request.data["city"]
            if request.data.get("state", None) is not None:
                school.state = request.data["state"]
            if request.data.get("country", None) is not None:
                school.country = request.data["country"]
            if request.data.get("zipcode", None) is not None:
                school.zipcode = request.data["zipcode"]
            school.save()

            user = school.user
            if request.data.get("email", None) is not None:
                user.email = request.data["email"]
            if request.data.get("password", None) is not None:
                user.check_password(request.data["password"])
            if request.data.get("name", None) is not None:
                user.name = request.data["name"]
            if request.FILES.get("image", None) is not None:
                user.image = file_save(request.FILES["image"])
            user.save()

            return Response({"status": "success"}, status=HTTP_200_OK)

        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(
                **user_serializer.validated_data
            )
            data = request.data
            data["user"] = user.id
            school_serializer = self.serializer_class(data=data)
            if school_serializer.is_valid():
                school = self.model.objects.create(**school_serializer.validated_data)
                school.save()
                return Response(
                    {
                        "status": "success",
                    },
                    status=HTTP_201_CREATED,
                )
            return Response(school_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)


class StudentView(APIView):
    model = Student
    serializer_class = StudentSerializer

    def get(self, request):
        students = Student.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            students = school.student_set.all()
        if request.query_params.get("teacher", None) is not None:
            teacher = Teacher.objects.get(id=request.query_params.get("teacher"))
            students = teacher.students
        if request.query_params.get("parent", None) is not None:
            parent = Parent.objects.get(id=request.query_params.get("parent"))
            students = parent.students
        serializers = StudentSerializer(students, many=True).data
        for serializer in serializers:
            student = self.model.objects.get(id=serializer.get("id"))
            user_serializer = UserSerializer(student.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            goal_serializers = GoalSerializer(student.goal_set.all(), many=True).data
            for goal_serializer in goal_serializers:
                goal = Goal.objects.get(id=goal_serializer.get("id"))
                goal_serializer["name"] = goal.goal.name
                goal_serializer["type"] = goal.goal.type
            serializer["goals"] = goal_serializers
            serializer["teachers"] = student.teacher_set.count()
            serializer["parents"] = student.parent_set.count()
            school_serializer = SchoolSerializer(student.school).data
            school_serializer["name"] = UserSerializer(student.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(student.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
        if request.query_params.get("id", None) is not None:
            student = Student.objects.get(id=request.query_params.get("id"))
            goal_serializers = GoalSerializer(student.goal_set.all(), many=True).data
            for goal_serializer in goal_serializers:
                goal = Goal.objects.get(id=goal_serializer.get("id"))
                goal_serializer["name"] = goal.goal.name
                goal_serializer["type"] = goal.goal.type

            serializer = StudentSerializer(student).data
            user_serializer = UserSerializer(student.user).data
            serializer["name"] = user_serializer.get("name")
            serializer["email"] = user_serializer.get("email")
            serializer["image"] = user_serializer.get("image")
            serializer["last_login"] = user_serializer.get("last_login")
            serializer["teachers"] = TeacherSerializer(
                student.teacher_set.all(), many=True
            ).data
            serializer["parents"] = StudentSerializer(
                student.parent_set.all(), many=True
            ).data
            school_serializer = SchoolSerializer(student.school).data
            school_serializer["name"] = UserSerializer(student.school.user).data.get(
                "name"
            )
            school_serializer["image"] = UserSerializer(student.school.user).data.get(
                "image"
            )
            serializer["school"] = school_serializer
            serializer["goals"] = goal_serializers
            serializer["rewards"] = RewardSerializer(
                student.reward_set.all(), many=True
            ).data

            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            student = Student.objects.get(id=request.query_params.get("id"))
            if request.data.get("grade", None) is not None:
                student.grade = request.data.get("grade")
            if request.data.get("gender", None) is not None:
                student.gender = request.data.get("gender")
            if request.data.get("athlete", None) is not None:
                student.athlete = request.data.get("athlete") == "true"
            if request.data.get("college_bound", None) is not None:
                student.college_bound = request.data.get("college_bound") == "true"
            if request.data.get("workforce_bound", None) is not None:
                student.workforce_bound = request.data.get("workforce_bound") == "true"
            if request.data.get("school", None) is not None:
                student.school = School.objects.get(id=request.data.get("school"))
            if request.data.get("interests[]", None) is not None:
                student.interests = request.data.getlist("interests[]")
            if request.data.get("teachers[]", None) is not None:
                student.teacher_set.clear()
                for t_id in request.data.getlist("teachers[]"):
                    teacher = Teacher.objects.get(id=t_id)
                    teacher.students.add(student)
            student.save()
            user = student.user
            if request.data.get("name", None) is not None:
                user.name = request.data.get("name")
            if request.FILES.get("image", None) is not None:
                user.image = file_save(request.FILES["image"])
            if request.data.get("email", None) is not None:
                user.email = request.data["email"]
            if request.data.get("password", None) is not None:
                user.check_password(request.data["password"])
            user.save()
            return Response({"status": "success"}, status=HTTP_200_OK)

        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(
                **user_serializer.validated_data
            )

            data = request.data
            data["user"] = user.id
            student_serializer = self.serializer_class(data=data)
            if student_serializer.is_valid():
                student = Student.objects.create(**student_serializer.validated_data)
                student.save()
                for t_id in request.POST.getlist("teachers[]"):
                    teacher = Teacher.objects.get(id=t_id)
                    teacher.students.add(student)
                return Response(
                    {
                        "status": "success",
                    },
                    status=HTTP_201_CREATED,
                )
            return Response(student_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)


class RewardView(APIView):
    model = Reward
    serializer_class = RewardSerializer

    def get(self, request):
        if request.query_params.get("id", None) is not None:
            reward = self.model.objects.get(id=request.query_params.get("id"))
            serializer = self.serializer_class(reward).data
            if request.query_params.get("school", None) is None:
                serializer["schools"] = SchoolSerializer(reward.schools, many=True).data
                serializer["students"] = StudentSerializer(
                    reward.students.all(), many=True
                ).data
            else:
                serializer["students"] = StudentSerializer(
                    reward.students.filter(school=request.query_params.get(school)),
                    many=True,
                ).data
            return Response(serializer, status=HTTP_200_OK)

        rewards = self.model.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            rewards = school.reward_set.all()
        if request.query_params.get("student", None) is not None:
            student = Student.objects.get(id=request.query_params.get("student"))
            rewards = student.reward_set.all()
        serializers = self.serializer_class(rewards, many=True).data
        for serializer in serializers:
            reward = self.model.objects.get(id=serializer.get("id"))
            if request.query_params.get("school", None) is None:
                serializer["schools"] = SchoolSerializer(reward.schools, many=True).data
                serializer["students"] = reward.students.count()
            else:
                serializer["students"] = reward.students.filter(
                    school=request.query_params.get(school)
                ).count()
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            reward = self.model.objects.get(id=request.query_params.get("id"))
            if request.data.get("schools[]", None) is not None:
                reward.schools.clear()
                for item in request.data.getlist("schools[]"):
                    school = School.objects.get(id=item)
                    reward.schools.add(school)
            if request.data.get("students[]", None) is not None:
                reward.students.clear()
                for item in request.data.getlist("students[]"):
                    student = Student.objects.get(id=item)
                    reward.students.add(student)
            if request.data.get("student", None) is not None:
                student = Student.objects.get(id=request.data.get("student"))
                reward.students.add(student)
            if request.FILES.get("image", None) is not None:
                reward.image = file_save(request.FILES["image"])
            if request.data.get("url", None) is not None:
                reward.url = request.data.get("url")
            if request.data.get("title", None) is not None:
                reward.title = request.data.get("title")
            if request.data.get("coin", None) is not None:
                reward.coin = request.data.get("coin")
            reward.save()
            return Response({"status": "success"}, status=HTTP_200_OK)
        if request.query_params.get("student", None) is not None:
            student = Student.objects.get(id=request.query_params.get("student"))
            if request.data.get("select", None) is not None:
                reward = Reward.objects.get(id=request.data.get("select"))
                reward.students.add(student)
                reward.save()
                student.coin = student.coin - reward.coin
                student.save()
            return Response({"status": "success"}, status=HTTP_200_OK)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            reward = self.model.objects.create(**serializer.validated_data)
            reward.save()
            for school_id in request.data.getlist("schools[]"):
                school = School.objects.get(id=school_id)
                reward.schools.add(school)
            for student_id in request.data.getlist("students[]"):
                student = Student.objects.get(id=student_id)
                reward.students.add(student)
            return Response({"status": "success"}, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class GoalsView(APIView):
    def get(self, request):
        goals = Goals.objects.all()
        if request.query_params.get("user") is not None:
            goals = Goals.objects.filter(reporter=request.query_params.get("user"))
        serializer = GoalsSerializer(goals, many=True).data
        return Response(serializer, status=HTTP_200_OK)


class GoalView(APIView):
    def get(self, request):
        if request.query_params.get("id", None) is not None:
            goal = Goal.objects.get(id=request.query_params.get("id"))
            serializer = GoalSerializer(goal).data
            serializer["name"] = goal.goal.name
            serializer["responses"] = goal.goal.responses
            serializer["type"] = goal.goal.type
            student_serializer = StudentSerializer(goal.student).data
            student_serializer["name"] = UserSerializer(goal.student.user).data.get(
                "name"
            )
            student_serializer["image"] = UserSerializer(goal.student.user).data.get(
                "image"
            )
            student_serializer["email"] = UserSerializer(goal.student.user).data.get(
                "email"
            )
            serializer["student"] = student_serializer
            serializer["records"] = RecordSerializer(
                goal.record_set.all(), many=True
            ).data
            return Response(serializer, status=HTTP_200_OK)
        goals = Goal.objects.all()
        if request.query_params.get("student", None) is not None:
            goals = Goal.objects.filter(student=request.query_params.get("student"))
        if request.query_params.get("user", None) is not None:
            goals = Goal.objects.filter(reporter=request.query_params.get("user"))

        serializers = GoalSerializer(goals, many=True).data
        for serializer in serializers:
            goal = Goal.objects.get(id=serializer.get("id"))
            serializer["name"] = goal.goal.name
            serializer["responses"] = goal.goal.responses
            serializer["type"] = goal.goal.type
            serializer["records"] = RecordSerializer(
                goal.record_set.all(), many=True
            ).data
            student_serializer = StudentSerializer(goal.student).data
            user_serializer = UserSerializer(goal.student.user).data
            student_serializer["name"] = user_serializer.get("name")
            student_serializer["image"] = user_serializer.get("image")
            student_serializer["email"] = user_serializer.get("email")
            student_serializer["last_login"] = user_serializer.get("last_login")
            serializer["student"] = student_serializer
            if goal.goal.type == "Parent":
                serializer["parent"] = ParentSerializer(goal.reporter.parent).data
            else:
                serializer["teacher"] = TeacherSerializer(goal.reporter.teacher).data
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get("id", None) is not None:
            goal = Goal.objects.get(id=request.query_params.get("id"))
            goal_2 = goal.goal
            if request.data.get("start_date", None) is not None:
                goal.start_date = request.data.get("start_date")
            if request.data.get("end_date", None) is not None:
                goal.end_date = request.data.get("end_date")
            if request.data.get("score", None) is not None:
                goal.score = float(request.data.get("score"))
            if request.data.get("student", None) is not None:
                goal.student = Student.objects.get(id=request.data.get("student"))
            if request.data.get("goal", None) is not None:
                goal.goal = Goals.objects.get(id=request.data.get("goal"))
            if request.data.get("status", None) is not None:
                goal.status = request.data.get("status")
            if request.data.get("view_status", None) is not None:
                goal.status = request.data.get("view_status")
            if request.data.get("type", None) is not None:
                goal_2.type = request.data.get("type")
            if request.data.get("reporter", None) is not None:
                goal.reporter = CustomUser.objects.get(id=request.data.get("reporter"))
                goal_2.reporter = CustomUser.objects.get(
                    id=request.data.get("reporter")
                )
            goal.save()
            if request.data.get("goal", None) is None:
                if request.data.get("name", None) is not None:
                    goal_2.name = request.data.get("name")
                if request.data.get("responses", None) is not None:
                    goal_2.responses = request.data.get("responses")
            goal_2.save()
            return Response({"status": "success"}, status=HTTP_200_OK)

        if request.data.get("goal", None) is None:
            goal_serializer = GoalsSerializer(data=request.data)
            if goal_serializer.is_valid():
                goal = Goals.objects.create(**goal_serializer.validated_data)
                goal.save()
                print(goal.id)
                data = request.data
                request.data._mutable = True
                data["goal"] = goal.id
                serializer = GoalSerializer(data=request.data)
                if serializer.is_valid():
                    goal = Goal.objects.create(**serializer.validated_data)
                    goal.save()
                    return Response({"status": "success"}, status=HTTP_200_OK)
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
            return Response(goal_serializer.errors, status=HTTP_400_BAD_REQUEST)

        serializer = GoalsSerializer(data=request.data)
        if serializer.is_valid():
            goals = Goals.objects.create(**serializer.validated_data)
            goals.save()
            data = request.data
            data["goal"] = goals.id
            goal_serializer = GoalSerializer(data=request.data)
            if goal_serializer.is_valid():
                goal = Goal.objects.create(**goal_serializer.validated_data)
                goal.save()
                return Response({"status": "success"}, status=HTTP_200_OK)
            return Response(goal_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class RecordView(APIView):
    def get(self, request):
        if request.query_params.get("goal", None) is not None:
            records = Record.objects.filter(goal=request.query_params.get("goal"))
            serializers = RecordSerializer(records, many=True)
            return Response(serializers.data, status=HTTP_200_OK)
        if request.query_params.get("id", None) is not None:
            serializer = RecordSerializer(
                Record.objects.get(id=request.query_params.get("id"))
            )
            return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        if request.data.get("id", None) is not None:
            record = Record.objects.get(id=request.data.get("id"))
            if request.data.get("score", None) is not None:
                record.score = request.data.get("score")
            if request.data.get("note", None) is not None:
                record.note = request.data.get("note")
            record.save()
            return Response({"status": "success"}, status=HTTP_200_OK)
        serializer = RecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.query_params.get("id", None) is not None:
            record = Record.objects.get(id=request.query_params.get("id"))
            record.delete()
            return Response({"status": "success"}, status=HTTP_200_OK)


class CompleteView(APIView):
    def get(self, request):
        if request.query_params.get("goal", None) is not None:
            complete = Complete.objects.get(goal=request.query_params.get("goal"))
            serializer = CompleteSearializer(complete)
            return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        serializer = CompleteSearializer(data=request.data)
        if serializer.is_valid():
            complete = Complete.objects.create(**serializer.validated_data)
            complete.save()
            goal = complete.goal
            goal.status = "completed"
            goal.save()
            student = goal.student
            student.coin = student.coin + serializer.get("coin")
            student.save()
            return Response(serializer, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

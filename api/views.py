from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import update_last_login
from .serializers import UserSerializer, TokenObtainPairSerializer, PasswordSerializer, StudentSerializer, TeacherSerializer, ParentSerializer, SchoolSerializer, RewardSerializer
from .models import Teacher, Student, Parent, School, Reward

class SignUpView(APIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = get_user_model().objects.create_user(**serializer.validated_data)
            role = user.role
            if role == 'parent':
                Parent.objects.create(user=user)
            elif role == 'teacher':
                Teacher.objects.create(user=user)
            elif role == 'student':
                Student.objects.create(user=user)
            
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
            user = get_user_model().objects.get(email = request.data['email'])
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
            email = serializer.data['email']
            user = self.get_object(email)
            password = serializer.data['password']
            if user.check_password(password):
                return Response({
                    'status': HTTP_400_BAD_REQUEST,
                    "message": "It should be different from your last password."
                })
            user.set_password(password)
            user.save()
            return Response({"status": HTTP_200_OK})
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
class ProfileView(APIView):

    def get(self, request):
        user = request.user
        if request.query_params.get('id', None) is not None:
            user = get_object_or_404(get_user_model(), id=request.query_params.get('id'))
        serializer = {}
        if user.role == "school": serializer = SchoolSerializer(user.school).data
        if user.role == "teacher": serializer = TeacherSerializer(user.teacher).data
        if user.role == "student": serializer = StudentSerializer(user.student).data
        if user.role == "parent": serializer = StudentSerializer(user.parent).data
        serializer["role"] = user.role
        serializer["email"] = user.email
        return Response(serializer, status=HTTP_200_OK)
    
class UserView(APIView):

    def get(self, request):
        if request.query_params.get('id', None) is not None:
            user = get_object_or_404(get_user_model(), id=request.query_params.get('id'))
            serializer = UserSerializer(user)
            return Response({
                "status": "success",
                "user": serializer.data
            }, status=HTTP_200_OK)
        return Response(status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.query_params.get('id', None) is not None:
            user = get_object_or_404(get_user_model(), id=request.query_params.get('id'))
            user.delete()
            return Response({
                "status": "success"
            },status=HTTP_200_OK)
        return Response(status=HTTP_400_BAD_REQUEST)

class ParentView(APIView):
    serializer_class = ParentSerializer

    def get(self, request):
        parents = Parent.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            parents = school.parent_set.all()
        serializers = self.serializer_class(parents, many=True).data
        for serializer in serializers:
            user = get_user_model().objects.get(id = serializer.get("user"))
            parent = user.parent
            serializer['school'] = SchoolSerializer(parent.school).data
            serializer["students"] = StudentSerializer(parent.students, many=True).data
            serializer["last"] = user.last_login
        if request.query_params.get('id', None) is not None:
            parent = Parent.objects.get(id = request.query_params.get('id'))
            serializer = self.serializer_class(parent).data
            serializer['school'] = SchoolSerializer(parent.school).data
            serializer["students"] = StudentSerializer(parent.students, many=True).data
            serializer["last"] = parent.user.last_login
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get('id', None) is not None:
            parent = Parent.objects.get(id = request.query_params.get('id'))
        
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(**user_serializer.validated_data)
            data = request.data
            data["user"] = user.id
            parent_serializer = self.serializer_class(data=data)
            if parent_serializer.is_valid():
                parent = Parent.objects.create(**parent_serializer.validated_data)
                parent.save()
                for s_id in request.POST.getlist("students[]"):
                        student = Student.objects.get(id = s_id)
                        parent.students.add(student)
                return Response({
                    "status": "success",
                    "user": user_serializer.data,
                    "profile": parent_serializer.data
                }, status=HTTP_201_CREATED)
            return Response(parent_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class TeacherView(APIView):
    serializer_class = TeacherSerializer

    def get(self, request):
        teachers = Teacher.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            teachers = school.teacher_set.all()
        serializers = TeacherSerializer(teachers, many=True).data
        for serializer in serializers:
            user = get_user_model().objects.get(id = serializer.get("user"))
            teacher = user.teacher
            serializer["school"] = SchoolSerializer(teacher.school).data
            serializer["students"] = StudentSerializer(teacher.students, many=True).data
            serializer["last"] = user.last_login

        if request.query_params.get('id', None) is not None:
            teacher = Teacher.objects.get(id = request.query_params.get('id'))
            serializer = TeacherSerializer(teacher).data
            serializer["school"] = SchoolSerializer(teacher.school).data
            serializer["students"] = StudentSerializer(teacher.students, many = True).data
            serializer["last"] = teacher.user.last_login
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)
    def post(self, request):
        if request.query_params.get('id', None) is not None:
            teacher = Teacher.objects.get(id = request.query_params.get('id'))
        
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(**user_serializer.validated_data)
            user.save()
            data = request.data
            data["user"] = user.id
            teacher_serializer = self.serializer_class(data=data)
            if teacher_serializer.is_valid():
                teacher = Teacher.objects.create(**teacher_serializer.validated_data)
                teacher.save()
                
                for s_id in request.POST.getlist("students[]"):
                    student = Student.objects.get(id = s_id)
                    teacher.students.add(student)
                return Response({
                    "status": "success",
                    "user": user_serializer.data,
                    "profile": teacher_serializer.data
                }, status=HTTP_201_CREATED)
            return Response(teacher_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)
    
class SchoolView(APIView):
    serializer_class = SchoolSerializer

    def get(self, request):
        schools = School.objects.all()
        serializers = SchoolSerializer(schools, many=True).data
        for serializer in serializers:
            user = get_user_model().objects.get(id = serializer.get("user"))
            students = user.school.student_set.all()
            teachers = user.school.teacher_set.all()
            serializer["teachers"] = TeacherSerializer(teachers, many=True).data
            serializer["students"] = StudentSerializer(students, many=True).data

        if request.query_params.get('id', None) is not None:
            school = School.objects.get(id = request.query_params.get('id'))
            user = school.user
            serializer = SchoolSerializer(school).data
            students = school.student_set.all()
            teachers = school.teacher_set.all()
            serializer["teachers"] = TeacherSerializer(teachers, many=True).data
            serializer["students"] = StudentSerializer(students, many=True).data
            
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)
        
    def post(self, request):
        if request.query_params.get('id', None) is not None:
            school = School.objects.get(id = request.query_params.get('id'))
            if request.data.get("name", None) is not None: user.name = request.data["name"]
            if request.data.get("image", None) is not None: user.image = request.data["image"]
            if request.data.get("level", None) is not None: school.level = request.data["level"]
            if request.data.get("contact", None) is not None:school.contact = request.data["contact"]
            if request.data.get("contact_2", None) is not None:school.contact_2 = request.data["contact_2"]
            if request.data.get("email", None) is not None:school.email = request.data["email"]
            if request.data.get("email_2", None) is not None:school.email = request.data["email_2"]
            if request.data.get("address", None) is not None:school.email = request.data["address"]
            if request.data.get("extras", None) is not None:school.extras = request.data["extras"]
            if request.data.get("city", None) is not None:school.city = request.data["city"]
            if request.data.get("state", None) is not None:school.state = request.data["state"]
            if request.data.get("country", None) is not None:school.country = request.data["country"]            
            if request.data.get("zipcode", None) is not None:school.zipcode = request.data["zipcode"]
            school.save()
            user = school.user
            if request.data.get("email", None) is not None: user.email = request.data["email"]
            if request.data.get("password", None) is not None: user.check_password(request.data["password"])
            user.save()            
            return Response(status=HTTP_200_OK)
        
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(**user_serializer.validated_data)
            data = request.data
            data["user"] = user.id
            school_serializer = self.serializer_class(data=data)
            if school_serializer.is_valid():
                school = School.objects.create(**school_serializer.validated_data)
                school.save()
                return Response({
                    "status": "success",
                }, status=HTTP_201_CREATED)
            return Response(school_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class StudentView(APIView):
    serializer_class = StudentSerializer

    def get(self, request):
        students = Student.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            students = school.student_set.all()
        if request.query_params.get("teacher", None) is not None:
            teacher = Teacher.objects.get(id=request.query_params.get("teacher"))
            students = teacher.students
        serializers = StudentSerializer(students, many=True).data
        for serializer in serializers:
            user = get_user_model().objects.get(id = serializer.get("user"))
            serializer["teachers"] = TeacherSerializer(user.student.teacher_set.all(), many=True).data
            serializer["last"] = user.last_login
            serializer["parents"] = ParentSerializer(user.student.parent_set.all(), many=True).data
            serializer["school"] = SchoolSerializer(user.student.school).data

        if request.query_params.get('id', None) is not None:
            student = Student.objects.get(id = request.query_params.get('id'))
            user = student.user
            serializer = StudentSerializer(student).data
            serializer["teachers"] = TeacherSerializer(student.teacher_set.all(), many=True).data
            serializer["parents"] = StudentSerializer(student.parent_set.all(), many=True).data
            serializer["last"] = student.user.last_login
            serializer["school"] = SchoolSerializer(student.school).data
            
            return Response(serializer, status=HTTP_200_OK)
        return Response(serializers, status=HTTP_200_OK)
        
    def post(self, request):
        if request.query_params.get('id', None) is not None:
            student = Student.objects.get(id = request.query_params.get('id'))
            if request.data.get("name", None) is not None: student.name = request.data.get("name")
            if request.data.get("image", None) is not None: student.image = request.data.get("image")
            if request.data.get("grade", None) is not None: student.grade = request.data.get("grade")
            if request.data.get("gender", None) is not None: student.gender = request.data.get("gender")
            if request.data.get("athlete", None) is not None: student.athlete = request.data.get("athlete")
            if request.data.get("college_bound", None) is not None: student.college_bound = request.data.get("college_bound")
            if request.data.get("workforce_bound", None) is not None: student.workforce_bound = request.data.get("workforce_bound")
            if request.data.get("school", None) is not None: student.school = request.data.get("school")
            if request.data.get("interests", None) is not None: student.interests = request.data.get("interests")
            student.save()
            user = student.user
            if request.data.get("email", None) is not None: user.email = request.data["email"]
            if request.data.get("password", None) is not None: user.check_password(request.data["password"])
            user.save()            
            return Response({
                "status": "success"
            },status=HTTP_200_OK)
        
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = get_user_model().objects.create_user(**user_serializer.validated_data)
            
            data = request.data
            data["user"] = user.id
            student_serializer = self.serializer_class(data=data)
            if student_serializer.is_valid():
                student = Student.objects.create(**student_serializer.validated_data)
                student.save()
                for t_id in request.POST.getlist("teachers[]"):
                    teacher = Teacher.objects.get(id=t_id)
                    print(teacher)
                    teacher.students.add(student)
                return Response({
                    "status": "success",
                }, status=HTTP_201_CREATED)
            return Response(student_serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class RewardView(APIView):
    model = Reward
    serializer_class = RewardSerializer

    def get(self, request):
        if request.query_params.get('id', None) is not None:
            reward = self.model.objects.get(id=request.query_params.get('id'))
            serializer = self.serializer_class(reward).data
            if request.query_params.get("school", None) is None:
                serializer["schools"] = SchoolSerializer(reward.schools, many=True).data
                serializer["students"] = StudentSerializer(reward.students, many=True).data
            else:
                serializer["students"] = StudentSerializer(reward.students.filter(school=request.query_params.get(school)), many=True).data
            return Response(serializer, status=HTTP_200_OK)

        rewards = self.model.objects.all()
        if request.query_params.get("school", None) is not None:
            school = School.objects.get(id=request.query_params.get("school"))
            rewards = school.reward_set.all()
        serializers = self.serializer_class(rewards, many=True).data
        for serializer in serializers:
            reward = self.model.objects.get(id = serializer.get("id"))
            if request.query_params.get("school", None) is None:
                serializer["schools"] = SchoolSerializer(reward.schools, many=True).data
                serializer["students"] = StudentSerializer(reward.students, many=True).data
            else:
                serializer["students"] = StudentSerializer(reward.students.filter(school=request.query_params.get(school)), many=True).data
        return Response(serializers, status=HTTP_200_OK)

    def post(self, request):
        if request.query_params.get('id', None) is not None:
            reward = self.model.objects.get(id = request.query_params.get('id'))
            if(request.data.get("schools[]", None) is not None):
                reward.schools.clear()
                for item in request.POST.getlist("schools[]"):
                    school = School.objects.get(id=item)
                    reward.schools.add(school)
            if(request.data.get("students[]", None) is not None):
                reward.students.clear()
                for item in request.POST.getlist("students[]"):
                    student = School.objects.get(id=item)
                    reward.students.add(student)
            return Response({
                "status": "success"
            }, status=HTTP_200_OK)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            reward = self.model.objects.create(**serializer.validated_data)
            reward.save()
            for school_id in request.POST.getlist("schools[]"):
                school = School.objects.get(id=school_id)
                reward.schools.add(school)
            return Response({
                "status": "success"
            }, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
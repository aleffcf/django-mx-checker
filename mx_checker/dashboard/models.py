from django.db import models

# Create your models here.
class Domain(models.Model):
    domain_name = models.CharField(max_length=100)

    def __str__(self):
        return self.domain_name

class Record(models.Model):
    mx_extry = models.CharField(max_length=100)
    domain_name = models.ForeignKey(Domain, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(f"{domain_name} - {mx_extry}")
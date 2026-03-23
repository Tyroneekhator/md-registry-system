# We import the 'models' module to define our database structure
from django.db import models

# We define the Departments class to represent the 'Departments' table 
class Departments(models.Model):
    # 'DepartmentID' is the Primary Key (PK) as an integer.
    # AutoField ensures it increments automatically in SQL Server.
    DepartmentID = models.AutoField(primary_key=True)

    # 'DepartmentName' matches your nvarchar(200) constraint.
    # null=False ensures every department must have a name defined.
    DepartmentName = models.CharField(max_length=200, null=False)
    
    Description = models.CharField(max_length=500, null=True, blank=True)
    # 'CreatedAt' uses DateTimeField to match 'datetime2(7)'.
    # null=True allows this to be empty if the timestamp isn't auto-generated.
    CreatedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        # This explicitly maps this model to the 'Departments' table in MDRegistryDB 
        db_table = 'Departments'
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    # Returns the name of the department when referenced in the app
    def __str__(self):
        return self.DepartmentName
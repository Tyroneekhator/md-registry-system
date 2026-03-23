from django.db import models

# We import the 'models' module from Django to define our database structure
from django.db import models

# [cite_start]We define the Users class, which represents the 'Users' table in your database [cite: 1]
class Users(models.Model):
    # 'UserID' is the Primary Key (PK). 
    # In SQL Server it is an 'int', so we use AutoField or IntegerField.
    # primary_key=True prevents the system from creating its own 'id' column.
    UserID = models.AutoField(primary_key=True)

    # 'Username' is a text field with a 150-character limit.
    # null=False ensures this column cannot be empty in the database.
    Username = models.CharField(max_length=150, null=False)

    # 'PasswordHash' stores the encrypted password.
    # We use a 255-character limit to accommodate long hash strings.
    PasswordHash = models.CharField(max_length=255, null=False)

    # 'IsActive' maps to the 'bit' type in SQL Server.
    # In Python, this is represented as a Boolean (True/False).
    IsActive = models.BooleanField(default=True, null=False)

    # 'CreatedAt' uses DateTimeField to match the 'datetime2' type.
    # null=True allows the field to be empty if the timestamp isn't provided.
    CreatedAt = models.DateTimeField(null=True, blank=True)

    # 'LastLoginAt' tracks the user's most recent access.
    # blank=True allows this to be empty in forms/applications.
    LastLoginAt = models.DateTimeField(null=True, blank=True)
    
    FullName = models.CharField(max_length=255, null=True, blank=True)
    Email = models.CharField(max_length=255, null=True, blank=True)
    UpdatedAt = models.DateTimeField(null=True, blank=True)

    # The 'Meta' class provides extra information about the model
    class Meta:
        # [cite_start]This tells the application to look for a table named 'Users' [cite: 1]
        # in your 'MDRegistryDB' rather than generating a new name.
        db_table = 'Users'
        verbose_name = "User"
        verbose_name_plural = "Users"
        
    # This function defines how the User appears in the admin panel or logs
    def __str__(self):
        return self.Username


# (Continuing in apps/accounts/models.py)

# We define the Groups class to represent the 'Groups' table from your database list
class Groups(models.Model):
    # 'GroupID' is the Primary Key (PK).
    # We use AutoField so the database handles the unique ID generation automatically.
    GroupID = models.AutoField(primary_key=True)

    # 'GroupName' stores the name of the group (e.g., 'Administrators' or 'Staff').
    # max_length=50 matches your SQL Server nvarchar(50) constraint.
    # null=False ensures every group must have a name.
    GroupName = models.CharField(max_length=50, null=False)

    # The 'Meta' class links this Python code to your actual SQL table
    class Meta:
        # This tells the framework to connect to the 'Groups' table in MDRegistryDB
        db_table = 'Groups'
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    # This helps identify the object by its name when viewing it in a list
    def __str__(self):
        return self.GroupName


# (Continuing in apps/accounts/models.py)

# We define the Permissions class to represent the 'Permissions' table
class Permissions(models.Model):
    # 'PermissionID' is the Primary Key (PK).
    # Using AutoField ensures SQL Server handles the incrementing ID.
    PermissionID = models.AutoField(primary_key=True)

    # 'PermissionCode' is a unique string used by the code to check for access.
    # max_length=80 matches your nvarchar(80) requirement.
    # null=False ensures every permission has a code.
    PermissionCode = models.CharField(max_length=80, null=False)

    # 'Description' provides a human-readable explanation of what the permission does.
    # max_length=300 matches nvarchar(300).
    # null=True and blank=True allow this field to be optional.
    Description = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        # Connects this class specifically to the 'Permissions' table in your DB 
        db_table = 'Permissions'
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.PermissionCode
    


# (Continuing in apps/accounts/models.py)

# We define the UserGroups class to link Users and Groups
class UserGroups(models.Model):
    UserGroupID = models.AutoField(primary_key=True)

    UserID = models.ForeignKey(
        'Users',
        on_delete=models.CASCADE,
        db_column='UserID'
    )

    GroupID = models.ForeignKey(
        'Groups',
        on_delete=models.CASCADE,
        db_column='GroupID'
    )

    class Meta:
        db_table = 'UserGroups'
        verbose_name = "UserGroup"
        verbose_name_plural = "UserGroups"
        unique_together = (('UserID', 'GroupID'),)

    def __str__(self):
        return f"{self.UserID.Username} in {self.GroupID.GroupName}"    

# (Continuing in apps/accounts/models.py)

# We define the GroupPermissions class to link the entities together
class GroupPermissions(models.Model):
    GroupPermissionID = models.AutoField(primary_key=True)

    GroupID = models.ForeignKey(
        Groups,
        on_delete=models.CASCADE,
        db_column="GroupID",
    )

    PermissionID = models.ForeignKey(
        Permissions,
        on_delete=models.CASCADE,
        db_column="PermissionID",
    )

    class Meta:
        db_table = "GroupPermissions"
        unique_together = (("GroupID", "PermissionID"),)
        verbose_name = "Group Permission"
        verbose_name_plural = "Group Permissions"

    def __str__(self):
        return f"{self.GroupID.GroupName} - {self.PermissionID.PermissionCode}"
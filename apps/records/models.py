# We import models from Django and also reference the models we created earlier
from django.db import models
from apps.organization.models import Departments
from apps.accounts.models import Users


class ExternalCompanyNames(models.Model):
    ExternalCompanyNameID = models.AutoField(primary_key=True)
    CompanyName = models.CharField(max_length=255, unique=True)
    Description = models.CharField(max_length=500, null=True, blank=True)
    CreatedAt = models.DateTimeField(null=True, blank=True)
    UpdatedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ExternalCompanyNames"
        verbose_name = "External Company Name"
        verbose_name_plural = "External Company Names"
        ordering = ["CompanyName"]

    def __str__(self):
        return self.CompanyName
    
    
class Records(models.Model):
    # 'RecordID' is the primary key.
    RecordID = models.AutoField(primary_key=True)

    # 'InvoiceNumber' is a required integer.
    InvoiceNumber = models.IntegerField(null=False)

    # 'MessengerName' and 'Subject' have specific character limits.
    MessengerName = models.CharField(max_length=200, null=False)
    Subject = models.CharField(max_length=300, null=False)

    # 'Description' has a MaxLength of -1, which means 'max' in SQL Server.
    # In Python/Django, we use TextField for unlimited or very long text.
    Description = models.TextField(null=False)

    # Core date tracking using high-precision datetime2.
    DateReceived = models.DateTimeField(null=False)

    # These fields link to the Departments table in your organization app.
    # 'IncomingDepartmentID' is mandatory.
    IncomingDepartmentID = models.ForeignKey(
        Departments, 
        on_delete=models.PROTECT, 
        null=True,
        blank=True,
        related_name='incoming_records',
        db_column='IncomingDepartmentID'
    )
    
    # 'OutgoingDepartmentID' is optional (AllowNulls=YES).
    OutgoingDepartmentID = models.ForeignKey(
        Departments, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='outgoing_records',
        db_column='OutgoingDepartmentID'
    )
    
    ExternalDocument = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        default="No"
    )

    ExternalCompanyName = models.ForeignKey(
        ExternalCompanyNames,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="records",
        db_column="ExternalCompanyNameID",
    )

    # Status and tracking fields.
    DateDispatched = models.DateTimeField(null=True, blank=True)
    Returned = models.CharField(max_length=30, null=True, blank=True)
    DateReturned = models.DateField(null=True, blank=True)
    Status = models.CharField(max_length=30, null=False)

    # Soft delete and auditing logic.
    # 'IsDeleted' is a bit (Boolean) and allows nulls.
    IsDeleted = models.BooleanField(null=True, blank=True, default=False)
    DeletedAt = models.DateTimeField(null=True, blank=True)
    
    # Links to the Users table in your accounts app for auditing.
    DeletedByUserID = models.ForeignKey(
        Users, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='records_deleted',
        db_column='DeletedByUserID'
    )
    
    RestoredAt = models.DateTimeField(null=True, blank=True)
    RestoredByUserID = models.ForeignKey(
        Users, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='records_restored',
        db_column='RestoredByUserID'
    )

    # Standard timestamps.
    CreatedAt = models.DateTimeField(null=True, blank=True)
    UpdatedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Maps explicitly to the 'Records' table.
        db_table = 'Records'
        verbose_name = "Record"
        verbose_name_plural = "Records"

    def __str__(self):
        return f"Record {self.InvoiceNumber}: {self.Subject}"
    

# (Continuing in apps/records/models.py)

class RecordAttachments(models.Model):
    # 'AttachmentID' is the Primary Key. [cite: 3]
    # We use AutoField to match the 'int' type that is not null. [cite: 3]
    AttachmentID = models.AutoField(primary_key=True)

    # 'RecordID' is a Foreign Key linking this attachment to a specific Record. [cite: 3]
    # We use the 'Records' model defined earlier in this file.
    RecordID = models.ForeignKey(
        'Records', 
        on_delete=models.CASCADE, 
        db_column='RecordID',
        related_name='attachments'
    )

    # 'FilePath' stores the location of the file on the server. [cite: 3]
    # MaxLength 500 matches your nvarchar(500) constraint. [cite: 3]
    FilePath = models.CharField(max_length=500, null=False)

    # 'OriginalFileName' keeps the name of the file as it was uploaded. [cite: 3]
    # MaxLength 260 matches the standard Windows path limit. [cite: 3]
    OriginalFileName = models.CharField(max_length=260, null=False)

    # 'UploadedByUserID' links to the Users model in the accounts app. [cite: 3]
    # This tracks who added the file to the system.
    UploadedByUserID = models.ForeignKey(
        'accounts.Users', 
        on_delete=models.PROTECT, 
        db_column='UploadedByUserID'
    )

    # 'UploadedAt' tracks the time of upload using high-precision datetime2. [cite: 3]
    # It allows nulls according to your schema. [cite: 3]
    UploadedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Maps explicitly to the 'RecordAttachments' table in MDRegistryDB.
        db_table = 'RecordAttachments'
        
        verbose_name = "RecordAttachment"
        verbose_name_plural = "RecordAttachments"

    def __str__(self):
        return f"Attachment for Record {self.RecordID_id}: {self.OriginalFileName}"
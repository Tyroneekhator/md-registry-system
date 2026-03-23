# We import models from Django and reference the foreign apps
from django.db import models
from apps.accounts.models import Users
from apps.records.models import Records

class ActionRequests(models.Model):
    # [cite_start]'RequestID' is the Primary Key for this workflow entry[cite: 3].
    RequestID = models.AutoField(primary_key=True)

    # [cite_start]'RequestType' defines the nature of the action (e.g., 'Delete', 'Edit')[cite: 3].
    # [cite_start]MaxLength 40 matches your nvarchar(40) constraint[cite: 3].
    RequestType = models.CharField(max_length=40, null=False)

    # [cite_start]'TargetRecordID' links this request to a specific Record[cite: 3].
    # [cite_start]AllowNulls=YES means a request might not be tied to a specific record[cite: 3].
    TargetRecordID = models.ForeignKey(
        Records, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='TargetRecordID'
    )

    # [cite_start]'RequestedByUserID' tracks the user who initiated the request[cite: 3].
    # [cite_start]This is a mandatory field (AllowNulls=NO)[cite: 3].
    RequestedByUserID = models.ForeignKey(
        Users, 
        on_delete=models.PROTECT, 
        related_name='requests_made', 
        db_column='RequestedByUserID'
    )

    # [cite_start]'RequestDetails' uses nvarchar(-1) in SQL, so we use TextField in Python[cite: 3].
    # [cite_start]This allows for long, detailed explanations of the request[cite: 3].
    RequestDetails = models.TextField(null=True, blank=True)

    # [cite_start]'Status' tracks where the request is in the lifecycle (e.g., 'Pending', 'Approved')[cite: 3].
    Status = models.CharField(max_length=20, null=True, blank=True)

    # [cite_start]'ReviewedByUserID' links to the User who approved or rejected the request[cite: 3].
    ReviewedByUserID = models.ForeignKey(
        Users, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='requests_reviewed', 
        db_column='ReviewedByUserID'
    )

    # [cite_start]Timestamps for auditing the workflow[cite: 3].
    ReviewedAt = models.DateTimeField(null=True, blank=True)
    CreatedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        # [cite_start]Maps to the 'ActionRequests' table in MDRegistryDB[cite: 3].
        db_table = 'ActionRequests'
        verbose_name = "ActionRequest"
        verbose_name_plural = "ActionRequests"

    def __str__(self):
        return f"{self.RequestType} Request #{self.RequestID} ({self.Status})"
    


# (Continuing in apps/workflow/models.py)

class AuditLogs(models.Model):
    # 'AuditLogID' is the primary key for the log entry.
    AuditLogID = models.AutoField(primary_key=True)

    # 'EventType' describes what happened (e.g., 'Update', 'Login', 'Export').
    # MaxLength 60 matches your nvarchar(60) constraint.
    EventType = models.CharField(max_length=60, null=False)

    # 'ActorUserID' links to the User who performed the action.
    # AllowNulls=YES because some events might be system-automated.
    ActorUserID = models.ForeignKey(
        'accounts.Users', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='ActorUserID',
        related_name='actions_performed'
    )

    # 'TargetRecordID' links to the specific record affected by the event.
    TargetRecordID = models.ForeignKey(
        'records.Records', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='TargetRecordID'
    )

    # 'TargetRequestID' links to an ActionRequest if applicable.
    TargetRequestID = models.ForeignKey(
        'ActionRequests', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='TargetRequestID'
    )

    # 'EventTime' captures exactly when the action occurred.
    EventTime = models.DateTimeField(null=True, blank=True)

    # 'Details' stores the specifics of the change (nvarchar max).
    # We use TextField for unlimited text data.
    Details = models.TextField(null=True, blank=True)

    # Soft Delete Audit Fields:
    # Allows the system to track if a log entry itself was removed.
    IsDeleted = models.BooleanField(null=True, blank=True, default=False) 
    DeletedAt = models.DateTimeField(null=True, blank=True) 
    DeletedByUserID = models.ForeignKey(
        'accounts.Users', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='DeletedByUserID',
        related_name='logs_deleted'
    ) 
    
    RestoredAt = models.DateTimeField(null=True, blank=True) 
    RestoredByUserID = models.ForeignKey(
        'accounts.Users', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='RestoredByUserID',
        related_name='logs_restored'
    ) 

    class Meta:
        # Maps explicitly to the 'AuditLogs' table.
        db_table = 'AuditLogs'
        verbose_name = "AuditLog"
        verbose_name_plural = "AuditLogs"

    def __str__(self):
        return f"{self.EventType} at {self.EventTime} by User {self.ActorUserID_id}"
"""
CivicPro Admin Configuration
Customized Django Admin panel for the Worker Hiring Platform.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, HireRequest, Review, WorkerAvailabilityLog,
    EmergencyCall, SupportConversation, SupportMessage
)


# Customize Admin Site Header
admin.site.site_header = "⚡ CivicPro Admin"
admin.site.site_title = "CivicPro Portal"
admin.site.index_title = "Welcome to CivicPro Admin Panel"


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    fk_name = 'user'
    fields = (
        'role', 'phone', 'skill_category', 'daily_rate', 'experience_years',
        'location_name', 'latitude', 'longitude', 'is_available', 'is_verified'
    )


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_skill', 'is_active')
    list_filter = ('is_active', 'is_staff', 'profile__role', 'profile__skill_category')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def get_role(self, obj):
        try:
            role = obj.profile.role
            styles = {
                'WORKER': 'background:#faefe3; color:#9c5120; border:1px solid #ebdccb;',
                'EMPLOYER': 'background:#f5dcbf; color:#562a12; border:1px solid #dfc3a7;',
                'ADMIN': 'background:#562a12; color:#ffffff; border:1px solid #421d0a;',
            }
            style = styles.get(role, 'background:#f5f5f4; color:#57534e; border:1px solid #e7e5e4;')
            return format_html(
                '<span style="{}; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; display:inline-block;">{}</span>',
                style, role
            )
        except UserProfile.DoesNotExist:
            return 'N/A'
    get_role.short_description = 'Role'

    def get_skill(self, obj):
        try:
            return obj.profile.get_skill_category_display() or '-'
        except UserProfile.DoesNotExist:
            return '-'
    get_skill.short_description = 'Skill'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'role', 'skill_category', 'daily_rate',
        'experience_years', 'location_name', 'availability_badge', 'verified_badge'
    )
    list_filter = ('role', 'skill_category', 'is_available', 'is_verified')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location_name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['verify_workers', 'unverify_workers', 'mark_available', 'mark_busy']

    fieldsets = (
        ('User Identity', {
            'fields': ('user', 'role', 'phone')
        }),
        ('Professional Details', {
            'fields': ('skill_category', 'daily_rate', 'experience_years', 'bio')
        }),
        ('Location', {
            'fields': ('location_name', 'latitude', 'longitude')
        }),
        ('Status', {
            'fields': ('is_available', 'is_verified', 'profile_photo')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def availability_badge(self, obj):
        if obj.is_available:
            return mark_safe('<span style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">✓ Available</span>')
        return mark_safe('<span style="background:#fef2f2; color:#dc2626; border:1px solid #fecaca; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">✗ Busy</span>')
    availability_badge.short_description = 'Status'

    def verified_badge(self, obj):
        if obj.is_verified:
            return mark_safe('<span style="background:#faefe3; color:#9c5120; border:1px solid #ebdccb; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">✓ Verified</span>')
        return mark_safe('<span style="background:#f5f5f4; color:#785e4f; border:1px solid #e7e5e4; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:500;">Pending</span>')
    verified_badge.short_description = 'Verification'

    def verify_workers(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} worker(s) verified successfully.")
    verify_workers.short_description = "✓ Verify selected workers"

    def unverify_workers(self, request, queryset):
        queryset.update(is_verified=False)
    unverify_workers.short_description = "✗ Remove verification"

    def mark_available(self, request, queryset):
        queryset.update(is_available=True)
    mark_available.short_description = "Mark as Available"

    def mark_busy(self, request, queryset):
        queryset.update(is_available=False)
    mark_busy.short_description = "Mark as Busy"


@admin.register(HireRequest)
class HireRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'employer', 'get_worker_name', 'work_date',
        'status_badge', 'created_at'
    )
    list_filter = ('status', 'work_date', 'created_at')
    search_fields = ('employer__username', 'worker__user__username', 'job_description')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_completed', 'mark_accepted', 'mark_rejected']

    def get_worker_name(self, obj):
        return obj.worker.user.get_full_name() or obj.worker.user.username
    get_worker_name.short_description = 'Worker'

    def status_badge(self, obj):
        badges = {
            'PENDING': 'background:#fffbeb; color:#b45309; border:1px solid #fde68a;',
            'ACCEPTED': 'background:#ecfdf5; color:#059669; border:1px solid #a7f3d0;',
            'REJECTED': 'background:#fef2f2; color:#dc2626; border:1px solid #fecaca;',
            'COMPLETED': 'background:#faefe3; color:#9c5120; border:1px solid #ebdccb;',
        }
        style = badges.get(obj.status, 'background:#f5f5f4; color:#57534e; border:1px solid #e7e5e4;')
        return format_html(
            '<span style="{}; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">{}</span>',
            style, obj.status
        )
    status_badge.short_description = 'Status'

    def mark_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_completed.short_description = "Mark as Completed"

    def mark_accepted(self, request, queryset):
        queryset.update(status='ACCEPTED')
    mark_accepted.short_description = "Mark as Accepted"

    def mark_rejected(self, request, queryset):
        queryset.update(status='REJECTED')
    mark_rejected.short_description = "Mark as Rejected"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('employer', 'get_worker_name', 'star_display', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('employer__username', 'worker__user__username', 'comment')
    readonly_fields = ('created_at',)

    def get_worker_name(self, obj):
        return obj.worker.user.get_full_name() or obj.worker.user.username
    get_worker_name.short_description = 'Worker'

    def star_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b; font-size:14px;">{}</span>', stars)
    star_display.short_description = 'Rating'

    def comment_preview(self, obj):
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
    comment_preview.short_description = 'Comment'


@admin.register(WorkerAvailabilityLog)
class WorkerAvailabilityLogAdmin(admin.ModelAdmin):
    list_display = ('worker', 'became_available', 'logged_at')
    list_filter = ('became_available', 'logged_at')
    readonly_fields = ('logged_at',)


@admin.register(EmergencyCall)
class EmergencyCallAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service_type', 'condition', 'status_badge', 'location_name', 'created_at')
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('user__username', 'condition', 'location_name')
    readonly_fields = ('created_at', 'ended_at')

    def status_badge(self, obj):
        if obj.status == 'ACTIVE':
            return mark_safe('<span style="background:#fef2f2; color:#dc2626; border:1px solid #fecaca; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">🚨 Active</span>')
        return mark_safe('<span style="background:#f5f5f4; color:#785e4f; border:1px solid #e7e5e4; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:500;">Ended</span>')
    status_badge.short_description = 'Status'


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ('sender', 'message', 'created_at')
    can_delete = True


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'subject', 'status_badge', 'get_message_count', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'session_key', 'subject', 'messages__message')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SupportMessageInline]
    actions = ['mark_resolved', 'mark_escalated', 'mark_open']

    def get_user(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return f"Guest ({obj.session_key[:8] if obj.session_key else 'Anonymous'})"
    get_user.short_description = 'User / Guest'

    def get_message_count(self, obj):
        return obj.messages.count()
    get_message_count.short_description = 'Messages'

    def status_badge(self, obj):
        badges = {
            'OPEN': 'background:#fffbeb; color:#b45309; border:1px solid #fde68a;',
            'RESOLVED': 'background:#ecfdf5; color:#059669; border:1px solid #a7f3d0;',
            'ESCALATED': 'background:#fef2f2; color:#dc2626; border:1px solid #fecaca;',
        }
        style = badges.get(obj.status, 'background:#f5f5f4; color:#57534e; border:1px solid #e7e5e4;')
        return format_html(
            '<span style="{}; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">{}</span>',
            style, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_resolved(self, request, queryset):
        queryset.update(status='RESOLVED')
    mark_resolved.short_description = "✓ Mark as Resolved"

    def mark_escalated(self, request, queryset):
        queryset.update(status='ESCALATED')
    mark_escalated.short_description = "⚠️ Escalate to Human Admin"

    def mark_open(self, request, queryset):
        queryset.update(status='OPEN')
    mark_open.short_description = "Re-open Conversation"

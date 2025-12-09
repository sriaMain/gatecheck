from django.core.management.base import BaseCommand
from add_visitors.models import Visitor
from user_onboarding.models import Company, CustomUser
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix visitor and user company assignments for correct filtering.'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Fix Visitor.coming_from to be company name (string) matching CustomUser.company.company_name
            for visitor in Visitor.objects.all():
                # Try to find a matching company by name
                company = Company.objects.filter(company_name=visitor.coming_from).first()
                if company:
                    # Find users in this company
                    users = CustomUser.objects.filter(company=company)
                    if users.exists():
                        # Assign coming_from to the correct company name
                        visitor.coming_from = company.company_name
                        visitor.save(update_fields=['coming_from'])
                        self.stdout.write(self.style.SUCCESS(f'Updated Visitor {visitor.pk} coming_from to {company.company_name}'))

            # Fix CustomUser.company assignment if company_name matches coming_from of any visitor
            for user in CustomUser.objects.all():
                if user.company is None:
                    # Try to find a company by matching visitor coming_from
                    visitor = Visitor.objects.filter(coming_from__iexact=user.company.company_name if user.company else '').first()
                    if visitor:
                        company = Company.objects.filter(company_name=visitor.coming_from).first()
                        if company:
                            user.company = company
                            user.save(update_fields=['company'])
                            self.stdout.write(self.style.SUCCESS(f'Updated User {user.pk} company to {company.company_name}'))

        self.stdout.write(self.style.SUCCESS('Company assignments fixed for visitors and users.'))
